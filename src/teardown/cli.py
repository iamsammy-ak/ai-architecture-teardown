"""Command line: ``python -m teardown {cost,bench,manifest,verify-sources}``."""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Sequence
from pathlib import Path

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from . import __version__
from .inputs import load_inputs
from .manifest import Mode, ModeSpec, load_manifest
from .paths import project_root


def _cost(args: argparse.Namespace, console: Console) -> int:
    from .report import ILLUSTRATIVE, CostReport, usd

    root = project_root()
    report = CostReport(load_inputs(), load_manifest())
    if not args.no_write:
        chart_dir = None if args.no_charts else root / "docs" / "assets" / "charts"
        written = report.write(root / "bench" / "results", chart_dir)
        if not args.svg:
            console.print(f"[dim]wrote {len(written)} files under bench/results/ and docs/assets/charts/[/dim]")
    tables = report.inputs.price_tables
    table = Table(title="Cost per task (USD) under each price table", title_style="bold", header_style="bold",
                  box=box.SIMPLE_HEAVY)
    table.add_column("Scenario", min_width=30)
    short = {"gateway-illustrative": "Gateway\nillustrative", "gateway-narrow": "Gateway\nnarrow",
             "trajectory-flat": "Trajectory\ngate flat", "scenario-premium-large": "Premium\nlarge"}
    for t in tables:
        header = short.get(t.id, t.label)
        table.add_column(header + (" *" if t.kind == "scenario" else ""), justify="right")
    for s in report.scenarios:
        table.add_row(s.label, *[usd(report.matrix[s.id][t.id].usd) for t in tables])
    console.print(table)
    illustrative = report.matrix["coding-swarm"][ILLUSTRATIVE]
    console.print(
        f"Coding task, 3 reviewers @ 0.8: {usd(illustrative.usd)} per task, "
        f"{usd(illustrative.usd_per_success or 0)} per correct solution (gateway illustrative prices).\n"
        "* hypothetical scenario defined in this repository. Prices are illustrative, not quotes; every token count "
        "is a measurement at a pinned commit or a stated assumption (bench/cost_inputs.yaml)."
    )
    if args.svg:
        svg = console.export_svg(title="python -m teardown cost")
        kept = [line for line in svg.splitlines() if not line.strip().startswith("<!--")]  # drop the tool comment
        Path(args.svg).write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")
        print(f"saved {args.svg}")
    return 0


def _manifest(args: argparse.Namespace, console: Console) -> int:
    from .runner import manifest_markdown

    manifest = load_manifest()
    table = Table(title=f"{len(manifest.repos)} repositories, pinned", header_style="bold")
    for column in ("Repository", "Commit", "Fast (min)", "Full (min)", "Fast needs", "Full needs"):
        table.add_column(column)
    def needs(spec: ModeSpec) -> str:
        items = [n for n, flag in (("models", spec.needs_models), ("data", spec.needs_data)) if flag]
        return ", ".join(items) or "-"

    for r in manifest.repos:
        fast, full = r.mode("fast"), r.mode("full")
        table.add_row(r.name, r.short_commit, f"{fast.runtime_minutes:g}", f"{full.runtime_minutes:g}", needs(fast),
                      needs(full))
    console.print(table)
    if args.markdown:
        path = project_root() / "bench" / "results" / "manifest.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest_markdown(manifest), encoding="utf-8", newline="\n")
        console.print(f"[dim]wrote {path.relative_to(project_root()).as_posix()}[/dim]")
    return 0


def _bench(args: argparse.Namespace, console: Console) -> int:
    from .runner import Runner, RunOptions, load_records, merge_records, select, write_summary

    manifest = load_manifest()
    mode: Mode = "full" if args.full else "fast"
    only = [name for item in args.only for name in item.split(",") if name]
    repos = select(manifest, mode, only, model_free=args.model_free)
    if not repos:
        console.print("[yellow]nothing selected[/yellow]")
        return 1
    options = RunOptions(mode=mode, workdir=args.workdir, keep=args.keep, clone_from=args.clone_from,
                         python=args.python, use_venv=not args.no_venv, timeout_factor=args.timeout_factor,
                         collect_dir=args.out / "runs")
    runner = Runner(manifest, options)
    if args.dry_run:
        for repo in repos:
            console.print(f"[bold]{repo.name}[/bold] @ {repo.short_commit} ({mode})")
            if not repo.published:
                console.print("  skipped: not published yet")
                continue
            for phase, command in runner.plan(repo):
                console.print(f"  [dim]{phase:9}[/dim] {escape(command)}")
        return 0
    records = []
    for repo in repos:
        console.print(f"[bold]{repo.name}[/bold] @ {repo.short_commit} ({mode}) ...")
        record = runner.run(repo)
        colour = {"passed": "green", "failed": "red", "skipped": "yellow"}[record.status]
        console.print(f"  [{colour}]{record.status}[/{colour}] in {record.seconds:.0f} s {escape(record.reason)}")
        for h in record.headline:
            console.print(f"    {escape(h.label)}: fresh {h.fresh} | committed {h.committed}")
        for line in record.log_tail[-8:]:
            console.print(f"    [dim]{line}[/dim]", markup=False, highlight=False)
        records.append(record)
    summary = args.out / "summary.json"
    merged = merge_records(load_records(summary), records)
    json_path, md_path = write_summary(merged, manifest, args.out)
    console.print(f"[dim]summary: {md_path.as_posix()}[/dim]")
    return 0 if all(r.status != "failed" for r in records) else 1


