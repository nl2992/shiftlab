"""Evaluator-side streams, truth, feedback (delay/missingness) models and the family registry.

Adapted from GAVE-R / Failure-Atlas conventions (source: origin/research/gave-r-2026-11-06
``docs/gaver/01_HARNESS_MAP.md`` and ``src/shiftlab/dive/failure_atlas.py`` at main@7354480a):
binary outcome chain Y, ``loss_inc = Y``, ``loss_cand = 1 - Y``, Markov transitions
``(p(1-rho), p+rho(1-p))``, RNG ``default_rng([seed, tag, crc32(id)])``. New here: per-round
precomputed potential delays / missingness (common random numbers across policies), a monitor
signal, retrain/route/query randomness (common random numbers), and null-status truth for cond / marg / absolute-risk nulls.

Gain convention: ``g_t = l_inc,t - l_cand,t`` (positive = candidate better). With hurdle h:
  H0cond   : E[g_t | F_{t-1}] <= h  for every history (checked via the Markov state)
  H0marg   : E[g_t]           <= h
  abs-risk : R_t(incumbent)   <= tau
"""

from __future__ import annotations

import hashlib
import os
import zlib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

from .guards import Sealed

SEED_BLOCKS = {  # proposed; to be registered in configs/seed_registry.yaml by the coordinator
    "smoke": (110_900_000, 110_900_999),
    "dev": (110_000_000, 110_099_999),
    "confirmation": (120_000_000, 120_099_999),
}
STREAM_TAG = 71007
N_U = 16  # shared uniforms per round exposed to policies


class ConfirmationAccessError(PermissionError):
    """Confirmation families are held out and read-only."""


@dataclass(frozen=True)
class DelaySpec:
    kind: str = "fixed"  # fixed | uniform | geometric | lognormal | informative
    d: int = 10  # fixed; informative: delay of favourable-to-candidate rounds
    lo: int = 1
    hi: int = 20
    mean: float = 20.0  # geometric mean delay
    median: float = 20.0
    sigma: float = 1.0
    d_unfav: int = 50  # informative: delay when the candidate is not better


@dataclass(frozen=True)
class MissingSpec:
    kind: str = "none"  # none | bernoulli | informative
    p: float = 0.0
    p_fav: float = 0.0  # informative: P(never released) when candidate better
    p_unfav: float = 0.0


@dataclass(frozen=True)
class StreamSpec:
    family: str
    T: int = 1000
    dependence: str = "iid"  # iid | markov
    rho: float = 0.0
    onset_frac: float = 0.3
    duration_frac: float = 0.6  # regime 'during' lasts duration_frac*T (1.0 = to end)
    p_before: float = 0.25  # P(Y=1) = P(candidate better) = incumbent loss rate
    p_during: float = 0.9
    p_after: float | None = None  # None -> p_before
    onset_jitter: float = 0.05
    # Retrain quality model (evaluator-side, see BENCHMARK_CONTRACT section 4a): a model retrained
    # with clean labelled fraction e has loss rate q(e) = retrain_rate + (retrain_poor_rate -
    # retrain_rate) * (1 - min(1, e / retrain_sat_fraction)).
    retrain_rate: float = 0.25  # best attainable loss rate of a retrained model
    retrain_poor_rate: float = 0.6  # loss rate when no clean label is available in W_train
    retrain_sat_fraction: float = 0.7  # clean labelled fraction at which q saturates (RAR theta_L)
    hurdle: float = 0.1
    tau: float = 0.5  # absolute-risk requirement
    delay: DelaySpec = field(default_factory=DelaySpec)
    missing: MissingSpec = field(default_factory=MissingSpec)
    x_signal: float = 0.8  # shift of monitor signal mean during the 'during' regime

    @property
    def spec_id(self) -> str:
        return f"{self.family}|T{self.T}|{self.dependence}{self.rho:g}|on{self.onset_frac:g}"

    def null_twin(self) -> StreamSpec:
        """Boundary-null path: constant P(Y=1)=(1+h)/2 so marginal gain = h at every round."""
        p = (1.0 + self.hurdle) / 2.0
        return replace(self, family=self.family + "_NULL", p_before=p, p_during=p, p_after=p)


