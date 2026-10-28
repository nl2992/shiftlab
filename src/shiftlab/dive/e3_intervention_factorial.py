"""E3 matched-opportunity intervention factorial (protocol P2, H-B3).

One synthetic stream (seed) is replayed through a crossed set of cells; every
response arm inside a cell sees the same stream, the same query uniforms and the
same Q1 trigger (coupled replay, matching level L1-L3, never L4).

Reused by import from ``integrated_pipeline`` / ``budgeted_promotion``: the
stream generator, the candidate family, the Q1 e-process settings, the target
scout + certification step and the rollback constants. Copy-adapted here
(``integrated_pipeline.run_seed`` is monolithic and fixes the stage boundaries):
the Q1 loop, the rollback loop, the onset transform and the policy timeline.

Learner-side code (``run_q1_monitor``, ``run_certification``,
``run_rollback_monitor``) never receives oracle probabilities. The oracle lives
only in :class:`OracleView` and is read only by :func:`evaluate_timeline`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import ndtr

from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from .budgeted_promotion import (
    BudgetedPromotionConfig,
    _candidate_outcome_contrasts,
    _fit_candidate_family,
    _monitor_scout_context_policy,
)
from .eprocess import BoundedMeanEProcess
from .experiment import _binary_cost
from .integrated_pipeline import (
    HARM_MARGIN,
    MONITOR_ALPHA,
    MONITOR_QUERY_RATE,
    PROMOTION_ALPHA,
    QUERY_RATE,
    ROLLBACK_ALPHA,
    ROLLBACK_COST,
    ROLLBACK_LABEL_CAP,
    SCOUT_CERT_LABEL_CAP,
    STAGES,
    SWITCH_COST,
)

N_EVENTS = STAGES["stream_end"]  # 3200
FIT_END = STAGES["fit_end"]  # 800: the Q1 monitor window opens here
CERT_WINDOW = 800  # scout (400) + fresh certification (400), as in the integrated pipeline

# ---- registered factor levels (docs/research_refinement_v1/stage1/P2_E3_protocol.md) ----
ONSETS: dict[str, int] = {"before": 800, "at": 1600, "after": 2000}
COVERAGE_END: dict[str, int] = {"short": 1600, "long": N_EVENTS}
ROLLBACKS: tuple[str, ...] = ("off", "parity")
REFERENCE_STATES: tuple[str, ...] = ("safe", "deteriorating")
RESPONSES: tuple[str, ...] = (
    "continue",
    "revert",
    "certify_promote",
    "revert_while_certifying",
)
# Reference deterioration (evaluator side): from the first event after the cell's Q1 alarm
# (alarm index + 1 + DETERIORATION_LAG) every latent target is shifted by
# +DETERIORATION_SHIFT before thresholding at zero. No Q1 alarm -> no deterioration.
DETERIORATION_LAG = 0
DETERIORATION_SHIFT = 0.6
SCORE_SCALE = 0.3  # the generator's label noise scale; p = ndtr(score / 0.3)
BASE_SEED_OFFSET = 700_001  # query-uniform stream offset, as in integrated_pipeline

SCENARIO = {s.name: s for s in SCENARIOS}["harmful_adaptation"]
FN_COST, FP_COST = SCENARIO.fn_cost, SCENARIO.fp_cost
COST_BOUND = float(max(FN_COST, FP_COST))


def cell_key(onset: str, coverage: str, rollback: str, reference: str) -> str:
    return f"{onset}|{coverage}|{rollback}|{reference}"


def all_cells() -> list[tuple[str, str, str, str]]:
    return [
        (o, c, r, s)
        for o in ONSETS
        for c in COVERAGE_END
        for r in ROLLBACKS
        for s in REFERENCE_STATES
    ]


def _cost(actions: np.ndarray, y: np.ndarray) -> np.ndarray:
    return _binary_cost(actions, y, FN_COST, FP_COST)


def expected_cost(actions: np.ndarray, p: np.ndarray) -> np.ndarray:
    return np.where(actions == 1, FP_COST * (1.0 - p), FN_COST * p)


# ------------------------------------------------------------------------------------
# Stream construction
# ------------------------------------------------------------------------------------
@dataclass(frozen=True)
class OracleView:
    """Evaluator-side truth. Never passed to a learner-side function."""

    probability: np.ndarray  # P(y=1 | x_t) after any deterioration


@dataclass(frozen=True)
class StreamBundle:
    seed: int
    x: np.ndarray
    target: np.ndarray  # latent target; y = 1{target > 0}
    score: np.ndarray
    probability_safe: np.ndarray
    reference: np.ndarray
    uniforms: np.ndarray
    family: dict[str, Any]  # learner-safe: h_truth is a decoy of zeros
    promotion_config: BudgetedPromotionConfig


def build_stream(seed: int, device: str = "cpu") -> StreamBundle:
    cfg = ExperimentConfig(
        n=N_EVENTS,
        d=16,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=FIT_END,
        window=64,
        stride=32,
        alpha=MONITOR_ALPHA,
        eprocess_epsilon=HARM_MARGIN,
        seed_offset=seed,
        change_fraction=0.20,
        device=device,
    )
    _, frame, oracle, _ = _generate(SCENARIO, seed, cfg)
    x = np.stack(frame.features.to_numpy()).astype(float)
    target = frame.target.to_numpy(dtype=float)
    y0 = (target > 0).astype(int)
    p0 = oracle.probability_positive.to_numpy(dtype=float).copy()
    pconfig = BudgetedPromotionConfig(
        n=N_EVENTS,
        d=x.shape[1],
        seeds=1,
        seed_offset=seed,
        alpha=PROMOTION_ALPHA,
        switching_cost=SWITCH_COST,
        budget_rates=(QUERY_RATE,),
        query_policies=("uniform",),
        shared_query_randomness=True,
        alpha_allocations=("rank",),
        estimators=("direct_ipw",),
        monitoring_rules=("fixed_mixture",),
        context_feature_index=0,
        context_threshold=0.0,
        scout_bound_mode="eventwise_propensity",
        include_scout_context_policy=True,
        create_plot=False,
        device=device,
    )
    # Fitted on events < FIT_END only (train + validation), so identical for every onset/state.
    family = _fit_candidate_family(
        x=x, y=y0, probability_true=p0, scenario=SCENARIO, config=pconfig
    )
    if int(family["validation_end"]) != FIT_END:
        raise RuntimeError("candidate family fit window differs from protocol")
    family["h_truth"] = np.zeros_like(family["h_truth"])  # oracle decoy: learners never see truth
    family["h_proxy"] = np.zeros_like(family["h_proxy"])
    uniforms = np.random.default_rng(seed + BASE_SEED_OFFSET).random(N_EVENTS)
    score = x[:, 0] - 0.9 * x[:, 1]
    return StreamBundle(
        seed=seed,
        x=x,
        target=target,
        score=score,
        probability_safe=p0,
        reference=np.asarray(_source_action(x, SCENARIO), dtype=int),
        uniforms=uniforms,
        family=family,
        promotion_config=pconfig,
    )


def deterioration_start(trigger: int | None) -> int:
    """First deteriorated event: strictly after the cell's common Q1 trigger (N if none).

    The labels y_t, t <= trigger, are identical in both reference states, so the Q1
    history, and therefore the trigger, is identical across states by construction.
    """
    if trigger is None:
        return N_EVENTS
    return min(N_EVENTS, trigger + 1 + DETERIORATION_LAG)


def realised_outcomes(
    bundle: StreamBundle, reference_state: str, start: int, shift: float = DETERIORATION_SHIFT
) -> tuple[np.ndarray, OracleView]:
    """Observed labels and evaluator-side truth for a reference state.

    ``deteriorating``: for t >= ``start`` the latent target is shifted by +0.6, so
    y_t = 1{target_t + 0.6 > 0} and p_t = ndtr((score_t + 0.6) / 0.3). Features are
    unchanged (pure concept shift): the fixed source reference misses boundary-region
    positives (false-negative cost 5) while liberal logistic candidates in the frozen
    family do not. ``safe``: the stationary labels.
    """
    if reference_state == "safe":
        return (bundle.target > 0).astype(int), OracleView(bundle.probability_safe.copy())
    if reference_state != "deteriorating":
        raise ValueError(f"unknown reference state {reference_state}")
    target = bundle.target.copy()
    p = bundle.probability_safe.copy()
    target[start:] += shift
    p[start:] = ndtr((bundle.score[start:] + shift) / SCORE_SCALE)
    return (target > 0).astype(int), OracleView(p)


def family_for_onset(bundle: StreamBundle, onset: int) -> tuple[dict[str, Any], np.ndarray]:
    """Incumbent = pre-onset classifier, then all-positive from ``onset`` (harmful adaptation)."""
    family = dict(bundle.family)
    incumbent = (bundle.score >= 0).astype(int)
    incumbent[onset:] = 1
    actions = np.asarray(family["actions"], dtype=int).copy()
    for row, name in enumerate(family["candidate_ids"]):
        if name == "incumbent_snapshot":
            actions[row] = incumbent
    z0, z1 = _candidate_outcome_contrasts(incumbent, actions, fn=FN_COST, fp=FP_COST)
    family.update(incumbent=incumbent, actions=actions, z0=z0, z1=z1)
    family["q_min"] = dict(family["q_min"])
    family["q_paths"] = dict(family["q_paths"])
    return family, incumbent


# ------------------------------------------------------------------------------------
# Learner-side components (no oracle access)
# ------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Q1Result:
    trigger: int | None
    labels: int
    processed: int
    rate: float
    window_end: int


def monitor_rate(coverage: str) -> float:
    """Q1 rate is the integrated pipeline's constant 0.40 at both coverage levels."""
    return MONITOR_QUERY_RATE


