# Model Training System

This guide explains how to train and use the LightGBM risk prediction model for the Sentry wildlife conservation platform.

## Overview

The training system consists of:
- **Data Generator**: Creates synthetic training data (10k samples)
- **Model Trainer**: Trains LightGBM regression model
- **Feature Extractor**: Maps user polygons to model features
- **Risk Model**: Production prediction service

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `lightgbm>=4.0.0` - Gradient boosting model
- `scikit-learn>=1.3.0` - ML utilities and metrics
- `pandas>=2.0.0` - Data manipulation
- `joblib>=1.3.0` - Model serialization
- `ephem>=4.1.0` - Moon phase calculations

### 2. Generate Training Data

```bash
python backend/data/synthetic_data_generator.py
```

This creates `backend/data/training_data.csv` with 10,000 samples containing:
- 21 features (vegetation, proximity, temporal, topographical, species)
- Realistic feature correlations
- Risk scores distributed across all levels

**Output:**
- CSV file: ~500 KB
- Risk distribution: 15% high, 25% medium, 30% low, 30% safe
- Missing values: <3% (realistic)

### 3. Train Model

```bash
python backend/services/model_trainer.py
```

Training process:
1. Loads training data from CSV
2. Prepares features (encoding, derived features)
3. Splits data: 70% train, 15% validation, 15% test
4. Trains LightGBM with 1000 boosting rounds (early stopping)
5. Evaluates with RMSE, MAE, R², and domain-specific metrics
6. Saves model to `backend/models/trained/risk_model_v1.pkl`

**Expected Performance:**
- Test RMSE: <15 points
- Test R²: >0.70
- High-risk precision: >80%

**Output:**
- Model file: `risk_model_v1.pkl` (~200 KB)
- Metadata: `risk_model_v1_metadata.json` (metrics, feature importance)

### 4. Use Trained Model

The production system automatically loads the trained model:

```python
from models.risk_model import get_model_instance

model = get_model_instance()
# Model loads backend/models/trained/risk_model_v1.pkl

predictions = model.predict_batch(cells_with_features)
```

**Fallback Mode**: If no trained model exists, the system uses simulation mode (simple heuristics based on NDVI).

## Architecture

### Data Flow

```
User draws polygon on map
    ↓
backend/main.py:analyze_risk_websocket()
    ↓
utils/gee_satellite.py:create_grid_cells()
    ↓
services/feature_extractor.py:extract_features_for_cells()
    ↓
models/risk_model.py:predict_batch()
    ↓
Return GeoJSON with risk scores
```

### Feature Extraction Pipeline

When a user draws a polygon, the system:

1. **Grid Generation** (`gee_satellite.py`)
   - Divide polygon into 1km x 1km cells
   - Filter cells inside polygon

2. **Satellite Features** (`feature_extractor.py`)
   - Extract NDVI from Sentinel-2
   - Classify vegetation type
   - Get terrain from SRTM DEM

3. **Proximity Features** (`feature_extractor.py`)
   - Calculate distance to boundary
   - Estimate distance to water, roads, settlements
   - TODO: Integrate real datasets (OSM, water bodies)

4. **Temporal Features** (`feature_extractor.py`)
   - Calculate moon phase for analysis date
   - Determine season (Kenya wet/dry)
   - Day of week

5. **Derived Features** (`feature_extractor.py`)
   - Boundary risk: 1/(dist+100)
   - Water attraction: 1/(dist+50)
   - Access ease: 1/(dist+200)
   - Vegetation binary, temporal flags

6. **Model Prediction** (`risk_model.py`)
   - Format features to match training schema
   - Run LightGBM prediction
   - Convert to risk levels and explanations

## File Structure

```
backend/
├── data/
│   ├── data.md                        # Data format documentation
│   ├── synthetic_data_generator.py    # Generate training CSV
│   └── training_data.csv              # Generated training data (gitignored)
│
├── services/
│   ├── model_trainer.py               # Train LightGBM model
│   └── feature_extractor.py           # Extract features from polygons
│
├── models/
│   ├── risk_model.py                  # Production prediction service
│   └── trained/
│       ├── risk_model_v1.pkl          # Trained model (gitignored)
│       └── risk_model_v1_metadata.json # Metrics and feature importance
│
└── requirements.txt                    # Updated with ML dependencies
```

## Feature Engineering

### Input Features (21 total)

**Satellite:**
- `ndvi` - Vegetation index (0-1)
- `vegetation_type` - Categorical: sparse, scrub, grassland, forest

**Proximity (meters):**
- `dist_to_boundary` - Distance to analysis area boundary
- `dist_to_water` - Distance to water sources
- `dist_to_road` - Distance to roads
- `dist_to_settlement` - Distance to settlements

**Historical:**
- `incidents_5km_radius` - Count of past incidents nearby
- `days_since_last_incident` - Recency of incidents
- `seasonal_incident_rate` - Historical rate for season

**Temporal:**
- `moon_illumination` - Moon phase (0-1, poachers avoid full moon)
- `season` - Wet or dry season
- `day_of_week` - Day of week (0-6)

