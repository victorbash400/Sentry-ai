"""
Test Synthetic Data Generator
Validates data quality, distributions, correlations, and feature engineering
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.synthetic_data_generator import SyntheticDataGenerator


class TestSyntheticDataGenerator:
    """Test suite for synthetic data generation"""
    
    @pytest.fixture
    def generator(self):
        """Create generator with small sample size for testing"""
        return SyntheticDataGenerator(n_samples=1000, seed=42)
    
    @pytest.fixture
    def generated_data(self, generator):
        """Generate data for tests"""
        return generator.generate()
    
    def test_generator_initialization(self, generator):
        """Test generator initializes correctly"""
        assert generator.n_samples == 1000
        assert generator.seed == 42
        assert len(generator.parks) == 5
        assert 'Tsavo East' in generator.parks
        assert 'Maasai Mara' in generator.parks
    
    def test_data_shape(self, generated_data):
        """Test generated data has correct shape"""
        assert len(generated_data) == 1000
        # Should have at least 20 feature columns + identifiers + target
        assert len(generated_data.columns) >= 22
    
    def test_required_columns(self, generated_data):
        """Test all required columns are present"""
        required_cols = [
            'cell_id', 'lat', 'lng', 'risk_score',
            'ndvi', 'vegetation_type',
            'dist_to_boundary', 'dist_to_water', 'dist_to_road', 'dist_to_settlement',
            'incidents_5km_radius', 'days_since_last_incident', 'seasonal_incident_rate',
            'moon_illumination', 'season', 'day_of_week',
            'elevation', 'slope', 'terrain_ruggedness',
            'elephant_migration_route', 'breeding_season', 'watering_pattern'
        ]
        
        for col in required_cols:
            assert col in generated_data.columns, f"Missing column: {col}"
    
    def test_risk_score_range(self, generated_data):
        """Test risk scores are in valid range [0, 100]"""
        assert generated_data['risk_score'].min() >= 0
        assert generated_data['risk_score'].max() <= 100
        assert generated_data['risk_score'].notna().all()
    
    def test_risk_distribution(self, generated_data):
        """Test risk score distribution matches expected proportions"""
        df = generated_data
        
        high_risk = len(df[df['risk_score'] >= 80])
        medium_risk = len(df[(df['risk_score'] >= 60) & (df['risk_score'] < 80)])
        low_risk = len(df[(df['risk_score'] >= 40) & (df['risk_score'] < 60)])
        safe = len(df[df['risk_score'] < 40])
        
        total = len(df)
        
        # Allow 5% tolerance
        assert 0.10 <= high_risk / total <= 0.20, f"High risk: {high_risk/total:.2%}"
        assert 0.20 <= medium_risk / total <= 0.30, f"Medium risk: {medium_risk/total:.2%}"
        assert 0.25 <= low_risk / total <= 0.35, f"Low risk: {low_risk/total:.2%}"
        assert 0.25 <= safe / total <= 0.35, f"Safe: {safe/total:.2%}"
    
    def test_geographic_bounds(self, generated_data):
        """Test coordinates are within Kenyan park boundaries"""
        df = generated_data
        
        # Kenya latitude range: approximately -5 to 5
        assert df['lat'].min() >= -5
        assert df['lat'].max() <= 5
        
        # Kenya longitude range: approximately 34 to 42
        assert df['lng'].min() >= 34
        assert df['lng'].max() <= 42
    
    def test_ndvi_range(self, generated_data):
        """Test NDVI values are in valid range [-0.2, 0.9]"""
        ndvi = generated_data['ndvi']
        assert ndvi.min() >= -0.2, f"NDVI too low: {ndvi.min()}"
        assert ndvi.max() <= 0.9, f"NDVI too high: {ndvi.max()}"
    
    def test_ndvi_risk_correlation(self, generated_data):
        """Test NDVI has negative correlation with risk (lower vegetation = higher risk)"""
        correlation = generated_data['ndvi'].corr(generated_data['risk_score'])
        assert correlation < -0.3, f"NDVI-risk correlation too weak: {correlation:.3f}"
    
    def test_vegetation_type_consistency(self, generated_data):
        """Test vegetation type matches NDVI values"""
        df = generated_data
        
        # Check sparse vegetation has low NDVI
        sparse = df[df['vegetation_type'] == 'sparse']
        if len(sparse) > 0:
            assert sparse['ndvi'].mean() < 0.3, "Sparse vegetation should have low NDVI"
        
        # Check forest has high NDVI
        forest = df[df['vegetation_type'] == 'forest']
        if len(forest) > 0:
            assert forest['ndvi'].mean() > 0.5, "Forest should have high NDVI"
    
    def test_proximity_features_positive(self, generated_data):
        """Test all distance features are positive"""
        distance_cols = ['dist_to_boundary', 'dist_to_water', 'dist_to_road', 'dist_to_settlement']
        
        for col in distance_cols:
            assert (generated_data[col] > 0).all(), f"{col} has non-positive values"
    
    def test_boundary_distance_correlation(self, generated_data):
        """Test distance to boundary has negative correlation with risk"""
        correlation = generated_data['dist_to_boundary'].corr(generated_data['risk_score'])
        assert correlation < -0.4, f"Boundary distance correlation too weak: {correlation:.3f}"
    
    def test_historical_incidents_correlation(self, generated_data):
        """Test historical incidents correlate positively with risk"""
        correlation = generated_data['incidents_5km_radius'].corr(generated_data['risk_score'])
        assert correlation > 0.5, f"Incidents correlation too weak: {correlation:.3f}"
    
    def test_days_since_incident_correlation(self, generated_data):
        """Test days since last incident has negative correlation (recent = higher risk)"""
        correlation = generated_data['days_since_last_incident'].corr(generated_data['risk_score'])
        assert correlation < -0.3, f"Days since incident correlation wrong sign: {correlation:.3f}"
    
    def test_temporal_features_range(self, generated_data):
        """Test temporal features are in valid ranges"""
        df = generated_data
        
        # Moon illumination: 0-1
        assert df['moon_illumination'].min() >= 0
        assert df['moon_illumination'].max() <= 1
        
        # Day of week: 0-6
        assert df['day_of_week'].min() >= 0
        assert df['day_of_week'].max() <= 6
        
        # Season: only wet or dry
        assert set(df['season'].unique()).issubset({'wet', 'dry'})
    
    def test_topographical_features_realistic(self, generated_data):
        """Test topographical features are realistic"""
        df = generated_data
        
        # Elevation in Kenya: 200-5500 meters
        assert df['elevation'].min() >= 200
        assert df['elevation'].max() <= 5500
        
        # Slope: 0-60 degrees
        assert df['slope'].min() >= 0
        assert df['slope'].max() <= 60
        
        # Terrain ruggedness: 0.5-10
        assert df['terrain_ruggedness'].min() >= 0.5
        assert df['terrain_ruggedness'].max() <= 10
    
    def test_slope_risk_correlation(self, generated_data):
        """Test slope has negative correlation with risk (flat = easier access)"""
        correlation = generated_data['slope'].corr(generated_data['risk_score'])
        assert correlation < -0.1, f"Slope correlation unexpected: {correlation:.3f}"
    
    def test_species_features_binary(self, generated_data):
        """Test binary species features are 0 or 1"""
        df = generated_data
        
        assert set(df['elephant_migration_route'].unique()).issubset({0, 1})
        assert set(df['breeding_season'].unique()).issubset({0, 1})
    
    def test_watering_pattern_categories(self, generated_data):
        """Test watering pattern has expected categories"""
        expected = {'regular', 'seasonal', 'rare'}
        actual = set(generated_data['watering_pattern'].unique())
        assert actual == expected, f"Unexpected watering patterns: {actual}"
    
    def test_missing_values_limited(self, generated_data):
        """Test missing values are limited to realistic amounts (<5%)"""
        df = generated_data
        
        for col in df.columns:
            missing_pct = df[col].isna().sum() / len(df)
            assert missing_pct <= 0.05, f"{col} has {missing_pct:.1%} missing (>5%)"
    
    def test_target_variable_no_missing(self, generated_data):
        """Test risk_score has no missing values"""
        assert generated_data['risk_score'].notna().all(), "Target variable has missing values"
    
    def test_cell_id_uniqueness(self, generated_data):
        """Test all cell IDs are unique"""
        assert generated_data['cell_id'].nunique() == len(generated_data)
    
    def test_cell_id_format(self, generated_data):
        """Test cell IDs follow expected format"""
        sample_id = generated_data['cell_id'].iloc[0]
        assert sample_id.startswith('cell-'), f"Cell ID format unexpected: {sample_id}"
    
    def test_data_types(self, generated_data):
        """Test columns have expected data types"""
        df = generated_data
        
        # Numeric columns
        numeric_cols = ['lat', 'lng', 'risk_score', 'ndvi', 'dist_to_boundary', 
                       'elevation', 'slope', 'moon_illumination']
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric"
        
        # Integer columns
        int_cols = ['incidents_5km_radius', 'days_since_last_incident', 'day_of_week',
                   'elephant_migration_route', 'breeding_season']
        for col in int_cols:
            assert pd.api.types.is_integer_dtype(df[col]), f"{col} is not integer"
        
        # String columns
        str_cols = ['cell_id', 'vegetation_type', 'season', 'watering_pattern']
        for col in str_cols:
            assert pd.api.types.is_object_dtype(df[col]), f"{col} is not string/object"
    
    def test_feature_variance(self, generated_data):
        """Test features have sufficient variance (not constant)"""
        df = generated_data
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col not in ['elephant_migration_route', 'breeding_season', 'dry_season']:
                variance = df[col].var()
                assert variance > 0, f"{col} has no variance (constant values)"
    
    def test_reproducibility(self, generator):
        """Test generator produces same data with same seed"""
        df1 = generator.generate()
        
        # Create new generator with same seed
        generator2 = SyntheticDataGenerator(n_samples=1000, seed=42)
        df2 = generator2.generate()
        
        # Check risk scores match
        assert df1['risk_score'].equals(df2['risk_score']), "Reproducibility failed"
    
    def test_csv_save_and_load(self, generator, tmp_path):
        """Test data can be saved and loaded from CSV"""
        df = generator.generate()
        
        # Save to temporary file
        output_file = tmp_path / "test_training_data.csv"
        generator.save_csv(df, str(output_file))
        
        # Load and compare
        df_loaded = pd.read_csv(output_file)
        
        assert len(df_loaded) == len(df)
        assert list(df_loaded.columns) == list(df.columns)
        
        # Check a few values match
        assert df_loaded['risk_score'].mean() == pytest.approx(df['risk_score'].mean(), rel=0.01)
    
    def test_high_risk_zones_have_expected_characteristics(self, generated_data):
        """Test high-risk zones have expected feature patterns"""
        high_risk = generated_data[generated_data['risk_score'] >= 80]
        
        if len(high_risk) > 0:
            # High risk should have:
            # - Lower NDVI (sparse vegetation)
            assert high_risk['ndvi'].mean() < generated_data['ndvi'].mean()
            
            # - Closer to boundary
            assert high_risk['dist_to_boundary'].mean() < generated_data['dist_to_boundary'].mean()
            
            # - More incidents
            assert high_risk['incidents_5km_radius'].mean() > generated_data['incidents_5km_radius'].mean()
    
    def test_safe_zones_have_expected_characteristics(self, generated_data):
        """Test safe zones have expected feature patterns"""
        safe = generated_data[generated_data['risk_score'] < 40]
        
        if len(safe) > 0:
            # Safe zones should have:
            # - Higher NDVI (more vegetation)
            assert safe['ndvi'].mean() > generated_data['ndvi'].mean()
            
            # - Farther from boundary
            assert safe['dist_to_boundary'].mean() > generated_data['dist_to_boundary'].mean()
            
            # - Fewer incidents
            assert safe['incidents_5km_radius'].mean() < generated_data['incidents_5km_radius'].mean()
    
    def test_large_dataset_generation(self):
        """Test can generate large dataset (10k samples)"""
        generator = SyntheticDataGenerator(n_samples=10000, seed=42)
        df = generator.generate()
        
        assert len(df) == 10000
        assert df['risk_score'].notna().all()
    
    def test_statistical_summary(self, generated_data):
        """Test statistical summary makes sense"""
        df = generated_data
        
        # Print summary for inspection
        print("\n=== Data Summary ===")
        print(df[['risk_score', 'ndvi', 'dist_to_boundary', 'incidents_5km_radius']].describe())
        
        # Basic sanity checks
        assert df['risk_score'].mean() > 30, "Mean risk score too low"
        assert df['risk_score'].mean() < 70, "Mean risk score too high"
        assert df['risk_score'].std() > 20, "Risk score variance too low"


def test_main_execution():
    """Test main() function runs without errors"""
    from data.synthetic_data_generator import main
    
    # This should print output and generate data
    # We're just testing it doesn't crash
    try:
        main()
        assert True
    except Exception as e:
        pytest.fail(f"main() raised exception: {str(e)}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
