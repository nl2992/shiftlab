"""Balanced marginal experimental plans; no Cartesian parameter-grid allocation."""

import hashlib
import json

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..schemas import SyntheticConfig
from .generators import SCENARIOS


class SamplingPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_seed: int = Field(default=42, ge=0)
    profiles: int = Field(default=12, ge=1, le=10000)
    scenarios: list[str] = Field(default_factory=lambda: ["iid_regression", "concept"])
    seeds: list[int] = Field(default_factory=lambda: [42])
    levels: dict[str, list] = Field(default_factory=dict)
    base: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_levels(self):
        if not self.scenarios or len(set(self.scenarios)) != len(self.scenarios):
            raise ValueError("Require nonempty unique scenarios")
        if set(self.scenarios) - SCENARIOS.keys():
            raise ValueError("Unknown plan scenario")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("Require nonempty unique paired seeds")
        if any(isinstance(s, bool) or not isinstance(s, int) or s < 0 for s in self.seeds):
            raise ValueError("Seeds must be nonnegative integers")
        allowed = {
            "n",
            "d",
            "severity",
            "change_fraction",
            "regimes",
            "delay",
            "missing",
            "rho",
            "noise",
            "pattern",
            "transition_fraction",
        }
        if set(self.levels) - allowed:
            raise ValueError("Unsupported sampling axis")
        for name, values in self.levels.items():
            if not values or len(set(values)) != len(values):
                raise ValueError(f"Require nonempty unique levels for {name}")
            if len(values) > self.profiles:
                raise ValueError(f"Increase profiles to cover every {name} level")
            for value in values:
                SyntheticConfig.model_validate({**self.base, name: value})
        SyntheticConfig.model_validate(self.base)
        return self


def profiles(plan: SamplingPlan):
    """Each level appears floor(m/k) or ceil(m/k) times; joint balance is not promised.

    Independent seeded permutations avoid ordered-axis coupling. This is a screening
    design, not a full factorial or a power guarantee. Every profile is crossed with
    the same DGP seeds and scenarios for subsequent paired algorithm comparisons.
    """
    rng = np.random.default_rng(plan.plan_seed)
    columns = {}
    for axis, values in sorted(plan.levels.items()):
        order = rng.permutation(len(values))
        indices = np.resize(order, plan.profiles)
        rng.shuffle(indices)
        columns[axis] = [values[int(i)] for i in indices]
    result = []
    for i in range(plan.profiles):
        config = {**plan.base, **{key: values[i] for key, values in columns.items()}}
        # Validate combinations as well as individual axis levels.
        SyntheticConfig.model_validate(config)
        result.append(config)
    return result


def expand_plan(plan: SamplingPlan):
    """Yield validated stream configs, plus stable profile IDs for pairing."""
    for profile in profiles(plan):
        identity = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()[:16]
        for scenario in plan.scenarios:
            for seed in plan.seeds:
                yield (
                    identity,
                    SyntheticConfig.model_validate({**profile, "scenario": scenario, "seed": seed}),
                )


def summarize_plan(plan: SamplingPlan):
    chosen = profiles(plan)
    coverage = {
        axis: {str(level): sum(p[axis] == level for p in chosen) for level in values}
        for axis, values in plan.levels.items()
    }
    configs = [SyntheticConfig.model_validate(p) for p in chosen]
    multiplicity = len(plan.scenarios) * len(plan.seeds)
    return {
        "design": "balanced marginals; interactions not exhaustively covered",
        "paired_dgp_seeds": plan.seeds,
        "profile_count": len(chosen),
        "stream_count": len(chosen) * multiplicity,
        "observation_count": sum(c.n for c in configs) * multiplicity,
        "uncompressed_feature_bytes": sum(
            c.n * c.d * (4 if c.dtype == "float32" else 8) for c in configs
        )
        * multiplicity,
        "storage_note": "Feature arrays only; Parquet, row metadata and oracles require additional space.",
        "coverage": coverage,
        "plan": plan.model_dump(),
    }
