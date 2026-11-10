"""Loading the J table and building (stream, window, scenario) samples."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import streams
from .embed import embed_window
from .sim import SCENARIOS, Costs

JT = Path("outputs/paper3/transfer/jtable")


@dataclass
class SRec:
    name: str
    family: str
    fold: str
    real: bool
    delay: int
    K: int
    n_early: int
    J: dict  # scenario -> (K, C)
    labels: dict
    rel: np.ndarray
    dis: np.ndarray
    never: np.ndarray


def load_all(root: Path = JT) -> dict[str, SRec]:
    out = {}
    for f in sorted(root.glob("*.npz")):
        name = f.stem
        if name in streams.SEALED_STREAMS:
            raise streams.SealedAccessError(name)
        z = np.load(f, allow_pickle=False)
        K = z["J_primary"].shape[0]
        real = name in streams.REGISTRY
        fam = str(z["family"])
        out[name] = SRec(
            name,
            fam,
            fam,
            real,
            int(z["delay"]),
            K,
            max(2, int(np.ceil(streams.EARLY_FRAC * K))),
            {s: z[f"J_{s}"].astype(float) for s in SCENARIOS},
            {s: z[f"labels_{s}"].astype(float) for s in SCENARIOS},
            z["rel"],
            z["dis"],
            z["never"].astype(float),
        )
    return out


def embed(r: SRec, a: int, b: int, costs: Costs) -> np.ndarray:
    """Embedding from episodes [a, b) only."""
    return embed_window(r.rel[a:b], r.dis[a:b], r.delay, costs)


def windows(r: SRec, scope: str = "all"):
    """Training windows (a, b, target_slice): embed [a,b); target = following episodes.
    scope 'early': only the early window, target = the same window (no later data used)."""
    w = r.n_early
    if scope == "early":
        return [(0, w, slice(0, w))]
    out, a = [], 0
    stride = max(1, w // 2)
    while a + w + 3 <= r.K:
        out.append((a, a + w, slice(a + w, r.K)))
        a += stride
    return out
