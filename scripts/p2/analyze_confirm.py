"""P2-NAD confirmation analysis (docs/p2/07_CONFIRMATION.md, H1-H7 + frontier tables).

Written and committed before the confirmation records exist. Usage:
    PYTHONIOENCODING=utf-8 analyze_confirm.py outputs/p2/confirm > docs/p2/results/confirm.md
"""

import collections
import json
import sys
from pathlib import Path

import numpy as np

A, B = "NAD2S-g10-f6", "PB80-g10"
NULLS = ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95", "O_null_semimarkov", "O_null_order2",
         "WP2_o2_null", "WP2_sm_null", "WP2_hs_null"]  # fmt: skip
ALTS = ["F0_better", "F5_dep_better_r8", "S_dep_better_r95", "WP2_o2_better", "WP2_sm_better",
        "WP2_hs_better"]  # fmt: skip
NB = 4000
RNG = np.random.default_rng(20261109)
TIER_A = 0.05 + 2 * np.sqrt(0.05 * 0.95 / 500)


def load(path):
    rows = []
    p = Path(path, "records.jsonl")
    if p.exists():
        rows = [json.loads(x) for x in p.read_text().splitlines()]
    return rows


def by(rows, field):
    D = collections.defaultdict(dict)
    for r in rows:
        D[r["policy"]][(r["regime"], r["ep"], r["seed"])] = r[field]
    return D


def strat_diff(D, a, c, strata, cluster):
    """Stratum-equal mean of paired differences, bootstrap over clusters within strata."""
    per = []
    for s in strata:
        groups = collections.defaultdict(list)
        for k, v in D[a].items():
            if k[0] == s and k in D[c]:
                groups[k[1] if cluster == "ep" else k[2]].append(v - D[c][k])
        if groups:
            per.append(np.array([np.mean(g) for g in groups.values()]))
    est = np.mean([x.mean() for x in per])
    bs = np.mean([x[RNG.integers(0, len(x), (NB, len(x)))].mean(1) for x in per], 0)
    base = np.mean([np.mean([v for k, v in D[c].items() if k[0] == s]) for s in strata])
    return est, np.percentile(bs, [0.5, 2.5, 97.5, 99.5]), base, per


def mean_ub(x, q=97.5):
    x = np.asarray(x, float)
    bs = x[RNG.integers(0, len(x), (NB, len(x)))].mean(1)
    return x.mean(), np.percentile(bs, q)


