from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from teardown.paths import project_root

ROOT = project_root()
DOCS = ROOT / "docs"
LINK = re.compile(r"https://github\.com/iamsammy-ak/([a-z0-9-]+)/(?:blob|tree)/([0-9a-f]{40})")
MADR_SECTIONS = ("## Context and problem statement", "## Decision drivers", "## Considered options",
                 "## Decision outcome", "### Consequences", "### Confirmation", "## Pros and cons of the options",
                 "## More information")
DEEP_DIVE_SECTIONS = ("## Problem", "## Architecture", "## Key mechanisms", "## Measured results", "## Trade-offs",
                      "## Failure modes", "## What I would change at scale")


class _Loader(yaml.SafeLoader):
    """Reads mkdocs.yml, ignoring the ``!!python/name`` tags MkDocs resolves itself."""


_Loader.add_multi_constructor("tag:yaml.org,2002:python/", lambda loader, suffix, node: None)


def _nav_files(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        return [f for item in node for f in _nav_files(item)]
    if isinstance(node, dict):
        return [f for value in node.values() for f in _nav_files(value)]
    return []


def test_every_page_is_in_the_navigation() -> None:
    config = yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=_Loader)
    nav = set(_nav_files(config["nav"]))
    pages = {p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*.md")}
    assert pages == nav


def test_every_repository_has_a_deep_dive_with_the_standard_sections(manifest) -> None:
    for repo in manifest.repos:
        page = (DOCS / "systems" / f"{repo.name}.md").read_text(encoding="utf-8")
        for heading in DEEP_DIVE_SECTIONS:
            assert heading in page, (repo.name, heading)
        assert "```mermaid" in page


def test_links_to_repositories_use_the_pinned_commits(manifest) -> None:
    commits = manifest.commits()
    seen = 0
    for path in [*DOCS.rglob("*.md"), ROOT / "README.md"]:
        for repo, sha in LINK.findall(path.read_text(encoding="utf-8")):
            assert repo in commits, (path.name, repo)
            assert commits[repo] == sha, f"{path.name} links {repo} at {sha[:7]}, pinned {str(commits[repo])[:7]}"
            seen += 1
    assert seen > 100


def test_adrs_follow_madr() -> None:
    adrs = sorted((DOCS / "adr").glob("0*.md"))
    assert 12 <= len(adrs) <= 16
    index = (DOCS / "adr" / "index.md").read_text(encoding="utf-8")
    for number, adr in enumerate(adrs, start=1):
        text = adr.read_text(encoding="utf-8")
        assert text.startswith(f"# ADR-{number:04d}: ")
        assert "- **Status:** accepted" in text
        for section in MADR_SECTIONS:
            assert section in text, (adr.name, section)
        assert adr.name in index


def test_snippets_and_images_exist() -> None:
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for snippet in re.findall(r'--8<-- "([^"]+)"', text):
            assert (ROOT / snippet).is_file(), (page.name, snippet)
        for image in re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", text):
            assert (page.parent / image).resolve().is_file(), (page.name, image)


@pytest.mark.docs
@pytest.mark.skipif(importlib.util.find_spec("material") is None, reason="mkdocs-material is not installed")
def test_site_builds_in_strict_mode(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--quiet", "--site-dir", str(tmp_path / "site")],
        cwd=ROOT, capture_output=True, text=True, timeout=300, env={**os.environ, "NO_MKDOCS_2_WARNING": "1"},
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    assert (tmp_path / "site" / "index.html").is_file()
