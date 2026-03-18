"""
ARES FastAPI Server — bridges Python simulation engine to Next.js UI
[MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]

Usage:
    pip install fastapi uvicorn
    cd ares && python server.py
"""

import sys
import os
import time
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add ares/ to path so we can import engine modules
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ARES] %(message)s")
log = logging.getLogger("ares.server")

# ── Lazy-import engine (handles missing deps gracefully) ──────────────────────
try:
    from engine.montecarlo import MonteCarloSimulation
    from engine.lanchester import LanchesterModel
    from engine.economic   import EconomicModel
    from engine.escalation import EscalationModel
    from engine.actors     import build_actors
    ENGINE_AVAILABLE = True
    log.info("Python simulation engine loaded OK")
except ImportError as e:
    ENGINE_AVAILABLE = False
    log.warning(f"Engine import failed ({e}) — using fallback simulation")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ARES — Adaptive Risk & Escalation Simulator",
    version="1.0.0",
    description="[MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response schemas ────────────────────────────────────────────────
class SimParams(BaseModel):
    strikeIntensity:     float = Field(7.0,   ge=1,   le=10)
    allianceReliability: float = Field(0.85,  ge=0,   le=1)
    oilDisruptionPct:    float = Field(45.0,  ge=0,   le=100)
    iranRetaliationProb: float = Field(0.90,  ge=0,   le=1)
    usInvolvement:       str   = Field("isr_support")
    nuclearDeterrence:   float = Field(0.75,  ge=0,   le=1)
    simulationRuns:      int   = Field(10000, ge=100, le=100000)


