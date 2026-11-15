"""Registered statistics C1-C6 of 04F_F3_CONFIRMATION_REGISTRATION.md. usage: analyze_confirm.py TAG"""

import json
import sys

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT, stress_ids

OUT = ROOT / "outputs" / "paper3" / "riskbudget"
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
EPS = 1e-9


def wilson(k, n, z=1.959964):
    p = k / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    d = 1 + z * z / n
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


def main(tag):
    D = {}
    for f in sorted((OUT / tag).glob("*.json")):
        d = json.loads(f.read_text())
        D[d["regime"]] = d
    rids = list(D)

    def arr(a, key):  # (n_regime, n_seed)
        return np.array([D[g]["fields"][key][D[g]["arms"].index(a)] for g in rids], float)

    def exceed(a, R):
        S = arr(a, "sup_harm")
        n = S.shape[1]
        out = {}
        for g, row in zip(rids, S, strict=True):
            k = int(np.sum(row > R + EPS))
            lo, hi = wilson(k, n)
            out[g] = {"k": k, "n": n, "rate": k / n, "lo": lo, "hi": hi}
        w = max(out, key=lambda g: out[g]["rate"])
        return {
            "pooled": float(np.mean([v["rate"] for v in out.values()])),
            "worst": w,
            "worst_stats": out[w],
            "max_hi": max(v["hi"] for v in out.values()),
            "total_k": sum(v["k"] for v in out.values()),
            "per_regime": out,
        }

    def delta(a, b, sel=None, n_boot=10000):
        idx = [i for i, g in enumerate(rids) if sel is None or g in sel]
        d = (arr(a, "J") - arr(b, "J"))[idx].mean(0)
        base = arr(b, "J")[idx].mean()
        rng = np.random.default_rng(0)
        bs = d[rng.integers(0, len(d), (n_boot, len(d)))].mean(1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        return {
            "delta": float(d.mean()),
            "lo": float(lo),
            "hi": float(hi),
            "base": float(base),
            "rel_pct": float(100 * d.mean() / base),
            "hi_rel_pct": float(100 * hi / base),
        }

    r = {"tag": tag, "n_regimes": len(rids), "n_seeds": len(D[rids[0]]["seeds"])}
    c1 = {f"f3_pi1_R{R}": exceed(f"f3_pi1_R{R}", R) for R in (12, 20, 30)}
    c1["f3v2_R20_blind8"] = exceed("f3v2_R20_blind8", 20)
    r["C1"] = {"arms": c1, "supported": all(v["total_k"] == 0 for v in c1.values())}
    c2 = {f"f3v2d_R{R}": exceed(f"f3v2d_R{R}", R) for R in (20, 30)}
    r["C2"] = {"arms": c2, "supported": all(v["max_hi"] <= 0.05 for v in c2.values())}
    c3 = {
        a: exceed(a, 20) for a in ("wald_cut", "cusum", "gate_wald", "cusum_rb_h8", "stoploss_R20")
    }
    r["C3"] = {"arms": c3, "supported": all(v["worst_stats"]["lo"] > 0.05 for v in c3.values())}
    a = delta("f3_pi1_R20", "wald_cut")
    b = delta("f3_pi1_R20", "never")
    r["C4"] = {
        "vs_wald_cut": a,
        "vs_never": b,
        "secondary_f3v2d_R30_vs_wald_cut": delta("f3v2d_R30", "wald_cut"),
        "supported": a["hi_rel_pct"] < 3.0 and b["hi"] < 0,
    }
    s = delta("f3_pi1_R20", "wald_cut", set(stress_ids()))
    r["C5"] = {
        "stress6": s,
        "original24": delta("f3_pi1_R20", "wald_cut", set(rids) - set(stress_ids())),
        "supported": s["hi"] < 0,
    }
    c6 = {
        n: exceed(n, 12)
        for n in ("f3_pi1_R12_nopending", "f3_pi1_R12_norollback", "f3_pi25_R12_noconf")
    }
    r["C6"] = {"arms": c6, "supported": all(v["worst_stats"]["lo"] > 0.05 for v in c6.values())}
    desc = {}
    for arm in D[rids[0]]["arms"]:
        S = arr(arm, "sup_harm").ravel()
        desc[arm] = {
            "J": float(arr(arm, "J").mean()),
            "labels": float(arr(arm, "n_queries").mean()),
            "sup_q95": float(np.quantile(S, 0.95)),
            "sup_q99": float(np.quantile(S, 0.99)),
            "sup_max": float(S.max()),
            "deployed": float(arr(arm, "frac_time_deployed").mean()),
        }
    r["descriptive"] = desc
    RES.mkdir(parents=True, exist_ok=True)
    (RES / f"{tag}_summary.json").write_text(json.dumps(r, indent=1))
    for c in ("C1", "C2", "C3", "C4", "C5", "C6"):
        print(c, "SUPPORTED" if r[c]["supported"] else "NOT SUPPORTED")
    for k, v in desc.items():
        print(
            f"{k:24s} J {v['J']:.2f} q99 {v['sup_q99']:.0f} max {v['sup_max']:.0f} labels {v['labels']:.1f}"
        )


if __name__ == "__main__":
    main(sys.argv[1])
