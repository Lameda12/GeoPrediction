"""
ARES Scenario: USA + Israel vs Iran
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Initial Conditions (public domain baseline):
  - Israel Air Force strikes Iranian nuclear sites (Fordow, Natanz, Arak)
  - USA provides ISR support + potential F-35 strike package
  - Iran retaliates via: ballistic missiles on Israel,
    Hezbollah rocket barrage, Houthi Red Sea disruption,
    militia attacks on US bases in Iraq/Syria
  - Strait of Hormuz mining/blockade probability: 40-60%

Simulation phases:
  - Day 1-7:   Initial exchange phase
  - Day 7-30:  Escalation/de-escalation window
  - Day 30-90: Economic contagion phase
  - Day 90-365: Strategic outcome stabilization
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from engine.montecarlo import ScenarioParameters, MonteCarloResults, run_monte_carlo
from engine.lanchester import (
    ForceState, CombatResult, scenario_usa_israel_vs_iran,
    lanchester_square_law, lanchester_linear_law,
)
from engine.escalation import (
    ActorProfile, EscalationState, simulate_escalation_ladder,
    compute_nuclear_threshold, _default_usa_iran_actors,
)
from engine.economic import (
    OilShockScenario, EconomicImpactResult, run_economic_simulation,
    build_gdp_impact_dataframe,
)


SCENARIO_NAME = "USA_ISRAEL_IRAN"
SCENARIO_VERSION = "1.0"


@dataclass
class ScenarioConfig:
    """Full configuration for the USA/Israel vs Iran scenario."""

    # ── Strike parameters ──────────────────────────────────────────────
    israel_strike_intensity: float = 0.80
    # 0-1: scope of Israeli air strike package
    # 0.5 = limited strikes (e.g., 1 site)
    # 0.8 = comprehensive multi-site campaign (Fordow + Natanz + Arak)
    # 1.0 = maximum effort incl. decapitation strikes

    usa_isr_support_only: bool = False
    # If False: USA provides strike support (F-35B/F-22 packages)
    # If True: USA ISR+logistics only, no direct strikes

    usa_direct_strike_prob: float = 0.55
    # Probability USA escalates from ISR support to direct strikes

    # ── Retaliation parameters ─────────────────────────────────────────
    iran_missile_salvo_size: int = 500
    # Estimated ballistic + cruise missiles in initial retaliation
    hezbollah_rocket_count: int = 130000
    houthi_activation: bool = True
    iraq_militia_attacks: bool = True

    # ── Hormuz parameters ─────────────────────────────────────────────
    hormuz_blockade_prob: float = 0.50
    # Base probability of full/partial blockade
    hormuz_blockade_pct: float = 0.45
    # If blockade: fraction of flow disrupted

    # ── Diplomatic parameters ──────────────────────────────────────────
    ceasefire_probability_30days: float = 0.35
    russia_china_mediation_effect: float = 0.15

    # ── Simulation parameters ─────────────────────────────────────────
    n_monte_carlo_runs: int = 10_000
    random_seed: Optional[int] = 42


@dataclass
class ScenarioResult:
    """Full results bundle for the USA/Israel vs Iran scenario."""
    config: ScenarioConfig
    monte_carlo: MonteCarloResults
    lanchester_air: dict[str, CombatResult]
    lanchester_missile: dict[str, CombatResult]
    lanchester_proxy: dict[str, CombatResult]
    escalation_state: EscalationState
    economic_impact: EconomicImpactResult
    phase_summaries: dict[str, dict]


def _build_monte_carlo_params(config: ScenarioConfig) -> ScenarioParameters:
    return ScenarioParameters(
        strike_intensity=config.israel_strike_intensity,
        strike_success_prob=0.72 * (0.8 + config.israel_strike_intensity * 0.2),
        iran_retaliation_prob=0.92,
        hezbollah_activation_prob=0.85 * config.israel_strike_intensity,
        houthi_escalation_prob=0.78 if config.houthi_activation else 0.10,
        iran_militia_iraq_prob=0.88 if config.iraq_militia_attacks else 0.20,
        us_direct_entry_prob=config.usa_direct_strike_prob if not config.usa_isr_support_only else 0.10,
        iran_hormuz_blockade_prob=config.hormuz_blockade_prob,
        ceasefire_negotiation_prob=config.ceasefire_probability_30days + config.russia_china_mediation_effect,
        us_deterrence_credibility=0.78,
        israel_existential_threshold=0.28,
        oil_disruption_pct=config.hormuz_blockade_pct,
        n_simulations=config.n_monte_carlo_runs,
        random_seed=config.random_seed,
    )


def _build_oil_shock_scenario(config: ScenarioConfig) -> OilShockScenario:
    return OilShockScenario(
        hormuz_blockade_pct=config.hormuz_blockade_pct,
        disruption_duration_months=3.0,
        iea_spr_release_mbpd=4.0,
        opec_spare_capacity_mbpd=3.5,
        baseline_oil_price_usd=82.0,
        red_sea_disruption_pct=0.20 if config.houthi_activation else 0.0,
        iran_sanctions_intensity=0.95,
        iran_oil_offline_mbpd=1.5,
    )


def _compute_phase_summaries(
    result_bundle: dict,
    config: ScenarioConfig,
) -> dict[str, dict]:
    """Compute phase-by-phase narrative summaries."""

    mc: MonteCarloResults = result_bundle["monte_carlo"]
    eco: EconomicImpactResult = result_bundle["economic"]

    probs = mc.outcome_probabilities
    cis   = mc.confidence_intervals

    return {
        "phase_1_day1_7": {
            "description": "Initial Strike Exchange",
            "events": [
                "Israel F-35I/F-16I strike package on Fordow/Natanz/Arak",
                "US B-2/F-35B forward deployment to Diego Garcia/regional bases",
                f"Iran missile retaliation: estimated {config.iran_missile_salvo_size} ballistic + cruise missiles",
                "Arrow-3/Patriot/Iron Dome intercept engagement",
                "Hezbollah activation: probability {:.0f}%".format(
                    mc.outcome_probabilities.get(5, 0.15) * 100 +
                    mc.outcome_probabilities.get(6, 0.05) * 100
                ),
            ],
            "key_uncertainties": [
                "Israeli strike success vs dispersed/hardened sites",
                "Iron Dome saturation under mass rocket + missile salvo",
                "US carrier group positioning and ROE",
            ],
        },
        "phase_2_day7_30": {
            "description": "Escalation / De-escalation Window",
            "p_ceasefire": probs.get(1, 0.0) + probs.get(2, 0.0),
            "p_conventional_war": probs.get(3, 0.0) + probs.get(4, 0.0),
            "p_proxy_expansion": probs.get(5, 0.0),
            "p_nuclear_signal": mc.nuclear_probability,
            "nuclear_flag": mc.nuclear_probability > 0.15,
            "hormuz_probability": config.hormuz_blockade_prob,
            "key_actors": ["Qatar_mediation", "UN_Security_Council", "China_Russia_pressure"],
        },
        "phase_3_day30_90": {
            "description": "Economic Contagion Phase",
            "oil_price_peak_usd": eco.oil_price_peak,
            "global_gdp_loss_12mo": eco.global_gdp_loss_pct,
            "recession_probability": eco.recession_probability,
            "usa_gdp_12mo": float(eco.gdp_impact["USA"][12]) if len(eco.gdp_impact["USA"]) > 12 else 0.0,
            "eu_gdp_12mo": float(eco.gdp_impact["EU"][12]) if len(eco.gdp_impact["EU"]) > 12 else 0.0,
            "china_gdp_12mo": float(eco.gdp_impact["China"][12]) if len(eco.gdp_impact["China"]) > 12 else 0.0,
            "p_economic_contagion_outcome": probs.get(8, 0.0),
        },
        "phase_4_day90_365": {
            "description": "Strategic Outcome Stabilization",
            "most_probable_outcome": max(probs, key=probs.get),
            "second_most_probable": sorted(probs, key=probs.get, reverse=True)[1],
            "p_regional_war": probs.get(6, 0.0),
            "iran_nuclear_breakout_risk": "HIGH" if mc.nuclear_probability > 0.15 else "MEDIUM",
            "us_israel_strategic_objective_achieved_prob": probs.get(1, 0.0) + probs.get(2, 0.0) * 0.6,
            "recovery_timeline_months": {
                c: eco.recovery_months.get(c, 36.0)
                for c in ["USA", "Israel", "Iran", "Saudi_Arabia", "EU", "China", "India"]
                if c in eco.recovery_months
            },
        },
    }


def run_scenario(
    config: ScenarioConfig | None = None,
    verbose: bool = True,
    progress_callback=None,
) -> ScenarioResult:
    """
    Run the full USA + Israel vs Iran scenario simulation.

    Args:
        config: Scenario configuration. Uses defaults if None.
        verbose: Print progress and results.
        progress_callback: Optional callable for progress updates.

    Returns:
        ScenarioResult with all simulation outputs.
    """
    if config is None:
        config = ScenarioConfig()

    if verbose:
        print("[ARES] Starting USA + Israel vs Iran scenario simulation...")
        print(f"       Strike intensity: {config.israel_strike_intensity:.2f}")
        print(f"       Monte Carlo runs: {config.n_monte_carlo_runs:,}")

    # ── Monte Carlo simulation ─────────────────────────────────────────
    if verbose:
        print("[ARES] Running Monte Carlo escalation tree...")
    mc_params = _build_monte_carlo_params(config)
    mc_result = run_monte_carlo(mc_params, progress_callback=progress_callback)

    # ── Lanchester combat models ───────────────────────────────────────
    if verbose:
        print("[ARES] Running Lanchester combat equations...")
    lanchester_results = scenario_usa_israel_vs_iran()

    # ── Escalation ladder ─────────────────────────────────────────────
    if verbose:
        print("[ARES] Simulating escalation ladder dynamics...")
    actors = _default_usa_iran_actors()
    esc_state = simulate_escalation_ladder(
        initial_rung=9,
        actors=actors,
        n_days=90,
        rng_seed=config.random_seed,
    )

    # ── Economic simulation ────────────────────────────────────────────
    if verbose:
        print("[ARES] Running economic shock propagation...")
    oil_scenario = _build_oil_shock_scenario(config)
    eco_result = run_economic_simulation(oil_scenario, n_months=36)

    # ── Phase summaries ───────────────────────────────────────────────
    phase_summaries = _compute_phase_summaries(
        {"monte_carlo": mc_result, "economic": eco_result},
        config,
    )

    result = ScenarioResult(
        config=config,
        monte_carlo=mc_result,
        lanchester_air=lanchester_results["air_campaign"],
        lanchester_missile=lanchester_results["missile_exchange"],
        lanchester_proxy=lanchester_results["proxy_warfare"],
        escalation_state=esc_state,
        economic_impact=eco_result,
        phase_summaries=phase_summaries,
    )

    if verbose:
        _print_full_report(result)

    return result


def _print_full_report(result: ScenarioResult) -> None:
    """Print structured terminal report."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console = Console()

    console.print()
    console.print(Panel(
        "[bold red]ARES - ADAPTIVE RISK AND ESCALATION SIMULATOR[/bold red]\n"
        "[yellow]Scenario: USA + Israel vs Iran[/yellow]\n"
        "[dim]MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE[/dim]",
        border_style="red",
        padding=(1, 4),
    ))

    # Monte Carlo outcome table
    mc = result.monte_carlo
    table = Table(
        title="[bold]OUTCOME PROBABILITY DISTRIBUTION[/bold]",
        box=box.HEAVY,
        style="dim",
        header_style="bold yellow",
        show_lines=True,
    )
    table.add_column("State", style="bold white", width=4)
    table.add_column("Outcome", width=42)
    table.add_column("Probability", justify="right", width=12)
    table.add_column("95% CI", justify="right", width=16)
    table.add_column("Mean Day", justify="right", width=10)

    from engine.montecarlo import OUTCOME_LABELS
    for state, label in OUTCOME_LABELS.items():
        p = mc.outcome_probabilities.get(state, 0.0)
        lo, hi = mc.confidence_intervals.get(state, (0.0, 0.0))
        day = mc.mean_outcome_day.get(state, 0.0)
        bar_count = int(p * 30)
        bar = "█" * bar_count
        color = "green" if state == 1 else ("yellow" if state <= 3 else ("red" if state >= 6 else "orange3"))
        table.add_row(
            f"[{color}]{state}[/{color}]",
            f"[{color}]{label}[/{color}]",
            f"[bold {color}]{p*100:.1f}%[/bold {color}]",
            f"[dim]{lo*100:.1f}–{hi*100:.1f}%[/dim]",
            f"{day:.0f}d",
        )

    console.print(table)

    # Nuclear flag
    nuc_p = mc.nuclear_probability
    nuc_lo, nuc_hi = mc.nuclear_ci
    nuc_color = "bold red" if nuc_p > 0.15 else "yellow"
    nuclear_text = (
        f"[{nuc_color}]Nuclear Threshold Probability: {nuc_p*100:.1f}%  "
        f"[95% CI: {nuc_lo*100:.1f}–{nuc_hi*100:.1f}%][/{nuc_color}]"
    )
    if nuc_p > 0.15:
        nuclear_text += "\n[bold red blink]*** RED FLAG: NUCLEAR THRESHOLD > 15% ***[/bold red blink]"
    console.print(Panel(nuclear_text, title="NUCLEAR RISK ASSESSMENT", border_style="red"))

    # Economic summary
    eco = result.economic_impact
    eco_table = Table(
        title=f"[bold]ECONOMIC IMPACT  |  Oil Peak: ${eco.oil_price_peak:.0f}/bbl[/bold]",
        box=box.SIMPLE_HEAVY,
        header_style="bold yellow",
    )
    eco_table.add_column("Country", width=16)
    eco_table.add_column("12mo GDP Chg", justify="right", width=12)
    eco_table.add_column("24mo GDP Chg", justify="right", width=12)
    eco_table.add_column("Recovery", justify="right", width=14)

    for country in ["USA", "Israel", "Iran", "Saudi_Arabia", "EU", "China", "India"]:
        imp = eco.gdp_impact.get(country)
        if imp is None:
            continue
        m12 = float(imp[12]) if len(imp) > 12 else float(imp[-1])
        m24 = float(imp[24]) if len(imp) > 24 else float(imp[-1])
        rec = eco.recovery_months.get(country, 36.0)
        color = "green" if m12 > 0 else ("red" if m12 < -3 else "yellow")
        eco_table.add_row(
            country,
            f"[{color}]{m12:+.2f}%[/{color}]",
            f"[{color}]{m24:+.2f}%[/{color}]",
            f"{rec:.0f} mo",
        )

    console.print(eco_table)
    console.print(f"\n[dim]Global recession probability: {eco.recession_probability*100:.1f}%[/dim]")

    # Phase summaries
    for phase_key, phase in result.phase_summaries.items():
        console.print(f"\n[bold cyan]{phase['description'].upper()}[/bold cyan]")


