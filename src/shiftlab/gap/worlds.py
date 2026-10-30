"""Synthetic generators G3-G6 and delay models for the mandate-gap-closure study (synthetic only).

Every generator returns a stream dict understood by ``shiftlab.gap.engine`` (arrays (S, T)) plus an
evaluator-only ``truth`` dict holding three separately measured ground-truth dimensions per step:
``discrepancy`` (RBF MMD^2 of the joint law vs the source), ``predictive`` (change of mean Brier-type
loss) and ``harm`` (change of expected decision cost of the fixed deployed policy). ``truth`` is never
passed to an algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from shiftlab.sota_search import generators as g

D = g.D
W_SRC, B_SRC, TAU = g.W_SRC, g.B_SRC, g.TAU
FN0, FP0 = g.FN_COST, g.FP_COST


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


# --------------------------------------------------------------------------------------------- regimes
@dataclass(frozen=True)
class Regime:
    kind: str = "none"  # none | concept | cov_benign | cov_inform | prior | subgroup | cost
    delta: float = 0.0
    fn: float = FN0  # realised false-negative cost in this regime (deployed policy is unchanged)

    def terms(self):
        dmu, dw, db, dsub = np.zeros(D), np.zeros(D), 0.0, 0.0
        if self.kind == "cov_benign":
            dmu[2] = self.delta
        elif self.kind == "cov_inform":
            dmu[0] = self.delta
        elif self.kind == "prior":
            db = self.delta
        elif self.kind == "concept":
            dw[0], dw[1] = -self.delta, self.delta
        elif self.kind == "subgroup":
            dsub = -self.delta
        elif self.kind not in ("none", "cost"):
            raise ValueError(self.kind)
        return dmu, dw, db, dsub


@dataclass(frozen=True)
class LogitWorld:
    """Regime-indexed logistic world. ``regimes[0]`` is the source."""

    regimes: tuple = (Regime(),)
    family: str = "G1"  # 'G1' linear / 'G2' nonlinear truth
    T: int = 2000
    t0: int = 500  # no regime change before t0 (reference period)
    ar_rho: float = 0.0  # AR(1) latent logit noise (G6 dependence)
    ar_sigma: float = 0.0
    cluster_len: int = 0  # >0: block-shared logit random effect with this block length
    cluster_sigma: float = 0.0
    harm_thr: float = 0.10
    name: str = ""
    sub_thr: float = 1.0  # subgroup = {x_2 > sub_thr}


def markov_path(P: np.ndarray, S: int, T: int, t0: int, rng) -> np.ndarray:
    """Regime paths: regime 0 before t0, then a Markov chain from regime 0 with transition matrix P."""
    K = P.shape[0]
    z = np.zeros((S, T), dtype=np.int64)
    cur = np.zeros(S, dtype=np.int64)
    cum = np.cumsum(P, 1)
    u = rng.random((S, T))
    for t in range(T):
        if t >= t0:
            cur = (u[:, t][:, None] > cum[cur]).sum(1)
            cur = np.minimum(cur, K - 1)
        z[:, t] = cur
    return z


def transition(K: int, persistence: float, structure: str = "jump") -> np.ndarray:
    P = np.full((K, K), (1 - persistence) / max(K - 1, 1))
    if structure == "cycle":
        P = np.zeros((K, K))
        for k in range(K):
            P[k, (k + 1) % K] = 1 - persistence
    np.fill_diagonal(P, persistence)
    return P


def _noise(rng, S, T, w: LogitWorld):
    u = np.zeros((S, T))
    if w.ar_sigma > 0 and w.ar_rho > 0:
        e = rng.standard_normal((S, T))
        a = np.sqrt(1 - w.ar_rho**2)
        cur = rng.standard_normal(S)
        for t in range(T):
            cur = w.ar_rho * cur + a * e[:, t]
            u[:, t] = w.ar_sigma * cur
    if w.cluster_len > 0 and w.cluster_sigma > 0:
        nb = -(-T // w.cluster_len)
        blk = rng.standard_normal((S, nb)) * w.cluster_sigma
        u += np.repeat(blk, w.cluster_len, 1)[:, :T]
    return u


def _logit_sample(rng, w: LogitWorld, z: np.ndarray):
    S, T = z.shape
    tab = [r.terms() for r in w.regimes]
    dmu = np.stack([a for a, _, _, _ in tab])
    dw = np.stack([b for _, b, _, _ in tab])
    db = np.array([c for _, _, c, _ in tab])
    dsub = np.array([d for _, _, _, d in tab])
    fn = np.array([r.fn for r in w.regimes])
    x = rng.standard_normal((S, T, D)) + dmu[z]
    logit = (x * (W_SRC + dw[z])).sum(-1) + B_SRC + db[z] + dsub[z] * (x[..., 2] > w.sub_thr)
    if w.family == "G2":
        logit = logit + g.nonlinear_term(x)
    u = _noise(rng, S, T, w)
    y = (rng.random((S, T)) < sigmoid(logit + u)).astype(np.int8)
    p = sigmoid(x @ W_SRC + B_SRC)
    act = (p >= TAU).astype(float)
    loss = act * (1 - y) * FP0 + (1 - act) * y * fn[z]
    return x, y, p, act, loss, sigmoid(logit)


def _mmd(a, b, gamma=0.25):
    return max(g._rbf_mmd2(a, b, gamma), 0.0)


@lru_cache(maxsize=128)
def regime_effects(w: LogitWorld, n: int = 30_000):
    """Evaluator-only per-regime (discrepancy, predictive, harm) vs the source regime."""
    rng = np.random.default_rng(424242)
    out = []
    base = None
    for k in range(len(w.regimes)):
        z = np.full((1, n), k, dtype=np.int64)
        x, y, p, _act, loss, _ = _logit_sample(np.random.default_rng(424242 + k), w, z)
        x, y, p, loss = x[0], y[0], p[0], loss[0]
        brier = ((p - y) ** 2).mean()
        cost = loss.mean()
        cur = np.c_[x[:1200], y[:1200]]
        if k == 0:
            base = (brier, cost, cur)
            out.append((0.0, 0.0, 0.0))
        else:
            out.append((_mmd(base[2], cur), brier - base[0], cost - base[1]))
    del rng
    return np.array(out)


def _truth_from_regimes(w: LogitWorld, z: np.ndarray) -> dict:
    eff = regime_effects(w)
    return {
        "discrepancy": eff[z, 0],
        "predictive": eff[z, 1],
        "harm": eff[z, 2],
        "thr": w.harm_thr,
        "regime": z,
    }


def source_risks(w: LogitWorld, S: int = 60, seed: int = 31337) -> dict:
    """Nominal source risks from an independent source-only stream of the same world (noise included)."""
    z = np.zeros((S, w.T), dtype=np.int64)
    _x, _y, _p, _a, loss, _ = _logit_sample(np.random.default_rng(seed), w, z)
    # Brier risk: recompute
    rng = np.random.default_rng(seed)
    _x, y, p, _a, _l, _ = _logit_sample(rng, w, z)
    return {"cost": float(loss.mean()), "brier": float(((p - y) ** 2).mean())}


def make_stream(
    w: LogitWorld, S: int, seed: int, P: np.ndarray | None = None, z: np.ndarray | None = None
) -> dict:
    rng = np.random.default_rng(seed)
    if z is None:
        z = (
            markov_path(P, S, w.T, w.t0, rng)
            if P is not None
            else np.zeros((S, w.T), dtype=np.int64)
        )
    x, y, p, act, loss, pi = _logit_sample(rng, w, z)
    stream = {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "score": p,
        "loss": loss,
        "brier": (p - y) ** 2,
        "proxy_brier": p * (1 - p),
        "proxy_cost": act * (1 - p) * FP0 + (1 - act) * p * FN0,
        "pi_true": pi,
        "group": x[..., 2] > w.sub_thr,
        "r0": source_risks(w),
        "pmax": {"brier": 0.25, "cost": FN0 / 6.0},
        "truth": _truth_from_regimes(w, z),
        "world": w,
    }
    return stream


def scheduled_regimes(
    shape: str, T: int, t0: int, ramp: int = 200, length: int = 400, period: int = 600
):
    """0/1 regime path from a deterministic schedule (regime 1 = shifted)."""
    m = g.schedule(shape, T, t0, ramp, length, period)
    return (m >= 0.5).astype(np.int64)


# ------------------------------------------------------------------------------------------ G5 proxies
def apply_proxy(stream: dict, mode: str, t0: int = 800, length: int = 400) -> dict:
    """Return a copy with corrupted proxies (G5). The corruption is a property of the proxy model."""
    out = dict(stream)
    _S, T = stream["loss"].shape
    tt = np.arange(T)[None, :]
    after = tt >= t0
    window = (tt >= t0) & (tt < t0 + length)
    x2 = stream["x"][..., 2]
    for ch, key in (("brier", "proxy_brier"), ("cost", "proxy_cost")):
        pm = stream["pmax"][ch]
        pr = stream[key].copy()
        if mode == "accurate":
            new = pr
        elif mode == "static_bias":
            new = np.clip(pr + 0.25 * pm, 0, pm)
        elif mode == "bias_after_shift":
            new = np.where(after, np.clip(pr + 0.4 * pm, 0, pm), pr)
        elif mode == "anti":
            new = np.where(after, pm - pr, pr)
        elif mode == "subgroup":
            new = np.where(x2 > 1.0, pm - pr, pr)
        elif mode == "calibration":
            new = pm * (np.clip(pr / pm, 1e-6, 1) ** 0.35)
        elif mode == "recover":
            new = np.where(window, pm - pr, pr)
        elif mode.startswith(
            "blend"
        ):  # after the shift the proxy is a blend of accurate (0) and anti-informative (1)
            sv = float(mode[5:])
            new = np.where(after, (1 - sv) * pr + sv * (pm - pr), pr)
        elif mode == "oracle_adapt":
            pi = stream["pi_true"]
            p = stream["p"]
            if ch == "brier":
                new = pi * (1 - p) ** 2 + (1 - pi) * p**2
            else:
                act = (p >= TAU).astype(float)
                new = act * (1 - pi) * FP0 + (1 - act) * pi * FN0
            new = np.clip(new, 0, pm * 4)
        else:
            raise ValueError(mode)
        out[key] = np.clip(new, 0.0, pm)  # proxy models declare their output range [0, pmax]
    out["proxy_mode"] = mode
    return out


# ------------------------------------------------------------------------------------------ G6 delays
def delays(
    kind: str, S: int, T: int, loss: np.ndarray | None = None, d: int = 5, seed: int = 0
) -> np.ndarray:
    rng = np.random.default_rng(777_000 + seed)
    if kind == "fixed":
        return np.full((S, T), d, dtype=np.int64)
    if kind == "uniform":  # random independent delay, mean d
        return rng.integers(0, 2 * d + 1, (S, T))
    if kind == "geometric":  # heavier random independent delay, mean d
        return rng.geometric(1.0 / (d + 1.0), (S, T)) - 1
    if (
        kind == "outcome"
    ):  # errors are reported fast, correct outcomes slowly (outcome-dependent delay)
        assert loss is not None
        return np.where(loss > 0, 2, 6 * d).astype(np.int64)
    if kind == "outcome_rev":  # errors reported slowly
        assert loss is not None
        return np.where(loss > 0, 6 * d, 2).astype(np.int64)
    if kind == "heavy":  # long pending queues
        return np.minimum((rng.pareto(1.3, (S, T)) * d * 2).astype(np.int64), T)
    if kind == "burst":  # labels released in batches every 4d steps
        B = max(4 * d, 1)
        base = np.arange(T)[None, :] + rng.integers(0, d + 1, (S, T))
        return (-(-base // B) * B - np.arange(T)[None, :]).astype(np.int64)
    raise ValueError(kind)


# ------------------------------------------------------------------------------------------ G4 finance
@dataclass(frozen=True)
class FinWorld:
    betas: tuple = (1.0, 0.3, -1.0)  # signal-to-return loading by regime (source first)
    T: int = 2000
    t0: int = 500
    nu: float = 4.0
    omega: float = 0.05
    a: float = 0.10
    b: float = 0.85
    kappa: float = 0.40  # signal scale
    tc: float = 0.02  # transaction cost per unit turnover
    clip_c: float = 2.0  # loss clipping (extreme but bounded)
    act_thr: float = 0.3
    harm_thr: float = 0.03
    name: str = "G4"


def _fin_sample(w: FinWorld, rng, z: np.ndarray):
    S, T = z.shape
    beta = np.array(w.betas)[z]
    sig = rng.standard_normal((S, T))
    zs = rng.standard_t(w.nu, (S, T)) / np.sqrt(w.nu / (w.nu - 2))
    h = np.empty((S, T))
    r = np.empty((S, T))
    hp = np.full(S, w.omega / (1 - w.a - w.b))
    rp = np.zeros(S)
    for t in range(T):
        ht = w.omega + w.a * rp**2 + w.b * hp
        h[:, t] = ht
        rt = beta[:, t] * w.kappa * sig[:, t] * np.sqrt(ht) + np.sqrt(ht) * zs[:, t]
        r[:, t] = rt
        hp, rp = ht, rt
    a = np.where(sig > w.act_thr, 1.0, np.where(sig < -w.act_thr, -1.0, 0.0))
    prev = np.concatenate([np.zeros((S, 1)), a[:, :-1]], 1)
    pnl = a * r - w.tc * np.abs(a - prev) * np.sqrt(h)
    c = w.clip_c
    loss = np.clip(0.5 - pnl / (2 * c), 0.0, 1.0)
    f = w.kappa * sig * np.sqrt(h)
    brier = np.clip((r - f) ** 2 / c**2, 0.0, 1.0)
    pf = a * f - w.tc * np.abs(a - prev) * np.sqrt(h)
    proxy_cost = np.clip(0.5 - pf / (2 * c), 0.0, 1.0)
    proxy_brier = np.clip(h / c**2, 0.0, 1.0)
    return sig, h, r, a, loss, brier, proxy_cost, proxy_brier


@lru_cache(maxsize=32)
def fin_effects(w: FinWorld, n: int = 60_000):
    out = []
    base = None
    for k in range(len(w.betas)):
        z = np.full((20, n // 20), k, dtype=np.int64)
        sig, h, r, _a, loss, brier, *_ = _fin_sample(w, np.random.default_rng(99 + k), z)
        feat = np.c_[sig[:, 200:].ravel()[:1200], (r / np.sqrt(h))[:, 200:].ravel()[:1200]]
        cost, br = loss[:, 200:].mean(), brier[:, 200:].mean()
        if k == 0:
            base = (cost, br, feat)
            out.append((0.0, 0.0, 0.0))
        else:
            out.append((_mmd(base[2], feat, 0.5), br - base[1], cost - base[0]))
    return np.array(out)


def make_fin_stream(w: FinWorld, S: int, seed: int, P: np.ndarray) -> dict:
    rng = np.random.default_rng(seed)
    z = markov_path(P, S, w.T, w.t0, rng)
    sig, h, r, _a, loss, brier, pc, pb = _fin_sample(w, rng, z)
    z0 = np.zeros((60, w.T), dtype=np.int64)
    s0 = _fin_sample(w, np.random.default_rng(2024), z0)
    eff = fin_effects(w)
    return {
        "x": np.stack([sig, np.log(h), r], -1).astype(np.float32),
        "y": (r > 0).astype(np.int8),
        "p": pc,
        "score": np.clip(0.5 + 0.5 * np.tanh(sig), 0, 1),
        "loss": loss,
        "brier": brier,
        "proxy_cost": pc,
        "proxy_brier": pb,
        "r0": {"cost": float(s0[4][:, 200:].mean()), "brier": float(s0[5][:, 200:].mean())},
        "pmax": {"cost": 1.0, "brier": 1.0},
        "truth": {
            "discrepancy": eff[z, 0],
            "predictive": eff[z, 1],
            "harm": eff[z, 2],
            "thr": w.harm_thr,
            "regime": z,
        },
        "world": w,
    }


# ----------------------------------------------------------------------- finite-support heterogeneous null
@dataclass(frozen=True)
class HeteroNull:
    """x in {0,1}; binary loss with P(loss=1|x)=rho_x; proxy h_x. Marginal risk equals r0 for ``shift``
    in {0 (calibrated), 1 (risk re-arranged across x with the marginal risk unchanged)}."""

    h: tuple = (0.05, 0.35)
    shift_mass: float = 0.30
    T: int = 2000
    p_x1: float = 0.5

    def r0(self) -> float:
        return (1 - self.p_x1) * self.h[0] + self.p_x1 * self.h[1]

    def rho(self, shifted: bool):
        if not shifted:
            return self.h
        d0 = self.shift_mass * (1 - self.h[0])  # risk up where proxy is low
        d1 = d0 * (1 - self.p_x1) / self.p_x1  # risk down where proxy is high (marginal unchanged)
        if not (0.0 <= self.h[1] - d1 and self.h[0] + d0 <= 1.0):
            raise ValueError(
                "shift_mass too large: re-arranged risks leave [0, 1]; marginal risk would change"
            )
        return (self.h[0] + d0, self.h[1] - d1)


def make_hetero_stream(hn: HeteroNull, S: int, seed: int, shifted: bool) -> dict:
    rng = np.random.default_rng(seed)
    T = hn.T
    x1 = rng.random((S, T)) < hn.p_x1
    rho = np.where(x1, hn.rho(shifted)[1], hn.rho(shifted)[0])
    loss = (rng.random((S, T)) < rho).astype(float)
    proxy = np.where(x1, hn.h[1], hn.h[0])
    return {
        "x": x1[..., None].astype(np.float32),
        "y": loss.astype(np.int8),
        "p": proxy,
        "score": proxy,
        "loss": loss,
        "brier": loss,
        "proxy_cost": proxy,
        "proxy_brier": proxy,
        "r0": {"cost": hn.r0(), "brier": hn.r0()},
        "pmax": {"cost": max(hn.h), "brier": max(hn.h)},
        "truth": {
            "harm": np.zeros(T),
            "discrepancy": np.zeros(T),
            "predictive": np.zeros(T),
            "thr": 0.1,
        },
    }


@dataclass
class Pool:
    """Named world with its stream factory for registry-friendly bookkeeping."""

    name: str
    kind: str
    make: object = field(repr=False, default=None)
