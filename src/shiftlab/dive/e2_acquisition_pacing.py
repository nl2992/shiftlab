"""E2: acquisition (gated vs uniform) and pacing (fixed vs paced) generators and cell runner.

New generators are built on the existing synthetic ``boundary_local_harm`` mechanism: the
covariates ``X`` and standardised noise ``z`` are taken from the existing generator at severity
zero (identical for every severity), and the mean shift ``severity * w_t * exp(-5 |m_t|)`` is
re-applied with a stream-specific weight ``w_t``. Burst events additionally resample the decision
score into the disagreement band. Nothing in the existing generator is modified.

Evaluator/learner separation: ``Stream.oracle`` (weights, expected costs, onset, burst masks) is
used only to compute summary endpoints. Replays receive ``MonitorInputs`` only.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr
from scipy.stats import norm

from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from .comparison_betting_engines import replay_engine
from .eprocess import PredictableBoundMeanEProcess
from .experiment import _binary_cost, _material_harm_onset, _synthetic_label_costs
from .gated_monitor_comparison import DisagreementPacer, gated_increment, replay_gated
from .proxy import DecisionLossProxy

N_EVENTS = 3200
MONITOR_START = 800
HORIZON = N_EVENTS - MONITOR_START  # 2400 monitored events
EPSILON = 0.1
ALPHA = 0.05
NOISE = 0.3
SEED_BLOCKS = {
    "dev": {"id": "e2_dev_smoke_and_power", "start": 100_000_000, "end": 100_001_999},
    "grid": {"id": "e2_dev_grid", "start": 100_500_000, "end": 100_509_999},
    "confirmation": {"id": "e2_confirmation", "start": 100_100_000, "end": 100_149_999},
}
# Development sub-block sizes (primary cells, then mechanism cells).
SUB_BLOCK = {"dev": (250, 80)}
GRID_WIDTH = 100  # seeds per grid-selection cell in the e2_dev_grid block
CONFIRMATION_WIDTH = 3000  # seeds per confirmation cell (at most 16 cells)
GATED_ARMS_E2 = ("gated_ht_fixed", "gated_ht_paced", "gated_ht_horizon")
ARMS = (*GATED_ARMS_E2, "uniform_ht", "uniform_ppi")
ENGINES = ("fixed08", "timans_grapa")  # fixed08 = default mixture; GRAPA is secondary
WINDOW = 300  # fixed informative-label window after onset (mechanism check)

# Disagreement band of the (deployed, reference) pair in score units: the reference acts
# positively when the source probability exceeds 1/6, the deployed policy when the score is >= 0.
BAND_LO = NOISE * float(norm.ppf(1 / 6))
HARMLESS_WIDTH = 0.015


@dataclass(frozen=True)
class CellSpec:
    name: str
    kind: str  # "b1", "burst_i", "burst_ii", "burst_iii", "mech"
    budget_rate: float
    severity: float = 1.5
    role: str = "primary"  # "primary" | "mech_train" | "mech_heldout" | "grid"
    arms: tuple[str, ...] = ARMS
    burst_len: int = 0  # 0 = the kind's default length
    burst_frac: float = 0.0  # 0 = the kind's default fraction of events replaced by a burst


_MECH = ("gated_ht_fixed",)
CORE_B1_CELLS = (
    CellSpec("b1_r0.02", "b1", 0.02),
    CellSpec("b1_r0.05", "b1", 0.05),
    CellSpec("b1_r0.20", "b1", 0.20),
)
# Original (ceiling) burst cells: development only. Confirmation uses locked grid cells.
LEGACY_BURST_CELLS = (
    CellSpec("b2_i", "burst_i", 0.10),
    CellSpec("b2_ii", "burst_ii", 0.10),
    CellSpec("b2_iii", "burst_iii", 0.10),
)
PRIMARY_CELLS = CORE_B1_CELLS + LEGACY_BURST_CELLS
MECH_CELLS = (
    CellSpec("mech_s0.8_r0.02", "mech", 0.02, 0.8, "mech_train", _MECH),
    CellSpec("mech_s0.8_r0.10", "mech", 0.10, 0.8, "mech_train", _MECH),
    CellSpec("mech_s1.5_r0.02", "mech", 0.02, 1.5, "mech_train", _MECH),
    CellSpec("mech_s1.5_r0.10", "mech", 0.10, 1.5, "mech_train", _MECH),
    CellSpec("mech_s1.0_r0.05", "mech", 0.05, 1.0, "mech_heldout", _MECH),
    CellSpec("mech_s2.0_r0.05", "mech", 0.05, 2.0, "mech_heldout", _MECH),
)
ALL_CELLS = PRIMARY_CELLS + MECH_CELLS  # development-block cells

# Grid for development-only selection (block e2_dev_grid): severity x budget x burst length.
GRID_SEVERITIES = (0.15, 0.25, 0.4, 0.7)
GRID_RATES = (0.02, 0.05, 0.10)
GRID_LENGTHS = {"i": (200, 500), "iii": (150, 300)}
GRID_II_RATES = (0.05, 0.10, 0.20)
GRID_II_LENGTHS = (60, 120, 200, 300, 450)


def _grid() -> tuple[CellSpec, ...]:
    cells = []
    for tag in ("i", "iii"):
        for sev in GRID_SEVERITIES:
            for r in GRID_RATES:
                for length in GRID_LENGTHS[tag]:
                    name = f"g_{tag}_s{sev}_r{r}_L{length}"
                    cells.append(
                        CellSpec(name, f"burst_{tag}", r, sev, "grid", GATED_ARMS_E2, length, 0.5)
                    )
    for r in GRID_II_RATES:
        for length in GRID_II_LENGTHS:
            name = f"g_ii_s1.5_r{r}_L{length}"
            cells.append(CellSpec(name, "burst_ii", r, 1.5, "grid", GATED_ARMS_E2, length, 0.8))
    return tuple(cells)


GRID_CELLS = _grid()
CELLS = {c.name: c for c in (*ALL_CELLS, *GRID_CELLS)}
CONFIRMATION_CORE = tuple(c.name for c in (*CORE_B1_CELLS, *MECH_CELLS))


def cell_seed_range(block: str, cell: str, order: list[str] | None = None) -> tuple[int, int]:
    """Inclusive seed range of one cell: disjoint sub-blocks inside the registered block.

    ``order`` is required for the confirmation block: the ordered cell names (core cells, then the
    locked grid cells) whose index fixes the sub-block.
    """
    start = SEED_BLOCKS[block]["start"]
    if block == "dev":
        primary, mech = SUB_BLOCK["dev"]
        names = [c.name for c in ALL_CELLS]
        k = names.index(cell)
        if k < len(PRIMARY_CELLS):
            lo, size = start + k * primary, primary
        else:
            lo, size = start + len(PRIMARY_CELLS) * primary + (k - len(PRIMARY_CELLS)) * mech, mech
    elif block == "grid":
        k = [c.name for c in GRID_CELLS].index(cell)
        lo, size = start + k * GRID_WIDTH, GRID_WIDTH
    elif block == "confirmation":
        if order is None or len(set(order)) != len(order) or len(order) > 16:
            raise ValueError("confirmation needs an ordered list of at most 16 distinct cells")
        lo, size = start + order.index(cell) * CONFIRMATION_WIDTH, CONFIRMATION_WIDTH
    else:
        raise ValueError(f"unknown block {block!r}")
    hi = lo + size - 1
    if hi > SEED_BLOCKS[block]["end"]:
        raise RuntimeError("cell sub-block exceeds the registered seed block")
    return lo, hi


def cell_seeds(block: str, cell: str, n: int, order: list[str] | None = None) -> list[int]:
    lo, hi = cell_seed_range(block, cell, order)
    if not 0 < n <= hi - lo + 1:
        raise ValueError(f"n={n} exceeds sub-block capacity {hi - lo + 1} for {cell}")
    return list(range(lo, lo + n))  # the seed is used directly as the stream seed


@dataclass
class Oracle:
    """Evaluator-side truth; never passed to a replay."""

    weight: np.ndarray
    burst: np.ndarray
    expected_cost: np.ndarray
    onset: int | None
    sample_path_onset: int | None
    regimes: list[tuple[int, int, str]]


@dataclass
class MonitorInputs:
    x: np.ndarray
    paired_cost: np.ndarray  # only read on queried events
    disagreement: np.ndarray
    tariffs: np.ndarray
    uniforms: np.ndarray
    validation_disagreement: np.ndarray
    validation_tariffs: np.ndarray
    proxy: DecisionLossProxy
    budget_rate: float


@dataclass
class Stream:
    monitor: MonitorInputs
    oracle: Oracle
    seed: int
    cell: str


def _plan(cell: CellSpec, rng: np.random.Generator) -> list[tuple[int, int, str]]:
    """Regimes in monitored coordinates: (start, end, label).

    ``harm``: boundary-local harm (w=1). ``harm_burst``: harm plus a disagreement burst of
    in-band events. ``harmless_burst``: in-band events confined to a narrow subband whose paired
    cost mean is below epsilon (w=0). ``cell.burst_len`` is the burst length (class i, ii) or
    the harm-window length (class iii).
    """
    h = HORIZON
    kind = cell.kind
    if kind in {"b1", "mech"}:
        onset = int(rng.integers(300, 1501))
        return [(onset, h, "harm")]
    if kind == "burst_i":
        length = cell.burst_len or 500
        onset = int(rng.integers(300, 1201))
        start = onset + int(rng.integers(100, 301))
        return [
            (onset, start, "harm"),
            (start, start + length, "harm_burst"),
            (start + length, h, "harm"),
        ]
    if kind == "burst_ii":
        length = cell.burst_len or 400
        b0 = int(rng.integers(100, 401))
        onset = b0 + length + int(rng.integers(100, 501))
        return [(b0, b0 + length, "harmless_burst"), (onset, h, "harm")]
    if kind == "burst_iii":
        length = cell.burst_len or 300
        onset = int(rng.integers(200, 601))
        out = []
        start = onset
        while start < h:
            out.append((start, min(start + length, h), "harm_burst"))
            start += 2 * length
        return out
    raise ValueError(f"unknown cell kind {kind!r}")


def burst_fraction(cell: CellSpec, label: str) -> float:
    if label == "harm":
        return 0.0
    return cell.burst_frac or (0.8 if label == "harmless_burst" else 0.5)


def build_stream(cell: CellSpec, seed: int) -> Stream:
    scenario = next(s for s in SCENARIOS if s.name == "boundary_local_harm")
    null_scenario = dataclasses.replace(scenario, severity=0.0)
    base = ExperimentConfig(n=N_EVENTS, d=16, seed_offset=seed, device="cpu")
    _, frame, _, _ = _generate(null_scenario, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    mean0 = x[:, 0] - 0.9 * x[:, 1]
    z = (frame.target.to_numpy(dtype=float) - mean0) / NOISE
    rng = np.random.default_rng([seed, 0xE2A1])
    regimes = _plan(cell, rng)
    burst_rng = np.random.default_rng([seed, 0xE2B2])
    weight = np.zeros(N_EVENTS)
    burst = np.zeros(N_EVENTS, dtype=bool)
    for start, end, label in regimes:
        lo, hi = MONITOR_START + start, MONITOR_START + end
        if label in {"harm", "harm_burst"}:
            weight[lo:hi] = 1.0
        frac = burst_fraction(cell, label)
        if frac > 0:
            members = burst_rng.random(hi - lo) < frac
            width = HARMLESS_WIDTH if label == "harmless_burst" else -BAND_LO
            score = BAND_LO + burst_rng.random(hi - lo) * width
            idx = np.flatnonzero(members) + lo
            x[idx, 0] = 0.9 * x[idx, 1] + score[members]
            burst[idx] = True
    mean0 = x[:, 0] - 0.9 * x[:, 1]
    mean = mean0 + cell.severity * weight * np.exp(-5 * np.abs(mean0))
    y = (mean + NOISE * z) > 0
    probability = norm.cdf(mean / NOISE)
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / NOISE) >= 0.5).astype(int)
    reference = _source_action(x, scenario)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    paired = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    expected = np.where(deployed == 1, fp * (1 - probability), fn * probability) - np.where(
        reference == 1, fp * (1 - probability), fn * probability
    )
    # Design onset: the start of the first planned harm regime (population mean > epsilon by
    # construction; checked on the evaluator's expected costs). The repository's sample-path rule
    # is kept only as a diagnostic because finite-stream baseline averages can cross epsilon by
    # chance and would relabel a null gap as the onset.
    cuts = sorted(
        {MONITOR_START + s for s, _, _ in regimes} | {MONITOR_START + e for _, e, _ in regimes}
    )
    sample_path_onset = _material_harm_onset(
        expected, EPSILON, change_times=cuts, monitor_start=MONITOR_START
    )
    onset = None
    for a_, b_, label in regimes:
        if label in {"harm", "harm_burst"} and (
            float(expected[MONITOR_START + a_ : MONITOR_START + b_].mean()) > EPSILON
        ):
            onset = a_  # first planned harm regime that is material at the population level
            break
    active = deployed != reference
    tariffs = _synthetic_label_costs(x)
    centered = paired - EPSILON
    proxy = DecisionLossProxy(clip=5.1, seed=seed, update_every=20).fit(
        x[:400], centered[:400], x[400:800], centered[400:800]
    )
    uniforms = np.random.default_rng(seed + 9_173).random(N_EVENTS)
    monitor = MonitorInputs(
        x=x[MONITOR_START:],
        paired_cost=paired[MONITOR_START:],
        disagreement=active[MONITOR_START:],
        tariffs=tariffs[MONITOR_START:],
        uniforms=uniforms[:HORIZON],
        validation_disagreement=active[400:800],
        validation_tariffs=tariffs[400:800],
        proxy=proxy,
        budget_rate=cell.budget_rate,
    )
    oracle = Oracle(
        weight=weight[MONITOR_START:],
        burst=burst[MONITOR_START:],
        expected_cost=expected[MONITOR_START:],
        onset=onset,
        sample_path_onset=sample_path_onset,
        regimes=regimes,
    )
    return Stream(monitor, oracle, seed, cell.name)


@dataclass
class UniformReplay:
    increments: np.ndarray
    bounds: np.ndarray
    queried: np.ndarray
    log_e: np.ndarray
    dollars: float
    budget: float
    propensity: float


def replay_uniform(
    *,
    arm: str,
    m: MonitorInputs,
    epsilon: float = EPSILON,
    alpha: float = ALPHA,
) -> UniformReplay:
    """Uniform HT or PPI: every event may be queried with one constant propensity ``q = r``.

    The expected spend per event is ``q * E[tariff]``, which equals the paced/fixed gated target
    ``r * E[tariff]`` (the same reserve ``target * horizon``). The HT bound is ``C/q + eps`` and the
    PPI bound ``(C+eps)(2/q - 1)``; both are constants, so they are predictable. The reserve stop
    uses past spend only.
    """
    if arm not in {"uniform_ht", "uniform_ppi"}:
        raise ValueError("unknown uniform arm")
    q = float(m.budget_rate)
    pacer = DisagreementPacer(m.validation_disagreement, m.validation_tariffs, q)
    budget = pacer.target * len(m.x)
    proxy = copy_proxy(m.proxy) if arm == "uniform_ppi" else None
    process = PredictableBoundMeanEProcess(alpha=alpha)
    bound = (5 + epsilon) * (2 / q - 1) if proxy is not None else 5 / q + epsilon
    spent = 0.0
    inc, bnd, qry, logs = [], [], [], []
    for i in range(len(m.x)):
        if budget - spent + 1e-12 < 2.5:
            break
        anchor = float(proxy.predict(m.x[i : i + 1])[0]) + epsilon if proxy else 0.0
        query = bool(m.uniforms[i] < q)
        observed = float(m.paired_cost[i]) if query else None
        value = gated_increment(
            disagreement=True, observed_cost=observed, propensity=q, anchor=anchor, epsilon=epsilon
        )
        if abs(value) > bound:
            if abs(value) - bound > 1e-9 * bound:
                raise ValueError("increment exceeds its predictable support bound")
            value = float(np.copysign(bound, value))
        logs.append(process.update(value, bound=bound))
        if query:
            spent += float(m.tariffs[i])
            if proxy is not None:
                proxy.observe(m.x[i], observed - epsilon)
        inc.append(value)
        bnd.append(bound)
        qry.append(query)
    return UniformReplay(
        np.asarray(inc),
        np.asarray(bnd),
        np.asarray(qry, dtype=bool),
        np.asarray(logs),
        spent,
        budget,
        q,
    )


def copy_proxy(proxy: DecisionLossProxy) -> DecisionLossProxy:
    import copy

    return copy.deepcopy(proxy)


@dataclass
class HorizonReplay:
    increments: np.ndarray
    bounds: np.ndarray
    queried: np.ndarray
    log_e: np.ndarray
    dollars: float
    budget: float


def replay_gated_horizon(
    *, m: MonitorInputs, epsilon: float = EPSILON, alpha: float = ALPHA
) -> HorizonReplay:
    """Horizon-aware reserve baseline: gated HT whose propensity caps spend per remaining event.

    ``q_t = clip(min(q_fixed, (reserve - spent) / ((T - t) * rate)), 0.10, 1)`` where ``rate`` is the
    validation mean of ``D * tariff`` and ``q_fixed`` is the frozen validation propensity. It uses
    only the validation data, the elapsed time and the past spend, so it is predictable; the HT
    increment, bound ``5/q + eps`` and reserve stop are those of the other gated arms. It reacts to
    spend, not to the disagreement rate, so it is a simple alternative to the 200-event pacer.
    """
    pacer = DisagreementPacer(m.validation_disagreement, m.validation_tariffs, m.budget_rate)
    rate = max(float(np.mean(m.validation_disagreement * m.validation_tariffs)), 1e-6)
    n = len(m.x)
    budget = pacer.target * n
    process = PredictableBoundMeanEProcess(alpha=alpha)
    spent = 0.0
    inc, bnd, qry, logs = [], [], [], []
    for i in range(n):
        if budget - spent + 1e-12 < 2.5:
            break
        allowed = (budget - spent) / (n - i)
        q = float(np.clip(min(pacer.fixed, allowed / rate), 0.10, 1.0))
        bound = 5 / q + epsilon
        query = bool(m.disagreement[i] and m.uniforms[i] < q)
        observed = float(m.paired_cost[i]) if query else None
        value = gated_increment(
            disagreement=bool(m.disagreement[i]),
            observed_cost=observed,
            propensity=q,
            epsilon=epsilon,
        )
        logs.append(process.update(value, bound=bound))
        if query:
            spent += float(m.tariffs[i])
        inc.append(value)
        bnd.append(bound)
        qry.append(query)
    return HorizonReplay(
        np.asarray(inc),
        np.asarray(bnd),
        np.asarray(qry, dtype=bool),
        np.asarray(logs),
        spent,
        budget,
    )


def _ensure_scripts_importable() -> None:
    """``replay_engine`` imports the Timans reproduction from the repository's ``scripts``."""
    import importlib.util
    import sys
    from pathlib import Path

    if importlib.util.find_spec("scripts") is None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def _alarm(log_e: np.ndarray) -> int | None:
    hits = np.flatnonzero(log_e >= -np.log(ALPHA))
    return int(hits[0]) if len(hits) else None


