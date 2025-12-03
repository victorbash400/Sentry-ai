"""
Test Feature Extractor
Validates feature extraction from geographic coordinates for model input
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.feature_extractor import FeatureExtractor, get_extractor_instance


class TestFeatureExtractor:
    """Test suite for feature extraction service"""
    
    @pytest.fixture
    def extractor(self):
        """Create feature extractor instance"""
        return FeatureExtractor()
    
    @pytest.fixture
    def sample_cells(self):
        """Create sample grid cells for testing"""
        return [
            {
                'id': 'cell-001',
                'center': {'lat': -2.8, 'lng': 38.9},
                'bounds': {
                    'south': -2.81, 'north': -2.79,
                    'west': 38.89, 'east': 38.91
                }
            },
            {
                'id': 'cell-002',
                'center': {'lat': -2.85, 'lng': 38.95},
                'bounds': {
                    'south': -2.86, 'north': -2.84,
                    'west': 38.94, 'east': 38.96
                }
            }
        ]
    
    @pytest.fixture
    def sample_polygon(self):
        """Create sample polygon for boundary calculations"""
        return [
            {'lat': -2.80, 'lng': 38.90},
            {'lat': -2.80, 'lng': 39.00},
            {'lat': -2.90, 'lng': 39.00},
            {'lat': -2.90, 'lng': 38.90},
            {'lat': -2.80, 'lng': 38.90}
        ]
    
    def test_extractor_initialization(self, extractor):
        """Test extractor initializes correctly"""
        assert extractor.feature_names == []
        assert isinstance(extractor, FeatureExtractor)
    
    def test_singleton_instance(self):
        """Test singleton pattern for extractor"""
        extractor1 = get_extractor_instance()
        extractor2 = get_extractor_instance()
        
        assert extractor1 is extractor2
    
    def test_haversine_distance(self, extractor):
        """Test Haversine distance calculation"""
        # Known distance: Nairobi to Mombasa ~440km
        nairobi_lat, nairobi_lng = -1.286389, 36.817223
        mombasa_lat, mombasa_lng = -4.043477, 39.668206
        
        distance = extractor._haversine_distance(
            nairobi_lat, nairobi_lng,
            mombasa_lat, mombasa_lng
        )
        
        # Should be roughly 440km (440000m)
        assert 400000 < distance < 480000, f"Distance {distance}m seems wrong"
    
    def test_haversine_same_point(self, extractor):
        """Test distance between same point is zero"""
        distance = extractor._haversine_distance(0, 0, 0, 0)
        assert distance == 0
    
    def test_distance_to_polygon_edge(self, extractor, sample_polygon):
        """Test distance calculation to polygon edge"""
        # Point inside polygon
        lat, lng = -2.85, 38.95
        
        distance = extractor._distance_to_polygon_edge(lat, lng, sample_polygon)
        
        assert distance >= 0, "Distance should be non-negative"
        assert distance < 100000, "Distance should be reasonable (<100km)"
    
    def test_distance_to_polygon_corner(self, extractor, sample_polygon):
        """Test distance to polygon from corner point"""
        # Exact corner point
        lat, lng = -2.80, 38.90
        
        distance = extractor._distance_to_polygon_edge(lat, lng, sample_polygon)
        
        # Should be very close to zero (at edge)
        assert distance < 1000, f"Corner should be close to edge: {distance}m"
    
    def test_calculate_ruggedness(self, extractor):
        """Test terrain ruggedness calculation"""
        # Flat terrain (low slope)
        flat_ruggedness = extractor._calculate_ruggedness(5)
        assert 0 <= flat_ruggedness <= 2
        
        # Steep terrain (high slope)
        steep_ruggedness = extractor._calculate_ruggedness(45)
        assert 6 <= steep_ruggedness <= 10
        
        # Maximum slope
        max_ruggedness = extractor._calculate_ruggedness(60)
        assert max_ruggedness == 10
    
    def test_extract_features_structure(self, extractor, sample_cells, sample_polygon):
        """Test extract_features_for_cells returns proper structure"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        assert len(cells_with_features) == len(sample_cells)
        
        for cell in cells_with_features:
            assert 'id' in cell
            assert 'center' in cell
            assert 'features' in cell
            assert isinstance(cell['features'], dict)
    
    def test_satellite_features_extracted(self, extractor, sample_cells, sample_polygon):
        """Test satellite features (NDVI) are extracted"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # NDVI should be present
            assert 'ndvi' in features
            assert -0.2 <= features['ndvi'] <= 0.9
            
            # Vegetation type should be present
            assert 'vegetation_type' in features
            assert features['vegetation_type'] in ['sparse', 'scrub', 'grassland', 'forest']
            
            # Encoded version should exist
            assert 'vegetation_type_encoded' in features
            assert 0 <= features['vegetation_type_encoded'] <= 3
    
    def test_proximity_features_extracted(self, extractor, sample_cells, sample_polygon):
        """Test proximity features are extracted"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # All proximity features should exist
            assert 'dist_to_boundary' in features
            assert 'dist_to_water' in features
            assert 'dist_to_road' in features
            assert 'dist_to_settlement' in features
            
            # All should be positive
            assert features['dist_to_boundary'] > 0
            assert features['dist_to_water'] > 0
            assert features['dist_to_road'] > 0
            assert features['dist_to_settlement'] > 0
    
    def test_temporal_features_extracted(self, extractor, sample_cells, sample_polygon):
        """Test temporal features are extracted"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # Moon illumination
            assert 'moon_illumination' in features
            assert 0 <= features['moon_illumination'] <= 1
            
            # Season
            assert 'season' in features
            assert features['season'] in ['wet', 'dry']
            assert 'season_encoded' in features
            assert features['season_encoded'] in [0, 1]
            
            # Day of week
            assert 'day_of_week' in features
            assert 0 <= features['day_of_week'] <= 6
    
    def test_topographical_features_extracted(self, extractor, sample_cells, sample_polygon):
        """Test topographical features are extracted"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # Elevation
            assert 'elevation' in features
            assert 200 <= features['elevation'] <= 5500
            
            # Slope
            assert 'slope' in features
            assert 0 <= features['slope'] <= 60
            
            # Terrain ruggedness
            assert 'terrain_ruggedness' in features
            assert 0.5 <= features['terrain_ruggedness'] <= 10
    
    def test_species_features_extracted(self, extractor, sample_cells, sample_polygon):
        """Test species-specific features are extracted"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # Migration route
            assert 'elephant_migration_route' in features
            assert features['elephant_migration_route'] in [0, 1]
            
            # Breeding season
            assert 'breeding_season' in features
            assert features['breeding_season'] in [0, 1]
            
            # Watering pattern
            assert 'watering_pattern' in features
            assert features['watering_pattern'] in ['regular', 'seasonal', 'rare']
            assert 'watering_pattern_encoded' in features
            assert 0 <= features['watering_pattern_encoded'] <= 2
    
    def test_derived_features_calculated(self, extractor, sample_cells, sample_polygon):
        """Test derived features are calculated correctly"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # Boundary risk (inverse of distance)
            assert 'boundary_risk' in features
            expected_boundary_risk = 1 / (features['dist_to_boundary'] + 100)
            assert abs(features['boundary_risk'] - expected_boundary_risk) < 0.001
            
            # Water attraction
            assert 'water_attraction' in features
            expected_water_attraction = 1 / (features['dist_to_water'] + 50)
            assert abs(features['water_attraction'] - expected_water_attraction) < 0.001
            
            # Access ease
            assert 'access_ease' in features
            expected_access_ease = 1 / (features['dist_to_road'] + 200)
            assert abs(features['access_ease'] - expected_access_ease) < 0.001
            
            # Isolation score
            assert 'isolation_score' in features
            expected_isolation = (features['dist_to_settlement'] + features['dist_to_road']) / 2000
            assert abs(features['isolation_score'] - expected_isolation) < 0.01
            
            # Dense vegetation binary
            assert 'dense_vegetation' in features
            assert features['dense_vegetation'] in [0, 1]
            if features['ndvi'] > 0.5:
                assert features['dense_vegetation'] == 1
            else:
                assert features['dense_vegetation'] == 0
            
            # Dry season binary
            assert 'dry_season' in features
            assert features['dry_season'] in [0, 1]
            
            # Weekend binary
            assert 'is_weekend' in features
            assert features['is_weekend'] in [0, 1]
            
            # Incident density
            assert 'incident_density' in features
            assert features['incident_density'] >= 0
    
    def test_historical_features_placeholders(self, extractor, sample_cells, sample_polygon):
        """Test historical incident features have placeholder values"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            features = cell['features']
            
            # Historical features should exist with defaults
            assert 'incidents_5km_radius' in features
            assert 'days_since_last_incident' in features
            assert 'seasonal_incident_rate' in features
            
            # Check they're reasonable defaults
            assert features['incidents_5km_radius'] >= 0
            assert features['days_since_last_incident'] > 0
            assert 0 <= features['seasonal_incident_rate'] <= 1
    
    def test_format_for_model_input(self, extractor, sample_cells, sample_polygon):
        """Test formatting features for model input"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        model_inputs = extractor.format_for_model_input(cells_with_features)
        
        assert len(model_inputs) == len(sample_cells)
        
        for model_input in model_inputs:
            assert 'cell_id' in model_input
            assert 'center' in model_input
            assert 'features' in model_input
            
            features = model_input['features']
            
            # Check all required model features are present
            required_features = [
                'ndvi', 'vegetation_type_encoded',
                'dist_to_boundary', 'dist_to_water', 'dist_to_road', 'dist_to_settlement',
                'incidents_5km_radius', 'days_since_last_incident', 'seasonal_incident_rate',
                'moon_illumination', 'season_encoded', 'day_of_week',
                'elevation', 'slope', 'terrain_ruggedness',
                'elephant_migration_route', 'breeding_season', 'watering_pattern_encoded',
                'boundary_risk', 'water_attraction', 'access_ease', 'isolation_score',
                'dense_vegetation', 'dry_season', 'is_weekend', 'incident_density'
            ]
            
            for feature in required_features:
                assert feature in features, f"Missing model feature: {feature}"
    
    def test_vegetation_type_ndvi_consistency(self, extractor, sample_cells, sample_polygon):
        """Test vegetation type matches NDVI ranges"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            ndvi = cell['features']['ndvi']
            veg_type = cell['features']['vegetation_type']
            
            # Check mapping is consistent (with some tolerance for edge cases)
            if veg_type == 'sparse':
                assert ndvi <= 0.25, f"Sparse vegetation has high NDVI: {ndvi}"
            elif veg_type == 'scrub':
                assert 0.15 <= ndvi <= 0.45, f"Scrub has wrong NDVI: {ndvi}"
            elif veg_type == 'grassland':
                assert 0.35 <= ndvi <= 0.65, f"Grassland has wrong NDVI: {ndvi}"
            elif veg_type == 'forest':
                assert ndvi >= 0.55, f"Forest has low NDVI: {ndvi}"
    
    def test_watering_pattern_water_distance_correlation(self, extractor, sample_cells, sample_polygon):
        """Test watering pattern correlates with water distance"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        for cell in cells_with_features:
            water_dist = cell['features']['dist_to_water']
            watering = cell['features']['watering_pattern']
            
            # Check correlation (with tolerance)
            if watering == 'regular':
                assert water_dist < 3000, f"Regular watering far from water: {water_dist}m"
            elif watering == 'rare':
                assert water_dist > 3000, f"Rare watering close to water: {water_dist}m"
    
    def test_date_range_handling(self, extractor, sample_cells, sample_polygon):
        """Test different date ranges are handled correctly"""
        # Test various date ranges
        date_ranges = [
            ("2024-01-01", "2024-03-31"),  # Q1
            ("2024-06-01", "2024-08-31"),  # Mid year
            ("2023-01-01", "2023-12-31"),  # Previous year
        ]
        
        for date_start, date_end in date_ranges:
            cells_with_features = extractor.extract_features_for_cells(
                sample_cells,
                sample_polygon,
                date_start,
                date_end
            )
            
            assert len(cells_with_features) == len(sample_cells)
            
            # Check temporal features are computed
            for cell in cells_with_features:
                assert 'moon_illumination' in cell['features']
                assert 'season' in cell['features']
    
    def test_empty_cells_list(self, extractor, sample_polygon):
        """Test handling of empty cells list"""
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            [],
            sample_polygon,
            date_start,
            date_end
        )
        
        assert len(cells_with_features) == 0
    
    def test_single_cell(self, extractor, sample_polygon):
        """Test extraction for single cell"""
        single_cell = [{
            'id': 'cell-solo',
            'center': {'lat': -2.85, 'lng': 38.95},
            'bounds': {
                'south': -2.86, 'north': -2.84,
                'west': 38.94, 'east': 38.96
            }
        }]
        
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            single_cell,
            sample_polygon,
            date_start,
            date_end
        )
        
        assert len(cells_with_features) == 1
        assert cells_with_features[0]['id'] == 'cell-solo'
    
    def test_large_batch_cells(self, extractor, sample_polygon):
        """Test extraction for larger batch of cells"""
        # Create 20 cells in grid
        cells = []
        for i in range(20):
            lat = -2.80 - (i % 5) * 0.02
            lng = 38.90 + (i // 5) * 0.02
            cells.append({
                'id': f'cell-{i:03d}',
                'center': {'lat': lat, 'lng': lng},
                'bounds': {
                    'south': lat - 0.01, 'north': lat + 0.01,
                    'west': lng - 0.01, 'east': lng + 0.01
                }
            })
        
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            cells,
            sample_polygon,
            date_start,
            date_end
        )
        
        assert len(cells_with_features) == 20
        
        # All should have complete features
        for cell in cells_with_features:
            assert 'features' in cell
            assert len(cell['features']) > 20
    
    def test_park_boundary_vs_polygon_boundary(self, extractor, sample_cells, sample_polygon):
        """Test using separate park boundary vs analysis polygon"""
        # Larger park boundary
        park_boundary = [
            {'lat': -3.00, 'lng': 38.80},
            {'lat': -3.00, 'lng': 39.20},
            {'lat': -2.60, 'lng': 39.20},
            {'lat': -2.60, 'lng': 38.80},
            {'lat': -3.00, 'lng': 38.80}
        ]
        
        date_start = "2024-01-01"
        date_end = "2024-12-31"
        
        cells_with_features = extractor.extract_features_for_cells(
            sample_cells,
            sample_polygon,
            date_start,
            date_end,
            park_boundary=park_boundary
        )
        
        assert len(cells_with_features) == len(sample_cells)
        
        # Distance to boundary should be different from without park boundary
        for cell in cells_with_features:
            assert 'dist_to_boundary' in cell['features']


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
