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
from backend.utils.gee_satellite import get_gee_instance
from backend.models.risk_model import get_model_instance
from backend.models.insurance_model import get_insurance_model
from backend.services.perplexity_search import get_perplexity_instance
from backend.services.data_service import get_data_service

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


class InsuranceContextRequest(BaseModel):
    agri_risk_score: float
    lat: float
    lon: float
    # Optional: Allow overriding specific factors if known
    override_factors: Optional[dict] = None


class InsuranceAnalysisResponse(BaseModel):
    risk_score: float
    premium: float
    policy_type: str
    max_coverage: float
    deductible: float
    factors: List[dict]


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
        insurance_model = get_insurance_model()
        
        return {
            "status": "healthy",
            "database": "not_connected",
            "model": "loaded" if model.is_loaded else "not_loaded",
            "insurance_model": "loaded" if insurance_model.is_loaded else "not_loaded",
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


@app.post("/api/insurance/analyze", response_model=InsuranceAnalysisResponse)
async def analyze_insurance_risk(request: InsuranceContextRequest):
    """
    Analyze insurance risk based on agricultural score and location context.
    Uses DataService to deterministically fetch/generate auxiliary data.
    """
    print(f"INFO: Received insurance analysis request for location ({request.lat}, {request.lon}) with agri_risk={request.agri_risk_score}")
    
    model = get_insurance_model()
    data_service = get_data_service()
    
    # Load model if not loaded (lazy loading)
    if not model.is_loaded:
        model_path = "insurance_model.joblib"
        if not model.load(model_path):
             # Fallback to training if not found (auto-healing)
             print("WARNING: Model not found, training new one...")
             try:
                 from backend.services.insurance_trainer import InsuranceModelTrainer
                 trainer = InsuranceModelTrainer()
                 trainer.train()
                 trainer.save_model(model_path)
                 # Try loading again
                 model.load(model_path)
             except Exception as e:
                 print(f"ERROR: Failed to train fallback model: {e}")
                 raise HTTPException(status_code=500, detail="Model not available and training failed")

    try:
        # 1. Get Context Data (Deterministic)
        context_data = data_service.get_context_data(request.lat, request.lon, request.agri_risk_score)
        
        # Apply overrides if any
        if request.override_factors:
            context_data.update(request.override_factors)
            
        # 2. Prepare Features
        features = {
            'agri_risk_score': request.agri_risk_score,
            **context_data
        }
        
        print(f"INFO: Running prediction with features: {features}")
        
        # 3. Predict
        risk_score = model.predict(features)
        
        # Calculate policy details based on risk score (in Kenyan Shillings)
        # Premium range: 50,000 - 200,000 KES
        premium = 50000 + (risk_score * 1500)
        # Coverage range: 500,000 - 5,000,000 KES
        max_coverage = 5000000 - (risk_score * 45000)
        # Deductible range: 10,000 - 50,000 KES
        deductible = 10000 + (risk_score * 400)
        
        policy_type = 'Standard'
        if risk_score > 80: policy_type = 'Uninsurable'
        elif risk_score > 60: policy_type = 'High Risk'
        elif risk_score < 30: policy_type = 'Premium'
        
        # Generate explanatory factors (expanded to 6 factors)
        factors = [
            {'name': 'Agricultural Risk', 'impact': 'High' if request.agri_risk_score > 60 else 'Low', 'value': f"{request.agri_risk_score:.1f}"},
            {'name': 'Weather Volatility', 'impact': 'High' if context_data['weather_volatility'] > 0.6 else 'Low', 'value': f"{context_data['weather_volatility']:.2f}"},
            {'name': 'Yield Stability', 'impact': 'High' if context_data['yield_stability'] < 0.4 else 'Low', 'value': f"{context_data['yield_stability']:.2f}"},
            {'name': 'Soil Quality', 'impact': 'High' if context_data['soil_quality'] < 0.5 else 'Low', 'value': f"{context_data['soil_quality']:.2f}"},
            {'name': 'Market Stability', 'impact': 'High' if context_data['market_stability'] < 0.5 else 'Low', 'value': f"{context_data['market_stability']:.2f}"},
            {'name': 'Claims History', 'impact': 'High' if context_data['claims_history_index'] > 0.6 else 'Low', 'value': f"{context_data['claims_history_index']:.2f}"}
        ]
        
        # Coverage period
        coverage_period = "12 months (Annual)"
        
        # Recommended actions based on risk level
        recommended_actions = []
        if risk_score > 70:
            recommended_actions = [
                "Consider drought-resistant crop varieties",
                "Implement soil conservation measures",
                "Diversify crop portfolio to reduce risk"
            ]
        elif risk_score > 50:
            recommended_actions = [
                "Monitor weather forecasts regularly",
                "Maintain adequate irrigation systems"
            ]
        else:
            recommended_actions = [
                "Continue current best practices",
                "Consider expanding coverage area"
            ]

        return {
            "risk_score": round(risk_score, 1),
            "premium": round(premium, 0),  # No decimals for KES
            "policy_type": policy_type,
            "max_coverage": round(max_coverage, 0),  # No decimals for KES
            "deductible": round(deductible, 0),  # No decimals for KES
            "factors": factors,
            "context_data": context_data,
            "coverage_period": coverage_period,
            "recommended_actions": recommended_actions
        }
    except Exception as e:
        print(f"ERROR: Insurance analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
        await websocket.send_json({'type': 'status', 'step': 'soil_analysis', 'message': f'Analyzing soil moisture and composition...', 'progressPercent': 20})
        await asyncio.sleep(1.0)
        
        # Weather Forecasting
        print(f">>> Sending: weather_forecast")
        await websocket.send_json({'type': 'status', 'step': 'weather_forecast', 'message': 'Retrieving long-term precipitation and temperature forecasts...', 'progressPercent': 40})
        await asyncio.sleep(1.0)
        
        # Market Data
        print(f">>> Sending: market_data")
        await websocket.send_json({'type': 'status', 'step': 'market_data', 'message': f'Fetching regional market volatility data...', 'progressPercent': 50})
        await asyncio.sleep(1.0)
        
        # Web Search for Agricultural Intelligence
        print(f">>> Sending: web_search")
        await websocket.send_json({'type': 'status', 'step': 'web_search', 'message': 'Searching latest climatic intelligence and research...', 'progressPercent': 60})
        
        # Calculate centroid for search context
        location_context = "Kenya"
        gemini_context = ""
        
        if polygon:
            lats = [p['lat'] for p in polygon]
            lons = [p['lng'] for p in polygon]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # 1. Reverse Geocoding
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="sentry_app")
                location = geolocator.reverse(f"{center_lat}, {center_lon}", language='en')
                if location and location.address:
                    address = location.raw.get('address', {})
                    city = address.get('city') or address.get('town') or address.get('village') or address.get('county')
                    state = address.get('state') or address.get('region')
                    country = address.get('country')
                    parts = [p for p in [city, state, country] if p]
                    location_context = ", ".join(parts)
                    print(f"  ✓ Geocoded location: {location_context}")
                else:
                    location_context = f"coordinates {center_lat:.4f}, {center_lon:.4f}"
            except Exception as e:
                print(f"  ⚠ Geocoding failed: {e}")
                location_context = f"coordinates {center_lat:.4f}, {center_lon:.4f}"

            # 2. Gemini Visual Analysis
            try:
                print("  Running Gemini visual analysis...")
                from backend.services.gemini_service import GeminiService
                
                gemini = GeminiService()
                
                # Fetch satellite image from GEE
                # Note: 'gee' instance is already initialized above
                satellite_img_bytes = gee.get_satellite_image(polygon)
                
                if satellite_img_bytes:
                    prompt = f"Analyze this satellite image of an agricultural area at {location_context}. Identify the specific crops grown (e.g. tea, coffee, maize) and the agricultural landscape features. Return a concise 1-sentence description for a search query."
                    
                    analysis = gemini.analyze_image_with_search(satellite_img_bytes, prompt)
                    if analysis and 'text' in analysis:
                        gemini_context = analysis['text'].strip()
                        print(f"  ✓ Gemini Context: {gemini_context}")
                        
                        # Enhance location context with Gemini's findings
                        location_context = f"{location_context}. {gemini_context}"
                else:
                    print("  ⚠ Could not fetch satellite image for Gemini analysis")
                    
            except Exception as e:
                print(f"  ⚠ Gemini analysis failed: {e}")

        perplexity = get_perplexity_instance()
        search_results = perplexity.search_agricultural_intelligence(
            crop_type=request.parameters.cropType,
            risk_factors=request.parameters.riskFactors,
            region=location_context,
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
        # 5. Calculate Risk Score
        # -----------------------
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


from fastapi.responses import StreamingResponse
from backend.services.pdf_service import PDFService

class PDFRequest(BaseModel):
    farmName: str
    lat: float
    lon: float
    areaKm2: float
    cropType: str
    risk_score: float
    policy_type: str
    max_coverage: float
    deductible: float
    premium: float
    coverage_period: str
    factors: List[dict]
    recommended_actions: List[str]
    polygon: Optional[List[dict]] = None

@app.post("/api/insurance/pdf")
async def generate_pdf(request: PDFRequest):
    """
    Generate a PDF report for the insurance policy.
    """
    try:
        pdf_service = PDFService()
        pdf_buffer = pdf_service.generate_insurance_report(request.dict())
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=insurance_proposal.pdf"}
        )
    except Exception as e:
        print(f"ERROR: PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
