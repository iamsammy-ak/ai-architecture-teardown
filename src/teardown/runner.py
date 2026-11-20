"""Reproduce the benchmarks of the pinned repositories.

For each selected repository: clone it at the pinned commit into a temporary directory, create a fresh virtual
environment, install it, run the chosen mode's benchmark commands with API keys removed from the environment, then
collect the declared result files and compare their headline numbers with the versions committed at that commit.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .manifest import Manifest, Mode, RepoSpec
from .sources import SourceError, resolve_pointer

Status = Literal["passed", "failed", "skipped"]
#: Environment variables removed before any benchmark runs, so nothing can call a paid model: every ``*_API_KEY``
#: plus these.
SECRET_VARS = ("OPENROUTER_API_KEY", "OPENROUTER_MODELS", "HF_TOKEN")


class StepResult(BaseModel):
    """One command the runner executed."""

    model_config = ConfigDict(frozen=True)

    phase: Literal["clone", "venv", "install", "benchmark"]
    command: str
    returncode: int
    seconds: float


class ResultFile(BaseModel):
    """A declared result file after the run."""

    model_config = ConfigDict(frozen=True)

    path: str
    exists: bool
    bytes: int = 0
    sha256: str | None = None
    changed: bool | None = None


class HeadlineValue(BaseModel):
    """A headline number from the fresh run next to the committed one."""

    model_config = ConfigDict(frozen=True)

    label: str
    file: str
    pointer: str
    fresh: float | None
    committed: float | None

    @property
    def delta(self) -> float | None:
        """Fresh minus committed, when both exist."""
        if self.fresh is None or self.committed is None:
            return None
        return self.fresh - self.committed


class RunRecord(BaseModel):
    """The outcome of reproducing one repository's benchmark."""

    model_config = ConfigDict(frozen=True)

    repo: str
    commit: str | None
    mode: Mode
    status: Status
    reason: str = ""
    started: str
    seconds: float = 0.0
    python: str = ""
    comparable: bool = False
    steps: list[StepResult] = []
    files: list[ResultFile] = []
    headline: list[HeadlineValue] = []
    log_tail: list[str] = []


Executor = Callable[[list[str], Path, dict[str, str], float, Path], int]


def run_logged(argv: list[str], cwd: Path, env: dict[str, str], timeout: float, log: Path) -> int:
    """Run a command, appending its output to ``log``; return the exit code (124 on timeout)."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("ab") as fh:
        fh.write(f"\n$ {shlex.join(argv)}\n".encode())
        fh.flush()
        try:
            proc = subprocess.run(argv, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout,
                                  check=False)
        except subprocess.TimeoutExpired:
            fh.write(f"\n[teardown] timed out after {timeout:.0f} s\n".encode())
            return 124
        except OSError as exc:
            fh.write(f"\n[teardown] could not start: {exc}\n".encode())
            return 127
    return proc.returncode


@dataclass
class RunOptions:
    """How to run the selected benchmarks."""

    mode: Mode = "fast"
    workdir: Path | None = None
    keep: bool = False
    clone_from: Path | None = None
    python: str = sys.executable
    use_venv: bool = True
    timeout_factor: float = 4.0
    collect_dir: Path | None = None


def venv_bin(venv: Path) -> Path:
    """The directory holding a virtual environment's executables."""
    return venv / ("Scripts" if os.name == "nt" else "bin")


def resolve_command(command: str, python: str, bin_dir: Path | None) -> list[str]:
    """Split a manifest command and point ``python``, ``pip`` and console scripts at the right environment."""
    argv = shlex.split(command)
    if not argv:
        raise ValueError("empty command")
    head = argv[0]
    if head == "python":
        return [python, *argv[1:]]
    if head == "pip":
        return [python, "-m", "pip", *argv[1:]]
    if bin_dir is not None:
        for suffix in (".exe", ""):
            candidate = bin_dir / f"{head}{suffix}"
            if candidate.exists():
                return [str(candidate), *argv[1:]]
    found = shutil.which(head)
    return [found or head, *argv[1:]]


