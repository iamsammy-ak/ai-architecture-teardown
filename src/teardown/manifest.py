"""The pinned benchmark manifest (``bench/manifest.yaml``): data model, loading and validation."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .paths import project_root

Mode = Literal["fast", "full"]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _relative_posix(value: str) -> str:
    """Reject absolute paths and parent references in repository-relative paths."""
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"expected a repository-relative POSIX path, got {value!r}")
    return value


class Headline(BaseModel):
    """One number read from a result file: what the summary table compares between a fresh and a committed run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1)
    file: str
    pointer: str

    @field_validator("file")
    @classmethod
    def _file(cls, value: str) -> str:
        if not value.endswith(".json"):
            raise ValueError("headline values are read from JSON result files")
        return _relative_posix(value)

    @field_validator("pointer")
    @classmethod
    def _pointer(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("a JSON pointer starts with '/'")
        return value


class ModeSpec(BaseModel):
    """How to run one benchmark mode. Unset fields fall back to the repository-level values."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    commands: list[str] = Field(min_length=1)
    runtime_minutes: float = Field(gt=0)
    install: list[str] | None = None
    needs_models: bool = False
    needs_data: bool = False
    matches_committed: bool = False
    """The committed result files of this mode were produced by exactly these commands."""
    results: list[str] | None = None
    headline: list[Headline] | None = None

    @field_validator("results")
    @classmethod
    def _results(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else [_relative_posix(v) for v in value]


class RepoSpec(BaseModel):
    """One repository of the teardown, pinned to a commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    title: str
    summary: str
    commit: str | None
    published: bool
    install: list[str] = Field(min_length=1)
    env: dict[str, str] = Field(default_factory=dict)
    downloads: list[str] = Field(default_factory=list)
    deterministic: bool
    modes: dict[Mode, ModeSpec]
    results: list[str] = Field(default_factory=list)
    headline: list[Headline] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        if not NAME_RE.match(value):
            raise ValueError(f"repository names are lower-case kebab-case, got {value!r}")
        return value

    @field_validator("results")
    @classmethod
    def _results(cls, value: list[str]) -> list[str]:
        return [_relative_posix(v) for v in value]

    @model_validator(mode="after")
    def _consistent(self) -> RepoSpec:
        if self.published and (self.commit is None or not SHA_RE.match(self.commit)):
            raise ValueError(f"{self.name}: a published repository needs a full 40-character commit SHA")
        if not self.published and self.commit is not None:
            raise ValueError(f"{self.name}: an unpublished repository cannot be pinned to a commit yet")
        if set(self.modes) != {"fast", "full"}:
            raise ValueError(f"{self.name}: both a 'fast' and a 'full' mode are required")
        for mode in self.modes:
            files = set(self.results_for(mode))
            if not files:
                raise ValueError(f"{self.name}/{mode}: no result files declared")
            for headline in self.headline_for(mode):
                if headline.file not in files:
                    raise ValueError(f"{self.name}/{mode}: headline file {headline.file} is not a declared result")
        return self

    @property
    def url(self) -> str:
        """Public clone URL."""
        return f"https://github.com/iamsammy-ak/{self.name}"

    @property
    def short_commit(self) -> str:
        """Seven-character commit, or ``unpublished``."""
        return self.commit[:7] if self.commit else "unpublished"

    def mode(self, mode: Mode) -> ModeSpec:
        """The spec of one mode."""
        return self.modes[mode]

    def install_for(self, mode: Mode) -> list[str]:
        """Install commands for a mode (mode override, else the repository default)."""
        return self.modes[mode].install or self.install

    def results_for(self, mode: Mode) -> list[str]:
        """Result files a mode writes."""
        return self.modes[mode].results or self.results

    def headline_for(self, mode: Mode) -> list[Headline]:
        """Headline values compared for a mode."""
        override = self.modes[mode].headline
        return self.headline if override is None else override

    def comparable(self, mode: Mode) -> bool:
        """True when a run in ``mode`` should reproduce the committed headline numbers exactly.

        That needs a deterministic benchmark run with the same commands that produced the committed result files:
        the full mode, a fast mode identical to it, or a fast mode flagged ``matches_committed``.
        """
        spec = self.modes[mode]
        same = mode == "full" or spec.commands == self.modes["full"].commands or spec.matches_committed
        return self.deterministic and same

    def model_free(self, mode: Mode) -> bool:
        """True when the mode downloads neither model weights nor datasets."""
        spec = self.modes[mode]
        return not (spec.needs_models or spec.needs_data)

    def blob_url(self, path: str, lines: tuple[int, int] | None = None) -> str:
        """GitHub URL of a file at the pinned commit, optionally anchored to a line range."""
        if self.commit is None:
            return f"{self.url}/blob/main/{path}"
        anchor = f"#L{lines[0]}-L{lines[1]}" if lines else ""
        return f"{self.url}/blob/{self.commit}/{path}{anchor}"


class Manifest(BaseModel):
    """All repositories of the teardown."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(ge=1)
    owner: str
    repos: list[RepoSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> Manifest:
        names = [r.name for r in self.repos]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        if duplicates:
            raise ValueError(f"duplicate repository names: {', '.join(duplicates)}")
        return self

    def get(self, name: str) -> RepoSpec:
        """The repository called ``name``."""
        for repo in self.repos:
            if repo.name == name:
                return repo
        raise KeyError(f"unknown repository {name!r}; known: {', '.join(r.name for r in self.repos)}")

    def commits(self) -> dict[str, str | None]:
        """Pinned commit per repository."""
        return {r.name: r.commit for r in self.repos}


def default_manifest_path() -> Path:
    """``bench/manifest.yaml`` in the project root."""
    return project_root() / "bench" / "manifest.yaml"


def load_manifest(path: Path | None = None) -> Manifest:
    """Load and validate the manifest."""
    path = path or default_manifest_path()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Manifest.model_validate(data)
