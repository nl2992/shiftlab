"""Evaluate the locked validation protocol (docs/sota_sprint/validation_protocol.md) exactly as written.

    uv run python scripts/sota_sprint/analyze_validation.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/sota_sprint/validation"
DOC = ROOT / "docs/sota_sprint/validation"
BOUND = 0.0936
CERT = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
        "discern_design_floor", "SMCS+retain-incumbent", "xu_acquisition_only", "choe_ramdas_eb",
        "choe_ramdas_eb+front"]
UNC = ["model_picker_adapter", "model_selector_causal", "online_llm_picker", "cams_adapter",
       "variance_min_ipw", "gong_zhang_paid_obs", "qiu_delayed_movement", "ryabchenko_capacity"]
IID_ALT = ["V_better_a", "V_better_b", "V_better_c", "V_near", "W_delay600_better"]
DECLARED_LOSS = ["V_bursty", "V_dep_better_r5", "W_better_dep_r7", "W_better_dep_r9", "V_late_600",
                 "W_late_1000", "V_reversal_1000", "W_reversal_700", "V_recurrent"]
NULLS = ["V_null", "V_worse", "V_null_dep_r5", "V_null_dep_r8", "W_null_dep_r9", "W_null_dep_r95",
         "W_worse_dep_r8"]
H2_CANDS = ["A5b", "D1", "D2", "C2", "C6", "X_A5C"]
SAFETY_CANDS = ["A5b", "A1b", "X_A5C", "C2", "C6", "D1", "D2", "B2", "rmm:gated_deployment+RMM", "QSG"]


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def diff(piv, a, b):
    d = (piv[a] - piv[b]).dropna().to_numpy()
    se = d.std(ddof=1) / np.sqrt(len(d))
    t = d.mean() / se if se > 0 else 0.0
    return {"vs": b, "mean": round(float(d.mean()), 2), "lo": round(float(d.mean() - 1.96 * se), 2),
            "hi": round(float(d.mean() + 1.96 * se), 2), "n": len(d),
            "p_one_sided_less": float(stats.t.cdf(t, len(d) - 1)),
            "frac_better": round(float((d < 0).mean()), 3)}


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for i, j in enumerate(order):
        run = max(run, min(1.0, (len(ps) - i) * ps[j]))
        adj[j] = run
    return adj


def main():
    syn = pd.read_json(OUT / "synth/records.jsonl", lines=True)
    nul = pd.read_json(OUT / "null1000/records.jsonl", lines=True)
    piv = {r: g.pivot_table(index="seed", columns="policy", values="net")
           for r, g in syn.groupby("regime")}
    res = {"null_safety": {}, "regimes": {}, "H1": {}, "H2": {}, "H3": {}}

    # null safety, 1000 seeds
    for (r, p), g in nul.groupby(["regime", "policy"]):
        k, n = int(g.ever_promote.sum()), len(g)
        lo, hi = wilson(k, n)
        res["null_safety"].setdefault(p, {})[r] = {"k": k, "n": n, "rate": k / n,
                                                  "wilson_lo": round(lo, 4), "wilson_hi": round(hi, 4)}
    # per-regime cost table (synthetic 100 seeds)
    for r, P in piv.items():
        means = P.mean()
        g = syn[syn.regime == r].groupby("policy")
        cell = {"mean": means.round(2).to_dict(),
                "promote": g.ever_promote.mean().round(3).to_dict(),
                "first": g.first_deploy.apply(lambda s: float(np.median(s[s >= 0])) if (s >= 0).any() else -1).to_dict(),
                "labels": g.labels.mean().round(1).to_dict(),
                "switches": g.switches.mean().round(2).to_dict()}
        cert = [c for c in CERT if c in means]
        unc = [c for c in UNC if c in means]
        cell["best_certified"] = means[cert].idxmin()
        cell["best_uncertified"] = means[unc].idxmin()
        cell["contrasts"] = {c: {"best_certified": diff(P, c, cell["best_certified"]),
                                 "best_uncertified": diff(P, c, cell["best_uncertified"])}
                             for c in SAFETY_CANDS + ["A1b"] if c in means}
        res["regimes"][r] = cell

    # H1 for A5b
    s = res["null_safety"]
    part1 = {r: s["A5b"][r]["rate"] <= BOUND for r in NULLS}
    part2 = {c: [r for r in NULLS if s[c][r]["rate"] > BOUND and s[c][r]["wilson_lo"] > 0.05]
             for c in CERT}
    part3 = {r: res["regimes"][r]["contrasts"]["A5b"]["best_certified"] for r in IID_ALT}
    ni = sum(v["hi"] <= 5.0 for v in part3.values())
    res["H1"] = {"part1_safety": part1, "part1_pass": all(part1.values()),
                 "part2_failures": part2, "part2_pass": all(len(v) > 0 for v in part2.values()),
                 "part3_noninferiority": part3, "part3_n_ni": ni, "part3_pass": ni >= 4,
                 "declared_losses": {r: res["regimes"][r]["contrasts"]["A5b"]["best_certified"]
                                     for r in DECLARED_LOSS}}
    res["H1"]["pass"] = res["H1"]["part1_pass"] and res["H1"]["part2_pass"] and res["H1"]["part3_pass"]
    # comparators that pass every null (for a restated H1)
    res["H1"]["certified_passing_all_nulls"] = [c for c in CERT if not part2[c]
                                                and all(s[c][r]["rate"] <= BOUND for r in NULLS)]

    # H2: Holm over the 5 iid alternatives per candidate, vs best certified published
    for c in H2_CANDS:
        ds = [res["regimes"][r]["contrasts"][c]["best_certified"] for r in IID_ALT]
        adj = holm(np.array([d["p_one_sided_less"] for d in ds]))
        safe = all(s[c][r]["rate"] <= BOUND for r in NULLS)
        res["H2"][c] = {"safe_all_nulls": safe,
                        "rows": {r: {**d, "holm_p": round(float(a), 5)} for r, d, a in zip(IID_ALT, ds, adj)},
                        "n_sig": int((adj < 0.05).sum())}
    # H3 attribution
    h3 = {}
    for r in IID_ALT + ["V_bursty", "V_dep_better_r5"]:
        h3[f"A5b-A1b@{r}"] = diff(piv[r], "A5b", "A1b")
    for r in ["V_reversal_1000", "W_reversal_700", "V_recurrent"]:
        h3[f"B2-host@{r}"] = diff(piv[r], "B2", "rmm:gated_deployment+RMM")
    for r in ["V_null", "V_null_dep_r8"]:
        h3[f"D1-model_picker@{r}"] = diff(piv[r], "D1", "model_picker_adapter")
        h3[f"D2-cams@{r}"] = diff(piv[r], "D2", "cams_adapter")
    for r in IID_ALT:
        h3[f"C2-front@{r}"] = diff(piv[r], "C2", "gated_adaptive_range+front")
    res["H3"] = h3
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "validation_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    write_md(res)


def write_md(res):
    s = res["null_safety"]
    L = ["# SOTA sprint validation results (locked protocol)", "",
         "Raw: `outputs/sota_sprint/validation/{synth,null1000}`. Synthetic 100 seeds (base 2026110601); "
         "nulls 1000 seeds (base 2026110602).", "", "## Null safety (promotion rate over 1000 seeds; bound .0936)", "",
         "| policy | " + " | ".join(NULLS) + " |", "|---|" + "---|" * len(NULLS)]
    for p in sorted(s):
        L.append(f"| {p} | " + " | ".join(
            (f"**{s[p][r]['rate']:.3f}**" if s[p][r]["rate"] > BOUND else f"{s[p][r]['rate']:.3f}")
            for r in NULLS) + " |")
    h1 = res["H1"]
    L += ["", f"## H1 (A5b reliability at matched cost): **{'PASS' if h1['pass'] else 'FAIL'}**", "",
          f"* Part 1 safety: {'pass' if h1['part1_pass'] else 'FAIL'}",
          f"* Part 2 every certified comparator fails a null: {'pass' if h1['part2_pass'] else 'FAIL'}; "
          f"failures {json.dumps(h1['part2_failures'])}; passing all nulls: {h1['certified_passing_all_nulls']}",
          f"* Part 3 non-inferiority (+5 margin) on {h1['part3_n_ni']}/5: {'pass' if h1['part3_pass'] else 'FAIL'}", "",
          "| regime | A5b - best certified [95% CI] | comparator |", "|---|---|---|"]
    for r, d in {**h1["part3_noninferiority"], **h1["declared_losses"]}.items():
        L.append(f"| {r}{' (declared loss)' if r in DECLARED_LOSS else ''} | {d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}] | {d['vs']} |")
    L += ["", "## H2 (cost superiority vs best certified published, Holm over 5 iid alternatives)", "",
          "| candidate | safe on all nulls | " + " | ".join(IID_ALT) + " | n sig |", "|---|---|" + "---|" * len(IID_ALT) + "---|"]
    for c, v in res["H2"].items():
        L.append(f"| {c} | {v['safe_all_nulls']} | " + " | ".join(
            f"{v['rows'][r]['mean']:+.1f} (p={v['rows'][r]['holm_p']:.3g})" for r in IID_ALT) + f" | {v['n_sig']} |")
    L += ["", "## H3 attribution (paired, 95% CI)", "", "| contrast | mean [CI] |", "|---|---|"]
    for k, d in res["H3"].items():
        L.append(f"| {k} | {d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}] |")
    L += ["", "## All regimes: mean cost of key policies", ""]
    keys = ["A5b", "A1b", "X_A5C", "D1", "D2", "C2", "C6", "B2", "QSG", "xu_acquisition_only",
            "gated_adaptive_range+front", "choe_ramdas_eb+front", "SMCS+retain-incumbent",
            "discern_design_floor", "CONTROL_never_switch"]
    L += ["| regime | best cert | best uncert | " + " | ".join(keys) + " |", "|---|---|---|" + "---|" * len(keys)]
    for r, c in res["regimes"].items():
        m = c["mean"]
        L.append(f"| {r} | {c['best_certified']} {m[c['best_certified']]:.1f} | {c['best_uncertified']} "
                 f"{m[c['best_uncertified']]:.1f} | " + " | ".join(f"{m.get(k, float('nan')):.1f}" for k in keys) + " |")
    (DOC / "validation_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
