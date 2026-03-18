import type { SimulationResult, SimulationParams, ActorAttrition, EconomicImpact, EscalationNode, OilDataPoint } from './types';

// Deterministic-ish mock simulation — parameterized so sliders feel live
export function generateMockData(params?: Partial<SimulationParams>): SimulationResult {
  const t0 = performance.now();
  const intensity    = params?.strikeIntensity   ?? 7;
  const oilPct       = params?.oilDisruptionPct  ?? 45;
  const retaliProb   = params?.iranRetaliationProb ?? 0.90;
  const nuclear      = params?.nuclearDeterrence  ?? 0.75;
  const runs         = params?.simulationRuns     ?? 10000;

  // Scale outcome probabilities based on parameters
  const escalationFactor = (intensity / 10) * retaliProb * (1 - nuclear * 0.4);
  const deEscalFactor    = 1 - escalationFactor;

  const rawOutcomes = [
    { base: 0.185, scale: deEscalFactor  },  // 1 No escalation
    { base: 0.284, scale: 1.0            },  // 2 Limited exchange
    { base: 0.221, scale: escalationFactor * 0.8 }, // 3 Conv <30d
    { base: 0.135, scale: escalationFactor * 0.9 }, // 4 Conv >30d
    { base: 0.090, scale: escalationFactor       }, // 5 Proxy
    { base: 0.051, scale: escalationFactor * 1.1 }, // 6 Regional
    { base: 0.021, scale: escalationFactor * (1.3 - nuclear) }, // 7 Nuclear
    { base: 0.015, scale: 1 + oilPct / 200       }, // 8 Econ contagion
  ];

  const raw   = rawOutcomes.map(o => Math.max(0.001, o.base * o.scale));
  const total = raw.reduce((a, b) => a + b, 0);
  const probs = raw.map(v => v / total);

  const sampleStdDev = (p: number) => Math.sqrt(p * (1 - p) / runs);
  const z95 = 1.96;

  const NAMES = [
    ['No Escalation / De-escalation',    'No Escalation',     'safe'    ],
    ['Limited Strike Exchange',           'Limited Exchange',  'low'     ],
    ['Conventional War < 30 Days',        'Conv. War <30d',    'moderate'],
    ['Conventional War > 30 Days',        'Conv. War >30d',    'high'    ],
    ['Proxy Expansion (Lebanon/Yemen)',   'Proxy Expansion',   'high'    ],
    ['Regional War (Multi-state)',        'Regional War',      'critical'],
    ['Nuclear Signaling / Threshold',     'Nuclear Signaling', 'critical'],
    ['Global Economic Contagion',         'Econ. Contagion',   'high'    ],
  ] as const;

  const outcomes = probs.map((p, i) => {
    const sd = sampleStdDev(p);
    return {
      id:          i + 1,
      name:        NAMES[i][0],
      shortName:   NAMES[i][1],
      probability: p,
      ciLow:       Math.max(0, p - z95 * sd),
      ciHigh:      Math.min(1, p + z95 * sd),
      severity:    NAMES[i][2] as any,
    };
  });

  const nuclearRisk = outcomes[6].probability;

  return {
    outcomes,
    attrition:          buildAttrition(intensity, retaliProb),
    economic:           buildEconomic(oilPct),
    escalationNodes:    buildEscalationNodes(escalationFactor, nuclearRisk),
    nuclearRisk,
    oilPriceTrajectory: buildOilCurve(oilPct),
    casualtyEstimate: {
      israel:   Math.round(1800 + intensity * 350),
      iran:     Math.round(6000 + intensity * 800),
      civilian: Math.round(8000 + intensity * 1200),
    },
    timestamp:    new Date().toISOString(),
    runsCompleted: runs,
    durationMs:   Math.round(performance.now() - t0 + 200 + Math.random() * 800),
  };
}

function buildAttrition(intensity: number, retaliProb: number): ActorAttrition[] {
  const days = Array.from({ length: 91 }, (_, i) => i);
  const lerp  = (a: number, b: number, t: number) => a + (b - a) * t;

  const curves: [string, string, string, number[], number[]][] = [
    // [actor, key, color, [phase0Rate, phase1Rate, floor], [phase0Rate, phase1Rate, floor]]
    ['Israel (IDF)',   'israel',    '#ff8c00', [2.5, 0.7, 65], []],
    ['Iran (IRGC)',    'iran',      '#ff2020', [5.5 * (intensity/7), 1.4, 28], []],
    ['USA (CENTCOM)',  'usa',       '#00ccff', [0.25, 0.1, 95], []],
    ['Hezbollah',      'hezbollah', '#ff5500', [3.2 * retaliProb, 1.6, 22], []],
    ['Houthis (AAS)',  'houthis',   '#cc44ff', [1.2, 0.9, 38], []],
  ];

  const rates: [number, number, number][] = [
    [2.5 * (intensity / 7),  0.7 * (intensity / 7), 65],
    [5.8 * (intensity / 7),  1.5 * (intensity / 7), 28],
    [0.25,                   0.10,                  95],
    [3.2 * retaliProb,       1.6 * retaliProb,      22],
    [1.2,                    0.90,                  38],
  ];

  return curves.map(([actor, key, color], idx) => {
    const [r0, r1, floor] = rates[idx];
    const data = days.map(d => {
      let s = 100;
      if (d <= 7)       s = 100 - d * r0;
      else if (d <= 30) s = (100 - 7 * r0) - (d - 7) * r1;
      else              s = (100 - 7 * r0) - 23 * r1 - (d - 30) * r1 * 0.35;
      return { day: d, strength: Math.max(floor, Math.round(s * 10) / 10) };
    });
    return { actor, key: key as any, color, data };
  });
}

