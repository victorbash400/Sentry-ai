# Training Data Documentation

## Overview
This document describes the structure and format of training data for the Sentry wildlife conservation risk prediction model. The model uses **LightGBM regression** to predict continuous risk scores (0-100) for geographic grid cells.

## Data Format: CSV

### File Structure
- **Location:** `backend/data/training_data.csv`
- **Format:** CSV with header row
- **Size:** ~10,000 training samples
- **Encoding:** UTF-8

### CSV Schema

```csv
cell_id,lat,lng,ndvi,vegetation_type,dist_to_boundary,dist_to_water,dist_to_road,dist_to_settlement,incidents_5km_radius,days_since_last_incident,seasonal_incident_rate,moon_illumination,season,day_of_week,elevation,slope,terrain_ruggedness,elephant_migration_route,breeding_season,watering_pattern,risk_score
cell-0001,-1.234,36.567,0.65,forest,2500,800,1200,5000,3,45,0.12,0.35,dry,5,1250,15,8.5,1,0,regular,78.5
cell-0002,-1.235,36.568,0.42,grassland,5200,300,3400,12000,1,120,0.08,0.62,wet,2,890,8,4.2,0,1,seasonal,45.2
...
```

## Feature Definitions

### Geographic Features
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `cell_id` | string | - | - | Unique identifier for grid cell |
| `lat` | float | -5.0 to 5.0 | degrees | Latitude (Kenya region) |
| `lng` | float | 33.0 to 42.0 | degrees | Longitude (Kenya region) |

### Vegetation Features
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `ndvi` | float | -1.0 to 1.0 | index | Normalized Difference Vegetation Index (0.2-0.8 typical for Kenya) |
| `vegetation_type` | categorical | - | - | Options: `forest`, `grassland`, `scrub`, `sparse` |

### Proximity Features (meters)
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `dist_to_boundary` | float | 0 to 50000 | meters | Distance to nearest park boundary |
| `dist_to_water` | float | 0 to 20000 | meters | Distance to nearest water source (river, lake, waterhole) |
| `dist_to_road` | float | 0 to 50000 | meters | Distance to nearest road or trail |
| `dist_to_settlement` | float | 0 to 100000 | meters | Distance to nearest human settlement |

### Historical Context
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `incidents_5km_radius` | int | 0 to 20 | count | Number of historical incidents within 5km radius |
| `days_since_last_incident` | int | 0 to 365 | days | Days since most recent incident in 10km radius |
| `seasonal_incident_rate` | float | 0.0 to 1.0 | rate | Historical incident rate for this season/location |

### Temporal Features
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `moon_illumination` | float | 0.0 to 1.0 | percentage | Moon phase (0=new moon, 1=full moon) |
| `season` | categorical | - | - | Options: `wet`, `dry` |
| `day_of_week` | int | 0 to 6 | day | Day of week (0=Monday, 6=Sunday) |

### Topographical Features
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `elevation` | float | 0 to 6000 | meters | Elevation above sea level |
| `slope` | float | 0 to 60 | degrees | Terrain slope |
| `terrain_ruggedness` | float | 0.0 to 10.0 | index | Ruggedness index (0=flat, 10=very rugged) |

### Species-Specific Features
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `elephant_migration_route` | binary | 0 or 1 | boolean | Is cell on known elephant migration route? |
| `breeding_season` | binary | 0 or 1 | boolean | Is current period breeding season for target species? |
| `watering_pattern` | categorical | - | - | Options: `regular`, `seasonal`, `rare` |

### Target Variable
| Feature | Type | Range | Unit | Description |
|---------|------|-------|------|-------------|
| `risk_score` | float | 0.0 to 100.0 | score | Continuous risk prediction target |

## Risk Score Calculation (Ground Truth)

The target `risk_score` is calculated using historical incident data:

```
risk_score = (
    incident_density_weight * 40 +      # Weight: 40%
    severity_multiplier * 30 +          # Weight: 30%
    recency_factor * 20 +               # Weight: 20%
    environmental_risk * 10             # Weight: 10%
) → clamped to [0, 100]
```

### Component Formulas

**Incident Density:**
```
incident_density_weight = min(incidents_5km_radius / 5, 1.0)
```

**Severity Multiplier:**
- Poaching: 1.0
- Logging: 0.7
- Fishing: 0.5
- Encroachment: 0.6

**Recency Factor:**
```
recency_factor = exp(-days_since_last_incident / 180)
```

**Environmental Risk:**
```
environmental_risk = (
    boundary_proximity * 0.4 +    # Closer = higher risk
    vegetation_access * 0.3 +     # Sparse vegetation = higher risk
    water_proximity * 0.3         # Closer = higher risk (wildlife congregation)
)
```

## Data Generation Strategy

### Sample Distribution
- **High Risk (80-100):** 15% of samples (~1,500 rows)
- **Medium Risk (60-80):** 25% of samples (~2,500 rows)
- **Low Risk (40-60):** 30% of samples (~3,000 rows)
- **Safe (0-40):** 30% of samples (~3,000 rows)

