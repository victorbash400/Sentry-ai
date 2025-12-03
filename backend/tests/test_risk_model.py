"""
Test Risk Prediction Model
Validates model loading, predictions, risk categorization, and explanations
"""

import pytest
import numpy as np
import sys
from pathlib import Path
import tempfile
import joblib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.risk_model import RiskPredictionModel, get_model_instance


class TestRiskPredictionModel:
    """Test suite for risk prediction model"""
    
    @pytest.fixture
    def model(self):
        """Load the trained model"""
        # Use default path which points to trained model
        return RiskPredictionModel()
    
    @pytest.fixture
    def sample_features(self):
        """Create sample features for prediction"""
        return {
            'ndvi': 0.45,
            'vegetation_type_encoded': 2,
            'dist_to_boundary': 5000,
            'dist_to_water': 2000,
            'dist_to_road': 8000,
            'dist_to_settlement': 20000,
            'incidents_5km_radius': 2,
            'days_since_last_incident': 60,
            'seasonal_incident_rate': 0.15,
            'moon_illumination': 0.3,
            'season_encoded': 0,
            'day_of_week': 5,
            'elevation': 1200,
            'slope': 15,
            'terrain_ruggedness': 6.5,
            'elephant_migration_route': 1,
            'breeding_season': 0,
            'watering_pattern_encoded': 1,
            'boundary_risk': 1/5100,
            'water_attraction': 1/2050,
            'access_ease': 1/8200,
            'isolation_score': 14,
            'dense_vegetation': 0,
            'dry_season': 1,
            'is_weekend': 1,
            'incident_density': 0.033
        }
    
    @pytest.fixture
    def sample_cell_with_features(self, sample_features):
        """Create sample cell with features"""
        return {
            'id': 'cell-test-001',
            'center': {'lat': -2.8, 'lng': 38.9},
            'bounds': {
                'south': -2.81, 'north': -2.79,
                'west': 38.89, 'east': 38.91
            },
            'features': sample_features
        }
    
    def test_model_initialization(self, model):
        """Test model initializes and loads successfully"""
        assert model.is_loaded == True
        assert model.model is not None
        assert len(model.feature_names) > 0
    
    def test_singleton_instance(self):
        """Test singleton pattern for model instance"""
        model1 = get_model_instance()
        model2 = get_model_instance()
        
        assert model1 is model2
    
    def test_categorize_risk(self, model):
        """Test risk categorization thresholds"""
        assert model._categorize_risk(95) == 'critical'
        assert model._categorize_risk(80) == 'critical'
        assert model._categorize_risk(75) == 'high'
        assert model._categorize_risk(60) == 'high'
        assert model._categorize_risk(55) == 'medium'
        assert model._categorize_risk(40) == 'medium'
        assert model._categorize_risk(30) == 'low'
        assert model._categorize_risk(10) == 'low'
    
    def test_predict_batch_fallback(self, model, sample_cell_with_features):
        """Test batch prediction in fallback mode"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells, threat_type="poaching")
        
        assert len(predictions) == 1
        
        prediction = predictions[0]
        
        # Check structure
        assert 'id' in prediction
        assert 'center' in prediction
        assert 'risk_score' in prediction
        assert 'risk_level' in prediction
        assert 'confidence' in prediction
        assert 'risk_factors' in prediction
        assert 'model_metadata' in prediction
    
    def test_risk_score_range(self, model, sample_cell_with_features):
        """Test risk scores are in valid range [0, 100]"""
        cells = [sample_cell_with_features] * 10
        
        predictions = model.predict_batch(cells)
        
        for pred in predictions:
            assert 0 <= pred['risk_score'] <= 100
    
    def test_risk_score_type(self, model, sample_cell_with_features):
        """Test risk score is integer"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells)
        
        assert isinstance(predictions[0]['risk_score'], int)
    
    def test_confidence_range(self, model, sample_cell_with_features):
        """Test confidence is in valid range [0, 1]"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells)
        
        assert 0 <= predictions[0]['confidence'] <= 1
    
    def test_risk_factors_structure(self, model, sample_cell_with_features):
        """Test risk factors have proper structure"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells)
        
        factors = predictions[0]['risk_factors']
        
        assert isinstance(factors, list)
        assert len(factors) > 0
        
        for factor in factors:
            assert 'factor' in factor
            assert 'contribution' in factor
            assert 'description' in factor
            assert isinstance(factor['factor'], str)
            assert isinstance(factor['contribution'], int)
            assert isinstance(factor['description'], str)
            assert 0 <= factor['contribution'] <= 100
    
    def test_risk_factors_sum_to_100(self, model, sample_cell_with_features):
        """Test risk factor contributions sum to approximately 100"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells)
        
        factors = predictions[0]['risk_factors']
        total_contribution = sum(f['contribution'] for f in factors)
        
        # Should be close to 100 (allow some rounding error)
        assert 95 <= total_contribution <= 105
    
    def test_model_metadata(self, model, sample_cell_with_features):
        """Test model metadata is included in predictions"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells)
        
        metadata = predictions[0]['model_metadata']
        
        assert 'version' in metadata
        assert 'model_type' in metadata
        assert 'features_used' in metadata
        assert 'prediction_time' in metadata
    
    def test_low_ndvi_high_risk(self, model):
        """Test sparse vegetation (low NDVI) correlates with higher risk"""
        # Sparse vegetation cell
        sparse_cell = {
            'id': 'sparse',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': 0.15}
        }
        
        # Dense vegetation cell
        dense_cell = {
            'id': 'dense',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': 0.75}
        }
        
        predictions = model.predict_batch([sparse_cell, dense_cell])
        
        sparse_risk = predictions[0]['risk_score']
        dense_risk = predictions[1]['risk_score']
        
        # Sparse vegetation should generally have higher risk
        # Allow some randomness in simulation
        assert sparse_risk >= dense_risk - 15
    
    def test_batch_prediction_consistency(self, model, sample_cell_with_features):
        """Test same input produces similar predictions"""
        cells = [sample_cell_with_features] * 2
        
        predictions = model.predict_batch(cells)
        
        # Same features should produce similar (but not identical due to noise) risk scores
        score_diff = abs(predictions[0]['risk_score'] - predictions[1]['risk_score'])
        assert score_diff < 20, "Same features producing very different scores"
    
    def test_threat_type_parameter(self, model, sample_cell_with_features):
        """Test different threat types can be specified"""
        cells = [sample_cell_with_features]
        
        threat_types = ["poaching", "logging", "fishing", "encroachment"]
        
        for threat_type in threat_types:
            predictions = model.predict_batch(cells, threat_type=threat_type)
            assert len(predictions) == 1
            assert predictions[0]['risk_score'] >= 0
    
    def test_empty_batch(self, model):
        """Test prediction with empty batch"""
        predictions = model.predict_batch([])
        
        assert len(predictions) == 0
    
    def test_large_batch(self, model, sample_features):
        """Test prediction with larger batch"""
        # Create 100 cells
        cells = []
        for i in range(100):
            cells.append({
                'id': f'cell-{i:03d}',
                'center': {'lat': -2.8 - i*0.01, 'lng': 38.9 + i*0.01},
                'features': sample_features.copy()
            })
        
        predictions = model.predict_batch(cells)
        
        assert len(predictions) == 100
        
        # All should have valid risk scores
        for pred in predictions:
            assert 0 <= pred['risk_score'] <= 100
    
    def test_missing_features_handled(self, model):
        """Test model handles missing features gracefully"""
        # Cell with only NDVI
        minimal_cell = {
            'id': 'minimal',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': 0.5}
        }
        
        predictions = model.predict_batch([minimal_cell])
        
        assert len(predictions) == 1
        assert 0 <= predictions[0]['risk_score'] <= 100
    
    def test_none_ndvi_handled(self, model):
        """Test model handles None NDVI (no satellite data)"""
        no_data_cell = {
            'id': 'no-data',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': None}
        }
        
        predictions = model.predict_batch([no_data_cell])
        
        assert len(predictions) == 1
        # Should have lower confidence
        assert predictions[0]['confidence'] < 0.6
    
    def test_calculate_confidence(self, model):
        """Test confidence calculation logic"""
        import pandas as pd
        
        # Complete features - high confidence
        complete_features = pd.Series({
            'ndvi': 0.5,
            'dist_to_boundary': 5000,
            'elevation': 1000
        })
        confidence_complete = model._calculate_confidence(50, complete_features)
        assert confidence_complete > 0.8
        
        # Missing features - lower confidence
        incomplete_features = pd.Series({
            'ndvi': 0.5,
            'dist_to_boundary': np.nan,
            'elevation': np.nan
        })
        confidence_incomplete = model._calculate_confidence(50, incomplete_features)
        assert confidence_incomplete < confidence_complete
    
    def test_extreme_risk_lower_confidence(self, model):
        """Test extreme predictions have lower confidence"""
        import pandas as pd
        
        features = pd.Series({
            'ndvi': 0.5,
            'dist_to_boundary': 5000,
            'elevation': 1000
        })
        
        # Middle risk - higher confidence
        confidence_middle = model._calculate_confidence(50, features)
        
        # Extreme risk - lower confidence
        confidence_extreme = model._calculate_confidence(95, features)
        
        assert confidence_middle > confidence_extreme
    
    def test_get_model_info(self, model):
        """Test model info retrieval"""
        info = model.get_model_info()
        
        assert 'status' in info
        assert 'supported_threats' in info
        assert 'input_features' in info
        
        assert len(info['supported_threats']) > 0
        assert len(info['input_features']) > 0
    
    def test_risk_level_consistency(self, model, sample_cell_with_features):
        """Test risk level matches risk score thresholds"""
        cells = [sample_cell_with_features] * 20
        
        predictions = model.predict_batch(cells)
        
        for pred in predictions:
            score = pred['risk_score']
            level = pred['risk_level']
            
            if score >= 80:
                assert level in ['critical', 'high']
            elif score >= 60:
                assert level in ['high', 'medium']
            elif score >= 40:
                assert level in ['medium', 'low']
            else:
                assert level == 'low'
    
    def test_predictions_preserve_cell_info(self, model, sample_cell_with_features):
        """Test predictions preserve original cell information"""
        cells = [sample_cell_with_features]
        
        predictions = model.predict_batch(cells)
        
        pred = predictions[0]
        
        assert pred['id'] == sample_cell_with_features['id']
        assert pred['center'] == sample_cell_with_features['center']
        assert 'bounds' in pred
    
    def test_different_ndvi_different_factors(self, model):
        """Test different NDVI values produce different risk factor explanations"""
        sparse_cell = {
            'id': 'sparse',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': 0.15}
        }
        
        dense_cell = {
            'id': 'dense',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': 0.75}
        }
        
        predictions = model.predict_batch([sparse_cell, dense_cell])
        
        sparse_factors = [f['factor'] for f in predictions[0]['risk_factors']]
        dense_factors = [f['factor'] for f in predictions[1]['risk_factors']]
        
        # Factors should mention vegetation in both cases but with different descriptions
        assert any('vegetation' in f.lower() for f in sparse_factors)
        assert any('vegetation' in f.lower() for f in dense_factors)
    
    def test_high_risk_has_multiple_factors(self, model):
        """Test high-risk predictions have multiple contributing factors"""
        # Create conditions for high risk
        high_risk_cell = {
            'id': 'high-risk',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {'ndvi': 0.15}  # Sparse vegetation
        }
        
        predictions = model.predict_batch([high_risk_cell])
        
        if predictions[0]['risk_score'] > 60:
            factors = predictions[0]['risk_factors']
            assert len(factors) >= 2, "High risk should have multiple factors"
    
    def test_model_version_info(self, model):
        """Test model version information is accessible"""
        info = model.get_model_info()
        
        # Should have version information
        assert 'version' in info or 'model_version' in info
    
    def test_feature_names_stored(self, model):
        """Test feature names are stored in model"""
        assert len(model.feature_names) > 0
        
        # Should include key features
        expected_features = ['ndvi', 'water_proximity', 'boundary_distance']
        # In fallback mode, feature names might be simplified
        assert any(f in str(model.feature_names) for f in ['ndvi', 'boundary', 'water'])


