from __future__ import annotations

import json
from pathlib import Path

import pytest

from teardown.paths import project_root
from teardown.report import CostReport, usd

RESULTS = project_root() / "bench" / "results"


@pytest.fixture(scope="module")
def report(inputs, manifest) -> CostReport:
    return CostReport(inputs, manifest)


def test_committed_tables_match_the_inputs(report: CostReport) -> None:
    """The Markdown fragments the site includes must be exactly what the current inputs produce."""
    for name, text in report.fragments().items():
        committed = (RESULTS / "cost" / name).read_text(encoding="utf-8")
        assert committed == text, f"bench/results/cost/{name} is stale: run python -m teardown cost"


def test_committed_json_matches_the_inputs(report: CostReport) -> None:
    committed = json.loads((RESULTS / "cost_model.json").read_text(encoding="utf-8"))
    fresh = json.loads(json.dumps(report.to_json()))
    assert committed == fresh


def test_every_measurement_links_to_its_pinned_commit(report: CostReport, manifest) -> None:
    text = report.measurements_md()
    for m in report.inputs.measurements:
        assert manifest.get(m.repo).blob_url(m.path) in text


def test_breakdown_lists_the_inputs_used_by_every_call(report: CostReport) -> None:
    text = report.breakdown_md()
    for scenario in report.scenarios:
        for call in scenario.task.calls:
            for key in call.basis:
                assert f"`{key}`" in text
                report.inputs.value(key)  # every basis id resolves to a measurement or an assumption


def test_write_produces_tables_json_and_charts(report: CostReport, tmp_path: Path) -> None:
    written = report.write(tmp_path / "results", tmp_path / "charts")
    names = {p.name for p in written}
    assert {"cost_model.md", "cost_model.json", "headline.md"} <= names
    charts = sorted((tmp_path / "charts").glob("*.png"))
    assert len(charts) == 6
    for chart in charts:
        assert 10_000 < chart.stat().st_size < 300_000, chart.name
    assert "Reproduce" in (tmp_path / "results" / "cost_model.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "value,expected",
    [(0, "$0"), (0.00285, "$0.00285"), (0.0599, "$0.0599"), (2.85, "$2.85"), (299.49, "$299"), (1234.5, "$1,234")],
)
def test_usd_formatting(value: float, expected: str) -> None:
    assert usd(value) == expected