def monitor_label_cap(coverage: str) -> int:
    """Per-stage cap proportional to the window: 320 labels at 1600, 960 at 3200."""
    return round(MONITOR_QUERY_RATE * (COVERAGE_END[coverage] - FIT_END))


def total_label_cap(coverage: str) -> int:
    """Sum of the per-stage caps (monitor + certification 320 + rollback 160)."""
    return monitor_label_cap(coverage) + SCOUT_CERT_LABEL_CAP + ROLLBACK_LABEL_CAP


def run_q1_monitor(
    *,
    incumbent: np.ndarray,
    reference: np.ndarray,
    y: np.ndarray,
    uniforms: np.ndarray,
    coverage: str,
) -> Q1Result:
    """Ungated HT harm e-process (incumbent minus reference), constant predictable rate."""
    rate = monitor_rate(coverage)
    cap = monitor_label_cap(coverage)
    end = COVERAGE_END[coverage]
    harm = _cost(incumbent, y) - _cost(reference, y)
    process = BoundedMeanEProcess(bound=COST_BOUND / rate + HARM_MARGIN, alpha=MONITOR_ALPHA)
    labels = processed = 0
    trigger: int | None = None
    for event in range(FIT_END, end):
        if labels >= cap:
            break
        processed += 1
        queried = bool(uniforms[event] < rate)
        labels += int(queried)
        estimate = harm[event] / rate if queried else 0.0
        if process.update(estimate - HARM_MARGIN) >= -np.log(MONITOR_ALPHA):
            trigger = event
            break
    return Q1Result(trigger, labels, processed, rate, end)


