# Sentry - AI Coding Agent Instructions

## Project Overview
Sentry is a **wildlife conservation risk assessment platform** that analyzes satellite imagery to predict poaching hotspots. The platform helps rangers prioritize patrol areas by generating risk heatmaps from Google Earth Engine data.

**Architecture:** Monorepo with separate frontend (Next.js) and backend (FastAPI) services communicating via REST and WebSocket APIs.

## Critical Architecture Patterns

### Dual-Service Communication
- **Frontend:** Next.js 16 in `sentry/` (port 3000)
- **Backend:** FastAPI in `backend/` (port 8000)
- **Real-time updates:** WebSocket endpoint at `ws://localhost:8000/api/analyze/ws` for streaming progress during analysis
- **REST fallback:** POST `/api/analyze` for synchronous requests
- See `sentry/src/lib/api.ts` for client implementation using conditional WebSocket/REST based on progress callback

### Data Flow: Analysis Pipeline
1. User draws polygon on map → `MapViewContent.tsx` captures coordinates
2. Frontend sends `AnalysisRequest` via WebSocket → `backend/main.py` analyzes
3. Backend generates grid cells → `utils/gee_satellite.py` extracts satellite features (NDVI, terrain, etc.)
4. ML model predicts risk → `models/risk_model.py` (currently simulated, designed for LightGBM regression)
5. Results stream back as GeoJSON → `RiskHeatmap.tsx` renders colored zones

**Key constraint:** Max analysis area is 1000 km² to prevent Google Earth Engine quota exhaustion.

### Component Structure (Frontend)
```
src/
├── app/page.tsx              # Main dashboard - orchestrates all state
├── components/
│   ├── Map/
│   │   ├── MapViewContent.tsx   # Leaflet map container + toolbar
│   │   ├── RiskHeatmap.tsx      # GeoJSON layer renderer
│   │   └── DrawingTools.tsx     # Polygon drawing (leaflet-draw)
│   ├── Sidebar/
│   │   ├── AnalysisParams.tsx   # Date range, species, threat type
│   │   └── ResultsPanel.tsx     # Priority zones display
│   └── UI/
│       ├── AnalysisProgressOverlay.tsx  # WebSocket progress tracker
│       └── ImageViewerModal.tsx         # Sentinel-2 image carousel
└── lib/
    ├── types.ts          # Shared TypeScript interfaces
    ├── api.ts            # WebSocket + REST client
    └── constants.ts      # Date presets, map config, park definitions
```

## Development Workflows

### Running the Stack
**Backend:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
python main.py
```
Backend runs on `http://localhost:8000`, docs at `/docs`.

**Frontend:**
```bash
cd sentry
pnpm install
pnpm dev
```
Frontend runs on `http://localhost:3000`.

### Google Earth Engine Setup
- Backend requires GCP service account credentials: `backend/ascendant-woods-462020-n0-78d818c9658e.json`
- Authentication happens automatically in `utils/gee_satellite.py:_authenticate()`
- GEE fetches Sentinel-2 imagery and extracts features (NDVI, elevation, slope, etc.)

### Key Testing Files
- `backend/tests/test_gee_satellite.py` - Satellite data extraction
- `backend/tests/test_integration.py` - End-to-end analysis pipeline

## Project-Specific Conventions

### Code Style (CRITICAL)
**NO EMOJIS** - See `backend/RULES.md`. Use text prefixes instead:
```python
# ❌ WRONG
print("✅ Success!")

# ✓ CORRECT
print("SUCCESS: Analysis complete")
```

### TypeScript Patterns
- **State management:** All analysis state lives in `app/page.tsx`, passed down as props (no global state)
- **Type safety:** Import types from `lib/types.ts`, never use `any`
- **Leaflet refs:** Use `useRef<L.Map>` pattern for map instance access (see `MapViewContent.tsx:mapRef`)

### Python Patterns
- **Pydantic models:** All API contracts defined in `main.py` (e.g., `AnalysisRequest`, `LocationInput`)
- **Singleton services:** Use `get_gee_instance()` and `get_model_instance()` for shared resources
- **Error handling:** Raise `HTTPException` for user-facing errors, log stacktraces for debugging

### Map Drawing Workflow (Complex)
Polygon drawing uses `leaflet-draw` with manual completion handling:
1. User clicks "Draw area" → `drawingMode` set to `'polygon'`
2. `MapViewContent.tsx` enables `L.Draw.Polygon` handler
3. User double-clicks to finish → Custom `DRAWSTOP` listener captures vertices
4. Manual polygon creation if Leaflet's `CREATED` event fails (see lines 200-250 in `MapViewContent.tsx`)
5. React re-renders persistent polygon, temporary drawn layers cleared

**Why manual handling?** Leaflet-draw's double-click completion conflicts with map zoom, requiring custom event coordination.

## Model Architecture (Important Context)

### Regression, Not Classification
The ML model predicts **continuous risk scores (0-100)**, not binary high/low risk. This enables fine-grained patrol prioritization.

**Risk levels:**
- `< 40` = safe (green)
- `40-60` = low (yellow)
- `60-80` = medium (orange)
- `80-100` = high/critical (red)

See `backend/guides/model_architecture.md` for full training approach.

### Feature Engineering
Key satellite features extracted per grid cell:
- **Vegetation:** NDVI (0.2-0.8 range, lower = easier poacher access)
- **Proximity:** Distance to park boundary, water, roads, settlements
- **Temporal:** Moon phase (poachers avoid full moon), season, day of week
- **Terrain:** Elevation, slope, ruggedness

Currently simulated in `models/risk_model.py`, designed for LightGBM gradient boosting.

## Common Tasks

### Adding a New Analysis Parameter
1. Update `AnalysisParameters` in `sentry/src/lib/types.ts`
2. Update Pydantic model in `backend/main.py`
3. Add UI control in `sentry/src/components/Sidebar/AnalysisParams.tsx`
4. Use parameter in `backend/models/risk_model.py:predict_batch()`

### Modifying Risk Calculation
Edit `backend/models/risk_model.py:_predict_single()` - this is where feature weights and risk logic live (currently simulated).

### Adding Map Layers
1. Define layer key in `LayerKey` type (`lib/types.ts`)
2. Add to `LAYER_LABELS` in `lib/constants.ts`
3. Conditionally render in `MapViewContent.tsx` based on `advancedOptions.enabledLayers`

## Date Range Constraints
Sentinel-2 data availability: **21-120 days ago** to balance cloud-free imagery with recency. See `DATE_RANGE_PRESETS` in `lib/constants.ts` for recommended windows.

## Integration Points
- **Google Earth Engine:** All satellite queries in `backend/utils/gee_satellite.py`
- **WebSocket protocol:** Progress messages use `{type, step, message, progressPercent}` format
- **GeoJSON:** Grid cells serialized as `FeatureCollection` with `riskScore`, `riskLevel`, `factors` properties

## File References
- Analysis entry point: `backend/main.py:analyze_risk_websocket()`
- Grid generation: `backend/utils/gee_satellite.py:create_grid_cells()`
- Map toolbar: `sentry/src/components/Map/MapViewContent.tsx:MapToolbar`
- Type definitions: `sentry/src/lib/types.ts`
