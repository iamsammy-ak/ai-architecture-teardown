"""Write the cost-model results: JSON, Markdown fragments (included by the docs site) and charts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import charts, cost
from .inputs import CostInputs
from .manifest import Manifest

REPRODUCE = "PYTHONPATH=src python -m teardown cost"
ILLUSTRATIVE = "gateway-illustrative"
CACHE_POINTS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
CRASH_POINTS = (0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3)
ROUTER_LABELS = {
    "all-large": "everything on the large tier",
    "rules": "rules router mix (measured)",
    "logistic": "logistic router mix (measured)",
    "all-small": "everything on the small tier",
}


def usd(value: float) -> str:
    """Format a small dollar amount with enough significant digits."""
    if value == 0:
        return "$0"
    if value >= 100:
        return f"${value:,.0f}"
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:.5f}" if value < 0.01 else f"${value:.4f}"


def _table(header: list[str], rows: list[list[str]], align: list[str] | None = None) -> str:
    align = align or ["---"] + ["---:"] * (len(header) - 1)
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def _source_link(manifest: Manifest, repo: str, path: str) -> str:
    spec = manifest.get(repo)
    return f"[{repo} · `{path}` @ {spec.short_commit}]({spec.blob_url(path)})"


def _num(value: float) -> str:
    if value == int(value) and abs(value) >= 1:
        return f"{int(value):,}"
    return f"{value:,.4g}" if abs(value) < 1000 else f"{value:,.1f}"


class CostReport:
    """Computes every table and chart of the cost page once, then writes them."""

    def __init__(self, inputs: CostInputs, manifest: Manifest) -> None:
        self.inputs = inputs
        self.manifest = manifest
        self.scenarios = cost.headline_scenarios(inputs)
        self.labels = {s.id: s.label for s in self.scenarios}
        self.matrix = cost.price_matrix(inputs, self.scenarios)
        self.cache = cost.sweep_cache(inputs, ILLUSTRATIVE, CACHE_POINTS)
        self.cache_fine = [i / 100 for i in range(0, 61, 2)]
        self.cache_series = cost.sweep_cache(inputs, ILLUSTRATIVE, self.cache_fine,
                                             routers=("all-large", "rules", "logistic"))
        self.reviewers = cost.sweep_reviewers(inputs, ILLUSTRATIVE)
        self.topologies = cost.baseline_topologies(inputs, ILLUSTRATIVE)
        self.crashes = cost.sweep_crashes(inputs, ILLUSTRATIVE, CRASH_POINTS)
        self.crash_fine = [i / 100 for i in range(0, 31)]
        self.crash_series = cost.sweep_crashes(inputs, ILLUSTRATIVE, self.crash_fine)

    # ------------------------------------------------------------------------------------------ fragments
    def price_tables_md(self) -> str:
        rows = []
        for t in self.inputs.price_tables:
            source = (_source_link(self.manifest, t.source.repo, t.source.path) if t.source
                      else "**hypothetical scenario** (this repository)")
            rows.append([t.label] + [f"{t.tiers[tier].input:g} / {t.tiers[tier].output:g}"
                                     for tier in ("small", "medium", "large")] + [source])
        return _table(["Table", "small (in / out)", "medium (in / out)", "large (in / out)", "Source"], rows,
                      ["---", "---:", "---:", "---:", "---"])

    def headline_md(self) -> str:
        tables = self.inputs.price_tables
        rows = []
        for s in self.scenarios:
            row = [s.label]
            for t in tables:
                c = self.matrix[s.id][t.id]
                row.append(f"{usd(c.usd)} · {usd(1000 * c.usd)}")
            rows.append(row)
        return ("USD per task · per 1,000 tasks.\n\n"
                + _table(["Scenario", *[t.label for t in tables]], rows))

    def breakdown_md(self) -> str:
        parts = []
        for s in self.scenarios:
            c = self.matrix[s.id][ILLUSTRATIVE]
            rows = [
                [line.component, line.system, line.tier, f"{line.calls:.3g}", f"{line.billed_calls:.3g}",
                 f"{line.input_tokens:,.0f}", f"{line.output_tokens:,.0f}", usd(line.usd),
                 ", ".join(f"`{b}`" for b in call.basis)]
                for line, call in zip(c.lines, s.task.calls, strict=True)
            ]
            rows.append(["**total**", "", "", "", f"{c.billed_calls:.3g}", f"{c.input_tokens:,.0f}",
                         f"{c.output_tokens:,.0f}", f"**{usd(c.usd)}**", ""])
            knobs = f"cache hit rate {100 * s.cache_hit_rate:.1f}%, routing: {ROUTER_LABELS[s.router]}"
            parts.append(f"**{s.label}** ({knobs})\n\n" + _table(
                ["Component", "System", "Tier", "Calls / task", "Billed calls", "Input tokens", "Output tokens",
                 "USD", "Inputs used"], rows, ["---", "---", "---", "---:", "---:", "---:", "---:", "---:", "---"]))
            if c.usd_per_success is not None:
                parts.append(f"Measured success rate {100 * (c.success_rate or 0):.1f}%, so "
                             f"**{usd(c.usd_per_success)} per correct accepted solution**.\n")
            parts.append("".join(f"- {note}\n" for note in s.task.notes))
        return "\n".join(parts)

    def cache_md(self) -> str:
        rows = [[f"{100 * h:.0f}%"] + [usd(1000 * self.cache[r][i]) for r in self.cache]
                for i, h in enumerate(CACHE_POINTS)]
        measured = (f"Measured hit rates on the gateway's synthetic workloads: support "
                    f"{100 * self.inputs.value('gateway.support.hit_rate.exact_semantic'):.1f}%, assistant "
                    f"{100 * self.inputs.value('gateway.assistant.hit_rate.exact_semantic'):.1f}% "
                    f"(exact + semantic, guard rails on).\n\n")
        return measured + "USD per 1,000 support answers, gateway illustrative prices.\n\n" + _table(
            ["Cache hit rate", *[ROUTER_LABELS[r] for r in self.cache]], rows)

    def reviewers_md(self) -> str:
        rows = []
        for accuracy, values in self.reviewers.items():
            for k, n in enumerate(cost.REVIEWER_COUNTS):
                rows.append([f"{n} @ {accuracy}", f"{self.inputs.value(f'swarm.r{n}.a{accuracy}.calls'):.1f}",
                             f"{100 * values['success_rate'][k]:.1f}%", usd(values["usd"][k]),
                             usd(values["usd_per_success"][k])])
        for name, c in self.topologies.items():
            label = charts.BASELINE_LABELS[name]
            key = "swarm.single" if name == "single" else "swarm.coder_executor"
            rows.append([label, f"{self.inputs.value(f'{key}.calls'):.1f}", f"{100 * (c.success_rate or 0):.1f}%",
                         usd(c.usd), usd(c.usd_per_success or 0)])
        marginal = []
        for accuracy, values in self.reviewers.items():
            d_usd = values["usd"][1] - values["usd"][0]
            d_success = values["success_rate"][1] - values["success_rate"][0]
            marginal.append([accuracy, f"{100 * d_success:+.1f} pts", usd(d_usd),
                             usd(d_usd / d_success) if d_success > 0 else "n/a"])
        return ("Large tier, gateway illustrative prices. Success = the accepted code passes every visible and "
                "hidden test with no major security finding (measured by execution).\n\n"
                + _table(["Panel", "Agent calls / task", "Success", "USD / task", "USD / correct solution"], rows)
                + "\nGoing from 1 to 3 reviewers:\n\n"
                + _table(["Reviewer accuracy", "Success change", "Extra USD / task",
                          "USD per additional correct solution"], marginal))

    def crashes_md(self) -> str:
        names = list(self.crashes)
        rows = [[f"{100 * p:g}%"] + [f"{self.crashes[n][i]:.2f}x" for n in names] for i, p in enumerate(CRASH_POINTS)]
        v = self.inputs.value
        chaos = (f"Measured in the chaos benchmark: {v('durable.chaos.kills'):.0f} worker kills over "
                 f"{v('durable.chaos.runs'):.0f} runs caused {v('durable.chaos.in_doubt_attempts'):.0f} re-run "
                 f"attempts ({v('durable.chaos.in_doubt_attempts') / v('durable.chaos.runs'):.3f} per run), "
                 f"{v('durable.chaos.completed_step_reexecutions'):.0f} completed steps executed again, and "
                 f"{v('durable.chaos.direct_duplicates'):.0f} duplicate publications when the side effect bypassed "
                 "the outbox.\n\n")
        header = ["Crash probability per step", *names]
        return chaos + "Expected cost relative to a crash-free run.\n\n" + _table(header, rows)

    def latency_md(self) -> str:
        parts = []
        for s in self.scenarios:
            if s.id == "support-cache-aligned":
                continue
            rows = [[item.label, item.system, f"{item.ms:,.1f} ms", f"`{item.measurement}`"] for item in s.task.latency]
            parts.append(f"**{s.task.title}**\n\n" + _table(["Step", "System", "Measured", "Input"], rows,
                                                             ["---", "---", "---:", "---"]))
        return "\n".join(parts)

    def measurements_md(self) -> str:
        rows = []
        for m in self.inputs.measurements:
            where = f"`{m.pointer}`" if m.pointer else ""
            if m.derive:
                where = (where + " " if where else "") + f"(derived: `{m.derive}`)"
            rows.append([f"`{m.id}`", f"{_num(m.value)} {m.unit}", m.description,
                         _source_link(self.manifest, m.repo, m.path), where])
        return _table(["Id", "Value", "What it is", "Source at pinned commit", "Pointer"], rows,
                      ["---", "---:", "---", "---", "---"])

    def assumptions_md(self) -> str:
        rows = [[f"`{a.id}`", f"{_num(a.value)} {a.unit}", a.rationale] for a in self.inputs.assumptions]
        return _table(["Id", "Value", "Why this value"], rows, ["---", "---:", "---"])

    # ------------------------------------------------------------------------------------------ outputs
    def to_json(self) -> dict[str, Any]:
        """Every number of the report."""
        return {
            "command": REPRODUCE,
            "price_tables": [t.model_dump() for t in self.inputs.price_tables],
            "routing_mix": {r: cost.routing_mix(self.inputs, r) for r in cost.ROUTERS},
            "scenarios": {
                s.id: {
                    "label": s.label,
                    "cache_hit_rate": s.cache_hit_rate,
                    "router": s.router,
                    "task": s.task.model_dump(mode="json"),
                    "by_price_table": {
                        t: {"usd": c.usd, "usd_per_1000": 1000 * c.usd, "usd_per_success": c.usd_per_success,
                            "billed_calls": c.billed_calls, "input_tokens": c.input_tokens,
                            "output_tokens": c.output_tokens, "lines": [line.model_dump() for line in c.lines]}
                        for t, c in self.matrix[s.id].items()
                    },
                }
                for s in self.scenarios
            },
            "sensitivity": {
                "cache": {"price_table": ILLUSTRATIVE, "hit_rates": list(CACHE_POINTS), "usd_per_answer": self.cache},
                "reviewers": {"price_table": ILLUSTRATIVE, "tier": "large", "reviewers": list(cost.REVIEWER_COUNTS),
                              "by_accuracy": self.reviewers,
                              "baselines": {k: {"usd": c.usd, "usd_per_success": c.usd_per_success}
                                            for k, c in self.topologies.items()}},
                "crashes": {"price_table": ILLUSTRATIVE, "probabilities": list(CRASH_POINTS),
                            "cost_multiplier": self.crashes},
            },
            "measurements": [m.model_dump() for m in self.inputs.measurements],
            "assumptions": [a.model_dump() for a in self.inputs.assumptions],
        }

    def fragments(self) -> dict[str, str]:
        """Markdown fragments by file name."""
        return {
            "price_tables.md": self.price_tables_md(),
            "headline.md": self.headline_md(),
            "breakdown.md": self.breakdown_md(),
            "cache.md": self.cache_md(),
            "reviewers.md": self.reviewers_md(),
            "crashes.md": self.crashes_md(),
            "latency.md": self.latency_md(),
            "measurements.md": self.measurements_md(),
            "assumptions.md": self.assumptions_md(),
        }

    def write(self, results_dir: Path, chart_dir: Path | None) -> list[Path]:
        """Write JSON, Markdown and (optionally) charts; return the paths written."""
        fragment_dir = results_dir / "cost"
        fragment_dir.mkdir(parents=True, exist_ok=True)
        written = []
        fragments = self.fragments()
        for name, text in fragments.items():
            path = fragment_dir / name
            path.write_text(text, encoding="utf-8", newline="\n")
            written.append(path)
        titles = {
            "price_tables.md": "Price tables (USD per million tokens)", "headline.md": "Cost per task",
            "breakdown.md": "Breakdown (gateway illustrative prices)", "cache.md": "Sensitivity: cache hit rate",
            "reviewers.md": "Sensitivity: reviewers", "crashes.md": "Sensitivity: crashes",
            "latency.md": "Measured non-LLM latency on each path", "measurements.md": "Measured inputs",
            "assumptions.md": "Assumptions",
        }
        body = "\n".join(f"## {titles[name]}\n\n{text}" for name, text in fragments.items())
        summary = results_dir / "cost_model.md"
        summary.write_text(
            f"# Cost-per-task model\n\nReproduce: `{REPRODUCE}`. Every number below is computed from "
            "`bench/cost_inputs.yaml`: measurements read from the repositories at their pinned commits, and "
            "assumptions stated with their reasons. Prices are illustrative, not quotes.\n\n" + body,
            encoding="utf-8", newline="\n")
        data = results_dir / "cost_model.json"
        data.write_text(json.dumps(self.to_json(), indent=2) + "\n", encoding="utf-8", newline="\n")
        written += [summary, data]
        if chart_dir is not None:
            written += self.write_charts(chart_dir)
        return written

    def write_charts(self, chart_dir: Path) -> list[Path]:
        """Render the six charts."""
        table_labels = {t.id: t.label for t in self.inputs.price_tables}
        markers = {
            "support workload (measured)": self.inputs.value("gateway.support.hit_rate.exact_semantic"),
            "assistant workload (measured)": self.inputs.value("gateway.assistant.hit_rate.exact_semantic"),
        }
        breakdown = {s.id: self.matrix[s.id][ILLUSTRATIVE] for s in self.scenarios}
        return [
            charts.price_table_chart(self.matrix, self.labels, table_labels, chart_dir / "cost-by-price-table.png"),
            charts.cache_chart(self.cache_fine, self.cache_series, markers, ROUTER_LABELS,
                               chart_dir / "cost-cache-sensitivity.png"),
            charts.reviewers_chart(self.reviewers, self.topologies, chart_dir / "cost-reviewers.png"),
            charts.crash_chart(self.crash_fine, self.crash_series, chart_dir / "cost-crashes.png"),
            charts.breakdown_chart(breakdown, self.labels, chart_dir / "cost-breakdown.png"),
            charts.swarm_frontier_chart(self.swarm_points(), self.swarm_baselines(), chart_dir / "swarm-frontier.png"),
        ]

    def swarm_points(self) -> dict[str, list[tuple[int, float, float]]]:
        """Measured (reviewers, calls, success) per reviewer accuracy."""
        v = self.inputs.value
        return {f"{a}": [(n, v(f"swarm.r{n}.a{a}.calls"), v(f"swarm.r{n}.a{a}.success")) for n in cost.REVIEWER_COUNTS]
                for a in cost.REVIEWER_ACCURACIES}

    def swarm_baselines(self) -> dict[str, tuple[float, float]]:
        """Measured (calls, success) of the single-coder and coder + executor topologies."""
        v = self.inputs.value
        return {"single": (v("swarm.single.calls"), v("swarm.single.success")),
                "coder-executor": (v("swarm.coder_executor.calls"), v("swarm.coder_executor.success"))}