def benchmark_env(repo: RepoSpec, bin_dir: Path | None, base: dict[str, str] | None = None) -> dict[str, str]:
    """Environment for install and benchmark commands: no API keys, UTF-8 output, the venv first on PATH."""
    env = dict(os.environ if base is None else base)
    for name in [n for n in env if n.endswith("_API_KEY")] + list(SECRET_VARS):
        env.pop(name, None)
    env.update(repo.env)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    if bin_dir is not None:
        env["VIRTUAL_ENV"] = str(bin_dir.parent)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        env.pop("PYTHONHOME", None)
    return env


def read_number(text: str, pointer: str) -> float | None:
    """A number at a JSON pointer, or None when the file or key is missing or not numeric."""
    try:
        value = resolve_pointer(json.loads(text), pointer)
    except (json.JSONDecodeError, SourceError):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


class Runner:
    """Clone, install, run and collect, one repository at a time."""

    def __init__(self, manifest: Manifest, options: RunOptions, executor: Executor = run_logged,
                 git: Callable[[list[str], Path], subprocess.CompletedProcess[bytes]] | None = None) -> None:
        self.manifest = manifest
        self.options = options
        self.executor = executor
        self.git = git or (lambda args, cwd: subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False))

    def plan(self, repo: RepoSpec) -> list[tuple[str, str]]:
        """The (phase, command) pairs a run would execute, for ``--dry-run``."""
        mode = self.options.mode
        source = str(self.options.clone_from / repo.name) if self.options.clone_from else f"{repo.url}.git"
        steps = [("clone", f"git clone {source} && git checkout {repo.commit}")]
        if self.options.use_venv:
            steps.append(("venv", f"{self.options.python} -m venv .venv"))
            steps += [("install", c) for c in repo.install_for(mode)]
        steps += [("benchmark", c) for c in repo.mode(mode).commands]
        return steps

    def run(self, repo: RepoSpec) -> RunRecord:
        """Reproduce one repository's benchmark in the configured mode."""
        mode = self.options.mode
        started = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        if not repo.published or repo.commit is None:
            return RunRecord(repo=repo.name, commit=None, mode=mode, status="skipped", started=started,
                             reason="not published yet: no pinned commit")
        workdir = self.options.workdir or Path(tempfile.mkdtemp(prefix="teardown-"))
        base = workdir / f"{repo.name}-{repo.short_commit}-{mode}"
        if base.exists():
            shutil.rmtree(base, ignore_errors=True)
        base.mkdir(parents=True)
        clone, log = base / "src", base / "run.log"
        t0 = time.perf_counter()
        steps: list[StepResult] = []

        def fail(reason: str) -> RunRecord:
            return RunRecord(repo=repo.name, commit=repo.commit, mode=mode, status="failed", reason=reason,
                             started=started, seconds=round(time.perf_counter() - t0, 1), steps=steps,
                             log_tail=_tail(log))

        try:
            error = self._clone(repo, clone, steps)
            if error:
                return fail(error)
            python, bin_dir = self.options.python, None
            if self.options.use_venv:
                venv = base / "venv"
                code = self._step(steps, "venv", [self.options.python, "-m", "venv", str(venv)], clone,
                                  benchmark_env(repo, None), 300, log, display="python -m venv venv")
                if code != 0:
                    return fail("could not create the virtual environment")
                bin_dir = venv_bin(venv)
                python = str(bin_dir / ("python.exe" if os.name == "nt" else "python"))
            env = benchmark_env(repo, bin_dir)
            budget = repo.mode(mode).runtime_minutes * 60 * self.options.timeout_factor
            if self.options.use_venv:
                for command in repo.install_for(mode):
                    code = self._step(steps, "install", resolve_command(command, python, bin_dir), clone, env,
                                      1800, log, display=command)
                    if code != 0:
                        return fail(f"install failed: {command}")
            for command in repo.mode(mode).commands:
                code = self._step(steps, "benchmark", resolve_command(command, python, bin_dir), clone, env,
                                  budget, log, display=command)
                if code != 0:
                    return fail(f"benchmark command exited with {code}: {command}")
            files, headline = self._collect(repo, clone)
            missing = [f.path for f in files if not f.exists]
            status: Status = "failed" if missing else "passed"
            return RunRecord(
                repo=repo.name, commit=repo.commit, mode=mode, status=status,
                reason=f"missing result files: {', '.join(missing)}" if missing else "",
                started=started, seconds=round(time.perf_counter() - t0, 1),
                python=self._python_version(python, clone, env), comparable=repo.comparable(mode),
                steps=steps, files=files, headline=headline, log_tail=_tail(log) if missing else [],
            )
        finally:
            if not self.options.keep and self.options.workdir is None:
                shutil.rmtree(workdir, ignore_errors=True)

    # ------------------------------------------------------------------------------------------ helpers
    def _step(self, steps: list[StepResult], phase: Literal["clone", "venv", "install", "benchmark"],
              argv: list[str], cwd: Path, env: dict[str, str], timeout: float, log: Path, *, display: str) -> int:
        """Run one command; the record keeps the manifest's spelling, never machine-specific paths."""
        t = time.perf_counter()
        code = self.executor(argv, cwd, env, timeout, log)
        steps.append(StepResult(phase=phase, command=display, returncode=code,
                                seconds=round(time.perf_counter() - t, 1)))
        return code

    def _clone(self, repo: RepoSpec, clone: Path, steps: list[StepResult]) -> str | None:
        assert repo.commit is not None
        source = str(self.options.clone_from / repo.name) if self.options.clone_from else f"{repo.url}.git"
        t = time.perf_counter()
        proc = self.git(["clone", "--quiet", source, str(clone)], clone.parent)
        shown = f"{repo.url}.git" if self.options.clone_from is None else f"<mirror>/{repo.name}"
        steps.append(StepResult(phase="clone", command=f"git clone {shown}", returncode=proc.returncode,
                                seconds=round(time.perf_counter() - t, 1)))
        if proc.returncode != 0:
            return f"git clone failed: {proc.stderr.decode(errors='replace').strip()}"
        proc = self.git(["checkout", "--quiet", "--detach", repo.commit], clone)
        if proc.returncode != 0:
            return f"commit {repo.short_commit} not found: {proc.stderr.decode(errors='replace').strip()}"
        head = self.git(["rev-parse", "HEAD"], clone).stdout.decode().strip()
        if head != repo.commit:
            return f"checked out {head[:7]} instead of {repo.short_commit}"
        return None

    def _committed(self, repo: RepoSpec, clone: Path, path: str) -> str | None:
        proc = self.git(["show", f"{repo.commit}:{path}"], clone)
        return proc.stdout.decode("utf-8") if proc.returncode == 0 else None

    def _collect(self, repo: RepoSpec, clone: Path) -> tuple[list[ResultFile], list[HeadlineValue]]:
        mode = self.options.mode
        files = []
        for path in repo.results_for(mode):
            target = clone / path
            if not target.is_file():
                files.append(ResultFile(path=path, exists=False))
                continue
            data = target.read_bytes()
            committed = self._committed(repo, clone, path)
            files.append(ResultFile(path=path, exists=True, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                                    changed=None if committed is None else committed.encode() != data))
            if self.options.collect_dir is not None:
                dest = self.options.collect_dir / repo.name / mode / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
        headline = []
        for h in repo.headline_for(mode):
            target = clone / h.file
            fresh = read_number(target.read_text(encoding="utf-8"), h.pointer) if target.is_file() else None
            committed_text = self._committed(repo, clone, h.file)
            committed_value = read_number(committed_text, h.pointer) if committed_text is not None else None
            headline.append(HeadlineValue(label=h.label, file=h.file, pointer=h.pointer, fresh=fresh,
                                          committed=committed_value))
        return files, headline

    @staticmethod
    def _python_version(python: str, cwd: Path, env: dict[str, str]) -> str:
        try:
            proc = subprocess.run([python, "--version"], cwd=cwd, env=env, capture_output=True, check=False,
                                  timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return (proc.stdout or proc.stderr).decode(errors="replace").strip()


def _tail(log: Path, lines: int = 25) -> list[str]:
    if not log.is_file():
        return []
    return log.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]