**Topographical:**
- `elevation` - Meters above sea level
- `slope` - Terrain slope (degrees)
- `terrain_ruggedness` - Ruggedness index (0-10)

**Species:**
- `elephant_migration_route` - Binary (0/1)
- `breeding_season` - Binary (0/1)
- `watering_pattern` - Categorical: regular, seasonal, rare

### Derived Features (8 total)

Created during training and prediction:
- `boundary_risk` = 1/(dist_to_boundary + 100)
- `water_attraction` = 1/(dist_to_water + 50)
- `access_ease` = 1/(dist_to_road + 200)
- `isolation_score` = (dist_to_settlement + dist_to_road) / 2000
- `dense_vegetation` = 1 if NDVI > 0.5 else 0
- `dry_season` = 1 if season == 'dry' else 0
- `is_weekend` = 1 if day_of_week in [5,6] else 0
- `incident_density` = incidents_5km / (days_since + 1)

## Model Details

### LightGBM Hyperparameters

```python
{
    'objective': 'regression',         # Continuous risk scores
    'metric': 'rmse',                  # Root Mean Squared Error
    'boosting_type': 'gbdt',          # Gradient Boosting Decision Trees
    'num_leaves': 31,                  # Tree complexity
    'learning_rate': 0.05,             # Conservative learning
    'feature_fraction': 0.8,           # 80% features per tree
    'bagging_fraction': 0.8,           # 80% samples per tree
    'bagging_freq': 5,                 # Bagging every 5 iterations
    'max_depth': -1,                   # No depth limit
    'min_data_in_leaf': 20,            # Min samples per leaf
    'lambda_l1': 0.1,                  # L1 regularization
    'lambda_l2': 0.1,                  # L2 regularization
}
```

### Evaluation Metrics

**Regression Metrics:**
- RMSE (Root Mean Squared Error) - lower is better
- MAE (Mean Absolute Error) - average prediction error
- R² (R-squared) - variance explained (0-1, higher is better)

**Domain-Specific Metrics:**
- High-risk precision: Of predicted >80, what % were actually >80?
- High-risk recall: Of actual >80, what % were predicted >80?

### Feature Importance

After training, check `risk_model_v1_metadata.json` for feature importance:

```json
{
  "feature_importance": [
    {"feature": "dist_to_boundary", "importance": 1850.5},
    {"feature": "ndvi", "importance": 1420.3},
    {"feature": "incidents_5km_radius", "importance": 1102.7},
    ...
  ]
}
```

## Testing

### Validate Data Generation

```bash
python -c "import pandas as pd; df = pd.read_csv('backend/data/training_data.csv'); print(df.describe())"
```

### Check Model Performance

```bash
# After training, check metadata
cat backend/models/trained/risk_model_v1_metadata.json
```

### Test Prediction

```python
from models.risk_model import get_model_instance
import pandas as pd

model = get_model_instance()
print(model.metadata)

# Test with sample features
sample = [{
    'id': 'test-1',
    'center': {'lat': -2.5, 'lng': 37.5},
    'features': {
        'ndvi': 0.45,
        'dist_to_boundary': 5000,
        'dist_to_water': 2000,
        # ... other features
    }
}]

predictions = model.predict_batch(sample)
print(predictions[0]['risk_score'])
```

## Next Steps

### Immediate
1. ✅ Generate training data
2. ✅ Train initial model
3. ✅ Verify predictions work in production

### Future Enhancements

**Real Data Integration:**
- Replace synthetic data with historical incident reports
- Integrate actual ranger patrol logs
- Add camera trap data
- Wildlife tracking data

**Feature Improvements:**
- OpenStreetMap road network (real distance to roads)
- Water body datasets from GEE (real distance to water)
- Population density grids (real distance to settlements)
- Sentinel-1 SAR data (cloud-penetrating radar)
- MODIS fire detection (human activity)

**Model Improvements:**
- Separate models per threat type (poaching, logging, fishing)
- Species-specific models (elephant, rhino, lion)
- Time-horizon models (7-day, 30-day, 90-day risk)
- Uncertainty quantification (prediction intervals)

**Production:**
- Model versioning system
- A/B testing framework
- Model monitoring and retraining pipeline
- Incident feedback loop (update model with new data)

## Troubleshooting

### Model Not Loading

If you see "Using fallback simulation mode":
1. Generate training data: `python backend/data/synthetic_data_generator.py`
2. Train model: `python backend/services/model_trainer.py`
3. Verify file exists: `backend/models/trained/risk_model_v1.pkl`

### Poor Performance

If RMSE > 20 or R² < 0.6:
- Check feature correlations in training data
- Increase training samples (n_samples in generator)
- Tune hyperparameters in model_trainer.py
- Add more features or better feature engineering

### Missing Features

If you get "Missing feature X" warnings:
- Check `feature_extractor.py:format_for_model_input()`
- Ensure all features from training are extracted
- Add default values for missing features

## Documentation

- `backend/data/data.md` - Training data format and features
- `backend/guides/model_architecture.md` - Model design rationale
- This file - Training system workflow

## Contact

For questions about model training:
- Review `model_architecture.md` for design decisions
- Check `model_trainer.py` for training implementation
- See `feature_extractor.py` for feature engineering