def get_scenario_as_dataframes(result: ScenarioResult) -> dict[str, pd.DataFrame]:
    """Export all scenario results as DataFrames for CSV export."""
    dfs = {}

    # Outcome probabilities
    mc = result.monte_carlo
    from engine.montecarlo import OUTCOME_LABELS
    dfs["outcome_probabilities"] = pd.DataFrame([
        {
            "state": s,
            "label": OUTCOME_LABELS[s],
            "probability": mc.outcome_probabilities.get(s, 0.0),
            "ci_low": mc.confidence_intervals.get(s, (0, 0))[0],
            "ci_high": mc.confidence_intervals.get(s, (0, 0))[1],
            "mean_day": mc.mean_outcome_day.get(s, 0.0),
        }
        for s in OUTCOME_LABELS
    ])

    # GDP impact
    dfs["gdp_impact"] = build_gdp_impact_dataframe(result.economic_impact)

    # Oil price
    dfs["oil_price"] = pd.DataFrame({
        "month": result.economic_impact.months,
        "price_usd": result.economic_impact.oil_price_path[:len(result.economic_impact.months)],
    })

    # Lanchester air (square law)
    air_sq = result.lanchester_air["square"]
    dfs["lanchester_air_square"] = pd.DataFrame({
        "day": air_sq.time_days,
        air_sq.name_x: air_sq.force_x,
        air_sq.name_y: air_sq.force_y,
    })

    # Lanchester proxy (linear law)
    prx_lin = result.lanchester_proxy["linear"]
    dfs["lanchester_proxy_linear"] = pd.DataFrame({
        "day": prx_lin.time_days,
        prx_lin.name_x: prx_lin.force_x,
        prx_lin.name_y: prx_lin.force_y,
    })

    # Escalation ladder
    esc = result.escalation_state
    dfs["escalation_ladder"] = pd.DataFrame(esc.history)

    return dfs
