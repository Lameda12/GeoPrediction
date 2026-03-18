"""
ARES Escalation Ladder & Deterrence Model
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Implements:
  1. Herman Kahn-inspired escalation ladder (44-rung adapted)
  2. Nash equilibrium deterrence model for rational actor behavior
  3. Nuclear threshold detection (RED flag > 15%)
  4. Game-theoretic payoff matrices for key decision nodes

References:
  - Kahn, H. (1965). On Escalation.
  - Powell, R. (1990). Nuclear Deterrence Theory.
  - Schelling, T. (1960). The Strategy of Conflict.
  - Fearon, J. (1995). Rationalist Explanations for War.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum


class EscalationRung(IntEnum):
    """
    Simplified 12-rung escalation ladder for the Iran conflict scenario.
    Derived from Kahn's 44-rung model, condensed for computational tractability.
    """
    OSTENSIBLE_CRISIS       = 1   # Political/diplomatic tensions
    POLITICAL_MILITARY      = 2   # Mil movements, alerts, sanctions tightening
    SOLEMN_DECLARATIONS     = 3   # Red lines declared publicly
    HARASSING_ACTS          = 4   # Cyber attacks, drone incursions, proxy probing
    SHOW_OF_FORCE           = 5   # Carrier group movements, exercise demonstrations
    SIGNIFICANT_MOBILIZATION = 6  # Partial mobilization, base activations
    LEGAL_HARASSMENT        = 7   # Sanctions, seizures, asset freezes
    DRAMATIC_MILITARY_MOVES = 8   # Airspace closures, naval blockade declarations
    CONVENTIONAL_STRIKES    = 9   # Air strikes on military facilities
    LARGE_CONVENTIONAL_WAR  = 10  # Ground forces, sustained air campaign
    LARGE_COMPOUND_ESCALATION = 11  # Multi-front war, proxy + direct
    NUCLEAR_SIGNALING       = 12  # Alert changes, tactical deployment, rhetoric


RUNG_LABELS = {rung: rung.name.replace("_", " ").title() for rung in EscalationRung}


@dataclass
class ActorProfile:
    name: str
    current_rung: int = 1
    existential_threat_perception: float = 0.0  # 0-1
    regime_stability_index: float = 0.7         # 0-1
    leadership_rationality_score: float = 0.8   # 0-1
    us_extended_deterrence_credibility: float = 0.0  # 0-1 (0 for non-allies)
    nuclear_warheads: int = 0
    nuclear_doctrine: str = "NFU"
    domestic_political_pressure: float = 0.3    # 0-1
    war_weariness: float = 0.0                  # 0-1, grows with conflict duration
    alliance_support_probability: float = 0.5


@dataclass
class PayoffMatrix:
    """
    2x2 Nash equilibrium payoff matrix for escalation decisions.
    Rows = Actor1 choices (Escalate/De-escalate)
    Cols = Actor2 choices (Escalate/De-escalate)
    Values = utility for Actor1, Actor2 (positive = preferred)
    """
    name: str
    # Format: [[EscEsc, EscDeesc], [DeescEsc, DeescDeesc]]
    actor1_payoffs: list[list[float]] = field(default_factory=list)
    actor2_payoffs: list[list[float]] = field(default_factory=list)
    actor1_name: str = "Actor1"
    actor2_name: str = "Actor2"

    def find_nash_equilibria(self) -> list[tuple[str, str]]:
        """
        Find pure strategy Nash equilibria.
        Returns list of (actor1_strategy, actor2_strategy) pairs.
        """
        strategies = ["Escalate", "De-escalate"]
        equilibria = []

        for i, s1 in enumerate(strategies):
            for j, s2 in enumerate(strategies):
                # Check if (i,j) is a Nash equilibrium
                a1_optimal = all(
                    self.actor1_payoffs[i][j] >= self.actor1_payoffs[k][j]
                    for k in range(2)
                )
                a2_optimal = all(
                    self.actor2_payoffs[i][j] >= self.actor2_payoffs[i][k]
                    for k in range(2)
                )
                if a1_optimal and a2_optimal:
                    equilibria.append((s1, s2))

        return equilibria

    def dominant_strategy(self, actor: int = 1) -> Optional[str]:
        """Find dominant strategy for actor (1 or 2), if it exists."""
        payoffs = self.actor1_payoffs if actor == 1 else self.actor2_payoffs
        strategies = ["Escalate", "De-escalate"]

        for i, s in enumerate(strategies):
            dominates = all(
                payoffs[i][j] > payoffs[1 - i][j]
                for j in range(2)
            )
            if dominates:
                return s
        return None


def build_crisis_payoff_matrix(
    actor1: ActorProfile,
    actor2: ActorProfile,
    stakes_multiplier: float = 1.0,
) -> PayoffMatrix:
    """
    Build context-sensitive payoff matrix from actor profiles.
    Based on Fearon's bargaining model with risk-return tradeoffs.

    Utility function:
    U_escalate = p * V - C
    U_deescalate = (1-p) * V + B_deesc (diplomatic gains)

    Where:
      p = probability of winning given escalation
      V = value of stakes (existential = very high)
      C = cost of war (function of capability ratio)
      B_deesc = benefit from de-escalation (face-saving, economic)
    """
    # Capability ratio estimation
    cap_ratio_1_vs_2 = (
        actor1.leadership_rationality_score * 2.0
        + (1.0 - actor2.existential_threat_perception)
    ) / 3.0

    # Probability actor1 "wins" an escalation exchange
    p1_wins = 0.3 + cap_ratio_1_vs_2 * 0.4

    # Stakes value (how much both actors value the disputed object)
    V1 = 0.5 + actor1.existential_threat_perception * 0.5
    V2 = 0.5 + actor2.existential_threat_perception * 0.5

    # Cost of escalation
    C1 = (1.0 - actor1.regime_stability_index) * 0.4 + 0.1
    C2 = (1.0 - actor2.regime_stability_index) * 0.4 + 0.1

    # Extended deterrence protection
    det1 = actor1.us_extended_deterrence_credibility * 0.3
    det2 = actor2.us_extended_deterrence_credibility * 0.3

    S = stakes_multiplier

    # Payoff matrix [Escalate, De-escalate] x [Escalate, De-escalate]
    # a1_payoff[i][j], a2_payoff[i][j]
    a1 = [
        # Actor2 Escalates:
        [S * (p1_wins * V1 - C1 + det1), S * (p1_wins * V1 * 1.2 - C1 * 0.5)],
        # Actor2 De-escalates:
        [S * (p1_wins * V1 * 0.4 - C1 * 0.2 + 0.1), S * 0.25],
    ]

    a2 = [
        # Actor1 Escalates:
        [S * ((1 - p1_wins) * V2 - C2 + det2), S * ((1 - p1_wins) * V2 * 0.4 - C2 * 0.2 + 0.1)],
        # Actor1 De-escalates:
        [S * ((1 - p1_wins) * V2 * 1.2 - C2 * 0.5), S * 0.25],
    ]

    return PayoffMatrix(
        name=f"{actor1.name} vs {actor2.name}",
        actor1_payoffs=a1,
        actor2_payoffs=a2,
        actor1_name=actor1.name,
        actor2_name=actor2.name,
    )


@dataclass
class EscalationState:
    """Current state of the escalation ladder simulation."""
    day: float = 0.0
    current_rung: int = 1
    actors: dict[str, ActorProfile] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    nuclear_flags: list[str] = field(default_factory=list)  # actors at nuclear threshold
    de_escalation_active: bool = False

    def record(self) -> None:
        self.history.append({
            "day": self.day,
            "rung": self.current_rung,
            "nuclear_flags": list(self.nuclear_flags),
            "actor_threat_perceptions": {
                name: actor.existential_threat_perception
                for name, actor in self.actors.items()
            },
        })


def compute_nuclear_threshold(
    actor: ActorProfile,
    nuclear_taboo_strength: float = 0.78,
    war_day: float = 0.0,
) -> float:
    """
    Compute probability that actor crosses nuclear use threshold.

    P(nuclear) = f(existential_threat, rationality, deterrence, taboo)

    Flags RED if P > 0.15 per ARES red-line convention.

    Args:
        actor: Actor profile
        nuclear_taboo_strength: Baseline strength of nuclear non-use norm (0-1)
        war_day: Day of conflict (taboo erodes slightly with war duration)

    Returns:
        Probability of nuclear threshold crossing (0-1)
    """
    if actor.nuclear_warheads == 0:
        # Non-nuclear state: cannot cross threshold unless has breakout
        # Iran case: model as acquisition rush risk
        if actor.name == "Iran":
            return min(0.08, actor.existential_threat_perception * 0.12)
        return 0.0

    # Taboo erosion with war duration
    taboo_erosion = min(0.20, war_day * 0.001)
    effective_taboo = max(0.0, nuclear_taboo_strength - taboo_erosion)

    # Base probability from existential threat
    threat_component = actor.existential_threat_perception ** 1.5

    # Rationality suppression
    rationality_suppression = actor.leadership_rationality_score * 0.6

    # Extended deterrence suppression
    deterrence_suppression = actor.us_extended_deterrence_credibility * 0.4

    # War weariness can increase desperation
    desperation = actor.war_weariness * 0.15

    raw_prob = (
        threat_component * 0.50
        + actor.domestic_political_pressure * 0.15
        + desperation
        - rationality_suppression
        - deterrence_suppression
        - effective_taboo * 0.35
    )

    return min(1.0, max(0.0, raw_prob))


def simulate_escalation_ladder(
    initial_rung: int = 9,
    actors: dict[str, ActorProfile] | None = None,
    n_days: int = 90,
    dt: float = 1.0,
    rng_seed: int | None = None,
) -> EscalationState:
    """
    Simulate escalation ladder progression over time.
    Returns time-series of escalation state.

    Uses stochastic state transitions informed by actor profiles
    and Nash equilibrium analysis at each decision node.
    """
    if actors is None:
        actors = _default_usa_iran_actors()

    rng = np.random.default_rng(rng_seed)
    state = EscalationState(current_rung=initial_rung, actors=actors)
    state.record()

    for day_i in range(int(n_days / dt)):
        t = day_i * dt
        state.day = t

        # ── Nuclear threshold check ──────────────────────────────────────
        new_flags = []
        for name, actor in actors.items():
            p_nuc = compute_nuclear_threshold(actor, war_day=t)
            if p_nuc > 0.15:
                new_flags.append(name)
                actor.existential_threat_perception = min(
                    1.0, actor.existential_threat_perception + 0.02
                )
        state.nuclear_flags = new_flags

        # ── Nash equilibrium at current rung ─────────────────────────────
        # Simplified: check USA vs Iran escalation decision
        usa = actors.get("USA", actors.get("Coalition"))
        iran = actors.get("Iran")

        if usa and iran:
            matrix = build_crisis_payoff_matrix(usa, iran, stakes_multiplier=1.0 + t / 90.0)
            equilibria = matrix.find_nash_equilibria()

            # Probabilistic rung transition based on Nash outcome
            if ("Escalate", "Escalate") in equilibria:
                p_escalate = 0.45 + usa.existential_threat_perception * 0.2
            elif ("De-escalate", "De-escalate") in equilibria:
                p_escalate = 0.15 - iran.regime_stability_index * 0.1
            else:
                p_escalate = 0.28

            # War weariness reduces escalation propensity over time
            p_escalate *= max(0.3, 1.0 - t / (n_days * 1.5))

            # Stochastic rung transition
            if rng.random() < p_escalate and state.current_rung < 12:
                state.current_rung = min(12, state.current_rung + 1)
                # Increase threat perceptions
                for actor in actors.values():
                    actor.existential_threat_perception = min(
                        1.0,
                        actor.existential_threat_perception + rng.uniform(0.02, 0.06)
                    )
                    actor.war_weariness = min(1.0, actor.war_weariness + 0.01)
            elif rng.random() < 0.12 and state.current_rung > 1:
                state.current_rung = max(1, state.current_rung - 1)
                state.de_escalation_active = True

        state.record()

    return state


def _default_usa_iran_actors() -> dict[str, ActorProfile]:
    """Default actor profiles for the USA/Israel vs Iran scenario."""
    return {
        "USA": ActorProfile(
            name="USA",
            current_rung=9,
            existential_threat_perception=0.10,
            regime_stability_index=0.80,
            leadership_rationality_score=0.88,
            us_extended_deterrence_credibility=1.0,
            nuclear_warheads=5550,
            nuclear_doctrine="Flexible_Response",
            domestic_political_pressure=0.45,
        ),
        "Israel": ActorProfile(
            name="Israel",
            current_rung=9,
            existential_threat_perception=0.55,
            regime_stability_index=0.72,
            leadership_rationality_score=0.82,
            us_extended_deterrence_credibility=0.88,
            nuclear_warheads=90,
            nuclear_doctrine="Opacity",
            domestic_political_pressure=0.60,
        ),
        "Iran": ActorProfile(
            name="Iran",
            current_rung=9,
            existential_threat_perception=0.75,
            regime_stability_index=0.55,
            leadership_rationality_score=0.72,
            us_extended_deterrence_credibility=0.0,
            nuclear_warheads=0,
            nuclear_doctrine="Non_Nuclear_Weapons_State",
            domestic_political_pressure=0.65,
        ),
        "Hezbollah": ActorProfile(
            name="Hezbollah",
            current_rung=8,
            existential_threat_perception=0.60,
            regime_stability_index=0.65,
            leadership_rationality_score=0.60,
            nuclear_warheads=0,
            domestic_political_pressure=0.50,
        ),
    }


def format_escalation_report(state: EscalationState) -> str:
    """Format escalation state as a readable report."""
    lines = [
        "[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]",
        "=" * 60,
        f"ESCALATION LADDER ANALYSIS  |  {len(state.history)} time steps",
        "=" * 60,
        f"  Peak Rung Reached: {max(h['rung'] for h in state.history)} / 12",
        f"  Final Rung: {state.current_rung}",
        f"  Nuclear Flags Active: {', '.join(state.nuclear_flags) or 'NONE'}",
        f"  De-escalation Triggered: {state.de_escalation_active}",
        "",
        "ACTOR THREAT PERCEPTIONS (final):",
    ]
    for name, actor in state.actors.items():
        p_nuc = compute_nuclear_threshold(actor, war_day=state.day)
        flag = " [*** RED FLAG ***]" if p_nuc > 0.15 else ""
        lines.append(
            f"  {name:<15} Threat={actor.existential_threat_perception:.2f}  "
            f"Stability={actor.regime_stability_index:.2f}  "
            f"P(Nuclear)={p_nuc:.3f}{flag}"
        )
    lines.append("=" * 60)
    return "\n".join(lines)
