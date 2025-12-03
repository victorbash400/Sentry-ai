```markdown
# SENTRY - Poaching Hotspot Intelligence Platform

## Overview
Sentry is a predictive intelligence tool that helps wildlife rangers identify high-risk poaching zones before incidents occur. Instead of reactive patrolling, rangers get actionable intelligence about WHERE poaching is most likely to happen in the coming days.

**Problem:** Rangers patrol massive protected areas with limited resources. They need to know where threats are most likely.

**Solution:** Sentry analyzes satellite imagery, environmental patterns, and historical data to generate risk heatmaps showing "patrol here first" zones.

**Target Users:** Kenya Wildlife Service rangers, park management, conservation NGOs

---

## How It Works

### User Perspective
1. Ranger opens Sentry dashboard
2. Selects location (park or coordinates)
3. Sets date range (typically next 7 days)
4. Optionally filters by species or threat type
5. Clicks "Run Analysis"
6. Gets interactive map with color-coded risk zones
7. Sees top priority patrol areas with explanations
8. Can export report or generate optimal patrol route

### System Perspective
1. Frontend sends analysis request to backend
2. Backend pulls latest satellite imagery for that area
3. Extracts environmental features (vegetation, water proximity, boundaries, etc.)
4. Loads historical incident data for context
5. Runs all features through trained LightGBM model
6. Model outputs risk scores for grid cells across the park
7. Backend converts predictions to GeoJSON
8. Frontend displays interactive heatmap
9. User explores results and takes action

---

## Model Architecture

### Model Type: LightGBM Gradient Boosting
- **Not binary classification** - this is regression predicting risk scores (0-100)
- LightGBM chosen for speed, accuracy, and ability to handle spatial data well
- Model trained on historical poaching incidents with environmental context

### Why LightGBM?
- Fast inference (important for real-time analysis)
- Handles mixed feature types well (continuous, categorical)
- Native feature importance (helps explain predictions)
- Works well with imbalanced spatial data
- Lower memory footprint than XGBoost

### Training Approach
- Historical incidents (2020-2024) from multiple Kenyan parks
- Each incident location gets environmental features extracted
- Negative samples generated from verified safe zones
- Target: risk score based on incident density + severity
- Cross-validation by park (model must generalize to unseen locations)

### Features (15-20 features)
**Vegetation:**
- NDVI (Normalized Difference Vegetation Index) - dense vegetation = cover for poachers
- Vegetation type (forest, grassland, scrub)

**Proximity Metrics:**
- Distance to park boundary (poachers enter from edges)
- Distance to nearest water source (animals congregate at water)
- Distance to nearest road (vehicle access)
- Distance to nearest settlement (human pressure)

**Historical Context:**
- Incident density within 5km radius
- Incident recency (days since last incident nearby)
- Seasonal incident patterns

**Temporal:**
- Moon phase (poachers avoid full moons - visibility)
- Season (dry season = easier access)
- Day of week

**Topographical:**
- Elevation
- Slope (steep areas harder to patrol)
- Terrain ruggedness

**Species-Specific (if selected):**
- Known migration routes for that species
- Breeding season indicators
- Watering patterns

### Model Output Format
The model returns risk scores (0-100) for each grid cell, which get packaged into multiple useful formats:

**Primary Output: Risk Heatmap**
- Grid of 1km x 1km cells (configurable)
- Each cell has risk score 0-100
- Converted to risk levels: Safe (<40), Low (40-60), Medium (60-80), High (80-100)

**Secondary Outputs (automatically generated):**

1. **Temporal Breakdown** - Risk by time of day
   - Dawn risk map (5-7am)
   - Day risk map (7am-6pm)
   - Dusk risk map (6-8pm)
   - Night risk map (8pm-5am)
   - Shows "patrol dusk for maximum impact"

2. **Threat Type Classification** - If model trained on labeled threat types
   - Poaching risk overlay
   - Illegal logging risk overlay
   - Encroachment risk overlay
   - Each threat has different environmental signatures

3. **Species-Specific Views** - If user selected a species
   - Filters predictions to areas where that species is present
   - Adjusts weights based on species behavior (elephants vs rhinos)

4. **Anomaly Detection**
   - Zones where risk suddenly spiked vs historical baseline
   - "This area is usually safe but risk jumped 300% this week"
   - Helps catch emerging threats

5. **Factor Attribution**
   - For each high-risk zone, shows WHY it's high-risk
   - "65% vegetation density + 20% boundary proximity + 15% historical incidents"
   - Uses LightGBM's built-in feature importance per prediction

6. **Trend Analysis**
   - Compares current risk to previous week/month
   - "Northern sector risk up 23% compared to last week"
   - Helps track if interventions are working

---

## Frontend Architecture

### Technology
- **Framework:** Next.js 14 with App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS with custom color scheme
- **Map Library:** Leaflet.js (react-leaflet)
- **Icons:** Lucide React

### Color Scheme
- **Sidebar background:** #E0FFC2 (light lime green)
- **Map area background:** #F5FFEB (very light green, subtle)
- **Primary actions:** #064734 (dark forest green)
- **Cards/inputs:** #FFFFFF (white for contrast)
- **Text:** #064734 (dark green on light backgrounds)

### Layout
Collapsible sidebar interface:
- **Left sidebar (400px expanded, 72px collapsed):** All inputs, parameters, and results summary with collapse/expand control
- **Top toolbar (fixed):** Map style selector, drawing tools, layer controls
- **Right map area (flex):** Interactive Leaflet map with risk overlay

### Component Structure

**Main Dashboard (page.tsx)**
- Orchestrates entire UI
- Manages analysis state (location, parameters, results, pins, drawing mode)
- Handles sidebar collapse/expand state
- Handles API communication
- Responsive layout with smooth transitions

**Sidebar Component**
Collapsible panel with collapse/expand button integrated into the sidebar itself. When expanded (400px), shows card-based sections:

1. **Location Input** (white card)
   - Search dropdown for Kenyan protected areas (searchable)
   - "Draw custom area on map" button (activates polygon drawing)
   - "Place patrol pin on map" button (for marking specific zones)
   - Current selection summary with pin count
   - Clear selection button
   - Live polygon metrics (points, area, perimeter)

2. **Analysis Parameters** (white card)
   - Date range picker (start/end dates, default: next 7 days)
   - Time of day toggle buttons (dawn/day/dusk/night) with icons
   - Species filter dropdown (All, Elephants, Rhinos, Lions, Giraffes, Zebras)
   - Threat type checkboxes (poaching, logging, fishing, encroachment)

3. **Advanced Options** (white card, expandable)
   - **Display threshold slider:** Only show zones above X% risk (filters output)
   - **Grid granularity radio buttons:** 1km vs 2km vs 5km cells
   - **Layer visibility checkboxes:** Risk heatmap, boundaries, water, roads, incidents, settlements, temporal layers
   - These are display/filtering options, NOT model tuning

4. **Run Analysis** (white card)
   - Primary "Run analysis" button
   - Loading spinner with status text when processing

5. **Results Panel** (white card, only appears after analysis)
   - High-risk alert banner (if detected)
   - Top 3 patrol priorities as clickable cards showing risk score and factors
   - Action buttons:
     - Generate patrol route
     - Export PDF report
     - Schedule follow-up analysis

When collapsed (72px), sidebar shows only the expand icon button at the top.

**MapView Component**
- Leaflet map with switchable base layers:
  - OpenStreetMap (default street view)
  - Terrain (OpenTopoMap with contours and elevation)
  - Satellite (Esri world imagery)
- GeoJSON overlay showing risk heatmap
- Color gradient: Green (safe) → Yellow → Orange → Red (high risk)
- Interactive polygon drawing mode (click to add points, double-click to finish)
- Pin placement mode for marking priority zones (with pin type selection)
- Interactive features:
  - Click zone → show detailed risk breakdown
  - Click pin → show pin details with remove option
  - Auto-zoom to selected park or drawn area

**Top Toolbar** (fixed white bar at top of map)
Contains horizontally arranged controls:
- **Base map selector:** Dropdown to switch between OpenStreetMap/Terrain/Satellite
- **Drawing tools section:**
  - "Draw area" button (activates/cancels polygon drawing)
  - "Clear area" button
  - Active drawing indicator with instructions
  - Polygon summary stats (points, area, perimeter)
- **Pin tools section:**
  - Pin type selector dropdown (Priority Patrol, Intel Note, Support Request)
  - "Place pin" / "Stop placing pins" button
  - "Clear pins (count)" button
- **Layer controls:**
  - "Map layers" button that opens dropdown with checkboxes for:
    - Risk heatmap, Park boundaries, Water sources, Roads, Historical incidents, Settlements, Temporal layers

### User Interactions

**Standard Flow:**
1. User selects "Tsavo National Park" from dropdown
2. Leaves default date range (next 7 days)
3. Clicks "Run Analysis"
4. Loading spinner appears on map
5. Backend processes (5-15 seconds)
6. Map fills with color-coded risk zones
7. Results panel slides in with top priorities
8. User clicks "Northern Boundary Sector" priority
9. Map zooms to that zone
10. Popup shows detailed risk factors
11. User clicks "Generate Patrol Route"
12. Optimal route drawn on map connecting high-risk zones

**Advanced Flow:**
1. User clicks "Draw custom area on map" button in sidebar
2. Clicks points on map to create polygon (sees live metrics in sidebar)
3. Double-clicks to finish drawing
4. Places patrol pins at specific hotspots using "Place patrol pin on map"
5. Opens Advanced Options in sidebar
6. Sets display threshold to 70% (only show high/medium risk)
7. Changes grid size to 2km for faster processing
8. Toggles layer visibility options
9. Collapses sidebar for better map view using collapse button
10. Runs analysis
11. Gets more detailed, focused results with clean full-map view

### API Integration

**Single Endpoint:** `POST /api/analyze`

Frontend sends:
```
{
  location: park name or coordinates,
  dateRange: start and end dates,
  parameters: species, threats, time of day,
  advanced: display options
}
```

Frontend receives:
```
{
  geoJSON: risk heatmap polygons with scores,
  temporal: separate GeoJSON for dawn/day/dusk/night,
  priorities: array of top zones with details,
  summary: stats and trends,
  factors: attribution data
}
```

Frontend then:
1. Renders main GeoJSON on Leaflet map with color coding
2. Populates results panel with priorities
3. Stores temporal/threat-specific layers for toggling
4. Enables interactive features

### State Management
- React hooks (useState, useEffect)
- No complex state library needed for hackathon
- Loading states for async operations
- Error boundaries for API failures

---

## Backend Architecture

### Technology
- **Framework:** Flask or FastAPI (Python 3.10+)
- **ML:** LightGBM (saved as .pkl file)
- **Geospatial:** GeoPandas, Rasterio, Shapely
- **Satellite Data:** Google Earth Engine API
- **Data Processing:** Pandas, NumPy

### File Structure
```
/backend
  /app.py                           # Main Flask/FastAPI server
  /routes
    /analyze.py                     # POST /api/analyze endpoint
  /ml
    /predictor.py                   # Model wrapper class
    /models
      /poaching_model_v1.pkl        # Trained LightGBM model
  /data_processing
    /satellite.py                   # Google Earth Engine integration
    /features.py                    # Feature extraction logic
    /geojson_builder.py             # Convert predictions to GeoJSON
  /data
    /static
      /kenya_parks.geojson          # Park boundaries
      /water_sources.geojson        # Rivers, waterholes
      /roads.geojson                # Road network
    /historical
      /incidents_2020_2024.csv      # Past poaching data
  /utils
    /distance_calc.py               # Spatial distance functions
    /moon_phase.py                  # Lunar calendar calculations
