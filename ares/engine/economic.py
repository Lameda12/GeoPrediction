"""
ARES Economic Shock Propagation Model
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Implements:
  1. Oil price shock model (Strait of Hormuz disruption)
  2. Simplified Leontief input-output sector propagation
  3. GDP impact curves for key actors over 12/24/36 month windows
  4. Trade disruption and sanctions amplification

References:
  - Leontief, W. (1970). Environmental repercussions and the economic structure.
  - IMF Working Paper: Oil Price Shocks and the Global Economy (2018)
  - World Bank: The Impact of Oil Price Shocks (2015)
  - Hamilton, J.D. (2009). Causes and Consequences of the Oil Shock of 2007-08.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


# ─── Country baseline data ────────────────────────────────────────────────────

COUNTRY_PROFILES = {
    "USA": {
        "gdp_trillion": 27.4,
        "oil_import_dep": 0.10,
        "oil_price_elasticity": -0.008,
        "trade_openness": 0.25,
        "financial_depth_index": 0.99,
        "sector_weights": {"energy": 0.08, "manufacturing": 0.11, "finance": 0.21, "services": 0.78},
        "iran_trade_share": 0.001,
        "hormuz_exposure": 0.15,
        "reserve_currency_buffer": 0.95,
    },
    "Israel": {
        "gdp_trillion": 0.521,
        "oil_import_dep": 0.99,
        "oil_price_elasticity": -0.015,
        "trade_openness": 0.58,
        "financial_depth_index": 0.85,
        "sector_weights": {"energy": 0.02, "technology": 0.18, "manufacturing": 0.13, "services": 0.73},
        "iran_trade_share": 0.0,
        "hormuz_exposure": 0.35,
        "war_economy_capacity": 0.85,
    },
    "Iran": {
        "gdp_trillion": 0.401,
        "oil_import_dep": -0.79,  # Net exporter
        "oil_price_elasticity": 0.12,
        "trade_openness": 0.30,
        "financial_depth_index": 0.35,
        "sector_weights": {"oil_gas": 0.35, "manufacturing": 0.13, "services": 0.43},
        "sanctions_amplifier": 1.8,
        "china_lifeline_factor": 0.55,
        "hormuz_leverage": 0.90,
    },
    "Saudi_Arabia": {
        "gdp_trillion": 1.068,
        "oil_import_dep": -1.72,  # Major exporter (mbpd exports / consumption)
        "oil_price_elasticity": 0.15,
        "trade_openness": 0.60,
        "financial_depth_index": 0.75,
        "sector_weights": {"oil_gas": 0.42, "manufacturing": 0.10, "services": 0.48},
        "swf_buffer_months": 24,
        "fiscal_breakeven_oil": 78.0,
    },
    "China": {
        "gdp_trillion": 17.7,
        "oil_import_dep": 0.75,
        "oil_price_elasticity": -0.018,
        "trade_openness": 0.37,
        "financial_depth_index": 0.80,
        "sector_weights": {"manufacturing": 0.28, "services": 0.54, "agriculture": 0.07},
        "iran_oil_dependency": 0.09,
        "hormuz_exposure": 0.55,
        "bri_exposure": 0.08,
    },
    "EU": {
        "gdp_trillion": 18.4,
        "oil_import_dep": 0.85,
        "oil_price_elasticity": -0.014,
        "trade_openness": 0.86,
        "financial_depth_index": 0.90,
        "sector_weights": {"manufacturing": 0.20, "services": 0.74, "agriculture": 0.015},
        "hormuz_exposure": 0.50,
        "energy_transition_buffer": 0.30,
    },
    "India": {
        "gdp_trillion": 3.73,
        "oil_import_dep": 0.85,
        "oil_price_elasticity": -0.016,
        "trade_openness": 0.44,
        "financial_depth_index": 0.65,
        "sector_weights": {"services": 0.55, "manufacturing": 0.16, "agriculture": 0.17},
        "hormuz_exposure": 0.65,
        "russia_oil_alternative": 0.35,
    },
}

# Leontief inter-sector multipliers (simplified)
SECTOR_MULTIPLIERS = {
    ("energy", "manufacturing"): 0.35,
    ("energy", "transport"):     0.45,
    ("energy", "agriculture"):   0.15,
    ("energy", "finance"):       0.08,
    ("energy", "services"):      0.12,
    ("manufacturing", "services"): 0.22,
    ("finance", "manufacturing"):  0.18,
    ("finance", "services"):       0.15,
    ("trade_disruption", "all"):   0.18,
}


@dataclass
class OilShockScenario:
    """Parameters defining the oil shock event."""
    hormuz_blockade_pct: float = 0.45       # Fraction of flow disrupted (0-1)
    disruption_duration_months: float = 3.0
    iea_spr_release_mbpd: float = 4.0       # IEA Strategic Petroleum Reserve release
    opec_spare_capacity_mbpd: float = 3.5   # OPEC surplus that can be activated
    baseline_oil_price_usd: float = 82.0
    global_demand_mbpd: float = 103.0
    hormuz_flow_mbpd: float = 21.0
    red_sea_disruption_pct: float = 0.20    # Additional Red Sea trade disruption
    iran_sanctions_intensity: float = 0.90  # 0-1
    iran_oil_offline_mbpd: float = 1.5      # Iranian exports taken offline by conflict


@dataclass
class EconomicImpactResult:
    """Results of economic impact simulation."""
    oil_price_path: np.ndarray        # $/barrel over simulation period
    months: np.ndarray
    gdp_impact: dict[str, np.ndarray] # Country -> GDP impact % per month (cumulative)
    sector_impacts: dict[str, dict[str, np.ndarray]]  # Country -> sector -> impact
    trade_loss_billion: dict[str, np.ndarray]
    oil_price_peak: float
    global_gdp_loss_pct: float
    recession_probability: float
    recovery_months: dict[str, float]


def compute_oil_price_shock(scenario: OilShockScenario) -> np.ndarray:
    """
    Model oil price path over 36 months given disruption scenario.

    Uses simplified supply-demand clearing:
      disrupted_supply = baseline - (hormuz_disruption + iran_offline - offsets)
      price_shock = baseline * (demand_elasticity_factor)^(-1) * supply_gap_pct

    Returns: array of oil prices in USD/barrel over 36 months.
    """
    months = np.arange(0, 37, 1.0)

    # Supply gap calculation
    hormuz_disrupted = scenario.hormuz_flow_mbpd * scenario.hormuz_blockade_pct
    total_disrupted = hormuz_disrupted + scenario.iran_oil_offline_mbpd
    offset = min(total_disrupted, scenario.iea_spr_release_mbpd + scenario.opec_spare_capacity_mbpd)
    net_disruption_mbpd = max(0.0, total_disrupted - offset)

    supply_gap_pct = net_disruption_mbpd / scenario.global_demand_mbpd

    # Price elasticity of supply/demand: rough -0.15 demand side
    # Price spike = supply_gap / |demand_elasticity|
    demand_elasticity = -0.15
    price_spike_pct = supply_gap_pct / abs(demand_elasticity)

    peak_price = scenario.baseline_oil_price_usd * (1.0 + price_spike_pct)
    peak_price = min(peak_price, 300.0)  # Physical ceiling

    # Time profile: spike then gradual recovery
    peak_month = 2.0
    recovery_half_life = scenario.disruption_duration_months * 1.5

    prices = np.zeros(len(months))
    for i, m in enumerate(months):
        if m <= peak_month:
            # Rapid rise to peak
            prices[i] = scenario.baseline_oil_price_usd + (peak_price - scenario.baseline_oil_price_usd) * (m / peak_month)
        else:
            # Exponential decay back toward new equilibrium
            new_equilibrium = scenario.baseline_oil_price_usd * 1.15  # Permanently elevated
            decay = np.exp(-(m - peak_month) / recovery_half_life)
            prices[i] = new_equilibrium + (peak_price - new_equilibrium) * decay

    return prices


def compute_sector_propagation(
    country: str,
    energy_shock_pct: float,
    trade_disruption_pct: float,
    months: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    Simplified Leontief sector propagation.
    Returns cumulative GDP impact % per sector over time.
    """
    profile = COUNTRY_PROFILES.get(country, {})
    sector_weights = profile.get("sector_weights", {"services": 0.6, "manufacturing": 0.2})

    impacts = {}

    # Energy sector direct impact
    if "energy" in sector_weights or "oil_gas" in sector_weights:
        energy_weight = sector_weights.get("energy", sector_weights.get("oil_gas", 0.08))
        if profile.get("oil_import_dep", 0) < 0:  # Exporter: oil price up = good initially
            energy_base = energy_shock_pct * 0.3  # War discount on revenue
        else:
            energy_base = -energy_shock_pct * energy_weight * 0.5
        impacts["energy"] = _time_profile(energy_base, months, ramp_months=2, decay=False)

    # Manufacturing impact via energy costs
    if "manufacturing" in sector_weights:
        mfg_weight = sector_weights["manufacturing"]
        energy_passthrough = SECTOR_MULTIPLIERS.get(("energy", "manufacturing"), 0.35)
        mfg_base = -energy_shock_pct * energy_passthrough * mfg_weight
        impacts["manufacturing"] = _time_profile(mfg_base, months, ramp_months=3)

    # Services (includes finance, retail)
    if "services" in sector_weights:
        svc_weight = sector_weights["services"]
        svc_base = -energy_shock_pct * 0.12 * svc_weight - trade_disruption_pct * 0.08
        impacts["services"] = _time_profile(svc_base, months, ramp_months=4)

    # Finance sector (credit tightening from uncertainty)
    fin_weight = sector_weights.get("finance", 0.10)
    fin_base = -energy_shock_pct * 0.08 * fin_weight - trade_disruption_pct * 0.10
    impacts["finance"] = _time_profile(fin_base, months, ramp_months=5, decay=True)

    return impacts


