"""
Google Earth Engine Satellite Data Processing
Handles authentication, imagery fetching, and feature extraction
"""

import ee
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import math
from concurrent.futures import ThreadPoolExecutor, as_completed


class GEESatellite:
    """Google Earth Engine satellite data processor"""
    
    def __init__(self):
        """Initialize GEE with service account authentication"""
        self.authenticated = False
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with GEE using service account"""
        try:
            service_account_key = Path(__file__).parent.parent / 'ascendant-woods-462020-n0-78d818c9658e.json'
            
            if not service_account_key.exists():
                raise FileNotFoundError(f"Service account key not found at: {service_account_key}")
            
            with open(service_account_key, 'r') as f:
                key_data = json.load(f)
            
            service_account = key_data['client_email']
            credentials = ee.ServiceAccountCredentials(service_account, str(service_account_key))
            ee.Initialize(credentials)
            
            self.authenticated = True
            print(f"✓ GEE authenticated: {service_account}")
            
        except Exception as e:
            print(f"✗ GEE authentication failed: {str(e)}")
            raise
    
    def create_grid_cells(
        self, 
        polygon: List[Dict[str, float]], 
        cell_size_km: float = 1.0
    ) -> List[Dict]:
        """
        Divide polygon into grid cells
        
        Args:
            polygon: List of {lat, lng} coordinates defining the boundary
            cell_size_km: Size of each grid cell in kilometers
        
        Returns:
            List of grid cells with center coordinates and bounds
        """
        # Get bounding box
        lats = [p['lat'] for p in polygon]
        lngs = [p['lng'] for p in polygon]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        # Convert km to degrees (approximate at equator: 1° ≈ 111km)
        lat_step = cell_size_km / 111.0
        lng_step = cell_size_km / (111.0 * math.cos(math.radians((min_lat + max_lat) / 2)))
        
        # Generate grid
        cells = []
        cell_id = 0
        
        lat = min_lat
        while lat < max_lat:
            lng = min_lng
            while lng < max_lng:
                center_lat = lat + lat_step / 2
                center_lng = lng + lng_step / 2
                
                # Check if cell center is inside polygon (simple point-in-polygon)
                if self._point_in_polygon(center_lat, center_lng, polygon):
                    cells.append({
                        'id': f'cell-{cell_id}',
                        'center': {'lat': center_lat, 'lng': center_lng},
                        'bounds': {
                            'southWest': {'lat': lat, 'lng': lng},
                            'northEast': {'lat': lat + lat_step, 'lng': lng + lng_step}
                        }
                    })
                    cell_id += 1
                
                lng += lng_step
            lat += lat_step
        
        return cells
    
    def _point_in_polygon(self, lat: float, lng: float, polygon: List[Dict]) -> bool:
        """Simple ray casting algorithm for point-in-polygon test"""
        n = len(polygon)
        inside = False
        
        p1_lat, p1_lng = polygon[0]['lat'], polygon[0]['lng']
        
        for i in range(1, n + 1):
            p2_lat, p2_lng = polygon[i % n]['lat'], polygon[i % n]['lng']
            
            if min(p1_lng, p2_lng) < lng <= max(p1_lng, p2_lng):
                if lat <= max(p1_lat, p2_lat):
                    if p1_lng != p2_lng:
                        x_intersect = (lng - p1_lng) * (p2_lat - p1_lat) / (p2_lng - p1_lng) + p1_lat
                    if p1_lat == p2_lat or lat <= x_intersect:
                        inside = not inside
            
            p1_lat, p1_lng = p2_lat, p2_lng
        
        return inside
    
    def calculate_polygon_area_km2(self, polygon: List[Dict[str, float]]) -> float:
        """
        Calculate approximate area of polygon in square kilometers
        Uses spherical excess formula for better accuracy
        """
        coords = [[p['lng'], p['lat']] for p in polygon]
        coords.append(coords[0])  # Close the polygon
        
        ee_polygon = ee.Geometry.Polygon([coords])
        area_m2 = ee_polygon.area().getInfo()
        area_km2 = area_m2 / 1_000_000
        
        return area_km2
    
    def extract_features_for_cells(
        self,
        cells: List[Dict],
        date_start: str,
        date_end: str,
        include_features: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Extract satellite-derived features for each grid cell
        
        Args:
            cells: List of grid cells from create_grid_cells()
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            include_features: List of features to extract (default: all)
        
        Returns:
            List of cells with extracted features
        """
        if include_features is None:
            include_features = ['ndvi', 'water_proximity', 'boundary_distance']
        
        # Create GEE points for all cells
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
        print(f"  Found {image_count} cloud-free Sentinel-2 images")
        
        if image_count == 0:
            print("  WARNING: No images available for date range")
            # Return cells with null features
            return [
                {**cell, 'features': {'ndvi': None, 'image_count': 0}}
                for cell in cells
            ]
        
        # Calculate median composite
        median = collection.median()
        
        # Generate thumbnail URLs for the first few images (PARALLELIZED)
        image_urls = []
        try:
            print(f"  Generating thumbnail URLs from {image_count} images...")
            image_list = collection.toList(5).getInfo()  # Get up to 5 images
            print(f"  Retrieved {len(image_list)} images for thumbnails")
            
            def generate_thumbnail(img_info):
                """Helper function to generate a single thumbnail (for parallel execution)"""
                img_id = img_info['id']
                img = ee.Image(img_id)
                # Generate RGB thumbnail URL
                vis_params = {
                    'bands': ['B4', 'B3', 'B2'],
                    'min': 0,
                    'max': 3000,
                    'dimensions': 512,
                }
                thumb_url = img.getThumbURL(vis_params)
                print(f"    Generated thumbnail for {img_id}")
                return {
                    'url': thumb_url,
                    'id': img_id,
                    'date': img_info.get('properties', {}).get('system:time_start')
                }
            
            # Use ThreadPoolExecutor to generate thumbnails in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all thumbnail generation tasks
                future_to_img = {executor.submit(generate_thumbnail, img_info): img_info for img_info in image_list}
                
                # Collect results as they complete
                for future in as_completed(future_to_img):
                    try:
                        result = future.result()
                        image_urls.append(result)
                    except Exception as exc:
                        img_info = future_to_img[future]
                        print(f"    Failed to generate thumbnail for {img_info['id']}: {exc}")
            
            print(f"  Total thumbnails generated: {len(image_urls)}")
        except Exception as e:
            print(f"  Could not generate image thumbnails: {str(e)}")
        
        # Extract features
        results = []
        for cell in cells:
            point = ee.Geometry.Point([cell['center']['lng'], cell['center']['lat']])
            features = {
                'image_count': image_count,
                'image_urls': image_urls  # Share same URLs across all cells
            }
            
            try:
                # NDVI: (NIR - Red) / (NIR + Red)
                if 'ndvi' in include_features:
                    nir = median.select('B8')
                    red = median.select('B4')
                    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
                    ndvi_value = ndvi.sample(point, 30).first().get('NDVI').getInfo()
                    features['ndvi'] = round(ndvi_value, 3) if ndvi_value else None
                
                # TODO: Add more features
                # - Water proximity (using water body datasets)
                # - Distance to park boundaries
                # - Terrain elevation/slope
                # - Night-time lights (human activity)
                # - Temperature anomalies
                
            except Exception as e:
                print(f"  Error extracting features for {cell['id']}: {str(e)}")
                features['ndvi'] = None
            
            results.append({
                **cell,
                'features': features
            })
        
        return results


# Singleton instance
_gee_instance = None

def get_gee_instance() -> GEESatellite:
    """Get or create GEE satellite instance"""
    global _gee_instance
    if _gee_instance is None:
        _gee_instance = GEESatellite()
    return _gee_instance
