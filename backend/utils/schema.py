"""
Model Output Schema
Defines the structure of predictions returned by the ML model
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level categories based on score"""
    SAFE = "safe"        # 0-39
    LOW = "low"          # 40-59
    MEDIUM = "medium"    # 60-79
    HIGH = "high"        # 80-100


class GridCell(BaseModel):
    """Individual grid cell prediction"""
    id: str = Field(..., description="Unique identifier for grid cell")
    lat: float = Field(..., description="Latitude of cell center")
    lng: float = Field(..., description="Longitude of cell center")
    risk_score: float = Field(..., ge=0, le=100, description="Continuous risk score 0-100")
    risk_level: RiskLevel = Field(..., description="Categorized risk level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cell-1234",
                "lat": -2.5,
                "lng": 38.7,
                "risk_score": 87.5,
                "risk_level": "high"
            }
        }


class FeatureContribution(BaseModel):
    """Feature importance for a specific prediction"""
    name: str = Field(..., description="Feature name")
    value: float = Field(..., description="Feature value for this cell")
    contribution: float = Field(..., description="Contribution to risk score (percentage)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "dist_to_boundary",
                "value": 500,
                "contribution": 35.2
            }
        }


class CellWithFactors(GridCell):
    """Grid cell with detailed factor breakdown"""
    factors: List[FeatureContribution] = Field(
        default_factory=list,
        description="Top contributing factors for this cell"
    )
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Prediction confidence (0-1)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cell-1234",
                "lat": -2.5,
                "lng": 38.7,
                "risk_score": 87.5,
                "risk_level": "high",
                "factors": [
                    {"name": "dist_to_boundary", "value": 500, "contribution": 35.2},
                    {"name": "ndvi", "value": 0.75, "contribution": 28.1}
                ],
                "confidence": 0.92
            }
        }


class TemporalPrediction(BaseModel):
    """Risk predictions broken down by time of day"""
    dawn: float = Field(..., ge=0, le=100, description="Risk score 5-7am")
    day: float = Field(..., ge=0, le=100, description="Risk score 7am-6pm")
    dusk: float = Field(..., ge=0, le=100, description="Risk score 6-8pm")
    night: float = Field(..., ge=0, le=100, description="Risk score 8pm-5am")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dawn": 72.5,
                "day": 45.2,
                "dusk": 89.3,
                "night": 91.7
            }
        }


class PriorityZone(BaseModel):
    """High-priority patrol zone"""
    id: str = Field(..., description="Zone identifier")
    name: str = Field(..., description="Human-readable zone name")
    risk_score: float = Field(..., ge=0, le=100, description="Average risk score for zone")
    cell_count: int = Field(..., description="Number of cells in this zone")
    center: dict = Field(..., description="Zone center coordinates {lat, lng}")
    bounds: dict = Field(..., description="Zone bounding box")
    factors: List[FeatureContribution] = Field(..., description="Top risk factors")
    temporal: Optional[TemporalPrediction] = Field(None, description="Time-of-day breakdown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "zone-1",
                "name": "Northern Boundary Sector",
                "risk_score": 87.5,
                "cell_count": 12,
                "center": {"lat": -2.45, "lng": 38.92},
                "bounds": {
                    "southWest": {"lat": -2.5, "lng": 38.85},
                    "northEast": {"lat": -2.4, "lng": 39.0}
                },
                "factors": [
                    {"name": "dist_to_boundary", "value": 350, "contribution": 35.2},
                    {"name": "vegetation_density", "value": 0.78, "contribution": 28.1}
                ],
                "temporal": {
                    "dawn": 72.5,
                    "day": 45.2,
                    "dusk": 89.3,
                    "night": 91.7
                }
            }
        }


