import {
  AdvancedOptions,
  AnalysisParameters,
  LayerKey,
  MapConfig,
  ParkOption,
  PinTypeOption,
  TimeOfDay,
} from "./types";

const toIsoDate = (date: Date) => date.toISOString().split("T")[0];

const today = new Date();
const yesterday = new Date(today);
yesterday.setDate(today.getDate() - 1);
const maxSelectableDate = new Date(yesterday);
const minSelectableDate = new Date(maxSelectableDate);
minSelectableDate.setDate(maxSelectableDate.getDate() - 150);

const dateDaysAgo = (daysAgo: number) => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date;
};

const clampIsoRange = (range: { start: string; end: string }) => {
  let { start, end } = range;
  const min = toIsoDate(minSelectableDate);
  const max = toIsoDate(maxSelectableDate);

  if (start < min) start = min;
  if (end > max) end = max;
  if (start > end) start = end;

  return { start, end };
};

export const DATE_RANGE_LIMITS = {
  min: toIsoDate(minSelectableDate),
  max: toIsoDate(maxSelectableDate),
};

export interface DateRangePreset {
  id: string;
  label: string;
  description: string;
  startDaysAgo: number;
  endDaysAgo: number;
}

export const DATE_RANGE_PRESETS: DateRangePreset[] = [
  {
    id: "recent-safe",
    label: "Recent (5–3 weeks ago)",
    description: "Balances recency with cloud-free Sentinel-2 coverage.",
    startDaysAgo: 35,
    endDaysAgo: 21,
  },
  {
    id: "wide-window",
    label: "Broad window (9–2 weeks ago)",
    description: "Wider sample that is unlikely to be fully cloudy.",
    startDaysAgo: 63,
    endDaysAgo: 14,
  },
  {
    id: "dry-season",
    label: "Dry season band (4–3 months ago)",
    description: "Peak dry season imagery with minimal cloud cover.",
    startDaysAgo: 120,
    endDaysAgo: 75,
  },
];

export const resolveDateRangePreset = (preset: DateRangePreset) => {
  const start = toIsoDate(dateDaysAgo(preset.startDaysAgo));
  const end = toIsoDate(dateDaysAgo(preset.endDaysAgo));
  return clampIsoRange({ start, end });
};

const defaultDateRange = resolveDateRangePreset(DATE_RANGE_PRESETS[0]);

export const MAP_CONFIG: MapConfig = {
  center: { lat: -1.2921, lng: 36.8219 },
  zoom: 6,
  minZoom: 5,
  maxZoom: 18,
  tileLayer: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  attribution: "© OpenStreetMap contributors",
};

export const KENYAN_PARKS: ParkOption[] = [
  {
    id: "rift-valley",
    name: "Rift Valley (Maize Belt)",
    bounds: {
      southWest: { lat: -0.5, lng: 35.0 },
      northEast: { lat: 0.5, lng: 36.0 },
    },
    description: "Major maize growing region.",
  },
  {
    id: "central",
    name: "Central (Coffee/Tea)",
    bounds: {
      southWest: { lat: -1.0, lng: 36.5 },
      northEast: { lat: -0.3, lng: 37.5 },
    },
    description: "High altitude coffee and tea plantations.",
  },
];

export const CROP_OPTIONS = [
  "Maize",
  "Wheat",
  "Coffee",
  "Tea",
  "Beans",
  "Sorghum",
];

export const RISK_FACTOR_OPTIONS: string[] = [
  "Drought",
  "Flood",
  "Pests",
  "Market",
  "Soil Degradation",
];

export const TIME_OF_DAY_OPTIONS: TimeOfDay[] = [
  "dawn",
  "day",
  "dusk",
  "night",
];

export const DEFAULT_ANALYSIS_PARAMETERS: AnalysisParameters = {
  dateRange: {
    start: defaultDateRange.start,
    end: defaultDateRange.end,
  },
  timeOfDay: ["dawn", "day", "dusk", "night"],
  cropType: "Maize",
  riskFactors: ["Drought", "Market"],
};

export const DEFAULT_ADVANCED_OPTIONS: AdvancedOptions = {
  displayThreshold: 40,
  gridGranularity: 1,
  enabledLayers: ["riskHeatmap"],
  temporalFocus: [],
};

export const LAYER_LABELS: Record<LayerKey, string> = {
  riskHeatmap: "Risk Heatmap",
  boundaries: "Park Boundaries",
  water: "Water Sources",
  roads: "Roads",
  incidents: "Historical Incidents",
  settlements: "Settlements",
  "temporal:dawn": "Dawn Layer",
  "temporal:day": "Day Layer",
  "temporal:dusk": "Dusk Layer",
  "temporal:night": "Night Layer",
};

export const RISK_LEVEL_COLORS = {
  safe: "#7BC67E",
  low: "#F7E967",
  medium: "#FFB347",
  high: "#FF6B6B",
};

export const SIDEBAR_WIDTH = 400;

export const COLOR_PALETTE = {
  sidebarBackground: "#E0FFC2",
  mapBackground: "#F5FFEB",
  primary: "#064734",
  primaryHover: "#085d45",
  surface: "#FFFFFF",
  text: "#064734",
  mutedText: "#2E6B56",
};

export const PIN_TYPE_OPTIONS: PinTypeOption[] = [
  {
    id: "priority-zone",
    label: "Priority Patrol Pin",
    description: "Mark a hotspot that needs ranger attention",
    color: "#d97706",
  },
  {
    id: "intel-note",
    label: "Intel Note",
    description: "Drop notes about intelligence sightings",
    color: "#2563eb",
  },
  {
    id: "support",
    label: "Support Request",
    description: "Flag areas requiring supplies or backup",
    color: "#dc2626",
  },
];