function buildEconomic(oilPct: number): EconomicImpact[] {
  const f = oilPct / 100;
  return [
    { country: 'USA',           flag: '🇺🇸', m6: -0.4*f,        m12: -0.9*f,        m24: -0.6*f,       m36: -0.2*f,       oilDependency: 15  },
    { country: 'European Union',flag: '🇪🇺', m6: -1.3*f,        m12: -2.3*f,        m24: -1.7*f,       m36: -0.9*f,       oilDependency: 45  },
    { country: 'China',         flag: '🇨🇳', m6: -1.9*f,        m12: -3.0*f,        m24: -2.1*f,       m36: -1.2*f,       oilDependency: 55  },
    { country: 'India',         flag: '🇮🇳', m6: -2.2*f,        m12: -3.4*f,        m24: -2.5*f,       m36: -1.4*f,       oilDependency: 65  },
    { country: 'Japan',         flag: '🇯🇵', m6: -2.5*f,        m12: -3.8*f,        m24: -2.8*f,       m36: -1.6*f,       oilDependency: 72  },
    { country: 'South Korea',   flag: '🇰🇷', m6: -2.3*f,        m12: -3.5*f,        m24: -2.6*f,       m36: -1.5*f,       oilDependency: 68  },
    { country: 'Saudi Arabia',  flag: '🇸🇦', m6:  2.5*f,        m12:  3.9*f,        m24:  2.1*f,       m36:  0.9*f,       oilDependency: -85 },
    { country: 'Israel',        flag: '🇮🇱', m6: -4.8*f - 1.5,  m12: -6.5*f - 2.0,  m24: -4.2*f - 1.0, m36: -2.6*f - 0.5, oilDependency: 30  },
    { country: 'Iran',          flag: '🇮🇷', m6: -8.8*f - 3.0,  m12: -12.5*f - 4.0, m24: -9.5*f - 2.5, m36: -6.5*f - 1.5, oilDependency: 80  },
    { country: 'Russia',        flag: '🇷🇺', m6:  1.2*f,        m12:  2.0*f,        m24:  1.2*f,       m36:  0.5*f,       oilDependency: -70 },
  ];
}

function buildEscalationNodes(ef: number, nucRisk: number): EscalationNode[] {
  return [
    { id: 1, name: 'INITIAL STRIKE',          desc: 'IAF + USAF strike on Iran nuclear sites',    probability: 0.96,         active: true,  color: '#ff8c00', layer: 0 },
    { id: 2, name: 'IRAN RETALIATION',         desc: 'Ballistic missiles, drones on Israel',        probability: 0.88 * ef,    active: true,  color: '#ff7000', layer: 1 },
    { id: 3, name: 'PROXY ACTIVATION',         desc: 'Hezbollah + Houthi + Iraqi militia surge',    probability: 0.76 * ef,    active: true,  color: '#ff5500', layer: 2 },
    { id: 4, name: 'ESCALATION DECISION',      desc: 'Iran chooses full conventional war',           probability: 0.52 * ef,    active: false, color: '#ff3300', layer: 3 },
    { id: 5, name: 'DE-ESCALATION WINDOW',     desc: 'Back-channel diplomacy, ceasefire signal',     probability: 0.48 * (1-ef*0.3), active: false, color: '#00cc66', layer: 3 },
    { id: 6, name: 'CEASEFIRE / CONTAINMENT', desc: 'US-mediated halt, UN resolution',              probability: 0.36 * (1-ef*0.2), active: false, color: '#00aa44', layer: 4 },
    { id: 7, name: 'NUCLEAR SIGNALING',        desc: 'Iran redlines breached, warhead assembly',     probability: nucRisk,      active: false, color: '#ff0033', layer: 5 },
    { id: 8, name: 'THRESHOLD BREACH',         desc: 'First nuclear detonation — regime survival',  probability: nucRisk * 0.2, active: false, color: '#cc0022', layer: 6 },
  ];
}

function buildOilCurve(oilPct: number): OilDataPoint[] {
  const months = Array.from({ length: 37 }, (_, i) => i);
  const base   = 85;
  const spike  = oilPct * 1.2;
  return months.map(m => {
    let p: number, lo: number, hi: number;
    if (m === 0)       { p = base; lo = base - 3; hi = base + 3; }
    else if (m <= 2)   { p = base + spike * (m / 2); lo = p - 10; hi = p + 20; }
    else if (m <= 8)   { p = base + spike - (m - 2) * (spike * 0.12); lo = p - 12; hi = p + 15; }
    else if (m <= 20)  { p = base + spike * 0.28 - (m - 8) * 0.8; lo = p - 8; hi = p + 8; }
    else               { p = base + 5 + Math.sin(m * 0.4) * 3; lo = p - 5; hi = p + 5; }
    return { month: m, price: +p.toFixed(2), pessimistic: +hi.toFixed(2), optimistic: +lo.toFixed(2) };
  });
}