class RiskSummary(BaseModel):
    """Overall risk statistics for the analysis area"""
    total_cells: int = Field(..., description="Total grid cells analyzed")
    high_risk_cells: int = Field(..., description="Cells with risk >= 80")
    medium_risk_cells: int = Field(..., description="Cells with risk 60-79")
    low_risk_cells: int = Field(..., description="Cells with risk 40-59")
    safe_cells: int = Field(..., description="Cells with risk < 40")
    average_risk: float = Field(..., ge=0, le=100, description="Mean risk score")
    max_risk: float = Field(..., ge=0, le=100, description="Highest risk score found")
    trend: Optional[str] = Field(None, description="Compared to previous analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_cells": 250,
                "high_risk_cells": 12,
                "medium_risk_cells": 45,
                "low_risk_cells": 88,
                "safe_cells": 105,
                "average_risk": 42.5,
                "max_risk": 94.2,
                "trend": "Risk up 12% from last week"
            }
        }


class GeoJSONFeature(BaseModel):
    """Single GeoJSON feature for a grid cell"""
    type: Literal["Feature"] = "Feature"
    geometry: dict = Field(..., description="GeoJSON geometry (Polygon)")
    properties: CellWithFactors = Field(..., description="Cell properties including risk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [38.7, -2.5],
                            [38.71, -2.5],
                            [38.71, -2.51],
                            [38.7, -2.51],
                            [38.7, -2.5]
                        ]
                    ]
                },
                "properties": {
                    "id": "cell-1234",
                    "lat": -2.5,
                    "lng": 38.7,
                    "risk_score": 87.5,
                    "risk_level": "high",
                    "factors": [],
                    "confidence": 0.92
                }
            }
        }


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection for map rendering"""
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": []
            }
        }


class ModelOutput(BaseModel):
    """
    Complete output from the ML model prediction pipeline
    This is what gets returned to the frontend
    """
    geoJSON: GeoJSONFeatureCollection = Field(..., description="Map-ready risk heatmap")
    priorities: List[PriorityZone] = Field(..., description="Top priority patrol zones")
    summary: RiskSummary = Field(..., description="Overall statistics")
    temporal: Optional[dict] = Field(None, description="Time-specific GeoJSON layers")
    factors: Optional[dict] = Field(None, description="Global feature importance")
    metadata: dict = Field(
        default_factory=dict,
        description="Analysis metadata (date, model version, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "geoJSON": {
                    "type": "FeatureCollection",
                    "features": []
                },
                "priorities": [
                    {
                        "id": "zone-1",
                        "name": "Northern Boundary Sector",
                        "risk_score": 87.5,
                        "cell_count": 12,
                        "center": {"lat": -2.45, "lng": 38.92},
                        "bounds": {
                            "southWest": {"lat": -2.5, "lng": 38.85},
                            "northEast": {"lat": -2.4, "lng": 39.0}
                        },
                        "factors": []
                    }
                ],
                "summary": {
                    "total_cells": 250,
                    "high_risk_cells": 12,
                    "medium_risk_cells": 45,
                    "low_risk_cells": 88,
                    "safe_cells": 105,
                    "average_risk": 42.5,
                    "max_risk": 94.2
                },
                "metadata": {
                    "model_version": "1.0.0",
                    "analysis_date": "2024-11-13",
                    "processing_time_seconds": 8.5
                }
            }
        }


# Helper functions for converting raw predictions to schema

def categorize_risk_score(score: float) -> RiskLevel:
    """Convert continuous risk score to category"""
    if score < 40:
        return RiskLevel.SAFE
    elif score < 60:
        return RiskLevel.LOW
    elif score < 80:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def create_grid_cell(
    cell_id: str,
    lat: float,
    lng: float,
    risk_score: float,
    factors: Optional[List[dict]] = None,
    confidence: float = 1.0
) -> CellWithFactors:
    """Create a grid cell object from raw prediction"""
    return CellWithFactors(
        id=cell_id,
        lat=lat,
        lng=lng,
        risk_score=risk_score,
        risk_level=categorize_risk_score(risk_score),
        factors=[FeatureContribution(**f) for f in (factors or [])],
        confidence=confidence
    )


def create_geojson_feature(
    cell: CellWithFactors,
    polygon_coords: List[List[float]]
) -> GeoJSONFeature:
    """Convert grid cell to GeoJSON feature"""
    return GeoJSONFeature(
        type="Feature",
        geometry={
            "type": "Polygon",
            "coordinates": [polygon_coords]
        },
        properties=cell
    )
