"""WP B follow-up: hull-targeted test of the restricted conjectures at alpha <= 1/2.

Z2<=1/2: symmetric stationary persistent (t01 = t10 <= 1/2, e0 = 1 - e1, prior 1/2) and alpha <= 1/2 => Gamma = 0.
S+<=1/2: static alternative, c > 0 allowed, alpha <= 1/2 => Gamma = 0.

For each cell the Lagrangian hull of {(R_IID, C)} over pure plans is computed by parametric DP. Lemma R
(remark 2) and Lemma Zc apply: if every hull vertex adjacent to an alpha <= 1/2 is attained by a z-monotone
Lagrangian-optimal plan, then Gamma = 0 for every alpha <= 1/2. The relevant vertices are those with R <= 1/2
plus the lowest vertex with R > 1/2, which closes the edge crossing 1/2. Each relevant vertex is tested at an
interior lambda of its range under four tie-breaks (cont, promote, minR, maxR; static: cont, promote).
If a relevant vertex fails all of them, the repo's certified gamma_cell (exact rationals) is run. Its alpha
values are the vertex risks <= 1/2, the midpoints of relevant hull edges (capped at 1/2), and 1/2 itself.
Floats locate the hull; a certified Gamma > 0 is exact.
usage: wpB2_halfscan.py OUT.json FAMILY SHARD NSHARDS SECONDS   (FAMILY: sym | static | symbig)
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import product

sys.set_int_max_str_digits(0)
sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
import wpB_falsify as GF  # noqa: E402
import wpB_static_falsify as SF  # noqa: E402
from wpB_lib import Model, z_monotone  # noqa: E402
from wpB_static import z_monotone_static  # noqa: E402

TB = [(T, B) for T in range(4, 9) for B in (4, 5, 6) if B <= T]
TR = [F(1, 50), F(1, 20), F(1, 10), F(1, 4), F(1, 2)]
E1 = [F(51, 100), F(3, 5), F(9, 10), F(99, 100), F(999, 1000)]
CK = [F(0), F(1, 100), F(1, 5)]
KK = [F(0), F(1, 100), F(1, 2)]
PRIORS = [F(1, 10), F(1, 2), F(9, 10)]
E0S = [F(1, 100), F(2, 5)]


def cells(family):
    out = []
    if family == "symbig":  # larger horizons/budgets, aggressive (accurate, persistent) cells only
        for T, B, tr, e1, k in product((9, 10), (6, 7), (F(1, 50), F(1, 20), F(1, 10)), (F(99, 100), F(999, 1000)),
                                       (F(0), F(1, 100))):
            out.append((T, B, 1, tr, tr, 1 - e1, e1, F(1, 2), F(0), k))
        return out
    for (T, B), d in product(TB, (1, 2)):
        if family == "sym":
            for tr, e1, c, k in product(TR, E1, CK, KK):
                out.append((T, B, d, tr, tr, 1 - e1, e1, F(1, 2), c, k))
        else:
            for p, e0, e1, c, k in product(PRIORS, E0S, E1, CK, KK):
                out.append((T, B, d, F(0), F(0), e0, e1, p, c, k))
    return out


def vertex_data(family, cell):
    fl = [int(x) for x in cell[:3]] + [float(x) for x in cell[3:]]
    if family in ("sym", "symbig"):
        m = Model(*fl)
        ranges = GF.hull(m)
        ties = ("cont", "promote", "minR", "maxR")

        def at(lam, tie):
            _, R, C, plan = GF.point(m, lam, tie)
            return R, z_monotone(plan, m)[0]
    else:
        T, B, d, _, _, e0, e1, p, c, k = fl
        sc = (int(T), int(B), int(d), e0, e1, p, c, k)
        ranges = SF.hull(sc)
        ties = ("cont", "promote")

        def at(lam, tie):
            _, R, C, plan = SF.point(sc, lam, tie)
            return R, z_monotone_static(plan, int(T), int(B), int(d))[0]

    verts = []
    for lo, hi in ranges:
        lam = (lo + hi) / 2 if hi < 1e4 else lo + 1.0
        R, _ = at(lam, ties[0])
        verts.append({"R": R, "lam": lam, "range": [lo, hi]})
    rel = [i for i, v in enumerate(verts) if v["R"] <= 0.5 + 1e-12]
    above = [i for i, v in enumerate(verts) if v["R"] > 0.5 + 1e-12]
    if above:
        rel = [max(above, key=lambda i: -verts[i]["R"])] + rel  # lowest vertex above 1/2
    for i in rel:
        verts[i]["monotone"] = any(at(verts[i]["lam"], t)[1] for t in ties)
    # lowest-risk non-monotone vertex anywhere (diagnostic: all vertices)
    lowest_bad = None
    for v in verts:
        if "monotone" not in v:
            v["monotone"] = any(at(v["lam"], t)[1] for t in ties)
        if not v["monotone"] and (lowest_bad is None or v["R"] < lowest_bad):
            lowest_bad = v["R"]
    return verts, rel, lowest_bad


def main():
    out, family, shard, nsh, secs = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
    allc = cells(family)
    mine = [c for i, c in enumerate(allc) if i % nsh == shard]
    t0 = time.time()
    done, flagged, positives, lowest = 0, [], [], []
    for cell in mine:
        if time.time() - t0 > secs:
            break
        verts, rel, lowest_bad = vertex_data(family, cell)
        done += 1
        if lowest_bad is not None:
            lowest.append((lowest_bad, [str(x) for x in cell]))
        bad = [i for i in rel if not verts[i]["monotone"]]
        if not bad:
            continue
        Rs = sorted({F(verts[i]["R"]).limit_denominator(1 << 12) for i in rel})
        alphas = {r for r in Rs if r <= F(1, 2)} | {F(1, 2)}
        for a, b in zip(Rs, Rs[1:]):
            alphas.add(min((a + b) / 2, F(1, 2)))
        rec = {"cell": [str(x) for x in cell], "relevant_vertices": [verts[i] for i in rel], "gamma": {}}
        for a in sorted(alphas):
            if a <= 0:
                continue
            g = gamma_cell(*cell, a)
            rec["gamma"][str(a)] = [g["Gamma_lo_f"], g["Gamma_hi_f"], g["Gamma_positive_certified"]]
            if g["Gamma_positive_certified"]:
                positives.append({"cell": rec["cell"], "alpha": str(a), "Gamma_lo": g["Gamma_lo_f"]})
                print("POSITIVE", rec["cell"], a, g["Gamma_lo_f"], flush=True)
        flagged.append(rec)
        print("FLAG", rec["cell"], rec["gamma"], flush=True)
    lowest.sort()
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB2_halfscan.py", "family": family,
               "shard": shard, "nshards": nsh, "n_cells_in_shard": len(mine), "n_cells_done": done,
               "seconds": time.time() - t0, "n_flagged_relevant": len(flagged),
               "n_certified_positive_alpha_le_half": len(positives), "positives": positives,
               "flagged": flagged, "lowest_nonmonotone_vertex_R": lowest[:20],
               "n_cells_with_any_nonmonotone_vertex": len(lowest)}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k not in ("flagged", "lowest_nonmonotone_vertex_R")},
          lowest[:5])


if __name__ == "__main__":
    main()