def select(manifest: Manifest, mode: Mode, only: Sequence[str] = (), model_free: bool = False) -> list[RepoSpec]:
    """Repositories to run: ``only`` (validated) or all, optionally just the model- and data-free ones."""
    repos = [manifest.get(name) for name in only] if only else list(manifest.repos)
    if model_free:
        repos = [r for r in repos if r.model_free(mode)]
    return repos


# ---------------------------------------------------------------------------------------------- summary


def merge_records(existing: Sequence[RunRecord], new: Sequence[RunRecord]) -> list[RunRecord]:
    """Keep the latest record per (repository, mode), in manifest-independent alphabetical order."""
    latest = {(r.repo, r.mode): r for r in existing}
    for record in new:
        latest[(record.repo, record.mode)] = record
    return [latest[key] for key in sorted(latest)]


def load_records(path: Path) -> list[RunRecord]:
    """Records from a summary JSON file (empty if it does not exist)."""
    if not path.is_file():
        return []
    return [RunRecord.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8"))["runs"]]


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4g}"


def summary_markdown(records: Sequence[RunRecord], manifest: Manifest) -> str:
    """The summary table plus one headline table per repository."""
    lines = [
        "| Repository | Commit | Mode | Status | Wall time | Python | Result files |",
        "|---|---|---|---|---:|---|---:|",
    ]
    for r in records:
        spec = manifest.get(r.repo)
        commit = f"[`{spec.short_commit}`]({spec.url}/tree/{r.commit})" if r.commit else "unpublished"
        icon = {"passed": "✅ passed", "failed": "❌ failed", "skipped": "⏭️ skipped"}[r.status]
        files = f"{sum(f.exists for f in r.files)} / {len(r.files)}" if r.files else "-"
        status = icon + (f" ({r.reason})" if r.reason else "")
        lines.append(f"| {r.repo} | {commit} | {r.mode} | {status} | {r.seconds:.0f} s | {r.python or '-'} | {files} |")
    parts = ["\n".join(lines) + "\n"]
    for r in records:
        if not r.headline:
            continue
        note = ("same settings as the committed results on a deterministic benchmark: fresh and committed values "
                "should agree" if r.comparable else "smaller settings or a non-deterministic benchmark, so fresh "
                "values are not expected to equal the committed full-mode values")
        rows = ["| Headline | Fresh run | Committed | Difference |", "|---|---:|---:|---:|"]
        rows += [f"| {h.label} | {_fmt(h.fresh)} | {_fmt(h.committed)} | {_fmt(h.delta)} |" for h in r.headline]
        parts.append(f"**{r.repo}** ({r.mode}; {note})\n\n" + "\n".join(rows) + "\n")
    return "\n".join(parts)