@dataclass(frozen=True)
class CertResult:
    start: int  # first scout event (= trigger + 1)
    window_end: int  # start + CERT_WINDOW
    certified: bool
    crossing: int | None
    selected: dict[int, int | None]  # context -> candidate row (None = incumbent)
    labels: int
    scout_events: int
    cert_events: int
    candidate_ids: dict[int, str | None]


def run_certification(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    uniforms: np.ndarray,
    promotion_config: BudgetedPromotionConfig,
    start: int,
    coverage: str,
) -> CertResult | None:
    """Target scout + fresh certification on [start, start + 800); None if infeasible.

    Estimand (Q2 code-defined null, VALIDITY_TABLE rows 22-23): the e-process tests
    E[I_t (g_t - s) | F_{t-1}] <= 0 with g_t the candidate-vs-INCUMBENT gain and the
    amortised switch rate s charged only on selected contexts. It is not a full-cost
    net-benefit certificate and it says nothing about candidate-vs-reference.
    """
    end = start + CERT_WINDOW
    deployment_length = N_EVENTS - end
    if deployment_length < 1:
        return None
    budget = SCOUT_CERT_LABEL_CAP
    rate = budget / CERT_WINDOW
    fam = dict(family)
    fam.update(
        validation_end=start,
        monitor_end=end,
        monitor_length=CERT_WINDOW,
        deployment_length=deployment_length,
        q_min={**family["q_min"], rate: rate / 2},
        q_paths={**family["q_paths"], ("uniform", rate): np.full(CERT_WINDOW, rate)},
    )
    result = _monitor_scout_context_policy(
        family=fam,
        y=y,
        scenario=SCENARIO,
        config=replace(promotion_config, budget_rates=(rate,)),
        query_name="uniform",
        budget_rate=rate,
        query_uniforms=uniforms[start:end],
    )
    ids = {str(k): i for i, k in enumerate(family["candidate_ids"])}
    named = json.loads(str(result["selected_candidates_by_context"]))
    selected = {int(g): (None if v is None else ids[str(v)]) for g, v in named.items()}
    crossing = result["promotion_event"]
    return CertResult(
        start=start,
        window_end=end,
        certified=bool(result["promoted"]),
        crossing=None if crossing is None else int(crossing),
        selected=selected,
        labels=int(result["labels_queried"]),
        scout_events=int(result["scout_events_processed"]),
        cert_events=int(result["monitor_events_processed"]),
        candidate_ids={g: (None if v is None else str(v)) for g, v in named.items()},
    )