```

### Core Components

**1. API Endpoint (`/routes/analyze.py`)**

Receives analysis request from frontend, orchestrates the pipeline:
- Validates input parameters
- Determines bounding box for area of interest
- Triggers satellite data fetch
- Runs feature extraction
- Calls model predictor
- Builds response GeoJSON
- Returns everything to frontend

**2. Satellite Data Module (`/data_processing/satellite.py`)**

Connects to Google Earth Engine:
- Authenticates with GEE
- Queries Sentinel-2 imagery for date range and bounding box
- Filters clouds
- Extracts latest clear images
- Calculates NDVI (vegetation index)
- Returns raster data for the area

**3. Feature Extractor (`/data_processing/features.py`)**

For each grid cell in the analysis area:
- Reads NDVI value from satellite raster
- Loads park boundary shapefile
- Calculates distance to nearest boundary point
- Loads water sources GeoJSON
- Calculates distance to nearest water
- Loads road network
- Calculates distance to nearest road
- Queries historical incidents CSV
- Counts incidents within 5km radius
- Gets moon phase for analysis dates
- Determines season
- Assembles feature vector for that cell

Returns: DataFrame with one row per grid cell, columns = features

**4. Model Predictor (`/ml/predictor.py`)**

Wrapper around the trained LightGBM model:
- Loads model.pkl on startup
- Receives feature DataFrame
- Runs model.predict() to get risk scores
- Uses model.predict_contrib() to get feature attributions
- Applies any post-processing (scaling, clipping)
- Returns predictions + attributions

**5. GeoJSON Builder (`/data_processing/geojson_builder.py`)**

Converts model predictions into map-ready format:
- Takes predictions DataFrame (grid_id, lat, lng, risk_score, features)
- Creates polygon for each grid cell
- Assigns risk level (safe/low/medium/high)
- Adds properties (risk score, factors, temporal breakdown)
- Builds FeatureCollection in GeoJSON format
- Generates separate layers for temporal/threat-specific views
- Returns complete GeoJSON structure

**6. Historical Data Handler**

Manages past incident data:
- CSV with columns: date, lat, lng, species, threat_type, severity
- Spatial indexing for fast proximity queries
- Aggregation functions (incidents per zone, trends over time)
- Used both for feature extraction and anomaly detection

### Data Flow

**Request comes in:**
```
Frontend → /api/analyze
  ↓