class EvaluatorTruth(Sealed):
    """Evaluator-only truth. Never passed to a policy; unreadable inside policy_context."""

    def __init__(self, regime, p, gain_marg, gain_cond_max, risk_inc, risk_cand, h, tau):
        self.regime = regime  # 0 before, 1 during, 2 after
        self.p = p
        self.gain_marg = gain_marg  # E[g_t]
        self.gain_cond_max = gain_cond_max  # sup over Markov state of E[g_t | F_{t-1}]
        self.risk_inc = risk_inc
        self.risk_cand = risk_cand
        self.h = h
        self.tau = tau
        # Per-round null status
        self.marg_null_t = gain_marg <= h + 1e-12
        self.cond_null_t = gain_cond_max <= h + 1e-12
        self.abs_null_t = risk_inc <= tau + 1e-12
        # Stream-level: does the claimed null hold on the WHOLE path? (validity metrics use these)
        self.null_holds = {
            "cond": bool(self.cond_null_t.all()),
            "marg": bool(self.marg_null_t.all()),
            "abs_risk": bool(self.abs_null_t.all()),
        }


class Stream(Sealed):
    """One realised stream (evaluator-side). Policies only ever see it through the simulator."""

    def __init__(
        self, spec, seed, loss_inc, loss_cand, retrain_u, x, delay, missing, truth, route_u, query_u
    ):
        self.spec = spec
        self.seed = int(seed)
        self.T = int(spec.T)
        self.loss_inc = loss_inc
        self.loss_cand = loss_cand
        self.retrain_u = retrain_u  # loss of a retrained model at t is 1[retrain_u[t] < q]
        self.route_u = route_u  # canary routing draw: served by target iff route_u[t] < fraction
        self.query_u = query_u  # shared randomness exposed to policies as state.u
        self.x = x
        self.delay = delay  # potential delay of the label of round t (used only if queried)
        self.missing = missing  # label of round t never released if queried
        self.truth = truth
        h = hashlib.sha256()
        for a in (loss_inc, loss_cand, retrain_u, x, delay, missing, route_u, query_u):
            h.update(np.ascontiguousarray(a).tobytes())
        self.fingerprint = h.hexdigest()[:16]


def _sample_delays(spec: DelaySpec, rng, gain: np.ndarray) -> np.ndarray:
    T = len(gain)
    k = spec.kind
    if k == "fixed":
        d = np.full(T, spec.d, dtype=float)
    elif k == "uniform":
        d = rng.integers(spec.lo, spec.hi + 1, size=T).astype(float)
    elif k == "geometric":
        d = rng.geometric(1.0 / max(spec.mean, 1.0), size=T).astype(float)
    elif k == "lognormal":
        d = np.ceil(rng.lognormal(np.log(spec.median), spec.sigma, size=T))
    elif k == "informative":
        d = np.where(gain > 0, spec.d, spec.d_unfav).astype(float)
    else:
        raise ValueError(f"unknown delay kind {k!r}")
    return np.maximum(1, d).astype(np.int64)


def _sample_missing(spec: MissingSpec, rng, gain: np.ndarray) -> np.ndarray:
    u = rng.random(len(gain))
    if spec.kind == "none":
        return np.zeros(len(gain), dtype=bool)
    if spec.kind == "bernoulli":
        return u < spec.p
    if spec.kind == "informative":
        return u < np.where(gain > 0, spec.p_fav, spec.p_unfav)
    raise ValueError(f"unknown missing kind {spec.kind!r}")