def candidate_actions(family: dict[str, Any], cert: CertResult) -> np.ndarray:
    """Per-event action of the selected context policy (incumbent where nothing is selected)."""
    out = np.asarray(family["incumbent"], dtype=int).copy()
    contexts = np.asarray(family["contexts"], dtype=int)
    for group, row in cert.selected.items():
        if row is not None:
            use = contexts == group
            out[use] = np.asarray(family["actions"][row], dtype=int)[use]
    return out


@dataclass(frozen=True)
class RollbackResult:
    alarm: int | None
    labels: int
    processed: int


def run_rollback_monitor(
    *,
    start: int,
    end: int,
    deployed: np.ndarray,
    incumbent: np.ndarray,
    y: np.ndarray,
    uniforms: np.ndarray,
    label_cap: int,
) -> RollbackResult:
    """Rollback e-process: deployed-minus-incumbent harm beyond the amortised rollback cost.

    The same monitor (rate 0.2, alpha 0.015, bound, amortisation horizon n - start) is
    attached to every arm that deploys a non-incumbent policy (rollback parity).
    """
    if start >= end or label_cap < 1:
        return RollbackResult(None, 0, 0)
    deployment_length = N_EVENTS - start
    threshold = ROLLBACK_COST / deployment_length
    process = BoundedMeanEProcess(bound=COST_BOUND / QUERY_RATE + threshold, alpha=ROLLBACK_ALPHA)
    harm = _cost(deployed[start:end], y[start:end]) - _cost(incumbent[start:end], y[start:end])
    labels = processed = 0
    for relative, event in enumerate(range(start, end)):
        if labels >= label_cap:
            break
        queried = bool(uniforms[event] < QUERY_RATE)
        processed += 1
        labels += int(queried)
        estimate = harm[relative] / QUERY_RATE if queried else 0.0
        if process.update(estimate - threshold) >= -np.log(ROLLBACK_ALPHA):
            return RollbackResult(event, labels, processed)
    return RollbackResult(None, labels, processed)


# ------------------------------------------------------------------------------------
# Arm state machine -> policy timeline (learner-side decisions only)
# ------------------------------------------------------------------------------------
INCUMBENT, REFERENCE, CANDIDATE = 0, 1, 2


@dataclass
class Timeline:
    """Which policy acts at each event, plus every timeline marker."""

    response: str
    policy: np.ndarray
    trigger: int | None = None
    revert_start: int | None = None
    cert_start: int | None = None
    cert_complete: int | None = None
    deploy: int | None = None
    certified: bool = False
    cert_infeasible: bool = False
    reference_rollback: int | None = None
    candidate_rollback: int | None = None
    switches: int = 0
    rollbacks: int = 0
    q1_labels: int = 0
    cert_labels: int = 0
    rollback_labels: int = 0
    compute_units: int = 0

    @property
    def total_labels(self) -> int:
        return self.q1_labels + self.cert_labels + self.rollback_labels

    @property
    def intervention_cost(self) -> float:
        return SWITCH_COST * self.switches + ROLLBACK_COST * self.rollbacks


