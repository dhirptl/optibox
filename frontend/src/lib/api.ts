import { parseSiloCsv } from "./parsing";
import type {
  RandomizeResponse,
  RunSimulationResponse,
  SiloState,
  SimulationTimelineFrame,
} from "./types";

export const API_BASE = "http://localhost:8000";

export async function randomizeSilo(
  numBoxes: number,
): Promise<RandomizeResponse> {
  const res = await fetch(`${API_BASE}/api/randomize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ num_boxes: numBoxes }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `randomize failed: ${res.status}`);
  }
  return res.json();
}

export async function resetSilo(): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`reset failed: ${res.status}`);
  }
  return res.json();
}

export type RunSimulationParams = {
  ticks?: number;
  inboundSeed?: number;
  numBoxes?: number;
};

export async function runSimulation({
  ticks = 3600,
  inboundSeed = 42,
  numBoxes,
}: RunSimulationParams = {}): Promise<RunSimulationResponse> {
  const body: Record<string, number> = {
    ticks,
    inbound_seed: inboundSeed,
  };
  if (typeof numBoxes === "number") {
    body.num_boxes = numBoxes;
  }

  const res = await fetch(`${API_BASE}/api/run-simulation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.error || `run simulation failed: ${res.status}`);
  }
  const payload = await res.json();
  return normalizeRunSimulationResponse(payload);
}

function normalizeRunSimulationResponse(payload: unknown): RunSimulationResponse {
  const root = asRecord(payload) ?? {};
  const data = asRecord(root.data) ?? root;

  const durationSeconds = asNumber(data.duration_seconds) ?? 3600;
  const timelineRaw = Array.isArray(data.timeline) ? data.timeline : [];
  const timeline = timelineRaw.map((item, idx) =>
    normalizeTimelineFrame(item, idx),
  );
  const metricsRaw = asRecord(data.metrics) ?? {};
  const finalMetricsRaw = asRecord(data.final_metrics) ?? metricsRaw;

  return {
    success: Boolean(data.success ?? root.success ?? true),
    duration_seconds: durationSeconds,
    metrics: toMetrics(metricsRaw),
    final_metrics: toMetrics(finalMetricsRaw),
    events: Array.isArray(data.events) ? data.events : [],
    timeline,
    log_path: String(data.log_path ?? ""),
  };
}

function toMetrics(input: Record<string, unknown>) {
  const fullPalletPct = asNumber(input.full_pallet_pct);
  const fullPalletsOutOf8 = asNumber(input.full_pallets_out_of_8);
  const derivedFromPct =
    fullPalletPct === null
      ? 0
      : Math.max(0, Math.min(8, Math.round((fullPalletPct / 100) * 8)));

  return {
    full_pallets_out_of_8: fullPalletsOutOf8 ?? derivedFromPct,
    full_pallet_pct: fullPalletPct ?? undefined,
    pallets_completed: asNumber(input.pallets_completed) ?? 0,
    avg_time_per_pallet: asNumber(input.avg_time_per_pallet) ?? 0,
  };
}

function normalizeTimelineFrame(
  framePayload: unknown,
  idx: number,
): SimulationTimelineFrame {
  const frame = asRecord(framePayload) ?? {};
  const metricsRaw = asRecord(frame.metrics) ?? {};
  const finalMetricsRaw = asRecord(frame.final_metrics);
  return {
    t: asNumber(frame.t) ?? idx,
    metrics: toMetrics(metricsRaw),
    pallet_slots: Array.isArray(frame.pallet_slots) ? frame.pallet_slots : [],
    shuttles: Array.isArray(frame.shuttles) ? frame.shuttles : [],
    grid_changes: Array.isArray(frame.grid_changes) ? frame.grid_changes : [],
    action_message: String(frame.action_message ?? "Awaiting simulation start..."),
    event_count: asNumber(frame.event_count) ?? 0,
    final_metrics: finalMetricsRaw ? toMetrics(finalMetricsRaw) : undefined,
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) return false;
    const body = await res.json();
    return body.status === "ok";
  } catch {
    return false;
  }
}

async function tryFetchCsv(url: string): Promise<string | null> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) return null;
  const text = await res.text();
  // Vite's dev server returns index.html with 200 OK for unknown paths
  // (SPA fallback). Detect and treat as a miss so the mock fallback runs.
  if (text.trimStart().startsWith("<")) return null;
  return text;
}

export async function fetchSiloState(): Promise<SiloState> {
  // Try the live CSV (overwritten by server.py); fall back to the committed
  // mock so the frontend works standalone when the backend is offline.
  const cacheBuster = `t=${Date.now()}`;
  const live = await tryFetchCsv(`/data/silo_setup.csv?${cacheBuster}`);
  const text =
    live ?? (await tryFetchCsv(`/data/silo_setup_mock.csv?${cacheBuster}`));
  if (text === null) {
    throw new Error("fetchSiloState: no CSV available");
  }
  return parseSiloCsv(text);
}
