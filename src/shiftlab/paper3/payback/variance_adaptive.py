"""B3: variance-adaptive payback certificates (design: 2026_programme/03B3_VARIANCE_ADAPTIVE_DESIGN.md).

PROOF_SKETCH only (not audited).  A predictable-plug-in empirical-Bernstein (PrPl-EB) lower confidence
sequence (Waudby-Smith and Ramdas 2024, Thm 2; psi_E/4 fix as in ``atlas/certificate_stops.PrPlEBCS``) replaces
B2's range-based normal mixture.  Differences from that port: one-sided threshold 1/alpha_b and NO running
intersection (the intersection is valid for a constant mean only; under drift the CS is for the lambda-weighted
average of conditional means at the *current* prefix).

Interface identical to ``certificates``: start_batch(r, n), observe(s, z, t), lcb_sum(t, h); the gated variant also
has observe_known(s).  ``dirty`` is set whenever the evidence changed (the driver evaluates lcb_sum only then;
between changes lcb_sum is non-increasing, so a certification cannot first occur between events).
"""

from __future__ import annotations

import math

import numpy as np

from .envelope import Envelope

NEG = -math.inf


class PrPl:
    """Incremental PrPl-EB bookkeeping for W in [0,1] (lower side only)."""

    def __init__(self, delta: float, lam_max: float = 0.5, prior_var: float = 0.25):
        if not 0 < delta < 1 or not 0 < lam_max < 1:
            raise ValueError("delta in (0,1), lam_max in (0,1)")
        self.logd, self.lam_max, self.s0 = math.log(1.0 / delta), lam_max, prior_var
        self.n = 0
        self.sw = 0.0
        self.ss = 0.0
        self.sl = 0.0
        self.slw = 0.0
        self.svp = 0.0
        self.lams: list[float] = []

    def update(self, w: float) -> float:
        n = self.n + 1
        sig2 = (
            self.s0 + self.ss
        ) / n  # sigma2hat_{n-1}  (sum over previous n-1 terms, prior mass 1)
        mu_prev = (0.5 + self.sw) / n
        lam = min(math.sqrt(2.0 * self.logd / (sig2 * n * math.log(1.0 + n))), self.lam_max)
        psi = (-math.log1p(-lam) - lam) / 4.0
        self.sl += lam
        self.slw += lam * w
        self.svp += 4.0 * (w - mu_prev) ** 2 * psi
        self.lams.append(lam)
        self.n = n
        self.sw += w
        self.ss += (w - (0.5 + self.sw) / (n + 1)) ** 2
        return lam

    def lo(self) -> float:
        """Lower bound on the lambda-weighted average of E[W_i | past] over the current prefix."""
        if self.n == 0:
            return NEG
        return (self.slw - self.svp - self.logd) / self.sl


class _B3Base:
    def __init__(self, env: Envelope, alpha: float, lam_max=0.5, prior_var=0.25):
        self.env, self.alpha, self.lam_max, self.s0 = env, alpha, lam_max, prior_var
        self.dirty = False

    def _lcb_from(self, pr: PrPl, reqs: list, t: int, h: int) -> float:
        if pr.n == 0:
            return NEG
        lo = pr.lo()
        w = np.asarray(pr.lams)
        w = w / w.sum()
        tab = self.env.future_drop_table(h, t + 1)
        pen = float((w * tab[t - np.asarray(reqs)]).sum())
        return h * (2.0 * lo - 1.0) - pen


class B3Certificate(_B3Base):
    """Labelled-sequence PrPl-EB certificate.  mode='batch': alpha_b = alpha/(b(b+1)), one CS per committed batch;
    mode='single': one CS over all labels in request order with the full alpha."""

    def __init__(self, env, alpha, mode="batch", lam_max=0.5, prior_var=0.25):
        super().__init__(env, alpha, lam_max, prior_var)
        if mode not in ("batch", "single"):
            raise ValueError(mode)
        self.mode = mode
        self.batches: list[dict] = []  # each: r, n, pr, reqs

    def start_batch(self, r: int, n: int):
        b = len(self.batches) + 1
        if self.mode == "single":
            if self.batches:
                self.batches[0]["n"] += n  # same sequence, extended
                return
            ab = self.alpha
        else:
            ab = self.alpha / (b * (b + 1))
        self.batches.append({"r": r, "n": n, "pr": PrPl(ab, self.lam_max, self.s0), "reqs": []})

    def observe(self, s: int, z: float, t: int):
        bt = self.batches[0] if self.mode == "single" else None
        if bt is None:
            for cand in reversed(self.batches):
                if cand["r"] <= s < cand["r"] + cand["n"]:
                    bt = cand
                    break
        if bt is None:
            raise ValueError("label outside any batch")
        bt["pr"].update((z + 1.0) / 2.0)
        bt["reqs"].append(s)
        self.dirty = True

    def lcb_sum(self, t: int, h: int) -> float:
        return max([self._lcb_from(b["pr"], b["reqs"], t, h) for b in self.batches] or [NEG])