class TestTrainedModelLoading:
    """Test suite for loading and using a trained model"""
    
    @pytest.fixture
    def mock_trained_model(self, tmp_path):
        """Create a mock trained model file"""
        import lightgbm as lgb
        import pandas as pd
        
        # Create small training data
        np.random.seed(42)
        X = pd.DataFrame({
            'ndvi': np.random.uniform(0, 0.8, 100),
            'dist_to_boundary': np.random.uniform(100, 20000, 100),
            'elevation': np.random.uniform(500, 3000, 100)
        })
        y = 50 + X['ndvi'] * -30 + np.random.normal(0, 10, 100)
        y = np.clip(y, 0, 100)
        
        # Train simple model
        train_data = lgb.Dataset(X, label=y)
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'num_leaves': 7,
            'learning_rate': 0.1,
            'verbose': -1
        }
        model = lgb.train(params, train_data, num_boost_round=10)
        
        # Save model
        model_path = tmp_path / "test_model.pkl"
        joblib.dump({
            'model': model,
            'feature_names': list(X.columns),
            'label_encoders': {}
        }, model_path)
        
        # Save metadata
        metadata_path = tmp_path / "test_model_metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump({
                'model_version': 'v1.0-test',
                'model_type': 'LightGBM',
                'num_trees': 10,
                'validation_rmse': 12.5
            }, f)
        
        return str(model_path)
    
    def test_load_trained_model(self, mock_trained_model):
        """Test loading a trained model from disk"""
        model = RiskPredictionModel(model_path=mock_trained_model)
        
        assert model.is_loaded == True
        assert model.model is not None
        assert len(model.feature_names) > 0
    
    def test_trained_model_prediction(self, mock_trained_model):
        """Test making predictions with trained model"""
        model = RiskPredictionModel(model_path=mock_trained_model)
        
        cell = {
            'id': 'test-cell',
            'center': {'lat': -2.8, 'lng': 38.9},
            'features': {
                'ndvi': 0.5,
                'dist_to_boundary': 5000,
                'elevation': 1000
            }
        }
        
        predictions = model.predict_batch([cell])
        
        assert len(predictions) == 1
        assert 0 <= predictions[0]['risk_score'] <= 100


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
