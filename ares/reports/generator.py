"""
ARES PDF Report Generator
[MODEL OUTPUT - NOT PREDICTIVE INTELLIGENCE]

Generates structured PDF reports from scenario results.
Uses ReportLab for PDF generation.
"""

from __future__ import annotations

import os
import io
import sys
from datetime import datetime
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec


# ReportLab imports
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, HRFlowable, PageBreak, KeepTogether,
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from engine.montecarlo import OUTCOME_LABELS
from engine.economic import COUNTRY_PROFILES


# ─── Color palette ────────────────────────────────────────────────────────────

AMBER    = colors.HexColor("#ff6b35") if REPORTLAB_AVAILABLE else None
RED      = colors.HexColor("#c0392b") if REPORTLAB_AVAILABLE else None
DARK_BG  = colors.HexColor("#0a0a0a") if REPORTLAB_AVAILABLE else None
MID_DARK = colors.HexColor("#1a1a1a") if REPORTLAB_AVAILABLE else None
LIGHT    = colors.HexColor("#e0e0e0") if REPORTLAB_AVAILABLE else None
GREEN    = colors.HexColor("#2ecc71") if REPORTLAB_AVAILABLE else None
DIM      = colors.HexColor("#666666") if REPORTLAB_AVAILABLE else None


# ─── Matplotlib chart generators ─────────────────────────────────────────────

def _fig_to_image_bytes(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()


def make_outcome_bar_chart(mc_result) -> bytes:
    """Outcome probability bar chart."""
    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    states = list(OUTCOME_LABELS.keys())
    labels = [f"S{s}" for s in states]
    probs  = [mc_result.outcome_probabilities.get(s, 0.0) * 100 for s in states]
    cis_lo = [(mc_result.outcome_probabilities.get(s, 0.0) - mc_result.confidence_intervals.get(s, (0, 0))[0]) * 100 for s in states]
    cis_hi = [(mc_result.confidence_intervals.get(s, (0, 0))[1] - mc_result.outcome_probabilities.get(s, 0.0)) * 100 for s in states]

    outcome_colors_mpl = ["#2ecc71", "#f39c12", "#e67e22", "#e74c3c", "#9b59b6", "#c0392b", "#922b21", "#1a5276"]
    bars = ax.bar(labels, probs, color=outcome_colors_mpl, edgecolor="#333", linewidth=0.5)
    ax.errorbar(labels, probs, yerr=[cis_lo, cis_hi], fmt="none", ecolor="#ff6b35", capsize=4, linewidth=1.2)

    for bar, p in zip(bars, probs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{p:.1f}%", ha="center", va="bottom", color="#e0e0e0", fontsize=8, fontfamily="monospace")

    ax.set_xlabel("Outcome State", color="#888", fontsize=9)
    ax.set_ylabel("Probability (%)", color="#888", fontsize=9)
    ax.set_title("Monte Carlo Outcome Distribution (95% CI)", color="#ff6b35", fontsize=11)
    ax.tick_params(colors="#888", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#333")
    ax.set_ylim(0, max(probs) * 1.25 if probs else 50)
    ax.yaxis.grid(True, color="#222", linewidth=0.5)

    fig.tight_layout()
    data = _fig_to_image_bytes(fig)
    plt.close(fig)
    return data


def make_gdp_heatmap(eco_result) -> bytes:
    """GDP impact heatmap."""
    countries = ["USA", "Israel", "Iran", "Saudi_Arabia", "EU", "China", "India"]
    countries = [c for c in countries if c in eco_result.gdp_impact]
    months    = [0, 3, 6, 12, 18, 24, 30, 36]

    matrix = np.array([
        [float(eco_result.gdp_impact[c][m]) if m < len(eco_result.gdp_impact[c]) else 0.0
         for m in months]
        for c in countries
    ])

    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "ares", ["#8b0000", "#cc3300", "#1a1a1a", "#003300", "#00aa44"]
    )
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=-10, vmax=5)

    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([f"Mo {m}" for m in months], color="#888", fontsize=8)
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries, color="#e0e0e0", fontsize=9, fontfamily="monospace")

    for i in range(len(countries)):
        for j in range(len(months)):
            ax.text(j, i, f"{matrix[i, j]:+.1f}%", ha="center", va="center",
                    color="#fff", fontsize=7, fontfamily="monospace")

    plt.colorbar(im, ax=ax, label="GDP Δ%", fraction=0.046, pad=0.04)
    ax.set_title("GDP Impact Heatmap (Countries × Months)", color="#ff6b35", fontsize=11)
    ax.tick_params(colors="#888")

    fig.tight_layout()
    data = _fig_to_image_bytes(fig)
    plt.close(fig)
    return data