def write_summary(records: Sequence[RunRecord], manifest: Manifest, out_dir: Path) -> tuple[Path, Path]:
    """Write ``summary.json`` and ``summary.md`` under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "summary.json", out_dir / "summary.md"
    payload = {"command": "python -m teardown bench", "runs": [r.model_dump(mode="json") for r in records]}
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(summary_markdown(records, manifest), encoding="utf-8", newline="\n")
    return json_path, md_path


def manifest_markdown(manifest: Manifest) -> str:
    """A table of every repository's pinned commit, modes, runtimes and download needs."""
    rows = [
        "| Repository | Pinned commit | Fast mode | Full mode | Needs models | Needs data |",
        "|---|---|---|---|---|---|",
    ]
    for r in manifest.repos:
        commit = f"[`{r.short_commit}`]({r.url}/tree/{r.commit})" if r.commit else "not published yet"
        fast, full = r.mode("fast"), r.mode("full")
        cmd = "<br>".join(f"`{c}`" for c in fast.commands)
        models = ", ".join(m for m, s in (("fast", fast), ("full", full)) if s.needs_models) or "no"
        data = ", ".join(m for m, s in (("fast", fast), ("full", full)) if s.needs_data) or "no"
        rows.append(f"| [{r.name}]({r.url}) | {commit} | {cmd}<br>~{fast.runtime_minutes:g} min | "
                    f"~{full.runtime_minutes:g} min | {models} | {data} |")
    return "\n".join(rows) + "\n"
