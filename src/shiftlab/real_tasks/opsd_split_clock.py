"""OPSD split-clock task (Lane B Phase D, gate D1): a fast partial-day surrogate channel.

The base task (``opsd_reserve``) is unchanged: round D is a Europe/Berlin local delivery day, the
decision is at 10:00 local on D-1, and the gold label is the full-day paired reserve loss
``Z_D``, released at the end of local day D plus 1 h (usable first at round D+2, ``d_g = 2``).

The fast channel is the partial-day paired loss over the first ``FAST_HOURS`` local clock hours
of day D (local 00:00-07:59), on the same cost scale (divide by 125), so that
``Z_D = Zf_D + R_D`` where ``R_D`` is the rest-of-day paired loss. Under Art. 6(2)(a) each
operating hour's actual load is published at most 1 h after the hour ends, so the last fast hour
(07:00-08:00) is published by 09:00 local, strictly before the next decision (10:00 local on D),
giving ``d_f = 1``. Development windows only: every entry point is guarded by the base task's
holdout guard.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..dive.reserve_costs import decision_cost
from . import (
    OPSD_HOLDOUT_START,
    UNRELEASED,
    PublicRounds,
    RealTask,
    guard_timestamps,
    release_rounds,
)
from .opsd_reserve import (
    BERLIN,
    DEFAULT_WINDOWS,
    FIRST_DAY,
    LOSS_SCALE,
    ONE_HOUR,
    HourlySeries,
    _rolling_tau,
    _utc,
    build_opsd_tasks,
    day_start_utc,
)

FAST_HOURS = 8  # local clock hours 00..07 of the delivery day
FAST_MARGIN_HOURS = 1  # Art. 6(2)(a): actual load published at most 1 h after the operating hour
# Imposed relative prices (gold price = 1 price unit). Interpretation: a fast query is a partial
# review of the overnight/morning settled hours; a gold query is the full-day settlement audit.
PRICE_GOLD = 1.0
PRICE_FAST_RATIOS = (0.125, 0.25, 0.5)
PRICE_FAST_PRIMARY = 0.25


def fast_available_utc(days: np.ndarray) -> np.ndarray:
    """UTC instant at which the fast label of each local day is available: local
    ``FAST_HOURS`` o'clock plus the 1 h publication margin (09:00 local)."""
    local = np.asarray(days).astype("datetime64[D]").astype("datetime64[ns]")
    return _utc(pd.DatetimeIndex(local + np.timedelta64(FAST_HOURS + FAST_MARGIN_HOURS, "h")))


@dataclass(frozen=True)
class SplitClockTask:
    """Base task plus the fast channel (evaluator side). Public side is unchanged."""

    base: RealTask
    fast_paired: np.ndarray  # Zf_t, NaN where the fast label is missing
    rest_paired: np.ndarray  # R_t = Z_t - Zf_t, NaN where gold or fast is missing
    fast_observed: np.ndarray
    fast_available_time: np.ndarray
    fast_release_round: np.ndarray
    fast_hours_differing: (
        np.ndarray
    )  # disagreement hours inside the fast window (public-side count)

    @property
    def public(self) -> PublicRounds:
        return self.base.public

    def __len__(self) -> int:
        return len(self.base)

    def delay_gap_rounds(self) -> np.ndarray:
        """Gold release round minus fast release round where both are released; -1 otherwise."""
        both = self.base.outcomes.released & (self.fast_release_round < UNRELEASED)
        return np.where(both, self.base.outcomes.release_round - self.fast_release_round, -1)


