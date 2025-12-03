"""
SENTRY - Agri-Climate Risk Intelligence Platform
FastAPI Backend Server
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import json
import asyncio
import random
from utils.gee_satellite import get_gee_instance
from models.risk_model import get_model_instance
from services.perplexity_search import get_perplexity_instance

app = FastAPI(
    title="Agri-Sentry API",
    description="Climate risk and market volatility intelligence for smallholder farmers",
    version="2.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class LocationInput(BaseModel):
    type: str  # "farm" or "custom"
    farmId: Optional[str] = None
    farmName: Optional[str] = None
    cropType: Optional[str] = None
    polygon: Optional[List[dict]] = None
    bounds: Optional[dict] = None


class AnalysisParameters(BaseModel):
    dateRange: dict  # {"start": "2024-01-01", "end": "2024-01-07"}
    cropType: str  # "Maize", "Wheat", "Coffee", etc.
    riskFactors: List[str]  # ["Drought", "Flood", "Pests", "Market"]


class AdvancedOptions(BaseModel):
    displayThreshold: int = 40
    gridGranularity: int = 1  # km
    enabledLayers: List[str] = []
    temporalFocus: List[str] = []


class AnalysisRequest(BaseModel):
    location: LocationInput
    parameters: AnalysisParameters
    advanced: AdvancedOptions


class AnalysisResponse(BaseModel):
    geoJSON: dict
    temporal: Optional[dict] = None
    priorities: List[dict]
    summary: dict
    factors: Optional[dict] = None
    marketData: Optional[dict] = None


# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Agri-Sentry API",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        gee = get_gee_instance()
        model = get_model_instance()
        
        return {
            "status": "healthy",
            "database": "not_connected",
            "model": "loaded" if model.is_loaded else "not_loaded",
            "satellite": "configured" if gee.authenticated else "not_configured",
            "model_version": "agri-v1"
        }
    except Exception:
        return {
            "status": "degraded",
            "database": "not_connected",
            "model": "error",
            "satellite": "error"
        }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_risk(request: AnalysisRequest):
    """
    Main analysis endpoint
    Receives location and parameters, returns agricultural risk predictions
    """
    # This endpoint is kept for compatibility but the primary interaction is via WebSocket
    # We'll implement a basic synchronous version here if needed, but for now we rely on WS
    raise HTTPException(status_code=501, detail="Please use WebSocket endpoint /api/analyze/ws for analysis")


@app.websocket("/api/analyze/ws")
async def analyze_risk_websocket(websocket: WebSocket):
    """
    WebSocket analysis endpoint with real-time progress updates
    """
    await websocket.accept()
    
    try:
        # Receive the request data
        data = await websocket.receive_text()
        request_dict = json.loads(data)
        request = AnalysisRequest(**request_dict)
        
        # Validate polygon
        if request.location.type == "custom":
            if not request.location.polygon or len(request.location.polygon) < 3:
                await websocket.send_json({'type': 'error', 'step': 'error', 'message': 'Invalid polygon', 'progressPercent': 0})
                await websocket.close()
                return
            polygon = request.location.polygon
        else:
            # Mock farm selection
            pass
        
        # Initialize
        print(">>> Sending: initializing")
        await websocket.send_json({'type': 'status', 'step': 'initializing', 'message': 'Initializing Agri-Climate Engine...', 'progressPercent': 5})
        await asyncio.sleep(0.5)
        
        gee = get_gee_instance()
        area_km2 = gee.calculate_polygon_area_km2(polygon)
        
        MAX_AREA_KM2 = 5000 # Larger area allowed for farms/regions
        if area_km2 > MAX_AREA_KM2:
            await websocket.send_json({'type': 'error', 'step': 'error', 'message': f'Area too large: {area_km2:.1f} km². Maximum: {MAX_AREA_KM2} km²', 'progressPercent': 0})
            await websocket.close()
            return
        
        # Soil Analysis
        print(f">>> Sending: soil_analysis")
        await websocket.send_json({'type': 'status', 'step': 'soil_analysis', 'message': f'Analyzing soil moisture and composition for {request.parameters.cropType}...', 'progressPercent': 20})
        await asyncio.sleep(1.0)
        
        # Weather Forecasting
        print(f">>> Sending: weather_forecast")
        await websocket.send_json({'type': 'status', 'step': 'weather_forecast', 'message': 'Retrieving long-term precipitation and temperature forecasts...', 'progressPercent': 40})
        await asyncio.sleep(1.0)
        
        # Market Data
        print(f">>> Sending: market_data")
        await websocket.send_json({'type': 'status', 'step': 'market_data', 'message': f'Fetching market volatility data for {request.parameters.cropType}...', 'progressPercent': 50})
        await asyncio.sleep(1.0)
        
        # Web Search for Agricultural Intelligence
        print(f">>> Sending: web_search")
        await websocket.send_json({'type': 'status', 'step': 'web_search', 'message': 'Searching latest agricultural intelligence and research...', 'progressPercent': 60})
        
        perplexity = get_perplexity_instance()
        search_results = perplexity.search_agricultural_intelligence(
            crop_type=request.parameters.cropType,
            risk_factors=request.parameters.riskFactors,
            region="Kenya",
            max_results=5
        )
        
        # Send search results to frontend
        await websocket.send_json({
            'type': 'search_results',
            'step': 'web_search',
            'data': search_results,
            'progressPercent': 65
        })
        await asyncio.sleep(0.5)

        # Generate grid and extract satellite features
        cell_size_km = request.advanced.gridGranularity
        cells = gee.create_grid_cells(polygon, cell_size_km)
        
        # Extract satellite features (including thumbnail URLs)
        print(f">>> Sending: satellite_extraction")
        await websocket.send_json({'type': 'status', 'step': 'satellite_extraction', 'message': 'Extracting satellite imagery and NDVI data...', 'progressPercent': 70})
        
        date_start = request.parameters.dateRange['start']
        date_end = request.parameters.dateRange['end']
        cells_with_features = gee.extract_features_for_cells(cells, date_start, date_end)
        
        # Extract satellite images from first cell (they're shared across all cells)
        satellite_images = []
        if cells_with_features and len(cells_with_features) > 0:
            first_cell_features = cells_with_features[0].get('features', {})
            image_urls = first_cell_features.get('image_urls', [])
            
            # Transform to frontend format
            for img_data in image_urls:
                satellite_images.append({
                    'url': img_data['url'],
                    'id': img_data['id'],
                    'timestamp': img_data.get('date')  # milliseconds since epoch
                })
            
            print(f"  Extracted {len(satellite_images)} satellite images")
            
            # Send satellite images in real-time as they're extracted
            if satellite_images:
                await websocket.send_json({
                    'type': 'satellite_images',
                    'step': 'satellite_extraction',
                    'data': {'satelliteImages': satellite_images},
                    'progressPercent': 75
                })
        
        print(f">>> Sending: risk_modeling")
        await websocket.send_json({'type': 'status', 'step': 'risk_modeling', 'message': 'Calculating composite risk scores...', 'progressPercent': 85})
        await asyncio.sleep(0.5)

        # Mock Risk Calculation (TODO: Use real model predictions with extracted features)
        cells_with_risk = []
        for i, cell in enumerate(cells):
            # Generate deterministic pseudo-random risk based on location
            random.seed(i) 
            risk_score = random.randint(20, 95)
            
            risk_level = "Low"
            if risk_score > 75: risk_level = "High"
            elif risk_score > 50: risk_level = "Medium"
            
            # Mock factors
            factors = []
            if risk_score > 50:
                possible_factors = ["Drought Stress", "Pest Susceptibility", "Market Volatility", "Soil Degradation"]
                factors = random.sample(possible_factors, k=2)

            cells_with_risk.append({
                **cell,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": factors,
                "features": {} # Placeholder for satellite features
            })

        # Build response
        features = []
        for cell in cells_with_risk:
            bounds = cell['bounds']
            sw = bounds['southWest']
            ne = bounds['northEast']
            
            coordinates = [[
                [sw['lng'], sw['lat']],
                [ne['lng'], sw['lat']],
                [ne['lng'], ne['lat']],
                [sw['lng'], ne['lat']],
                [sw['lng'], sw['lat']]
            ]]
            
            features.append({
                "type": "Feature",
                "id": cell['id'],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                },
                "properties": {
                    "riskScore": cell['risk_score'],
                    "riskLevel": cell['risk_level'],
                    "factors": cell['risk_factors'],
                }
            })
        
        # Summary Stats
        risk_scores = [c['risk_score'] for c in cells_with_risk]
        high_risk = sum(1 for s in risk_scores if s >= 75)
        medium_risk = sum(1 for s in risk_scores if 50 <= s < 75)
        low_risk = sum(1 for s in risk_scores if s < 50)
        
        # Market Data Mock
        market_data = {
            "currentPrice": 145.50,
            "currency": "KES/kg",
            "trend": "down",
            "volatility": "High",
            "forecast": "Bearish due to expected surplus"
        }

        response_data = {
            "geoJSON": {
                "type": "FeatureCollection",
                "features": features
            },
            "priorities": [], # Can populate if needed
            "summary": {
                "totalCells": len(cells_with_risk),
                "highRiskCells": high_risk,
                "mediumRiskCells": medium_risk,
                "lowRiskCells": low_risk,
                "averageRisk": round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0,
                "areaKm2": round(area_km2, 2),
            },
            "marketData": market_data,
            "satelliteImages": satellite_images
        }
        
        print(f">>> Sending: complete")
        await websocket.send_json({'type': 'complete', 'step': 'complete', 'message': 'Analysis complete.', 'progressPercent': 100, 'data': response_data})
        
        await websocket.close()
        
    except WebSocketDisconnect:
        print(">>> WebSocket disconnected")
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({'type': 'error', 'step': 'error', 'message': f'Analysis failed: {str(e)}', 'progressPercent': 0})
            await websocket.close()
        except:
            pass


@app.get("/api/regions")
async def get_regions():
    """Get list of available agricultural regions"""
    return {
        "regions": [
            {
                "id": "rift-valley",
                "name": "Rift Valley (Maize Belt)",
                "bounds": {
                    "southWest": {"lat": -0.5, "lng": 35.0},
                    "northEast": {"lat": 0.5, "lng": 36.0}
                }
            },
            {
                "id": "central",
                "name": "Central (Coffee/Tea)",
                "bounds": {
                    "southWest": {"lat": -1.0, "lng": 36.5},
                    "northEast": {"lat": -0.3, "lng": 37.5}
                }
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
