# ⬡ ARES — Adaptive Risk & Escalation Simulator

> **[MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]**
> A research-grade geopolitical conflict simulation engine with a real-time 3D intelligence dashboard.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-r183-green.svg)](https://threejs.org/)

---

```
╔═══════════════════════════════════════════════════════════════╗
║  ARES v1.0  ·  SCENARIO: USA + ISRAEL vs IRAN                 ║
║  ENGINE: MONTE CARLO N=10,000  ·  95% CI  ·  LANCHESTER MODEL ║
╚═══════════════════════════════════════════════════════════════╝
```

## What is ARES?

ARES is a **mathematical modeling platform** for geopolitical conflict analysis, built for researchers, educators, and policy analysts. It combines:

- **Lanchester combat equations** (Square Law + Linear Law) for force attrition modeling
- **Monte Carlo simulation** (N=10,000 runs) over a probabilistic escalation decision tree
- **Leontief input-output economics** for oil shock and GDP contagion propagation
- **Game-theoretic deterrence model** with Nash equilibrium nuclear threshold logic
- **Real-time 3D Earth visualization** with animated conflict arcs, radar rings, and country highlights

All outputs are clearly labeled as model outputs — **not predictive intelligence**.

---

## Dashboard Preview

```
┌─ HEADER: ARES · THREAT LEVEL · UTC CLOCK ─────────────────────────────────┐
│                                                                             │
│  ┌─ PARAMS ─┐  ┌─────────── 3D GLOBE ────────────┐  ┌─ OUTCOMES ────────┐ │
│  │ Sliders  │  │  🌍 Night Earth + Missile Arcs  │  │ 8-state MC bars  │ │
│  │ Scenario │  │  ● Conflict Markers              │  │ 95% CI shown     │ │
│  │ US Level │  │  ◈ Radar Rings                  │  ├─ ESCALATION ─────┤ │
│  │ [RUN ▶]  │  │  Nuclear Risk Meter             │  │ SVG flow graph   │ │
│  └──────────┘  │  Casualty Estimates             │  ├─ ATTRITION ──────┤ │
│                └─────────────────────────────────┘  │ Lanchester curves│ │
│                                                      ├─ OIL CURVE ──────┤ │
│                                                      │ Brent projection │ │
│                                                      ├─ ECONOMIC ───────┤ │
│                                                      │ GDP heatmap      │ │
│                                                      └──────────────────┘ │
│                                                                             │
└─ STATUS BAR: MOST PROBABLE OUTCOME · NUCLEAR RISK % · ENGINE STATUS ───────┘
```

---

## Quick Start

### 1 — Clone

```bash
git clone https://github.com/Lameda12/GeoPrediction.git
cd GeoPrediction
```

### 2 — Launch (Windows)

Double-click **`start_ares.bat`** — it starts both servers and opens the browser.

Or manually in PowerShell (use `;` not `&&`):

```powershell
# Terminal 1 — Python simulation API (optional)
cd ares
py -3 server.py

# Terminal 2 — Next.js UI
cd ares-ui
npm install
npm run dev
```

Open → [http://localhost:3000](http://localhost:3000)

### 3 — Python CLI (original engine)

```powershell
cd ares
pip install -r requirements.txt
py -3 main.py --scenario usa_israel_iran --runs 10000 --export-csv
```

---

## Architecture

```
GeoPrediction/
├── start_ares.bat              ← One-click launcher (Windows)
│
├── ares/                       ← Python simulation engine
│   ├── main.py                 ← CLI entrypoint
│   ├── server.py               ← FastAPI bridge → Next.js UI (port 8000)
│   ├── engine/
│   │   ├── lanchester.py       ← Square Law + Linear Law combat equations
│   │   ├── montecarlo.py       ← Probabilistic escalation tree (N=10,000)
│   │   ├── escalation.py       ← Nash equilibrium deterrence model
│   │   ├── economic.py         ← Leontief I-O shock propagation
│   │   └── actors.py           ← Actor capability data classes (9 actors)
│   ├── data/
│   │   ├── military.json       ← IISS Military Balance 2024 baselines
│   │   ├── economic.json       ← World Bank GDP / trade data
│   │   └── nuclear.json        ← NTI deterrence parameters
│   └── scenarios/
│       ├── usa_israel_iran.py  ← Primary scenario (D1–D365)
│       └── global_spillover.py ← Second-order contagion model
│
└── ares-ui/                    ← Next.js 14 interactive dashboard
    ├── app/
    │   ├── page.tsx            ← Main dashboard layout & state
    │   └── api/simulate/       ← Proxy route → Python API
    ├── components/
    │   ├── Globe3D.tsx         ← react-globe.gl: 3D Earth, arcs, rings
    │   ├── panels/
    │   │   ├── OutcomeBars.tsx     ← Animated MC probability bars
    │   │   ├── EscalationGraph.tsx ← SVG node graph with flow animation
    │   │   ├── AttritionChart.tsx  ← Recharts Lanchester curves
    │   │   └── EconomicHeatmap.tsx ← GDP impact color grid
    │   └── ui/
    │       ├── Header.tsx          ← Threat level · clock · engine status
    │       ├── ControlPanel.tsx    ← Live parameter sliders
    │       └── StatusBar.tsx       ← Bottom status strip
    └── lib/
        ├── types.ts            ← Shared TypeScript interfaces
        ├── geodata.ts          ← Conflict locations & missile arc coordinates
        ├── mockData.ts         ← Parameterized JS simulation (offline mode)
        └── simulation.ts       ← API client with Python → JS fallback
```

---

## Mathematical Models

### Lanchester Combat Equations
Both laws are implemented and selectable per scenario phase:

| Law | Formula | Use Case |
|-----|---------|----------|
| **Square Law** | `dA/dt = −β·B` | Conventional warfare, modern air power |
| **Linear Law** | `dA/dt = −β·(B/B₀)·A` | Guerrilla / attrition warfare |

Parameters per actor: `force_size`, `attrition_rate`, `reinforcement_rate`, `air_superiority_coefficient`

### Monte Carlo Escalation Tree
8 outcome states, 10,000 simulations, Bayesian priors from Correlates of War dataset:

```
1. No Escalation / De-escalation
2. Limited Strike Exchange
3. Conventional War < 30 Days
4. Conventional War > 30 Days
5. Proxy Expansion (Lebanon / Hezbollah / Yemen)
6. Regional War (Multi-state)
7. Nuclear Signaling / Threshold   ← RED FLAG if > 15%
8. Global Economic Contagion
```

All outputs include **95% confidence intervals** computed from binomial variance.

### Economic Shock Propagation (Leontief I-O)
Oil price elasticity → sector cascade: `energy → manufacturing → finance → GDP`

Tracks: USA · EU · China · India · Japan · South Korea · Saudi Arabia · Israel · Iran · Russia
Windows: 6-month · 12-month · 24-month · 36-month

### Deterrence & Nuclear Threshold
Nash equilibrium logic: escalation preferred when expected payoff of escalation > de-escalation.
Nuclear threshold modeled as function of: `existential_threat_perception × leadership_rationality × US_extended_deterrence_credibility`

---

## Scenario: USA + Israel vs Iran

**Initial conditions** (IISS 2024 / SIPRI public data baseline):

| Phase | Days | Events |
|-------|------|--------|
| Initial Exchange | D1–7 | IAF strikes Natanz, Fordow, Isfahan; Iran ballistic response |
| Escalation Window | D7–30 | Hezbollah barrage, Houthi Red Sea ops, Iraqi militia strikes |
| Economic Contagion | D30–90 | Hormuz disruption, oil spike, sanctions escalation |
| Strategic Outcome | D90–365 | Stabilization or regional war |

**Strait of Hormuz mining probability:** 40–60% (slider-adjustable)

---

## Dashboard Controls

| Slider | Range | Effect |
|--------|-------|--------|
| Strike Intensity | 1–10 | Scales initial force attrition rates |
| Alliance Reliability | 0–100% | US commitment probability |
| Hormuz Disruption | 0–100% | Oil price spike + GDP cascade |
| Iran Retaliation Prob | 0–100% | Escalation tree branch weights |
| Nuclear Deterrence | 0–100% | Threshold suppression factor |
| Monte Carlo Runs | 1K–50K | Statistical precision |

All sliders **live-update** the simulation within 250ms via debounced client-side engine.

---

## Data Sources (Public Baseline Values)

| Source | Used For |
|--------|----------|
| [IISS Military Balance 2024](https://www.iiss.org/publications/the-military-balance/) | Force sizes, air assets, missile inventories |
| [SIPRI Arms Transfers](https://www.sipri.org/databases/armstransfers) | Weapons flows, capability indices |
| [World Bank Open Data](https://data.worldbank.org/) | GDP, trade volumes, forex reserves |
| [US EIA](https://www.eia.gov/) | Energy dependency, Hormuz flow statistics |
| [Correlates of War Project](https://correlatesofwar.org/) | Historical conflict base rates for Bayesian priors |
| [Nuclear Threat Initiative (NTI)](https://www.nti.org/) | Nuclear deterrence parameters |
| [RAND Corporation](https://www.rand.org/) | Conflict probability calibration studies |

---

## Tech Stack

### Python Engine
| Package | Purpose |
|---------|---------|
| `numpy`, `scipy` | Mathematical modeling, statistics |
| `pandas` | Data manipulation |
| `matplotlib`, `plotly` | Chart generation |
| `streamlit` | Original Python dashboard |
| `fastapi`, `uvicorn` | REST API server |
| `reportlab` | PDF report export |
| `rich` | Terminal output formatting |

### Next.js UI
| Package | Purpose |
|---------|---------|
| `next` 14 | React framework, App Router |
| `react-globe.gl` | WebGL 3D Earth visualization |
| `three.js` r183 | 3D rendering engine |
| `framer-motion` | Panel animations, transitions |
| `recharts` | Lanchester & oil price charts |
| `tailwindcss` | Utility-first styling |

---

## Lessons Learned & Technical Notes

### 1. Next.js Hydration with Dynamic Data
**Problem:** `useState(() => generateMockData())` runs on the server during SSR, producing a different result than the client (different `Date.now()`, `performance.now()`). This causes React's hydration mismatch error.

**Fix:** Initialize state to `null`, generate data inside `useEffect` (client-only). Show a deterministic boot screen during SSR:

```tsx
// ❌ Causes hydration error — runs on server AND client with different values
const [result, setResult] = useState(() => generateMockData());

// ✅ Correct — only runs client-side, server always renders null → boot screen
const [result, setResult] = useState<SimulationResult | null>(null);
useEffect(() => { setResult(generateMockData()); }, []);
```

### 2. Three.js / react-globe.gl Version Pinning
**Problem:** `three-globe` uses the `./tsl` (Three.js Shading Language) subpath export, which was only added in Three.js **r168+**. Pinning `three@^0.163.0` causes a webpack build error.

**Fix:** Always install `three@latest` alongside `react-globe.gl`:

```bash
npm install three@latest react-globe.gl
```

### 3. PowerShell vs Bash Syntax
**Problem:** `&&` is not a valid statement separator in Windows PowerShell (it is in bash/zsh and Command Prompt).

**Fix:** Use `;` in PowerShell, or run commands on separate lines:

```powershell
# ❌ PowerShell error
cd ares-ui && npm run dev

# ✅ PowerShell correct
cd ares-ui; npm run dev
```

### 4. Globe SSR with react-globe.gl
`react-globe.gl` uses `window` and WebGL APIs unavailable during server-side rendering. Always wrap with Next.js dynamic import:

```tsx
const Globe3D = dynamic(() => import('@/components/Globe3D'), { ssr: false });
```

### 5. `as const` Narrows Types Too Aggressively
**Problem:** Using `as const` on an array of objects with union-type string values causes TypeScript to narrow each element's type to its literal, making `let level = ARRAY[0]` unable to be reassigned to other elements.

**Fix:** Remove `as const` when the array items will be used as mutable variables, or explicitly type the variable:

```typescript
// ❌ TypeScript error — type of level[0] is too narrow
const LEVELS = [{ label: 'LOW' }, { label: 'HIGH' }] as const;
let level = LEVELS[0]; // Type: { label: 'LOW' } — can't assign LEVELS[1]

// ✅ Correct
const LEVELS = [{ label: 'LOW' }, { label: 'HIGH' }];
```

---

## Disclaimer

This tool is built for **academic research, education, and policy analysis**. All probability outputs are mathematical model results based on publicly available data.

> **This is NOT a prediction system. This is NOT intelligence analysis. Outputs do NOT represent any government, military, or intelligence assessment.**

All scenario parameters are derived from open-source public data (IISS, SIPRI, World Bank, US EIA). No classified or restricted information is used.

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built with Claude Code · Research tool for conflict modeling education*
