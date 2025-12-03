"""
Integration test for full analysis pipeline
Tests: polygon -> grid cells -> satellite features -> risk scores
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.gee_satellite import get_gee_instance


def test_full_analysis_pipeline():
    """Test complete analysis flow with small test polygon"""
    print("\n" + "="*60)
    print("Full Analysis Pipeline Test")
    print("="*60)
    
    # Small test polygon in Tsavo East (~25 km²)
    test_polygon = [
        {"lat": -2.80, "lng": 38.90},
        {"lat": -2.80, "lng": 39.00},
        {"lat": -2.85, "lng": 39.00},
        {"lat": -2.85, "lng": 38.90},
        {"lat": -2.80, "lng": 38.90}
    ]
    
    gee = get_gee_instance()
    
    # Step 1: Calculate area
    print("\n1. Calculating polygon area...")
    area_km2 = gee.calculate_polygon_area_km2(test_polygon)
    print(f"   Area: {area_km2:.2f} km²")
    
    # Step 2: Generate grid
    print("\n2. Generating grid cells (1km)...")
    cells = gee.create_grid_cells(test_polygon, cell_size_km=1.0)
    print(f"   Generated {len(cells)} cells")
    
    if len(cells) > 0:
        print(f"   Sample cell: {cells[0]['id']} at {cells[0]['center']}")
    
    # Step 3: Extract features
    print("\n3. Extracting satellite features...")
    cells_with_features = gee.extract_features_for_cells(
        cells,
        "2024-01-01",
        "2024-12-31"
    )
    
    print(f"   Processed {len(cells_with_features)} cells")
    if cells_with_features:
        sample = cells_with_features[0]
        print(f"   Sample features: NDVI={sample['features'].get('ndvi')}, Images={sample['features'].get('image_count')}")
    
    # Step 4: Generate risk scores
    print("\n4. Generating risk scores...")
    cells_with_risk = gee.simulate_risk_scores(cells_with_features, "poaching")
    
    risk_scores = [c['risk_score'] for c in cells_with_risk]
    print(f"   Risk scores: min={min(risk_scores)}, max={max(risk_scores)}, avg={sum(risk_scores)/len(risk_scores):.1f}")
    
    high_risk = sum(1 for s in risk_scores if s >= 75)
    print(f"   High risk cells: {high_risk}/{len(cells_with_risk)}")
    
    # Show top 3 riskiest cells
    sorted_cells = sorted(cells_with_risk, key=lambda x: x['risk_score'], reverse=True)
    print("\n   Top 3 riskiest areas:")
    for i, cell in enumerate(sorted_cells[:3]):
        print(f"   {i+1}. {cell['id']}: Score={cell['risk_score']} ({cell['risk_level']})")
        print(f"      Factors: {', '.join(cell['risk_factors'])}")
    
    print("\n" + "="*60)
    print("Pipeline test complete!")
    print("="*60)


if __name__ == "__main__":
    test_full_analysis_pipeline()
