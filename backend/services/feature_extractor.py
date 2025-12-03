"""
Feature Extraction Service
Maps user-drawn polygon coordinates to model input features
Extracts satellite data and calculates derived features for prediction
"""

import ee
import math
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import ephem


class FeatureExtractor:
    """
    Extract model features from geographic coordinates
    Bridges gap between user map input and ML model input
    """
    
    def __init__(self):
        """Initialize feature extractor"""
        self.feature_names = []
    
    def extract_features_for_cells(
        self,
        cells: List[Dict],
        polygon: List[Dict[str, float]],
        date_start: str,
        date_end: str,
        park_boundary: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all model features for grid cells
        
        Args:
            cells: List of grid cells with center coordinates
            polygon: User-drawn polygon (for boundary distance)
            date_start: Analysis start date (YYYY-MM-DD)
            date_end: Analysis end date (YYYY-MM-DD)
            park_boundary: Optional park boundary polygon
        
        Returns:
            List of cells with extracted features ready for model prediction
        """
        print(f"\nExtracting features for {len(cells)} cells...")
        
        # Extract satellite features
        cells_with_satellite = self._extract_satellite_features(cells, date_start, date_end)
        
        # Calculate proximity features
        cells_with_proximity = self._calculate_proximity_features(
            cells_with_satellite, polygon, park_boundary
        )
        
        # Add temporal features
        cells_with_temporal = self._add_temporal_features(
            cells_with_proximity, date_start, date_end
        )
        
        # Add topographical features
        cells_with_topo = self._extract_topographical_features(cells_with_temporal)
        
        # Add species features (placeholder for now)
        cells_with_species = self._add_species_features(cells_with_topo)
        
        # Calculate derived features (feature engineering)
        cells_final = self._calculate_derived_features(cells_with_species)
        
        print(f"SUCCESS: Extracted features for {len(cells_final)} cells")
        
        return cells_final
    
    def _extract_satellite_features(
        self,
        cells: List[Dict],
        date_start: str,
        date_end: str
    ) -> List[Dict]:
        """
        Extract NDVI and vegetation features from satellite imagery
        Uses Google Earth Engine Sentinel-2 data
        """
        print("  Extracting satellite features (NDVI, vegetation)...")
        
        # Create GEE points
        points = [
            ee.Geometry.Point([cell['center']['lng'], cell['center']['lat']]) 
            for cell in cells
        ]
        
        # Get Sentinel-2 imagery
        collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(ee.Geometry.MultiPoint(points)) \
            .filterDate(date_start, date_end) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        
        image_count = collection.size().getInfo()
        
        if image_count == 0:
            print("    WARNING: No satellite images available")
            # Return cells with default NDVI
            for cell in cells:
                cell['features'] = {
                    'ndvi': 0.5,  # Median default
                    'vegetation_type': 'grassland'
                }
            return cells
        
        # Calculate median composite
        median = collection.median()
        
        # Extract NDVI for each cell
        results = []
        for cell in cells:
            point = ee.Geometry.Point([cell['center']['lng'], cell['center']['lat']])
            
            try:
                # Calculate NDVI: (NIR - Red) / (NIR + Red)
                nir = median.select('B8')
                red = median.select('B4')
                ndvi = nir.subtract(red).divide(nir.add(red))
                
                ndvi_value = ndvi.sample(point, 30).first().get('NDVI').getInfo()
                ndvi_value = round(ndvi_value, 3) if ndvi_value else 0.5
                
                # Determine vegetation type from NDVI
                if ndvi_value < 0.2:
                    veg_type = 'sparse'
                elif ndvi_value < 0.4:
                    veg_type = 'scrub'
                elif ndvi_value < 0.6:
                    veg_type = 'grassland'
                else:
                    veg_type = 'forest'
                
                cell['features'] = {
                    'ndvi': ndvi_value,
                    'vegetation_type': veg_type,
                    'vegetation_type_encoded': ['sparse', 'scrub', 'grassland', 'forest'].index(veg_type)
                }
            
            except Exception as e:
                print(f"    Error extracting NDVI for {cell['id']}: {str(e)}")
                cell['features'] = {
                    'ndvi': 0.5,
                    'vegetation_type': 'grassland',
                    'vegetation_type_encoded': 2
                }
            
            results.append(cell)
        
        return results
    
    def _calculate_proximity_features(
        self,
        cells: List[Dict],
        polygon: List[Dict],
        park_boundary: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Calculate distance-based features
        - Distance to analysis area boundary
        - Distance to water sources
        - Distance to roads
        - Distance to settlements
        """
        print("  Calculating proximity features...")
        
        # Use user polygon as boundary if no park boundary provided
        if park_boundary is None:
            park_boundary = polygon
        
        for cell in cells:
            lat = cell['center']['lat']
            lng = cell['center']['lng']
            
            # Distance to boundary (closest edge of polygon)
            dist_to_boundary = self._distance_to_polygon_edge(lat, lng, park_boundary)
            
            # Distance to water - Use GEE water datasets
            # For now, estimate based on location (rivers typically in lower elevation)
            # TODO: Integrate real water body datasets
            dist_to_water = self._estimate_water_distance(lat, lng)
            
            # Distance to road - Estimate based on proximity to settlements
            # TODO: Integrate OpenStreetMap road network
            dist_to_road = self._estimate_road_distance(lat, lng)
            
            # Distance to settlement - Estimate from populated areas
            # TODO: Integrate population density grids
            dist_to_settlement = self._estimate_settlement_distance(lat, lng)
            
            cell['features'].update({
                'dist_to_boundary': round(dist_to_boundary, 1),
                'dist_to_water': round(dist_to_water, 1),
                'dist_to_road': round(dist_to_road, 1),
                'dist_to_settlement': round(dist_to_settlement, 1)
            })
        
        return cells
    
    def _add_temporal_features(
        self,
        cells: List[Dict],
        date_start: str,
        date_end: str
    ) -> List[Dict]:
        """
        Add temporal context features
        - Moon phase
        - Season
        - Day of week
        """
        print("  Adding temporal features...")
        
        # Use middle date of analysis period
        start = datetime.strptime(date_start, '%Y-%m-%d')
        end = datetime.strptime(date_end, '%Y-%m-%d')
        middle_date = start + (end - start) / 2
        
        # Calculate moon phase
        moon = ephem.Moon(middle_date)
        moon_illumination = round(moon.phase / 100, 2)  # Convert to 0-1
        
        # Determine season (Kenya has 2 seasons)
        month = middle_date.month
        if month in [12, 1, 2, 3]:
            season = 'dry'
            season_encoded = 0
        elif month in [4, 5]:
            season = 'wet'  # Long rains
            season_encoded = 1
        elif month in [6, 7, 8, 9, 10]:
            season = 'dry'
            season_encoded = 0
        else:  # [11]
            season = 'wet'  # Short rains
            season_encoded = 1
        
        # Day of week
        day_of_week = middle_date.weekday()  # 0=Monday, 6=Sunday
        
        for cell in cells:
            cell['features'].update({
                'moon_illumination': moon_illumination,
                'season': season,
                'season_encoded': season_encoded,
                'day_of_week': day_of_week
            })
        
        return cells
    
    def _extract_topographical_features(self, cells: List[Dict]) -> List[Dict]:
        """
        Extract terrain features from DEM
        - Elevation
        - Slope
        - Terrain ruggedness
        """
        print("  Extracting topographical features...")
        
        # Use SRTM Digital Elevation Model
        dem = ee.Image('USGS/SRTMGL1_003')
        
        # Calculate slope from DEM
        slope = ee.Terrain.slope(dem)
        
        for cell in cells:
            point = ee.Geometry.Point([cell['center']['lng'], cell['center']['lat']])
            
            try:
                # Extract elevation
                elevation = dem.sample(point, 30).first().get('elevation').getInfo()
                elevation = float(elevation) if elevation else 1000.0
                
                # Extract slope
                slope_value = slope.sample(point, 30).first().get('slope').getInfo()
                slope_value = float(slope_value) if slope_value else 10.0
                
                # Calculate terrain ruggedness index
                # Simplified: based on slope and elevation variance
                ruggedness = self._calculate_ruggedness(slope_value)
                
                cell['features'].update({
                    'elevation': round(elevation, 1),
                    'slope': round(slope_value, 1),
                    'terrain_ruggedness': round(ruggedness, 1)
                })
            
            except Exception as e:
                print(f"    Error extracting terrain for {cell['id']}: {str(e)}")
                cell['features'].update({
                    'elevation': 1000.0,
                    'slope': 10.0,
                    'terrain_ruggedness': 5.0
                })
        
        return cells
    
    def _add_species_features(self, cells: List[Dict]) -> List[Dict]:
        """
        Add species-specific features
        These would come from wildlife databases in production
        For now, use heuristics based on location
        """
        print("  Adding species features...")
        
        for cell in cells:
            lat = cell['center']['lat']
            lng = cell['center']['lng']
            
            # Elephant migration routes (simplified - major corridors)
            # In production, use actual migration tracking data
            is_migration_route = 0
            if -2.5 < lat < -1.5 and 37.0 < lng < 38.0:
                is_migration_route = 1  # Amboseli-Tsavo corridor
            
            # Breeding season (simplified - peak calving season)
            month = datetime.now().month
            breeding_season = 1 if month in [3, 4, 5, 11, 12] else 0
            
            # Watering pattern based on proximity to water
            dist_to_water = cell['features'].get('dist_to_water', 5000)
            if dist_to_water < 2000:
                watering = 'regular'
                watering_encoded = 0
            elif dist_to_water < 5000:
                watering = 'seasonal'
                watering_encoded = 1
            else:
                watering = 'rare'
                watering_encoded = 2
            
            cell['features'].update({
                'elephant_migration_route': is_migration_route,
                'breeding_season': breeding_season,
                'watering_pattern': watering,
                'watering_pattern_encoded': watering_encoded
            })
        
        return cells
    
    def _calculate_derived_features(self, cells: List[Dict]) -> List[Dict]:
        """
        Calculate derived features used in model training
        Must match feature engineering in model_trainer.py
        """
        print("  Calculating derived features...")
        
        for cell in cells:
            features = cell['features']
            
            # Proximity-based risk features
            features['boundary_risk'] = 1 / (features['dist_to_boundary'] + 100)
            features['water_attraction'] = 1 / (features['dist_to_water'] + 50)
            features['access_ease'] = 1 / (features['dist_to_road'] + 200)
            features['isolation_score'] = (
                features['dist_to_settlement'] + features['dist_to_road']
            ) / 2000
            
            # Vegetation binary
            features['dense_vegetation'] = 1 if features['ndvi'] > 0.5 else 0
            
            # Temporal interactions
            features['dry_season'] = 1 if features['season'] == 'dry' else 0
            features['is_weekend'] = 1 if features['day_of_week'] in [5, 6] else 0
            
            # Historical features (placeholder - no historical data yet)
            # In production, query incident database
            features['incidents_5km_radius'] = 0
            features['days_since_last_incident'] = 180
            features['seasonal_incident_rate'] = 0.05
            features['incident_density'] = 0.0
        
        return cells
    
    # Helper methods for distance calculations
    
    def _distance_to_polygon_edge(
        self, 
        lat: float, 
        lng: float, 
        polygon: List[Dict]
    ) -> float:
        """
        Calculate distance from point to nearest polygon edge
        Returns distance in meters
        """
        min_distance = float('inf')
        
        for i in range(len(polygon)):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % len(polygon)]
            
            # Distance from point to line segment
            dist = self._point_to_segment_distance(
                lat, lng,
                p1['lat'], p1['lng'],
                p2['lat'], p2['lng']
            )
            
            min_distance = min(min_distance, dist)
        
        return min_distance
    
    def _point_to_segment_distance(
        self,
        px: float, py: float,
        x1: float, y1: float,
        x2: float, y2: float
    ) -> float:
        """Calculate distance from point to line segment in meters"""
        # Simplified: Use Haversine for point-to-point, project to segment
        # For production, use more accurate geodesic calculations
        
        # Distance to both endpoints
        dist1 = self._haversine_distance(px, py, x1, y1)
        dist2 = self._haversine_distance(px, py, x2, y2)
        
        # Approximate distance to segment (simplified)
        return min(dist1, dist2)
    
    def _haversine_distance(
        self, 
        lat1: float, 
        lng1: float, 
        lat2: float, 
        lng2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)
        
        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    # Estimation methods (placeholders for real data integration)
    
    def _estimate_water_distance(self, lat: float, lng: float) -> float:
        """
        Estimate distance to water
        TODO: Integrate GEE water body datasets or OSM rivers
        """
        # Simplified: Random with geographic bias
        base = np.random.uniform(500, 5000)
        return base
    
    def _estimate_road_distance(self, lat: float, lng: float) -> float:
        """
        Estimate distance to roads
        TODO: Integrate OpenStreetMap road network
        """
        base = np.random.uniform(1000, 15000)
        return base
    
    def _estimate_settlement_distance(self, lat: float, lng: float) -> float:
        """
        Estimate distance to settlements
        TODO: Integrate population density grids
        """
        base = np.random.uniform(5000, 40000)
        return base
    
    def _calculate_ruggedness(self, slope: float) -> float:
        """
        Calculate terrain ruggedness index from slope
        Simplified: 0-10 scale based on slope
        """
        # Normalize slope (0-60 degrees) to ruggedness (0-10)
        ruggedness = (slope / 60) * 10
        return np.clip(ruggedness, 0, 10)
    
    def format_for_model_input(self, cells: List[Dict]) -> List[Dict]:
        """
        Format extracted features to match model training schema
        Returns list of feature dictionaries ready for model.predict()
        
        Args:
            cells: Cells with extracted features
        
        Returns:
            List of dictionaries with model input features
        """
        model_inputs = []
        
        for cell in cells:
            features = cell['features']
            
            # Extract only features used in model training
            # Must match feature list from model_trainer.py
            model_input = {
                # Satellite features
                'ndvi': features.get('ndvi', 0.5),
                'vegetation_type_encoded': features.get('vegetation_type_encoded', 2),
                
                # Proximity features
                'dist_to_boundary': features.get('dist_to_boundary', 10000),
                'dist_to_water': features.get('dist_to_water', 5000),
                'dist_to_road': features.get('dist_to_road', 10000),
                'dist_to_settlement': features.get('dist_to_settlement', 30000),
                
                # Historical features
                'incidents_5km_radius': features.get('incidents_5km_radius', 0),
                'days_since_last_incident': features.get('days_since_last_incident', 180),
                'seasonal_incident_rate': features.get('seasonal_incident_rate', 0.05),
                
                # Temporal features
                'moon_illumination': features.get('moon_illumination', 0.5),
                'season_encoded': features.get('season_encoded', 0),
                'day_of_week': features.get('day_of_week', 3),
                
                # Topographical features
                'elevation': features.get('elevation', 1000),
                'slope': features.get('slope', 10),
                'terrain_ruggedness': features.get('terrain_ruggedness', 5),
                
                # Species features
                'elephant_migration_route': features.get('elephant_migration_route', 0),
                'breeding_season': features.get('breeding_season', 0),
                'watering_pattern_encoded': features.get('watering_pattern_encoded', 1),
                
                # Derived features
                'boundary_risk': features.get('boundary_risk', 0),
                'water_attraction': features.get('water_attraction', 0),
                'access_ease': features.get('access_ease', 0),
                'isolation_score': features.get('isolation_score', 0),
                'dense_vegetation': features.get('dense_vegetation', 0),
                'dry_season': features.get('dry_season', 0),
                'is_weekend': features.get('is_weekend', 0),
                'incident_density': features.get('incident_density', 0)
            }
            
            model_inputs.append({
                'cell_id': cell['id'],
                'center': cell['center'],
                'features': model_input
            })
        
        return model_inputs


# Singleton instance
_extractor_instance = None

def get_extractor_instance() -> FeatureExtractor:
    """Get or create feature extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = FeatureExtractor()
    return _extractor_instance
