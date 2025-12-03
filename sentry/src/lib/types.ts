export type TimeOfDay = "dawn" | "day" | "dusk" | "night";

export type RiskFactorType = "Drought" | "Flood" | "Pests" | "Market" | "Soil Degradation";

export type LayerKey =
  | "riskHeatmap"
  | "boundaries"
  | "water"
  | "roads"
  | "incidents"
  | "settlements"
  | "temporal:dawn"
  | "temporal:day"
  | "temporal:dusk"
  | "temporal:night";

export interface LatLng {
  lat: number;
  lng: number;
}

export interface LatLngBounds {
  southWest: LatLng;
  northEast: LatLng;
}

export type DrawingMode = "none" | "polygon" | "pin";

export interface LocationSelection {
  type: "park" | "custom";
  parkId?: string;
  parkName?: string;
  polygon?: LatLng[];
  point?: LatLng;
  bounds: LatLngBounds;
}

export interface DateRange {
  start: string; // ISO date string
  end: string; // ISO date string
}

export interface AnalysisParameters {
  dateRange: DateRange;
  timeOfDay: TimeOfDay[];
  cropType: string;
  riskFactors: string[];
}

export interface AdvancedOptions {
  displayThreshold: number;
  gridGranularity: 1 | 2 | 5;
  enabledLayers: LayerKey[];
  temporalFocus: TimeOfDay[];
}

export interface RiskFactor {
  name: string;
  contribution: number;
  description?: string;
}

export interface PriorityZone {
  id: string;
  name: string;
  riskScore: number;
  center?: LatLng;
  location?: LatLng;
  factors: RiskFactor[];
}

export interface GridCell {
  id: string;
  polygon: LatLng[];
  riskScore: number;
  riskLevel: "safe" | "low" | "medium" | "high";
  factors: RiskFactor[];
}

export interface MarketData {
  currentPrice: number;
  currency: string;
  trend: "up" | "down" | "stable";
  volatility: "Low" | "Medium" | "High";
  forecast: string;
}

export interface AnalysisSummary {
  totalCells: number;
  highRiskCells: number;
  mediumRiskCells?: number;
  lowRiskCells?: number;
  safeCells?: number;
  averageRisk: number;
  trend?: "increasing" | "stable" | "decreasing";
  message?: string;
  areaKm2?: number;
  imageCount?: number;
}

export interface SatelliteImage {
  url: string;
  id: string;
  timestamp?: number;
}

export interface GeoJsonFeatureCollection {
  type: "FeatureCollection";
  features: Array<Record<string, unknown>>;
}

export interface AnalysisResult {
  geoJSON: GeoJsonFeatureCollection | null;
  priorities: PriorityZone[];
  summary: AnalysisSummary | null;
  temporal?: Partial<Record<TimeOfDay, GeoJsonFeatureCollection>>;
  metadata?: Record<string, unknown>;
  satelliteImages?: SatelliteImage[];
  marketData?: MarketData;
}

export interface AnalysisRequest {
  location: LocationSelection;
  parameters: AnalysisParameters;
  advanced: AdvancedOptions;
}

export interface ParkOption {
  id: string;
  name: string;
  description?: string;
  bounds: LatLngBounds;
}

export interface MapConfig {
  center: LatLng;
  zoom: number;
  minZoom: number;
  maxZoom: number;
  tileLayer: string;
  attribution: string;
}

export interface PinTypeOption {
  id: string;
  label: string;
  description?: string;
  color: string;
}

export interface MapPin {
  id: string;
  typeId: string;
  position: LatLng;
  createdAt: number;
}