# ── Fallback pure-Python simulation (no numpy required) ───────────────────────
def _fallback_simulate(p: SimParams) -> dict:
    """Lightweight Monte Carlo implemented in pure Python for fallback."""
    import random, math
    t0 = time.perf_counter()
    rng = random.Random(42)

    ef  = (p.strikeIntensity / 10) * p.iranRetaliationProb * (1 - p.nuclearDeterrence * 0.4)
    oilF = p.oilDisruptionPct / 100

    # Base probabilities (8 outcomes)
    bases = [
        0.185 * (1 - ef),          # 1 No escalation
        0.284,                      # 2 Limited exchange
        0.221 * ef * 0.8,          # 3 Conv <30d
        0.135 * ef * 0.9,          # 4 Conv >30d
        0.090 * ef,                 # 5 Proxy
        0.051 * ef * 1.1,          # 6 Regional
        0.021 * ef * (1.3 - p.nuclearDeterrence), # 7 Nuclear
        0.015 * (1 + oilF),        # 8 Econ contagion
    ]
    bases = [max(0.001, b) for b in bases]
    total = sum(bases)
    probs = [b / total for b in bases]

    # Simulate runs via multinomial sampling
    counts = [0] * 8
    N = p.simulationRuns
    for _ in range(N):
        r = rng.random()
        cum = 0.0
        for i, pr in enumerate(probs):
            cum += pr
            if r <= cum:
                counts[i] += 1
                break

    z95 = 1.96
    NAMES = [
        ("No Escalation / De-escalation",    "No Escalation",     "safe"),
        ("Limited Strike Exchange",           "Limited Exchange",  "low"),
        ("Conventional War < 30 Days",        "Conv. War <30d",    "moderate"),
        ("Conventional War > 30 Days",        "Conv. War >30d",    "high"),
        ("Proxy Expansion (Lebanon/Yemen)",   "Proxy Expansion",   "high"),
        ("Regional War (Multi-state)",        "Regional War",      "critical"),
        ("Nuclear Signaling / Threshold",     "Nuclear Signaling", "critical"),
        ("Global Economic Contagion",         "Econ. Contagion",   "high"),
    ]

    outcomes = []
    for i, (name, short, sev) in enumerate(NAMES):
        prob = counts[i] / N
        sd   = math.sqrt(prob * (1 - prob) / N) if prob > 0 else 0
        outcomes.append({
            "id": i + 1, "name": name, "shortName": short,
            "probability": round(prob, 6),
            "ciLow":  round(max(0, prob - z95 * sd), 6),
            "ciHigh": round(min(1, prob + z95 * sd), 6),
            "severity": sev,
        })

    nuke_risk = outcomes[6]["probability"]

    # Attrition (Lanchester-style simplified)
    r0_table = [
        ("Israel (IDF)",   "israel",    "#ff8c00", 2.5 * p.strikeIntensity / 7,  0.7, 65),
        ("Iran (IRGC)",    "iran",      "#ff2020", 5.8 * p.strikeIntensity / 7,  1.5, 28),
        ("USA (CENTCOM)",  "usa",       "#00ccff", 0.25,                          0.1, 95),
        ("Hezbollah",      "hezbollah", "#ff5500", 3.2 * p.iranRetaliationProb,   1.6, 22),
        ("Houthis (AAS)",  "houthis",   "#cc44ff", 1.2,                           0.9, 38),
    ]
    attrition = []
    for actor, key, color, r0, r1, floor in r0_table:
        data = []
        for d in range(91):
            if d <= 7:
                s = 100 - d * r0
            elif d <= 30:
                s = (100 - 7 * r0) - (d - 7) * r1
            else:
                s = (100 - 7 * r0) - 23 * r1 - (d - 30) * r1 * 0.35
            data.append({"day": d, "strength": round(max(floor, s), 1)})
        attrition.append({"actor": actor, "key": key, "color": color, "data": data})

    # Economic
    economic = [
        {"country": "USA",            "flag": "🇺🇸", "m6": -0.4*oilF,       "m12": -0.9*oilF,       "m24": -0.6*oilF,      "m36": -0.2*oilF,      "oilDependency": 15},
        {"country": "European Union", "flag": "🇪🇺", "m6": -1.3*oilF,       "m12": -2.3*oilF,       "m24": -1.7*oilF,      "m36": -0.9*oilF,      "oilDependency": 45},
        {"country": "China",          "flag": "🇨🇳", "m6": -1.9*oilF,       "m12": -3.0*oilF,       "m24": -2.1*oilF,      "m36": -1.2*oilF,      "oilDependency": 55},
        {"country": "India",          "flag": "🇮🇳", "m6": -2.2*oilF,       "m12": -3.4*oilF,       "m24": -2.5*oilF,      "m36": -1.4*oilF,      "oilDependency": 65},
        {"country": "Japan",          "flag": "🇯🇵", "m6": -2.5*oilF,       "m12": -3.8*oilF,       "m24": -2.8*oilF,      "m36": -1.6*oilF,      "oilDependency": 72},
        {"country": "South Korea",    "flag": "🇰🇷", "m6": -2.3*oilF,       "m12": -3.5*oilF,       "m24": -2.6*oilF,      "m36": -1.5*oilF,      "oilDependency": 68},
        {"country": "Saudi Arabia",   "flag": "🇸🇦", "m6":  2.5*oilF,       "m12":  3.9*oilF,       "m24":  2.1*oilF,      "m36":  0.9*oilF,      "oilDependency": -85},
        {"country": "Israel",         "flag": "🇮🇱", "m6": -4.8*oilF - 1.5, "m12": -6.5*oilF - 2.0, "m24": -4.2*oilF - 1.0,"m36": -2.6*oilF - 0.5,"oilDependency": 30},
        {"country": "Iran",           "flag": "🇮🇷", "m6": -8.8*oilF - 3.0, "m12": -12.5*oilF - 4.0,"m24": -9.5*oilF - 2.5,"m36": -6.5*oilF - 1.5,"oilDependency": 80},
        {"country": "Russia",         "flag": "🇷🇺", "m6":  1.2*oilF,       "m12":  2.0*oilF,       "m24":  1.2*oilF,      "m36":  0.5*oilF,      "oilDependency": -70},
    ]

    # Escalation nodes
    escalation_nodes = [
        {"id": 1, "name": "INITIAL STRIKE",       "desc": "IAF + USAF strike nuclear sites",     "probability": 0.96,          "active": True,  "color": "#ff8c00", "layer": 0},
        {"id": 2, "name": "IRAN RETALIATION",      "desc": "Ballistic + drone salvo on Israel",   "probability": round(0.88*ef,4),"active": True, "color": "#ff7000", "layer": 1},
        {"id": 3, "name": "PROXY ACTIVATION",      "desc": "Hezbollah + Houthi surge",            "probability": round(0.76*ef,4),"active": True, "color": "#ff5500", "layer": 2},
        {"id": 4, "name": "ESCALATION DECISION",   "desc": "Iran elects full conventional war",   "probability": round(0.52*ef,4),"active": False,"color": "#ff3300", "layer": 3},
        {"id": 5, "name": "DE-ESCALATION WINDOW",  "desc": "Back-channel signal, UN mediation",   "probability": round(0.48*(1-ef*0.3),4),"active": False,"color": "#00cc66","layer": 3},
        {"id": 6, "name": "CEASEFIRE/CONTAINMENT", "desc": "US-brokered halt, resolution 2x34",   "probability": round(0.36*(1-ef*0.2),4),"active": False,"color": "#00aa44","layer": 4},
        {"id": 7, "name": "NUCLEAR SIGNALING",     "desc": "IRGC redlines, warhead assembly",     "probability": round(nuke_risk,6),   "active": False,"color": "#ff0033", "layer": 5},
        {"id": 8, "name": "THRESHOLD BREACH",      "desc": "First detonation — regime survival",  "probability": round(nuke_risk*0.2,6),"active": False,"color": "#cc0022", "layer": 6},
    ]

    # Oil price curve
    base = 85.0
    spike = p.oilDisruptionPct * 1.2
    oil_curve = []
    for m in range(37):
        if m == 0:
            price, lo, hi = base, base - 3, base + 3
        elif m <= 2:
            price = base + spike * (m / 2); lo = price - 10; hi = price + 20
        elif m <= 8:
            price = base + spike - (m - 2) * (spike * 0.12); lo = price - 12; hi = price + 15
        elif m <= 20:
            price = base + spike * 0.28 - (m - 8) * 0.8; lo = price - 8; hi = price + 8
        else:
            price = base + 5 + math.sin(m * 0.4) * 3; lo = price - 5; hi = price + 5
        oil_curve.append({"month": m, "price": round(price, 2), "pessimistic": round(hi, 2), "optimistic": round(lo, 2)})

    duration_ms = int((time.perf_counter() - t0) * 1000)

    return {
        "outcomes":           outcomes,
        "attrition":          attrition,
        "economic":           economic,
        "escalationNodes":    escalation_nodes,
        "nuclearRisk":        nuke_risk,
        "oilPriceTrajectory": oil_curve,
        "casualtyEstimate": {
            "israel":   int(1800 + p.strikeIntensity * 350),
            "iran":     int(6000 + p.strikeIntensity * 800),
            "civilian": int(8000 + p.strikeIntensity * 1200),
        },
        "timestamp":    __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "runsCompleted": N,
        "durationMs":   duration_ms,
    }


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status":         "operational",
        "engine":         "python" if ENGINE_AVAILABLE else "fallback",
        "model":          "ARES v1.0",
        "disclaimer":     "MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE",
    }


@app.post("/api/simulate")
async def simulate(params: SimParams):
    log.info(
        f"Simulation request | runs={params.simulationRuns} "
        f"intensity={params.strikeIntensity} oil={params.oilDisruptionPct}%"
    )
    try:
        if ENGINE_AVAILABLE:
            # Use the full Python engine
            mc     = MonteCarloSimulation(params.dict())
            result = mc.run()
        else:
            result = _fallback_simulate(params)

        log.info(f"Simulation complete in {result.get('durationMs', '?')}ms")
        return result

    except Exception as exc:
        log.error(f"Simulation error: {exc}", exc_info=True)
        # Always return something useful
        return _fallback_simulate(params)


if __name__ == "__main__":
    print("=" * 60)
    print("  ARES — Adaptive Risk & Escalation Simulator")
    print("  [MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]")
    print("=" * 60)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
