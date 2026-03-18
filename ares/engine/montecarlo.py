"""
ARES Monte Carlo Escalation Tree
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Implements a probabilistic decision tree with N=10,000 simulations.
Branch probabilities calibrated from:
  - Correlates of War Project (COW) historical base rates
  - RAND conflict termination studies
  - SIPRI armed conflict data
  - Crisis escalation literature (Fearon 1995, Powell 1999)

Outcome States:
  1. No escalation
  2. Limited strike exchange
  3. Conventional war < 30 days
  4. Conventional war > 30 days
  5. Proxy expansion (Lebanon/Hezbollah/Yemen)
  6. Regional war
  7. Nuclear signaling / threshold crossing
  8. Global economic contagion without direct war
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Callable
from collections import Counter


OUTCOME_LABELS = {
    1: "No Escalation / Ceasefire",
    2: "Limited Strike Exchange",
    3: "Conventional War <30 Days",
    4: "Conventional War >30 Days",
    5: "Proxy Expansion (Lebanon/Yemen/Iraq)",
    6: "Regional War",
    7: "Nuclear Signaling / Threshold",
    8: "Global Economic Contagion (No Direct War)",
}

OUTCOME_COLORS = {
    1: "#2ecc71",
    2: "#f39c12",
    3: "#e67e22",
    4: "#e74c3c",
    5: "#9b59b6",
    6: "#c0392b",
    7: "#922b21",
    8: "#1a5276",
}


@dataclass
class ScenarioParameters:
    """
    Bayesian prior parameters for the USA+Israel vs Iran scenario.
    Calibrated from COW, RAND, and historical Middle East conflict data.
    Adjust via dashboard sliders.
    """
    # Initial strike parameters
    strike_intensity: float = 0.75          # 0-1: scale of initial strike (0=limited, 1=full)
    strike_success_prob: float = 0.72       # P(strikes achieve military objectives)
    iran_retaliation_prob: float = 0.92     # P(Iran retaliates if struck)

    # Alliance & proxy parameters
    hezbollah_activation_prob: float = 0.85
    houthi_escalation_prob: float = 0.78
    iran_militia_iraq_prob: float = 0.88
    us_direct_entry_prob: float = 0.60      # P(US from ISR/support -> direct strikes)

    # Escalation control parameters
    iran_hormuz_blockade_prob: float = 0.45
    ceasefire_negotiation_prob: float = 0.35
    us_deterrence_credibility: float = 0.78
    israel_existential_threshold: float = 0.25  # P(Israel perceives existential threat)

    # Nuclear parameters
    iran_nuclear_signaling_threshold: float = 0.15  # RED flag threshold
    israel_samson_option_threshold: float = 0.08
    us_extended_deterrence_weight: float = 0.85

    # Economic contagion
    oil_disruption_pct: float = 0.45       # Fraction of Hormuz flow disrupted
    global_recession_trigger_prob: float = 0.40

    # Simulation control
    n_simulations: int = 10_000
    random_seed: int | None = None


@dataclass
class SimulationRun:
    """Single Monte Carlo run traversal through the decision tree."""
    outcome: int
    escalation_path: list[str] = field(default_factory=list)
    nuclear_flag: bool = False
    day_of_outcome: float = 0.0
    oil_disruption_triggered: bool = False
    hezbollah_activated: bool = False
    houthi_activated: bool = False


@dataclass
class MonteCarloResults:
    outcome_counts: Counter
    outcome_probabilities: dict[int, float]
    confidence_intervals: dict[int, tuple[float, float]]
    nuclear_probability: float
    nuclear_ci: tuple[float, float]
    mean_outcome_day: dict[int, float]
    n_simulations: int
    runs: list[SimulationRun] = field(default_factory=list)

    def print_summary(self) -> None:
        print("\n[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]")
        print("=" * 65)
        print(f"MONTE CARLO RESULTS  |  N={self.n_simulations:,} simulations")
        print("=" * 65)
        for state, label in OUTCOME_LABELS.items():
            p = self.outcome_probabilities.get(state, 0.0)
            lo, hi = self.confidence_intervals.get(state, (0.0, 0.0))
            bar_len = int(p * 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            print(f"  [{state}] {label:<42} {p*100:5.1f}%  [{lo*100:.1f}-{hi*100:.1f}%]")
            print(f"      {bar}")
        print("-" * 65)
        p_nuc = self.nuclear_probability
        lo_n, hi_n = self.nuclear_ci
        flag = " *** RED FLAG ***" if p_nuc > 0.15 else ""
        print(f"  [!] Nuclear Threshold Crossing:  {p_nuc*100:5.1f}%  [{lo_n*100:.1f}-{hi_n*100:.1f}%]{flag}")
        print("=" * 65)


def _wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for proportions."""
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def _simulate_single_run(
    params: ScenarioParameters,
    rng: np.random.Generator,
) -> SimulationRun:
    """
    Traverse the escalation decision tree for a single Monte Carlo run.

    Tree structure:
    STRIKE -> IRAN_RETALIATE -> PROXY_ACTIVATE -> HORMUZ ->
    US_DIRECT_ENTRY -> ESCALATION_CONTROL -> NUCLEAR_THRESHOLD -> OUTCOME
    """
    path: list[str] = []
    nuclear_flag = False
    oil_triggered = False
    hezbollah_on = False
    houthi_on = False

    # ── Node 0: Strike intensity modifies base probs ──────────────────────
    intensity = params.strike_intensity
    base_retaliation = params.iran_retaliation_prob * (0.5 + intensity * 0.5)

    # ── Node 1: Initial strike outcome ────────────────────────────────────
    strike_succeeds = rng.random() < params.strike_success_prob
    path.append("STRIKE_LAUNCHED")

    if not strike_succeeds:
        # Strike fails -> limited exchange most likely
        path.append("STRIKE_FAILS")
        if rng.random() < 0.55:
            return SimulationRun(2, path, False, rng.uniform(1, 7))
        return SimulationRun(1, path, False, rng.uniform(1, 14))

    path.append("STRIKE_SUCCEEDS")

    # ── Node 2: Iran retaliation decision ─────────────────────────────────
    iran_retaliates = rng.random() < base_retaliation
    if not iran_retaliates:
        path.append("IRAN_NO_RETALIATION")
        # De-escalation with ceasefire
        if rng.random() < 0.70:
            return SimulationRun(1, path, False, rng.uniform(3, 21))
        return SimulationRun(2, path, False, rng.uniform(7, 30))

    path.append("IRAN_RETALIATES")

    # ── Node 3: Proxy network activation ──────────────────────────────────
    hezbollah_on = rng.random() < params.hezbollah_activation_prob * intensity
    houthi_on    = rng.random() < params.houthi_escalation_prob * intensity
    militia_on   = rng.random() < params.iran_militia_iraq_prob * intensity

    if hezbollah_on:
        path.append("HEZBOLLAH_ACTIVATED")
    if houthi_on:
        path.append("HOUTHI_ACTIVATED")
    if militia_on:
        path.append("IRAQ_MILITIA_ACTIVATED")

    proxy_count = sum([hezbollah_on, houthi_on, militia_on])

    # ── Node 4: Strait of Hormuz disruption ───────────────────────────────
    hormuz_blocked = rng.random() < params.iran_hormuz_blockade_prob * (0.5 + intensity * 0.5)
    if hormuz_blocked:
        path.append("HORMUZ_DISRUPTION")
        oil_triggered = True

        # Hormuz blockade -> high probability of economic contagion path
        if rng.random() < params.global_recession_trigger_prob and proxy_count <= 1:
            return SimulationRun(8, path, False, rng.uniform(14, 60), True, hezbollah_on, houthi_on)

    # ── Node 5: US direct military entry ──────────────────────────────────
    us_enters = rng.random() < params.us_direct_entry_prob * intensity
    if us_enters:
        path.append("US_DIRECT_ENTRY")

    # ── Node 6: Escalation control / ceasefire window ─────────────────────
    ceasefire_prob = params.ceasefire_negotiation_prob
    # Modify ceasefire probability based on conditions
    if proxy_count >= 2:
        ceasefire_prob *= 0.55
    if hormuz_blocked:
        ceasefire_prob *= 0.70
    if us_enters:
        ceasefire_prob *= 0.80  # US entry escalates but also raises diplomatic pressure

    ceasefire = rng.random() < ceasefire_prob
    if ceasefire and not us_enters and proxy_count <= 1:
        path.append("CEASEFIRE_NEGOTIATED")
        day = rng.uniform(7, 30)
        if proxy_count == 0:
            return SimulationRun(2, path, False, day, oil_triggered, hezbollah_on, houthi_on)
        return SimulationRun(3, path, False, day, oil_triggered, hezbollah_on, houthi_on)

    # ── Node 7: Regional war threshold ────────────────────────────────────
    regional_war = (proxy_count >= 2 and us_enters) or rng.random() < (0.25 * proxy_count * intensity)

    # ── Node 8: Nuclear signaling threshold ───────────────────────────────
    # Israeli Samson Option: if hit hard enough
    israel_existential = rng.random() < (params.israel_existential_threshold * intensity)
    # Iran nuclear signal: if facing existential defeat
    iran_nuclear_signal = (
        us_enters
        and rng.random() < params.iran_nuclear_signaling_threshold * (1.5 * intensity)
    )

    nuclear_flag = israel_existential or iran_nuclear_signal
    if nuclear_flag:
        path.append("NUCLEAR_THRESHOLD_APPROACHED")
        # Nuclear signaling does not necessarily mean use - but flags RED
        if rng.random() < 0.75:
            return SimulationRun(7, path, True, rng.uniform(7, 60), oil_triggered, hezbollah_on, houthi_on)

    # ── Node 9: Determine war duration outcome ────────────────────────────
    if regional_war:
        path.append("REGIONAL_WAR")
        return SimulationRun(6, path, nuclear_flag, rng.uniform(30, 180), oil_triggered, hezbollah_on, houthi_on)

    if proxy_count >= 2:
        # Multi-front proxy war
        path.append("PROXY_EXPANSION")
        day = rng.uniform(7, 90)
        if us_enters:
            return SimulationRun(4 if day > 30 else 3, path, nuclear_flag, day, oil_triggered, hezbollah_on, houthi_on)
        return SimulationRun(5, path, nuclear_flag, day, oil_triggered, hezbollah_on, houthi_on)

    if proxy_count == 1:
        path.append("LIMITED_PROXY")
        day = rng.uniform(7, 60)
        return SimulationRun(5, path, nuclear_flag, day, oil_triggered, hezbollah_on, houthi_on)

    # Direct Iran-Israel/USA exchange without proxy expansion
    if us_enters:
        day = rng.uniform(14, 90)
        path.append("DIRECT_WAR")
        return SimulationRun(4 if day > 30 else 3, path, nuclear_flag, day, oil_triggered, hezbollah_on, houthi_on)

    # Limited exchange
    return SimulationRun(2, path, nuclear_flag, rng.uniform(3, 21), oil_triggered, hezbollah_on, houthi_on)


