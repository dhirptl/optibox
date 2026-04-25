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

export async function fetchSiloState(): Promise<SiloState> {
  const res = await fetch("/data/silo_setup.csv", { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`fetchSiloState failed: ${res.status}`);
  }
  const text = await res.text();
  return parseSiloCsv(text);
}
