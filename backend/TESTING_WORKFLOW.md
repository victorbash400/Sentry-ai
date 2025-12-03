# Complete Model Training & Testing Workflow

This guide provides step-by-step instructions for training, testing, and deploying the Sentry risk prediction model.

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows PowerShell
   pip install -r requirements.txt
   ```

2. **Install Test Dependencies**
   ```bash
   pip install pytest pytest-cov
   ```

3. **Verify GEE Credentials**
   - Ensure `ascendant-woods-462020-n0-78d818c9658e.json` exists in `backend/`
   - Test authentication: `python tests/test_gee_satellite.py`

## Step 1: Generate Training Data

Generate 10,000 synthetic training samples with realistic feature correlations.

```bash
python data/synthetic_data_generator.py
```

**Output:**
- File: `data/training_data.csv` (~500 KB)
- Samples: 10,000 rows with 22 features
- Distribution: 15% high risk, 25% medium, 30% low, 30% safe

**Verify Data Quality:**
```bash
python run_tests.py data
```

This runs 40+ tests checking:
- Risk score distribution
- Feature correlations (NDVI vs risk, boundary distance vs risk)
- Geographic bounds (Kenya)
- Missing values (<5%)
- Data types and ranges

**Expected Result:** All tests pass ✓

## Step 2: Test Feature Extraction

Before training, verify feature extraction works correctly.

```bash
python run_tests.py extractor
```

This tests:
- Satellite feature extraction (NDVI from Sentinel-2)
- Proximity calculations (boundary, water, roads)
- Temporal features (moon phase, season)
- Topographical features (elevation, slope, ruggedness)
- Derived features (27 engineered features)

**Expected Result:** 30+ tests pass ✓

## Step 3: Train the Model

Train LightGBM regression model on synthetic data.

```bash
python services/model_trainer.py
```

**Training Process:**
1. Loads `data/training_data.csv`
2. Prepares features (encoding, engineering)
3. Splits data: 70% train, 15% validation, 15% test
4. Trains LightGBM with 1000 boosting rounds
5. Evaluates with RMSE, MAE, R²
6. Performs 5-fold cross-validation
7. Calculates feature importance
8. Saves model and metadata

**Output:**
- Model: `models/trained/risk_model_v1.pkl` (~200 KB)
- Metadata: `models/trained/risk_model_v1_metadata.json`

**Expected Performance:**
- Test RMSE: <15 points
- Test MAE: <12 points
- Test R²: >0.70
- High-risk precision: >80%
- Training time: 1-3 minutes

**Verify Training:**
```bash
# Check metadata
cat models/trained/risk_model_v1_metadata.json