def run_monte_carlo(
    params: ScenarioParameters | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> MonteCarloResults:
    """
    Run the Monte Carlo simulation.

    Args:
        params: Scenario parameters. Uses defaults if None.
        progress_callback: Optional callable(completed, total) for progress reporting.

    Returns:
        MonteCarloResults with outcome distribution and confidence intervals.
    """
    if params is None:
        params = ScenarioParameters()

    rng = np.random.default_rng(params.random_seed)
    runs: list[SimulationRun] = []
    nuclear_count = 0

    for i in range(params.n_simulations):
        run = _simulate_single_run(params, rng)
        runs.append(run)
        if run.nuclear_flag:
            nuclear_count += 1
        if progress_callback and i % 500 == 0:
            progress_callback(i, params.n_simulations)

    n = params.n_simulations
    counts = Counter(run.outcome for run in runs)

    probs = {state: counts.get(state, 0) / n for state in OUTCOME_LABELS}
    cis   = {state: _wilson_ci(counts.get(state, 0), n) for state in OUTCOME_LABELS}

    # Mean day of outcome per state
    mean_days: dict[int, float] = {}
    for state in OUTCOME_LABELS:
        state_runs = [r.day_of_outcome for r in runs if r.outcome == state]
        mean_days[state] = float(np.mean(state_runs)) if state_runs else 0.0

    nuc_ci = _wilson_ci(nuclear_count, n)

    return MonteCarloResults(
        outcome_counts=counts,
        outcome_probabilities=probs,
        confidence_intervals=cis,
        nuclear_probability=nuclear_count / n,
        nuclear_ci=nuc_ci,
        mean_outcome_day=mean_days,
        n_simulations=n,
        runs=runs,
    )


def run_sensitivity_analysis(
    base_params: ScenarioParameters,
    n_points: int = 20,
) -> dict[str, list[dict]]:
    """
    Sweep key parameters to show sensitivity of outcome distribution.
    Returns dict of {param_name: [{"value": v, "probs": {...}}]}
    """
    results: dict[str, list[dict]] = {}

    sensitivity_params = [
        ("strike_intensity", np.linspace(0.1, 1.0, n_points)),
        ("iran_hormuz_blockade_prob", np.linspace(0.0, 1.0, n_points)),
        ("us_direct_entry_prob", np.linspace(0.0, 1.0, n_points)),
        ("hezbollah_activation_prob", np.linspace(0.0, 1.0, n_points)),
        ("ceasefire_negotiation_prob", np.linspace(0.0, 0.8, n_points)),
    ]

    for param_name, values in sensitivity_params:
        param_results = []
        for v in values:
            p = ScenarioParameters(**{**base_params.__dict__, param_name: v, "n_simulations": 2000})
            mc = run_monte_carlo(p)
            param_results.append({
                "value": float(v),
                "probs": mc.outcome_probabilities,
                "nuclear_prob": mc.nuclear_probability,
            })
        results[param_name] = param_results

    return results
