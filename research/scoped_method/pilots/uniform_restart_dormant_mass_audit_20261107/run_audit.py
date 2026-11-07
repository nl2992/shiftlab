from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "sota_sprint"))
import fam_p  # noqa: E402


N_STREAMS = 5_000
N_EVENTS = 200
N_STARTS = 20
STRIDE = 10
ALPHA = 0.05
SEED_BASE = 2026110707


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return center - half, center + half


def sample_null(rng: np.random.Generator, kind: str) -> np.ndarray:
    z = np.zeros(N_EVENTS, dtype=np.int8)
    if kind == "iid":
        z[:] = rng.binomial(1, 0.5, size=N_EVENTS)
    else:
        z[0] = rng.binomial(1, 0.5)
        for t in range(1, N_EVENTS):
            p = 0.8 * z[t - 1] + 0.1
            z[t] = rng.binomial(1, p)
    return z


def evaluate(z: np.ndarray, *, carry_dormant: bool) -> tuple[float, bool]:
    ev = fam_p.UniformStartSUI(
        n_starts=N_STARTS,
        stride=STRIDE,
        rho_prior=fam_p.fam_a._B["rho_prior"],
        n_rho=40,
        n_p=20,
    )
    prev = None
    max_value = 1.0
    for hit in z:
        value = ev.update(int(hit), 1, prev)
        if carry_dormant:
            dormant = (N_STARTS - len(ev.starts)) / N_STARTS
            value += dormant
        max_value = max(max_value, value)
        prev = int(hit)
    return max_value, max_value >= 1.0 / ALPHA


def main() -> None:
    rows: list[dict[str, float | int | str]] = []
    for null_i, kind in enumerate(("iid", "markov_rho_08")):
        rng = np.random.default_rng(SEED_BASE + null_i)
        mx_original: list[float] = []
        mx_dormant: list[float] = []
        crossed_original = crossed_dormant = 0
        for _ in range(N_STREAMS):
            z = sample_null(rng, kind)
            m0, c0 = evaluate(z, carry_dormant=False)
            m1, c1 = evaluate(z, carry_dormant=True)
            mx_original.append(m0)
            mx_dormant.append(m1)
            crossed_original += int(c0)
            crossed_dormant += int(c1)
        lo0, hi0 = wilson(crossed_original, N_STREAMS)
        lo1, hi1 = wilson(crossed_dormant, N_STREAMS)
        print(
            f"{kind}: original={crossed_original}/{N_STREAMS} "
            f"[{lo0:.5f},{hi0:.5f}], dormant={crossed_dormant}/{N_STREAMS} "
            f"[{lo1:.5f},{hi1:.5f}], maxE_mean={np.mean(mx_original):.4f}/"
            f"{np.mean(mx_dormant):.4f}"
        )


if __name__ == "__main__":
    main()