def _verify(args: argparse.Namespace, console: Console) -> int:
    from .sources import GitHubRawFetcher, LocalGitFetcher, verify_inputs

    manifest = load_manifest()
    fetcher = LocalGitFetcher(args.local) if args.local else GitHubRawFetcher(manifest.owner)
    checks = verify_inputs(load_inputs(), manifest, fetcher)
    table = Table(title="Cost-model inputs re-read at the pinned commits", header_style="bold")
    for column in ("Input", "Repository", "Expected", "Found", ""):
        table.add_column(column)
    for c in checks:
        table.add_row(c.id, c.repo, c.expected, c.actual, "[green]ok[/green]" if c.ok else "[red]MISMATCH[/red]")
    console.print(table)
    bad = [c for c in checks if not c.ok]
    console.print(f"{len(checks) - len(bad)} of {len(checks)} inputs match their sources.")
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    """The argument parser (exposed for tests)."""
    parser = argparse.ArgumentParser(prog="teardown", description=__doc__)
    parser.add_argument("--version", action="version", version=f"teardown {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("cost", help="compute the cost-per-task model; write results and charts")
    p.add_argument("--no-charts", action="store_true", help="skip the matplotlib charts")
    p.add_argument("--no-write", action="store_true", help="print only")
    p.add_argument("--svg", help="also save the printed table as an SVG")
    p.set_defaults(func=_cost)

    p = sub.add_parser("bench", help="reproduce pinned benchmarks in fresh clones and virtual environments")
    p.add_argument("--only", action="append", default=[], help="repository name(s), comma-separated; repeatable")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--fast", action="store_true", help="small settings (default)")
    group.add_argument("--full", action="store_true", help="the settings behind the committed results")
    p.add_argument("--model-free", action="store_true", help="only modes that download no models or datasets")
    p.add_argument("--dry-run", action="store_true", help="print the commands without running them")
    p.add_argument("--clone-from", type=Path, help="clone from local mirrors <dir>/<repo> instead of GitHub")
    p.add_argument("--workdir", type=Path, help="keep clones and venvs here (default: a temporary directory)")
    p.add_argument("--keep", action="store_true", help="do not delete the temporary directory")
    p.add_argument("--python", default=sys.executable, help="interpreter used to create the virtual environments")
    p.add_argument("--no-venv", action="store_true", help="use --python directly and skip installation")
    p.add_argument("--timeout-factor", type=float, default=4.0, help="timeout = expected runtime x this factor")
    p.add_argument("--out", type=Path, default=None, help="results directory (default: bench/results)")
    p.set_defaults(func=_bench)

    p = sub.add_parser("manifest", help="validate and list the pinned manifest")
    p.add_argument("--markdown", action="store_true", help="also write bench/results/manifest.md")
    p.set_defaults(func=_manifest)

    p = sub.add_parser("verify-sources", help="re-read every measured input from its repository at the pinned commit")
    p.add_argument("--local", type=Path, help="directory with local clones (default: raw.githubusercontent.com)")
    p.set_defaults(func=_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args = build_parser().parse_args(argv)
    if getattr(args, "out", "unset") is None:
        args.out = project_root() / "bench" / "results"
    if getattr(args, "svg", None):  # record off-screen with Unicode boxes, whatever the terminal's encoding
        console = Console(record=True, file=io.StringIO(), width=110, force_terminal=True, color_system="truecolor",
                          legacy_windows=False, safe_box=False)
    else:
        console = Console(width=110)
    return int(args.func(args, console))
