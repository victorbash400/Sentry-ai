"""
Synthetic Training Data Generator for Agricultural Risk Model
Generates realistic 10k row CSV dataset with correlated agricultural features
"""

import numpy as np
import pandas as pd
from datetime import datetime
import random
from pathlib import Path


class AgriculturalDataGenerator:
    """Generate realistic training data for agricultural pest/disease risk prediction"""
    
    def __init__(self, n_samples: int = 10000, seed: int = 42):
        """
        Initialize generator
        
        Args:
            n_samples: Number of training samples to generate
            seed: Random seed for reproducibility
        """
        self.n_samples = n_samples
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        # Define Kenyan Agricultural Regions (approximate boundaries)
        self.regions = {
            'Rift Valley': {'lat_range': (0.0, 1.0), 'lng_range': (35.0, 36.0)},
            'Central': {'lat_range': (-1.0, -0.3), 'lng_range': (36.5, 37.5)},
            'Nyanza': {'lat_range': (-1.0, 0.0), 'lng_range': (34.0, 35.0)},
            'Western': {'lat_range': (0.0, 1.0), 'lng_range': (34.0, 35.0)},
            'Coast': {'lat_range': (-4.0, -3.0), 'lng_range': (39.0, 40.0)}
        }
    
    def generate(self) -> pd.DataFrame:
        """
        Generate complete training dataset
        
        Returns:
            DataFrame with all features and target variable
        """
        print(f"Generating {self.n_samples} synthetic agricultural training samples...")
        
        # Generate risk distribution first (determines other features)
        risk_scores = self._generate_risk_distribution()
        
        # Generate geographic features
        locations = self._generate_locations()
        
        # Generate correlated features based on risk scores
        data = {
            'cell_id': [f'cell-{i:05d}' for i in range(self.n_samples)],
            'lat': locations[:, 0],
            'lng': locations[:, 1],
            'risk_score': risk_scores
        }
        
        # Add crop features (correlated with risk)
        crop_data = self._generate_crop_features(risk_scores)
        data.update(crop_data)
        
        # Add environmental features (key risk indicators)
        env_data = self._generate_environmental_features(risk_scores)
        data.update(env_data)
        
        # Add historical pest features
        historical_data = self._generate_historical_features(risk_scores)
        data.update(historical_data)
        
        # Add weather features
        weather_data = self._generate_weather_features(risk_scores)
        data.update(weather_data)
        
        # Add topographical features
        topo_data = self._generate_topographical_features(risk_scores, locations)
        data.update(topo_data)
        
        # Add pest-specific features
        pest_data = self._generate_pest_features(risk_scores)
        data.update(pest_data)
        
        df = pd.DataFrame(data)
        
        # Add some realistic noise and missing values
        df = self._add_noise_and_missing(df)
        
        print(f"SUCCESS: Generated {len(df)} samples")
        print(f"  Critical Risk (80-100): {len(df[df.risk_score >= 80])}")
        print(f"  High Risk (60-80): {len(df[(df.risk_score >= 60) & (df.risk_score < 80)])}")
        print(f"  Medium Risk (40-60): {len(df[(df.risk_score >= 40) & (df.risk_score < 60)])}")
        print(f"  Low Risk (0-40): {len(df[df.risk_score < 40])}")
        
        return df
    
    def _generate_risk_distribution(self) -> np.ndarray:
        """
        Generate risk scores with realistic distribution
        15% critical, 25% high, 30% medium, 30% low
        """
        n_critical = int(self.n_samples * 0.15)      # 80-100
        n_high = int(self.n_samples * 0.25)          # 60-80
        n_medium = int(self.n_samples * 0.30)        # 40-60
        n_low = self.n_samples - n_critical - n_high - n_medium  # 0-40
        
        critical_risk = np.random.uniform(80, 100, n_critical)
        high_risk = np.random.uniform(60, 80, n_high)
        medium_risk = np.random.uniform(40, 60, n_medium)
        low_risk = np.random.uniform(0, 40, n_low)
        
        risk_scores = np.concatenate([critical_risk, high_risk, medium_risk, low_risk])
        np.random.shuffle(risk_scores)
        
        return risk_scores
    
    def _generate_locations(self) -> np.ndarray:
        """Generate realistic lat/lng coordinates within Kenyan agricultural regions"""
        locations = []
        
        region_names = list(self.regions.keys())
        
        for _ in range(self.n_samples):
            # Randomly select region
            region = self.regions[random.choice(region_names)]
            
            lat = np.random.uniform(region['lat_range'][0], region['lat_range'][1])
            lng = np.random.uniform(region['lng_range'][0], region['lng_range'][1])
            
            locations.append([lat, lng])
        
        return np.array(locations)
    
    def _generate_crop_features(self, risk_scores: np.ndarray) -> dict:
        """
        Generate crop features
        Certain crops might be more susceptible to specific pests/diseases
        """
        n = len(risk_scores)
        
        # NDVI: Healthy crops have high NDVI, but stressed crops (high risk) might have lower
        # However, dense monocultures (high NDVI) can also be high risk for rapid spread
        # Let's assume: High Risk -> stressed crops (lower NDVI) OR very dense canopy (high NDVI)
        # Simplified: High risk correlates with slightly lower NDVI (stress)
        base_ndvi = 0.8 - (risk_scores / 100) * 0.3  # Range: 0.5 to 0.8
        ndvi = base_ndvi + np.random.normal(0, 0.08, n)
        ndvi = np.clip(ndvi, 0.1, 0.9)
        
        # Crop type
        crop_types = []
        for _ in range(n):
            crop_types.append(random.choice(['Maize', 'Wheat', 'Coffee', 'Tea', 'Vegetables']))
            
        return {
            'ndvi': np.round(ndvi, 3),
            'crop_type': crop_types
        }
    
    def _generate_environmental_features(self, risk_scores: np.ndarray) -> dict:
        """
        Generate environmental features strongly correlated with risk
        """
        n = len(risk_scores)
        
        # Soil Moisture: High moisture -> fungal risk (High Risk)
        # Risk 100 -> High moisture, Risk 0 -> Low/Optimal
        base_moisture = (risk_scores / 100) * 0.8
        soil_moisture = base_moisture + np.random.normal(0, 0.1, n)
        soil_moisture = np.clip(soil_moisture, 0.0, 1.0)
        
        # Distance to water: Closer to water -> higher humidity/pest risk
        base_water = 5000 - (risk_scores / 100) * 4000
        dist_to_water = base_water + np.random.exponential(800, n)
        dist_to_water = np.clip(dist_to_water, 50, 20000)
        
        return {
            'soil_moisture': np.round(soil_moisture, 2),
            'dist_to_water': np.round(dist_to_water, 1)
        }
    
    def _generate_historical_features(self, risk_scores: np.ndarray) -> dict:
        """
        Generate historical pest/disease report features
        """
        n = len(risk_scores)
        
        # Reports in 5km radius: Higher risk -> more reports
        base_reports = (risk_scores / 100) * 15
        pest_reports = np.random.poisson(base_reports)
        pest_reports = np.clip(pest_reports, 0, 50)
        
        # Days since last report: Higher risk -> more recent
        base_days = 350 - (risk_scores / 100) * 330
        days_since = base_days + np.random.exponential(30, n)
        days_since = np.clip(days_since, 1, 365).astype(int)
        
        return {
            'pest_reports_5km': pest_reports.astype(int),
            'days_since_last_report': days_since
        }
    
    def _generate_weather_features(self, risk_scores: np.ndarray) -> dict:
        """
        Generate weather features (Temperature, Humidity)
        """
        n = len(risk_scores)
        
        # Humidity: High humidity -> High risk (fungal/pest)
        base_humidity = 40 + (risk_scores / 100) * 50
        humidity = base_humidity + np.random.normal(0, 5, n)
        humidity = np.clip(humidity, 20, 100)
        
        # Temperature: Optimal range for pests is often 20-30C
        # We'll simulate a mix, but generally warmer = higher metabolic rate for pests
        base_temp = 15 + (risk_scores / 100) * 15
        temperature = base_temp + np.random.normal(0, 3, n)
        temperature = np.clip(temperature, 10, 40)
        
        return {
            'humidity': np.round(humidity, 1),
            'temperature': np.round(temperature, 1)
        }
    
    def _generate_topographical_features(
        self, 
        risk_scores: np.ndarray, 
        locations: np.ndarray
    ) -> dict:
        """
        Generate topographical features
        """
        n = len(risk_scores)
        
        # Elevation: Varies by location
        base_elevation = np.abs(locations[:, 0]) * 400 + 1000
        elevation = base_elevation + np.random.normal(0, 200, n)
        elevation = np.clip(elevation, 500, 3000)
        
        # Slope: Flatter land (low slope) -> water stagnation -> higher disease risk
        base_slope = 20 - (risk_scores / 100) * 15
        slope = base_slope + np.random.exponential(5, n)
        slope = np.clip(slope, 0, 45)
        
        return {
            'elevation': np.round(elevation, 1),
            'slope': np.round(slope, 1)
        }
    
    def _generate_pest_features(self, risk_scores: np.ndarray) -> dict:
        """
        Generate pest-specific features
        """
        n = len(risk_scores)
        
        # Pest Pressure (Regional load): High risk -> High pressure
        pest_pressure = []
        for risk in risk_scores:
            if risk > 70:
                pest_pressure.append(random.choices(['High', 'Medium', 'Low'], weights=[0.7, 0.2, 0.1])[0])
            elif risk > 40:
                pest_pressure.append(random.choices(['High', 'Medium', 'Low'], weights=[0.2, 0.5, 0.3])[0])
            else:
                pest_pressure.append(random.choices(['High', 'Medium', 'Low'], weights=[0.1, 0.2, 0.7])[0])
        
        # Crop Stage: Vulnerable stages (Flowering, Fruiting) -> Higher Risk
        crop_stage = []
        stages = ['Vegetative', 'Flowering', 'Fruiting', 'Harvesting']
        for risk in risk_scores:
            if risk > 60:
                # High risk often coincides with sensitive stages
                crop_stage.append(random.choices(stages, weights=[0.1, 0.4, 0.4, 0.1])[0])
            else:
                crop_stage.append(random.choice(stages))
        
        return {
            'pest_pressure': pest_pressure,
            'crop_stage': crop_stage
        }
    
    def _add_noise_and_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add realistic noise and missing values
        """
        # Add small noise to continuous features
        continuous_features = ['ndvi', 'soil_moisture', 'dist_to_water', 
                              'humidity', 'temperature', 'elevation', 'slope']
        
        for feature in continuous_features:
            if feature in df.columns:
                noise_scale = df[feature].std() * 0.02  # 2% noise
                df[feature] += np.random.normal(0, noise_scale, len(df))
        
        # Add missing values
        missing_candidates = ['ndvi', 'soil_moisture', 'humidity']
        
        for feature in missing_candidates:
            if feature in df.columns:
                n_missing = int(len(df) * 0.025)  # 2.5% missing
                missing_idx = np.random.choice(len(df), n_missing, replace=False)
                df.loc[missing_idx, feature] = np.nan
        
        # Ensure target variable has no missing values
        df['risk_score'] = df['risk_score'].fillna(df['risk_score'].mean())
        
        # Clip continuous features to valid ranges
        if 'ndvi' in df.columns:
            df['ndvi'] = df['ndvi'].clip(0.0, 1.0)
        if 'soil_moisture' in df.columns:
            df['soil_moisture'] = df['soil_moisture'].clip(0.0, 1.0)
        if 'risk_score' in df.columns:
            df['risk_score'] = df['risk_score'].clip(0.0, 100.0)
        
        return df
    
    def save_csv(self, df: pd.DataFrame, filename: str = 'training_data.csv'):
        """
        Save DataFrame to CSV in data folder
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        output_path = Path(__file__).parent / filename
        df.to_csv(output_path, index=False, float_format='%.3f')
        print(f"SUCCESS: Saved training data to {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Rows: {len(df)}")
        
        return output_path


def main():
    """Generate and save training data"""
    print("=" * 60)
    print("Sentry Agricultural Data Generator")
    print("=" * 60)
    
    generator = AgriculturalDataGenerator(n_samples=10000, seed=42)
    df = generator.generate()
    
    print("\nDataset Statistics:")
    print(df.describe())
    
    print("\nCategorical Feature Distribution:")
    print(f"  Crop Types: {df['crop_type'].value_counts().to_dict()}")
    print(f"  Pest Pressure: {df['pest_pressure'].value_counts().to_dict()}")
    print(f"  Crop Stages: {df['crop_stage'].value_counts().to_dict()}")
    
    print("\nFeature Correlations with Risk Score:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlations = df[numeric_cols].corr()['risk_score'].sort_values(ascending=False)
    print(correlations[1:11])  # Top 10 correlated features
    
    output_path = generator.save_csv(df)
    
    print("\n" + "=" * 60)
    print(f"Training data ready at: {output_path}")
    print("Next steps:")
    print("  1. Review data quality: python -c 'import pandas as pd; print(pd.read_csv(\"backend/data/training_data.csv\").head())'")
    print("  2. Train model: python backend/services/model_trainer.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
