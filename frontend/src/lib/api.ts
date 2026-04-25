import { parseSiloCsv } from "./parsing";
import type { RandomizeResponse, SiloState } from "./types";

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
  const live = await tryFetchCsv("/data/silo_setup.csv");
  const text = live ?? (await tryFetchCsv("/data/silo_setup_mock.csv"));
  if (text === null) {
    throw new Error("fetchSiloState: no CSV available");
  }
  return parseSiloCsv(text);
}
