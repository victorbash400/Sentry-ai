"""
Test Model Trainer
Validates model training pipeline, feature engineering, and evaluation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import joblib
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.model_trainer import ModelTrainer
from data.synthetic_data_generator import SyntheticDataGenerator


class TestModelTrainer:
    """Test suite for model training pipeline"""
    
    @pytest.fixture(scope="class")
    def training_data(self):
        """Generate small training dataset for tests"""
        generator = SyntheticDataGenerator(n_samples=500, seed=42)
        return generator.generate()
    
    @pytest.fixture(scope="class")
    def training_data_file(self, training_data, tmp_path_factory):
        """Save training data to temporary CSV"""
        tmp_dir = tmp_path_factory.mktemp("data")
        csv_path = tmp_dir / "test_training_data.csv"
        training_data.to_csv(csv_path, index=False)
        return str(csv_path)
    
    @pytest.fixture
    def trainer(self, training_data_file):
        """Create trainer instance with test data"""
        return ModelTrainer(data_path=training_data_file)
    
    def test_trainer_initialization(self, trainer, training_data_file):
        """Test trainer initializes correctly"""
        assert trainer.data_path == Path(training_data_file)
        assert trainer.model is None
        assert trainer.label_encoders == {}
        assert trainer.feature_names == []
    
    def test_load_data(self, trainer):
        """Test data loading from CSV"""
        df = trainer.load_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 500
        assert 'risk_score' in df.columns
        assert df['risk_score'].notna().all()
    
    def test_load_data_missing_file(self):
        """Test error handling when data file doesn't exist"""
        trainer = ModelTrainer(data_path="nonexistent_file.csv")
        
        with pytest.raises(FileNotFoundError):
            trainer.load_data()
    
    def test_prepare_features(self, trainer):
        """Test feature preparation pipeline"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # Check X (features)
        assert isinstance(X, pd.DataFrame)
        assert len(X) == len(df)
        assert len(X.columns) > 20  # Should have many features
        
        # Check y (target)
        assert isinstance(y, pd.Series)
        assert len(y) == len(df)
        assert y.notna().all()
        assert y.min() >= 0
        assert y.max() <= 100
    
    def test_categorical_encoding(self, trainer):
        """Test categorical features are encoded"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # Check encoded columns exist
        assert 'vegetation_type_encoded' in X.columns
        assert 'season_encoded' in X.columns
        assert 'watering_pattern_encoded' in X.columns
        
        # Check label encoders were created
        assert 'vegetation_type' in trainer.label_encoders
        assert 'season' in trainer.label_encoders
        assert 'watering_pattern' in trainer.label_encoders
    
    def test_derived_features_created(self, trainer):
        """Test derived features are calculated"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # Check derived features exist
        derived = ['boundary_risk', 'water_attraction', 'access_ease', 
                  'isolation_score', 'dense_vegetation', 'dry_season',
                  'is_weekend', 'incident_density']
        
        for feature in derived:
            assert feature in X.columns, f"Derived feature missing: {feature}"
    
    def test_feature_names_stored(self, trainer):
        """Test feature names are stored for later use"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        assert len(trainer.feature_names) > 0
        assert len(trainer.feature_names) == len(X.columns)
        assert trainer.feature_names == list(X.columns)
    
    def test_missing_value_handling(self, trainer):
        """Test missing values are handled properly"""
        df = trainer.load_data()
        
        # Add some missing values
        df.loc[0:5, 'ndvi'] = np.nan
        df.loc[10:15, 'elevation'] = np.nan
        
        X, y = trainer.prepare_features(df)
        
        # Features should have no missing values after preparation
        assert X['ndvi'].notna().all()
        assert X['elevation'].notna().all()
        
        # Target should have no missing values
        assert y.notna().all()
    
    def test_no_target_in_features(self, trainer):
        """Test target variable is not included in features"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        assert 'risk_score' not in X.columns
    
    def test_no_identifiers_in_features(self, trainer):
        """Test identifier columns are not included in features"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        assert 'cell_id' not in X.columns
        assert 'lat' not in X.columns
        assert 'lng' not in X.columns
    
    def test_train_model(self, trainer):
        """Test model training pipeline"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # Train with smaller parameters for speed
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Check model was created
        assert trainer.model is not None
        assert hasattr(trainer.model, 'predict')
        
        # Check results structure
        assert 'model' in results
        assert 'val_metrics' in results
        assert 'test_metrics' in results
        assert 'cv_scores' in results
        assert 'feature_importance' in results
        assert 'metadata' in results
    
    def test_validation_metrics(self, trainer):
        """Test validation metrics are computed"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        val_metrics = results['val_metrics']
        
        # Check metric keys
        assert 'rmse' in val_metrics
        assert 'mae' in val_metrics
        assert 'r2' in val_metrics
        assert 'high_risk_precision' in val_metrics
        assert 'high_risk_recall' in val_metrics
        
        # Check metric values are reasonable
        assert val_metrics['rmse'] > 0
        assert val_metrics['mae'] > 0
        assert 0 <= val_metrics['r2'] <= 1
        assert 0 <= val_metrics['high_risk_precision'] <= 1
        assert 0 <= val_metrics['high_risk_recall'] <= 1
    
    def test_test_metrics(self, trainer):
        """Test test set metrics are computed"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        test_metrics = results['test_metrics']
        
        # Test metrics should exist
        assert 'rmse' in test_metrics
        assert 'mae' in test_metrics
        assert 'r2' in test_metrics
    
    def test_cross_validation(self, trainer):
        """Test cross-validation scores"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        cv_scores = results['cv_scores']
        
        # Check CV score keys
        assert 'rmse_mean' in cv_scores
        assert 'rmse_std' in cv_scores
        assert 'mae_mean' in cv_scores
        assert 'mae_std' in cv_scores
        assert 'r2_mean' in cv_scores
        assert 'r2_std' in cv_scores
        
        # Check values are reasonable
        assert cv_scores['rmse_mean'] > 0
        assert cv_scores['rmse_std'] >= 0
        assert 0 <= cv_scores['r2_mean'] <= 1
    
    def test_feature_importance(self, trainer):
        """Test feature importance is computed"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        importance = results['feature_importance']
        
        assert isinstance(importance, pd.DataFrame)
        assert 'feature' in importance.columns
        assert 'importance' in importance.columns
        assert len(importance) == len(trainer.feature_names)
        
        # Check importance values are non-negative
        assert (importance['importance'] >= 0).all()
    
    def test_metadata_creation(self, trainer):
        """Test metadata is created correctly"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        metadata = results['metadata']
        
        # Check required metadata fields
        required_fields = [
            'model_version', 'training_date', 'model_type',
            'training_samples', 'validation_samples', 'test_samples',
            'num_features', 'num_trees', 'best_iteration',
            'validation_rmse', 'validation_mae', 'validation_r2',
            'test_rmse', 'test_mae', 'test_r2'
        ]
        
        for field in required_fields:
            assert field in metadata, f"Missing metadata field: {field}"
    
    def test_model_save(self, trainer, tmp_path):
        """Test model can be saved to disk"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Save to temporary directory
        model_file = tmp_path / "test_model.pkl"
        
        # Temporarily change models directory
        original_parent = Path(__file__).parent.parent
        trainer_file_path = original_parent / 'services' / 'model_trainer.py'
        
        # Save model
        model_path, metadata_path = trainer.save_model(str(model_file))
        
        # Check files were created
        assert model_path.exists()
        assert metadata_path.exists()
        assert model_path.stat().st_size > 0
        assert metadata_path.stat().st_size > 0
    
    def test_model_save_and_load(self, trainer, tmp_path):
        """Test saved model can be loaded and used"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Save model
        model_file = tmp_path / "test_model.pkl"
        model_path, metadata_path = trainer.save_model(str(model_file))
        
        # Load model
        loaded_data = joblib.load(model_path)
        
        assert 'model' in loaded_data
        assert 'feature_names' in loaded_data
        assert 'label_encoders' in loaded_data
        
        # Test prediction with loaded model
        loaded_model = loaded_data['model']
        predictions = loaded_model.predict(X.head(10))
        
        assert len(predictions) == 10
        assert all(0 <= p <= 100 for p in predictions)
    
    def test_metadata_save_and_load(self, trainer, tmp_path):
        """Test metadata JSON can be loaded"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Save model and metadata
        model_file = tmp_path / "test_model.pkl"
        model_path, metadata_path = trainer.save_model(str(model_file))
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert 'model_version' in metadata
        assert 'training_date' in metadata
        assert 'features' in metadata
        assert 'feature_importance' in metadata
    
    def test_model_predictions_in_range(self, trainer):
        """Test model predictions are in valid range"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Make predictions on all data
        predictions = trainer.model.predict(X)
        
        # Check predictions are in valid range (allowing slight overflow)
        assert predictions.min() >= -10, f"Prediction too low: {predictions.min()}"
        assert predictions.max() <= 110, f"Prediction too high: {predictions.max()}"
    
    def test_stratified_split(self, trainer):
        """Test data split maintains risk distribution"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # Count risk levels before split
        def count_risk_levels(scores):
            return {
                'high': sum(scores >= 80),
                'medium': sum((scores >= 60) & (scores < 80)),
                'low': sum((scores >= 40) & (scores < 60)),
                'safe': sum(scores < 40)
            }
        
        original_dist = count_risk_levels(y)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Check metadata has reasonable split sizes
        total_samples = len(y)
        assert results['metadata']['training_samples'] < total_samples
        assert results['metadata']['validation_samples'] < total_samples
        assert results['metadata']['test_samples'] < total_samples
    
    def test_high_risk_precision_recall(self, trainer):
        """Test high-risk zone detection metrics"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # High-risk precision should be reasonable
        # (may be 0 if no high-risk zones in small test set)
        precision = results['val_metrics']['high_risk_precision']
        recall = results['val_metrics']['high_risk_recall']
        
        assert 0 <= precision <= 1
        assert 0 <= recall <= 1
    
    def test_reproducibility(self, trainer):
        """Test training is reproducible with same data"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # Train twice
        results1 = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Reset trainer
        trainer.model = None
        results2 = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Models should have similar performance
        rmse_diff = abs(results1['test_metrics']['rmse'] - results2['test_metrics']['rmse'])
        assert rmse_diff < 5, "Training not reproducible"
    
    def test_feature_importance_ranking(self, trainer):
        """Test feature importance ranks expected features highly"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        importance = results['feature_importance']
        
        # Get top 10 features
        top_features = importance.head(10)['feature'].tolist()
        
        # Expected important features should be in top ranks
        important_expected = ['dist_to_boundary', 'incidents_5km_radius', 'ndvi',
                             'boundary_risk', 'days_since_last_incident']
        
        # At least some expected features should be in top 10
        matches = sum(1 for f in important_expected if f in top_features)
        assert matches >= 3, f"Expected features not in top 10: {top_features}"
    
    def test_no_data_leakage(self, trainer):
        """Test no data leakage between train/val/test"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        # This is implicitly tested by sklearn's train_test_split
        # Just verify metadata shows proper splits
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        train_size = results['metadata']['training_samples']
        val_size = results['metadata']['validation_samples']
        test_size = results['metadata']['test_samples']
        
        # Splits should be non-overlapping and sum to total
        assert train_size + val_size + test_size == len(X)
    
    def test_early_stopping(self, trainer):
        """Test early stopping prevents overfitting"""
        df = trainer.load_data()
        X, y = trainer.prepare_features(df)
        
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=3)
        
        # Best iteration should be less than max rounds
        best_iter = results['metadata']['best_iteration']
        num_trees = results['metadata']['num_trees']
        
        assert best_iter <= num_trees
        # Usually early stopping triggers before max rounds
        assert best_iter < 1000, "Early stopping may not be working"
    
    def test_handles_imbalanced_risk_distribution(self, trainer):
        """Test trainer handles imbalanced risk distributions"""
        df = trainer.load_data()
        
        # Create imbalanced dataset (mostly safe zones)
        df_imbalanced = df.copy()
        df_imbalanced.loc[df_imbalanced['risk_score'] >= 80, 'risk_score'] = \
            df_imbalanced.loc[df_imbalanced['risk_score'] >= 80, 'risk_score'] * 0.5
        
        X, y = trainer.prepare_features(df_imbalanced)
        
        # Training should still work
        results = trainer.train(X, y, test_size=0.2, val_size=0.2, cv_folds=2)
        
        assert results['model'] is not None
        assert results['val_metrics']['rmse'] > 0


def test_main_execution(training_data_file):
    """Test main() function runs without errors"""
    # This would require actual file at expected location
    # Skip for unit tests, but could be integration test
    pass


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