### Geographic Coverage
Data should span multiple Kenyan national parks:
- Tsavo East National Park
- Tsavo West National Park
- Amboseli National Park
- Maasai Mara National Reserve
- Samburu National Reserve

Coordinates should be distributed realistically within park boundaries.

### Feature Correlations (Realistic)
- **Higher risk areas:** Low NDVI, close to boundaries, near roads, high historical incidents
- **Lower risk areas:** Dense vegetation, far from boundaries, remote from settlements
- **Wildlife congregation:** Near water sources during dry season
- **Temporal patterns:** Higher risk during new moon (low visibility), weekends

## Data Quality Requirements

### Missing Data
- Maximum 5% missing values per feature
- Missing NDVI: Replace with seasonal average for vegetation type
- Missing proximity features: Use park-level median
- **Never** missing: `lat`, `lng`, `risk_score` (target)

### Outlier Handling
- NDVI outside [-0.2, 0.9]: Review or remove
- Distance features > 100km: Cap at 100km
- Risk scores must be [0, 100]

### Data Validation
Before training:
1. Check for duplicate `cell_id`
2. Verify lat/lng within Kenya bounds (-5°S to 5°N, 33°E to 42°E)
3. Ensure categorical features use defined values only
4. Confirm no NaN in target variable
5. Validate feature ranges

## Feature Engineering (During Training)

### Derived Features
The model training pipeline creates additional features:
- `boundary_risk`: 1 / (dist_to_boundary + 100) - inverse proximity
- `water_attraction`: 1 / (dist_to_water + 50)
- `access_ease`: 1 / (dist_to_road + 200)
- `isolation_score`: (dist_to_settlement + dist_to_road) / 2000
- `vegetation_cover_binary`: 1 if NDVI > 0.5 else 0
- `seasonal_water_interaction`: `season` * `watering_pattern` encoding

### Categorical Encoding
- **One-hot encoding:** `vegetation_type`, `season`, `watering_pattern`
- **Label encoding:** `day_of_week` (already numeric 0-6)
- **Binary features:** Keep as-is (0/1)

## Model Training Pipeline

### Data Split
```python
# Stratified split by risk level
train_data: 70% (7,000 samples)
validation_data: 15% (1,500 samples)
test_data: 15% (1,500 samples)
```

### Cross-Validation
- **5-Fold Stratified CV** on training set
- Stratify by risk level bins (0-40, 40-60, 60-80, 80-100)

### Input to Model
```python
X = df[feature_columns]  # All features except cell_id, lat, lng, risk_score
y = df['risk_score']     # Target variable
```

## Model Output Format

### Trained Model File
- **Path:** `backend/models/trained/risk_model_v1.pkl`
- **Format:** Python pickle (joblib)
- **Contents:** Trained LightGBM Booster object

### Model Metadata
Stored alongside model as `risk_model_v1_metadata.json`:
```json
{
  "model_version": "v1.0",
  "training_date": "2025-01-15",
  "model_type": "LightGBM Regressor",
  "training_samples": 7000,
  "validation_rmse": 12.5,
  "validation_mae": 9.3,
  "validation_r2": 0.78,
  "features": ["ndvi", "vegetation_type", ...],
  "feature_importance": {
    "dist_to_boundary": 0.28,
    "ndvi": 0.22,
    ...
  }
}
```

## Usage in Production

### Real-Time Feature Extraction
When a user draws a polygon on the map:

1. **Grid Generation:** `gee_satellite.py:create_grid_cells()`
2. **Feature Extraction:** Extract satellite features per cell
3. **Feature Formatting:** Convert to model input format (match training schema)
4. **Prediction:** `model.predict(features)`
5. **Output:** Risk scores + explanations

### Feature Extraction Mapping
```python
# From user polygon → model input
gee_features = extract_features_for_cells(cells, date_start, date_end)
model_input = map_gee_to_model_features(gee_features)
predictions = model.predict(model_input)
```

See `backend/services/feature_extractor.py` for implementation.

## Data Versioning

### File Naming Convention
```
training_data_v1_20250115.csv    # Version 1, generated Jan 15 2025
training_data_v2_20250220.csv    # Version 2, updated Feb 20 2025
```

### Model Version Linking
Each trained model metadata should reference its training data version.

## Future Enhancements

### Real Historical Data Integration
Replace synthetic data with:
- Actual incident reports (2020-2024)
- Ranger patrol logs
- Camera trap data
- Wildlife tracking data

### Additional Features
- Sentinel-1 SAR (cloud-penetrating radar)
- MODIS fire detection (human activity indicator)
- OpenStreetMap road network density
- Population density grids
- Cellular network coverage (proxy for human access)

### Multi-Output Models
Train separate models per:
- Threat type (poaching, logging, fishing)
- Species (elephant, rhino, lion)
- Time horizon (7-day, 30-day, 90-day risk)

## Contact
For questions about data format or feature engineering, see:
- `backend/guides/model_architecture.md` - Model design rationale
- `backend/services/model_trainer.py` - Training implementation
- `backend/data/synthetic_data_generator.py` - Data generation script