def build_timeline(
    *,
    response: str,
    rollback_on: bool,
    q1: Q1Result,
    cert: CertResult | None,
    cert_candidate: np.ndarray | None,
    family: dict[str, Any],
    incumbent: np.ndarray,
    reference: np.ndarray,
    y: np.ndarray,
    uniforms: np.ndarray,
    deploy_rule: str = "window_end",
    coverage: str = "short",
) -> Timeline:
    """Registered state machine (see protocol section 2).

    trigger t_a -> revert acts from t_a + 1 (revert, revert_while_certifying);
    certification starts at t_a + 1 and runs CERT_WINDOW events (certify_promote,
    revert_while_certifying); the certified candidate acts from the window end
    (``window_end``; optional waiting) or from crossing + 1 (``crossing``).
    """
    if response not in RESPONSES:
        raise ValueError(f"unknown response {response}")
    if deploy_rule not in {"window_end", "crossing"}:
        raise ValueError("deploy_rule must be window_end or crossing")
    policy = np.zeros(N_EVENTS, dtype=np.int8)
    line = Timeline(response=response, policy=policy, q1_labels=q1.labels)
    line.compute_units = q1.processed
    line.trigger = q1.trigger
    if q1.trigger is None or response == "continue":
        return line
    trigger = q1.trigger
    reverts = response in {"revert", "revert_while_certifying"}
    certifies = response in {"certify_promote", "revert_while_certifying"}

    deploy: int | None = None
    if certifies:
        line.cert_start = trigger + 1
        if cert is None:
            line.cert_infeasible = True
        else:
            line.cert_complete = cert.window_end
            line.certified = cert.certified and any(v is not None for v in cert.selected.values())
            line.cert_labels = cert.labels
            line.compute_units += (
                cert.scout_events * len(family["candidate_ids"]) + cert.cert_events
            )
            if line.certified:
                deploy = cert.window_end
                if deploy_rule == "crossing" and cert.crossing is not None:
                    deploy = cert.crossing + 1
                if deploy >= N_EVENTS:
                    deploy = None
    line.deploy = deploy

    cap_left = ROLLBACK_LABEL_CAP
    if reverts:
        line.revert_start = trigger + 1
        policy[trigger + 1 :] = REFERENCE
        line.switches += 1
        if rollback_on:
            segment_end = deploy if deploy is not None else N_EVENTS
            res = run_rollback_monitor(
                start=trigger + 1,
                end=segment_end,
                deployed=reference,
                incumbent=incumbent,
                y=y,
                uniforms=uniforms,
                label_cap=cap_left,
            )
            cap_left -= res.labels
            line.rollback_labels += res.labels
            line.compute_units += res.processed
            if res.alarm is not None:
                line.reference_rollback = res.alarm
                line.rollbacks += 1
                policy[res.alarm + 1 :] = INCUMBENT
    if deploy is not None and cert_candidate is not None:
        policy[deploy:] = CANDIDATE
        line.switches += 1
        if rollback_on:
            res = run_rollback_monitor(
                start=deploy,
                end=N_EVENTS,
                deployed=cert_candidate,
                incumbent=incumbent,
                y=y,
                uniforms=uniforms,
                label_cap=cap_left,
            )
            line.rollback_labels += res.labels
            line.compute_units += res.processed
            if res.alarm is not None:
                line.candidate_rollback = res.alarm
                line.rollbacks += 1
                policy[res.alarm + 1 :] = INCUMBENT
    if line.total_labels > total_label_cap(coverage):
        raise RuntimeError("hard label cap exceeded")
    return line


# ------------------------------------------------------------------------------------
# Evaluator-side scoring
# ------------------------------------------------------------------------------------
def deployed_actions(
    line: Timeline, incumbent: np.ndarray, reference: np.ndarray, cand: np.ndarray | None
) -> np.ndarray:
    out = incumbent.copy()
    out[line.policy == REFERENCE] = reference[line.policy == REFERENCE]
    if cand is not None:
        out[line.policy == CANDIDATE] = cand[line.policy == CANDIDATE]
    return out


def evaluate_timeline(
    line: Timeline,
    *,
    incumbent: np.ndarray,
    reference: np.ndarray,
    cand: np.ndarray | None,
    y: np.ndarray,
    oracle: OracleView,
) -> dict[str, float]:
    """Primary utility ``expected_net_gain_vs_incumbent``:

    sum_t [E c(incumbent_t) - E c(deployed_t)] under the oracle probabilities, minus
    SWITCH_COST per policy switch and ROLLBACK_COST per rollback. Realised twin uses
    the realised labels.
    """
    actions = deployed_actions(line, incumbent, reference, cand)
    exp_gain = expected_cost(incumbent, oracle.probability) - expected_cost(
        actions, oracle.probability
    )
    real_gain = _cost(incumbent, y) - _cost(actions, y)
    cost = line.intervention_cost
    return {
        "expected_net_gain_vs_incumbent": float(exp_gain.sum() - cost),
        "expected_gross_gain": float(exp_gain.sum()),
        "realized_net_gain_vs_incumbent": float(real_gain.sum() - cost),
    }


