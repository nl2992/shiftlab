"""Registered analyses of the EIA real-data validity protocol (docs/eia_real_data_validity_protocol.md).

Pure functions: coin construction, exact bounds, and the three analysis loops (null, unmodified,
injected harm). Replicate counts default to the registered values and are parameters only so that
tests can run tiny inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import beta

from shiftlab.dive.eia_injected_harm import injected_paired_cost, onset_index, select_band
from shiftlab.dive.eia_paired_reserve import PairedReserveStream
from shiftlab.dive.orientation_replay import ReplayBatch, replay_batch

PATHS = (("CISO", "2025"), ("CISO", "2026"), ("ERCO", "2025"), ("ERCO", "2026"))
BUDGETS = (0.02, 0.05, 0.10, 0.20)
GATED_AND_HT = ("ungated_ht", "gated_ht_fixed", "gated_ht_paced", "gated_eb_paced")
ONSETS = (0.25, 0.50, 0.75)
EPSILONS = (0.1, 0.0)
ALPHA = 0.05
HOUR = 3600.0
REHEARSAL = "rehearsal_2024"


def registered_cells() -> list[tuple[str, float | None]]:
    """Registered cell order for one path: full feedback, then each arm by budget (17 cells)."""
    cells: list[tuple[str, float | None]] = [("full_feedback", None)]
    cells.extend((arm, budget) for arm in GATED_AND_HT for budget in BUDGETS)
    return cells


def orientation_coins(k: int, n: int, replicates: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(59200000 + k)
    signs = 2 * rng.integers(0, 2, size=(replicates, n)) - 1
    uniforms = rng.random((replicates, n))
    return signs, uniforms


def rerun_coins(k: int, j: int, n: int, replicates: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(59230000 + 100 * k + j)
    signs = 2 * rng.integers(0, 2, size=(replicates, n)) - 1
    uniforms = rng.random((replicates, n))
    return signs, uniforms


def unmodified_coins(k: int, n: int, replicates: int = 200) -> np.ndarray:
    return np.random.default_rng(59220000 + k).random((replicates, n))


def injection_coins(k: int, o: int, n: int, replicates: int = 200) -> np.ndarray:
    return np.random.default_rng(59210000 + 10 * k + o).random((replicates, n))


def clopper_pearson_upper(x: int, n: int, level: float = 0.95) -> float:
    """Exact one-sided upper confidence bound for a binomial proportion."""
    if x >= n:
        return 1.0
    return float(beta.ppf(level, x + 1, n - x))


@dataclass(frozen=True)
class PathData:
    k: int
    stream: PairedReserveStream
    rehearsal: PairedReserveStream

    @property
    def n(self) -> int:
        return len(self.stream.event_time)

    @property
    def tariffs(self) -> np.ndarray:
        return np.ones(self.n)

    @property
    def validation_disagreement(self) -> np.ndarray:
        return np.asarray(self.rehearsal.disagreement, dtype=bool)

    @property
    def validation_tariffs(self) -> np.ndarray:
        return np.ones(len(self.rehearsal.event_time))


def collect_paths(
    streams: list[PairedReserveStream], paths: tuple[tuple[str, str], ...] = PATHS
) -> list[PathData]:
    """Pair each registered path with its respondent's rehearsal stream (index k = position)."""
    by_key = {(s.respondent, s.window): s for s in streams}
    out = []
    for k, (respondent, window) in enumerate(paths):
        if (respondent, window) not in by_key or (respondent, REHEARSAL) not in by_key:
            raise ValueError(f"missing stream for {respondent}/{window} or its rehearsal")
        out.append(PathData(k, by_key[(respondent, window)], by_key[(respondent, REHEARSAL)]))
    return out


def _replay(
    p: PathData,
    arm: str,
    budget: float | None,
    *,
    paired_cost: np.ndarray,
    disagreement: np.ndarray,
    signs: np.ndarray | None,
    uniforms: np.ndarray | None,
    epsilon: float,
) -> ReplayBatch:
    return replay_batch(
        arm,
        paired_cost=paired_cost,
        disagreement=disagreement,
        tariffs=p.tariffs,
        signs=signs,
        uniforms=uniforms,
        validation_disagreement=p.validation_disagreement,
        validation_tariffs=p.validation_tariffs,
        budget_rate=0.0 if budget is None else budget,
        epsilon=epsilon,
        alpha=ALPHA,
    )