def _time_profile(
    impact: float,
    months: np.ndarray,
    ramp_months: float = 3.0,
    decay: bool = True,
    half_life: float = 12.0,
) -> np.ndarray:
    """Build time profile for an impact: ramp up, then optionally decay."""
    result = np.zeros(len(months))
    for i, m in enumerate(months):
        if m <= ramp_months:
            result[i] = impact * (m / ramp_months)
        else:
            if decay:
                result[i] = impact * np.exp(-(m - ramp_months) / half_life)
            else:
                result[i] = impact
    return result


def run_economic_simulation(
    scenario: OilShockScenario | None = None,
    n_months: int = 36,
) -> EconomicImpactResult:
    """
    Run full economic shock propagation simulation.

    Returns GDP impact curves per country over n_months window.
    """
    if scenario is None:
        scenario = OilShockScenario()

    months = np.arange(0, n_months + 1, 1.0)

    # Oil price path
    oil_prices = compute_oil_price_shock(scenario)
    # Extend or truncate to match months
    if len(oil_prices) < len(months):
        oil_prices = np.concatenate([oil_prices, np.full(len(months) - len(oil_prices), oil_prices[-1])])
    oil_prices = oil_prices[:len(months)]

    oil_price_peak = float(oil_prices.max())
    oil_shock_pct = (oil_price_peak - scenario.baseline_oil_price_usd) / scenario.baseline_oil_price_usd

    # Trade disruption
    red_sea_trade_impact = scenario.red_sea_disruption_pct * 0.12  # 12% of global trade
    trade_disruption_pct = (scenario.hormuz_blockade_pct * 0.20 + red_sea_trade_impact) * 0.5

    gdp_impact: dict[str, np.ndarray] = {}
    sector_impacts: dict[str, dict[str, np.ndarray]] = {}
    trade_loss: dict[str, np.ndarray] = {}
    recovery_months: dict[str, float] = {}

    for country, profile in COUNTRY_PROFILES.items():
        # Base oil elasticity effect
        elasticity = profile.get("oil_price_elasticity", -0.01)
        base_gdp_impact_pct = elasticity * oil_shock_pct * 100.0

        # Iran: add sanctions amplifier
        if country == "Iran":
            base_gdp_impact_pct *= profile.get("sanctions_amplifier", 1.8)
            # Partially offset by China trade lifeline
            china_lifeline = profile.get("china_lifeline_factor", 0.55)
            base_gdp_impact_pct *= (1.0 - china_lifeline * 0.3)

        # Saudi Arabia: oil price rise is a revenue windfall initially
        if country == "Saudi_Arabia":
            fiscal_breakeven = profile.get("fiscal_breakeven_oil", 78.0)
            revenue_gain_pct = max(0.0, (oil_price_peak - fiscal_breakeven) / fiscal_breakeven * 0.4)
            base_gdp_impact_pct += revenue_gain_pct * 100.0 * 0.3  # War discount

        # Trade disruption component
        trade_weight = profile.get("trade_openness", 0.3)
        trade_gdp_impact = -trade_disruption_pct * trade_weight * 0.5 * 100.0

        total_base = base_gdp_impact_pct + trade_gdp_impact

        # Reserve currency / financial buffer
        buffer = profile.get("reserve_currency_buffer", 0.0) * 0.3
        total_base *= (1.0 - buffer)

        # Build time profile
        gdp_path = _time_profile(total_base, months, ramp_months=3, decay=True, half_life=18.0)
        gdp_impact[country] = gdp_path

        # Sector impacts
        sector_impacts[country] = compute_sector_propagation(
            country, oil_shock_pct * 100.0, trade_disruption_pct * 100.0, months
        )

        # Trade loss in $bn
        gdp_usd = profile.get("gdp_trillion", 1.0) * 1000  # in billions
        trade_loss[country] = np.abs(gdp_path) / 100.0 * gdp_usd * trade_weight

        # Recovery: months until GDP impact < 1%
        recovery_idx = np.where(np.abs(gdp_path) < 1.0)[0]
        recovery_months[country] = float(months[recovery_idx[0]]) if len(recovery_idx) > 0 else float(n_months)

    # Global GDP loss estimate
    global_gdp = sum(p["gdp_trillion"] for p in COUNTRY_PROFILES.values())
    global_gdp_loss = sum(
        gdp_impact[c][12] / 100.0 * COUNTRY_PROFILES[c]["gdp_trillion"]
        for c in COUNTRY_PROFILES
    ) / global_gdp

    # Recession probability (empirical: oil shocks >50% historically cause recessions 60% of time)
    recession_prob = min(0.95, max(0.0, oil_shock_pct * 0.8))

    return EconomicImpactResult(
        oil_price_path=oil_prices,
        months=months,
        gdp_impact=gdp_impact,
        sector_impacts=sector_impacts,
        trade_loss_billion=trade_loss,
        oil_price_peak=oil_price_peak,
        global_gdp_loss_pct=float(global_gdp_loss * 100.0),
        recession_probability=recession_prob,
        recovery_months=recovery_months,
    )


