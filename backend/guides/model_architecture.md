# Model Architecture Guide

## Model Type: Regression (Not Binary Classification)

### Overview
Sentry uses a **LightGBM Gradient Boosting Regressor** to predict continuous risk scores (0-100) for each grid cell, NOT binary classification (poaching/no poaching).

### Why Regression Instead of Binary Classification?

**Binary Classification Problems:**
- Only outputs: "High Risk" (1) or "Low Risk" (0)
- Loses nuance - can't distinguish between "somewhat risky" and "extremely dangerous"
- Difficult to prioritize when you have limited patrol resources
- All "high risk" zones treated equally

**Regression Advantages:**
- Outputs continuous risk scores: 0 (completely safe) to 100 (extreme danger)
- Enables fine-grained prioritization - patrol 95% risk zones before 70% zones
- Can set flexible thresholds: show only >80% risk, or >60%, depending on resources
- Better resource allocation - rangers know WHICH high-risk zones need attention first
- Supports multiple risk levels: Safe (<40), Low (40-60), Medium (60-80), High (80-100)

## Model: LightGBM Gradient Boosting

### Why LightGBM?
1. **Speed:** Fast training and inference (critical for real-time analysis)
2. **Accuracy:** State-of-art gradient boosting performance
3. **Feature Handling:** Naturally handles mixed feature types (continuous, categorical)
4. **Feature Importance:** Built-in SHAP-like explanations for predictions
5. **Memory Efficient:** Lower footprint than XGBoost
6. **Spatial Data:** Excellent for geospatial feature relationships

### Training Data Structure

**Input Features (per grid cell):**
```python
{
    # Vegetation
    'ndvi': 0.65,                    # Normalized Difference Vegetation Index
    'vegetation_type': 'forest',     # Categorical: forest, grassland, scrub
    
    # Proximity (all in meters)
    'dist_to_boundary': 2500,        # Distance to park boundary
    'dist_to_water': 800,            # Distance to nearest water source
    'dist_to_road': 1200,            # Distance to nearest road
    'dist_to_settlement': 5000,      # Distance to nearest human settlement
    
    # Historical Context
    'incidents_5km_radius': 3,       # Number of incidents within 5km
    'days_since_last_incident': 45,  # Recency of nearby incidents
    'seasonal_incident_rate': 0.12,  # Historical rate for this season
    
    # Temporal
    'moon_illumination': 0.35,       # 0-1 (poachers avoid full moon)
    'season': 'dry',                 # Categorical: wet, dry
    'day_of_week': 5,                # 0-6 (patterns in poacher activity)
    
    # Topographical
    'elevation': 1250,               # Meters above sea level
    'slope': 15,                     # Degrees
    'terrain_ruggedness': 8.5,       # Index 0-10
    
    # Species-specific (if selected)
    'elephant_migration_route': 1,   # Binary: 0 or 1
    'breeding_season': 0,            # Binary: 0 or 1
    'watering_pattern': 'regular'    # Categorical
}
```

**Target Variable:**
```python
'risk_score': 0-100  # Continuous regression target
```

### Risk Score Calculation

The target risk score is derived from:
1. **Incident Density:** Number of incidents in spatial proximity
2. **Incident Severity:** Weighted by type (poaching > logging > encroachment)
3. **Temporal Decay:** Recent incidents weighted higher
4. **Environmental Context:** Areas with persistent threat factors

**Formula:**
```
risk_score = (
    incident_density * 40 +      # Historical incidents
    severity_weight * 30 +       # Type of threat
    recency_factor * 20 +        # How recent
    environmental_risk * 10      # Vegetation, access, etc.
)
```

### Model Training Approach

**Data Preparation:**
1. Historical incidents (2020-2024) from multiple Kenyan parks
2. For each incident location:
   - Extract environmental features at that point
   - Calculate risk score based on local incident density
3. Generate negative samples (safe zones):
   - Areas with no incidents and confirmed patrol coverage
   - Lower risk scores assigned
4. Split by park (model must generalize to unseen locations)

**Training Configuration:**
```python
import lightgbm as lgb

params = {
    'objective': 'regression',           # Continuous output
    'metric': 'rmse',                    # Root Mean Squared Error
    'boosting_type': 'gbdt',            # Gradient Boosting Decision Tree
    'num_leaves': 31,                    # Tree complexity
    'learning_rate': 0.05,               # Conservative for stability
    'feature_fraction': 0.8,             # Prevent overfitting
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'max_depth': -1,                     # No limit (controlled by num_leaves)
    'min_data_in_leaf': 20,
    'lambda_l1': 0.1,                    # L1 regularization
    'lambda_l2': 0.1,                    # L2 regularization
    'verbose': -1
}

model = lgb.train(
    params,
    train_data,
    num_boost_round=1000,
    valid_sets=[train_data, valid_data],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50),
        lgb.log_evaluation(period=100)
    ]
)
```

**Cross-Validation Strategy:**
- Split by park (not random): Train on 3 parks, validate on 4th
- Ensures model generalizes to completely new locations
- Multiple folds rotating which park is held out

### Model Output

**Single Prediction:**
```python
# Input: feature vector for one grid cell
# Output: continuous risk score
risk_score = model.predict(features)  # Returns float 0-100
```

**Batch Prediction:**
```python
# Input: DataFrame with features for multiple grid cells
# Output: Array of risk scores
risk_scores = model.predict(features_df)
# Returns: [45.2, 78.9, 12.3, 91.5, ...]
```

**Feature Importance (Global):**
```python
# Which features matter most across all predictions
importance = model.feature_importance(importance_type='gain')
# Returns: {'dist_to_boundary': 0.35, 'ndvi': 0.28, ...}
```

**Feature Attribution (Per Prediction):**
```python
# Why did THIS specific cell get a high score?
contributions = model.predict(features, pred_contrib=True)
# Returns: [boundary: +25, vegetation: +18, water: +12, ...]
```

### Converting Scores to Risk Levels

After model prediction, scores are categorized:

```python
def categorize_risk(score: float) -> str:
    if score < 40:
        return "safe"      # Green on map
    elif score < 60:
        return "low"       # Yellow on map
    elif score < 80:
        return "medium"    # Orange on map
    else:
        return "high"      # Red on map
```

### Model Evaluation Metrics

**Regression Metrics:**
- **RMSE (Root Mean Squared Error):** Primary metric - lower is better
- **MAE (Mean Absolute Error):** Average prediction error
- **R² Score:** How much variance explained (0-1, higher is better)

**Domain-Specific Metrics:**
- **High-Risk Precision:** Of zones predicted >80, how many had incidents?
- **High-Risk Recall:** Of actual incident zones, how many were predicted >80?
- **Ranking Quality:** Are highest predictions actually highest risk?

**Target Performance:**
- RMSE < 15 points on validation set
- R² > 0.70
- High-risk zones (>80) have >85% precision

### Model Updates and Retraining

**Frequency:** Monthly or after major incidents
**Process:**
1. Append new incident data
2. Retrain with updated historical context
3. Validate on holdout park
4. Deploy if metrics improve or maintain
5. Version models (poaching_model_v2.pkl, v3.pkl, etc.)

### Handling Edge Cases

**No Historical Incidents in Area:**
- Model relies more heavily on environmental features
- Higher uncertainty (can be communicated to user)
- Conservative predictions (avoid false confidence)

**Limited Satellite Data:**
- Use most recent clear imagery (within 30 days)
- Fallback to seasonal vegetation averages
- Flag prediction as "lower confidence"

**New Parks (No Training Data):**
- Model trained on multiple parks should generalize
- Environmental patterns transfer across locations
- May need park-specific calibration over time
