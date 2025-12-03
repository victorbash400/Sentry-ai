# Backend Tests

Comprehensive test suite for the Sentry wildlife conservation platform backend.

## Test Files

### 1. `test_data_generator.py`
Tests synthetic training data generation.

**Coverage:**
- Data shape and structure (1000 samples, 22+ columns)
- Required columns presence
- Risk score distribution (15% high, 25% medium, 30% low, 30% safe)
- Geographic bounds (Kenya latitude/longitude)
- Feature ranges and validity (NDVI, distances, elevation, etc.)
- Feature correlations with risk
  - NDVI: negative correlation (lower vegetation = higher risk)
  - Boundary distance: negative correlation
  - Historical incidents: positive correlation
- Missing value handling (<5% per feature)
- Data types validation
- Reproducibility with seed
- CSV save/load functionality
- Statistical distributions

**Run:**
```bash
pytest backend/tests/test_data_generator.py -v
```

### 2. `test_model_trainer.py`
Tests LightGBM model training pipeline.

**Coverage:**
- Data loading from CSV
- Feature preparation and encoding
- Categorical feature encoding (vegetation, season, watering pattern)
- Derived feature creation (27 engineered features)
- Missing value handling
- Model training with LightGBM
- Train/validation/test splits (70/15/15)
- Evaluation metrics (RMSE, MAE, R², precision, recall)
- Cross-validation (k-fold)
- Feature importance calculation
- Model serialization and loading
- Metadata creation
- Early stopping
- Stratified splitting by risk level
- Reproducibility

**Run:**
```bash
pytest backend/tests/test_model_trainer.py -v
```

### 3. `test_feature_extractor.py`
Tests feature extraction from geographic coordinates.

**Coverage:**
- Haversine distance calculations
- Distance to polygon edge
- Terrain ruggedness calculation
- Satellite feature extraction (NDVI from Sentinel-2)
- Vegetation type classification
- Proximity features (boundary, water, roads, settlements)
- Temporal features (moon phase, season, day of week)
- Topographical features (elevation, slope, ruggedness from SRTM)
- Species features (migration routes, breeding season, watering patterns)
- Derived feature calculations
- Feature format for model input (27 features)
- Vegetation-NDVI consistency
- Date range handling
- Empty/single/batch cell processing

**Run:**
```bash
pytest backend/tests/test_feature_extractor.py -v
```

### 4. `test_risk_model.py`
Tests risk prediction model (production inference).

**Coverage:**
- Model initialization (trained and fallback modes)
- Risk categorization (critical/high/medium/low)
- Batch prediction
- Risk score range validation (0-100)
- Confidence calculation
- Risk factor explanations
- Contribution normalization (factors sum to ~100%)
- Model metadata
- NDVI-risk correlation in predictions
- Threat type parameters
- Empty/large batch handling
- Missing feature handling
- Confidence adjustments for completeness and extremity
- Model info retrieval
- Cell information preservation
- Trained model loading and prediction

**Run:**
```bash
pytest backend/tests/test_risk_model.py -v
```

### 5. `test_gee_satellite.py` (Existing)
Tests Google Earth Engine integration.

**Coverage:**
- GEE authentication with service account
- Sentinel-2 image access
- NDVI calculation
- Batch feature extraction

**Run:**
```bash
pytest backend/tests/test_gee_satellite.py -v
```

### 6. `test_integration.py` (Existing)
Tests full analysis pipeline end-to-end.

**Coverage:**
- Polygon area calculation
- Grid cell generation
- Satellite feature extraction
- Risk score generation
- Complete workflow

**Run:**
```bash
pytest backend/tests/test_integration.py -v
```

## Running All Tests

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run Specific Test Class
```bash
pytest tests/test_data_generator.py::TestSyntheticDataGenerator -v
```

### Run Specific Test
```bash
pytest tests/test_data_generator.py::TestSyntheticDataGenerator::test_risk_distribution -v
```

### Run Tests Matching Pattern
```bash
pytest tests/ -k "correlation" -v
```

## Test Dependencies

Install test dependencies:
```bash
pip install pytest pytest-cov
```

All other dependencies are in `requirements.txt`:
- lightgbm
- pandas
- numpy
- scikit-learn
- earthengine-api
- ephem (for moon phase)

## Test Data

Tests use:
- **Small datasets**: 500-1000 samples for speed
- **Temporary files**: Tests clean up automatically
- **Mocked models**: For testing model loading without full training
- **Fixed seeds**: For reproducibility (seed=42)

## Expected Test Results

### Data Generator Tests
- **40+ tests** covering all aspects of synthetic data
- All tests should pass
- Warnings acceptable for GEE operations

### Model Trainer Tests
- **30+ tests** covering training pipeline
- Tests create temporary models
- May take 1-2 minutes (LightGBM training)

### Feature Extractor Tests
- **30+ tests** covering feature engineering
- Some tests may be slow (GEE API calls)
- Fallback to defaults if GEE unavailable

### Risk Model Tests
- **35+ tests** covering predictions
- Fast tests (mostly fallback mode)
- Trained model tests require LightGBM

## Integration with CI/CD

These tests are designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    cd backend
    pytest tests/ -v --cov=. --cov-report=xml
```

**Note:** GEE tests require service account credentials. Set as CI secret.

## Test Coverage Goals

Target coverage by module:
- `data/synthetic_data_generator.py`: >90%
- `services/model_trainer.py`: >85%
- `services/feature_extractor.py`: >80%
- `models/risk_model.py`: >85%

## Common Issues

### GEE Authentication Fails
- Ensure `ascendant-woods-462020-n0-78d818c9658e.json` exists
- Check service account has Earth Engine enabled
- Tests fall back to simulation if GEE unavailable

### LightGBM Import Error
```bash
pip install lightgbm
```

### Slow Tests
- Use `-v` flag to see progress
- Skip slow tests: `pytest -m "not slow"`
- Run in parallel: `pytest -n auto` (requires pytest-xdist)

## Next Steps

1. **Generate training data:**
   ```bash
   python backend/data/synthetic_data_generator.py
   ```

2. **Train model:**
   ```bash
   python backend/services/model_trainer.py
   ```

3. **Run all tests:**
   ```bash
   pytest backend/tests/ -v
   ```

4. **Check coverage:**
   ```bash
   pytest backend/tests/ --cov=. --cov-report=html
   open htmlcov/index.html
   ```

## Test Documentation

Each test file includes:
- Docstrings explaining what is tested
- Fixtures for reusable test data
- Clear assertion messages
- Grouped test classes by functionality

See individual test files for detailed documentation.