Validate location, dates, parameters
  ↓
Generate grid of cells covering the area (1km x 1km)
  ↓
For each grid cell:
  - Fetch satellite data → Calculate NDVI
  - Load shapefiles → Calculate distances
  - Query historical data → Count nearby incidents
  - Get temporal data → Moon phase, season
  ↓
Assemble features into DataFrame
  ↓
Pass to LightGBM model
  ↓
Get risk scores + attributions
  ↓
Build GeoJSON with predictions
  ↓
Add temporal breakdowns, anomalies, trends
  ↓
Return JSON response to frontend
```

### Model Inference

Model is loaded once at server startup, not per request:

```python
# On server start
model = lgb.Booster(model_file='poaching_model_v1.pkl')

# Per request
predictions = model.predict(features_df)
attributions = model.predict(features_df, pred_contrib=True)
```

LightGBM inference is fast (milliseconds for hundreds of cells), but satellite data fetch and feature extraction are the bottleneck (5-15 seconds).

### Advanced Options Implementation

These are handled AFTER model prediction, not during:

**Display Threshold (e.g., "only show >70% risk"):**
- Model predicts all cells
- Backend filters GeoJSON to only include cells above threshold
- Reduces payload size, cleaner map

**Grid Granularity (1km vs 5km cells):**
- Determines how many cells to generate
- 1km = more detail, slower processing
- 5km = faster, less granular
- Model runs on whatever grid is requested

**Temporal Focus:**
- Model can output time-specific predictions if trained with time-of-day feature
- Or backend can weight existing predictions based on temporal patterns
- Example: Night risk = base_risk * 1.3 (poaching peaks at night)

### Performance Optimizations

**Caching:**
- Satellite imagery cached for 24 hours (doesn't change that fast)
- Park boundaries/roads/water cached in memory
- Historical data indexed spatially

**Async Processing:**
- Satellite fetch and feature extraction can run in parallel for different zones
- Use async/await or threading

**Response Streaming:**
- Can stream GeoJSON chunks as they're ready
- Frontend shows partial results while rest loads

### Error Handling

**Common failures:**
- Google Earth Engine rate limits → retry with backoff
- No satellite imagery (cloudy) → use most recent clear image
- Invalid coordinates → return 400 with clear message
- Model prediction fails → return 500, log for debugging

**Graceful degradation:**
- If satellite data unavailable, use last known NDVI values
- If historical data incomplete, use lower confidence threshold
- Always return something useful to frontend

---

## Data Sources

### Satellite Imagery
**Source:** Google Earth Engine (Sentinel-2)
- **Resolution:** 10m per pixel
- **Bands:** Red, NIR (for NDVI calculation)
- **Update frequency:** Every 5 days
- **Coverage:** Global, including all Kenyan parks
- **Access:** Free via Google Earth Engine API (requires account)

### Park Boundaries
**Source:** World Database on Protected Areas (WDPA)
- Kenya-specific shapefile with all national parks and reserves
- Downloaded once, stored locally

### Water Sources
**Source:** OpenStreetMap via Overpass API
- Rivers, lakes, waterholes tagged as water features
- Extract for Kenya bounding box
- Convert to GeoJSON, store locally

### Roads & Settlements
**Source:** OpenStreetMap
- Road network (all types)
- Settlements (villages, towns)
- Used for accessibility metrics

### Historical Incidents
**Source:** Multiple (requires manual compilation)
- Kenya Wildlife Service reports (if available)
- News articles (web scraping)
- Academic papers on poaching incidents
- NGO reports
- Format: CSV with date, location, species, type

**Challenge:** This is the hardest data to get. May need to:
- Scrape news sites systematically
- Contact KWS directly
- Use proxy data (seizure records, arrests)
- Start with small dataset and extrapolate

---

