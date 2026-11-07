"""Paired-run utilities: common streams per seed, pairing checks, paired bootstrap CIs."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from .audit import verify_run
from .simulator import Policy, RunResult, Simulator
from .streams import Stream, StreamSpec, make_stream
from .types import EnvSpec


class UnpairedError(ValueError):
    """Two runs were not produced on identical (seed, stream) pairs."""


@dataclass
class PairedRuns:
    seeds: tuple[int, ...]
    fingerprints: tuple[str, ...]
    runs: dict[str, list[RunResult]]

    def J(self, name: str) -> np.ndarray:
        return np.array([r.J for r in self.runs[name]])

    def component(self, name: str, key: str) -> np.ndarray:
        return np.array([r.breakdown[key] for r in self.runs[name]])

    def diff(self, a: str, b: str, key: str = "J") -> np.ndarray:
        """Per-seed (a - b). Raises UnpairedError unless the runs share seeds and streams."""
        assert_paired(self.runs[a], self.runs[b])
        return self.component(a, key) - self.component(b, key)

    def ci(self, a: str, b: str, key: str = "J", **kw):
        return paired_bootstrap_ci(self.diff(a, b, key), **kw)


def assert_paired(ra: Sequence[RunResult], rb: Sequence[RunResult]) -> None:
    if len(ra) != len(rb):
        raise UnpairedError("different numbers of runs")
    for x, y in zip(ra, rb):
        if x.seed != y.seed:
            raise UnpairedError(f"seed mismatch {x.seed} vs {y.seed}")
        if x.stream_fingerprint != y.stream_fingerprint:
            raise UnpairedError(f"seed {x.seed}: policies saw different streams")
        if x.spec_id != y.spec_id:
            raise UnpairedError("spec mismatch")


def paired_bootstrap_ci(
    diffs: np.ndarray, level: float = 0.95, n_boot: int = 2000, rng_seed: int = 0
) -> tuple[float, float, float]:
    """Percentile bootstrap over seeds of the mean paired difference -> (mean, lo, hi)."""
    d = np.asarray(diffs, dtype=float)
    if d.size < 2:
        raise ValueError("need >= 2 paired seeds")
    rng = np.random.default_rng(rng_seed)
    idx = rng.integers(0, d.size, size=(n_boot, d.size))
    means = d[idx].mean(axis=1)
    a = (1 - level) / 2
    return float(d.mean()), float(np.quantile(means, a)), float(np.quantile(means, 1 - a))


def run_paired(
    policies: Mapping[str, Callable[[], Policy]],
    spec: StreamSpec,
    env: EnvSpec,
    seeds: Sequence[int],
    on_violation: str = "raise",
    verify: bool = True,
) -> PairedRuns:
    """Every policy is run on the SAME stream object per seed (fresh policy instance each)."""
    runs: dict[str, list[RunResult]] = {k: [] for k in policies}
    fps = []
    for sd in seeds:
        stream: Stream = make_stream(spec, sd)
        fps.append(stream.fingerprint)
        for name, factory in policies.items():
            pol = factory()
            pol.name = name
            res = Simulator(stream, env, on_violation).run(pol)
            if verify:
                verify_run(res, stream)
            runs[name].append(res)
    return PairedRuns(tuple(seeds), tuple(fps), runs)
