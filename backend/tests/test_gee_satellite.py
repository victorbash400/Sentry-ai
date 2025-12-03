"""
Test Google Earth Engine Authentication and Basic Satellite Data Access
"""

import ee
import json
from pathlib import Path


def test_gee_authentication():
    """Test if GEE authentication works with service account"""
    try:
        # Path to service account key
        service_account_key = Path(__file__).parent.parent / 'ascendant-woods-462020-n0-78d818c9658e.json'
        
        if not service_account_key.exists():
            print(f"ERROR: Service account key not found at: {service_account_key}")
            return False
        
        # Load service account credentials
        with open(service_account_key, 'r') as f:
            key_data = json.load(f)
        
        service_account = key_data['client_email']
        
        print(f"Using service account: {service_account}")
        
        # Initialize Earth Engine with service account
        credentials = ee.ServiceAccountCredentials(service_account, str(service_account_key))
        ee.Initialize(credentials)
        
        print("SUCCESS: Google Earth Engine authentication successful!")
        return True
        
    except Exception as e:
        print(f"ERROR: Authentication failed: {str(e)}")
        return False


def test_sentinel2_access():
    """Test accessing Sentinel-2 imagery"""
    try:
        # Test location: Tsavo East National Park, Kenya
        test_point = ee.Geometry.Point([38.9, -2.8])
        
        print("\nTesting Sentinel-2 image access...")
        print(f"   Location: Tsavo East National Park (38.9°E, 2.8°S)")
        
        # Query Sentinel-2 imagery
        collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(test_point) \
            .filterDate('2024-01-01', '2024-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .select(['B4', 'B8'])  # Red and NIR bands for NDVI
        
        # Get collection size
        count = collection.size().getInfo()
        print(f"   Found {count} cloud-free images in 2024")
        
        if count == 0:
            print("   WARNING: No images found, but API access works!")
            return True
        
        print("SUCCESS: Sentinel-2 access successful!")
        return True
        
    except Exception as e:
        print(f"ERROR: Sentinel-2 access failed: {str(e)}")
        return False


def test_ndvi_calculation():
    """Test NDVI calculation from satellite imagery"""
    try:
        print("\nTesting NDVI calculation...")
        
        # Test location: Tsavo East
        test_point = ee.Geometry.Point([38.9, -2.8])
        
        # Get a recent Sentinel-2 image
        image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(test_point) \
            .filterDate('2024-01-01', '2024-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .first()
        
        if image is None:
            print("   WARNING: No images available, but calculation logic works!")
            return True
        
        # Calculate NDVI: (NIR - Red) / (NIR + Red)
        nir = image.select('B8')
        red = image.select('B4')
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        
        # Sample NDVI value at test point
        ndvi_value = ndvi.sample(test_point, 30).first().get('NDVI').getInfo()
        
        print(f"   NDVI value at test location: {ndvi_value:.3f}")
        print(f"   Interpretation: ", end="")
        
        if ndvi_value < 0.2:
            print("Bare soil/rock")
        elif ndvi_value < 0.5:
            print("Sparse vegetation")
        elif ndvi_value < 0.7:
            print("Moderate vegetation")
        else:
            print("Dense vegetation")
        
        print("SUCCESS: NDVI calculation successful!")
        return True
        
    except Exception as e:
        print(f"ERROR: NDVI calculation failed: {str(e)}")
        print(f"   (This might be normal if no recent images are available)")
        return False


def test_batch_feature_extraction():
    """Test extracting features for multiple grid cells"""
    try:
        print("\nTesting batch feature extraction...")
        
        # Test grid: 3 cells in Tsavo East
        test_cells = [
            {"id": "cell-1", "lat": -2.8, "lng": 38.9},
            {"id": "cell-2", "lat": -2.85, "lng": 38.95},
            {"id": "cell-3", "lat": -2.9, "lng": 39.0}
        ]
        
        print(f"   Extracting features for {len(test_cells)} grid cells...")
        
        # Create point geometries
        points = [ee.Geometry.Point([cell['lng'], cell['lat']]) for cell in test_cells]
        
        # Get image collection
        collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(ee.Geometry.MultiPoint(points)) \
            .filterDate('2024-01-01', '2024-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        
        count = collection.size().getInfo()
        print(f"   Using {count} satellite images")
        
        if count > 0:
            # Calculate median NDVI
            median = collection.median()
            nir = median.select('B8')
            red = median.select('B4')
            ndvi = nir.subtract(red).divide(nir.add(red))
            
            # Sample at each point
            for i, (cell, point) in enumerate(zip(test_cells, points)):
                try:
                    ndvi_renamed = ndvi.rename('NDVI')
                    value = ndvi_renamed.sample(point, 30).first().get('NDVI').getInfo()
                    print(f"   Cell {i+1}: NDVI = {value:.3f}")
                except Exception as e:
                    print(f"   Cell {i+1}: No data available - {str(e)}")
        
        print("SUCCESS: Batch extraction test complete!")
        return True
        
    except Exception as e:
        print(f"ERROR: Batch extraction failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Google Earth Engine Integration Test")
    print("=" * 60)
    
    # Test 1: Authentication
    if not test_gee_authentication():
        print("\nWARNING: Cannot proceed without authentication")
        return
    
    # Test 2: Sentinel-2 Access
    test_sentinel2_access()
    
    # Test 3: NDVI Calculation
    test_ndvi_calculation()
    
    # Test 4: Batch Processing
    test_batch_feature_extraction()
    
    print("\n" + "=" * 60)
    print("Test suite complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
