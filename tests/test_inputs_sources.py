from __future__ import annotations

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from teardown.inputs import CostInputs, PriceTable
from teardown.sources import (
    SourceError,
    extract,
    histogram_mean,
    matches,
    resolve_pointer,
    verify_inputs,
)

SHA = "b" * 40


def test_every_measurement_points_at_a_pinned_repository(inputs, manifest) -> None:
    names = {r.name for r in manifest.repos if r.published}
    assert inputs.measurements and inputs.assumptions
    for m in inputs.measurements:
        assert m.repo in names, m.id
    for table in inputs.price_tables:
        assert (table.kind == "scenario") == (table.source is None)


def test_values_and_kinds(inputs) -> None:
    assert inputs.value("gateway.support.hit_rate.exact_semantic") == pytest.approx(0.47167)
    assert inputs.kind_of("gateway.support.requests") == "measured"
    assert inputs.kind_of("support.answer_tokens") == "assumed"
    with pytest.raises(KeyError):
        inputs.value("does.not.exist")
    with pytest.raises(KeyError):
        inputs.price_table("nope")


def test_price_table_cost_is_per_million_tokens(inputs) -> None:
    table = inputs.price_table("gateway-illustrative")
    assert table.cost("large", 1_000_000, 0) == pytest.approx(3.0)
    assert table.cost("small", 0, 1_000_000) == pytest.approx(0.40)
    assert table.cost("medium", 1000, 1000) == pytest.approx((600 + 2400) / 1_000_000)


@pytest.mark.parametrize(
    "table",
    [
        {"id": "t", "label": "T", "kind": "repo", "description": "d",
         "tiers": {t: {"input": 1, "output": 1} for t in ("small", "medium", "large")}},
        {"id": "t", "label": "T", "kind": "scenario", "description": "d",
         "source": {"repo": "r", "path": "p", "contains": ["x"]},
         "tiers": {t: {"input": 1, "output": 1} for t in ("small", "medium", "large")}},
        {"id": "t", "label": "T", "kind": "scenario", "description": "d",
         "tiers": {t: {"input": 1, "output": 1} for t in ("small", "large")}},
        {"id": "t", "label": "T", "kind": "scenario", "description": "d",
         "tiers": {t: {"input": -1, "output": 1} for t in ("small", "medium", "large")}},
    ],
)
def test_invalid_price_tables(table: dict) -> None:
    with pytest.raises(ValidationError):
        PriceTable.model_validate(table)


def test_duplicate_ids_are_rejected(inputs) -> None:
    data = inputs.model_dump()
    data["assumptions"].append(dict(data["assumptions"][0]))
    with pytest.raises(ValidationError):
        CostInputs.model_validate(data)


def test_a_measurement_needs_a_locator(inputs) -> None:
    data = inputs.model_dump()
    data["measurements"][0]["pointer"] = None
    with pytest.raises(ValidationError):
        CostInputs.model_validate(data)


def test_resolve_pointer_handles_escapes_lists_and_errors() -> None:
    doc = {"a/b": {"c~d": [10, {"e": 2.5}]}, "x": 1}
    assert resolve_pointer(doc, "/a~1b/c~0d/0") == 10
    assert resolve_pointer(doc, "/a~1b/c~0d/1/e") == 2.5
    assert resolve_pointer(doc, "") == doc
    for bad in ("/missing", "/a~1b/c~0d/9", "/x/y", "no-slash", "/a~1b/c~0d/first"):
        with pytest.raises(SourceError):
            resolve_pointer(doc, bad)


keys = st.text(alphabet=st.sampled_from("ab/~· c1"), min_size=1, max_size=6)


@given(path=st.lists(keys, min_size=1, max_size=4), value=st.integers())
def test_pointer_round_trip_with_any_key(path: list[str], value: int) -> None:
    doc: object = value
    for key in reversed(path):
        doc = {key: doc}
    pointer = "".join("/" + k.replace("~", "~0").replace("/", "~1") for k in path)
    assert resolve_pointer(doc, pointer) == value


