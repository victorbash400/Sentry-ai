"""
Synthetic Training Data Generator for Insurance Risk Model
Generates realistic dataset for insurance risk assessment based on agricultural factors.
"""

import numpy as np
import pandas as pd
import random
from pathlib import Path

class InsuranceDataGenerator:
    """Generate realistic training data for insurance risk prediction"""
    
    def __init__(self, n_samples: int = 10000, seed: int = 42):
        self.n_samples = n_samples
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
    def generate(self) -> pd.DataFrame:
        """Generate complete training dataset"""
        print(f"Generating {self.n_samples} synthetic insurance training samples...")
        
        # 1. Base Agricultural Risk (0-100) - Primary driver
        # We simulate this as if it came from the agri model
        agri_risk_score = np.random.beta(2, 5, self.n_samples) * 100
        
        # 2. Historical Claims Data
        # Higher agri risk -> higher probability of past claims
        claims_history_index = (agri_risk_score / 100) + np.random.normal(0, 0.1, self.n_samples)
        claims_history_index = np.clip(claims_history_index, 0, 1)
        
        # 3. Crop Yield History (Stability)
        # Lower risk -> more stable yields (higher score)
        yield_stability = 1.0 - (agri_risk_score / 100) + np.random.normal(0, 0.15, self.n_samples)
        yield_stability = np.clip(yield_stability, 0, 1)
        
        # 4. Weather Volatility Index (0-1)
        # Correlated with risk
        weather_volatility = (agri_risk_score / 100) * 0.7 + np.random.uniform(0, 0.3, self.n_samples)
        
        # 5. Market Price Stability (0-1)
        # Independent of physical risk, but affects financial risk
        market_stability = np.random.beta(5, 2, self.n_samples)
        
        # 6. Soil Quality Index (0-1)
        # Inverse to some risk factors
        soil_quality = 1.0 - (agri_risk_score / 100) * 0.5 + np.random.normal(0, 0.1, self.n_samples)
        soil_quality = np.clip(soil_quality, 0, 1)
        
        # Calculate Target: Insurance Risk Score (0-100)
        # Weighted combination of factors + noise
        # Weights: Agri Risk (40%), Claims (20%), Weather (15%), Yield (10%), Market (10%), Soil (5%)
        
        target_score = (
            (agri_risk_score * 0.4) +
            (claims_history_index * 100 * 0.2) +
            (weather_volatility * 100 * 0.15) +
            ((1 - yield_stability) * 100 * 0.1) +
            ((1 - market_stability) * 100 * 0.1) +
            ((1 - soil_quality) * 100 * 0.05)
        )
        
        # Add non-linear effects and noise
        target_score += np.random.normal(0, 5, self.n_samples)
        
        # Insurance specific adjustments (e.g., extreme weather amplifies risk disproportionately)
        extreme_weather_mask = weather_volatility > 0.8
        target_score[extreme_weather_mask] *= 1.2
        
        target_score = np.clip(target_score, 0, 100)
        
        data = {
            'agri_risk_score': np.round(agri_risk_score, 1),
            'claims_history_index': np.round(claims_history_index, 2),
            'yield_stability': np.round(yield_stability, 2),
            'weather_volatility': np.round(weather_volatility, 2),
            'market_stability': np.round(market_stability, 2),
            'soil_quality': np.round(soil_quality, 2),
            'insurance_risk_score': np.round(target_score, 1)
        }
        
        df = pd.DataFrame(data)
        return df

    def save_csv(self, df: pd.DataFrame, filename: str = 'insurance_training_data.csv'):
        output_path = Path(__file__).parent / filename
        df.to_csv(output_path, index=False)
        print(f"SUCCESS: Saved insurance training data to {output_path}")
        return output_path

def main():
    generator = InsuranceDataGenerator()
    df = generator.generate()
    generator.save_csv(df)
    
    print("\nDataset Statistics:")
    print(df.describe())
    
    print("\nCorrelations with Insurance Risk Score:")
    print(df.corr()['insurance_risk_score'].sort_values(ascending=False))

if __name__ == '__main__':
    main()
