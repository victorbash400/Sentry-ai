import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path
import os
import json
from datetime import datetime

class InsuranceModelTrainer:
    """
    Trainer for Insurance Risk Model.
    Separates training logic from inference logic.
    """
    
    def __init__(self, data_path: str = None):
        if data_path:
            self.data_path = Path(data_path)
        else:
            self.data_path = Path(__file__).parent.parent / 'data' / 'insurance_training_data.csv'
            
        self.model = None
        self.metadata = {}
        
    def load_data(self):
        """Load training data"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found at {self.data_path}")
            
        print(f"Loading data from {self.data_path}...")
        return pd.read_csv(self.data_path)
        
    def train(self):
        """Train the model"""
        df = self.load_data()
        
        features = ['agri_risk_score', 'claims_history_index', 'yield_stability', 
                   'weather_volatility', 'market_stability', 'soil_quality']
        target = 'insurance_risk_score'
        
        X = df[features]
        y = df[target]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print("Training Random Forest Regressor...")
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        score = self.model.score(X_test, y_test)
        print(f"Model R^2 Score: {score:.4f}")
        
        self.metadata = {
            'r2_score': score,
            'features': features,
            'training_date': datetime.now().isoformat(),
            'n_samples': len(df)
        }
        
        return score
        
    def save_model(self, filename: str = 'insurance_model.joblib'):
        """Save trained model to backend/models/trained/"""
        if self.model is None:
            raise Exception("Model not trained")
            
        # Save to backend/models/trained/ to match other models
        output_dir = Path(__file__).parent.parent / 'models' / 'trained'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        joblib.dump(self.model, output_path)
        
        # Also save metadata
        meta_path = output_dir / filename.replace('.joblib', '_metadata.json')
        with open(meta_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
        print(f"Model saved to {output_path}")
        return str(output_path)

if __name__ == "__main__":
    trainer = InsuranceModelTrainer()
    trainer.train()
    trainer.save_model()