def main(d):
    out = []
    salt, c4, snull, twin = (load(Path(d, n)) for n in ("salt", "c4", "snull", "twin"))
    J_s, J_c = by(salt, "net"), by(c4, "net")
    c4src = sorted({r["regime"] for r in c4})
    pols = sorted({r["policy"] for r in salt})

    def test(label, D, a, c, strata, cl):
        est, ci, base, _ = strat_diff(D, a, c, strata, cl)
        ok = ci[3] < 0
        out.append(f"| {label} | {a} − {c} | {est:+.2f} | [{ci[0]:+.2f}, {ci[3]:+.2f}] | {100 * est / base:+.1f}% | {'PASS' if ok else 'FAIL'} |")  # fmt: skip
        return ok

    out += ["## Registered hypotheses", "", "| ID | Contrast | Δ | 99% CI | % | Verdict |", "|---|---|---|---|---|---|"]  # fmt: skip
    if salt:
        test("H1 (S-alt)", J_s, A, "A5b", ALTS, "seed")
        h3s = test("H3a (S-alt)", J_s, A, "D5", ALTS, "seed")
        test("H7 (S-alt)", J_s, B, "A5b", ALTS, "seed")
    if c4:
        test("H2 (C4)", J_c, A, "A5b", c4src, "ep")
        h3c = test("H3b (C4)", J_c, A, "D5", c4src, "ep")
        if salt:
            out.append(f"| H3 | both | | | | {'PASS' if (h3s and h3c) else 'FAIL'} |")
    if snull:
        P, H = by(snull, "ever_promote"), by(snull, "db")
        out += ["", "| ID | Policy | Null | Promotion | Tier A bound | Verdict |", "|---|---|---|---|---|---|"]  # fmt: skip
        for n in ("F0_null", "F5_dep_null_r8"):
            v = np.mean([x for k, x in P[A].items() if k[0] == n])
            out.append(f"| H4 | {A} | {n} | {v:.4f} | {TIER_A:.4f} | {'PASS' if v <= TIER_A else 'FAIL'} |")  # fmt: skip
        out += ["", "| ID | Policy | worst null | max 95% UB of decision harm | tolerance | Verdict |", "|---|---|---|---|---|---|"]  # fmt: skip
        for hid, p, tol in (("H5", A, 5.0), ("H6", B, 1.0)):
            ubs = {n: mean_ub([-x for k, x in H[p].items() if k[0] == n])[1] for n in NULLS}
            w = max(ubs, key=ubs.get)
            out.append(f"| {hid} | {p} | {w} | {ubs[w]:.2f} | {tol} | {'PASS' if ubs[w] <= tol else 'FAIL'} |")  # fmt: skip

    # frontier tables
    if salt:
        out += [
            "",
            "## Frontier: synthetic alternatives (A minus c, 95% CI) and null behaviour",
            "",
        ]
        hdr = "| Policy | J_alt | A − c [95% CI] | " + " | ".join(n.replace("_null", "") for n in NULLS) + " | max harm |"  # fmt: skip
        out += [hdr, "|" + "---|" * (4 + len(NULLS))]
        P = by(snull, "ever_promote") if snull else {}
        H = by(snull, "db") if snull else {}
        rows = []
        for c in pols:
            j = np.mean([np.mean([v for k, v in J_s[c].items() if k[0] == g]) for g in ALTS])
            if c != A:
                est, ci, _, _ = strat_diff(J_s, A, c, ALTS, "seed")
                dtxt = f"{est:+.1f} [{ci[1]:+.1f}, {ci[2]:+.1f}]"
            else:
                dtxt = "—"
            pr = [
                np.mean([x for k, x in P.get(c, {}).items() if k[0] == n] or [np.nan])
                for n in NULLS
            ]
            hm = max([np.mean([-x for k, x in H.get(c, {}).items() if k[0] == n] or [np.nan]) for n in NULLS])  # fmt: skip
            rows.append((j, f"| {c} | {j:.1f} | {dtxt} | " + " | ".join(f"{v:.3f}" for v in pr) + f" | {hm:.2f} |"))  # fmt: skip
        out += [r for _, r in sorted(rows)]
    if c4:
        out += ["", "## C4 real streams (A minus c, source-equal, 95% CI; wins = sources with negative mean)", ""]  # fmt: skip
        out += ["| Comparator | J (c) | A − c [95% CI] | % | wins |", "|---|---|---|---|---|"]
        rows = []
        for c in sorted({r["policy"] for r in c4}):
            if c == A:
                continue
            est, ci, base, per = strat_diff(J_c, A, c, c4src, "ep")
            wins = sum(x.mean() < 0 for x in per)
            rows.append((est, f"| {c} | {base:.1f} | {est:+.2f} [{ci[1]:+.2f}, {ci[2]:+.2f}] | {100 * est / base:+.1f}% | {wins}/{len(per)} |"))  # fmt: skip
        out += [r for _, r in sorted(rows)]
    if twin:
        P, H = by(twin, "ever_promote"), by(twin, "db")
        ds = sorted({r["regime"] for r in twin})
        out += ["", "## Real twins (exact marginal nulls): promotion rate / mean decision harm", ""]
        out += ["| Policy | " + " | ".join(ds) + " |", "|" + "---|" * (1 + len(ds))]
        for c in sorted(P):
            cells = []
            for s in ds:
                pv = [x for k, x in P[c].items() if k[0] == s]
                hv = [-x for k, x in H[c].items() if k[0] == s]
                cells.append(f"{np.mean(pv):.3f} / {np.mean(hv):+.2f}")
            out.append(f"| {c} | " + " | ".join(cells) + " |")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
