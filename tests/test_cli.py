from __future__ import annotations

from pathlib import Path

import pytest

from teardown.cli import build_parser, main


def test_cost_command_prints_without_writing(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["cost", "--no-write"]) == 0
    out = capsys.readouterr().out
    assert "Support answer" in out and "per correct solution" in out


def test_manifest_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["manifest"]) == 0
    assert "trajectory-eval-gate" in capsys.readouterr().out


def test_bench_dry_run_prints_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["bench", "--dry-run", "--only", "trajectory-eval-gate,hybrid-rerank-retrieval"]) == 0
    out = capsys.readouterr().out
    assert "git clone https://github.com/iamsammy-ak/trajectory-eval-gate.git" in out
    assert "git clone https://github.com/iamsammy-ak/hybrid-rerank-retrieval.git" in out
    assert 'pip install -e ".[dev]"' in out  # rich markup must not swallow the extras


def test_bench_with_an_empty_selection_fails(tmp_path: Path) -> None:
    # GraphRAG's full mode needs model weights, so --model-free selects nothing
    code = main(["bench", "--full", "--model-free", "--only", "graphrag-knowledge-pipeline", "--dry-run",
                 "--out", str(tmp_path)])
    assert code == 1


def test_verify_sources_reports_missing_local_clones(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["verify-sources", "--local", str(tmp_path)]) == 1
    assert "MISMATCH" in capsys.readouterr().out


def test_fast_and_full_are_exclusive() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["bench", "--fast", "--full"])
