"""
LightGBM Model Training Service
Trains regression model for agricultural pest/disease risk prediction
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder


class ModelTrainer:
    """LightGBM model training and evaluation for agricultural risk"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize trainer
        
        Args:
            data_path: Path to training data CSV (default: backend/data/training_data.csv)
        """
        if data_path is None:
            data_path = Path(__file__).parent.parent / 'data' / 'training_data.csv'
        else:
            data_path = Path(data_path)
        
        self.data_path = data_path
        self.model = None
        self.label_encoders = {}
        self.feature_names = []
        self.metadata = {}
        
        print(f"Model Trainer initialized with data: {data_path}")
    
    def load_data(self) -> pd.DataFrame:
        """
        Load training data from CSV
        
        Returns:
            DataFrame with all features and target
        """
        print(f"\nLoading training data from {self.data_path}...")
        
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Training data not found at {self.data_path}. "
                "Run: python backend/data/synthetic_data_generator.py"
            )
        
        df = pd.read_csv(self.data_path)
        
        print(f"SUCCESS: Loaded {len(df)} samples with {len(df.columns)} features")
        print(f"  Risk score range: [{df['risk_score'].min():.1f}, {df['risk_score'].max():.1f}]")
        print(f"  Missing values: {df.isnull().sum().sum()} total")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for model training
        - Handle missing values
        - Encode categorical features
        - Create derived features
        - Split features and target
        
        Args:
            df: Raw DataFrame
        
        Returns:
            Tuple of (X_features, y_target)
        """
        print("\nPreparing features...")
        
        df = df.copy()
        
        # Handle missing values
        # NDVI: Fill with median by crop type
        if df['ndvi'].isnull().any():
            df['ndvi'] = df.groupby('crop_type')['ndvi'].transform(
                lambda x: x.fillna(x.median())
            )
        
        # Other numeric features: Fill with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any() and col != 'risk_score':
                df[col] = df[col].fillna(df[col].median())
        
        # Encode categorical features
        categorical_features = ['crop_type', 'pest_pressure', 'crop_stage']
        
        for feature in categorical_features:
            if feature in df.columns:
                le = LabelEncoder()
                df[f'{feature}_encoded'] = le.fit_transform(df[feature])
                self.label_encoders[feature] = le
                print(f"  Encoded {feature}: {list(le.classes_)}")
        
        # Create derived features (feature engineering)
        print("\nCreating derived features...")
        
        # Environmental Stress Indices
        # High humidity + High Temp = Fungal Risk
        df['fungal_risk_index'] = (df['humidity'] * df['temperature']) / 100
        
        # Water Stress
        df['water_stress_index'] = (1 - df['soil_moisture']) * (df['temperature'] / 30)
        
        # Pest Vulnerability
        # Closer to water + High Temp = Pest Risk
        df['pest_habitat_suitability'] = (1 / (df['dist_to_water'] + 100)) * df['temperature']
        
        # Crop Health
        df['crop_health_score'] = df['ndvi'] * df['soil_moisture']
        
        # Historical Pressure
        df['pest_pressure_history'] = df['pest_reports_5km'] / (df['days_since_last_report'] + 1)
        
        # Define feature columns (exclude identifiers and target)
        exclude_cols = ['cell_id', 'lat', 'lng', 'risk_score', 
                       'crop_type', 'pest_pressure', 'crop_stage']  # Use encoded versions
        
        self.feature_names = [col for col in df.columns if col not in exclude_cols]
        
        X = df[self.feature_names]
        y = df['risk_score']
        
        print(f"SUCCESS: Prepared {len(self.feature_names)} features")
        print(f"  Feature list: {self.feature_names[:10]}... (showing first 10)")
        
        return X, y
    
    def train(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        test_size: float = 0.15,
        val_size: float = 0.15,
        cv_folds: int = 5
    ) -> Dict:
        """
        Train LightGBM model with cross-validation
        
        Args:
            X: Feature matrix
            y: Target variable
            test_size: Proportion for test set
            val_size: Proportion for validation set (from remaining data)
            cv_folds: Number of cross-validation folds
        
        Returns:
            Dictionary with training metrics and model
        """
        print("\n" + "=" * 60)
        print("Training LightGBM Regression Model (Agricultural Risk)")
        print("=" * 60)
        
        # Split data: train/val/test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=pd.cut(y, bins=[0, 40, 60, 80, 100])
        )
        
        val_size_adjusted = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=42,
            stratify=pd.cut(y_temp, bins=[0, 40, 60, 80, 100])
        )
        
        print(f"\nData Split:")
        print(f"  Training:   {len(X_train)} samples ({len(X_train)/len(X)*100:.1f}%)")
        print(f"  Validation: {len(X_val)} samples ({len(X_val)/len(X)*100:.1f}%)")
        print(f"  Test:       {len(X_test)} samples ({len(X_test)/len(X)*100:.1f}%)")
        
        # Create LightGBM datasets
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.feature_names)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data, feature_name=self.feature_names)
        
        # LightGBM parameters for regression
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'max_depth': -1,
            'min_data_in_leaf': 20,
            'lambda_l1': 0.1,
            'lambda_l2': 0.1,
            'verbose': -1,
            'seed': 42
        }
        
        print("\nTraining model...")
        print(f"Parameters: {params}")
        
        # Train model
        callbacks = [
            lgb.early_stopping(stopping_rounds=50, verbose=False),
            lgb.log_evaluation(period=100)
        ]
        
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=1000,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'valid'],
            callbacks=callbacks
        )
        
        print(f"\nSUCCESS: Model trained with {self.model.num_trees()} trees")
        
        # Evaluate on validation set
        print("\nValidation Set Performance:")
        y_val_pred = self.model.predict(X_val, num_iteration=self.model.best_iteration)
        val_metrics = self._calculate_metrics(y_val, y_val_pred)
        self._print_metrics(val_metrics)
        
        # Evaluate on test set
        print("\nTest Set Performance:")
        y_test_pred = self.model.predict(X_test, num_iteration=self.model.best_iteration)
        test_metrics = self._calculate_metrics(y_test, y_test_pred)
        self._print_metrics(test_metrics)
        
        # Cross-validation on training set
        print(f"\n{cv_folds}-Fold Cross-Validation on Training Set...")
        cv_scores = self._cross_validate(X_train, y_train, cv_folds)
        print(f"  CV RMSE: {cv_scores['rmse_mean']:.3f} (+/- {cv_scores['rmse_std']:.3f})")
        print(f"  CV MAE:  {cv_scores['mae_mean']:.3f} (+/- {cv_scores['mae_std']:.3f})")
        print(f"  CV R2:   {cv_scores['r2_mean']:.3f} (+/- {cv_scores['r2_std']:.3f})")
        
        # Feature importance
        print("\nTop 10 Most Important Features:")
        importance = self.model.feature_importance(importance_type='gain')
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        for idx, row in importance_df.head(10).iterrows():
            print(f"  {row['feature']:<30} {row['importance']:>10.1f}")
        
        # Store metadata
        self.metadata = {
            'model_version': 'v2.0-agri',
            'training_date': datetime.now().isoformat(),
            'model_type': 'LightGBM Regressor (Agricultural)',
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'test_samples': len(X_test),
            'num_features': len(self.feature_names),
            'num_trees': self.model.num_trees(),
            'best_iteration': self.model.best_iteration,
            'validation_rmse': float(val_metrics['rmse']),
            'validation_mae': float(val_metrics['mae']),
            'validation_r2': float(val_metrics['r2']),
            'test_rmse': float(test_metrics['rmse']),
            'test_mae': float(test_metrics['mae']),
            'test_r2': float(test_metrics['r2']),
            'cv_rmse_mean': float(cv_scores['rmse_mean']),
            'cv_rmse_std': float(cv_scores['rmse_std']),
            'features': self.feature_names,
            'feature_importance': importance_df.to_dict('records'),
            'label_encoders': {k: list(v.classes_) for k, v in self.label_encoders.items()}
        }
        
        return {
            'model': self.model,
            'val_metrics': val_metrics,
            'test_metrics': test_metrics,
            'cv_scores': cv_scores,
            'feature_importance': importance_df,
            'metadata': self.metadata
        }
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict:
        """Calculate regression metrics"""
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # Domain-specific metrics
        # Critical-risk precision: Of predicted critical-risk (>80), what % were actually critical?
        critical_risk_pred = y_pred > 80
        critical_risk_true = y_true > 80
        
        if critical_risk_pred.sum() > 0:
            critical_risk_precision = (critical_risk_pred & critical_risk_true).sum() / critical_risk_pred.sum()
        else:
            critical_risk_precision = 0.0
        
        # Critical-risk recall: Of actual critical-risk, what % were predicted critical-risk?
        if critical_risk_true.sum() > 0:
            critical_risk_recall = (critical_risk_pred & critical_risk_true).sum() / critical_risk_true.sum()
        else:
            critical_risk_recall = 0.0
        
        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'critical_risk_precision': critical_risk_precision,
            'critical_risk_recall': critical_risk_recall
        }
    
    def _print_metrics(self, metrics: Dict):
        """Print metrics in formatted way"""
        print(f"  RMSE: {metrics['rmse']:.3f}")
        print(f"  MAE:  {metrics['mae']:.3f}")
        print(f"  R2:   {metrics['r2']:.3f}")
        print(f"  Critical-Risk Precision: {metrics['critical_risk_precision']:.3f}")
        print(f"  Critical-Risk Recall:    {metrics['critical_risk_recall']:.3f}")
    
    def _cross_validate(self, X: pd.DataFrame, y: pd.Series, cv_folds: int) -> Dict:
        """Perform k-fold cross-validation"""
        kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        rmse_scores = []
        mae_scores = []
        r2_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X), 1):
            X_fold_train, X_fold_val = X.iloc[train_idx], X.iloc[val_idx]
            y_fold_train, y_fold_val = y.iloc[train_idx], y.iloc[val_idx]
            
            train_data = lgb.Dataset(X_fold_train, label=y_fold_train)
            val_data = lgb.Dataset(X_fold_val, label=y_fold_val, reference=train_data)
            
            params = {
                'objective': 'regression',
                'metric': 'rmse',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'verbose': -1,
                'seed': 42
            }
            
            model = lgb.train(
                params,
                train_data,
                num_boost_round=300,
                valid_sets=[val_data],
                callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
            )
            
            y_pred = model.predict(X_fold_val, num_iteration=model.best_iteration)
            
            rmse_scores.append(np.sqrt(mean_squared_error(y_fold_val, y_pred)))
            mae_scores.append(mean_absolute_error(y_fold_val, y_pred))
            r2_scores.append(r2_score(y_fold_val, y_pred))
        
        return {
            'rmse_mean': np.mean(rmse_scores),
            'rmse_std': np.std(rmse_scores),
            'mae_mean': np.mean(mae_scores),
            'mae_std': np.std(mae_scores),
            'r2_mean': np.mean(r2_scores),
            'r2_std': np.std(r2_scores)
        }
    
    def save_model(self, filename: str = 'risk_model_v1.pkl'):
        """
        Save trained model and metadata to disk
        
        Args:
            filename: Output filename (saved to backend/models/trained/)
        """
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        models_dir = Path(__file__).parent.parent / 'models' / 'trained'
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model using joblib
        model_path = models_dir / filename
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'label_encoders': self.label_encoders
        }, model_path)
        
        print(f"\nSUCCESS: Model saved to {model_path}")
        print(f"  File size: {model_path.stat().st_size / 1024:.1f} KB")
        
        # Save metadata as JSON
        metadata_path = models_dir / filename.replace('.pkl', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"SUCCESS: Metadata saved to {metadata_path}")
        
        return model_path, metadata_path


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("Sentry Model Training Pipeline (Agriculture)")
    print("=" * 60)
    
    # Initialize trainer
    trainer = ModelTrainer()
    
    # Load data
    df = trainer.load_data()
    
    # Prepare features
    X, y = trainer.prepare_features(df)
    
    # Train model
    results = trainer.train(X, y, test_size=0.15, val_size=0.15, cv_folds=5)
    
    # Save model
    model_path, metadata_path = trainer.save_model('risk_model_v1.pkl')
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Model saved to: {model_path}")
    print(f"Metadata saved to: {metadata_path}")
    print(f"\nFinal Performance:")
    print(f"  Test RMSE: {results['test_metrics']['rmse']:.3f}")
    print(f"  Test MAE:  {results['test_metrics']['mae']:.3f}")
    print(f"  Test R2:   {results['test_metrics']['r2']:.3f}")
    print("\nNext steps:")
    print("  1. Review model performance metrics")
    print("  2. Update backend/models/risk_model.py to load this model")
    print("  3. Test predictions with real satellite data")
    print("=" * 60)


if __name__ == '__main__':
    main()
