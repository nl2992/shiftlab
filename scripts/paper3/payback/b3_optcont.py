"""B3 optional-continuation counterexample world (03B: mu = k/h = .1 on the null boundary, no drift slack, no delay).
P(some look m <= M has LCB on the mean > .1): B3 PrPl-EB (one batch) vs Gaussian-naive.  MC, N paths."""

import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from shiftlab.paper3.payback.variance_adaptive import PrPl

MU0, MS = 0.1, (10, 100, 1000)


def one(args):
    seed, p, alpha, lam_max = args
    rng = np.random.default_rng(seed)
    M = max(MS)
    if p is None:
        z = np.where(rng.random(M) < (1 + MU0) / 2, 1.0, -1.0)
    else:
        d = rng.random(M) < p
        z = np.where(d, np.where(rng.random(M) < (1 + MU0 / p) / 2, 1.0, -1.0), 0.0)
    pr = PrPl(alpha, lam_max)
    first = None
    # Gaussian-naive: z=1.645-style one-sided at alpha, sample sd
    from scipy.stats import norm

    zq, cs, ss, gfirst = norm.ppf(1 - alpha), np.cumsum(z), np.cumsum(z * z), None
    for m in range(1, M + 1):
        pr.update((z[m - 1] + 1) / 2)
        if first is None and 2 * pr.lo() - 1 > MU0:
            first = m
        if m >= 2 and gfirst is None:
            mean = cs[m - 1] / m
            sd = max(np.sqrt(max(ss[m - 1] / m - mean**2, 0) * m / (m - 1)), 1e-9)
            if mean - zq * sd / np.sqrt(m) > MU0:
                gfirst = m
    return first, gfirst


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    out = {}
    with ProcessPoolExecutor(20) as ex:
        for p in (None, 0.3):
            for alpha in (0.05, 0.1):
                for lam_max in (0.5, 0.75):
                    r = list(
                        ex.map(
                            one,
                            [(7301600000 + i, p, alpha, lam_max) for i in range(N)],
                            chunksize=20,
                        )
                    )
                    row = {}
                    for M in MS:
                        row[f"B3_M{M}"] = float(np.mean([a is not None and a <= M for a, _ in r]))
                        row[f"gauss_M{M}"] = float(
                            np.mean([g is not None and g <= M for _, g in r])
                        )
                    out[f"p={p},alpha={alpha},lam_max={lam_max}"] = row
                    print(p, alpha, lam_max, row, flush=True)
    json.dump({"N": N, **out}, open("outputs/paper3/payback/b3/optcont.json", "w"), indent=1)  # noqa: SIM115