def test_histogram_mean() -> None:
    assert histogram_mean({"0": 52, "1": 5, "2": 12}) == pytest.approx(29 / 69)
    with pytest.raises(SourceError):
        histogram_mean({})


def test_extract_from_json_jsonl_and_derivations(inputs) -> None:
    m = inputs.measurement("rag.rewrite_rounds_mean")
    assert extract(m, json.dumps({"test_rewrites": {"0": 1, "2": 1}})) == pytest.approx(1.0)
    runs = [
        {"steps": [{"kind": "llm", "tokens_in": 100, "tokens_out": 10}, {"kind": "tool"},
                   {"kind": "llm", "tokens_in": 300, "tokens_out": 30}]},
        {"steps": [{"kind": "llm", "tokens_in": 200, "tokens_out": 20}]},
    ]
    text = "\n".join(json.dumps(r) for r in runs) + "\n"
    assert extract(inputs.measurement("trajectory.run.tokens_in"), text) == pytest.approx(300)
    assert extract(inputs.measurement("trajectory.run.tokens_out"), text) == pytest.approx(30)
    assert extract(inputs.measurement("trajectory.run.llm_calls"), text) == pytest.approx(1.5)
    plain = inputs.measurement("memory.turns")
    assert extract(plain, json.dumps({"meta": {"turns": 7}})) == 7
    with pytest.raises(SourceError):
        extract(plain, json.dumps({"meta": {"turns": "seven"}}))
    with pytest.raises(SourceError):
        extract(plain, "not json")


def test_matches_tolerates_copy_rounding_only() -> None:
    assert matches(0.32233, 0.3223333333)
    assert matches(1660.368, 1660.3679306)
    assert not matches(0.32233, 0.3233)
    assert matches(1.65, 1.6537, tolerance=0.005)


class FakeFetcher:
    def __init__(self, files: dict[tuple[str, str], str]) -> None:
        self.files = files
        self.calls = 0

    def read(self, repo: str, commit: str, path: str) -> str:
        self.calls += 1
        if (repo, path) not in self.files:
            raise SourceError(f"no {path}")
        return self.files[(repo, path)]


def _small_inputs() -> CostInputs:
    return CostInputs.model_validate({
        "price_tables": [{"id": "p", "label": "P", "kind": "repo", "description": "d",
                          "source": {"repo": "demo-repo", "path": "prices.py", "contains": ["PRICE = 1"]},
                          "tiers": {t: {"input": 1, "output": 2} for t in ("small", "medium", "large")}}],
        "measurements": [
            {"id": "a", "value": 3, "unit": "u", "description": "d", "repo": "demo-repo", "path": "r.json",
             "pointer": "/a"},
            {"id": "b", "value": 4, "unit": "u", "description": "d", "repo": "demo-repo", "path": "r.json",
             "pointer": "/b"},
        ],
        "assumptions": [],
    })


def _manifest(commit: str | None = SHA):
    from teardown.manifest import Manifest

    from .test_manifest import repo_dict

    return Manifest.model_validate({"version": 1, "owner": "o",
                                    "repos": [repo_dict(commit=commit, published=commit is not None)]})


def test_verify_inputs_reports_matches_and_mismatches() -> None:
    fetcher = FakeFetcher({("demo-repo", "r.json"): json.dumps({"a": 3, "b": 5}),
                           ("demo-repo", "prices.py"): "PRICE = 1\n"})
    checks = {c.id: c for c in verify_inputs(_small_inputs(), _manifest(), fetcher)}
    assert checks["a"].ok and not checks["b"].ok and checks["price:p"].ok
    assert fetcher.calls == 2  # the results file is read once


def test_verify_inputs_flags_missing_files_snippets_and_unpinned_repos() -> None:
    checks = verify_inputs(_small_inputs(), _manifest(), FakeFetcher({("demo-repo", "prices.py"): "PRICE = 2"}))
    assert not any(c.ok for c in checks)
    unpinned = verify_inputs(_small_inputs(), _manifest(commit=None), FakeFetcher({}))
    assert all(not c.ok and "not pinned" in c.actual for c in unpinned)