class B3GatedCertificate(_B3Base):
    """M2: disagreement-gated.  Sequence = ALL consecutive rounds from the start round; agreement rounds enter with
    Z=0 (known, no label), queried disagreement rounds enter when released.  Usable prefix = rounds before the
    earliest queried-but-unreleased round.  Single CS with full alpha (one sequence)."""

    def __init__(self, env, alpha, lam_max=0.5, prior_var=0.25):
        super().__init__(env, alpha, lam_max, prior_var)
        self.pr = PrPl(alpha, lam_max, prior_var)
        self.reqs: list[int] = []
        self.buf: dict[int, float] = {}
        self.start = None
        self.nxt = None

    def start_batch(self, r: int, n: int = 0):
        if self.start is None:
            self.start, self.nxt = r, r

    def _advance(self):
        while self.nxt in self.buf:
            self.pr.update((self.buf.pop(self.nxt) + 1.0) / 2.0)
            self.reqs.append(self.nxt)
            self.nxt += 1
            self.dirty = True

    def observe_known(self, s: int):
        self.buf[s] = 0.0
        self._advance()

    def observe(self, s: int, z: float, t: int):
        self.buf[s] = z
        self._advance()

    def lcb_sum(self, t: int, h: int) -> float:
        return self._lcb_from(self.pr, self.reqs, t, h)


def plan_batch_size_var(env: Envelope, alpha_b: float, cap: int, sigma2: float = 1.0) -> int:
    """n <= cap minimising sqrt(2 ln(1/alpha_b) sigma2 / n) + mean_{i<n} drop(i); sigma2=1 is B2's plan."""
    la = math.log(1 / alpha_b)
    best, arg = math.inf, 1
    csum = 0.0
    for n in range(1, max(cap, 1) + 1):
        csum += env.drop(n - 1)
        val = math.sqrt(2 * la * sigma2 / n) + csum / n
        if val < best:
            best, arg = val, n
    return arg


def run_events(
    z,
    cert,
    *,
    h: int,
    d: int,
    B: int,
    k: float,
    n_plan: int,
    dis=None,
    truncate: bool = True,
    every_round: bool = False,
):
    """Single-switch driver (same semantics as ``real.run_episode`` / ``sim.run_one``), evaluating lcb_sum only when
    the evidence changed (``every_round=True`` evaluates at every t, for equivalence tests).

    z: length T+1, z[0] unused (evaluator side).  dis: None (ungated) or length T+1 bool disagreement flags
    (gated: query iff dis[t]; agreement rounds are fed as known Z=0).  For gated, ``n_plan`` is the maximum
    window length in rounds and B the disagreement-label budget.
    Returns dict(certified, t, labels, gross, hold)."""
    T = len(z) - 1
    gated = dis is not None
    spent, batch_end, pending, req = 0, 0, {}, 0
    closed = False
    for t in range(1, T + 1):
        for s, val in pending.pop(t, []):
            cert.observe(s, val, t)
        if every_round or getattr(cert, "dirty", True):
            if hasattr(cert, "dirty"):
                cert.dirty = False
            if cert.lcb_sum(t, h) > k and (truncate or t + h - 1 <= T):
                hh = min(h, T - t + 1)
                return {
                    "certified": True,
                    "t": t,
                    "labels": req,
                    "gross": float(z[t : t + hh].sum() - k),
                    "hold": hh,
                }
        if gated:
            if t == 1:
                cert.start_batch(1)
            if not closed and t <= n_plan:
                if dis[t]:
                    if spent < B:
                        spent += 1
                        req += 1
                        if t + d <= T:
                            pending.setdefault(t + d, []).append((t, float(z[t])))
                    else:
                        closed = True
                else:
                    cert.observe_known(t)
            continue
        if t > batch_end and spent < B:
            n = min(n_plan, B - spent)
            spent += n
            cert.start_batch(t, n)
            batch_end = t + n - 1
        if t <= batch_end:
            req += 1
            if t + d <= T:
                pending.setdefault(t + d, []).append((t, float(z[t])))
    return {"certified": False, "t": T, "labels": req, "gross": 0.0, "hold": 0}


def make_sparse_stream(kind: str, spec, seed_parts: tuple, p: float):
    """Sparse-Z synthetic stream with explicit public disagreement D_t ~ Bern(p) (iid), Z = D*(+/-1), mean path
    mu_t = E[Z_t | past] (so the declared class applies to mu, as for +/-1 streams).  ``kind``:
    'sparse_in' (mu = p * drift-class path), 'sparse_null_flat', 'sparse_null_decline:<t_ref>' (the pilot1 tight nulls,
    clipped to [-p, p]; clipping only lowers the mean, so payback stays <= 0).  Returns (mu, z, dis), 1-indexed."""
    from .sim import make_stream

    base = {"sparse_in": "drift"}.get(kind, kind.replace("sparse_", "", 1))
    mu_b, _ = make_stream(base, spec, seed_parts)
    mu = p * mu_b if kind == "sparse_in" else np.clip(mu_b, -p, p)
    rng = np.random.default_rng(np.random.SeedSequence(list(seed_parts) + [99]))
    T = len(mu) - 1
    D = rng.random(T) < p
    m = np.clip(mu[1:] / p, -1, 1)
    sign = np.where(rng.random(T) < (1 + m) / 2, 1.0, -1.0)
    z = np.concatenate([[0.0], np.where(D, sign, 0.0)])
    return mu, z, np.concatenate([[False], D])