def make_oil_price_chart(eco_result) -> bytes:
    """Oil price trajectory."""
    fig, ax = plt.subplots(figsize=(10, 3.5), facecolor="#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    months = eco_result.months
    prices = eco_result.oil_price_path[:len(months)]

    ax.fill_between(months, prices, 82, where=(prices > 82),
                    facecolor="rgba(255,107,53,0.2)", interpolate=True)
    ax.plot(months, prices, color="#ff6b35", linewidth=2.5, label="Brent Crude")
    ax.axhline(82, color="#888", linestyle=":", linewidth=1, label="Baseline $82")
    ax.axhline(130, color="#e74c3c", linestyle="--", linewidth=1, label="Recession threshold $130")

    ax.set_xlabel("Month", color="#888", fontsize=9)
    ax.set_ylabel("$/barrel", color="#888", fontsize=9)
    ax.set_title(f"Oil Price Projection | Peak: ${eco_result.oil_price_peak:.0f}/bbl", color="#ff6b35", fontsize=11)
    ax.tick_params(colors="#888", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#333")
    ax.yaxis.grid(True, color="#222", linewidth=0.5)
    ax.legend(facecolor="#1a1a1a", edgecolor="#333", labelcolor="#e0e0e0", fontsize=8)

    fig.tight_layout()
    data = _fig_to_image_bytes(fig)
    plt.close(fig)
    return data


def make_lanchester_chart(lanchester_results: dict) -> bytes:
    """Force attrition multi-panel chart."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), facecolor="#0f0f0f")
    theaters = [
        ("air_campaign", "square", "Air Campaign (Square Law)"),
        ("missile_exchange", "square", "Missile Exchange (Square Law)"),
        ("proxy_warfare", "linear", "Proxy Warfare (Linear Law)"),
    ]

    for ax, (theater, law, title) in zip(axes, theaters):
        ax.set_facecolor("#0f0f0f")
        res = lanchester_results[theater][law]
        pct_x = res.force_x / res.force_x[0] * 100
        pct_y = res.force_y / res.force_y[0] * 100

        ax.fill_between(res.time_days, pct_x, alpha=0.1, color="#3498db")
        ax.fill_between(res.time_days, pct_y, alpha=0.1, color="#e74c3c")
        ax.plot(res.time_days, pct_x, color="#3498db", linewidth=2, label=res.name_x[:20])
        ax.plot(res.time_days, pct_y, color="#e74c3c", linewidth=2, label=res.name_y[:20])

        ax.set_title(title, color="#ff6b35", fontsize=8.5)
        ax.set_xlabel("Day", color="#888", fontsize=8)
        ax.set_ylabel("Force %", color="#888", fontsize=8)
        ax.tick_params(colors="#888", labelsize=7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#333")
        ax.yaxis.grid(True, color="#1a1a1a", linewidth=0.5)
        ax.legend(fontsize=7, facecolor="#111", edgecolor="#333", labelcolor="#e0e0e0")
        ax.set_ylim(0, 115)

    fig.suptitle("Lanchester Force Attrition Curves", color="#ff6b35", fontsize=12, y=1.02)
    fig.tight_layout()
    data = _fig_to_image_bytes(fig)
    plt.close(fig)
    return data


def make_escalation_chart(esc_state) -> bytes:
    """Escalation ladder trajectory."""
    history = esc_state.history
    days  = [h["day"] for h in history]
    rungs = [h["rung"] for h in history]

    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    ax.axhspan(11.5, 12.5, facecolor="#8b000033", label="Nuclear Zone")
    ax.axhspan(9.5, 11.5, facecolor="#8b450033")

    rung_colors_mpl = [
        "#e74c3c" if r >= 11 else ("#e67e22" if r >= 9 else ("#f1c40f" if r >= 6 else "#2ecc71"))
        for r in rungs
    ]
    ax.plot(days, rungs, color="#ff6b35", linewidth=1.5, zorder=2)
    ax.scatter(days[::5], rungs[::5], c=rung_colors_mpl[::5], s=15, zorder=3)

    ax.set_yticks(range(1, 13))
    ax.set_yticklabels([f"{i}" for i in range(1, 13)], color="#888", fontsize=8)
    ax.set_xlabel("Day", color="#888", fontsize=9)
    ax.set_ylabel("Escalation Rung", color="#888", fontsize=9)
    ax.set_title("Escalation Ladder Trajectory", color="#ff6b35", fontsize=11)
    ax.tick_params(colors="#888")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#333")
    ax.yaxis.grid(True, color="#222", linewidth=0.5)
    ax.set_ylim(0.5, 12.5)

    fig.tight_layout()
    data = _fig_to_image_bytes(fig)
    plt.close(fig)
    return data


# ─── PDF Generator ────────────────────────────────────────────────────────────

def generate_pdf_report(
    mc_result,
    lanchester_results: dict,
    eco_result,
    esc_state,
    output_path: str,
    scenario_name: str = "USA + Israel vs Iran",
) -> str:
    """
    Generate full PDF report.

    Args:
        mc_result: MonteCarloResults
        lanchester_results: dict from scenario_usa_israel_vs_iran()
        eco_result: EconomicImpactResult
        esc_state: EscalationState
        output_path: Output file path
        scenario_name: Scenario label

    Returns:
        Path to generated PDF file.
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback: generate a text report
        txt_path = output_path.replace(".pdf", ".txt")
        _generate_text_report(mc_result, eco_result, txt_path, scenario_name)
        print(f"[ARES] ReportLab not available. Text report saved: {txt_path}")
        return txt_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "AresTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=AMBER,
        fontName="Courier-Bold",
        spaceAfter=8,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "AresSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=LIGHT,
        fontName="Courier",
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    heading_style = ParagraphStyle(
        "AresHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=AMBER,
        fontName="Courier-Bold",
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "AresBody",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=LIGHT,
        fontName="Courier",
        spaceAfter=4,
        leading=13,
    )
    warning_style = ParagraphStyle(
        "AresWarning",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=RED,
        fontName="Courier-Bold",
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=4,
    )

    story = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # ── Cover ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("⚠ ARES", title_style))
    story.append(Paragraph("ADAPTIVE RISK AND ESCALATION SIMULATOR", title_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Scenario: {scenario_name}", subtitle_style))
    story.append(Paragraph(f"Generated: {timestamp}", subtitle_style))
    story.append(Paragraph(f"Monte Carlo Runs: {mc_result.n_simulations:,}", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=RED))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE. "
        "All values from open-source public research. "
        "For academic and research purposes only.",
        warning_style,
    ))
    story.append(Paragraph(
        "Data sources: IISS Military Balance 2024 | SIPRI Yearbook 2024 | "
        "World Bank 2024 | NTI Nuclear Security Index | US EIA | "
        "Correlates of War Project | RAND Corporation",
        warning_style,
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=AMBER))
    story.append(PageBreak())

    # ── Section 1: Executive Summary ───────────────────────────────────
    story.append(Paragraph("1. EXECUTIVE SUMMARY", heading_style))

    most_probable = max(mc_result.outcome_probabilities, key=mc_result.outcome_probabilities.get)
    most_p = mc_result.outcome_probabilities[most_probable]
    nuc_p  = mc_result.nuclear_probability

    exec_text = (
        f"The ARES Monte Carlo simulation ({mc_result.n_simulations:,} runs) "
        f"yields the following key findings for the {scenario_name} scenario:<br/><br/>"
        f"• <b>Most Probable Outcome:</b> State {most_probable} — "
        f"{OUTCOME_LABELS[most_probable]} ({most_p*100:.1f}%)<br/>"
        f"• <b>Nuclear Threshold Risk:</b> {nuc_p*100:.1f}% probability "
        f"[95% CI: {mc_result.nuclear_ci[0]*100:.1f}–{mc_result.nuclear_ci[1]*100:.1f}%] — "
        f"{'⚠ RED FLAG (>15%)' if nuc_p > 0.15 else 'Below RED threshold'}<br/>"
        f"• <b>Oil Price Peak:</b> ${eco_result.oil_price_peak:.0f}/bbl "
        f"(+{(eco_result.oil_price_peak/82-1)*100:.0f}% vs baseline $82)<br/>"
        f"• <b>Global GDP Loss (12-month):</b> {eco_result.global_gdp_loss_pct:.2f}%<br/>"
        f"• <b>Recession Probability:</b> {eco_result.recession_probability*100:.1f}%<br/>"
        f"• <b>Peak Escalation Rung:</b> {max(h['rung'] for h in esc_state.history)} / 12<br/>"
    )
    story.append(Paragraph(exec_text, body_style))
    story.append(Spacer(1, 0.5 * cm))

    # ── Section 2: Outcome Probabilities ──────────────────────────────
    story.append(Paragraph("2. MONTE CARLO OUTCOME DISTRIBUTION", heading_style))

    # Outcome table
    tbl_data = [["State", "Outcome", "Probability", "95% CI Low", "95% CI High", "Mean Day"]]
    for state, label in OUTCOME_LABELS.items():
        p     = mc_result.outcome_probabilities.get(state, 0.0)
        lo, hi = mc_result.confidence_intervals.get(state, (0.0, 0.0))
        day   = mc_result.mean_outcome_day.get(state, 0.0)
        tbl_data.append([
            str(state),
            label[:40],
            f"{p*100:.2f}%",
            f"{lo*100:.2f}%",
            f"{hi*100:.2f}%",
            f"{day:.0f}d",
        ])

    tbl = Table(tbl_data, colWidths=[1.2*cm, 8.5*cm, 2.2*cm, 2.2*cm, 2.2*cm, 1.8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1a1a1a")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  AMBER),
        ("FONTNAME",     (0, 0), (-1, 0),  "Courier-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 7.5),
        ("FONTNAME",     (0, 1), (-1, -1), "Courier"),
        ("TEXTCOLOR",    (0, 1), (-1, -1), LIGHT),
        ("BACKGROUND",   (0, 1), (-1, -1), colors.HexColor("#111111")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f0f0f"), colors.HexColor("#141414")]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#333333")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Chart
    try:
        chart_bytes = make_outcome_bar_chart(mc_result)
        img = Image(io.BytesIO(chart_bytes), width=17*cm, height=7*cm)
        story.append(img)
    except Exception as e:
        story.append(Paragraph(f"[Chart generation error: {e}]", body_style))

    story.append(PageBreak())

    # ── Section 3: Economic Impact ─────────────────────────────────────
    story.append(Paragraph("3. ECONOMIC SHOCK PROPAGATION", heading_style))
    story.append(Paragraph(
        f"Oil peak: ${eco_result.oil_price_peak:.0f}/bbl | "
        f"Global GDP loss (12mo): {eco_result.global_gdp_loss_pct:.2f}% | "
        f"Recession probability: {eco_result.recession_probability*100:.1f}%",
        body_style,
    ))

    # Country GDP impact table
    eco_tbl_data = [["Country", "GDP (T$)", "12-mo Δ%", "24-mo Δ%", "Recovery (mo)"]]
    for country in ["USA", "Israel", "Iran", "Saudi_Arabia", "EU", "China", "India"]:
        if country not in eco_result.gdp_impact:
            continue
        imp = eco_result.gdp_impact[country]
        m12 = float(imp[12]) if len(imp) > 12 else float(imp[-1])
        m24 = float(imp[24]) if len(imp) > 24 else float(imp[-1])
        rec = eco_result.recovery_months.get(country, 36.0)
        gdp = COUNTRY_PROFILES.get(country, {}).get("gdp_trillion", 0)
        eco_tbl_data.append([
            country,
            f"${gdp:.1f}T",
            f"{m12:+.2f}%",
            f"{m24:+.2f}%",
            f"{rec:.0f}",
        ])

    eco_tbl = Table(eco_tbl_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3.5*cm])
    eco_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1a1a1a")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), AMBER),
        ("FONTNAME",    (0, 0), (-1, 0), "Courier-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("FONTNAME",    (0, 1), (-1, -1), "Courier"),
        ("TEXTCOLOR",   (0, 1), (-1, -1), LIGHT),
        ("BACKGROUND",  (0, 1), (-1, -1), colors.HexColor("#111111")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f0f0f"), colors.HexColor("#141414")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#333333")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(eco_tbl)
    story.append(Spacer(1, 0.4 * cm))

    try:
        story.append(Image(io.BytesIO(make_oil_price_chart(eco_result)), width=17*cm, height=5.5*cm))
        story.append(Spacer(1, 0.3*cm))
        story.append(Image(io.BytesIO(make_gdp_heatmap(eco_result)), width=17*cm, height=6*cm))
    except Exception as e:
        story.append(Paragraph(f"[Chart error: {e}]", body_style))

    story.append(PageBreak())

    # ── Section 4: Lanchester Analysis ─────────────────────────────────
    story.append(Paragraph("4. LANCHESTER FORCE ATTRITION", heading_style))
    story.append(Paragraph(
        "Square Law applied to modern conventional combat (air strikes, missile exchange). "
        "Linear Law applied to proxy/guerrilla warfare. "
        "Results represent modeled attrition trajectories, not battlefield predictions.",
        body_style,
    ))
    try:
        story.append(Image(io.BytesIO(make_lanchester_chart(lanchester_results)), width=17*cm, height=6*cm))
    except Exception as e:
        story.append(Paragraph(f"[Chart error: {e}]", body_style))

    story.append(Spacer(1, 0.5 * cm))

    # ── Section 5: Escalation Ladder ──────────────────────────────────
    story.append(Paragraph("5. ESCALATION LADDER & NUCLEAR ASSESSMENT", heading_style))

    nuc_flag_text = (
        f"Nuclear Threshold Probability: <b>{nuc_p*100:.1f}%</b> "
        f"[95% CI: {mc_result.nuclear_ci[0]*100:.1f}–{mc_result.nuclear_ci[1]*100:.1f}%]<br/>"
        f"Status: {'⚠ RED FLAG — Exceeds 15% threshold' if nuc_p > 0.15 else '✓ Below RED threshold (15%)'}<br/><br/>"
        f"Peak escalation rung in simulation: {max(h['rung'] for h in esc_state.history)} / 12<br/>"
        f"De-escalation triggered: {esc_state.de_escalation_active}"
    )
    story.append(Paragraph(nuc_flag_text, body_style))
    story.append(Spacer(1, 0.3 * cm))

    try:
        story.append(Image(io.BytesIO(make_escalation_chart(esc_state)), width=17*cm, height=6*cm))
    except Exception as e:
        story.append(Paragraph(f"[Chart error: {e}]", body_style))

    # ── Footer disclaimer ─────────────────────────────────────────────
    story.append(Spacer(1, 1.0 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "DISCLAIMER: MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE. "
        "ARES is a research-grade mathematical modeling tool. "
        "Outputs are probabilistic model results calibrated to open-source historical data. "
        "They do not represent intelligence assessments, policy recommendations, "
        "or predictions of future events. "
        "ARES v1.0 | " + timestamp,
        warning_style,
    ))

    doc.build(story)
    return output_path


def _generate_text_report(mc_result, eco_result, output_path: str, scenario_name: str) -> None:
    """Fallback text report when ReportLab is not available."""
    lines = [
        "=" * 70,
        "ARES — ADAPTIVE RISK AND ESCALATION SIMULATOR",
        f"Scenario: {scenario_name}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Monte Carlo Runs: {mc_result.n_simulations:,}",
        "MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE",
        "=" * 70,
        "",
        "OUTCOME PROBABILITY DISTRIBUTION",
        "-" * 70,
    ]

    for state, label in OUTCOME_LABELS.items():
        p     = mc_result.outcome_probabilities.get(state, 0.0)
        lo, hi = mc_result.confidence_intervals.get(state, (0.0, 0.0))
        day   = mc_result.mean_outcome_day.get(state, 0.0)
        bar   = "█" * int(p * 40)
        lines.append(f"  [{state}] {label:<42} {p*100:5.1f}% [{lo*100:.1f}-{hi*100:.1f}%]")
        lines.append(f"      {bar}")

    lines += [
        "",
        f"Nuclear Threshold Risk: {mc_result.nuclear_probability*100:.1f}%",
        f"  {'*** RED FLAG ***' if mc_result.nuclear_probability > 0.15 else 'Below threshold'}",
        "",
        "ECONOMIC IMPACT",
        "-" * 70,
        f"Oil Price Peak: ${eco_result.oil_price_peak:.0f}/bbl",
        f"Global GDP Loss (12-month): {eco_result.global_gdp_loss_pct:.2f}%",
        f"Recession Probability: {eco_result.recession_probability*100:.1f}%",
        "",
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
