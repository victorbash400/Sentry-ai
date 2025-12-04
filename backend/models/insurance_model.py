import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import os
import json

class InsuranceRiskModel:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InsuranceRiskModel, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.is_loaded = False
        return cls._instance
    
    def predict(self, features: dict) -> float:
        """
        Predict insurance risk score
        features: dict containing 'agri_risk_score', 'claims_history_index', etc.
        """
        if not self.is_loaded or self.model is None:
            raise Exception("Model not loaded")
            
        # Input Validation
        required_features = ['agri_risk_score', 'claims_history_index', 'yield_stability', 
                           'weather_volatility', 'market_stability', 'soil_quality']
        
        for feature in required_features:
            if feature not in features:
                raise ValueError(f"Missing required feature: {feature}")
            
            val = features[feature]
            if feature == 'agri_risk_score':
                if not (0 <= val <= 100):
                    raise ValueError(f"agri_risk_score must be between 0 and 100, got {val}")
            else:
                if not (0 <= val <= 1.0):
                    # Allow small epsilon for floating point issues, or just clamp?
                    # Strict validation for now to catch bugs
                    if not (-0.1 <= val <= 1.1): # Loose bounds
                         print(f"WARNING: Feature {feature} value {val} out of expected 0-1 range")

        # Ensure feature order matches training
        input_data = pd.DataFrame([features], columns=required_features)
        prediction = self.model.predict(input_data)[0]
        return float(prediction)
    
    def load(self, filename: str = 'insurance_model.joblib'):
        """Load model from backend/models/trained/"""
        # Look in trained directory first
        trained_path = Path(__file__).parent / 'trained' / filename
        
        # Fallback to current directory for backward compatibility (if needed)
        legacy_path = Path(__file__).parent / filename
        
        if trained_path.exists():
            full_path = trained_path
        elif legacy_path.exists():
            full_path = legacy_path
        else:
            print(f"Model file not found at {trained_path} or {legacy_path}")
            return False
            
        try:
            self.model = joblib.load(full_path)
            self.is_loaded = True
            print(f"Insurance model loaded from {full_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

def get_insurance_model():
    return InsuranceRiskModel()
