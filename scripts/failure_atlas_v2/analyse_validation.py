"""Registered validation analysis for Atlas v2 (protocol + development freeze).

Primary family: V_late_* and V_better_* (plus their delay variants). For each candidate X:
  * repair transfer: J(base+RMM) - J(base) per seed, for Gated, DISCERN, SMCS;
  * SOTA: J(X) - J(C) per seed, C = the lowest-mean-cost error-controlled published comparator
    in that regime (selected on the same seeds, which favours the comparator);
  * family aggregate: per-seed mean over the family's regimes, bootstrap over seeds.
Safety: promotion frequency on V_null and V_worse_p40 with Wilson 95% upper bound (<= .10).
Real streams: per-episode means over replay seeds, bootstrap over episodes; reported per stream.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict

import numpy as np

CONTROLLED = ["gated_deployment", "discern_style", "SMCS+retain-incumbent", "xu_acquisition_only",
              "qiu_movement_oco", "gated_frontload_ipw", "discern_frontload_ipw"]
ALL_PUB = CONTROLLED + ["model_picker_adapter", "model_selector_causal", "online_llm_picker",
                        "cams_adapter", "variance_min_ipw", "gong_zhang_paid_obs",
                        "delayed_ftrl_capacity"]
BASES = ["gated_deployment", "discern_style", "SMCS+retain-incumbent"]
PRIMARY = ["V_late_600_p65", "V_late_1000_p72", "V_late_1400_p72", "V_late_1000_d50",
           "V_late_1000_d250", "V_better_p62", "V_better_p70"]
ADVERSE = ["V_transient_500_1200", "V_reversal_1000", "V_recurrent_400"]
NULLS = ["V_null", "V_worse_p40", "V_dep_null_r8"]
LRMD = "LRMD_w50"
rng = np.random.default_rng(20261104)


def boot(x, n=4000):
    x = np.asarray(x, float)
    idx = rng.integers(0, len(x), (n, len(x)))
    m = x[idx].mean(1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def wilson_ub(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
    return float(c)


def main(path, out):
    D = defaultdict(lambda: defaultdict(dict))  # source -> policy -> unit -> row
    for line in open(path):
        r = json.loads(line)
        unit = r["seed"] if r["kind"] == "syn" else (r["episode"], r["seed"])
        D[r["source"]][r["policy"]][unit] = r
    res = {"regimes": {}, "families": {}, "safety": {}, "real": {}}

    def vec(src, pol, key="net"):
        units = sorted(D[src][pol], key=str)
        return np.array([D[src][pol][u][key] for u in units], float)

    for src in D:
        if D[src][LRMD] and next(iter(D[src][LRMD].values()))["kind"] != "syn":
            continue
        means = {p: vec(src, p).mean() for p in D[src]}
        best_c = min(CONTROLLED, key=lambda p: means[p])
        best_a = min(ALL_PUB, key=lambda p: means[p])
        e = {"best_controlled": best_c, "best_any": best_a, "means": means,
             "promote": {p: float(vec(src, p, "ever_promote").mean()) for p in D[src]}}
        for cand in [LRMD] + [b + "+RMM" for b in BASES]:
            e[f"{cand}-best_controlled"] = boot(vec(src, cand) - vec(src, best_c))
            e[f"{cand}-best_any"] = boot(vec(src, cand) - vec(src, best_a))
        for b in BASES:
            e[f"{b}+RMM-{b}"] = boot(vec(src, b + "+RMM") - vec(src, b))
        for abl in ["LRMD_single", "LRMD_w50_k1"]:
            e[f"{LRMD}-{abl}"] = boot(vec(src, LRMD) - vec(src, abl))
        for abl in ["gated_deployment+RMM_single", "gated_deployment+RMM_noacq"]:
            e[f"gated_deployment+RMM-{abl}"] = boot(vec(src, "gated_deployment+RMM") - vec(src, abl))
        res["regimes"][src] = e

    for fam, regs in [("primary", PRIMARY), ("adverse", ADVERSE), ("null", NULLS)]:
        regs = [r for r in regs if r in res["regimes"]]
        f = {}
        # per-seed family mean, comparator fixed per regime as above
        def fam_vec(pol_fn):
            return np.mean([vec(r, pol_fn(r)) for r in regs], axis=0)
        f[f"{LRMD}-best_controlled"] = boot(fam_vec(lambda r: LRMD)
                                            - fam_vec(lambda r: res["regimes"][r]["best_controlled"]))
        f[f"{LRMD}-best_any"] = boot(fam_vec(lambda r: LRMD)
                                     - fam_vec(lambda r: res["regimes"][r]["best_any"]))
        for p in ["model_picker_adapter", "model_selector_causal", "gated_frontload_ipw"]:
            f[f"{LRMD}-{p}"] = boot(fam_vec(lambda r: LRMD) - fam_vec(lambda r, p=p: p))
        for b in BASES:
            f[f"{b}+RMM-{b}"] = boot(fam_vec(lambda r, b=b: b + "+RMM") - fam_vec(lambda r, b=b: b))
            f[f"{b}+RMM-best_controlled"] = boot(
                fam_vec(lambda r, b=b: b + "+RMM")
                - fam_vec(lambda r: res["regimes"][r]["best_controlled"]))
        for abl in ["LRMD_single", "LRMD_w50_k1"]:
            f[f"{LRMD}-{abl}"] = boot(fam_vec(lambda r: LRMD) - fam_vec(lambda r, a=abl: a))
        res["families"][fam] = f

    for src in NULLS:
        if src not in D:
            continue
        s = {}
        for p in D[src]:
            v = vec(src, p, "ever_promote")
            k, n = int(v.sum()), len(v)
            s[p] = {"k": k, "n": n, "rate": k / n, "wilson_ub": wilson_ub(k, n)}
        res["safety"][src] = s

    for src in D:
        rows = next(iter(D[src].values()))
        if next(iter(rows.values()))["kind"] != "real":
            continue
        eps = sorted({u[0] for u in rows})

        def ep_mean(p):
            return np.array([np.mean([D[src][p][u]["net"] for u in D[src][p] if u[0] == ep])
                             for ep in eps])
        means = {p: float(ep_mean(p).mean()) for p in D[src]}
        best_c = min(CONTROLLED, key=lambda p: means[p])
        best_a = min(ALL_PUB, key=lambda p: means[p])
        e = {"K": len(eps), "means": means, "best_controlled": best_c, "best_any": best_a}
        if len(eps) >= 2:
            e[f"{LRMD}-best_controlled"] = boot(ep_mean(LRMD) - ep_mean(best_c))
            e[f"{LRMD}-best_any"] = boot(ep_mean(LRMD) - ep_mean(best_a))
            for b in BASES:
                e[f"{b}+RMM-{b}"] = boot(ep_mean(b + "+RMM") - ep_mean(b))
        else:
            e[f"{LRMD}-best_controlled"] = (means[LRMD] - means[best_c], None, None)
            e[f"{LRMD}-best_any"] = (means[LRMD] - means[best_a], None, None)
            for b in BASES:
                e[f"{b}+RMM-{b}"] = (means[b + "+RMM"] - means[b], None, None)
        e["promote"] = {p: float(np.mean([D[src][p][u]["ever_promote"] for u in D[src][p]]))
                        for p in D[src]}
        res["real"][src] = e

    json.dump(res, open(out, "w"), indent=2, default=float)

    def fmt(t):
        return f"{t[0]:+7.2f} [{t[1]:+7.2f},{t[2]:+7.2f}]" if t[1] is not None else f"{t[0]:+7.2f} (K=1)"
    print("== families")
    for fam, f in res["families"].items():
        for k, v in f.items():
            print(f"{fam:8s} {k:48s} {fmt(v)}")
    print("== regimes")
    for src, e in res["regimes"].items():
        print(f"{src:22s} best_ctrl={e['best_controlled']:22s} best_any={e['best_any']:22s} "
              f"LRMD-ctrl {fmt(e[f'{LRMD}-best_controlled'])} LRMD-any {fmt(e[f'{LRMD}-best_any'])} "
              + " ".join(f"{b[:5]}RMM {fmt(e[f'{b}+RMM-{b}'])}" for b in BASES))
    print("== safety (promotion, Wilson UB)")
    for src, s in res["safety"].items():
        print(src, " ".join(f"{p[:14]}={v['rate']:.2f}/{v['wilson_ub']:.2f}" for p, v in s.items()
                            if p in [LRMD, "gated_deployment+RMM", "discern_style+RMM",
                                     "SMCS+retain-incumbent+RMM", "gated_deployment",
                                     "model_picker_adapter", "gated_frontload_ipw"]))
    print("== real")
    for src, e in res["real"].items():
        print(f"{src:14s} K={e['K']:3d} best_ctrl={e['best_controlled']:22s} best_any={e['best_any']:22s} "
              f"LRMD-ctrl {fmt(e[f'{LRMD}-best_controlled'])} LRMD-any {fmt(e[f'{LRMD}-best_any'])} "
              + " ".join(f"{b[:5]}RMM {fmt(e[f'{b}+RMM-{b}'])}" for b in BASES)
              + f" LRMDprom={e['promote'][LRMD]:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
