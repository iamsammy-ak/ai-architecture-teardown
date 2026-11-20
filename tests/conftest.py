"""Shared fixtures. Nothing in the suite calls a model or the network."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from hypothesis.configuration import set_hypothesis_home_dir

os.environ.setdefault("MPLBACKEND", "Agg")
# Keep Hypothesis's example database and caches out of the repository.
set_hypothesis_home_dir(str(Path(tempfile.gettempdir()) / "teardown-hypothesis"))


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force offline mode even when keys are set in the developer's environment."""
    for name in [n for n in os.environ if n.endswith("_API_KEY")] + ["OPENROUTER_MODELS", "HF_TOKEN"]:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(scope="session")
def manifest():
    from teardown.manifest import load_manifest

    return load_manifest()


@pytest.fixture(scope="session")
def inputs():
    from teardown.inputs import load_inputs

    return load_inputs()
