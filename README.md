# Sentry

Agricultural risk assessment platform powered by satellite imagery and machine learning.

## Overview

Sentry is a geospatial analytics tool designed to help farmers and agricultural teams identify and prioritize high-risk areas for crop pests and diseases. The platform combines real-time satellite data from Google Earth Engine with predictive risk modeling to provide actionable insights for agricultural management and crop protection.

## Key Features

- **Interactive Map Interface**: Draw custom analysis regions or select from predefined agricultural areas
- **Satellite Data Integration**: Automated extraction of Sentinel-2 imagery and environmental indicators (NDVI, soil moisture, weather data)
- **Risk Assessment Model**: LightGBM-based pest and disease risk prediction across multiple crop types
- **Real-time Analysis**: WebSocket-powered streaming analysis with progress tracking
- **Visual Results**: Interactive heatmaps, priority zone identification, and satellite image viewer
- **Crop Health Monitoring**: NDVI-based vegetation health assessment and stress detection

## Technology Stack

### Frontend
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Leaflet** - Interactive mapping library
- **React Leaflet** - React bindings for Leaflet

### Backend
- **FastAPI** - High-performance Python API framework
- **Google Earth Engine** - Satellite imagery and geospatial datasets
- **WebSockets** - Real-time bidirectional communication
- **Python 3.11+** - Core backend runtime

### Data & ML
- **Sentinel-2** - High-resolution satellite imagery (10m resolution)
- **Earth Engine Data Catalog** - Environmental and terrain datasets
- **LightGBM Regressor** - Agricultural pest/disease risk prediction model
- **Synthetic Training Data** - 10,000 samples with correlated agricultural features

## Project Structure

```
sentry/
├── backend/              # FastAPI server
│   ├── main.py          # API endpoints and WebSocket handlers
│   ├── models/          # Risk prediction models
│   ├── services/        # Model trainer, feature extraction, risk prediction
│   ├── data/            # Synthetic data generator and training data
│   ├── utils/           # GEE integration, grid generation
│   └── tests/           # Integration and unit tests
│
└── sentry/              # Next.js frontend
    ├── src/
    │   ├── app/         # Next.js App Router pages
    │   ├── components/  # React components
    │   │   ├── Map/     # Leaflet map components
    │   │   ├── Sidebar/ # Analysis controls
    │   │   └── UI/      # Progress, results, modals
    │   └── lib/         # API client, types, utilities
    └── public/          # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.11+
- Google Cloud Platform account with Earth Engine API enabled
- GCP service account credentials

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Add your GCP service account JSON file to the backend directory

5. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd sentry
```

2. Install dependencies:
```bash
pnpm install
```

3. Start the development server:
```bash
pnpm dev
```

4. Open http://localhost:3000 in your browser

## Usage

1. **Select Location**: Choose an agricultural area from the dropdown or draw a custom polygon on the map
2. **Configure Parameters**: Set date range, crop type, and risk factors (pests, diseases, weather)
3. **Adjust Options**: Fine-tune grid granularity, display threshold, and enabled map layers
4. **Run Analysis**: Click "Run Analysis" to start the agricultural risk assessment
5. **Review Results**: Examine the risk heatmap, priority zones, and satellite imagery sources

## API Endpoints

- `GET /api/health` - Health check and system status
- `POST /api/analyze` - HTTP-based analysis (synchronous)
- `WebSocket /api/analyze/ws` - Streaming analysis with real-time progress

## Environment Variables

### Backend
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP service account JSON

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API base URL (default: http://localhost:8000)

## Development

### Running Tests

Backend:
```bash
cd backend
pytest tests/
```

### Code Style

- Frontend: ESLint + Prettier
- Backend: Black + isort

## Model Training

The agricultural risk model uses LightGBM regression trained on synthetic agricultural data. To train or retrain the model:

### Generate Training Data

```bash
cd backend
python data/synthetic_data_generator.py
```

This generates `backend/data/training_data.csv` with 10,000 samples including:
- Geographic features (lat/lng, elevation, slope)
- Crop features (NDVI, crop type, crop stage)
- Environmental features (soil moisture, temperature, humidity)
- Historical pest data (reports, days since last incident)
- Proximity features (distance to water)

### Train the Model

```bash
cd backend
python services/model_trainer.py
```

This will:
1. Load training data from `data/training_data.csv`
2. Perform feature engineering (derived indices, encoding)
3. Train LightGBM regressor with 5-fold cross-validation
4. Save trained model to `models/trained/risk_model_v1.pkl`
5. Generate metadata JSON with performance metrics

### Model Components

- **`data/synthetic_data_generator.py`** - Generates realistic agricultural training data
- **`services/model_trainer.py`** - Trains and evaluates LightGBM model
- **`services/feature_extractor.py`** - Extracts features from satellite data
- **`models/risk_model.py`** - Loads trained model and makes predictions

## Contributing

This project is under active development. For major changes, please open an issue first to discuss proposed modifications.

## License

Proprietary - All rights reserved

## Acknowledgments

- Google Earth Engine for satellite data infrastructure
- Sentinel-2 mission for high-resolution optical imagery and NDVI data
- OpenStreetMap contributors for geographic data
- LightGBM project for gradient boosting framework
