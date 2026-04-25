import { parseSiloCsv } from './parsing'
import type { SiloState } from './types'

const API_BASE = 'http://localhost:8000'

export interface RandomizeResponse {
  success: boolean
  num_boxes: number
  csv_path: string
  fill_pct: number
}

export async function randomizeSilo(
  numBoxes: number,
): Promise<RandomizeResponse> {
  const res = await fetch(`${API_BASE}/api/randomize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ num_boxes: numBoxes }),
  })
  const payload = await res.json()
  if (!res.ok) throw new Error(payload.error ?? 'Request failed')
  return payload
}

export async function resetSilo(): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/reset`, { method: 'POST' })
  const payload = await res.json()
  if (!res.ok) throw new Error(payload.error ?? 'Request failed')
  return payload
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    return res.ok
  } catch {
    return false
  }
}

export async function fetchSiloState(csvPath = '/data/silo_setup.csv'): Promise<SiloState> {
  const res = await fetch(`${csvPath}?t=${Date.now()}`)
  if (!res.ok) throw new Error('Failed to fetch silo CSV')
  const text = await res.text()
  return parseSiloCsv(text)
}
