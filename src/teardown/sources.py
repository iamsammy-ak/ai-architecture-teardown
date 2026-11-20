"""Re-read every measured input of the cost model from its repository at the pinned commit.

A measurement names a file, a JSON pointer and optionally a derivation (for values that are computed from a file,
such as a mean over a JSONL log). Files are read either from local clones with ``git show <commit>:<path>`` or from
``raw.githubusercontent.com`` at the commit, so a value can never silently come from a newer version of a repository.
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from .inputs import CostInputs, Measurement
from .manifest import Manifest


class SourceError(RuntimeError):
    """A source file could not be read or does not contain what the input says."""


def resolve_pointer(document: Any, pointer: str) -> Any:
    """Resolve an RFC 6901 JSON pointer (``~1`` is ``/``, ``~0`` is ``~``)."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise SourceError(f"invalid JSON pointer {pointer!r}")
    current = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise SourceError(f"index {token!r} out of range in {pointer}")
            current = current[int(token)]
        elif isinstance(current, dict):
            if token not in current:
                raise SourceError(f"key {token!r} not found in {pointer}")
            current = current[token]
        else:
            raise SourceError(f"cannot descend into a {type(current).__name__} at {token!r} in {pointer}")
    return current


def histogram_mean(histogram: dict[str, float]) -> float:
    """Mean of a histogram whose keys are the integer values and whose values are counts."""
    total = sum(histogram.values())
    if total <= 0:
        raise SourceError("empty histogram")
    return sum(int(k) * v for k, v in histogram.items()) / total


def _jsonl(text: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _per_run_mean(text: str, value: Callable[[dict[str, Any]], float]) -> float:
    runs = _jsonl(text)
    if not runs:
        raise SourceError("no runs in the JSONL file")
    per_run = [sum(value(step) for step in run["steps"] if step.get("kind") == "llm") for run in runs]
    return sum(per_run) / len(per_run)


#: Derivations over a whole file (JSONL logs) or over the value at the pointer (``histogram_mean``).
FILE_DERIVATIONS: dict[str, Callable[[str], float]] = {
    "trajectory_llm_calls_per_run": lambda text: _per_run_mean(text, lambda step: 1.0),
    "trajectory_tokens_in_per_run": lambda text: _per_run_mean(text, lambda step: float(step.get("tokens_in", 0))),
    "trajectory_tokens_out_per_run": lambda text: _per_run_mean(text, lambda step: float(step.get("tokens_out", 0))),
}
VALUE_DERIVATIONS: dict[str, Callable[[Any], float]] = {"histogram_mean": histogram_mean}


def extract(measurement: Measurement, text: str) -> float:
    """Compute a measurement's value from the text of its source file."""
    if measurement.derive in FILE_DERIVATIONS:
        return FILE_DERIVATIONS[measurement.derive](text)
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceError(f"{measurement.path} is not JSON: {exc}") from exc
    value = resolve_pointer(document, measurement.pointer or "")
    if measurement.derive is not None:
        if measurement.derive not in VALUE_DERIVATIONS:
            raise SourceError(f"unknown derivation {measurement.derive!r}")
        return VALUE_DERIVATIONS[measurement.derive](value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SourceError(f"{measurement.pointer} is a {type(value).__name__}, not a number")
    return float(value)


def matches(expected: float, actual: float, tolerance: float | None = None) -> bool:
    """Equality up to the rounding used when a value was copied into the inputs file."""
    allowed = tolerance if tolerance is not None else max(5e-6, 1e-4 * abs(expected))
    return abs(actual - expected) <= allowed


class Fetcher(Protocol):
    """Reads one file of a repository at a commit."""

    def read(self, repo: str, commit: str, path: str) -> str:
        """Return the file's text."""
        ...


class LocalGitFetcher:
    """Reads files from local clones (``<root>/<repo>``) with ``git show <commit>:<path>``."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def read(self, repo: str, commit: str, path: str) -> str:
        """Return the file's text at the commit."""
        proc = subprocess.run(
            ["git", "-C", str(self.root / repo), "show", f"{commit}:{path}"],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise SourceError(f"git show {commit[:7]}:{path} failed in {repo}: {proc.stderr.decode(errors='replace')}")
        return proc.stdout.decode("utf-8")


class GitHubRawFetcher:
    """Reads files from raw.githubusercontent.com at the commit (needs network access)."""

    def __init__(self, owner: str, timeout: float = 30.0) -> None:
        self.owner = owner
        self.timeout = timeout

    def read(self, repo: str, commit: str, path: str) -> str:
        """Return the file's text at the commit."""
        url = f"https://raw.githubusercontent.com/{self.owner}/{repo}/{commit}/{urllib.parse.quote(path)}"
        request = urllib.request.Request(url, headers={"User-Agent": "teardown-verify-sources"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310 (fixed https host)
                return response.read().decode("utf-8")
        except OSError as exc:
            raise SourceError(f"could not fetch {url}: {exc}") from exc


class Check(BaseModel):
    """The outcome of re-reading one input from its source."""

    model_config = ConfigDict(frozen=True)

    id: str
    repo: str
    path: str
    expected: str
    actual: str
    ok: bool


class _CachedFetcher:
    def __init__(self, inner: Fetcher) -> None:
        self.inner = inner
        self.cache: dict[tuple[str, str, str], str] = {}

    def read(self, repo: str, commit: str, path: str) -> str:
        key = (repo, commit, path)
        if key not in self.cache:
            self.cache[key] = self.inner.read(repo, commit, path)
        return self.cache[key]


def verify_inputs(inputs: CostInputs, manifest: Manifest, fetcher: Fetcher) -> list[Check]:
    """Check every measurement and every repository price table against its source at the pinned commit."""
    cached = _CachedFetcher(fetcher)
    checks: list[Check] = []
    commits = manifest.commits()
    for m in inputs.measurements:
        commit = commits.get(m.repo)
        if commit is None:
            checks.append(Check(id=m.id, repo=m.repo, path=m.path, expected=f"{m.value:g}",
                                actual="repository not pinned", ok=False))
            continue
        try:
            actual = extract(m, cached.read(m.repo, commit, m.path))
            checks.append(Check(id=m.id, repo=m.repo, path=m.path, expected=f"{m.value:g}", actual=f"{actual:.6g}",
                                ok=matches(m.value, actual, m.tolerance)))
        except SourceError as exc:
            checks.append(Check(id=m.id, repo=m.repo, path=m.path, expected=f"{m.value:g}", actual=str(exc), ok=False))
    for table in inputs.price_tables:
        if table.source is None:
            continue
        src = table.source
        commit = commits.get(src.repo)
        try:
            if commit is None:
                raise SourceError("repository not pinned")
            text = cached.read(src.repo, commit, src.path)
            missing = [snippet for snippet in src.contains if snippet not in text]
            checks.append(Check(id=f"price:{table.id}", repo=src.repo, path=src.path,
                                expected=f"{len(src.contains)} snippets",
                                actual="all found" if not missing else f"missing {missing}", ok=not missing))
        except SourceError as exc:
            checks.append(Check(id=f"price:{table.id}", repo=src.repo, path=src.path,
                                expected=f"{len(src.contains)} snippets", actual=str(exc), ok=False))
    return checks
