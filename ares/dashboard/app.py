"""
ARES Streamlit Dashboard
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Dark terminal aesthetic with amber/red accents.
"""

from __future__ import annotations

import sys
import os

# Ensure engine is importable when run from dashboard/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from engine.montecarlo import (
    ScenarioParameters, run_monte_carlo, OUTCOME_LABELS, OUTCOME_COLORS
)
from engine.lanchester import (
    ForceState, lanchester_square_law, lanchester_linear_law,
    scenario_usa_israel_vs_iran,
)
from engine.escalation import (
    simulate_escalation_ladder, _default_usa_iran_actors,
    compute_nuclear_threshold, EscalationRung, RUNG_LABELS,
)
from engine.economic import (
    OilShockScenario, run_economic_simulation,
    build_gdp_impact_dataframe, COUNTRY_PROFILES,
)

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ARES – Adaptive Risk and Escalation Simulator",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS (terminal aesthetic) ─────────────────────────────────────────

st.markdown("""
<style>
  /* Background & typography */
  .stApp { background-color: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace; }
  .stSidebar { background-color: #111111; border-right: 1px solid #333; }
  h1, h2, h3 { color: #ff6b35; font-family: 'Courier New', monospace; letter-spacing: 2px; }
  .stMarkdown p { color: #c0c0c0; }
  /* Sliders */
  .stSlider > div > div { background-color: #1a1a1a; }
  /* Tabs */
  .stTabs [data-baseweb="tab"] { color: #888; background-color: #111; border: 1px solid #333; }
  .stTabs [aria-selected="true"] { color: #ff6b35 !important; border-bottom: 2px solid #ff6b35 !important; }
  /* Metric labels */
  [data-testid="stMetricLabel"] { color: #ff6b35; font-size: 0.7rem; letter-spacing: 1px; }
  [data-testid="stMetricValue"] { color: #ffffff; }
  /* Warning box */
  .warning-box {
    background-color: #1a0000;
    border: 2px solid #ff0000;
    padding: 10px 16px;
    border-radius: 4px;
    color: #ff4444;
    font-family: monospace;
    font-size: 0.85rem;
    margin: 8px 0;
  }
  .info-box {
    background-color: #001a0d;
    border: 1px solid #00ff88;
    padding: 8px 14px;
    border-radius: 4px;
    color: #00cc66;
    font-family: monospace;
    font-size: 0.8rem;
  }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown("""
# ⚠ ARES — ADAPTIVE RISK AND ESCALATION SIMULATOR
### Scenario: USA + Israel vs Iran  |  Research Grade Mathematical Modeling Tool
""")

st.markdown(
    '<div class="warning-box">⚠ MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE. '
    'All data from open-source public research. For academic/research use only. '
    'ARES v1.0</div>',
    unsafe_allow_html=True,
)

# ─── Sidebar controls ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## SCENARIO PARAMETERS")
    st.markdown("---")

    st.markdown("### ⚔ Strike Parameters")
    strike_intensity = st.slider(
        "Strike Intensity", 0.0, 1.0, 0.75, 0.05,
        help="0=Limited (1 site), 1.0=Full campaign (Fordow+Natanz+Arak)"
    )
    usa_direct_entry = st.slider(
        "US Direct Entry Prob", 0.0, 1.0, 0.55, 0.05,
        help="P(USA escalates from ISR support to direct strikes)"
    )

    st.markdown("### 🛡 Proxy & Alliance")
    hezbollah_prob = st.slider("Hezbollah Activation Prob", 0.0, 1.0, 0.85, 0.05)
    houthi_prob    = st.slider("Houthi Escalation Prob",    0.0, 1.0, 0.78, 0.05)

    st.markdown("### 🛢 Oil & Economic")
    hormuz_blockade_prob = st.slider(
        "Hormuz Blockade Prob", 0.0, 1.0, 0.45, 0.05,
        help="P(Iran attempts Strait of Hormuz interdiction)"
    )
    hormuz_blockade_pct = st.slider(
        "Hormuz Disruption %", 0.0, 1.0, 0.45, 0.05,
        help="Fraction of Strait flow disrupted if blockade attempted"
    )
    red_sea_disruption = st.slider("Red Sea Disruption %", 0.0, 0.5, 0.20, 0.05)

    st.markdown("### 🕊 Diplomacy")
    ceasefire_prob    = st.slider("Ceasefire Prob (30d)",   0.0, 0.8, 0.35, 0.05)
    us_deterrence     = st.slider("US Deterrence Credibility", 0.0, 1.0, 0.78, 0.05)

    st.markdown("### ⚙ Simulation")
    n_runs = st.selectbox("Monte Carlo Runs", [1000, 5000, 10000], index=1)
    random_seed = st.number_input("Random Seed", value=42, step=1)
    run_btn = st.button("▶ RUN SIMULATION", type="primary", use_container_width=True)

# ─── Session state for caching results ────────────────────────────────────────

if "results" not in st.session_state:
    st.session_state.results = None

if run_btn or st.session_state.results is None:
    with st.spinner("Running Monte Carlo simulation..."):
        params = ScenarioParameters(
            strike_intensity=strike_intensity,
            iran_retaliation_prob=0.92,
            hezbollah_activation_prob=hezbollah_prob,
            houthi_escalation_prob=houthi_prob,
            us_direct_entry_prob=usa_direct_entry,
            iran_hormuz_blockade_prob=hormuz_blockade_prob,
            ceasefire_negotiation_prob=ceasefire_prob,
            us_deterrence_credibility=us_deterrence,
            oil_disruption_pct=hormuz_blockade_pct,
            n_simulations=int(n_runs),
            random_seed=int(random_seed),
        )
        mc_result = run_monte_carlo(params)

    with st.spinner("Running Lanchester combat models..."):
        lanchester_results = scenario_usa_israel_vs_iran()

    with st.spinner("Running economic model..."):
        oil_scenario = OilShockScenario(
            hormuz_blockade_pct=hormuz_blockade_pct,
            red_sea_disruption_pct=red_sea_disruption,
            iran_oil_offline_mbpd=1.5,
        )
        eco_result = run_economic_simulation(oil_scenario, n_months=36)

    with st.spinner("Simulating escalation ladder..."):
        actors = _default_usa_iran_actors()
        # Update actors based on slider values
        actors["USA"].existential_threat_perception = 0.10 + strike_intensity * 0.15
        actors["Iran"].existential_threat_perception = 0.50 + strike_intensity * 0.35
        actors["Israel"].existential_threat_perception = 0.40 + strike_intensity * 0.20
        esc_state = simulate_escalation_ladder(
            initial_rung=9, actors=actors, n_days=90, rng_seed=int(random_seed)
        )

    st.session_state.results = {
        "mc": mc_result,
        "lanchester": lanchester_results,
        "eco": eco_result,
        "esc": esc_state,
    }

r = st.session_state.results
mc  = r["mc"]
lan = r["lanchester"]
eco = r["eco"]
esc = r["esc"]

# ─── Nuclear flag alert ──────────────────────────────────────────────────────

if mc.nuclear_probability > 0.15:
    st.markdown(
        f'<div class="warning-box">🔴 RED FLAG: Nuclear threshold crossing probability = '
        f'{mc.nuclear_probability*100:.1f}% [95% CI: '
        f'{mc.nuclear_ci[0]*100:.1f}–{mc.nuclear_ci[1]*100:.1f}%]  '
        f'— Exceeds 15% RED LINE threshold</div>',
        unsafe_allow_html=True,
    )

# ─── Top metrics row ─────────────────────────────────────────────────────────

col1, col2, col3, col4, col5 = st.columns(5)
most_probable = max(mc.outcome_probabilities, key=mc.outcome_probabilities.get)
with col1:
    st.metric("Most Probable Outcome", f"State {most_probable}", OUTCOME_LABELS[most_probable][:25])
with col2:
    st.metric("P(Most Probable)", f"{mc.outcome_probabilities[most_probable]*100:.1f}%")
with col3:
    st.metric("Nuclear Risk", f"{mc.nuclear_probability*100:.1f}%",
              "🔴 RED FLAG" if mc.nuclear_probability > 0.15 else "✅ Below threshold")
with col4:
    st.metric("Oil Price Peak", f"${eco.oil_price_peak:.0f}/bbl",
              f"{(eco.oil_price_peak/82-1)*100:+.0f}% vs baseline")
with col5:
    st.metric("Global Recession Risk", f"{eco.recession_probability*100:.0f}%")

st.markdown("---")

# ─── Tabs ────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Outcome Probabilities",
    "⚔ Force Attrition",
    "💰 Economic Impact",
    "🪜 Escalation Ladder",
    "📋 Raw Data & Export",
])

# ── TAB 1: Monte Carlo Outcome Probabilities ──────────────────────────────────

with tab1:
    st.markdown("### MONTE CARLO OUTCOME DISTRIBUTION")
    st.markdown(f"*N = {mc.n_simulations:,} simulations — 95% Wilson score confidence intervals*")

    probs  = mc.outcome_probabilities
    cis    = mc.confidence_intervals
    labels = [f"[{k}] {v[:35]}" for k, v in OUTCOME_LABELS.items()]
    values = [probs.get(k, 0.0) * 100 for k in OUTCOME_LABELS]
    ci_lo  = [(probs.get(k, 0.0) - cis.get(k, (0, 0))[0]) * 100 for k in OUTCOME_LABELS]
    ci_hi  = [(cis.get(k, (0, 0))[1] - probs.get(k, 0.0)) * 100 for k in OUTCOME_LABELS]

    bar_colors = [OUTCOME_COLORS.get(k, "#888") for k in OUTCOME_LABELS]

    fig_mc = go.Figure()
    fig_mc.add_trace(go.Bar(
        x=labels,
        y=values,
        error_y=dict(type="data", symmetric=False, array=ci_hi, arrayminus=ci_lo, color="#ff6b35"),
        marker_color=bar_colors,
        marker_line_color="#333",
        marker_line_width=1,
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
        textfont=dict(color="#e0e0e0", family="Courier New"),
    ))
    fig_mc.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
        font=dict(family="Courier New", color="#e0e0e0"),
        xaxis=dict(tickfont=dict(size=9), gridcolor="#222"),
        yaxis=dict(title="Probability (%)", gridcolor="#333"),
        title=dict(text="Outcome Probability Distribution with 95% CI", font=dict(color="#ff6b35")),
        margin=dict(t=60, b=120),
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    # Nuclear probability gauge
    col_a, col_b = st.columns(2)
    with col_a:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=mc.nuclear_probability * 100,
            title={"text": "Nuclear Threshold Probability (%)", "font": {"color": "#ff6b35", "family": "Courier New"}},
            gauge={
                "axis": {"range": [0, 50], "tickcolor": "#666"},
                "bar": {"color": "#ff0000" if mc.nuclear_probability > 0.15 else "#ff6b35"},
                "bgcolor": "#111",
                "bordercolor": "#333",
                "steps": [
                    {"range": [0, 15], "color": "#002200"},
                    {"range": [15, 30], "color": "#221100"},
                    {"range": [30, 50], "color": "#220000"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 3},
                    "thickness": 0.75,
                    "value": 15,
                },
            },
            number={"suffix": "%", "font": {"color": "#ff6b35"}},
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#0a0a0a",
            font=dict(family="Courier New", color="#e0e0e0"),
            height=280,
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_b:
        # Outcome probability pie
        fig_pie = go.Figure(go.Pie(
            labels=[f"S{k}" for k in OUTCOME_LABELS],
            values=list(values),
            marker=dict(colors=bar_colors, line=dict(color="#000", width=1)),
            textinfo="label+percent",
            textfont=dict(family="Courier New", size=10),
            hole=0.3,
        ))
        fig_pie.update_layout(
            paper_bgcolor="#0a0a0a",
            font=dict(family="Courier New", color="#e0e0e0"),
            title=dict(text="Outcome Distribution", font=dict(color="#ff6b35")),
            height=280,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# ── TAB 2: Force Attrition Curves ────────────────────────────────────────────

with tab2:
    st.markdown("### LANCHESTER FORCE ATTRITION CURVES")
    st.markdown(
        "*Square Law = modern conventional warfare. "
        "Linear Law = guerrilla/proxy/attrition warfare.*"
    )

    theater = st.selectbox(
        "Select Theater",
        ["Air Campaign (Square Law)", "Missile Exchange (Square Law)", "Proxy Warfare (Linear Law)"],
    )

    if theater == "Air Campaign (Square Law)":
        result = lan["air_campaign"]["square"]
        subtitle = "Coalition Air vs Iran Air Defense — Square Law"
    elif theater == "Missile Exchange (Square Law)":
        result = lan["missile_exchange"]["square"]
        subtitle = "Coalition Missile Defense vs Iran Ballistic Missiles — Square Law"
    else:
        result = lan["proxy_warfare"]["linear"]
        subtitle = "US/Israel Counter-Proxy vs Iran Proxy Network — Linear Law"

    fig_lan = go.Figure()
    pct_x = result.force_x / result.force_x[0] * 100
    pct_y = result.force_y / result.force_y[0] * 100

    fig_lan.add_trace(go.Scatter(
        x=result.time_days, y=pct_x,
        name=result.name_x,
        line=dict(color="#3498db", width=2.5),
        fill="tozeroy", fillcolor="rgba(52,152,219,0.08)",
    ))
    fig_lan.add_trace(go.Scatter(
        x=result.time_days, y=pct_y,
        name=result.name_y,
        line=dict(color="#e74c3c", width=2.5),
        fill="tozeroy", fillcolor="rgba(231,76,60,0.08)",
    ))

    # Depletion markers
    for dep, name, color in [
        (result.time_to_depletion_x, result.name_x, "#3498db"),
        (result.time_to_depletion_y, result.name_y, "#e74c3c"),
    ]:
        if dep is not None:
            fig_lan.add_vline(x=dep, line_dash="dash", line_color=color, opacity=0.6,
                              annotation_text=f"{name} depleted", annotation_font_color=color)

    fig_lan.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
        font=dict(family="Courier New", color="#e0e0e0"),
        title=dict(text=subtitle, font=dict(color="#ff6b35")),
        xaxis=dict(title="Day", gridcolor="#222"),
        yaxis=dict(title="Force Remaining (%)", gridcolor="#333", range=[0, 110]),
        legend=dict(bgcolor="#111", bordercolor="#333"),
    )
    st.plotly_chart(fig_lan, use_container_width=True)

    # Summary metrics
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Winner", result.winner)
    with colB:
        depx = f"Day {result.time_to_depletion_x:.0f}" if result.time_to_depletion_x else "Survives"
        depy = f"Day {result.time_to_depletion_y:.0f}" if result.time_to_depletion_y else "Survives"
        st.metric(f"{result.name_x} Depletion", depx)
        st.metric(f"{result.name_y} Depletion", depy)
    with colC:
        st.metric(f"{result.name_x} Survival", f"{pct_x[-1]:.1f}%")
        st.metric(f"{result.name_y} Survival", f"{pct_y[-1]:.1f}%")

# ── TAB 3: Economic Impact Heatmap ───────────────────────────────────────────

with tab3:
    st.markdown("### ECONOMIC SHOCK PROPAGATION")
    st.markdown(
        f"*Oil price peak: **${eco.oil_price_peak:.0f}/bbl** "
        f"(+{(eco.oil_price_peak/82-1)*100:.0f}% vs baseline) | "
        f"Global recession risk: **{eco.recession_probability*100:.0f}%***"
    )

    # Oil price chart
    fig_oil = go.Figure()
    months_full = eco.months
    prices_full = eco.oil_price_path[:len(months_full)]
    fig_oil.add_trace(go.Scatter(
        x=months_full, y=prices_full,
        fill="tozeroy", fillcolor="rgba(255,107,53,0.15)",
        line=dict(color="#ff6b35", width=2.5),
        name="Brent Crude",
    ))
    fig_oil.add_hline(y=82, line_dash="dot", line_color="#888",
                      annotation_text="Baseline $82", annotation_font_color="#888")
    fig_oil.add_hline(y=130, line_dash="dash", line_color="#e74c3c",
                      annotation_text="Recession threshold $130", annotation_font_color="#e74c3c")
    fig_oil.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
        font=dict(family="Courier New", color="#e0e0e0"),
        title=dict(text="Oil Price Projection (36 months)", font=dict(color="#ff6b35")),
        xaxis=dict(title="Month", gridcolor="#222"),
        yaxis=dict(title="$/barrel", gridcolor="#333"),
        height=280,
    )
    st.plotly_chart(fig_oil, use_container_width=True)

    # GDP impact heatmap
    gdp_df = build_gdp_impact_dataframe(eco)
    countries = ["USA", "Israel", "Iran", "Saudi_Arabia", "EU", "China", "India"]
    countries = [c for c in countries if c in gdp_df.columns]
    heatmap_data = gdp_df[countries].T

    fig_heat = go.Figure(go.Heatmap(
        z=heatmap_data.values,
        x=[f"Mo {int(m)}" for m in heatmap_data.columns],
        y=countries,
        colorscale=[
            [0.0, "#8b0000"],
            [0.4, "#cc3300"],
            [0.5, "#1a1a1a"],
            [0.6, "#003300"],
            [1.0, "#00aa44"],
        ],
        zmid=0,
        text=np.round(heatmap_data.values, 2),
        texttemplate="%{text:.1f}%",
        textfont=dict(family="Courier New", size=8),
        colorbar=dict(title="GDP Δ%", tickfont=dict(family="Courier New")),
    ))
    fig_heat.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
        font=dict(family="Courier New", color="#e0e0e0"),
        title=dict(text="GDP Impact Heatmap (Countries × Months)", font=dict(color="#ff6b35")),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        height=350,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Recovery timeline
    rec_data = {c: eco.recovery_months.get(c, 36.0) for c in countries}
    fig_rec = go.Figure(go.Bar(
        x=list(rec_data.keys()),
        y=list(rec_data.values()),
        marker_color=["#3498db" if v < 18 else "#e74c3c" for v in rec_data.values()],
        text=[f"{v:.0f}mo" for v in rec_data.values()],
        textposition="outside",
        textfont=dict(family="Courier New"),
    ))
    fig_rec.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
        font=dict(family="Courier New", color="#e0e0e0"),
        title=dict(text="Economic Recovery Timeline (months to <1% GDP impact)", font=dict(color="#ff6b35")),
        yaxis=dict(title="Months", gridcolor="#333"),
        height=280,
    )
    st.plotly_chart(fig_rec, use_container_width=True)

# ── TAB 4: Escalation Ladder ─────────────────────────────────────────────────

with tab4:
    st.markdown("### ESCALATION LADDER DYNAMICS")
    st.markdown(
        "*Herman Kahn-inspired escalation ladder. "
        "Node size = time spent at rung. Red = nuclear threshold zone.*"
    )

    history = esc.history
    days   = [h["day"] for h in history]
    rungs  = [h["rung"] for h in history]

    fig_esc = go.Figure()
    fig_esc.add_hrect(y0=11.5, y1=12.5, fillcolor="rgba(139,0,0,0.25)",
                       line_width=0, annotation_text="NUCLEAR ZONE", annotation_position="right")
    fig_esc.add_hrect(y0=9.5, y1=11.5, fillcolor="rgba(200,50,0,0.10)", line_width=0)
    fig_esc.add_hrect(y0=0.5, y1=5.5, fillcolor="rgba(0,100,0,0.08)", line_width=0)

    # Color by rung value
    rung_colors = [
        "#e74c3c" if r >= 11 else ("#e67e22" if r >= 9 else ("#f1c40f" if r >= 6 else "#2ecc71"))
        for r in rungs
    ]

    fig_esc.add_trace(go.Scatter(
        x=days, y=rungs,
        mode="lines+markers",
        line=dict(color="#ff6b35", width=2),
        marker=dict(size=5, color=rung_colors),
        name="Escalation Rung",
    ))

    fig_esc.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
        font=dict(family="Courier New", color="#e0e0e0"),
        title=dict(text="Escalation Ladder Trajectory (90 days)", font=dict(color="#ff6b35")),
        xaxis=dict(title="Day", gridcolor="#222"),
        yaxis=dict(
            title="Escalation Rung",
            gridcolor="#333",
            range=[0.5, 12.5],
            tickvals=list(range(1, 13)),
            ticktext=[f"{i}: {RUNG_LABELS.get(EscalationRung(i), '')[:25]}" for i in range(1, 13)],
            tickfont=dict(size=9),
        ),
        height=450,
    )
    st.plotly_chart(fig_esc, use_container_width=True)

    # Actor threat perceptions over time
    threat_data = {
        actor: [h["actor_threat_perceptions"].get(actor, 0.0) for h in history]
        for actor in ["USA", "Israel", "Iran", "Hezbollah"]
        if actor in history[0].get("actor_threat_perceptions", {})
    }

    if threat_data:
        fig_threat = go.Figure()
        colors_map = {"USA": "#3498db", "Israel": "#2ecc71", "Iran": "#e74c3c", "Hezbollah": "#9b59b6"}
        for actor, values in threat_data.items():
            fig_threat.add_trace(go.Scatter(
                x=days, y=values,
                name=actor,
                line=dict(color=colors_map.get(actor, "#888"), width=2),
            ))
        fig_threat.add_hline(y=0.15, line_dash="dash", line_color="#ff0000",
                              annotation_text="Nuclear RED threshold", annotation_font_color="#ff0000")
        fig_threat.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
            font=dict(family="Courier New", color="#e0e0e0"),
            title=dict(text="Actor Existential Threat Perception (0–1)", font=dict(color="#ff6b35")),
            xaxis=dict(title="Day", gridcolor="#222"),
            yaxis=dict(title="Threat Perception", gridcolor="#333", range=[0, 1]),
            height=320,
        )
        st.plotly_chart(fig_threat, use_container_width=True)

    # Nuclear threshold table
    st.markdown("#### NUCLEAR THRESHOLD ASSESSMENT")
    nuc_rows = []
    for name, actor in esc.actors.items():
        p_nuc = compute_nuclear_threshold(actor, war_day=esc.day)
        nuc_rows.append({
            "Actor": name,
            "Threat Perception": f"{actor.existential_threat_perception:.2f}",
            "Regime Stability": f"{actor.regime_stability_index:.2f}",
            "Rationality": f"{actor.leadership_rationality_score:.2f}",
            "P(Nuclear)": f"{p_nuc:.3f}",
            "Status": "🔴 RED FLAG" if p_nuc > 0.15 else ("🟡 ELEVATED" if p_nuc > 0.05 else "🟢 LOW"),
        })
    st.dataframe(
        pd.DataFrame(nuc_rows),
        use_container_width=True,
        hide_index=True,
    )

# ── TAB 5: Raw Data & Export ──────────────────────────────────────────────────

with tab5:
    st.markdown("### RAW DATA & CSV EXPORT")

    # Outcome probabilities table
    st.markdown("#### Outcome Probability Table")
    out_rows = []
    for state, label in OUTCOME_LABELS.items():
        p    = mc.outcome_probabilities.get(state, 0.0)
        lo, hi = mc.confidence_intervals.get(state, (0, 0))
        out_rows.append({
            "State": state,
            "Label": label,
            "Probability": round(p, 4),
            "CI_Low_95": round(lo, 4),
            "CI_High_95": round(hi, 4),
            "Mean_Day": round(mc.mean_outcome_day.get(state, 0.0), 1),
            "Count": mc.outcome_counts.get(state, 0),
        })
    outcome_df = pd.DataFrame(out_rows)
    st.dataframe(outcome_df, use_container_width=True, hide_index=True)

    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        st.download_button(
            "⬇ Download Outcomes CSV",
            outcome_df.to_csv(index=False),
            "ares_outcomes.csv", "text/csv",
        )

    # GDP impact table
    st.markdown("#### GDP Impact Table (% change from baseline)")
    gdp_df = build_gdp_impact_dataframe(eco)
    st.dataframe(gdp_df.round(3), use_container_width=True)
    with col_dl2:
        st.download_button(
            "⬇ Download GDP Impact CSV",
            gdp_df.round(4).to_csv(),
            "ares_gdp_impact.csv", "text/csv",
        )

    # Escalation history
    st.markdown("#### Escalation Ladder History")
    esc_df = pd.DataFrame(esc.history)
    st.dataframe(esc_df.head(50), use_container_width=True, hide_index=True)
    with col_dl3:
        st.download_button(
            "⬇ Download Escalation CSV",
            esc_df.to_csv(index=False),
            "ares_escalation.csv", "text/csv",
        )

    # Oil price export
    oil_df = pd.DataFrame({
        "month": eco.months,
        "price_usd_per_barrel": eco.oil_price_path[:len(eco.months)],
    })
    st.markdown("#### Oil Price Path")
    st.dataframe(oil_df.round(2), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇ Download Oil Price CSV",
        oil_df.to_csv(index=False),
        "ares_oil_price.csv", "text/csv",
    )

    st.markdown("---")
    st.markdown(
        '<div class="info-box">ℹ MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE. '
        'ARES v1.0 | Data sources: IISS Military Balance 2024, World Bank, '
        'SIPRI, NTI, US EIA, Correlates of War Project, RAND Corporation. '
        'For academic and research use only.</div>',
        unsafe_allow_html=True,
    )
