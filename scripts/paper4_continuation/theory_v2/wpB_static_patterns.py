"""WP B diagnostics for the open static c > 0 case.

(1) Decision pattern across the released-ones count s at each fixed structural state (t, pending, b, m)
    of the DP-optimal static plan: x = dead (never promotes from here), w = wait alive without query,
    Q = query (no promotion), P = promote.  Reports the run-length-compressed patterns.
(2) The stop-minus-continue difference D (normalised by the A1 mass) is NOT monotone in x once queries
    are endogenous (c > 0): records the witness found in the scratch search.
usage: wpB_static_patterns.py OUT.json SEED SECONDS
"""

from __future__ import annotations

import random
import re
import sys
import time
from collections import Counter, defaultdict
from functools import lru_cache

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpB_static import static_solve  # noqa: E402


def main():
    out, seed, secs = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    rng = random.Random(seed)
    t0 = time.time()
    pats, ex, ncfg = Counter(), {}, 0
    while time.time() - t0 < secs:
        T = rng.randint(3, 9)
        B = rng.randint(2, min(5, T))
        d = rng.randint(1, 3)
        e0 = rng.choice([0.01, 0.1, 0.25, 0.4, 0.49])
        e1 = rng.choice([0.51, 0.6, 0.75, 0.9, 0.99])
        c = rng.choice([1e-3, 0.01, 0.05, 0.2])
        k = rng.choice([0, 0.01, 0.1, 0.5, 1.0])
        p = rng.choice([0.05, 0.3, 0.5, 0.7, 0.95])
        lam = rng.choice([0.01, 0.1, 0.5, 2, 10])
        _, plan, _ = static_solve(T, B, d, e0, e1, c, k, 1 - p, lam, p)

        @lru_cache(None)
        def alive(t, pend, b, m, s, plan=plan, T=T, d=d):
            if t > T:
                return False
            a, q = plan[(t, pend, b, m, s)]
            if a:
                return True
            p2 = pend + ((t + d,) if q else ())
            if p2 and p2[0] <= t + 1:
                return alive(t + 1, p2[1:], b - q, m + 1, s) or alive(t + 1, p2[1:], b - q, m + 1, s + 1)
            return alive(t + 1, p2, b - q, m, s)

        byst = defaultdict(dict)
        for (t, pend, b, m, s), (a, q) in plan.items():
            sym = "P" if a else ("Q" if q else ("w" if alive(t, pend, b, m, s) else "x"))
            byst[(t, pend, b, m)][s] = sym
        for key, dct in byst.items():
            comp = re.sub(r"(.)\1+", r"\1", "".join(dct[s] for s in sorted(dct)))
            pats[comp] += 1
            ex.setdefault(comp, [T, B, d, e0, e1, c, k, p, lam, str(key)])
        ncfg += 1
    order = {"x": 0, "w": 1, "Q": 2, "P": 3}
    reversals = {k: v for k, v in pats.items() if any(order[a] > order[b] for a, b in zip(k, k[1:]))}
    # (2) D non-monotone in x with endogenous queries (c = 0.2)
    _, _, D1 = static_solve(3, 1, 1, 0.49, 0.75, 0.2, 0.0, 0.02, 1.0, 1.0)
    _, _, D2 = static_solve(3, 1, 1, 0.49, 0.75, 0.2, 0.0, 0.1, 1.0, 1.0)
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_static_patterns.py", "seed": seed,
               "seconds": time.time() - t0, "n_configs": ncfg, "n_structural_states": sum(pats.values()),
               "patterns": dict(pats.most_common()), "pattern_examples": ex,
               "patterns_violating_order_x<w<Q<P": reversals,
               "D_nonmonotone_witness": {"cell(T,B,d,e0,e1,c,k)": [3, 1, 1, 0.49, 0.75, 0.2, 0.0],
                                         "D(x=0.02,y=1) at t=1": D1[(1, (), 1, 0, 0)],
                                         "D(x=0.1,y=1) at t=1": D2[(1, (), 1, 0, 0)]}}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k not in ("pattern_examples",)})


if __name__ == "__main__":
    main()
