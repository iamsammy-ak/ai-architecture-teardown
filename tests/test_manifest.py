from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from teardown.manifest import Manifest, RepoSpec

SHA = "a" * 40


def repo_dict(**overrides: object) -> dict:
    base = {
        "name": "demo-repo",
        "title": "Demo",
        "summary": "A demo.",
        "commit": SHA,
        "published": True,
        "install": ['python -m pip install -e ".[dev]"'],
        "deterministic": True,
        "modes": {
            "fast": {"commands": ["python bench.py --fast"], "runtime_minutes": 1},
            "full": {"commands": ["python bench.py"], "runtime_minutes": 5, "needs_models": True},
        },
        "results": ["benchmarks/results/out.json"],
        "headline": [{"label": "metric", "file": "benchmarks/results/out.json", "pointer": "/a/b"}],
    }
    base.update(overrides)
    return base


def test_real_manifest_lists_eleven_repositories(manifest) -> None:
    assert len(manifest.repos) == 11
    assert all(r.published for r in manifest.repos)


def test_pinned_commits_match_the_published_versions(manifest) -> None:
    expected = {
        "context-assembler-engine": "1f7863c", "graphrag-knowledge-pipeline": "21dc6d1",
        "self-correcting-agentic-rag": "e84144b", "durable-agent-state-machine": "5facc0f",
        "raw-mcp-tool-server": "1cfc10e", "three-tier-agent-memory": "cf1aea0", "typed-multi-agent-swarm": "37b44ec",
        "trajectory-eval-gate": "3921cce", "inter-agent-security-proxy": "d2ad5b5", "semantic-cache-gateway": "b8b77e0",
        "hybrid-rerank-retrieval": "b43a6ec",
    }
    assert {r.name: r.short_commit for r in manifest.repos if r.published} == expected


def test_every_mode_declares_results_and_headlines_inside_them(manifest) -> None:
    for repo in manifest.repos:
        for mode in ("fast", "full"):
            files = repo.results_for(mode)
            assert files, repo.name
            assert all(h.file in files for h in repo.headline_for(mode))


def test_model_free_fast_modes_are_the_ones_ci_runs(manifest) -> None:
    free = {r.name for r in manifest.repos if r.published and r.model_free("fast")}
    assert "graphrag-knowledge-pipeline" not in free  # needs the spaCy pipeline
    assert {"durable-agent-state-machine", "trajectory-eval-gate", "typed-multi-agent-swarm"} <= free


def test_mode_overrides_fall_back_to_repository_values() -> None:
    data = repo_dict()
    data["modes"]["fast"]["results"] = ["benchmarks/results/fast.json"]
    data["modes"]["fast"]["headline"] = []
    data["modes"]["full"]["install"] = ["pip install -e .[models]"]
    repo = RepoSpec.model_validate(data)
    assert repo.results_for("fast") == ["benchmarks/results/fast.json"]
    assert repo.results_for("full") == ["benchmarks/results/out.json"]
    assert repo.headline_for("fast") == []
    assert repo.install_for("full") == ["pip install -e .[models]"]
    assert repo.install_for("fast") == data["install"]
    assert repo.model_free("fast") and not repo.model_free("full")


def test_blob_url_pins_the_commit_and_line_range() -> None:
    repo = RepoSpec.model_validate(repo_dict())
    url = repo.blob_url("src/x.py", (10, 20))
    assert url == f"https://github.com/iamsammy-ak/demo-repo/blob/{SHA}/src/x.py#L10-L20"
    unpublished = RepoSpec.model_validate(repo_dict(commit=None, published=False))
    assert unpublished.blob_url("README.md").endswith("/blob/main/README.md")
    assert unpublished.short_commit == "unpublished"


@pytest.mark.parametrize(
    "overrides",
    [
        {"commit": "abc123"},  # short SHA
        {"commit": None},  # published without a commit
        {"published": False},  # unpublished but pinned
        {"name": "Bad_Name"},
        {"results": ["/abs/path.json"]},
        {"results": ["../escape.json"]},
        {"results": ["C:\\win.json"]},
        {"headline": [{"label": "x", "file": "benchmarks/results/other.json", "pointer": "/a"}]},
        {"headline": [{"label": "x", "file": "benchmarks/results/out.json", "pointer": "a"}]},
        {"headline": [{"label": "x", "file": "benchmarks/results/out.md", "pointer": "/a"}]},
        {"install": []},
        {"unknown_field": 1},
    ],
)
def test_invalid_repository_specs_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        RepoSpec.model_validate(repo_dict(**overrides))


def test_both_modes_are_required() -> None:
    data = repo_dict()
    del data["modes"]["full"]
    with pytest.raises(ValidationError):
        RepoSpec.model_validate(data)


def test_duplicate_names_and_unknown_lookups() -> None:
    one = repo_dict()
    with pytest.raises(ValidationError):
        Manifest.model_validate({"version": 1, "owner": "o", "repos": [one, copy.deepcopy(one)]})
    manifest = Manifest.model_validate({"version": 1, "owner": "o", "repos": [one]})
    with pytest.raises(KeyError):
        manifest.get("nope")
    assert manifest.commits() == {"demo-repo": SHA}


def test_comparable_needs_determinism_and_the_full_settings(manifest) -> None:
    # trajectory-eval-gate's fast mode is its full benchmark, so even a fast run must reproduce the committed numbers
    assert manifest.get("trajectory-eval-gate").comparable("fast")
    assert not manifest.get("typed-multi-agent-swarm").comparable("fast")
    assert manifest.get("typed-multi-agent-swarm").comparable("full")
    assert not manifest.get("durable-agent-state-machine").comparable("full")  # timing-dependent chaos run
    # agentic RAG's fast mode is the committed hashing-backend benchmark
    assert manifest.get("self-correcting-agentic-rag").comparable("fast")
