"""
ARES Actor Capability Data Classes
[MODEL DATA - NOT PREDICTIVE INTELLIGENCE]

Palantir-style intelligence fusion layer modeling each actor
as a structured capability profile across military, economic,
and political dimensions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@dataclass
class AirAssets:
    fighter_attack: int = 0
    stealth_aircraft: int = 0
    bombers: int = 0
    tankers: int = 0
    isr_aircraft: int = 0
    uav_armed: int = 0

    @property
    def total_combat(self) -> int:
        return self.fighter_attack + self.stealth_aircraft + self.bombers + self.uav_armed

    @property
    def stealth_fraction(self) -> float:
        if self.total_combat == 0:
            return 0.0
        return self.stealth_aircraft / self.total_combat


@dataclass
class NavalAssets:
    aircraft_carriers: int = 0
    destroyers: int = 0
    frigates: int = 0
    corvettes: int = 0
    submarines_ssn: int = 0
    submarines_ssbn: int = 0
    submarines_conventional: int = 0
    fast_attack_craft: int = 0

    @property
    def blue_water_index(self) -> float:
        """Normalized 0-1 blue water capability"""
        score = (
            self.aircraft_carriers * 10
            + self.destroyers * 2.5
            + self.frigates * 1.5
            + self.submarines_ssn * 3
            + self.submarines_ssbn * 4
        )
        return min(1.0, score / 120.0)


@dataclass
class MilitaryProfile:
    force_size: int = 0
    active_personnel: int = 0
    reserve_personnel: int = 0
    air_assets: AirAssets = field(default_factory=AirAssets)
    naval_assets: NavalAssets = field(default_factory=NavalAssets)
    main_battle_tanks: int = 0
    missile_inventory: dict = field(default_factory=dict)
    nuclear_warheads: int = 0
    deployed_nuclear: int = 0
    cyber_capability_index: float = 0.0
    c4isr_index: float = 0.0
    power_projection_index: float = 0.0
    logistics_sustainability_months: float = 6.0
    attrition_rate: float = 0.02
    reinforcement_rate: float = 0.005

    @property
    def combat_power_index(self) -> float:
        """Composite combat power index, normalized 0-1"""
        air = self.air_assets.total_combat * 2.5
        naval = self.naval_assets.blue_water_index * 500
        ground = self.active_personnel * 0.001 + self.main_battle_tanks * 0.5
        cyber = self.cyber_capability_index * 200
        c4 = self.c4isr_index * 300
        raw = air + naval + ground + cyber + c4
        return min(1.0, raw / 5000.0)

    @property
    def air_superiority_coefficient(self) -> float:
        """
        Air superiority coefficient for Lanchester equations.
        Higher = better air capability multiplier on ground combat.
        """
        base = self.air_assets.total_combat / max(1, self.air_assets.total_combat + 100)
        stealth_bonus = self.air_assets.stealth_fraction * 0.3
        c4_bonus = self.c4isr_index * 0.2
        return min(1.0, base + stealth_bonus + c4_bonus)


@dataclass
class EconomicProfile:
    gdp_trillion_usd: float = 0.0
    gdp_growth_rate_pct: float = 2.0
    debt_to_gdp: float = 0.5
    forex_reserves_billion_usd: float = 0.0
    oil_production_mbpd: float = 0.0
    oil_consumption_mbpd: float = 0.0
    oil_import_dependency_pct: float = 0.0
    oil_revenue_gdp_pct: float = 0.0
    trade_with_china_billion_usd: float = 0.0
    sanctions_exposure_index: float = 0.0
    oil_price_gdp_elasticity: float = -0.01
    defense_spending_billion_usd: float = 0.0
    war_economy_mobilization_capacity: float = 0.3

    @property
    def economic_resilience_index(self) -> float:
        """0-1 index: ability to absorb economic shocks"""
        reserve_ratio = min(1.0, self.forex_reserves_billion_usd / (self.gdp_trillion_usd * 100))
        debt_penalty = max(0.0, 1.0 - self.debt_to_gdp)
        oil_penalty = 1.0 - self.oil_import_dependency_pct * 0.5
        sanctions_penalty = 1.0 - self.sanctions_exposure_index * 0.8
        return (reserve_ratio * 0.3 + debt_penalty * 0.2 + oil_penalty * 0.3 + sanctions_penalty * 0.2)

    def gdp_impact_from_oil_shock(self, oil_price_delta_pct: float) -> float:
        """Returns GDP impact % from oil price change %"""
        return self.oil_price_gdp_elasticity * oil_price_delta_pct


@dataclass
class PoliticalProfile:
    regime_stability_index: float = 0.7
    domestic_pressure: float = 0.3
    alliance_reliability: float = 0.7
    leadership_rationality_score: float = 0.8
    existential_threat_perception: float = 0.0
    us_extended_deterrence_credibility: float = 0.0
    nuclear_decision_authority_centralization: float = 0.5
    propaganda_info_warfare_capability: float = 0.5
    international_legitimacy_index: float = 0.7

    @property
    def escalation_propensity(self) -> float:
        """
        0-1: probability that actor escalates given opportunity.
        Driven by threat perception, domestic pressure, and inverse of rationality.
        """
        base = (
            self.existential_threat_perception * 0.45
            + self.domestic_pressure * 0.25
            + (1.0 - self.leadership_rationality_score) * 0.30
        )
        return min(1.0, max(0.0, base))

    @property
    def nuclear_threshold_proximity(self) -> float:
        """
        0-1: how close actor is to nuclear use threshold.
        Flags RED if > 0.15.
        """
        if self.existential_threat_perception < 0.3:
            return 0.0
        base = (
            self.existential_threat_perception * 0.60
            + (1.0 - self.regime_stability_index) * 0.25
            + (1.0 - self.us_extended_deterrence_credibility) * 0.15
        )
        return min(1.0, max(0.0, base))


@dataclass
class Actor:
    name: str
    military: MilitaryProfile = field(default_factory=MilitaryProfile)
    economic: EconomicProfile = field(default_factory=EconomicProfile)
    political: PoliticalProfile = field(default_factory=PoliticalProfile)

    def __repr__(self) -> str:
        return (
            f"Actor({self.name}: CPI={self.military.combat_power_index:.3f}, "
            f"GDP=${self.economic.gdp_trillion_usd:.2f}T, "
            f"Stability={self.political.regime_stability_index:.2f})"
        )

    @property
    def nuclear_flag(self) -> bool:
        return self.political.nuclear_threshold_proximity > 0.15

    def apply_attrition(self, attrition_fraction: float) -> None:
        """Apply force attrition from combat"""
        self.military.active_personnel = int(
            self.military.active_personnel * (1.0 - attrition_fraction)
        )
        self.military.air_assets.fighter_attack = int(
            self.military.air_assets.fighter_attack * (1.0 - attrition_fraction * 0.8)
        )
        self.military.main_battle_tanks = int(
            self.military.main_battle_tanks * (1.0 - attrition_fraction * 0.9)
        )

    def apply_economic_shock(self, gdp_impact_pct: float) -> None:
        """Apply economic damage"""
        self.economic.gdp_trillion_usd *= (1.0 + gdp_impact_pct / 100.0)
        self.economic.gdp_growth_rate_pct += gdp_impact_pct * 0.5

    def elevate_threat_perception(self, delta: float) -> None:
        """Increase existential threat perception"""
        self.political.existential_threat_perception = min(
            1.0, self.political.existential_threat_perception + delta
        )


def _build_air(data: dict) -> AirAssets:
    d = data.get("air_assets", {})
    return AirAssets(
        fighter_attack=d.get("fighter_attack", 0),
        stealth_aircraft=d.get("stealth_aircraft", 0),
        bombers=d.get("bombers", 0),
        tankers=d.get("tankers", 0),
        isr_aircraft=d.get("isr_aircraft", 0),
        uav_armed=d.get("uav_armed", 0),
    )


def _build_naval(data: dict) -> NavalAssets:
    d = data.get("naval_assets", {})
    return NavalAssets(
        aircraft_carriers=d.get("aircraft_carriers", 0),
        destroyers=d.get("destroyers", 0),
        frigates=d.get("frigates", 0),
        corvettes=d.get("corvettes", 0),
        submarines_ssn=d.get("submarines_ssn", 0),
        submarines_ssbn=d.get("submarines_ssbn", 0),
        submarines_conventional=d.get("submarines_conventional", 0),
        fast_attack_craft=d.get("fast_attack_craft", 0),
    )


def load_actors() -> dict[str, Actor]:
    """Load all actors from JSON data files."""
    mil_path = os.path.join(DATA_DIR, "military.json")
    eco_path = os.path.join(DATA_DIR, "economic.json")
    nuc_path = os.path.join(DATA_DIR, "nuclear.json")

    with open(mil_path) as f:
        mil_data = json.load(f)["actors"]
    with open(eco_path) as f:
        eco_data = json.load(f)["actors"]
    with open(nuc_path) as f:
        nuc_data = json.load(f)["doctrine_profiles"]

    actors: dict[str, Actor] = {}

    for name, md in mil_data.items():
        lf = md.get("land_forces", {})
        eco = eco_data.get(name, {})
        nuc = nuc_data.get(name, {})

        mil = MilitaryProfile(
            force_size=md.get("force_size", 0),
            active_personnel=md.get("active_personnel", md.get("force_size", 0)),
            reserve_personnel=md.get("reserve_personnel", 0),
            air_assets=_build_air(md),
            naval_assets=_build_naval(md),
            main_battle_tanks=lf.get("main_battle_tanks", 0),
            missile_inventory=md.get("missile_inventory", {}),
            nuclear_warheads=md.get("nuclear_warheads", 0),
            deployed_nuclear=md.get("deployed_nuclear", 0),
            cyber_capability_index=md.get("cyber_capability_index", 0.0),
            c4isr_index=md.get("c4isr_index", 0.5),
            power_projection_index=md.get("power_projection_index", 0.3),
            logistics_sustainability_months=md.get("logistics_sustainability_months", 3.0),
        )

        economic = EconomicProfile(
            gdp_trillion_usd=eco.get("gdp_trillion_usd", 0.0),
            gdp_growth_rate_pct=eco.get("gdp_growth_rate_pct", 2.0),
            debt_to_gdp=eco.get("debt_to_gdp", 0.5),
            forex_reserves_billion_usd=eco.get("forex_reserves_billion_usd", 0.0),
            oil_production_mbpd=eco.get("oil_production_mbpd", 0.0),
            oil_consumption_mbpd=eco.get("oil_consumption_mbpd", 0.0),
            oil_import_dependency_pct=eco.get("oil_import_dependency_pct", 0.0),
            oil_revenue_gdp_pct=eco.get("oil_revenue_gdp_pct", 0.0),
            trade_with_china_billion_usd=eco.get("trade_with_china_billion_usd", 0.0),
            sanctions_exposure_index=eco.get("sanctions_exposure_index", 0.0),
            oil_price_gdp_elasticity=eco.get("oil_price_gdp_elasticity", -0.01),
            defense_spending_billion_usd=eco.get("defense_spending_billion_usd", 0.0),
        )

        political = PoliticalProfile(
            regime_stability_index=md.get("regime_stability_index", 0.7),
            leadership_rationality_score=nuc.get("rationality_score", 0.75),
        )

        actors[name] = Actor(name=name, military=mil, economic=economic, political=political)

    return actors


# Default rationality scores per actor (calibrated from historical data)
RATIONALITY_SCORES = {
    "USA": 0.88,
    "Israel": 0.82,
    "Iran": 0.72,
    "Hezbollah": 0.60,
    "Houthis": 0.55,
    "Saudi_Arabia": 0.78,
    "China": 0.85,
    "Russia": 0.75,
    "EU": 0.90,
}

# Regime stability indices (0-1, higher = more stable)
REGIME_STABILITY = {
    "USA": 0.80,
    "Israel": 0.75,
    "Iran": 0.55,
    "Hezbollah": 0.65,
    "Houthis": 0.45,
    "Saudi_Arabia": 0.70,
    "China": 0.78,
    "Russia": 0.65,
    "EU": 0.82,
}