def run_arms(stream: Stream, arms: tuple[str, ...], engines: tuple[str, ...]) -> list[dict]:
    m, o = stream.monitor, stream.oracle
    if "timans_grapa" in engines:
        _ensure_scripts_importable()
    rows = []
    for arm in arms:
        if arm == "gated_ht_horizon":
            h = replay_gated_horizon(m=m)
            values, bounds, queried, log_e = h.increments, h.bounds, h.queried, h.log_e
            dollars, budget = h.dollars, h.budget
        elif arm.startswith("gated"):
            r = replay_gated(
                arm=arm,
                x=m.x,
                paired_cost=m.paired_cost,
                disagreement=m.disagreement,
                tariffs=m.tariffs,
                uniforms=m.uniforms,
                validation_disagreement=m.validation_disagreement,
                validation_tariffs=m.validation_tariffs,
                budget_rate=m.budget_rate,
                proxy_template=None,
            )
            values, bounds, queried, log_e = r.increments, r.bounds, r.queried, r.log_e
            dollars, budget = r.dollars, r.budget
        else:
            u = replay_uniform(arm=arm, m=m)
            values, bounds, queried, log_e = u.increments, u.bounds, u.queried, u.log_e
            dollars, budget = u.dollars, u.budget
        spend = queried * m.tariffs[: len(queried)]
        for engine in engines:
            logs = log_e if engine == "fixed08" else replay_engine(values, bounds, engine)
            alarm = _alarm(logs)
            onset = o.onset
            detected = alarm is not None and onset is not None and alarm >= onset
            end = alarm + 1 if alarm is not None else len(queried)
            window = int(queried[onset : onset + WINDOW].sum()) if onset is not None else 0
            pre = float(spend[:onset].sum()) if onset is not None else float(spend.sum())
            rows.append(
                {
                    "cell": stream.cell,
                    "seed": stream.seed,
                    "arm": arm,
                    "engine": engine,
                    "onset": onset,
                    "first_alarm": alarm,
                    "detected": bool(detected),
                    "false_alarm_pre_onset": bool(
                        alarm is not None and (onset is None or alarm < onset)
                    ),
                    "labels_spent": int(queried.sum()),
                    "labels_to_alarm_or_horizon": int(queried[:end].sum()),
                    "dollars": float(dollars),
                    "budget": float(budget),
                    "processed": len(queried),
                    "window_labels": window,
                    "dollars_pre_onset": pre,
                    "dollars_post_onset": float(dollars) - pre,
                    "reserve_used_frac_pre_onset": pre / float(budget),
                    "reserve_exhausted": len(queried) < HORIZON,
                    "reserve_exhausted_before_onset": bool(
                        onset is not None and len(queried) <= onset
                    ),
                }
            )
    return rows


def run_stream(cell_name: str, seed: int, engines: tuple[str, ...] = ENGINES) -> list[dict]:
    cell = CELLS[cell_name]
    if cell.role == "grid" and engines == ENGINES:
        engines = ("fixed08",)  # grid selection uses the primary engine only
    return run_arms(build_stream(cell, seed), cell.arms, engines)


def config_digest(extra: dict | None = None) -> str:
    payload = {
        "cells": [dataclasses.asdict(c) for c in (*ALL_CELLS, *GRID_CELLS)],
        "seed_blocks": SEED_BLOCKS,
        "sub_block": SUB_BLOCK,
        "arms": ARMS,
        "engines": ENGINES,
        "n_events": N_EVENTS,
        "epsilon": EPSILON,
        "alpha": ALPHA,
        "window": WINDOW,
        "harmless_width": HARMLESS_WIDTH,
        **(extra or {}),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def timed(fn, *args):
    t = time.perf_counter()
    out = fn(*args)
    return out, time.perf_counter() - t
