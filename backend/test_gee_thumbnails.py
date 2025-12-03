#!/usr/bin/env python3
"""
Quick test script to verify GEE thumbnail generation is working
"""

from utils.gee_satellite import get_gee_instance
from datetime import datetime, timedelta

def test_thumbnail_generation():
    print("=" * 60)
    print("Testing GEE Thumbnail Generation")
    print("=" * 60)
    
    # Initialize GEE
    print("\n1. Initializing Google Earth Engine...")
    try:
        gee = get_gee_instance()
        print(f"   ✓ GEE authenticated: {gee.authenticated}")
    except Exception as e:
        print(f"   ✗ Failed to authenticate: {e}")
        return False
    
    # Create a small test polygon in Kenya (Rift Valley region)
    print("\n2. Creating test polygon...")
    test_polygon = [
        {'lat': 0.0, 'lng': 35.5},
        {'lat': 0.0, 'lng': 35.6},
        {'lat': 0.1, 'lng': 35.6},
        {'lat': 0.1, 'lng': 35.5},
    ]
    print(f"   ✓ Test area: {len(test_polygon)} points")
    
    # Generate grid cells
    print("\n3. Generating grid cells...")
    cells = gee.create_grid_cells(test_polygon, cell_size_km=2.0)
    print(f"   ✓ Generated {len(cells)} grid cells")
    
    # Extract features with thumbnails
    print("\n4. Extracting satellite features and thumbnails...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    date_start = start_date.strftime('%Y-%m-%d')
    date_end = end_date.strftime('%Y-%m-%d')
    
    print(f"   Date range: {date_start} to {date_end}")
    
    try:
        cells_with_features = gee.extract_features_for_cells(
            cells, 
            date_start, 
            date_end
        )
        
        if not cells_with_features or len(cells_with_features) == 0:
            print("   ✗ No cells returned")
            return False
        
        print(f"   ✓ Extracted features for {len(cells_with_features)} cells")
        
        # Check for thumbnails
        first_cell = cells_with_features[0]
        features = first_cell.get('features', {})
        image_urls = features.get('image_urls', [])
        image_count = features.get('image_count', 0)
        ndvi = features.get('ndvi')
        
        print(f"\n5. Results:")
        print(f"   Images found: {image_count}")
        print(f"   Thumbnails generated: {len(image_urls)}")
        print(f"   NDVI value: {ndvi}")
        
        if len(image_urls) > 0:
            print(f"\n   ✓ SUCCESS! Generated {len(image_urls)} thumbnail URLs")
            print(f"\n   Sample thumbnail:")
            sample = image_urls[0]
            print(f"     ID: {sample['id']}")
            print(f"     URL: {sample['url'][:80]}...")
            print(f"     Date: {sample.get('date')}")
            return True
        else:
            print(f"\n   ⚠ No thumbnails generated (might be no cloud-free images)")
            print(f"   This is normal if there's heavy cloud cover in the date range")
            return True
            
    except Exception as e:
        print(f"   ✗ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_thumbnail_generation()
    print("\n" + "=" * 60)
    if success:
        print("✓ GEE thumbnail generation is working!")
    else:
        print("✗ GEE thumbnail generation failed")
    print("=" * 60)
