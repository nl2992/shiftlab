"""Scenario tapes for the HG x H2c programme (docs/hgxh2c/PROTOCOL.md sections 2-4).

A tape holds [S, T] float64 tensors (CPU-generated, so GPU and CPU runs see identical numbers):
B, C in [0, 1] (incumbent Brier loss and normalised excess economic cost), proxies Bhat, Chat,
the per-event label delay d (int64), common query uniforms U, plus an evaluator-only dict.
Monitors never receive ``tape["eval"]``.

Seeding: torch.Generator seed = base*1e10 + h30*1e5 + seed_index, base from PARTITIONS (disjoint
streams), h30 a 30-bit hash. The latent world (noise, tau, U) is keyed on (family, magnitude, T), so
delay / label regime / proxy cells of one world are paired; the proxy noise is keyed on the full cell.
Seed i of a cell is the same whatever n_seeds is. theta_B, theta_C come from a separate calibration
key (``CAL_KEY``): the sample mean of a pre-change null segment.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import cache

import torch

PARTITIONS = {"dev": 10_000_000, "stress": 20_000_000, "audit": 30_000_000, "confirm": 90_000_000}
CAL_KEY = 5_000_000  # calibration stream, disjoint from every partition
LABEL_FRAC = {"full": 1.0, "b20": 0.2, "b05": 0.05}
MAGS = (0.04, 0.08, 0.16)
M0 = 0.20  # source mean of B and C
PMAX = 0.6  # design-time upper bound of every proxy
RHO = 0.5  # copula correlation of the (B, C) noise
NULL_FAMILIES = ("null_stationary", "null_boundary", "null_ar")
ALT_FAMILIES = ("coshift", "cost_only", "pred_only", "opposed", "gradual", "intermittent", "lagged")
DELAYS = (0, 5, 20)
PROXIES = ("good", "biased", "noisy")


@dataclass(frozen=True)
class ScenarioCell:
    family: str
    magnitude: float
    delay: int
    label_regime: str
    proxy: str
    T: int = 2000

    @property
    def cell_id(self) -> str:
        return f"{self.family}|m{self.magnitude:g}|d{self.delay}|{self.label_regime}|{self.proxy}|T{self.T}"

    @property
    def frac(self) -> float:
        return LABEL_FRAC[self.label_regime]

    @property
    def budget(self) -> int:
        return self.T if self.frac >= 1 else round(self.frac * self.T)


def dev_grid(T: int = 2000) -> list[ScenarioCell]:
    fams = [(f, 0.0) for f in NULL_FAMILIES] + [(f, m) for f in ALT_FAMILIES for m in MAGS]
    return [
        ScenarioCell(f, m, d, r, p, T)
        for f, m in fams for d in DELAYS for r in LABEL_FRAC for p in PROXIES
    ]  # fmt: skip


def _h30(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big") & (2**30 - 1)


def seed_of(partition_base: int, key: str, i: int) -> int:
    return partition_base * 10_000_000_000 + _h30(key) * 100_000 + i


def _phi(z):
    return 0.5 * (1.0 + torch.erf(z / 2**0.5))


def _paths(fam, mag, tau, T):
    """Mean paths mB, mC [S, T] from change times tau [S] (float steps)."""
    S = tau.shape[0]
    t = torch.arange(T, dtype=torch.float64)[None, :]
    on = (t >= tau[:, None]).double()
    mB = torch.full((S, T), M0, dtype=torch.float64)
    mC = mB.clone()
    if fam == "null_boundary":
        mB -= 0.02
        mC -= 0.02
    elif fam == "coshift":
        mB, mC = mB + mag * on, mC + mag * on
    elif fam == "cost_only":
        mC = mC + mag * on
    elif fam == "pred_only":
        mB = mB + mag * on
    elif fam == "opposed":
        mB, mC = mB - mag * on, mC + mag * on
    elif fam == "gradual":
        ramp = ((t - tau[:, None]) / 500.0).clamp(0, 1)
        mB, mC = mB + mag * ramp, mC + mag * ramp
    elif fam == "intermittent":
        burst = on * (((t - tau[:, None]) % 200) < 100).double()
        mB, mC = mB + mag * burst, mC + mag * burst
    elif fam == "lagged":
        mB, mC = mB + mag * on, mC + mag * (t >= tau[:, None] + 200).double()
    return mB, mC


def _noise(fam, g, T):
    zb, zc = torch.randn(2, T, generator=g, dtype=torch.float64)
    zc = RHO * zb + (1 - RHO**2) ** 0.5 * zc
    if (
        fam == "null_ar"
    ):  # AR(0.9) latent Gaussian copula: marginals uniform, conditional mean not constant
        phi, sd = 0.9, (1 - 0.81) ** 0.5
        from scipy.signal import lfilter

        def ar(z):  # stationary start: first shock carries the N(0,1) marginal
            e = z.numpy().copy()
            e[0] /= sd
            return torch.from_numpy(lfilter([sd], [1.0, -phi], e))

        zb, zc = ar(zb), ar(zc)
    return 2 * _phi(zb) - 1, 2 * _phi(zc) - 1


def _proxy(kind, m, m0, amp, e, nz):
    if kind == "good":
        h = m + 0.8 * amp * e
    elif kind == "biased":  # tracks half of the change, overestimates by 0.1
        h = m0 + 0.5 * (m - m0) + 0.1 + 0.8 * amp * e
    else:  # noisy
        h = m + 0.3 * amp * e + 0.08 * nz
    return h.clamp(0.0, PMAX)


@cache
def calibrate(T: int = 2000, n: int = 256) -> tuple[float, float, float, float]:
    """theta_B, theta_C, sd_B, sd_C from a pre-change null segment (separate key)."""
    Bs, Cs = [], []
    for i in range(n):
        g = torch.Generator().manual_seed(seed_of(CAL_KEY, "cal", i))
        eB, eC = _noise("null_stationary", g, T)
        Bs.append(M0 + M0 * eB)
        Cs.append(M0 + M0 * eC)
    B, C = torch.stack(Bs), torch.stack(Cs)
    return float(B.mean()), float(C.mean()), float(B.std()), float(C.std())


def generate(
    cell: ScenarioCell, partition: str, n_seeds: int, device="cpu", seed0: int = 0
) -> dict:
    """Tape for ``cell``: seeds seed0 .. seed0+n_seeds-1 of ``partition``."""
    base = PARTITIONS[partition]
    T = cell.T
    wkey, ckey = f"{cell.family}|{cell.magnitude:g}|{T}", cell.cell_id
    tau, U, eB, eC, nzB, nzC = [], [], [], [], [], []
    for i in range(seed0, seed0 + n_seeds):
        g = torch.Generator().manual_seed(seed_of(base, wkey, i))
        tau.append(200 + torch.rand(1, generator=g, dtype=torch.float64) * 1000)
        U.append(torch.rand(T, generator=g, dtype=torch.float64))
        a, b = _noise(cell.family, g, T)
        eB.append(a), eC.append(b)
        gp = torch.Generator().manual_seed(seed_of(base, ckey, i))
        nz = torch.randn(2, T, generator=gp, dtype=torch.float64)
        nzB.append(nz[0]), nzC.append(nz[1])
    tau = torch.cat(tau).floor()
    U, eB, eC, nzB, nzC = (torch.stack(x) for x in (U, eB, eC, nzB, nzC))
    thB, thC, sdB, sdC = calibrate()
    mB, mC = _paths(cell.family, cell.magnitude, tau, T)
    # shift the paths so the null level equals the calibrated theta exactly
    mB, mC = mB + (thB - M0), mC + (thC - M0)
    ampB, ampC = torch.minimum(mB, 1 - mB), torch.minimum(mC, 1 - mC)
    B, C = mB + ampB * eB, mC + ampC * eC
    Bh = _proxy(cell.proxy, mB, thB, ampB, eB, nzB)
    Ch = _proxy(cell.proxy, mC, thC, ampC, eC, nzC)
    harmB, harmC = mB > thB + 1e-9, mC > thC + 1e-9
    is_null = cell.family in NULL_FAMILIES
    ev = {
        "tau": (torch.full_like(tau, -1) if is_null else tau).long(),
        "mB": mB, "mC": mC, "harm_B": harmB, "harm_C": harmC,
        "null_B": ~harmB.any(1), "null_C": ~harmC.any(1),
    }  # fmt: skip
    tape = {
        "B": B, "C": C, "Bhat": Bh, "Chat": Ch, "U": U, "d": torch.full((n_seeds, T), cell.delay, dtype=torch.long),
        "theta": {"B": thB, "C": thC}, "sd": {"B": sdB, "C": sdC}, "pmax": {"B": PMAX, "C": PMAX},
        "frac": cell.frac, "budget": cell.budget, "eval": ev, "cell": cell, "partition": partition,
        "seeds": torch.arange(seed0, seed0 + n_seeds),
    }  # fmt: skip
    return to_device(tape, device)


def to_device(x, device):
    if isinstance(x, torch.Tensor):
        return x.to(device)
    if isinstance(x, dict):
        return {k: to_device(v, device) for k, v in x.items()}
    return x


def cat_tapes(tapes: list[dict]) -> dict:
    """Stack tapes of equal T along the seed dim (batched cells). Scalars (frac, budget) become [S] tensors."""
    out = {}
    for k in ("B", "C", "Bhat", "Chat", "U", "d"):
        out[k] = torch.cat([t[k] for t in tapes])
    for k in ("frac", "budget"):
        out[k] = torch.cat(
            [
                torch.full(
                    (t["B"].shape[0],), float(t[k]), dtype=torch.float64, device=t["B"].device
                )
                for t in tapes
            ]
        )
    out["eval"] = {k: torch.cat([t["eval"][k] for t in tapes]) for k in tapes[0]["eval"]}
    out["theta"], out["sd"], out["pmax"] = tapes[0]["theta"], tapes[0]["sd"], tapes[0]["pmax"]
    out["sizes"] = [t["B"].shape[0] for t in tapes]
    out["cells"] = [t["cell"] for t in tapes]
    out["partition"] = tapes[0]["partition"]
    out["seeds"] = torch.cat([t["seeds"] for t in tapes])
    return out
