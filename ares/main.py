"""
ARES — Adaptive Risk and Escalation Simulator
CLI Entrypoint

[MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]

Usage:
  python main.py --scenario usa_israel_iran --runs 10000
  python main.py --scenario usa_israel_iran --runs 5000 --no-dashboard
  python main.py --scenario global_spillover --runs 5000
  python main.py --list-scenarios
"""

from __future__ import annotations

import argparse
import os
import sys
import subprocess
from datetime import datetime

# ── Ensure engine is importable ────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))


def _banner() -> None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel(
            "[bold red]    ARES — ADAPTIVE RISK AND ESCALATION SIMULATOR    [/bold red]\n"
            "[yellow]    Research-Grade Mathematical Modeling Tool v1.0     [/yellow]\n"
            "[dim]    MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE           [/dim]",
            border_style="red",
            padding=(0, 4),
        ))
    except ImportError:
        print("=" * 60)
        print("  ARES — ADAPTIVE RISK AND ESCALATION SIMULATOR v1.0")
        print("  MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE")
        print("=" * 60)


def _run_usa_israel_iran(args: argparse.Namespace) -> None:
    """Run the USA + Israel vs Iran primary scenario."""
    from scenarios.usa_israel_iran import ScenarioConfig, run_scenario, get_scenario_as_dataframes
    from reports.generator import generate_pdf_report

    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False
        console = None

    config = ScenarioConfig(
        israel_strike_intensity=args.strike_intensity,
        usa_isr_support_only=args.isr_only,
        n_monte_carlo_runs=args.runs,
        random_seed=args.seed,
    )

    if use_rich:
        console.print(f"\n[cyan]Strike intensity:[/cyan] {config.israel_strike_intensity:.2f}")
        console.print(f"[cyan]ISR support only:[/cyan] {config.usa_isr_support_only}")
        console.print(f"[cyan]Monte Carlo runs:[/cyan] {config.n_monte_carlo_runs:,}")
        console.print(f"[cyan]Random seed:[/cyan] {config.random_seed}\n")

    # Run scenario
    result = run_scenario(config, verbose=True)

    # ── Generate PDF report ────────────────────────────────────────────
    if not args.no_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(report_dir, exist_ok=True)
        pdf_path = os.path.join(report_dir, f"ares_report_{timestamp}.pdf")

        print("[ARES] Generating PDF report...")
        try:
            out = generate_pdf_report(
                mc_result=result.monte_carlo,
                lanchester_results={
                    "air_campaign": result.lanchester_air,
                    "missile_exchange": result.lanchester_missile,
                    "proxy_warfare": result.lanchester_proxy,
                },
                eco_result=result.economic_impact,
                esc_state=result.escalation_state,
                output_path=pdf_path,
                scenario_name="USA + Israel vs Iran",
            )
            print(f"[ARES] Report saved: {out}")
        except Exception as e:
            print(f"[ARES] Report error: {e}")

    # ── Export CSVs ────────────────────────────────────────────────────
    if args.export_csv:
        dfs = get_scenario_as_dataframes(result)
        csv_dir = os.path.join(os.path.dirname(__file__), "reports", "csv")
        os.makedirs(csv_dir, exist_ok=True)
        for name, df in dfs.items():
            path = os.path.join(csv_dir, f"ares_{name}.csv")
            df.to_csv(path)
            print(f"[ARES] CSV exported: {path}")

    # ── Launch dashboard ───────────────────────────────────────────────
    if not args.no_dashboard:
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
        print(f"\n[ARES] Launching Streamlit dashboard...")
        print(f"       Dashboard: {dashboard_path}")
        print(f"       Access at: http://localhost:8501\n")
        try:
            subprocess.run(
                [sys.executable, "-m", "streamlit", "run", dashboard_path,
                 "--server.headless", "false",
                 "--theme.base", "dark"],
                cwd=os.path.dirname(__file__),
            )
        except KeyboardInterrupt:
            print("\n[ARES] Dashboard closed.")
        except Exception as e:
            print(f"[ARES] Dashboard error: {e}")
            print("[ARES] Run manually: streamlit run dashboard/app.py")


def _run_global_spillover(args: argparse.Namespace) -> None:
    """Run the global spillover second-order contagion scenario."""
    from scenarios.global_spillover import SpilloverConfig, run_spillover_scenario

    config = SpilloverConfig(
        n_monte_carlo_runs=args.runs,
        random_seed=args.seed,
    )
    result = run_spillover_scenario(config, verbose=True)

    if not args.no_dashboard:
        print("\n[ARES] Global spillover scenario complete.")
        print("[ARES] For full dashboard: python main.py --scenario usa_israel_iran")


def _list_scenarios() -> None:
    """Print available scenarios."""
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(title="Available ARES Scenarios", header_style="bold amber3")
        table.add_column("ID", width=20)
        table.add_column("Name", width=40)
        table.add_column("Description", width=50)
        table.add_row(
            "usa_israel_iran",
            "USA + Israel vs Iran",
            "Primary scenario: Israeli strikes on nuclear sites, Iranian retaliation",
        )
        table.add_row(
            "global_spillover",
            "Global Spillover",
            "Second-order contagion: China, Russia, financial crisis",
        )
        console.print(table)
    except ImportError:
        print("Scenarios:")
        print("  usa_israel_iran  - USA + Israel vs Iran primary scenario")
        print("  global_spillover - Global spillover / second-order contagion")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ARES — Adaptive Risk and Escalation Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --scenario usa_israel_iran --runs 10000
  python main.py --scenario usa_israel_iran --runs 5000 --no-dashboard
  python main.py --scenario global_spillover --runs 5000
  python main.py --list-scenarios

[MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]
        """,
    )

    parser.add_argument(
        "--scenario", "-s",
        choices=["usa_israel_iran", "global_spillover"],
        default="usa_israel_iran",
        help="Scenario to simulate (default: usa_israel_iran)",
    )
    parser.add_argument(
        "--runs", "-n",
        type=int, default=10_000,
        help="Number of Monte Carlo simulations (default: 10000)",
    )
    parser.add_argument(
        "--seed",
        type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--strike-intensity", "-i",
        type=float, default=0.80,
        help="Strike intensity 0-1 (default: 0.80)",
        dest="strike_intensity",
    )
    parser.add_argument(
        "--isr-only",
        action="store_true",
        help="USA ISR support only (no direct strikes)",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Skip launching the Streamlit dashboard",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip PDF report generation",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export all results as CSV files",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios and exit",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    _banner()

    if args.list_scenarios:
        _list_scenarios()
        sys.exit(0)

    print(f"\n[ARES] Scenario: {args.scenario} | Runs: {args.runs:,} | Seed: {args.seed}")
    print("[ARES] Initializing simulation engine...\n")

    if args.scenario == "usa_israel_iran":
        _run_usa_israel_iran(args)
    elif args.scenario == "global_spillover":
        _run_global_spillover(args)
    else:
        print(f"[ARES] Unknown scenario: {args.scenario}")
        sys.exit(1)


if __name__ == "__main__":
    main()
