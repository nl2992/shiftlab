"""Binance split-clock task (Lane B Phase D, gate D1b): 1-bar fast label vs 24-bar gold label.

Rounds, public events and the two frozen momentum policies are exactly those of
``binance_momentum.build_binance_task``. The FAST label is that task's ``Z`` (one forward bar,
released one round later, ``d_f = 1``). The GOLD label is the paired clipped signal loss of the
position held fixed over the next ``H = 24`` bars:

    P_a(t) = p_a(t) * (C_{t+H} / C_t - 1),
    l_a(t) = 0.5 * (1 - clip(P_a(t) / (0.10 * sqrt(H)), -1, 1)),   Z_gold = l_0 - l_1,

so ``Z_gold = 0`` exactly on agreement and ``Z_gold`` lies in [-1, 1]. The sqrt(H) scale keeps the
clipping probability comparable to the 1-bar loss under a random walk. It is released when the close
of bar t+H is archived: ``d_g = H`` rounds. Consecutive gold labels share H-1 bars of return; see
``thinned_phase_mask`` and ``greedy_nonoverlapping`` for the certifying-label rules. Development
data only: bars at or after 2026-01-01 raise ``HoldoutAccessError``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import BINANCE_HOLDOUT_START, UNRELEASED, RealTask, guard_timestamps, release_rounds
from .binance_momentum import (
    BAR,
    PNL_SCALE,
    SLOW_BARS,
    Bars,
    _validated,
    build_binance_task,
    momentum_position,
)

HORIZON = 24
PRICE_FAST_RATIOS = (1 / 24, 1 / 8, 1 / 4)
PRICE_FAST_PRIMARY = 1 / 8
SIGN_AGREEMENT_FLOOR = 0.6


def gold_scale(horizon: int = HORIZON) -> float:
    return PNL_SCALE * float(np.sqrt(horizon))


def _loss(pnl: np.ndarray, horizon: int) -> np.ndarray:
    return 0.5 * (1.0 - np.clip(pnl / gold_scale(horizon), -1.0, 1.0))


@dataclass(frozen=True)
class BinanceSplitTask:
    base: RealTask  # fast channel: base.outcomes.paired_cost
    horizon: int
    gold_paired: np.ndarray  # NaN where C_{t+H} is outside the supplied bars
    gold_available_time: np.ndarray
    gold_release_round: np.ndarray
    first_bar: int  # bar index of round 0

    def __len__(self) -> int:
        return len(self.base)

    @property
    def public(self):
        return self.base.public

    @property
    def fast_paired(self) -> np.ndarray:
        return self.base.outcomes.paired_cost

    @property
    def fast_release_round(self) -> np.ndarray:
        return self.base.outcomes.release_round

    def delays(self) -> dict:
        r = np.arange(len(self))
        fast, gold = self.fast_release_round, self.gold_release_round
        return {
            "fast": sorted({int(v) for v in (fast - r)[fast < UNRELEASED]}),
            "gold": sorted({int(v) for v in (gold - r)[gold < UNRELEASED]}),
            "gold_unreleased": int((gold >= UNRELEASED).sum()),
        }


def build_binance_split(
    bars: Bars, fee: float = 0.001, name: str = "development", horizon: int = HORIZON
) -> BinanceSplitTask:
    bars = _validated(bars)
    guard_timestamps(bars.close_time, BINANCE_HOLDOUT_START, "Binance split-clock bars")
    base = build_binance_task(bars, fee, name)
    c = bars.close
    n_bars = len(c)
    rounds = np.arange(SLOW_BARS + 1, n_bars - 1)
    p0 = momentum_position(c, 24)[rounds]
    p1 = momentum_position(c, SLOW_BARS)[rounds]
    end = rounds + horizon
    ok = end <= n_bars - 1
    ret = np.full(len(rounds), np.nan)
    ret[ok] = c[end[ok]] / c[rounds[ok]] - 1.0
    z = _loss(p0 * ret, horizon) - _loss(p1 * ret, horizon)
    z = np.where(p0 == p1, np.where(ok, 0.0, np.nan), z)  # exactly 0 on agreement
    decision = base.public.decision_time
    open_end = np.where(ok, bars.open_time[np.minimum(end, n_bars - 1)], np.datetime64("NaT", "ns"))
    available = open_end + BAR.astype("timedelta64[ns]")
    release = np.full(len(rounds), UNRELEASED, dtype=np.int64)
    release[ok] = release_rounds(decision, available[ok])
    return BinanceSplitTask(base, horizon, z, available, release, int(rounds[0]))


# ----------------------------------------------------------------------------- overlap rules


def thinned_phase_mask(n_rounds: int, horizon: int = HORIZON, phase: int = 0) -> np.ndarray:
    """Fixed-phase thinning: rounds with ``index % horizon == phase``. The return windows
    ``(t, t+H]`` of selected rounds are disjoint. The phase is a calendar constant fixed before
    any outcome."""
    return (np.arange(n_rounds) % horizon) == phase


def greedy_nonoverlapping(query_rounds, horizon: int = HORIZON) -> np.ndarray:
    """Adaptive rule: a certifying gold query at t is allowed iff t >= s + H for the last allowed
    certifying query s. It depends only on past certifying requests (predictable)."""
    allowed, last = [], -(10**18)
    for t in np.asarray(query_rounds, dtype=np.int64):
        ok = t >= last + horizon
        allowed.append(bool(ok))
        if ok:
            last = int(t)
    return np.asarray(allowed, dtype=bool)


# ----------------------------------------------------------------------------- measurement


def _rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x))
    ranks[order] = np.arange(len(x))
    for v in np.unique(x):
        sel = x == v
        if sel.sum() > 1:
            ranks[sel] = ranks[sel].mean()
    return ranks


def surrogate_quality(task: BinanceSplitTask) -> dict:
    """Fast-versus-gold relationship on disagreement rounds whose gold value exists.

    ``sign_agreement_all`` (primary): among rounds with gold Z != 0, the share where
    sign(Z_fast) == sign(Z_gold), counting Z_fast == 0 as a miss."""
    m = task.public.disagreement & np.isfinite(task.gold_paired)
    zg, zf = task.gold_paired[m], task.fast_paired[m]
    nz = np.abs(zg) > 1e-12
    both = nz & (np.abs(zf) > 1e-12)
    slope, intercept = np.polyfit(zf, zg, 1)
    agree = float((np.sign(zf[nz]) == np.sign(zg[nz])).mean())
    return {
        "n_disagreement_rounds": int(m.sum()),
        "share_fast_exactly_zero": float((np.abs(zf) <= 1e-12).mean()),
        "corr_pearson": float(np.corrcoef(zf, zg)[0, 1]),
        "corr_spearman": float(np.corrcoef(_rank(zf), _rank(zg))[0, 1]),
        "sign_agreement_all": agree,
        "n_gold_nonzero": int(nz.sum()),
        "sign_agreement_both_nonzero": float((np.sign(zf[both]) == np.sign(zg[both])).mean()),
        "slope_gold_on_fast": float(slope),
        "intercept_gold_on_fast": float(intercept),
        "mean_gold": float(zg.mean()),
        "mean_fast": float(zf.mean()),
        "bias_fast_minus_gold": float((zf - zg).mean()),
        "sd_gold": float(zg.std(ddof=1)),
        "sd_fast": float(zf.std(ddof=1)),
        "passes_sign_floor": agree >= SIGN_AGREEMENT_FLOOR,
    }


def gold_autocorrelation(task: BinanceSplitTask, lags=(1, 2, 12, 23, 24, 25, 48)) -> dict:
    """Serial correlation of gold Z over all rounds (agreement rounds carry 0): shows the overlap."""
    z = task.gold_paired
    out = {}
    for lag in lags:
        a, b = z[:-lag], z[lag:]
        ok = np.isfinite(a) & np.isfinite(b)
        out[lag] = float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 3 else None
    return out


def detection_tradeoff(
    mean_shift: float, sd: float, alpha: float = 0.05, label_rate_per_bar: float = 1.0
) -> dict:
    """Gaussian LR/CUSUM approximation: labels needed ~ ln(1/alpha) / KL, KL = shift^2 / (2 sd^2).
    ``label_rate_per_bar`` is labels obtainable per bar. Descriptive only; ignores sequential
    overshoot, clipping and dependence."""
    kl = mean_shift**2 / (2 * sd**2)
    n = float(np.log(1 / alpha) / kl)
    return {
        "kl_per_label": float(kl),
        "labels_needed": n,
        "bars_to_collect": n / label_rate_per_bar,
    }


def run_measurements(root, months, fee: float = 0.001) -> dict:
    from .binance_momentum import load_binance_bars

    bars = load_binance_bars(root, months)
    task = build_binance_split(bars, fee)
    pub = task.public
    q = surrogate_quality(task)
    res = {
        "n_bars": len(bars.close),
        "n_rounds": len(task),
        "disagreement_share": float(pub.disagreement.mean()),
        "delays": task.delays(),
        "quality": q,
        "gold_autocorrelation_all_rounds": gold_autocorrelation(task),
    }
    # Typical reversal size: RMS over months of the monthly mean Z on disagreement rounds (a
    # descriptive stand-in for the size of a persistent change in policy merit).
    month = bars.open_time[task.first_bar : task.first_bar + len(task)].astype("datetime64[M]")
    dis = pub.disagreement & np.isfinite(task.gold_paired)
    shifts = {}
    for key, z in (("fast", task.fast_paired), ("gold", task.gold_paired)):
        means = [
            z[dis & (month == m)].mean()
            for m in np.unique(month)
            if (dis & (month == m)).sum() > 10
        ]
        shifts[key] = float(np.sqrt(np.mean(np.square(means))))
    res["monthly_mean_rms_shift"] = shifts
    share = float(dis.mean())
    res["trade_off_alpha_0.05"] = {
        "disagreement_share": share,
        "fast": detection_tradeoff(shifts["fast"], q["sd_fast"], 0.05, share),
        "gold_thinned_one_per_H_bars": detection_tradeoff(
            shifts["gold"], q["sd_gold"], 0.05, share / task.horizon
        ),
        "gold_if_overlap_ignored_INVALID": detection_tradeoff(
            shifts["gold"], q["sd_gold"], 0.05, share
        ),
    }
    return res


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    from .r2_dev_measurements import BINANCE_ROOT, DEV_MONTHS

    text = json.dumps(run_measurements(BINANCE_ROOT, DEV_MONTHS), indent=2, default=float)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text, encoding="utf-8")
    print(text)
