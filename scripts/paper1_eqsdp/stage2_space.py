"""Stage 2 search space: unit cube <-> Stage2Policy configuration (mixed, with module toggles).

Dimensions (all in [0, 1]):
  0 lam    -> EQSDp lambda in [0.95, 0.995]
  1 gamma  -> [0.1, 0.5]
  2 rho0   -> 0 (gate off) if u < 0.05, else log-uniform in [0.005, 0.2]   (Stage 1 grid .01-.1, widened 2x)
  3 s      -> [0, 2]                                                        (Stage 1: 0, 1)
  4 h      -> round(12 u)                                                   (Stage 1: 0, 6)
  5 floor  -> [0, 0.3]                                                      (Stage 1: 0.1)
  6 stop   -> 10 equal bins: none, 900, 1000, ..., 1600, 1750
  7 bw     -> module B weight: 0 (off) if u < 0.1 else u
  8 gs     -> module G strength: 0 (off) if u < 0.1 else 1.5 u
"""

from __future__ import annotations

import numpy as np

NAMES = ["lam", "gamma", "rho0", "s", "h", "floor", "stop", "bw", "gs"]
DIM = len(NAMES)
STOP_BINS = (None, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1750)


def to_cfg(u) -> dict:
    u = np.clip(np.asarray(u, dtype=float), 0.0, 1.0)
    rho0 = 0.0 if u[2] < 0.05 else 0.005 * 40.0 ** ((u[2] - 0.05) / 0.95)
    return {
        "lam": round(0.95 + 0.045 * u[0], 4),
        "gamma": round(0.1 + 0.4 * u[1], 4),
        "rho0": round(rho0, 5),
        "s": round(2.0 * u[3], 4),
        "h": round(12 * u[4]),
        "floor": round(0.3 * u[5], 4),
        "stop_h": STOP_BINS[min(int(u[6] * 10), 9)],
        "bw": 0.0 if u[7] < 0.1 else round(float(u[7]), 4),
        "gs": 0.0 if u[8] < 0.1 else round(1.5 * float(u[8]), 4),
    }


def ablate(cfg: dict, module: str) -> dict:
    c = dict(cfg)
    if module == "B":
        c["bw"] = 0.0
    elif module == "G":
        c["gs"] = 0.0
    elif module == "stop":
        c["stop_h"] = None
    elif module == "gate":
        c["rho0"] = 0.0
    else:
        raise ValueError(module)
    return c