# Test model loading
python run_tests.py trainer
```

## Step 4: Test Model Predictions

Test the trained model's prediction capabilities.

```bash
python run_tests.py model
```

This tests:
- Model loading from disk
- Batch prediction
- Risk score range (0-100)
- Risk categorization (critical/high/medium/low)
- Confidence calculation
- Risk factor explanations
- Fallback mode (if no trained model)

**Expected Result:** 35+ tests pass ✓

## Step 5: Integration Testing

Test the complete analysis pipeline end-to-end.

```bash
python run_tests.py integration
```

This tests:
1. User draws polygon → area calculation
2. Grid cell generation
3. Satellite feature extraction (GEE)
4. Risk prediction
5. GeoJSON output

**Expected Result:** Pipeline completes successfully ✓

## Step 6: Run All Tests

Run complete test suite to ensure everything works together.

```bash
python run_tests.py all
```

**Coverage:**
- `test_data_generator.py`: 40+ tests
- `test_model_trainer.py`: 30+ tests
- `test_feature_extractor.py`: 30+ tests
- `test_risk_model.py`: 35+ tests
- `test_gee_satellite.py`: 4 tests
- `test_integration.py`: 1 end-to-end test

**Expected Result:** 140+ tests pass ✓

## Step 7: Generate Coverage Report

```bash
python run_tests.py coverage
```

Opens HTML coverage report showing which lines are tested.

**Target Coverage:**
- Data generator: >90%
- Model trainer: >85%
- Feature extractor: >80%
- Risk model: >85%

## Step 8: Deploy to Production

Once all tests pass, the model is ready for production use.

```bash
# Start backend server
python main.py
```

The backend will automatically load `models/trained/risk_model_v1.pkl`.

**Verify in Production:**
1. Frontend: Draw polygon on map
2. Backend: Receives analysis request via WebSocket
3. Pipeline: Grid → Features → Prediction
4. Frontend: Displays risk heatmap

## Troubleshooting

### Test Failures

**Data Generator Tests Fail:**
- Check feature correlations make sense
- Verify risk distribution percentages
- Ensure no NaN in risk_score

**Model Trainer Tests Fail:**
- Verify training data exists: `data/training_data.csv`
- Check LightGBM installed: `pip install lightgbm`
- Increase training samples if poor performance

**Feature Extractor Tests Fail:**
- Check GEE authentication
- Verify date ranges are valid
- Ensure coordinates are in Kenya bounds

**Model Tests Fail:**
- Train model first: `python services/model_trainer.py`
- Check model file exists: `models/trained/risk_model_v1.pkl`
- Verify feature names match between training and prediction

### Model Performance Issues

**RMSE > 20:**
- Increase training samples in generator (n_samples=20000)
- Add more features or improve feature engineering
- Tune LightGBM hyperparameters in `model_trainer.py`

**Low R² (<0.6):**
- Check feature correlations with risk score
- Remove noisy features
- Add more informative features (historical incidents, etc.)

**Poor High-Risk Detection:**
- Check class imbalance in training data
- Adjust risk score thresholds
- Add more high-risk examples to training data

## Development Workflow

### Adding New Features

1. **Update Data Generator:**
   ```python
   # data/synthetic_data_generator.py
   def _generate_new_feature(self, risk_scores):
       # Generate feature correlated with risk
       return new_feature_values
   ```

2. **Add to Feature Extractor:**
   ```python
   # services/feature_extractor.py
   def _extract_new_feature(self, cells):
       # Extract from satellite or calculate
       return cells_with_new_feature
   ```

3. **Update Model Trainer:**
   ```python
   # services/model_trainer.py
   # Feature will be auto-included if in DataFrame
   ```

4. **Add Tests:**
   ```python
   # tests/test_data_generator.py
   def test_new_feature_range(self, generated_data):
       assert generated_data['new_feature'].min() >= 0
   ```

5. **Retrain Model:**
   ```bash
   python data/synthetic_data_generator.py
   python services/model_trainer.py
   python run_tests.py all
   ```

### Model Versioning

When retraining:
1. Change filename: `risk_model_v2.pkl`
2. Update `risk_model.py` to load new version
3. Keep old model for comparison
4. A/B test in production

### Continuous Integration

Add to CI pipeline:
```yaml
- name: Generate Data
  run: python backend/data/synthetic_data_generator.py

- name: Train Model
  run: python backend/services/model_trainer.py

- name: Run Tests
  run: python backend/run_tests.py coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Quick Reference

### Test Commands
```bash
# All tests
python run_tests.py all

# Specific component
python run_tests.py data
python run_tests.py trainer
python run_tests.py model

# With coverage
python run_tests.py coverage

# Fast tests only
python run_tests.py fast
```

### Training Commands
```bash
# Generate data
python data/synthetic_data_generator.py

# Train model
python services/model_trainer.py

# Test prediction
python -c "from models.risk_model import get_model_instance; print(get_model_instance().get_model_info())"
```

### Model Info
```bash
# Check model metadata
cat models/trained/risk_model_v1_metadata.json

# Check training data
python -c "import pandas as pd; df = pd.read_csv('data/training_data.csv'); print(df.describe())"
```

## Success Criteria

✓ Training data generated (10k samples)  
✓ Feature correlations make sense (NDVI vs risk < -0.3)  
✓ Model trained (RMSE <15, R² >0.70)  
✓ All tests pass (140+ tests)  
✓ Coverage >80%  
✓ Model loads in production  
✓ Predictions in valid range (0-100)  
✓ Risk factors provide explanations  

## Next Steps

Once basic workflow works:
1. Replace synthetic data with real incident data
2. Integrate real datasets (OSM roads, water bodies)
3. Train species-specific models
4. Implement model monitoring and retraining pipeline
5. Add prediction confidence intervals
6. Deploy model versioning system

See `guides/model_architecture.md` for detailed model design rationale.

# Run all tests
python backend/run_tests.py all

# Run specific component
python backend/run_tests.py data
python backend/run_tests.py trainer
python backend/run_tests.py model

# Generate coverage report
python backend/run_tests.py coverage

# Full workflow
python backend/data/synthetic_data_generator.py
python backend/services/model_trainer.py
python backend/run_tests.py all