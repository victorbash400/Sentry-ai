import { AnalysisRequest, AnalysisResult } from "./types";

const API_BASE_URL = "http://localhost:8000";
const ANALYZE_ENDPOINT = "/api/analyze";
const ANALYZE_WS_ENDPOINT = "ws://localhost:8000/api/analyze/ws";

export type ProgressCallback = (progress: {
  type: 'status' | 'progress' | 'complete' | 'error';
  step?: string;
  message?: string;
  [key: string]: unknown;
}) => void;

const buildDefaultResult = (): AnalysisResult => ({
  geoJSON: null,
  priorities: [],
  summary: null,
  temporal: {},
  metadata: { placeholder: true },
});

export interface InsuranceAnalysisRequest {
  agri_risk_score: number;
  lat: number;
  lon: number;
  override_factors?: Record<string, number>;
}

export interface InsuranceAnalysisResponse {
  risk_score: number;
  premium: number;
  policy_type: string;
  max_coverage: number;
  deductible: number;
  factors: { name: string; impact: string; value: string }[];
  context_data: Record<string, number>;
  coverage_period?: string;
  recommended_actions?: string[];
}

export async function runInsuranceAnalysis(data: InsuranceAnalysisRequest): Promise<InsuranceAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/insurance/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Insurance analysis failed');
  }

  return response.json();
}

export async function runAnalysis(
  payload: AnalysisRequest,
  options?: { signal?: AbortSignal; onProgress?: ProgressCallback }
): Promise<AnalysisResult> {
  // Use WebSocket if progress callback provided
  if (options?.onProgress) {
    return runAnalysisWebSocket(payload, options.onProgress, options.signal);
  }

  const response = await fetch(ANALYZE_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: options?.signal,
  });

  if (!response.ok) {
    const detail = await safeParseError(response);
    throw new Error(detail ?? "Failed to run analysis");
  }

  const result = (await response.json()) as AnalysisResult;
  return {
    ...buildDefaultResult(),
    ...result,
  };
}

async function runAnalysisWebSocket(
  payload: AnalysisRequest,
  onProgress: ProgressCallback,
  signal?: AbortSignal
): Promise<AnalysisResult> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(ANALYZE_WS_ENDPOINT);
    let result: AnalysisResult | null = null;

    // Handle abort signal
    if (signal) {
      signal.addEventListener('abort', () => {
        ws.close();
        reject(new Error('Analysis cancelled'));
      });
    }

    ws.onopen = () => {
      console.log('🟢 [WebSocket] Connected');
      ws.send(JSON.stringify(payload));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('🔵 [WebSocket] Received:', data.type, data.step, data.message);

        if (data.type === 'complete') {
          console.log('🎯 [WebSocket] Complete data received:', data.data);
          console.log('🖼️ [WebSocket] satelliteImages:', data.data?.satelliteImages);
          result = {
            ...buildDefaultResult(),
            ...data.data,
          };
          console.log('✅ [WebSocket] Final result:', result);
        }

        onProgress(data);

        if (data.type === 'error') {
          ws.close();
          reject(new Error(data.message || 'Analysis failed'));
        } else if (data.type === 'complete') {
          ws.close();
        }
      } catch (error) {
        console.error('🔴 [WebSocket] Parse error:', error);
        ws.close();
        reject(error);
      }
    };

    ws.onerror = (error) => {
      console.error('🔴 [WebSocket] Error:', error);
      reject(new Error('WebSocket connection failed'));
    };

    ws.onclose = () => {
      console.log('🔴 [WebSocket] Closed');
      if (result) {
        resolve(result);
      } else {
        reject(new Error('Connection closed without result'));
      }
    };
  });
}

async function safeParseError(response: Response) {
  try {
    const data = await response.json();
    if (typeof data?.message === "string") {
      return data.message;
    }
  } catch {
    // no-op parsing fallback
  }
  return response.statusText;
}

export interface PDFRequest {
  farmName: string;
  lat: number;
  lon: number;
  areaKm2: number;
  cropType: string;
  risk_score: number;
  policy_type: string;
  max_coverage: number;
  deductible: number;
  premium: number;
  coverage_period: string;
  factors: { name: string; impact: string; value: string }[];
  recommended_actions: string[];
  polygon?: { lat: number; lng: number }[];
}

export async function generateInsurancePDF(data: PDFRequest): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/insurance/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to generate PDF');
  }

  return response.blob();
}
