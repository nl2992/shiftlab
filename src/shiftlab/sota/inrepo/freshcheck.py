# PORTED UNCHANGED (COMMON_CONTRACT_PORT tier component) -- WP1e, d2a_rar branch.
# Source: origin/research/gave-r-2026-11-06@03289d1d (file last changed in 5521a269), path: src/shiftlab/gaver/freshcheck.py
# Only edit vs source: 'shiftlab.gaver' import paths -> 'shiftlab.sota.inrepo'. See tests/d2a_rar/test_inrepo_ports.py
# (test_port_source_identical) which re-extracts the source with git show and diffs it.
"""FreshCheck (GAVE-R WP3): separate promotion evidence from post-switch keep/rollback evidence.

Development/screening code. Nothing here is a theorem or a confirmatory result.

Validity argument (what is and is not claimed)
----------------------------------------------
* Promotion: unchanged from the repository gate. Episode j uses a started-mixture betting
  e-process on ``-D - h`` at level ``alpha * 2^-(j+1)``; under the conditional null
  ``E[-D_i | F_{i-1}] <= h`` for the released-label filtration it is a nonnegative supermartingale,
  so the probability that any episode falsely promotes is at most ``alpha``.
* At promotion the promotion wealth is *retired* (never read again in mode ``fresh``).
* Keep/rollback: a new started-mixture betting e-process, wealth 1, fed ``D + h`` from labels whose
  *event round* is >= the promotion round (so they are post-switch outcomes) and which have been
  released. Null ``H_keep``: ``E[-D_i | F_{i-1}] >= h`` (challenger still better by the hurdle).
  Under it ``E[(D_i + h)/(1+h) | F] <= 0`` and ``|D+h| <= 1+h``, so the same bounded-betting argument
  gives a supermartingale. An alarm is a statistical rollback signal at level
  ``alpha_rb * 2^-(k+1)`` for the k-th promotion (k=0,1,...), so the family-wise false-rollback
  probability over all post-switch episodes is at most ``alpha_rb``. This is an explicit allocation,
  not a reuse of promotion alpha: promotion errors and rollback errors concern different nulls and
  are budgeted separately.
  The rollback is the alarm AND an economic gate (remaining horizon times the estimated loss of
  the challenger exceeds ``econ_mult * s``); gating can only reduce false rollbacks.
* Assumptions NOT verified here: query rules are predictable (they use released labels and the
  clock only); the conditional null holds; D is observed for the paired losses on requested rounds.
  Under serially dependent D the conditional null can fail (01_HARNESS_MAP discrepancy 2); the
  simulations here use iid Bernoulli outcomes within each regime.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, replace

import numpy as np
from scipy import stats

from shiftlab.dive.atlas_components import (
    CandidateSpec,
    ComposedMethod,
    default_spec,
)
from shiftlab.dive.switching_explore import (
    Config,
    RunResult,
    Stream,
    make_bernoulli_stream,
    run,
    started_gate,
)

WP3_SEED_RANGE = (101120000, 101159999)
STREAM_TAG = 30301
T_DEFAULT = 1000

# ----------------------------------------------------------------------------- scenarios

KINDS = ("persistent", "reversal", "transient", "null", "keepnull")
EARLY, LATE = 0.2, 0.5
WINDOW = {"reversal": 0.25, "transient": 0.10, "keepnull": 0.25}
P_STATES = (
    0.5,
    0.9,
    0.1,
    0.55,
)  # P(Y=1): 0 neutral, 1 challenger better (D=-0.8), 2 harmful (D=+0.8)
P_KEEP = 0.55  # keep-null phase: challenger better by exactly the hurdle (in H_keep)
P_NULL = 0.55  # boundary null: E[-D] = h = 0.1 (1 - 2*0.55 = -0.1)
JITTER = 0.05


@dataclass(frozen=True)
class Wp3Cell:
    kind: str
    onset: float = EARLY
    d: int = 1
    budget_frac: float = 0.1
    s: float = 0.1
    T: int = T_DEFAULT
    c: float = 0.01
    h: float = 0.1
    alpha: float = 0.1

    @property
    def B(self) -> int:
        return round(self.budget_frac * self.T)

    @property
    def cell_id(self) -> str:
        if self.kind == "null":
            return f"null_d{self.d}_b{self.budget_frac:g}_s{self.s:g}"
        return f"{self.kind}_on{self.onset:g}_d{self.d}_b{self.budget_frac:g}_s{self.s:g}"

    @property
    def stable_index(self) -> int:
        return zlib.crc32(self.cell_id.encode("utf-8"))

    def config(self, seed: int) -> Config:
        return Config(
            T=self.T, B=self.B, d=self.d, c=self.c, s=self.s, h=self.h, alpha=self.alpha, seed=seed
        )


def make_stream(cell: Wp3Cell, seed: int) -> Stream:
    """Scripted 3-state path (iid Bernoulli within regime); truth is evaluator-side only."""
    rng = np.random.default_rng([int(seed), STREAM_TAG, cell.stable_index])
    jitter = float(rng.uniform(-JITTER, JITTER))
    T = cell.T
    path = np.zeros(T, dtype=int)
    if cell.kind == "null":
        return make_bernoulli_stream(rng, T, (P_NULL,), path=path)
    tau = round((cell.onset + jitter) * T)
    if cell.kind == "persistent":
        path[tau:] = 1
    else:
        end = min(T, tau + round(WINDOW[cell.kind] * T))
        path[tau:end] = 1
        if cell.kind == "reversal":
            path[end:] = 2
        elif cell.kind == "keepnull":
            path[end:] = 3
    return make_bernoulli_stream(rng, T, P_STATES, path=path)


# ----------------------------------------------------------------------------- method


class FreshCheckMethod(ComposedMethod):
    """Paced-acquisition promote/keep/rollback controller with selectable rollback evidence.

    ``rollback``: ``none`` | ``cusum`` (existing Page-CUSUM) | ``cost_threshold`` | ``fresh`` |
    ``reuse`` (ablation: keep feeding the promotion process, roll back when its wealth drops <1).
    ``reserve_frac``: fraction of B that the pre-promotion phase may not spend (deployed phase may).
    """

    def __init__(
        self,
        rollback: str = "fresh",
        reserve_frac: float = 0.2,
        alpha_rb: float = 0.1,
        econ_mult: float = 1.0,
        kappa: float = 2.0,
    ):
        if rollback not in ("none", "cusum", "cost_threshold", "fresh", "reuse", "ext"):
            raise ValueError(rollback)
        if not 0.0 <= reserve_frac < 1.0:
            raise ValueError("reserve_frac")
        super().__init__(default_spec())
        self.rollback_mode, self.reserve_frac = rollback, float(reserve_frac)
        self.alpha_rb, self.econ_mult, self.kappa = alpha_rb, econ_mult, kappa
        self.name = f"freshcheck_{rollback}_r{reserve_frac:g}"

    def _alpha_j(self, j: int) -> float:
        """Promotion level: geometric spending if rollback can open new episodes, else all alpha."""
        a = self.cfg.alpha
        return a if self.rollback_mode == "none" else a * 2.0 ** -(j + 1)

    def alpha_rb_k(self, k: int) -> float:
        """Rollback level of the k-th post-switch episode (sums to <= alpha_rb)."""
        return self.alpha_rb * 2.0 ** -(k + 1)

    def _init(self) -> None:
        super()._init()
        self.reserve = round(self.reserve_frac * self.cfg.B)
        self.credit = 0.0
        self.n_prom = 0
        self.rb = None
        self.retired_log_e: list[float] = []
        self.rb_events: list[tuple[int, int]] = []  # (consume_round, event_round) of keep-evidence
        self.consumed: list[tuple[int, int, int]] = []  # (round, event_round, act) of all evidence
        self.query_log: list[tuple[int, int, int]] = []  # (round, act, used_after)
        self.stat_trigger_ever = 0  # rollback statistic (no econ gate) fired while deployed

    # hooks (default behaviour = repository promotion gate; subclasses override) -------------
    def _promo_feed(self, ev: int, x: float) -> None:
        self.ep.update(x)
        self.ep_labels.append(x)

    def _promo_alarm(self, t: int) -> bool:
        return bool(self.ep.alarm)

    def _ext_promote(self, t: int) -> None:
        pass

    def _ext_feed(self, x: float) -> None:
        pass

    def _ext_rollback(self, t: int) -> bool:
        return False

    def _rb_econ(self, t: int) -> bool:
        if len(self.post) < 3:
            return False
        loss_rate = float(np.mean(self.post[-self.m :]))  # estimated E[D]: extra loss of challenger
        return (self.cfg.T - t + 1) * loss_rate > self.econ_mult * self.cfg.s

    def decide(self, t: int, released) -> tuple[int, bool]:
        c, mode = self.cfg, self.rollback_mode
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start:
                    self._promo_feed(ev, x)
                    self.consumed.append((t, ev, 0))
            elif ev >= self.promo_t:
                self.post.append(x)
                self.cus = max(0.0, self.cus + x - self.ref)
                self.consumed.append((t, ev, 1))
                if mode == "fresh":
                    self.rb.update(x + c.h)
                    self.rb_events.append((t, ev))
                elif mode == "reuse":
                    self.ep.update(x)
                elif mode == "ext":
                    self._ext_feed(x)
        if self.act == 0:
            ben = self._ben(self.ep_labels, 10)
            cond = bool(self._promo_alarm(t) and ben is not None and self._econ(t, ben))
            if cond:
                self.act, self.promo_t, self.post, self.cus = 1, t, [], 0.0
                self.ref = (-float(ben) - c.h) / 2.0
                self.retired_log_e.append(float(self.ep.proc.log_e_value))
                if mode == "fresh":
                    self.rb = started_gate(1.0 + c.h, self.alpha_rb_k(self.n_prom), c.B)
                    self.ep = None  # promotion wealth retired: unreadable in this mode
                self.n_prom += 1
                if mode == "ext":
                    self._ext_promote(t)
        else:
            if (
                (mode == "fresh" and self.rb.alarm)
                or (mode == "reuse" and self.ep.proc.log_e_value < 0.0)
                or (mode == "cusum" and self.cus >= self.kappa)
            ):
                self.stat_trigger_ever = 1
            if mode == "cusum":
                rollback = self.cus >= self.kappa
            elif mode == "cost_threshold":
                rollback = self._rb_econ(t) and len(self.post) >= self.m
            elif mode == "fresh":
                rollback = bool(self.rb.alarm) and self._rb_econ(t)
            elif mode == "reuse":
                rollback = self.ep.proc.log_e_value < 0.0 and self._rb_econ(t)
            elif mode == "ext":
                rollback = self._ext_rollback(t)
            else:
                rollback = False
            if rollback:
                self.act, self.cus = 0, 0.0
                self.rb = None
                self._new_episode(self.j + 1, t)
        q = self._query(t)
        self.query_log.append((t, self.act, self.used + int(q and self.can_query(t))))
        return self.act, q

    def _query(self, t: int) -> bool:
        """Credit pacing of the spendable budget; the pre-promotion phase cannot touch the reserve."""
        c = self.cfg
        rr = c.T - c.d - t + 1
        if rr <= 0:
            return False
        floor = self.reserve if self.act == 0 else 0
        eff = max(0, c.B - floor - self.used)
        if eff == 0:
            return False
        self.credit += eff / rr
        if self.credit >= 1.0:
            self.credit -= 1.0
            return True
        return False


_PACED = {
    "paced_promo_only": ("none", 0.0),
    "paced_cusum": ("cusum", 0.0),
    "cusum_reserve": ("cusum", 0.2),
    "paced_cost_threshold": ("cost_threshold", 0.0),
    "fresh_reserve": ("fresh", 0.2),
    "fresh_noreserve": ("fresh", 0.0),
    "reuse_reserve": ("reuse", 0.2),
    "reuse_noreserve": ("reuse", 0.0),
}


def make_method(name: str) -> ComposedMethod:
    """Registry used by the runner. ``existing_*`` are untouched repository controllers."""
    base = default_spec()
    if name == "existing_cusum":
        return ComposedMethod(base)
    if name == "existing_promo_only":
        return ComposedMethod(
            CandidateSpec(
                "uniform", "started_mixture_eprocess", "none", "certificate_econ", {}, "promo only"
            )
        )
    if name == "existing_hysteresis":
        return ComposedMethod(
            replace(
                base, decision="hysteresis", params={"decision.k": 2, "decision.econ_mult": 1.0}
            )
        )
    if name == "fresh_reserve_a20":  # sensitivity: family-wise false-rollback budget 0.2
        return FreshCheckMethod("fresh", 0.2, alpha_rb=0.2)
    if name in ("erb", "erb_a05", "two_phase"):
        from shiftlab.sota.inrepo import erb_port

        return erb_port.make(name)
    mode, r = _PACED[name]
    return FreshCheckMethod(mode, r)


METHODS = (
    "existing_promo_only",
    "existing_cusum",
    "existing_hysteresis",
    "paced_promo_only",
    "paced_cusum",
    "cusum_reserve",
    "paced_cost_threshold",
    "fresh_reserve",
    "fresh_noreserve",
    "reuse_reserve",
    "reuse_noreserve",
    "fresh_reserve_a20",
    "erb",
    "erb_a05",
    "two_phase",
)

# ----------------------------------------------------------------------------- evaluator metrics


def score(stream: Stream, cfg: Config, res: RunResult) -> dict:
    """Evaluator-side metrics (uses oracle regime; never visible to methods)."""
    a, T, h = res.actions, cfg.T, cfg.h
    reg, mean, D = stream.truth.regime, stream.truth.regime_mean, stream.D
    prev = np.concatenate(([0], a[:-1]))
    promo = (a == 1) & (prev == 0)
    rb = (a == 0) & (prev == 1)
    out = {
        "J": res.cost / T,
        "loss": res.decision_loss / T,
        "qcost": res.query_cost / T,
        "scost": res.switch_cost / T,
        "queries": res.queries,
        "switches": res.switches,
        "promotions": int(promo.sum()),
        "rollbacks": int(rb.sum()),
        "fp": int(np.any(promo & (mean >= -h - 1e-9))),
        "false_rb": int(np.any(rb & (mean <= -h + 1e-9))),  # true benefit >= h: in H_keep
        "any_promo": int(promo.any()),
        "frac_deployed": float(a.mean()),
    }
    better = np.where(reg == 1)[0]
    end = None
    if len(better) and better[-1] + 1 < T:
        end = int(better[-1]) + 1  # first round index after the challenger-better window
    out["window_end"] = -1 if end is None else end
    if end is None:
        out.update(post_harm=0.0, rb_delay=-1, exposed=0, censored=0)
    else:
        exposed = int(a[end] == 1)
        off = np.where(a[end:] == 0)[0]
        stop = end + (int(off[0]) if len(off) else T - end)
        seg_a, seg_D = a[end:stop], D[end:stop]
        out["post_harm"] = float(np.sum(seg_D[seg_a == 1])) / T  # extra loss vs incumbent / T
        out["rb_delay"] = (stop - end) if exposed else 0
        out["exposed"] = exposed
        out["censored"] = int(exposed and len(off) == 0)
    return out


def run_cell_seed(cell: Wp3Cell, seed: int, methods=METHODS) -> list[dict]:
    cfg, stream = cell.config(seed), make_stream(cell, seed)
    rows = []
    for m in methods:
        meth = make_method(m)
        res = run(stream, meth, cfg)
        assert res.queries <= cfg.B
        extra = {"stat_trigger": int(getattr(meth, "stat_trigger_ever", 0))}
        rows.append(
            {"cell": cell.cell_id, "seed": seed, "method": m, **score(stream, cfg, res), **extra}
        )
    return rows


# ----------------------------------------------------------------------------- statistics


def clopper_pearson(k: int, n: int, conf: float = 0.95) -> tuple[float, float, float]:
    """Two-sided exact interval; returns (rate, lower, upper)."""
    a = (1 - conf) / 2
    lo = 0.0 if k == 0 else float(stats.beta.ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - a, k + 1, n - k))
    return k / n, lo, hi


def paired_bootstrap(
    x: np.ndarray, n_boot: int = 2000, seed: int = 20261106, level: float = 0.95
) -> tuple[float, float, float]:
    """Mean and percentile bootstrap CI of paired differences ``x`` (resampling seeds)."""
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    m = x[idx].mean(axis=1)
    q = (1 - level) / 2
    return float(x.mean()), float(np.quantile(m, q)), float(np.quantile(m, 1 - q))


def grade(rel: float, lo: float, hi: float) -> str:
    """Fair grade of a relative improvement (positive = better) given the CI of the same ratio."""
    r = abs(rel)
    excl = lo > 0 or hi < 0
    sign = "better" if rel > 0 else "worse"
    if r >= 0.10 and excl:
        return f"substantial {sign}"
    if r >= 0.10:
        return f"large but CI spans 0 ({sign})"
    if r >= 0.03 and excl:
        return f"meaningful {sign}"
    if r >= 0.01 and excl:
        return f"small {sign}"
    if r < 0.01:
        return "negligible"
    return f"unresolved ({sign}, CI spans 0)"
