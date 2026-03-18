"""
ARES Scenario: Global Spillover / Second-Order Contagion
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Models second-order effects of the USA+Israel vs Iran conflict:
  - Chinese opportunistic action in Taiwan Strait
  - Russian leverage maneuvers in Ukraine/Black Sea
  - Saudi-Iran proxy balance shift
  - Global financial contagion (credit markets, energy transition)
  - Refugee/humanitarian crisis propagation
  - Alliance cohesion stress (NATO, Abraham Accords)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from engine.economic import OilShockScenario, run_economic_simulation, EconomicImpactResult
from engine.montecarlo import ScenarioParameters, run_monte_carlo, MonteCarloResults, OUTCOME_LABELS


@dataclass
class SpilloverConfig:
    """Configuration for global spillover scenario."""

    # ── Input from primary scenario ───────────────────────────────────
    primary_scenario_outcome: int = 5   # Most probable outcome from USA-Iran MC
    primary_oil_shock_pct: float = 0.50 # Oil disruption fraction from primary
    us_force_committed_pct: float = 0.40 # Fraction of US military tied down in ME

    # ── China Taiwan opportunism ──────────────────────────────────────
    china_taiwan_opportunism_base: float = 0.08
    # P(China accelerates Taiwan action if US tied down)
    # Source: RAND "War with China" (2016), CFR analysis
    us_distraction_multiplier: float = 2.0

    # ── Russia Ukraine leverage ───────────────────────────────────────
    russia_ukraine_escalation_base: float = 0.15
    russia_energy_leverage_pct: float = 0.12  # Fraction of EU gas still from Russia

    # ── Saudi Arabia balance shift ────────────────────────────────────
    saudi_iran_normalization_collapse: float = 0.70
    saudi_opec_plus_cohesion: float = 0.65

    # ── Alliance stress ───────────────────────────────────────────────
    nato_article5_invocation_prob: float = 0.05
    abraham_accords_stress_index: float = 0.55

    # ── Humanitarian crisis ───────────────────────────────────────────
    refugee_flows_millions: float = 2.5
    humanitarian_cost_billion_usd: float = 45.0

    # ── Financial contagion ───────────────────────────────────────────
    credit_spread_shock_bps: float = 150.0
    em_capital_flight_billion_usd: float = 200.0
    global_equity_drawdown_pct: float = -0.15

    # ── Simulation parameters ─────────────────────────────────────────
    n_monte_carlo_runs: int = 5_000
    random_seed: Optional[int] = 43


@dataclass
class SpilloverResult:
    config: SpilloverConfig
    china_taiwan_prob: float
    russia_leverage_prob: float
    nato_stress_index: float
    economic_contagion: EconomicImpactResult
    financial_shock: dict
    humanitarian_metrics: dict
    timeline: pd.DataFrame
    secondary_outcome_probs: dict[str, float]


def compute_china_opportunism(config: SpilloverConfig) -> dict:
    """
    Model Chinese opportunistic action probability under US distraction.
    Based on window-of-opportunity framework (Copeland 2000, Christensen 2011).
    """
    base = config.china_taiwan_opportunism_base
    us_distraction = config.us_force_committed_pct * config.us_distraction_multiplier
    us_carrier_gap = config.us_force_committed_pct * 0.5  # Fewer carriers in Pacific

    p_opportunism = min(0.95, base * (1.0 + us_distraction + us_carrier_gap))

    # Moderated by: Chinese economic interdependence, PLA readiness, Xi calculation
    pla_readiness = 0.72  # Not yet ready for contested amphibious (RAND estimates)
    economic_cost = 0.65  # Trade war + sanctions cost perception
    xi_calculation = 0.55  # Risk-aversion in Taiwan invasion

    p_opportunism *= (1.0 - economic_cost * 0.3) * pla_readiness * (0.5 + xi_calculation * 0.5)

    return {
        "p_opportunism": float(p_opportunism),
        "p_military_exercises": min(0.90, p_opportunism * 2.5),
        "p_blockade": min(0.25, p_opportunism * 0.4),
        "p_invasion": min(0.12, p_opportunism * 0.15),
        "p_cyberattack_escalation": min(0.45, p_opportunism * 1.2),
        "us_pacific_response_constrained_prob": min(0.70, config.us_force_committed_pct * 1.5),
    }


def compute_russia_leverage(config: SpilloverConfig) -> dict:
    """
    Model Russian leverage maneuvers during US/Middle East engagement.
    Russia has historically exploited Western distraction (2008 Georgia, 2014 Crimea).
    """
    base = config.russia_ukraine_escalation_base
    us_distraction_effect = config.us_force_committed_pct * 0.8

    p_offensive_action = min(0.60, base * (1.0 + us_distraction_effect))
    p_energy_blackmail = config.russia_energy_leverage_pct * 2.0

    return {
        "p_offensive_military_action": float(p_offensive_action),
        "p_energy_leverage_eu": float(min(0.80, p_energy_blackmail)),
        "p_cyberattacks_escalation": float(min(0.55, p_offensive_action * 1.5)),
        "p_nuclear_signaling": float(min(0.20, p_offensive_action * 0.3)),
        "eu_response_constrained_prob": float(min(0.65, config.us_force_committed_pct)),
        "nato_article5_trigger": float(config.nato_article5_invocation_prob),
    }


def compute_financial_contagion(config: SpilloverConfig, oil_peak: float) -> dict:
    """
    Model global financial market contagion.
    Based on VIX-spread dynamics and EM flight-to-safety patterns.
    """
    vix_spike = min(80.0, 20.0 + (oil_peak - 82.0) * 0.3 + config.credit_spread_shock_bps * 0.05)
    em_gdp_loss = config.em_capital_flight_billion_usd / 100.0  # rough GDP impact per $bn

    return {
        "vix_peak_estimate": float(vix_spike),
        "credit_spread_widening_bps": float(config.credit_spread_shock_bps),
        "em_capital_flight_billion_usd": float(config.em_capital_flight_billion_usd),
        "global_equity_drawdown_pct": float(config.global_equity_drawdown_pct),
        "usd_strengthen_pct": float(min(15.0, config.em_capital_flight_billion_usd / 50.0)),
        "em_gdp_loss_estimate_pct": float(-min(3.0, em_gdp_loss * 0.5)),
        "sovereign_debt_stress_countries": [
            "Turkey", "Egypt", "Pakistan", "Lebanon", "Jordan", "Iraq"
        ],
        "recession_contagion_prob": float(min(0.65, (oil_peak - 82.0) / 200.0 * 0.5 + 0.25)),
    }


def build_spillover_timeline(config: SpilloverConfig, china: dict, russia: dict) -> pd.DataFrame:
    """Build event probability timeline for spillover effects."""
    rows = []

    events = [
        # (day_start, day_end, event, probability, actor)
        (1,   7,   "Oil markets spike, VIX surge",        0.92,  "Global_Markets"),
        (3,   14,  "China PLA exercises near Taiwan",     china["p_military_exercises"], "China"),
        (7,   21,  "Russia probing attacks in Ukraine",   russia["p_offensive_military_action"], "Russia"),
        (7,   30,  "Houthi Red Sea interdiction escalation", 0.75, "Houthis"),
        (14,  45,  "OPEC+ emergency meeting / SPR release", 0.85, "Saudi_Arabia"),
        (14,  60,  "UN Security Council emergency session", 0.95, "UN"),
        (21,  60,  "EU emergency energy summit",          0.80, "EU"),
        (30,  90,  "IMF emergency credit lines activated", 0.65, "IMF"),
        (30,  90,  "Russia-China coordination signal",    0.70, "Russia_China"),
        (30, 120,  "Abraham Accords stress test",         config.abraham_accords_stress_index, "Gulf_States"),
        (45, 120,  "China blockade of Taiwan (partial)",  china["p_blockade"], "China"),
        (60, 180,  "NATO Article 5 consultations",        config.nato_article5_invocation_prob * 3, "NATO"),
        (90, 365,  "New nuclear deterrence architecture discussions", 0.55, "P5"),
        (90, 365,  "Iran nuclear breakout acceleration",  0.45, "Iran"),
        (90, 365,  "Global recession confirmed",          0.40, "Global_Markets"),
    ]

    for d_start, d_end, event, prob, actor in events:
        rows.append({
            "day_start": d_start,
            "day_end": d_end,
            "event": event,
            "probability": min(1.0, prob),
            "actor": actor,
        })

    return pd.DataFrame(rows)


def run_spillover_scenario(
    config: SpilloverConfig | None = None,
    verbose: bool = True,
) -> SpilloverResult:
    """
    Run the global spillover scenario.

    Args:
        config: Spillover configuration.
        verbose: Print summary.

    Returns:
        SpilloverResult with all second-order effects.
    """
    if config is None:
        config = SpilloverConfig()

    if verbose:
        print("[ARES] Running Global Spillover / Second-Order Contagion scenario...")

    # Economic contagion (amplified oil shock)
    oil_scenario = OilShockScenario(
        hormuz_blockade_pct=config.primary_oil_shock_pct,
        red_sea_disruption_pct=0.30,
        iran_sanctions_intensity=0.95,
        iran_oil_offline_mbpd=1.5,
    )
    eco = run_economic_simulation(oil_scenario, n_months=36)

    # China opportunism
    china_analysis = compute_china_opportunism(config)

    # Russia leverage
    russia_analysis = compute_russia_leverage(config)

    # Financial contagion
    fin_analysis = compute_financial_contagion(config, eco.oil_price_peak)

    # Spillover timeline
    timeline = build_spillover_timeline(config, china_analysis, russia_analysis)

    # Humanitarian metrics
    humanitarian = {
        "refugee_flows_millions": config.refugee_flows_millions,
        "humanitarian_cost_billion_usd": config.humanitarian_cost_billion_usd,
        "affected_countries": ["Lebanon", "Jordan", "Iraq", "Yemen", "Syria"],
        "un_funding_gap_billion_usd": config.humanitarian_cost_billion_usd * 0.4,
    }

    # Alliance cohesion
    nato_stress = (
        config.us_force_committed_pct * 0.4
        + russia_analysis["p_offensive_military_action"] * 0.4
        + config.nato_article5_invocation_prob * 0.2
    )

    # Secondary outcome probabilities
    secondary_outcomes = {
        "China_Taiwan_military_action": china_analysis["p_military_exercises"],
        "Russia_Ukraine_escalation": russia_analysis["p_offensive_military_action"],
        "NATO_Article5_trigger": russia_analysis["nato_article5_trigger"],
        "Global_recession_18mo": fin_analysis["recession_contagion_prob"],
        "Iran_nuclear_breakout": 0.35 * (config.primary_oil_shock_pct + config.us_force_committed_pct) / 2.0,
        "Abraham_Accords_collapse": config.abraham_accords_stress_index * 0.6,
        "OPEC_plus_fracture": 1.0 - config.saudi_opec_plus_cohesion,
        "Lebanon_state_collapse": 0.55,
        "Jordan_destabilization": 0.30,
        "Global_energy_transition_acceleration": 0.70,  # Shock drives renewables investment
    }

    result = SpilloverResult(
        config=config,
        china_taiwan_prob=china_analysis["p_military_exercises"],
        russia_leverage_prob=russia_analysis["p_offensive_military_action"],
        nato_stress_index=nato_stress,
        economic_contagion=eco,
        financial_shock=fin_analysis,
        humanitarian_metrics=humanitarian,
        timeline=timeline,
        secondary_outcome_probs=secondary_outcomes,
    )

    if verbose:
        _print_spillover_report(result)

    return result


def _print_spillover_report(result: SpilloverResult) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box

        console = Console()
        console.print("\n[bold red]GLOBAL SPILLOVER ANALYSIS[/bold red]")
        console.print("[dim]MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE[/dim]\n")

        table = Table(title="Second-Order Outcome Probabilities", box=box.SIMPLE_HEAVY)
        table.add_column("Event", width=45)
        table.add_column("Probability", justify="right", width=12)

        for event, prob in sorted(result.secondary_outcome_probs.items(), key=lambda x: -x[1]):
            color = "red" if prob > 0.5 else ("yellow" if prob > 0.25 else "green")
            table.add_row(
                event.replace("_", " "),
                f"[{color}]{prob*100:.1f}%[/{color}]",
            )

        console.print(table)
        console.print(f"\n[bold]Financial Contagion:[/bold]")
        console.print(f"  VIX Peak: {result.financial_shock['vix_peak_estimate']:.0f}")
        console.print(f"  EM Capital Flight: ${result.financial_shock['em_capital_flight_billion_usd']:.0f}bn")
        console.print(f"  Global Equity Drawdown: {result.financial_shock['global_equity_drawdown_pct']*100:.1f}%")

    except ImportError:
        print("\nGLOBAL SPILLOVER SUMMARY")
        for event, prob in result.secondary_outcome_probs.items():
            print(f"  {event}: {prob*100:.1f}%")