def build_split_clock(
    series: HourlySeries, windows=DEFAULT_WINDOWS, *, fast_hours: int = FAST_HOURS
) -> tuple[dict[str, SplitClockTask], object]:
    """Build the base tasks and attach the fast channel to each window."""
    guard_timestamps(series.actual.index.values, OPSD_HOLDOUT_START, "OPSD series")
    tasks, model = build_opsd_tasks(series, windows)
    last_day = max(
        np.datetime64(t.meta["last_day"]) for t in tasks.values() if t.meta.get("last_day")
    )
    all_days = np.arange(FIRST_DAY, last_day + np.timedelta64(1, "D"), dtype="datetime64[D]")
    starts = day_start_utc(
        np.arange(FIRST_DAY, last_day + np.timedelta64(2, "D"), dtype="datetime64[D]")
    )
    guard_timestamps(starts, OPSD_HOLDOUT_START, "OPSD split-clock table")
    n_hours = (np.diff(starts) // ONE_HOUR.astype("timedelta64[ns]")).astype(np.int64)
    idx = pd.date_range(starts[0], starts[-1], freq="h", inclusive="left")
    actual = series.actual.reindex(idx).to_numpy(float)
    offsets = np.concatenate([[0], np.cumsum(n_hours)])
    local_hour = idx.tz_localize("UTC").tz_convert(BERLIN).hour.to_numpy()
    out_tasks = {}
    for name, task in tasks.items():
        pub, out = task.public, task.outcomes
        n = len(task)
        local_days = (
            pd.DatetimeIndex(pub.round_time).tz_localize("UTC").tz_convert(BERLIN).tz_localize(None)
        ).values.astype("datetime64[D]")
        day_index = np.searchsorted(all_days, local_days)
        zf = np.full(n, np.nan)
        rest = np.full(n, np.nan)
        fast_obs = np.zeros(n, dtype=bool)
        diff_fast = np.zeros(n, dtype=np.int64)
        for r, i in enumerate(day_index):
            rows = slice(offsets[i], offsets[i + 1])
            m = int(n_hours[i])
            a0 = np.array([(int(pub.deployed_action[r]) >> h) & 1 for h in range(m)], dtype=np.int8)
            a1 = np.array(
                [(int(pub.reference_action[r]) >> h) & 1 for h in range(m)], dtype=np.int8
            )
            fast_mask = local_hour[rows] < fast_hours
            diff_fast[r] = int(((a0 != a1) & fast_mask).sum())
            y = actual[rows]
            if not (np.isfinite(y[fast_mask]).all() and local_days[r] not in series.irregular_days):
                continue  # fast label missing at release
            fast_obs[r] = True
            if not pub.disagreement[r]:
                zf[r] = 0.0  # Z = 0 on agreement in both channels
                if out.observed[r]:
                    rest[r] = out.paired_cost[r]
                continue
            tau = _rolling_tau(actual, offsets, int(i))
            c = (
                decision_cost(a0[fast_mask], y[fast_mask], tau)
                - decision_cost(a1[fast_mask], y[fast_mask], tau)
            ).sum() / LOSS_SCALE
            zf[r] = float(c)
            if out.observed[r]:
                rest[r] = out.paired_cost[r] - c
        avail = fast_available_utc(local_days)
        rel = release_rounds(pub.decision_time, avail)
        out_tasks[name] = SplitClockTask(task, zf, rest, fast_obs, avail, rel, diff_fast)
    return out_tasks, model


# ----------------------------------------------------------------------------- measurement

MEASURE_WINDOWS = (
    ("train2016_in_sample", np.datetime64("2016-01-01"), np.datetime64("2016-12-31")),
    *DEFAULT_WINDOWS,
)
SIGN_AGREEMENT_FLOOR = 0.6


def surrogate_quality(task: SplitClockTask) -> dict:
    """Surrogate-gold relationship on labelled disagreement rounds (descriptive).

    ``sign_agreement_all`` (primary): among rounds with gold Z != 0, share where sign(Zf) ==
    sign(Z), counting Zf == 0 as a miss. ``sign_agreement_both_nonzero``: same, restricted to Zf != 0.
    """
    pub, out = task.public, task.base.outcomes
    m = pub.disagreement & out.observed & task.fast_observed
    z, zf = out.paired_cost[m], task.fast_paired[m]
    res: dict = {"n_disagreement_rounds_both_labels": int(m.sum())}
    if m.sum() < 3:
        return res
    nz = np.abs(z) > 1e-12
    both = nz & (np.abs(zf) > 1e-12)
    slope, intercept = np.polyfit(zf, z, 1) if np.ptp(zf) > 0 else (np.nan, np.nan)
    res |= {
        "share_zf_exactly_zero": float((np.abs(zf) <= 1e-12).mean()),
        "share_gold_nonzero": float(nz.mean()),
        "corr_pearson": float(np.corrcoef(zf, z)[0, 1]) if np.ptp(zf) > 0 else None,
        "corr_spearman": float(pd.Series(zf).corr(pd.Series(z), method="spearman")),
        "sign_agreement_all": float((np.sign(zf[nz]) == np.sign(z[nz])).mean())
        if nz.any()
        else None,
        "n_gold_nonzero": int(nz.sum()),
        "sign_agreement_both_nonzero": float((np.sign(zf[both]) == np.sign(z[both])).mean())
        if both.any()
        else None,
        "n_both_nonzero": int(both.sum()),
        "slope_gold_on_fast": float(slope),
        "intercept_gold_on_fast": float(intercept),
        "mean_gold": float(z.mean()),
        "mean_fast": float(zf.mean()),
        "bias_fast_minus_gold": float((zf - z).mean()),
        "sd_gold": float(z.std(ddof=1)),
        "sd_fast": float(zf.std(ddof=1)),
        "rmse_fast_as_gold": float(np.sqrt(((zf - z) ** 2).mean())),
        "uninformative": bool(
            (not nz.any())
            or float((np.sign(zf[nz]) == np.sign(z[nz])).mean()) < SIGN_AGREEMENT_FLOOR
        ),
    }
    return res


def delay_summary(task: SplitClockTask) -> dict:
    out = task.base.outcomes
    gold = out.delay_rounds()
    fast = np.where(
        task.fast_release_round < UNRELEASED,
        task.fast_release_round - np.arange(len(task.fast_release_round)),
        -1,
    )
    return {
        "gold_delay_values": sorted({int(v) for v in gold}),
        "fast_delay_values": sorted({int(v) for v in fast}),
        "gap_values": sorted({int(v) for v in task.delay_gap_rounds()}),
        "fast_hour_clock_gap_to_next_decision_hours": 1.0,
    }


def run_measurements(path) -> dict:
    series = _load(path)
    tasks, model = build_split_clock(series, MEASURE_WINDOWS)
    res = {"ridge_penalty": model.penalty, "windows": {}}
    for name, t in tasks.items():
        pub = t.public
        res["windows"][name] = {
            "n_rounds": len(t),
            "n_disagreement_rounds": int(pub.disagreement.sum()),
            "share_disagreement_rounds_with_a_differing_hour_in_fast_window": float(
                (t.fast_hours_differing[pub.disagreement] > 0).mean()
            )
            if pub.disagreement.any()
            else None,
            "mean_differing_hours_in_fast_window": float(
                t.fast_hours_differing[pub.disagreement].mean()
            )
            if pub.disagreement.any()
            else None,
            "mean_differing_hours_all": float(pub.disagreement_units[pub.disagreement].mean())
            if pub.disagreement.any()
            else None,
            "delay": delay_summary(t),
            "quality": surrogate_quality(t),
        }
    return res


def _load(path):
    from .opsd_reserve import load_opsd_hourly

    return load_opsd_hourly(path)


if __name__ == "__main__":
    import json
    import sys

    from .r2_dev_measurements import OPSD_PATH

    result = run_measurements(OPSD_PATH)
    text = json.dumps(result, indent=2, default=float)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text, encoding="utf-8")
    print(text)