# ------------------------------------------------------------------------------------
# One stream -> rows
# ------------------------------------------------------------------------------------
def run_stream(
    seed: int,
    *,
    device: str = "cpu",
    deploy_rule: str = "window_end",
    onsets: Sequence[str] | None = None,
    coverages: Sequence[str] | None = None,
    bundle: StreamBundle | None = None,
    oracle_override: dict[str, OracleView] | None = None,
    shift: float = DETERIORATION_SHIFT,
) -> list[dict[str, Any]]:
    """All cells x responses for one seed (every seed enters every cell)."""
    bundle = bundle or build_stream(seed, device)
    rows: list[dict[str, Any]] = []
    for onset_name in onsets or ONSETS:
        onset = ONSETS[onset_name]
        family, incumbent = family_for_onset(bundle, onset)
        for coverage in coverages or COVERAGE_END:
            y_safe, _ = realised_outcomes(bundle, "safe", N_EVENTS)
            q1 = run_q1_monitor(
                incumbent=incumbent,
                reference=bundle.reference,
                y=y_safe,
                uniforms=bundle.uniforms,
                coverage=coverage,
            )
            t_det = deterioration_start(q1.trigger)
            for state in REFERENCE_STATES:
                y, oracle = realised_outcomes(bundle, state, t_det, shift)
                if oracle_override and state in oracle_override:
                    oracle = oracle_override[state]
                cert = (
                    run_certification(
                        family=family,
                        y=y,
                        uniforms=bundle.uniforms,
                        promotion_config=bundle.promotion_config,
                        start=q1.trigger + 1,
                        coverage=coverage,
                    )
                    if q1.trigger is not None
                    else None
                )
                cand = candidate_actions(family, cert) if cert is not None else None
                for rollback in ROLLBACKS:
                    for response in RESPONSES:
                        line = build_timeline(
                            response=response,
                            rollback_on=rollback == "parity",
                            q1=q1,
                            cert=cert,
                            cert_candidate=cand,
                            family=family,
                            incumbent=incumbent,
                            reference=bundle.reference,
                            y=y,
                            uniforms=bundle.uniforms,
                            deploy_rule=deploy_rule,
                            coverage=coverage,
                        )
                        score = evaluate_timeline(
                            line,
                            incumbent=incumbent,
                            reference=bundle.reference,
                            cand=cand,
                            y=y,
                            oracle=oracle,
                        )
                        rows.append(
                            {
                                "seed": seed,
                                "onset": onset_name,
                                "onset_index": onset,
                                "coverage": coverage,
                                "rollback": rollback,
                                "reference_state": state,
                                "response": response,
                                "deterioration_shift": shift,
                                "deterioration_start": t_det if state == "deteriorating" else -1,
                                "trigger": -1 if line.trigger is None else line.trigger,
                                "alarmed": q1.trigger is not None,
                                "revert_start": -1
                                if line.revert_start is None
                                else line.revert_start,
                                "cert_start": -1 if line.cert_start is None else line.cert_start,
                                "cert_complete": (
                                    -1 if line.cert_complete is None else line.cert_complete
                                ),
                                "deploy": -1 if line.deploy is None else line.deploy,
                                "certified": line.certified,
                                "cert_infeasible": line.cert_infeasible,
                                "reference_rollback": (
                                    -1
                                    if line.reference_rollback is None
                                    else line.reference_rollback
                                ),
                                "candidate_rollback": (
                                    -1
                                    if line.candidate_rollback is None
                                    else line.candidate_rollback
                                ),
                                "switches": line.switches,
                                "rollbacks": line.rollbacks,
                                "intervention_cost": line.intervention_cost,
                                "labels_q1": line.q1_labels,
                                "labels_cert": line.cert_labels,
                                "labels_rollback": line.rollback_labels,
                                "labels_total": line.total_labels,
                                "compute_units": line.compute_units,
                                **score,
                            }
                        )
    return rows


def rows_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows)
