"""Evaluate the locked validation protocol (docs/sota_sprint/validation_protocol.md) exactly as written.

    uv run python scripts/sota_sprint/analyze_validation.py
"""

from __future__ import annotations

import json
import math
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/sota_sprint/validation"
DOC = ROOT / "docs/sota_sprint/validation"
BOUND = 0.0936
CORRECTION_TAG = "_wmaxfix_20261105"
PAIR_KEYS = ["kind", "regime", "ep", "seed", "policy"]
CERT = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
        "discern_design_floor", "SMCS+retain-incumbent", "xu_acquisition_only", "choe_ramdas_eb",
        "choe_ramdas_eb+front", "gated_deployment+QCE", "gated_deployment+QCE+front"]  # QCE: Amendment 2
from bench import CERTIFIED_PUBLISHED
UNC = ["model_picker_adapter", "model_selector_causal", "online_llm_picker", "cams_adapter",
       "variance_min_ipw", "gong_zhang_paid_obs", "qiu_delayed_movement", "ryabchenko_capacity"]
IID_ALT = ["V_better_a", "V_better_b", "V_better_c", "V_near", "W_delay600_better"]
DECLARED_LOSS = ["V_bursty", "V_dep_better_r5", "W_better_dep_r7", "W_better_dep_r9", "V_late_600",
                 "W_late_1000", "V_reversal_1000", "W_reversal_700", "V_recurrent"]
NULLS = ["V_null", "V_worse", "V_null_dep_r5", "V_null_dep_r8", "W_null_dep_r9", "W_null_dep_r95",
         "W_worse_dep_r8"]
STAT6 = ["V_better_a", "V_better_b", "V_better_c", "V_dep_better_r5", "V_near", "V_bursty"]
OOC = ["O_null_semimarkov", "O_null_order2"]
H2_CANDS = ["A5b", "A1b", "D1", "D2", "C2", "C6", "X_A5C", "B5", "B2"]
SAFETY_CANDS = ["A5b", "A1b", "X_A5C", "C2", "C6", "D1", "D2", "B2", "B5", "rmm:gated_deployment+RMM",
                "QSG"]


