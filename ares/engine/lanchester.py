"""
ARES Lanchester Combat Equations
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Implements both:
  - Lanchester Square Law (modern conventional warfare)
    dX/dt = -beta * Y
    dY/dt = -alpha * X
    Valid when forces can target any enemy unit (ranged/fire superiority).

  - Lanchester Linear Law (guerrilla / attrition warfare)
    dX/dt = -beta * X * Y / X0
    dY/dt = -alpha * Y * X / Y0
    Valid when contact rate is proportional to both sides' densities.

Reference: Lanchester (1916), Taylor (1983), Helmbold (1993).
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Literal
from scipy.integrate import solve_ivp


@dataclass
class ForceState:
    name: str
    force_size: float
    attrition_rate: float       # alpha/beta: fractional loss rate per unit time per opposing unit
    reinforcement_rate: float   # troops/day added
    air_superiority_coeff: float = 1.0  # multiplier on effective attrition dealt
    tech_advantage: float = 1.0         # quality multiplier (precision, C4ISR)
    supply_days_remaining: float = 90.0

    @property
    def effective_combat_power(self) -> float:
        return (
            self.force_size
            * self.air_superiority_coeff
            * self.tech_advantage
        )


@dataclass
class CombatResult:
    time_days: np.ndarray
    force_x: np.ndarray
    force_y: np.ndarray
    name_x: str
    name_y: str
    law: str
    winner: str
    time_to_depletion_x: float | None
    time_to_depletion_y: float | None
    crossover_day: float | None

    def summary(self) -> dict:
        return {
            "law": self.law,
            "winner": self.winner,
            "time_to_depletion_x_days": self.time_to_depletion_x,
            "time_to_depletion_y_days": self.time_to_depletion_y,
            "crossover_day": self.crossover_day,
            "final_force_x": float(self.force_x[-1]),
            "final_force_y": float(self.force_y[-1]),
            "x_survival_pct": float(self.force_x[-1] / self.force_x[0] * 100),
            "y_survival_pct": float(self.force_y[-1] / self.force_y[0] * 100),
        }


def _find_depletion(t: np.ndarray, force: np.ndarray, threshold_pct: float = 0.10) -> float | None:
    """Return time at which force drops below threshold_pct of initial."""
    threshold = force[0] * threshold_pct
    idx = np.where(force <= threshold)[0]
    if len(idx) == 0:
        return None
    return float(t[idx[0]])


def _find_crossover(t: np.ndarray, fx: np.ndarray, fy: np.ndarray) -> float | None:
    """Return day X overtakes Y in attrition advantage (X > Y transitions)."""
    diff = fx - fy
    sign_changes = np.where(np.diff(np.sign(diff)))[0]
    if len(sign_changes) == 0:
        return None
    return float(t[sign_changes[0]])


def lanchester_square_law(
    force_x: ForceState,
    force_y: ForceState,
    t_max_days: float = 90.0,
    dt: float = 0.5,
) -> CombatResult:
    """
    Lanchester Square Law ODE integration.

    dX/dt = -beta * Y + r_x
    dY/dt = -alpha * X + r_y

    where alpha/beta are EFFECTIVE attrition rates incorporating
    technology, air superiority, and supply.
    """
    alpha = force_x.attrition_rate * force_x.air_superiority_coeff * force_x.tech_advantage
    beta  = force_y.attrition_rate * force_y.air_superiority_coeff * force_y.tech_advantage

    X0 = force_x.force_size
    Y0 = force_y.force_size

    def supply_factor(t: float, state_x: float, state_y: float) -> tuple[float, float]:
        """Reduce effectiveness when supplies exhausted."""
        sx = max(0.1, 1.0 - max(0.0, t - force_x.supply_days_remaining) / 30.0)
        sy = max(0.1, 1.0 - max(0.0, t - force_y.supply_days_remaining) / 30.0)
        return sx, sy

    def odes(t: float, y: list[float]) -> list[float]:
        X, Y = y
        X = max(0.0, X)
        Y = max(0.0, Y)
        sx, sy = supply_factor(t, X, Y)
        dX = -beta * Y * sx + force_x.reinforcement_rate * (1.0 if X > 0 else 0.0)
        dY = -alpha * X * sy + force_y.reinforcement_rate * (1.0 if Y > 0 else 0.0)
        dX = max(-X, dX)
        dY = max(-Y, dY)
        return [dX, dY]

    t_eval = np.arange(0, t_max_days + dt, dt)
    sol = solve_ivp(
        odes,
        [0, t_max_days],
        [X0, Y0],
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-8,
    )

    fx = np.maximum(0.0, sol.y[0])
    fy = np.maximum(0.0, sol.y[1])
    t  = sol.t

    dep_x = _find_depletion(t, fx)
    dep_y = _find_depletion(t, fy)
    cross = _find_crossover(t, fx, fy)

    if dep_x is None and dep_y is None:
        if fx[-1] > fy[-1]:
            winner = force_x.name
        else:
            winner = force_y.name
    elif dep_x is None:
        winner = force_x.name
    elif dep_y is None:
        winner = force_y.name
    else:
        winner = force_x.name if dep_x > dep_y else force_y.name

    return CombatResult(
        time_days=t,
        force_x=fx,
        force_y=fy,
        name_x=force_x.name,
        name_y=force_y.name,
        law="Square",
        winner=winner,
        time_to_depletion_x=dep_x,
        time_to_depletion_y=dep_y,
        crossover_day=cross,
    )


def lanchester_linear_law(
    force_x: ForceState,
    force_y: ForceState,
    t_max_days: float = 90.0,
    dt: float = 0.5,
) -> CombatResult:
    """
    Lanchester Linear Law (guerrilla attrition) ODE integration.

    dX/dt = -beta * (X/X0) * Y  =>  contact-rate proportional to density
    dY/dt = -alpha * (Y/Y0) * X

    Used for: insurgency, guerrilla, proxy warfare, urban combat.
    """
    alpha = force_x.attrition_rate * force_x.air_superiority_coeff * force_x.tech_advantage
    beta  = force_y.attrition_rate * force_y.air_superiority_coeff * force_y.tech_advantage
    X0 = force_x.force_size
    Y0 = force_y.force_size

    def odes(t: float, y: list[float]) -> list[float]:
        X, Y = y
        X = max(1.0, X)
        Y = max(1.0, Y)
        sx = max(0.1, 1.0 - max(0.0, t - force_x.supply_days_remaining) / 30.0)
        sy = max(0.1, 1.0 - max(0.0, t - force_y.supply_days_remaining) / 30.0)
        dX = -beta * (X / X0) * Y * sx + force_x.reinforcement_rate
        dY = -alpha * (Y / Y0) * X * sy + force_y.reinforcement_rate
        dX = max(-X + 1, dX)
        dY = max(-Y + 1, dY)
        return [dX, dY]

    t_eval = np.arange(0, t_max_days + dt, dt)
    sol = solve_ivp(
        odes,
        [0, t_max_days],
        [X0, Y0],
        t_eval=t_eval,
        method="RK45",
        rtol=1e-6,
        atol=1e-8,
    )

    fx = np.maximum(0.0, sol.y[0])
    fy = np.maximum(0.0, sol.y[1])
    t  = sol.t

    dep_x = _find_depletion(t, fx)
    dep_y = _find_depletion(t, fy)
    cross = _find_crossover(t, fx, fy)

    if dep_x is None and dep_y is None:
        winner = force_x.name if fx[-1] > fy[-1] else force_y.name
    elif dep_x is None:
        winner = force_x.name
    elif dep_y is None:
        winner = force_y.name
    else:
        winner = force_x.name if dep_x > dep_y else force_y.name

    return CombatResult(
        time_days=t,
        force_x=fx,
        force_y=fy,
        name_x=force_x.name,
        name_y=force_y.name,
        law="Linear",
        winner=winner,
        time_to_depletion_x=dep_x,
        time_to_depletion_y=dep_y,
        crossover_day=cross,
    )


def run_dual_law_comparison(
    force_x: ForceState,
    force_y: ForceState,
    t_max_days: float = 90.0,
) -> dict[str, CombatResult]:
    """Run both Square and Linear law models and return results dict."""
    return {
        "square": lanchester_square_law(force_x, force_y, t_max_days),
        "linear": lanchester_linear_law(force_x, force_y, t_max_days),
    }


def build_force_from_actor(actor_data: dict, name: str) -> ForceState:
    """Convenience builder from actor dict."""
    mil = actor_data.get("military", {})
    return ForceState(
        name=name,
        force_size=float(mil.get("active_personnel", 50000)),
        attrition_rate=float(mil.get("attrition_rate", 0.015)),
        reinforcement_rate=float(mil.get("reinforcement_rate", 200.0)),
        air_superiority_coeff=float(mil.get("air_superiority_coeff", 0.5)),
        tech_advantage=float(mil.get("c4isr_index", 0.5)),
        supply_days_remaining=float(mil.get("logistics_sustainability_months", 3)) * 30,
    )


def scenario_usa_israel_vs_iran() -> dict[str, CombatResult]:
    """
    Pre-configured scenario: US/Israel coalition vs Iran
    Uses IISS-calibrated parameters.

    Returns results for both combat law models across three theaters.
    """
    # Theater 1: Air campaign (strike packages - modeled as airframe attrition)
    coalition_air = ForceState(
        name="US_Israel_Coalition_Air",
        force_size=2425.0,          # US+Israel combat aircraft
        attrition_rate=0.008,       # Iran air defense effectiveness
        reinforcement_rate=5.0,     # Surge deployments per day
        air_superiority_coeff=0.95,
        tech_advantage=0.97,
        supply_days_remaining=180.0,
    )
    iran_air_defense = ForceState(
        name="Iran_Air_Defense",
        force_size=800.0,           # Effective SAM/intercept units
        attrition_rate=0.025,       # Coalition precision strike effectiveness
        reinforcement_rate=2.0,
        air_superiority_coeff=0.35,
        tech_advantage=0.55,
        supply_days_remaining=30.0,
    )

    # Theater 2: Missile exchange (salvo model approximated via Square Law)
    coalition_missile = ForceState(
        name="Coalition_Missile_Defense",
        force_size=4200.0,          # Patriot/Arrow/Iron Dome intercept capacity
        attrition_rate=0.012,
        reinforcement_rate=10.0,
        air_superiority_coeff=0.90,
        tech_advantage=0.95,
        supply_days_remaining=60.0,
    )
    iran_missile_force = ForceState(
        name="Iran_Ballistic_Missiles",
        force_size=3000.0,
        attrition_rate=0.018,
        reinforcement_rate=20.0,
        air_superiority_coeff=0.60,
        tech_advantage=0.65,
        supply_days_remaining=45.0,
    )

    # Theater 3: Proxy/guerrilla (Hezbollah + Houthis - Linear Law)
    proxy_forces = ForceState(
        name="Iran_Proxy_Network",
        force_size=330000.0,        # Hezbollah + Houthi + Iraqi militia
        attrition_rate=0.003,
        reinforcement_rate=500.0,
        air_superiority_coeff=0.15,
        tech_advantage=0.28,
        supply_days_remaining=60.0,
    )
    us_israel_counter = ForceState(
        name="US_Israel_Counter_Proxy",
        force_size=250000.0,
        attrition_rate=0.005,
        reinforcement_rate=300.0,
        air_superiority_coeff=0.75,
        tech_advantage=0.88,
        supply_days_remaining=90.0,
    )

    return {
        "air_campaign": run_dual_law_comparison(coalition_air, iran_air_defense, 90),
        "missile_exchange": run_dual_law_comparison(coalition_missile, iran_missile_force, 30),
        "proxy_warfare": run_dual_law_comparison(us_israel_counter, proxy_forces, 180),
    }
