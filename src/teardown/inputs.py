"""Inputs of the cost model (``bench/cost_inputs.yaml``): price tables, measurements and assumptions."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .paths import project_root

Tier = Literal["small", "medium", "large"]
TIERS: tuple[Tier, ...] = ("small", "medium", "large")


class TierPrice(BaseModel):
    """USD per million tokens."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input: float = Field(ge=0)
    output: float = Field(ge=0)


class PriceSource(BaseModel):
    """Where a repository defines a price table: literal snippets that must appear in the file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    repo: str
    path: str
    contains: list[str] = Field(min_length=1)


class PriceTable(BaseModel):
    """A price table per tier. ``kind`` says whether it comes from a repository or is a labelled scenario."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    label: str
    kind: Literal["repo", "scenario"]
    description: str
    source: PriceSource | None = None
    tiers: dict[Tier, TierPrice]

    @model_validator(mode="after")
    def _complete(self) -> PriceTable:
        if set(self.tiers) != set(TIERS):
            raise ValueError(f"{self.id}: prices are needed for small, medium and large")
        if self.kind == "repo" and self.source is None:
            raise ValueError(f"{self.id}: a repository price table must name its source file")
        if self.kind == "scenario" and self.source is not None:
            raise ValueError(f"{self.id}: a scenario is defined here, so it has no repository source")
        return self

    def cost(self, tier: Tier, input_tokens: float, output_tokens: float) -> float:
        """USD for one call of the given size on a tier."""
        price = self.tiers[tier]
        return (input_tokens * price.input + output_tokens * price.output) / 1_000_000


class Measurement(BaseModel):
    """A number read from a repository file at its pinned commit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    value: float
    unit: str
    description: str
    repo: str
    path: str
    pointer: str | None = None
    derive: str | None = None
    tolerance: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _locator(self) -> Measurement:
        if self.pointer is None and self.derive is None:
            raise ValueError(f"{self.id}: a measurement needs a JSON pointer, a derivation, or both")
        return self


class Assumption(BaseModel):
    """A number no repository measures, with the reason for its value."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    value: float
    unit: str
    rationale: str = Field(min_length=10)


class CostInputs(BaseModel):
    """Everything the cost model may use. Every number is either a measurement or a stated assumption."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    price_tables: list[PriceTable] = Field(min_length=1)
    measurements: list[Measurement]
    assumptions: list[Assumption]

    @model_validator(mode="after")
    def _unique_ids(self) -> CostInputs:
        ids = [m.id for m in self.measurements] + [a.id for a in self.assumptions]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"ids used more than once: {', '.join(duplicates)}")
        tables = [t.id for t in self.price_tables]
        if len(tables) != len(set(tables)):
            raise ValueError("price table ids must be unique")
        return self

    def value(self, key: str) -> float:
        """The value of a measurement or assumption."""
        for measurement in self.measurements:
            if measurement.id == key:
                return measurement.value
        for assumption in self.assumptions:
            if assumption.id == key:
                return assumption.value
        raise KeyError(f"no measurement or assumption called {key!r}")

    def kind_of(self, key: str) -> Literal["measured", "assumed"]:
        """Whether ``key`` is a measurement or an assumption."""
        if any(m.id == key for m in self.measurements):
            return "measured"
        if any(a.id == key for a in self.assumptions):
            return "assumed"
        raise KeyError(key)

    def measurement(self, key: str) -> Measurement:
        """The measurement called ``key``."""
        for item in self.measurements:
            if item.id == key:
                return item
        raise KeyError(key)

    def assumption(self, key: str) -> Assumption:
        """The assumption called ``key``."""
        for item in self.assumptions:
            if item.id == key:
                return item
        raise KeyError(key)

    def price_table(self, table_id: str) -> PriceTable:
        """The price table called ``table_id``."""
        for table in self.price_tables:
            if table.id == table_id:
                return table
        raise KeyError(f"unknown price table {table_id!r}")


def default_inputs_path() -> Path:
    """``bench/cost_inputs.yaml`` in the project root."""
    return project_root() / "bench" / "cost_inputs.yaml"


def load_inputs(path: Path | None = None) -> CostInputs:
    """Load and validate the cost-model inputs."""
    path = path or default_inputs_path()
    return CostInputs.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