def _null_row(
    p: PathData,
    arm: str,
    budget: float | None,
    epsilon: float,
    batch: ReplayBatch,
    stage: str,
) -> dict:
    reps = len(batch.first_alarm)
    alarms = int((batch.first_alarm >= 0).sum())
    upper = clopper_pearson_upper(alarms, reps)
    return {
        "path": p.k,
        "respondent": p.stream.respondent,
        "window": p.stream.window,
        "n": p.n,
        "disagreements": int(np.asarray(p.stream.disagreement).sum()),
        "arm": arm,
        "budget": budget,
        "epsilon": epsilon,
        "replicates": reps,
        "alarms": alarms,
        "rate": alarms / reps,
        "cp_upper": upper,
        "passes": bool(upper <= ALPHA),
        "stage": stage,
        "mean_labels": float(batch.labels.mean()),
        "mean_dollars": float(batch.dollars.mean()),
        "mean_processed": float(batch.processed.mean()),
    }


def null_analysis(
    paths: list[PathData], replicates: int = 1000, rerun_replicates: int = 4000
) -> tuple[pd.DataFrame, dict]:
    """Analysis (a). Returns the cell table and the decision record."""
    cells = registered_cells()
    rows: list[dict] = []
    failing: list[dict] = []
    reruns: list[dict] = []
    all_pass = True
    for p in paths:
        signs, uniforms = orientation_coins(p.k, p.n, replicates)
        for j, (arm, budget) in enumerate(cells):
            fb = arm == "full_feedback"
            cell_rows = {}
            for eps in EPSILONS:
                batch = _replay(
                    p,
                    arm,
                    budget,
                    paired_cost=p.stream.paired_cost,
                    disagreement=p.stream.disagreement,
                    signs=signs,
                    uniforms=None if fb else uniforms,
                    epsilon=eps,
                )
                row = _null_row(p, arm, budget, eps, batch, "original")
                rows.append(row)
                cell_rows[eps] = row
            primary = cell_rows[0.1]
            if primary["passes"]:
                continue
            r_signs, r_uniforms = rerun_coins(p.k, j, p.n, rerun_replicates)
            batch = _replay(
                p,
                arm,
                budget,
                paired_cost=p.stream.paired_cost,
                disagreement=p.stream.disagreement,
                signs=r_signs,
                uniforms=None if fb else r_uniforms,
                epsilon=0.1,
            )
            rerow = _null_row(p, arm, budget, 0.1, batch, "rerun")
            rows.append(rerow)
            ident = {"path": p.k, "cell_index": j, "arm": arm, "budget": budget}
            reruns.append(
                {
                    **ident,
                    "original_alarms": primary["alarms"],
                    "original_cp_upper": primary["cp_upper"],
                    "rerun_alarms": rerow["alarms"],
                    "rerun_cp_upper": rerow["cp_upper"],
                    "rerun_passes": rerow["passes"],
                }
            )
            if not rerow["passes"]:
                all_pass = False
                failing.append(ident)
    decision = {"null_passes": all_pass, "failing_cells": failing, "reruns": reruns}
    return pd.DataFrame(rows), decision


def _hours(p: PathData, idx: int) -> float:
    et = np.asarray(p.stream.event_time, dtype=float)
    return float((et[idx] - et[0]) / HOUR)