def build_gdp_impact_dataframe(result: EconomicImpactResult) -> pd.DataFrame:
    """Return wide-format DataFrame: months x countries, values = GDP impact %."""
    data = {"month": result.months}
    for country, impacts in result.gdp_impact.items():
        data[country] = impacts
    return pd.DataFrame(data).set_index("month")


def build_sector_impact_dataframe(result: EconomicImpactResult, country: str) -> pd.DataFrame:
    """Return sector impact DataFrame for a single country."""
    sectors = result.sector_impacts.get(country, {})
    data = {"month": result.months}
    data.update(sectors)
    return pd.DataFrame(data).set_index("month")


def print_economic_summary(result: EconomicImpactResult) -> None:
    print("\n[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]")
    print("=" * 65)
    print(f"ECONOMIC SHOCK PROPAGATION  |  Oil Peak: ${result.oil_price_peak:.0f}/bbl")
    print("=" * 65)
    print(f"  Global GDP Loss (12-month): {result.global_gdp_loss_pct:.2f}%")
    print(f"  Recession Probability: {result.recession_probability*100:.1f}%")
    print()
    print(f"  {'Country':<15} {'12mo GDP Δ%':>12} {'24mo GDP Δ%':>12} {'Recovery (mo)':>14}")
    print("  " + "-" * 55)
    for country in COUNTRY_PROFILES:
        imp = result.gdp_impact[country]
        m12 = imp[12] if len(imp) > 12 else imp[-1]
        m24 = imp[24] if len(imp) > 24 else imp[-1]
        rec = result.recovery_months.get(country, 36.0)
        print(f"  {country:<15} {m12:>+12.2f}% {m24:>+12.2f}% {rec:>14.1f}")
    print("=" * 65)
