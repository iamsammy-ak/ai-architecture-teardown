"""Matplotlib charts for the cost model (white background, fixed categorical colour order)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .cost import REVIEWER_COUNTS, TaskCost

# Categorical slots in fixed order (never cycled), neutral ink for text, a recessive grid.
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BASELINE_LABELS = {"single": "single coder", "coder-executor": "coder + executor"}


def _style() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "font.size": 10,
    })


def _save(fig: object, path: Path) -> Path:
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")  # type: ignore[attr-defined]
    plt.close(fig)  # type: ignore[arg-type]
    return path


def price_table_chart(matrix: dict[str, dict[str, TaskCost]], labels: dict[str, str], table_labels: dict[str, str],
                      path: Path) -> Path:
    """Grouped horizontal bars: USD per task for every headline scenario under every price table (log scale)."""
    _style()
    import matplotlib.pyplot as plt

    scenarios = list(matrix)
    tables = list(next(iter(matrix.values())))
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    height = 0.8 / len(tables)
    for j, table in enumerate(tables):
        ys = [i + (j - (len(tables) - 1) / 2) * height for i in range(len(scenarios))]
        values = [matrix[s][table].usd for s in scenarios]
        ax.barh(ys, values, height=height * 0.88, color=SERIES[j], label=table_labels[table])
        for y, value in zip(ys, values, strict=True):
            ax.text(value * 1.06, y, f"${value:.4f}", va="center", fontsize=7.5, color=INK_2)
    ax.set_yticks(range(len(scenarios)), [labels[s] for s in scenarios])
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(right=max(m.usd for row in matrix.values() for m in row.values()) * 3)
    ax.set_xlabel("USD per task (log scale)")
    ax.set_title("Cost per task under each price table")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
    return _save(fig, path)


def cache_chart(hit_rates: Sequence[float], series: dict[str, list[float]], markers: dict[str, float],
                router_labels: dict[str, str], path: Path) -> Path:
    """USD per 1,000 support answers against the cache hit rate, one line per routing policy."""
    _style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    xs = [100 * h for h in hit_rates]
    for k, (router, values) in enumerate(series.items()):
        ys = [1000 * v for v in values]
        ax.plot(xs, ys, color=SERIES[k], linewidth=2, label=router_labels[router])
    for label, rate in markers.items():
        ax.axvline(100 * rate, color=INK_2, linewidth=1, linestyle="--")
        ax.text(100 * rate + 0.6, ax.get_ylim()[1] * 0.95, label, fontsize=8, color=INK_2, va="top", rotation=90)
    ax.set_xlim(0, xs[-1])
    ax.set_ylim(bottom=0)
    ax.set_xlabel("cache hit rate (%)")
    ax.set_ylabel("USD per 1,000 answers")
    ax.set_title("Support answer: cache hit rate and routing policy")
    ax.legend(loc="upper right")
    return _save(fig, path)


def reviewers_chart(sweep: dict[str, dict[str, list[float]]], baselines: dict[str, TaskCost], path: Path) -> Path:
    """Two panels: USD per task and USD per correct solution against the number of reviewers."""
    _style()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=False)
    for ax, metric, title in ((axes[0], "usd", "USD per task"),
                              (axes[1], "usd_per_success", "USD per correct accepted solution")):
        for k, (accuracy, values) in enumerate(sweep.items()):
            ax.plot(REVIEWER_COUNTS, values[metric], color=SERIES[k], linewidth=2, marker="o", markersize=7,
                    label=f"reviewer accuracy {accuracy}")
        for style, (name, cost) in zip(("--", ":"), baselines.items(), strict=False):
            value = cost.usd if metric == "usd" else (cost.usd_per_success or 0.0)
            ax.axhline(value, color=INK_2, linewidth=1.4, linestyle=style, label=BASELINE_LABELS.get(name, name))
        ax.set_xticks(REVIEWER_COUNTS)
        ax.set_xlabel("reviewers")
        ax.set_title(title)
        ax.set_ylim(bottom=0)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Coding task through the swarm (large tier, gateway illustrative prices)", fontsize=11, color=INK)
    return _save(fig, path)


def crash_chart(probabilities: Sequence[float], series: dict[str, list[float]], path: Path) -> Path:
    """Expected cost multiplier against the per-step crash probability, durable versus restart.

    Resuming from the journal costs 1 / (1 - p) whatever the workflow's length, so the durable series coincide and
    are drawn once.
    """
    _style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    xs = [100 * p for p in probabilities]
    durable = next(values for name, values in series.items() if "durable" in name)
    restarts = [(name, values) for name, values in series.items() if "restart" in name]
    ax.plot(xs, durable, color=SERIES[0], linewidth=2, label="durable: resume from the journal (any length)")
    for k, (name, values) in enumerate(restarts):
        label = ("restart from scratch: research workflow (5 steps)" if name.startswith("research")
                 else f"restart from scratch: {name.split(',')[0]}, equal cost")
        ax.plot(xs, values, color=SERIES[1 + k], linewidth=2, label=label)
    ax.set_yscale("log")
    ax.set_xlim(0, xs[-1])
    ax.set_xlabel("probability that a step attempt crashes (%)")
    ax.set_ylabel("expected cost / crash-free cost (log)")
    ax.set_title("What a crash costs: resume from the journal or restart from scratch")
    ax.legend(loc="upper left")
    return _save(fig, path)


def breakdown_chart(costs: dict[str, TaskCost], labels: dict[str, str], path: Path) -> Path:
    """100% stacked bars: each task's cost split by component, with the total in the label (one price table)."""
    _style()
    import matplotlib.pyplot as plt

    scenarios = list(costs)
    components: list[str] = []
    for cost in costs.values():
        for line in cost.lines:
            if line.component not in components:
                components.append(line.component)
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    lefts = [0.0] * len(scenarios)
    for k, component in enumerate(components):
        widths = [100 * sum(line.usd for line in costs[s].lines if line.component == component) / costs[s].usd
                  for s in scenarios]
        ax.barh(range(len(scenarios)), widths, left=lefts, color=SERIES[k % len(SERIES)], label=component,
                edgecolor="white", linewidth=2, height=0.62)
        lefts = [a + b for a, b in zip(lefts, widths, strict=True)]
    ax.set_yticks(range(len(scenarios)), [f"{labels[s]}\n${costs[s].usd:.4f} per task" for s in scenarios])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of the task's cost (%)")
    ax.set_title("Where the money goes (gateway illustrative prices)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=3, fontsize=8)
    return _save(fig, path)


def swarm_frontier_chart(points: dict[str, list[tuple[int, float, float]]], baselines: dict[str, tuple[float, float]],
                         path: Path) -> Path:
    """Measured share of tasks ending correct against agent calls per task, one line per reviewer accuracy.

    ``points`` maps an accuracy label to (reviewers, calls, success) triples; ``baselines`` maps a topology name to
    (calls, success).
    """
    _style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for k, (accuracy, triples) in enumerate(points.items()):
        xs = [t[1] for t in triples]
        ys = [100 * t[2] for t in triples]
        ax.plot(xs, ys, color=SERIES[k], linewidth=2, marker="o", markersize=7, label=f"reviewer accuracy {accuracy}")
    for marker, (name, (calls, success)) in zip(("s", "D"), baselines.items(), strict=False):
        ax.plot([calls], [100 * success], marker=marker, markersize=8, color=INK_2, linestyle="none",
                label=BASELINE_LABELS.get(name, name))
    ax.set_xlabel("agent calls per task (measured)")
    ax.set_ylabel("tasks ending with a correct accepted solution (%)")
    ax.set_title("Typed swarm: correctness bought per agent call (points: 1, 3, 5 reviewers)")
    ax.set_ylim(55, 100)
    ax.set_xlim(left=0)
    ax.legend(loc="lower right", fontsize=8)
    return _save(fig, path)