def unmodified_analysis(paths: list[PathData], replicates: int = 200) -> pd.DataFrame:
    """Analysis (b): descriptive monitor verdicts on the unmodified streams."""
    rows: list[dict] = []
    for p in paths:
        z, dis = p.stream.paired_cost, p.stream.disagreement
        fb = _replay(
            p,
            "full_feedback",
            None,
            paired_cost=z,
            disagreement=dis,
            signs=np.ones((1, p.n)),
            uniforms=None,
            epsilon=0.1,
        )
        fb_idx = int(fb.first_alarm[0])
        fb_alarm = fb_idx >= 0
        base = {
            "path": p.k,
            "respondent": p.stream.respondent,
            "window": p.stream.window,
            "n": p.n,
            "fullfeedback_alarm": fb_alarm,
            "fullfeedback_alarm_index": fb_idx,
            "fullfeedback_alarm_hours": _hours(p, fb_idx) if fb_alarm else np.nan,
        }
        uniforms = unmodified_coins(p.k, p.n, replicates)
        for arm in GATED_AND_HT:
            for budget in BUDGETS:
                batch = _replay(
                    p,
                    arm,
                    budget,
                    paired_cost=z,
                    disagreement=dis,
                    signs=None,
                    uniforms=uniforms,
                    epsilon=0.1,
                )
                alarmed = batch.first_alarm >= 0
                rows.append(
                    {
                        **base,
                        "arm": arm,
                        "budget": budget,
                        "replicates": replicates,
                        "alarm_probability": float(alarmed.mean()),
                        "agreement_with_fullfeedback": float((alarmed == fb_alarm).mean()),
                        "mean_labels": float(batch.labels.mean()),
                        "mean_dollars": float(batch.dollars.mean()),
                        "mean_processed": float(batch.processed.mean()),
                    }
                )
    return pd.DataFrame(rows)


def classify_alarms(
    first_alarm: np.ndarray, onset: int, n: int, event_time: np.ndarray
) -> dict[str, float]:
    """Pre-onset alarms are never detections; undetected and pre-onset delays are censored."""
    first = np.asarray(first_alarm)
    pre = (first >= 0) & (first < onset)
    det = first >= onset
    et = np.asarray(event_time, dtype=float)
    ev = np.where(det, first - onset, n - onset).astype(float)
    safe = np.where(det, first, 0)
    hr = np.where(det, (et[safe] - et[onset]) / HOUR, (et[-1] - et[onset]) / HOUR)
    return {
        "detection_rate": float(det.mean()),
        "pre_onset_rate": float(pre.mean()),
        "mean_delay_events": float(ev.mean()),
        "median_delay_events": float(np.median(ev)),
        "mean_delay_hours": float(hr.mean()),
        "median_delay_hours": float(np.median(hr)),
    }


def injected_analysis(
    paths: list[PathData], replicates: int = 200, onsets: tuple[float, ...] = ONSETS
) -> pd.DataFrame:
    """Analysis (c): injected under-procurement with known onset (descriptive)."""
    rows: list[dict] = []
    for p in paths:
        s, reh = p.stream, p.rehearsal
        band = select_band(reh.frozen_margin, reh.deployed_action)
        for o, frac in enumerate(onsets):
            onset = onset_index(p.n, frac)
            new_action, z, dis = injected_paired_cost(
                s.deployed_action,
                s.frozen_margin,
                s.reference_action,
                s.demand,
                s.tau,
                onset,
                band,
            )
            base = {
                "path": p.k,
                "respondent": s.respondent,
                "window": s.window,
                "n": p.n,
                "onset_fraction": frac,
                "onset_index": onset,
                "band_low": band[0],
                "band_high": band[1],
                "flipped_events": int((new_action != s.deployed_action).sum()),
                "injected_post_onset_mean_excess": float(z[onset:].mean()),
                "replicates": replicates,
            }
            fb = _replay(
                p,
                "full_feedback",
                None,
                paired_cost=z,
                disagreement=dis,
                signs=np.ones((1, p.n)),
                uniforms=None,
                epsilon=0.1,
            )
            stats = classify_alarms(fb.first_alarm, onset, p.n, s.event_time)
            rows.append(
                {
                    **base,
                    "arm": "full_feedback",
                    "budget": None,
                    "replicates": 1,
                    **stats,
                    "mean_labels": float(fb.labels.mean()),
                    "mean_dollars": float(fb.dollars.mean()),
                }
            )
            uniforms = injection_coins(p.k, o, p.n, replicates)
            for arm in GATED_AND_HT:
                for budget in BUDGETS:
                    batch = _replay(
                        p,
                        arm,
                        budget,
                        paired_cost=z,
                        disagreement=dis,
                        signs=None,
                        uniforms=uniforms,
                        epsilon=0.1,
                    )
                    stats = classify_alarms(batch.first_alarm, onset, p.n, s.event_time)
                    rows.append(
                        {
                            **base,
                            "arm": arm,
                            "budget": budget,
                            **stats,
                            "mean_labels": float(batch.labels.mean()),
                            "mean_dollars": float(batch.dollars.mean()),
                        }
                    )
    return pd.DataFrame(rows)
