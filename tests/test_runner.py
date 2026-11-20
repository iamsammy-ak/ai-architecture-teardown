from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from teardown.manifest import Manifest
from teardown.runner import (
    Runner,
    RunOptions,
    RunRecord,
    benchmark_env,
    load_records,
    manifest_markdown,
    merge_records,
    read_number,
    resolve_command,
    run_logged,
    select,
    summary_markdown,
    venv_bin,
    write_summary,
)

from .test_manifest import SHA, repo_dict

COMMITTED = {"benchmarks/results/out.json": json.dumps({"a": {"b": 0.75}})}


def make_manifest(**overrides: object) -> Manifest:
    return Manifest.model_validate({"version": 1, "owner": "o", "repos": [repo_dict(**overrides)]})


class FakeGit:
    """Simulates clone, checkout, rev-parse and show without touching the network."""

    def __init__(self, head: str = SHA, clone_ok: bool = True) -> None:
        self.head, self.clone_ok, self.calls = head, clone_ok, []

    def __call__(self, args: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
        self.calls.append(args)
        if args[0] == "clone":
            if not self.clone_ok:
                return subprocess.CompletedProcess(args, 128, b"", b"repository not found")
            Path(args[-1]).mkdir(parents=True)
            return subprocess.CompletedProcess(args, 0, b"", b"")
        if args[0] == "rev-parse":
            return subprocess.CompletedProcess(args, 0, (self.head + "\n").encode(), b"")
        if args[0] == "show":
            path = args[1].split(":", 1)[1]
            if path in COMMITTED:
                return subprocess.CompletedProcess(args, 0, COMMITTED[path].encode(), b"")
            return subprocess.CompletedProcess(args, 128, b"", b"no such path")
        return subprocess.CompletedProcess(args, 0, b"", b"")


class FakeExecutor:
    """Records commands; a benchmark command writes the result file with a chosen value."""

    def __init__(self, value: float = 0.8, fail_on: str | None = None, write: bool = True) -> None:
        self.value, self.fail_on, self.write, self.commands = value, fail_on, write, []

    def __call__(self, argv: list[str], cwd: Path, env: dict[str, str], timeout: float, log: Path) -> int:
        self.commands.append((argv, env, timeout))
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(" ".join(argv) + "\n")
        if self.fail_on and any(self.fail_on in part for part in argv):
            return 3
        if "bench.py" in " ".join(argv) and self.write:
            out = cwd / "benchmarks" / "results" / "out.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"a": {"b": self.value}}), encoding="utf-8")
        return 0


def run(tmp_path: Path, executor: FakeExecutor, git: FakeGit | None = None, mode: str = "fast",
        manifest: Manifest | None = None, use_venv: bool = True) -> RunRecord:
    manifest = manifest or make_manifest()
    options = RunOptions(mode=mode, workdir=tmp_path / "work", use_venv=use_venv, collect_dir=tmp_path / "collected")
    return Runner(manifest, options, executor=executor, git=git or FakeGit()).run(manifest.repos[0])


def test_successful_run_collects_files_and_compares_headlines(tmp_path: Path) -> None:
    record = run(tmp_path, FakeExecutor(value=0.8))
    assert record.status == "passed", record.reason
    assert [s.phase for s in record.steps] == ["clone", "venv", "install", "benchmark"]
    (headline,) = record.headline
    assert headline.fresh == pytest.approx(0.8) and headline.committed == pytest.approx(0.75)
    assert headline.delta == pytest.approx(0.05)
    assert record.files[0].exists and record.files[0].changed is True
    assert (tmp_path / "collected" / "demo-repo" / "fast" / "benchmarks" / "results" / "out.json").is_file()
    assert not record.comparable  # fast mode never claims comparability


def test_full_mode_of_a_deterministic_benchmark_is_comparable(tmp_path: Path) -> None:
    record = run(tmp_path, FakeExecutor(value=0.75), mode="full")
    assert record.comparable and record.headline[0].delta == 0
    assert record.files[0].changed is False


def test_install_runs_inside_the_new_venv_and_without_api_keys(tmp_path: Path,
                                                               monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "placeholder")
    executor = FakeExecutor()
    run(tmp_path, executor)
    venv_python = str(venv_bin(tmp_path / "work" / f"demo-repo-{SHA[:7]}-fast" / "venv")
                      / ("python.exe" if os.name == "nt" else "python"))
    install_argv, env, _ = executor.commands[1]
    assert install_argv[:3] == [venv_python, "-m", "pip"]
    assert "OPENROUTER_API_KEY" not in env
    bench_argv, _, timeout = executor.commands[2]
    assert bench_argv[0] == venv_python and timeout == pytest.approx(1 * 60 * 4.0)


def test_failures_are_reported_with_a_reason_and_log_tail(tmp_path: Path) -> None:
    record = run(tmp_path, FakeExecutor(fail_on="pip"))
    assert record.status == "failed" and record.reason.startswith("install failed")
    assert record.log_tail
    record = run(tmp_path, FakeExecutor(fail_on="bench.py"))
    assert record.status == "failed" and "exited with 3" in record.reason
    record = run(tmp_path, FakeExecutor(write=False))
    assert record.status == "failed" and "missing result files" in record.reason


def test_clone_problems_fail_early(tmp_path: Path) -> None:
    executor = FakeExecutor()
    record = run(tmp_path, executor, git=FakeGit(clone_ok=False))
    assert record.status == "failed" and "git clone failed" in record.reason
    record = run(tmp_path, executor, git=FakeGit(head="c" * 40))
    assert record.status == "failed" and "instead of" in record.reason


def test_unpublished_repositories_are_skipped(tmp_path: Path) -> None:
    record = run(tmp_path, FakeExecutor(), manifest=make_manifest(commit=None, published=False))
    assert record.status == "skipped" and record.commit is None


def test_no_venv_mode_uses_the_given_interpreter(tmp_path: Path) -> None:
    executor = FakeExecutor()
    record = run(tmp_path, executor, use_venv=False)
    assert record.status == "passed"
    assert [s.phase for s in record.steps] == ["clone", "benchmark"]
    assert executor.commands[0][0][0] == sys.executable


def test_resolve_command(tmp_path: Path) -> None:
    assert resolve_command("python x.py --a 1", "/py", None) == ["/py", "x.py", "--a", "1"]
    assert resolve_command('pip install -e ".[dev]"', "/py", None) == ["/py", "-m", "pip", "install", "-e", ".[dev]"]
    (tmp_path / "graphrag").write_text("", encoding="utf-8")
    assert resolve_command("graphrag bench", "/py", tmp_path) == [str(tmp_path / "graphrag"), "bench"]
    assert resolve_command("surely-not-a-command-xyz run", "/py", None)[0] == "surely-not-a-command-xyz"
    with pytest.raises(ValueError):
        resolve_command("   ", "/py", None)


def test_benchmark_env_strips_secrets_and_puts_the_venv_first(tmp_path: Path) -> None:
    manifest = make_manifest(env={"PYTHONPATH": "src"})
    env = benchmark_env(manifest.repos[0], tmp_path, {"OPENAI_API_KEY": "x", "PATH": "/usr/bin", "HOME": "/h"})
    assert "OPENAI_API_KEY" not in env and env["PYTHONPATH"] == "src"
    assert env["PATH"].startswith(str(tmp_path)) and env["VIRTUAL_ENV"] == str(tmp_path.parent)
    assert env["PYTHONIOENCODING"] == "utf-8"


def test_read_number() -> None:
    assert read_number('{"a": [1, 2.5]}', "/a/1") == 2.5
    assert read_number('{"a": true}', "/a") is None
    assert read_number('{"a": "x"}', "/a") is None
    assert read_number("not json", "/a") is None
    assert read_number('{"a": 1}', "/b") is None


def test_select(manifest) -> None:
    assert [r.name for r in select(manifest, "fast", ["trajectory-eval-gate"])] == ["trajectory-eval-gate"]
    free = select(manifest, "fast", model_free=True)
    assert all(r.model_free("fast") for r in free)
    assert len(select(manifest, "full", model_free=True)) < len(free)
    with pytest.raises(KeyError):
        select(manifest, "fast", ["nope"])


def test_dry_run_plan(manifest) -> None:
    repo = manifest.get("trajectory-eval-gate")
    plan = Runner(manifest, RunOptions(mode="fast")).plan(repo)
    assert plan[0][0] == "clone" and repo.commit in plan[0][1]
    assert [p for p, _ in plan] == ["clone", "venv", "install", "benchmark"]
    no_venv = Runner(manifest, RunOptions(mode="fast", use_venv=False, clone_from=Path("mirrors"))).plan(repo)
    assert [p for p, _ in no_venv] == ["clone", "benchmark"] and "mirrors" in no_venv[0][1]


def test_summary_merge_write_and_reload(tmp_path: Path) -> None:
    manifest = make_manifest()
    first = run(tmp_path, FakeExecutor(value=0.8))
    later = run(tmp_path, FakeExecutor(value=0.9))
    merged = merge_records([first], [later])
    assert len(merged) == 1 and merged[0].headline[0].fresh == pytest.approx(0.9)
    json_path, md_path = write_summary(merged, manifest, tmp_path / "out")
    assert load_records(json_path)[0] == merged[0]
    text = md_path.read_text(encoding="utf-8")
    assert "demo-repo" in text and "passed" in text and "0.9" in text
    assert load_records(tmp_path / "missing.json") == []
    assert "not expected to equal" in summary_markdown(merged, manifest)
    assert "work" not in json_path.read_text(encoding="utf-8")  # no machine-specific paths in records


def test_manifest_markdown_lists_every_repository(manifest) -> None:
    text = manifest_markdown(manifest)
    for repo in manifest.repos:
        assert repo.name in text and repo.short_commit in text


def test_run_logged_runs_real_commands_and_enforces_timeouts(tmp_path: Path) -> None:
    log = tmp_path / "log.txt"
    code = run_logged([sys.executable, "-c", "print('hello')"], tmp_path, dict(os.environ), 60, log)
    assert code == 0 and "hello" in log.read_text(encoding="utf-8")
    code = run_logged([sys.executable, "-c", "import time; time.sleep(5)"], tmp_path, dict(os.environ), 0.5, log)
    assert code == 124 and "timed out" in log.read_text(encoding="utf-8")
    assert run_logged(["surely-not-a-command-xyz"], tmp_path, dict(os.environ), 5, log) == 127


def test_any_api_key_is_removed_whatever_its_provider(tmp_path: Path) -> None:
    env = benchmark_env(make_manifest().repos[0], None, {"SOME_VENDOR_API_KEY": "x", "OPENROUTER_MODELS": "m",
                                                         "PATH": "/usr/bin"})
    assert "SOME_VENDOR_API_KEY" not in env and "OPENROUTER_MODELS" not in env
    assert env["PATH"] == "/usr/bin" and "VIRTUAL_ENV" not in env
