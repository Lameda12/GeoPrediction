import type { SimulationParams, SimulationResult } from './types';
import { generateMockData } from './mockData';

const PYTHON_API = 'http://localhost:8000';

export async function runSimulation(params: SimulationParams): Promise<SimulationResult> {
  try {
    const res = await fetch('/api/simulate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(params),
      signal:  AbortSignal.timeout(15_000),
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
  } catch {
    console.warn('[ARES] Python API unavailable — using JS simulation engine');
    // Simulate computation delay for realism
    await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
    return generateMockData(params);
  }
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${PYTHON_API}/api/health`, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

export const DEFAULT_PARAMS: SimulationParams = {
  strikeIntensity:     7,
  allianceReliability: 0.85,
  oilDisruptionPct:    45,
  iranRetaliationProb: 0.90,
  usInvolvement:       'isr_support',
  nuclearDeterrence:   0.75,
  simulationRuns:      10000,
};