def _load(names, corrected=False):
    fs = [OUT / n / "records.jsonl" for n in names]
    missing = [str(f) for f in fs if not f.exists()]
    if missing:  # fail closed (ARIS m3 re-audit): every registered run must be present
        raise FileNotFoundError(f"missing registered validation runs: {missing}")
    frames = []
    for f in fs:
        old = pd.read_json(f, lines=True)
        new_path = f.parent.with_name(f.parent.name + CORRECTION_TAG) / "records.jsonl"
        if corrected and new_path.is_file():
            new = pd.read_json(new_path, lines=True)
            if not set(PAIR_KEYS).issubset(old) or not set(PAIR_KEYS).issubset(new):
                raise ValueError(f"missing exact pairing keys for {f.parent} or {new_path.parent}")
            policies = set(new.policy)
            old_rows = old[old.policy.isin(policies)].copy()
            if old_rows.duplicated(PAIR_KEYS).any() or new.duplicated(PAIR_KEYS).any():
                raise ValueError(f"duplicate keys in corrected validation merge: {f.parent}")
            paired = old_rows[PAIR_KEYS].merge(new[PAIR_KEYS], on=PAIR_KEYS, how="outer",
                                                indicator=True, validate="one_to_one")
            if not (paired["_merge"] == "both").all():
                raise ValueError(f"old/corrected validation keys differ for {f.parent}: "
                                 f"{paired[paired['_merge'] != 'both'].head().to_dict('records')}")
            contract = old_rows.merge(new, on=PAIR_KEYS, suffixes=("_old", "_new"),
                                      validate="one_to_one")
            for field in ("alpha", "budget", "delay", "cs", "cq"):
                if f"{field}_old" in contract and f"{field}_new" in contract and not np.allclose(
                        contract[f"{field}_old"].to_numpy(), contract[f"{field}_new"].to_numpy(),
                        equal_nan=True):
                    raise ValueError(f"contract mismatch in {field} for {f.parent}")
            old = old[~old.policy.isin(policies)]
            old = pd.concat([old, new], ignore_index=True)
        frames.append(old)
    return pd.concat(frames, ignore_index=True)


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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--amendment-dir", type=Path,
                    help="Write a separate corrected comparator-class sensitivity analysis here; never overwrite registered outputs.")
    ap.add_argument("--strict-published-dir", type=Path,
                    help="Write a separate analysis ranking only bench.CERTIFIED_PUBLISHED ports; never overwrite registered outputs.")
    ap.add_argument("--adaptive-gate-corrected", action="store_true",
                    help="Replace affected validation policy rows with exact-key same-seed correction replays.")
    args = ap.parse_args(argv)
    global DOC
    if args.amendment_dir and args.strict_published_dir:
        ap.error("choose only one of --amendment-dir or --strict-published-dir")
    if args.amendment_dir or args.strict_published_dir:
        # The registered analysis is preserved byte-for-byte. Xu remains in the operational panel,
        # but is removed from the published-certificate ranking per the paper-to-code audit.
        global CERT
        if args.strict_published_dir:
            CERT = list(CERTIFIED_PUBLISHED)
            DOC = args.strict_published_dir
        else:
            CERT = [p for p in CERT if p != "xu_acquisition_only"]
            DOC = args.amendment_dir
    syn = _load(["synth", "synth_b5", "synth_qce"], corrected=args.adaptive_gate_corrected)
    nul = _load(["null1000", "null1000_b5", "null1000_qce", "ooc1000"],
                corrected=args.adaptive_gate_corrected)
    harm = {}
    for r, g in nul.groupby("regime"):
        P = g.pivot_table(index="seed", columns="policy", values="net")
        harm[r] = (P.sub(P["CONTROL_never_switch"], axis=0)).mean().round(3).to_dict()
    piv = {r: g.pivot_table(index="seed", columns="policy", values="net")
           for r, g in syn.groupby("regime")}
    res = {"null_safety": {}, "regimes": {}, "H1": {}, "H2": {}, "H3": {},
           "analysis_status": (("strict published-certificate pool; only bench.CERTIFIED_PUBLISHED ports ranked; all are common-contract adapters rather than author-native full deployments; same-seed selection remains unadjusted"
                                if args.strict_published_dir else
                                "amended legacy sensitivity; Xu acquisition adapter excluded but Choe-Ramdas and QCE ports remain; not a strict published-certificate ranking; same-seed selection remains unadjusted"
                                if args.amendment_dir else "registered historical analysis")
                               + (" Same-seed corrected replay rows substituted by exact stream/episode/policy keys; not independent confirmation."
                                  if args.adaptive_gate_corrected else ""))}

    # null safety, 1000 seeds
    for (r, p), g in nul.groupby(["regime", "policy"]):
        k, n = int(g.ever_promote.sum()), len(g)
        lo, hi = wilson(k, n)
        res["null_safety"].setdefault(p, {})[r] = {"k": k, "n": n, "rate": k / n,
                                                  "harm_vs_never": harm[r].get(p),
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

    # H0 (Amendment 2): registered alternative set; corrected sensitivity excludes Xu's
    # acquisition adapter from the certified-comparator choice.
    s = res["null_safety"]
    for c in ("A5b", "A1b"):
        safe = all(s[c][r]["rate"] <= BOUND for r in ("V_null_dep_r8", "W_null_dep_r95"))
        rows = {}
        for r in STAT6:
            P = piv[r]
            h0_pool = ("gated_adaptive_range+pace_tuned",) if args.amendment_dir else (
                "xu_acquisition_only", "gated_adaptive_range+pace_tuned")
            base = min(h0_pool, key=lambda b: P[b].mean())
            rows[r] = diff(P, c, base)
        k = sum(v["hi"] < 0 for v in rows.values())
        res.setdefault("H0", {})[c] = {"safety_r8_r95": safe, "rows": rows, "n_ci_below_0": k,
                                       "pass": bool(safe and k >= 4)}
    # H1 (Amendment 2): class-scoped safety (Wilson upper bound), Pareto part 2, NI part 3
    def safe_ub(c):
        return {r: s[c][r]["wilson_hi"] <= BOUND for r in NULLS}
    for c in ("A5b", "A1b", "X_A5C"):
        part1 = safe_ub(c)
        p2 = {}
        for comp in CERT:
            fails = [r for r in NULLS if s[comp][r]["rate"] > BOUND and s[comp][r]["wilson_lo"] > 0.05]
            dom = [r for r in STAT6 if diff(piv[r], c, comp)["hi"] < 0]
            p2[comp] = {"fails_nulls": fails, "dominated_on": dom,
                        "ok": bool(fails) or len(dom) >= 3}
        part3 = {r: res["regimes"][r]["contrasts"][c]["best_certified"] for r in IID_ALT + ["V_bursty"]}
        ni5 = sum(part3[r]["hi"] <= 5.0 for r in IID_ALT)
        res["H1"][c] = {"part1_wilson_ub_safe": part1, "part1_pass": all(part1.values()),
                        "part2": p2, "part2_pass": all(v["ok"] for v in p2.values()),
                        "part3": part3, "part3_n_ni_of5": ni5,
                        "part3_n_ni_of6_incl_bursty": ni5 + int(part3["V_bursty"]["hi"] <= 5.0),
                        "part3_pass": ni5 >= 4,
                        "declared_losses": {r: res["regimes"][r]["contrasts"][c]["best_certified"]
                                            for r in DECLARED_LOSS}}
        h = res["H1"][c]
        h["pass"] = h["part1_pass"] and h["part2_pass"] and h["part3_pass"]
    res["ooc"] = {p: {r: s[p][r] for r in OOC if r in s.get(p, {})} for p in s}
    # H2: Holm over the 5 iid alternatives per candidate, vs best certified published
    for c in H2_CANDS:
        ds = [res["regimes"][r]["contrasts"][c]["best_certified"] for r in IID_ALT]
        adj = holm(np.array([d["p_one_sided_less"] for d in ds]))
        safe = all(s[c][r]["wilson_hi"] <= BOUND for r in NULLS)
        res["H2"][c] = {"safe_all_nulls": safe,
                        "rows": {r: {**d, "holm_p": round(float(a), 5)} for r, d, a in zip(IID_ALT, ds, adj)},
                        "n_sig": int((adj < 0.05).sum()),
                        "pass": bool(safe and (adj < 0.05).sum() >= 4)}
    # H3 attribution
    h3 = {}
    for r in IID_ALT + ["V_bursty", "V_dep_better_r5"]:
        h3[f"A5b-A1b@{r}"] = diff(piv[r], "A5b", "A1b")
    for r in ["V_reversal_1000", "W_reversal_700", "V_recurrent"]:
        h3[f"B2-host@{r}"] = diff(piv[r], "B2", "rmm:gated_deployment+RMM")
    for r in ["V_late_600", "W_late_1000"]:
        h3[f"X_A5C-A5b@{r}"] = diff(piv[r], "X_A5C", "A5b")
    for r in ["V_reversal_1000", "W_reversal_700", "V_recurrent"]:
        h3[f"B5-host@{r}"] = diff(piv[r], "B5", "rmm:gated_deployment+RMM")
    for r in ["V_null", "V_null_dep_r8"]:
        h3[f"D1-model_picker@{r}"] = diff(piv[r], "D1", "model_picker_adapter")
        h3[f"D2-cams@{r}"] = diff(piv[r], "D2", "cams_adapter")
    for r in IID_ALT:
        h3[f"C2-front@{r}"] = diff(piv[r], "C2", "gated_adaptive_range+front")
    res["H3"] = h3
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "validation_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    write_md(res)


def _ci(d):
    return f"{d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}]"


def write_md(res):
    s = res["null_safety"]
    regs = NULLS + OOC
    L = ["# SOTA sprint validation results (locked protocol + Amendments 1-2)", "",
        ("**CORRECTED-REPLAY SENSITIVITY:** affected rows were replaced from exact-key, same-seed adaptive-gate correction replays. "
         "This is not independent confirmation; selection remains on reused seeds. " if "same-seed corrected" in res["analysis_status"] else "") +
        (("**STRICT PUBLISHED-CERTIFICATE POOL:** only the six ports in `bench.CERTIFIED_PUBLISHED` are ranked. "
          "They remain common-contract adapters, not author-native full deployments. "
          "Raw runs and registered results are unchanged. Comparator selection still uses the same evaluation seeds; "
          "these contrasts are descriptive and do not provide selection-adjusted confirmatory inference." if "strict published" in res["analysis_status"] else
         "**LEGACY ADAPTER-POOL SENSITIVITY:** Xu is excluded, but Choe–Ramdas and QCE ports remain; this is not a strict published-certificate ranking. "
          "Raw runs and registered results are unchanged. Comparator selection still uses the same evaluation seeds; "
          "these contrasts are descriptive and do not provide selection-adjusted confirmatory inference." if "amended" in res["analysis_status"] else "Historical registered analysis; comparator pool as originally specified.")), "",
         "Raw: `outputs/sota_sprint/validation/`. Synthetic 100 seeds (base 2026110601); in-class nulls "
         "1000 seeds (base 2026110602); out-of-class nulls 1000 seeds (base 2026110605, descriptive).", "",
         "## Null promotion rate (1000 seeds; bold = point > .0936) and harm vs never-switch", "",
         "| policy | " + " | ".join(regs) + " |", "|---|" + "---|" * len(regs)]
    for p in sorted(s):
        cells = []
        for r in regs:
            v = s[p].get(r)
            if v is None:
                cells.append("")
                continue
            rate = f"**{v['rate']:.3f}**" if v["rate"] > BOUND else f"{v['rate']:.3f}"
            cells.append(f"{rate} (ub {v['wilson_hi']:.3f}; harm {v['harm_vs_never']:+.2f})")
        L.append(f"| {p} | " + " | ".join(cells) + " |")
    h0_label = ("tuned pacing only (Xu excluded from certificate-comparator selection)"
                if ("amended" in res["analysis_status"] or "strict published" in res["analysis_status"])
                else "stronger of Xu / tuned pacing")
    L += ["", f"## H0: Atlas v2 registered stop rule (vs {h0_label})", ""]
    for c, h in res["H0"].items():
        L.append(f"* **{c}: {'PASS' if h['pass'] else 'FAIL'}**; safety rho .8/.95 {h['safety_r8_r95']}; "
                 f"CI<0 on {h['n_ci_below_0']}/6: " + "; ".join(f"{r} {_ci(d)} vs {d['vs']}" for r, d in h["rows"].items()))
    L += ["", "## H1 (Amendment 2): class-scoped reliability on the safety-cost Pareto frontier", ""]
    for c, h in res["H1"].items():
        L += [f"### {c}: **{'PASS' if h['pass'] else 'FAIL'}**",
              f"* part 1 (Wilson ub <= .0936 on all in-class nulls): {h['part1_pass']} {h['part1_wilson_ub_safe']}",
              f"* part 2 (each certified comparator fails a null or is cost-dominated on >= 3/6): {h['part2_pass']}"]
        for comp, v in h["part2"].items():
            L.append(f"  * {comp}: fails {v['fails_nulls']}; dominated on {v['dominated_on']} -> {'ok' if v['ok'] else 'NOT OK'}")
        L.append(f"* part 3 NI (+5): {h['part3_n_ni_of5']}/5 iid ({h['part3_n_ni_of6_incl_bursty']}/6 incl. bursty): "
                 + "; ".join(f"{r} {_ci(d)} vs {d['vs']}" for r, d in h["part3"].items()))
        L.append("* declared losses: " + "; ".join(f"{r} {_ci(d)}" for r, d in h["declared_losses"].items()))
    L += ["", "## H2 (cost superiority vs best certificate-policy comparator; Holm over 5 iid; requires Wilson-ub safety)", "",
          "| candidate | safe | " + " | ".join(IID_ALT) + " | n sig | pass |", "|---|---|" + "---|" * len(IID_ALT) + "---|---|"]
    for c, v in res["H2"].items():
        L.append(f"| {c} | {v['safe_all_nulls']} | " + " | ".join(
            f"{v['rows'][r]['mean']:+.1f} (p={v['rows'][r]['holm_p']:.3g})" for r in IID_ALT)
            + f" | {v['n_sig']} | {v['pass']} |")
    L += ["", "## H3 attribution (paired, 95% CI)", "", "| contrast | mean [CI] |", "|---|---|"]
    L += [f"| {k} | {_ci(d)} |" for k, d in res["H3"].items()]
    keys = ["A5b", "A1b", "X_A5C", "D1", "D2", "C2", "C6", "B2", "B5", "QSG", "xu_acquisition_only",
            "gated_adaptive_range+pace_tuned", "gated_adaptive_range+front", "choe_ramdas_eb+front",
            "gated_deployment+QCE+front", "SMCS+retain-incumbent", "discern_style", "CONTROL_never_switch"]
    L += ["", "## All regimes: mean cost", "",
          "| regime | best cert | best uncert | " + " | ".join(keys) + " |", "|---|---|---|" + "---|" * len(keys)]
    for r, c in res["regimes"].items():
        m = c["mean"]
        L.append(f"| {r} | {c['best_certified']} {m[c['best_certified']]:.1f} | {c['best_uncertified']} "
                 f"{m[c['best_uncertified']]:.1f} | " + " | ".join(f"{m.get(k, float('nan')):.1f}" for k in keys) + " |")
    (DOC / "validation_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[: 40 + len(s)]))


if __name__ == "__main__":
    main()
