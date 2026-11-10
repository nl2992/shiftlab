"""Mechanistic atlas grid: cell spec, space-filling design, stream generator, validity table.

Stream model (adapted from scripts/failure_atlas_v2/regimes.py @8af33afe): on a disagreement the
challenger is right (D=l0-l1=+1) with probability p_t, else the incumbent is (D=-1); agreement gives
D=0. The sign process is a two-state chain with per-event persistence rho and marginal p_t.
Regime schedule (alt stream): p=0.5 before onset (boundary null), p=0.5+Delta during
[onset, onset+dwell), p=0.5-Delta_bad afterwards (stale promotion is harmful).
Null twin: p=0.5 throughout. Informative delay: challenger-correct outcomes (D=+1) are released
inform_mult times later than other outcomes (evaluator-side rule, policies never see it).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

import numpy as np

T = 2000
DELTA_BAD = 0.15


@dataclass(frozen=True)
class Cell:
    cid: int
    onset: int  # event index
    dwell: int  # events the improvement lasts (dwell>=T-onset means persists)
    delta: float  # p_good - 0.5
    rho: float
    delay: int
    informative: bool
    budget_frac: float
    price: float  # c_q per label
    switch_cost: float  # k
    dis: float  # disagreement rate

    @property
    def budget(self) -> int:
        return round(self.budget_frac * T)

    @property
    def end(self) -> int:
        return min(T, self.onset + self.dwell)

    @property
    def persists(self) -> bool:
        return self.end >= T

    def config_hash(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:12]

    def p_schedule(self, null: bool = False) -> np.ndarray:
        p = np.full(T, 0.5)
        if null:
            return p
        p[self.onset : self.end] = 0.5 + self.delta
        p[self.end :] = 0.5 - DELTA_BAD
        return p

    def regime(self, null: bool = False) -> np.ndarray:
        """Evaluator-side: +1 good, 0 neutral, -1 bad."""
        p = self.p_schedule(null)
        return np.sign(np.round(p - 0.5, 9)).astype(int)

    def delays(self, D: np.ndarray) -> np.ndarray:
        d = np.full(D.shape[0], self.delay, dtype=int)
        if self.informative:
            d = np.where(D > 0, self.delay * 4, self.delay)
        return d

    def sample(self, rng: np.random.Generator, null: bool = False) -> np.ndarray:
        p = self.p_schedule(null)
        on = rng.random(T) < self.dis
        v = rng.random(T)
        keep = rng.random(T) < self.rho
        sign = np.empty(T, dtype=bool)
        sign[0] = v[0] < p[0]
        for t in range(1, T):
            sign[t] = sign[t - 1] if keep[t] else (v[t] < p[t])
        bw = rng.random(T) < 0.1
        l0 = np.where(on, sign, bw).astype(np.int8)
        l1 = np.where(on, ~sign, bw).astype(np.int8)
        return np.stack([l0, l1], axis=1)


def design(n: int = 32, seed: int = 20261109) -> list[Cell]:
    """Scrambled-Sobol space-filling design over 7 continuous axes; rho and delay mode stratified."""
    from scipy.stats import qmc

    u = qmc.Sobol(d=7, scramble=True, seed=seed).random(n)
    cells = []
    rhos = [0.0, 0.5, 0.8, 0.95]
    for i in range(n):
        x = u[i]
        onset = int(200 + x[0] * 1000)  # 200..1200
        # dwell fraction of remaining: 0.15..1.0, top 25% of the unit interval = persists
        frac = 0.15 + x[1] * 0.85
        dwell = T if x[1] > 0.75 else int(frac * (T - onset))
        cells.append(
            Cell(
                cid=i,
                onset=onset,
                dwell=max(dwell, 100),
                delta=float(0.10 + x[2] * 0.20),
                rho=rhos[i % 4],
                delay=round(10 + x[3] * 190),
                informative=bool((i // 4) % 2),
                budget_frac=float(0.05 + x[4] * 0.20),
                price=float(0.01 + x[5] * 0.19),
                switch_cost=float(1 + x[6] * 19),
                dis=float(0.10 + ((x[0] * 7.31 + x[3] * 3.17) % 1.0) * 0.40),
            )
        )
    return cells


# Null-assumption validity per gate x mechanism. 'valid' = the claimed null guarantee plausibly
# holds in that cell class; 'invalid' = the null model is violated, so the cell is a STRESS TEST.
# These are statements about assumptions, not proofs; C1's sketch is in C_ATLAS_PROTOCOL.md.
GATES = {
    "gated_mope": "conditional-mean null E[d_t|F_{t-1}]<=0 (iid or martingale-difference signs)",
    "discern": "same conditional-mean null (HT-weighted EB CS)",
    "smcs": "same pairwise conditional null",
    "cusum/ph/edet/wald": "iid ARL / SPRT error rates only; no anytime null guarantee",
    "thinned_iid": "iid after thinning; no dependence correction (valid only if rho^gap ~ 0)",
    "markov_skeleton": "binary Markov, rho<=rho_max, but homogeneous nominal gap (approximation)",
    "c1_gapaware": "binary Markov, rho<=rho_max declared ex ante, actual gaps; any delay (sketch)",
}


def validity(cell: Cell, gate: str, rho_max: float = 0.95) -> str:
    dep = cell.rho > 0
    if gate in ("gated_mope", "discern", "smcs"):
        return (
            "INVALID-null (Markov: E[d|F] != 0)"
            if dep
            else "valid-null (iid); informative delay: sup-argument ok"
            if cell.informative
            else "valid-null (iid)"
        )
    if gate in ("cusum", "page_hinkley", "edetector", "wald_econ"):
        return (
            "no-guarantee (stress)"
            if (dep or cell.informative)
            else "iid-only (no anytime guarantee)"
        )
    if gate == "thinned_iid":
        return "INVALID-null (Markov)" if dep else "valid-null (iid)"
    if gate == "markov_skeleton":
        return "approx (nominal gap)" if dep else "valid-null (conservative)"
    if gate.startswith("c1"):
        rm = 0.80 if "rho80" in gate else rho_max
        return (
            "INVALID-null (rho>rho_max)" if cell.rho > rm else "valid-null (declared bound; sketch)"
        )
    return "n/a"
