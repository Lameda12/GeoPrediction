// ─── ARES UI — Type Definitions ───────────────────────────────────────────────
// [MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

export type UsInvolvement = 'isr_support' | 'direct_strike' | 'full_war';
export type Severity      = 'safe' | 'low' | 'moderate' | 'high' | 'critical';
export type LocationType  = 'nuclear_target' | 'military' | 'naval' | 'proxy' | 'command';
export type ActorKey      = 'israel' | 'iran' | 'usa' | 'hezbollah' | 'houthis' | 'saudi' | 'russia' | 'china';

export interface SimulationParams {
  strikeIntensity:      number;   // 1–10
  allianceReliability:  number;   // 0–1
  oilDisruptionPct:     number;   // 0–100
  iranRetaliationProb:  number;   // 0–1
  usInvolvement:        UsInvolvement;
  nuclearDeterrence:    number;   // 0–1
  simulationRuns:       number;
}

export interface OutcomeState {
  id:          number;
  name:        string;
  shortName:   string;
  probability: number;
  ciLow:       number;
  ciHigh:      number;
  severity:    Severity;
}

export interface ActorAttrition {
  actor: string;
  key:   ActorKey;
  color: string;
  data:  Array<{ day: number; strength: number }>;
}

export interface EconomicImpact {
  country:       string;
  flag:          string;
  m6:            number;  // % GDP impact at 6 months
  m12:           number;
  m24:           number;
  m36:           number;
  oilDependency: number;  // % of energy from Gulf oil
}

export interface EscalationNode {
  id:          number;
  name:        string;
  desc:        string;
  probability: number;
  active:      boolean;
  color:       string;
  layer:       number;   // 0 = trigger, higher = more escalated
}

export interface OilDataPoint {
  month:       number;
  price:       number;
  pessimistic: number;
  optimistic:  number;
}

export interface SimulationResult {
  outcomes:            OutcomeState[];
  attrition:           ActorAttrition[];
  economic:            EconomicImpact[];
  escalationNodes:     EscalationNode[];
  nuclearRisk:         number;
  oilPriceTrajectory:  OilDataPoint[];
  casualtyEstimate:    { israel: number; iran: number; civilian: number };
  timestamp:           string;
  runsCompleted:       number;
  durationMs:          number;
}

export interface ConflictLocation {
  lat:      number;
  lng:      number;
  name:     string;
  type:     LocationType;
  active:   boolean;
  severity: Severity;
}

export interface MissileArc {
  startLat: number;
  startLng: number;
  endLat:   number;
  endLng:   number;
  label:    string;
  color:    string;
  actor:    ActorKey;
  active:   boolean;
}