def make_stream(spec: StreamSpec, seed: int) -> Stream:
    """Pure function of (spec, seed): identical fingerprint on every call (pairing)."""
    T = spec.T
    base = np.random.default_rng([int(seed), STREAM_TAG, zlib.crc32(spec.spec_id.encode())])
    rng_y, rng_x, rng_d, rng_m, rng_r, rng_j, rng_ro, rng_q = base.spawn(8)
    jitter = rng_j.uniform(-spec.onset_jitter, spec.onset_jitter) * T
    on = int(np.clip(round(spec.onset_frac * T + jitter), 1, T))
    off = T if spec.duration_frac >= 1.0 else int(min(T, on + round(spec.duration_frac * T)))
    regime = np.zeros(T, dtype=np.int8)
    regime[on - 1 : off] = 1
    regime[off:] = 2
    p_after = spec.p_before if spec.p_after is None else spec.p_after
    p = np.select([regime == 0, regime == 1], [spec.p_before, spec.p_during], p_after).astype(float)

    u = rng_y.random(T)
    y = np.zeros(T, dtype=np.int8)
    rho = spec.rho if spec.dependence == "markov" else 0.0
    prev = None
    for t in range(T):
        if prev is None or rho == 0.0:
            pr = p[t]
        elif prev == 1:
            pr = p[t] + rho * (1 - p[t])
        else:
            pr = p[t] * (1 - rho)
        y[t] = 1 if u[t] < pr else 0
        prev = y[t]
    loss_inc = y.astype(float)
    loss_cand = 1.0 - loss_inc
    retrain_u = rng_r.random(T)
    route_u = rng_ro.random(T)
    query_u = rng_q.random((T, N_U))
    gain = loss_inc - loss_cand
    x = rng_x.normal(0.0, 1.0, T) + spec.x_signal * (regime == 1)
    delay = _sample_delays(spec.delay, rng_d, gain)
    missing = _sample_missing(spec.missing, rng_m, gain)

    gain_marg = 2 * p - 1
    g1 = 2 * (p + rho * (1 - p)) - 1  # E[g_t | Y_{t-1}=1]
    g0 = 2 * p * (1 - rho) - 1  # E[g_t | Y_{t-1}=0]
    gain_cond_max = np.maximum(g1, g0)
    gain_cond_max[0] = gain_marg[0]
    truth = EvaluatorTruth(
        regime, p, gain_marg, gain_cond_max, p.copy(), 1 - p, spec.hurdle, spec.tau
    )
    return Stream(
        spec, seed, loss_inc, loss_cand, retrain_u, x, delay, missing, truth, route_u, query_u
    )


# --------------------------------------------------------------------------- family registry
def _config_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "configs" / "d2a_rar"


def _spec_from_dict(d: dict[str, Any]) -> StreamSpec:
    d = dict(d)
    d["delay"] = DelaySpec(**d.get("delay", {}))
    d["missing"] = MissingSpec(**d.get("missing", {}))
    return StreamSpec(**d)


def load_family(name: str, split: str = "dev", config_dir: Path | None = None) -> StreamSpec:
    """Load a stream family. Confirmation requires D2A_CONFIRMATION_UNLOCK=1 and is logged."""
    import yaml

    cdir = config_dir or _config_dir()
    if split == "confirmation":
        if os.environ.get("D2A_CONFIRMATION_UNLOCK") != "1":
            raise ConfirmationAccessError(
                "confirmation families are held out; unlock only via the preregistered WP7 protocol"
            )
        path = cdir / "confirmation_families.yaml"
        if not path.exists():
            raise ConfirmationAccessError("confirmation_families.yaml not yet registered")
        with open(cdir / "confirmation_access.log", "a", encoding="utf8") as f:
            f.write(f"{name}\n")
    elif split == "dev":
        path = cdir / "stream_families.yaml"
    else:
        raise ValueError("split must be 'dev' or 'confirmation'")
    fams = yaml.safe_load(path.read_text(encoding="utf8"))["families"]
    return _spec_from_dict({"family": name, **fams[name]})


def list_families(split: str = "dev", config_dir: Path | None = None) -> list[str]:
    import yaml

    if split != "dev":
        raise ConfirmationAccessError("confirmation family names are not listed")
    path = (config_dir or _config_dir()) / "stream_families.yaml"
    return sorted(yaml.safe_load(path.read_text(encoding="utf8"))["families"])


def seed_for(split: str, index: int) -> int:
    lo, hi = SEED_BLOCKS[split]
    if not 0 <= index <= hi - lo:
        raise ValueError("index outside seed block")
    return lo + index


def retrain_loss_rate(spec: StreamSpec, clean_labelled_fraction: float) -> float:
    """Loss rate q of a model retrained when a fraction e of its W_train window is clean-labelled."""
    e = min(1.0, max(0.0, clean_labelled_fraction) / spec.retrain_sat_fraction)
    return spec.retrain_rate + (spec.retrain_poor_rate - spec.retrain_rate) * (1.0 - e)
