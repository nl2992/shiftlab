"""Evaluate Amendment 3 (RMM transfer, HR/HR2) and Amendment 4 (deploy-gate transfer, HD) as registered.

    uv run python scripts/sota_sprint/analyze_transfer.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_real import contrast as ep_contrast
from analyze_validation import BOUND, CERT, IID_ALT, diff, holm, wilson

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/sota_sprint"
DOC = ROOT / "docs/sota_sprint/validation"
HOSTS = ["gated_deployment", "discern_style", "SMCS+retain-incumbent", "model_picker_adapter",
         "cams_adapter"]
FAM = ["V_late_600", "W_late_1000", "V_better_a", "V_better_b", "V_better_c", "V_near"]
CERT_A3 = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
           "discern_design_floor", "xu_acquisition_only", "choe_ramdas_eb+front"]


def _ci(x):
    se = x.std(ddof=1) / np.sqrt(len(x))
    return {"mean": round(float(x.mean()), 2), "lo": round(float(x.mean() - 1.96 * se), 2),
            "hi": round(float(x.mean() + 1.96 * se), 2), "n": len(x)}


def null_table(df):
    t = {}
    for (r, p), g in df.groupby(["regime", "policy"]):
        k, n = int(g.ever_promote.sum()), len(g)
        t.setdefault(p, {})[r] = {"rate": k / n, "wilson_hi": round(wilson(k, n)[1], 4)}
    return t


def _overlay_replayed_policies(original: Path, replayed: Path) -> pd.DataFrame:
    """Replace only replayed policy arms, retaining same-seed unaffected arms from source."""
    old = pd.read_json(original, lines=True)
    new = pd.read_json(replayed, lines=True)
    replaced = set(new.policy.astype(str))
    merged = pd.concat([old[~old.policy.astype(str).isin(replaced)], new], ignore_index=True)
    keys = [c for c in ("kind", "regime", "ep", "seed", "policy") if c in merged.columns]
    if keys and merged.duplicated(keys).any():
        raise ValueError(f"replayed policy overlay has duplicate keys: {replayed}")
    return merged


def rmm():
    syn = pd.read_json(OUT / "rmm_transfer/synth/records.jsonl", lines=True)
    nul = null_table(pd.read_json(OUT / "rmm_transfer/null1000/records.jsonl", lines=True))
    P = syn[syn.regime.isin(FAM)].pivot_table(index="seed", columns=["regime", "policy"], values="net")
    fam = {p: P.xs(p, axis=1, level=1).mean(axis=1) for p in syn.policy.unique()}  # per-seed family mean
    res = {"HR": {}, "attribution": {}, "nulls": nul}
    n_ok = 0
    for h in HOSTS:
        d = _ci((fam[f"rmm:{h}+RMM"] - fam[h]).to_numpy())
        safe = all(nul[f"rmm:{h}+RMM"][r]["wilson_hi"] <= BOUND for r in ("V_null", "V_worse"))
        res["HR"][h] = {"family_delta": d, "iid_null_safe": safe,
                        "dep_null_r8": nul[f"rmm:{h}+RMM"]["V_null_dep_r8"]["rate"],
                        "dep_null_r95": nul[f"rmm:{h}+RMM"]["W_null_dep_r95"]["rate"],
                        "per_regime": {r: diff(syn[syn.regime == r].pivot_table(
                            index="seed", columns="policy", values="net"), f"rmm:{h}+RMM", h)
                            for r in FAM + ["V_reversal_1000", "W_reversal_700", "V_recurrent"]}}
        n_ok += int(d["hi"] < 0 and safe)
    res["HR_pass"] = n_ok >= 4
    res["HR_n_hosts_ok"] = n_ok
    best = min((f"rmm:{h}+RMM" for h in HOSTS), key=lambda p: fam[p].mean())
    res["HR2"] = {"best_rmm": best, "family_vs": {}}
    for c in ["gated_adaptive_range+front", "gated_deployment+QCE+front", "xu_acquisition_only",
              "discern_design_floor", "P7s_settled", "A5b", "rmm:LRMD"]:
        if c in fam:
            res["HR2"]["family_vs"][c] = _ci((fam[best] - fam[c]).to_numpy())
    rows = []
    for r in ("V_late_600", "W_late_1000"):
        Q = syn[syn.regime == r].pivot_table(index="seed", columns="policy", values="net")
        bc = Q[[c for c in CERT_A3 if c in Q]].mean().idxmin()
        rows.append((r, diff(Q, best, bc)))
    adj = holm(np.array([d["p_one_sided_less"] for _, d in rows]))
    res["HR2"]["late_test"] = {r: {**d, "holm_p": round(float(a), 5)} for (r, d), a in zip(rows, adj)}
    for a, b in [("rmm:gated_deployment+RMM", "rmm:gated_deployment+RMM_single"),
                 ("rmm:discern_style+RMM", "rmm:discern_style+RMM_single"),
                 ("rmm:SMCS+retain-incumbent+RMM", "rmm:SMCS+retain-incumbent+RMM_single"),
                 ("rmm:gated_deployment+RMM", "rmm:gated_deployment+RMM_noacq"),
                 ("rmm:discern_style+RMM", "rmm:discern_style+RMM_noacq")]:
        res["attribution"][f"{a} - {b}"] = _ci((fam[a] - fam[b]).to_numpy())
    return res


def gate():
    syn = pd.read_json(OUT / "gate_transfer/synth/records.jsonl", lines=True)
    nul = null_table(pd.read_json(OUT / "gate_transfer/null1000/records.jsonl", lines=True))
    real = pd.read_json(OUT / "gate_transfer/real_fresh/records.jsonl", lines=True)
    pairs = {"D1": "model_picker_adapter", "D2": "cams_adapter", "D6-D1params:ms": "model_selector_causal"}
    res = {"HD": {}, "nulls": nul}
    Pall = syn.pivot_table(index=["regime", "seed"], columns="policy", values="net")
    n_ok = 0
    for g, h in pairs.items():
        vs_host = _ci((Pall[g] - Pall[h]).dropna().to_numpy())
        rows = []
        for r in IID_ALT:
            Q = syn[syn.regime == r].pivot_table(index="seed", columns="policy", values="net")
            bc = Q[[c for c in CERT if c in Q]].mean().idxmin()
            rows.append((r, diff(Q, g, bc)))
        adj = holm(np.array([d["p_one_sided_less"] for _, d in rows]))
        nsig = int((adj < 0.05).sum())
        safe = all(nul[g][r]["wilson_hi"] <= BOUND for r in ("V_null", "V_worse", "V_null_dep_r5"))
        realc = {}
        for ds, gg in real.groupby("regime"):
            E = gg.groupby(["ep", "policy"]).net.mean().unstack()
            bc = E[[c for c in CERT if c in E]].mean().idxmin()
            realc[ds] = {"best_certified": ep_contrast(E, g, bc), "host": ep_contrast(E, g, h)}
        res["HD"][g] = {"host": h, "vs_host_all_regimes": vs_host,
                        "vs_best_certified_iid": {r: {**d, "holm_p": round(float(a), 5)}
                                                  for (r, d), a in zip(rows, adj)},
                        "n_sig": nsig, "iid_null_safe": safe,
                        "null_rates": {r: nul[g][r]["rate"] for r in nul[g]},
                        "real_fresh": realc, "pass": bool(safe and nsig >= 3)}
        n_ok += int(safe and nsig >= 3)
    res["HD_pass"] = n_ok == 3
    return res


def main():
    out = {"amendment3_rmm": rmm(), "amendment4_gate": gate()}
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "transfer_results.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    a3, a4 = out["amendment3_rmm"], out["amendment4_gate"]
    L = ["# Transfer tests (Amendments 3 and 4)", "",
         f"## HR, RMM transfer across 5 hosts: **{'PASS' if a3['HR_pass'] else 'FAIL'}** ({a3['HR_n_hosts_ok']}/5 hosts with CI<0 and iid-null safety)", "",
         "| host | family Delta J (host+RMM - host) | iid nulls safe | rho .8 null | rho .95 null | reversal_1000 | reversal_700 |", "|---|---|---|---|---|---|---|"]
    for h, v in a3["HR"].items():
        d = v["family_delta"]
        L.append(f"| {h} | {d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}] | {v['iid_null_safe']} | {v['dep_null_r8']:.3f} | "
                 f"{v['dep_null_r95']:.3f} | {v['per_regime']['V_reversal_1000']['mean']:+.1f} | {v['per_regime']['W_reversal_700']['mean']:+.1f} |")
    L += ["", f"HR2, best host+RMM = {a3['HR2']['best_rmm']}; family Delta vs: " + "; ".join(
        f"{k} {v['mean']:+.1f} [{v['lo']:+.1f},{v['hi']:+.1f}]" for k, v in a3["HR2"]["family_vs"].items()),
          "", "Late-regime test vs best certified published (Holm): " + "; ".join(
        f"{r} {v['mean']:+.1f} [{v['lo']:+.1f},{v['hi']:+.1f}] vs {v['vs']} (holm p={v['holm_p']:.3g})"
        for r, v in a3["HR2"]["late_test"].items()),
          "", "Attribution (family mean): " + "; ".join(f"{k}: {v['mean']:+.1f} [{v['lo']:+.1f},{v['hi']:+.1f}]"
                                                         for k, v in a3["attribution"].items()), "",
          f"## HD, deploy-gate transfer across 3 hosts: **{'PASS' if a4['HD_pass'] else 'FAIL'}**", "",
          "| gated host | vs native host (all regimes) | Holm-sig vs best certified (of 5) | iid nulls safe | null rates | fresh real vs best certified (improved/K) |",
          "|---|---|---|---|---|---|"]
    for g, v in a4["HD"].items():
        d = v["vs_host_all_regimes"]
        rr = "; ".join(f"{ds} {c['best_certified']['mean']:+.1f} ({c['best_certified']['improved']}/{c['best_certified']['K']})"
                       for ds, c in v["real_fresh"].items())
        L.append(f"| {g} ({v['host']}) | {d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}] | {v['n_sig']} | {v['iid_null_safe']} | "
                 + ", ".join(f"{r} {x:.3f}" for r, x in v["null_rates"].items()) + f" | {rr} |")
    (DOC / "transfer_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))





def amend5(*, mopeinterval_corrected: bool = False):
    """Amendment 5, HC: registered certificate-host RMM claim (4 hosts).

    The corrected replay is reported separately so the original registered result remains
    immutable. It reuses the registered seed bases and isolates the MOPE interval correction.
    """
    if mopeinterval_corrected:
        syn_dir = OUT / "amend5/synth_mopeinterval_20261106"
        null_dir = OUT / "amend5/null1000_mopeinterval_20261106"
        report_stem = DOC / "amend5_mopeinterval_20261106_results"
        report_title = "# Amendment 5, HC after MOPE interval correction (same-seed sensitivity)"
    else:
        syn_dir = OUT / "amend5/synth"
        null_dir = OUT / "amend5/null1000"
        report_stem = DOC / "amend5_results"
        report_title = "# Amendment 5, HC (registered certificate-host RMM claim)"
    if mopeinterval_corrected:
        syn = _overlay_replayed_policies(OUT / "amend5/synth/records.jsonl", syn_dir / "records.jsonl")
        null_records = _overlay_replayed_policies(OUT / "amend5/null1000/records.jsonl",
                                                  null_dir / "records.jsonl")
    else:
        syn = pd.read_json(syn_dir / "records.jsonl", lines=True)
        null_records = pd.read_json(null_dir / "records.jsonl", lines=True)
    nul = null_table(null_records)
    hosts = ["gated_deployment", "discern_style", "SMCS+retain-incumbent", "gated_adaptive_range"]
    P = syn[syn.regime.isin(FAM)].pivot_table(index="seed", columns=["regime", "policy"], values="net")
    fam = {p: P.xs(p, axis=1, level=1).mean(axis=1) for p in syn.policy.unique()}
    cert = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
            "discern_design_floor", "xu_acquisition_only", "choe_ramdas_eb", "choe_ramdas_eb+front",
            "gated_deployment+QCE", "gated_deployment+QCE+front", "SMCS+retain-incumbent"]
    tests, res = [], {"hosts": {}}
    for h in hosts:
        c = f"rmm:{h}+RMM"
        a = _ci((fam[c] - fam[h]).to_numpy())
        safe = all(nul[c][r]["wilson_hi"] <= BOUND for r in ("V_null", "V_worse"))
        late = {}
        for r in ("V_late_600", "W_late_1000"):
            Q = syn[syn.regime == r].pivot_table(index="seed", columns="policy", values="net")
            bc = Q[[x for x in cert if x in Q and x != h]].mean().idxmin()
            late[r] = diff(Q, c, bc)
            tests.append((h, r))
        co = {r: diff(syn[syn.regime == r].pivot_table(index="seed", columns="policy", values="net"), c, h)
              for r in ("V_reversal_1000", "W_reversal_700", "V_recurrent")}
        res["hosts"][h] = {"a_family_vs_host": a, "a_ok": a["hi"] < 0, "late": late, "c_iid_safe": safe,
                           "coprimary_vs_host": co,
                           "persistent_null": {r: nul[c][r]["rate"] for r in ("V_null_dep_r8", "W_null_dep_r95")}}
    ps = np.array([res["hosts"][h]["late"][r]["p_one_sided_less"] for h, r in tests])
    adj = holm(ps)
    for (h, r), q in zip(tests, adj):
        res["hosts"][h]["late"][r]["holm_p"] = round(float(q), 6)
    for h in hosts:
        v = res["hosts"][h]
        v["b_ok"] = all(v["late"][r]["holm_p"] < 0.05 for r in v["late"])
        v["ok"] = bool(v["a_ok"] and v["b_ok"] and v["c_iid_safe"])
    res["HC_pass"] = all(res["hosts"][h]["ok"] for h in hosts)
    L = [f"{report_title}: **{'PASS' if res['HC_pass'] else 'FAIL'}**", "",
         "Fresh seeds 2026110611 (100) / nulls 2026110612 (1000).", "",
         "| host | (a) family vs host | (b) late vs best certified (Holm p) | (c) iid safe | reversal_1000 / reversal_700 / recurrent vs host | rho .8 / .95 null |",
         "|---|---|---|---|---|---|"]
    for h, v in res["hosts"].items():
        a = v["a_family_vs_host"]
        lt = "; ".join(f"{r} {d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}] vs {d['vs']} (p={d['holm_p']:.2g})" for r, d in v["late"].items())
        co = " / ".join(f"{d['mean']:+.1f}" for d in v["coprimary_vs_host"].values())
        pn = " / ".join(f"{x:.3f}" for x in v["persistent_null"].values())
        L.append(f"| {h} | {a['mean']:+.1f} [{a['lo']:+.1f},{a['hi']:+.1f}] | {lt} | {v['c_iid_safe']} | {co} | {pn} |")
    if mopeinterval_corrected:
        L.insert(2, "MOPE-affected policy arms are replaced by their corrected same-seed replays; unaffected arms retain their registered records.")
        res["data_provenance"] = {
            "replay": "MOPE interval-correction same-seed sensitivity",
            "replayed_synthetic_policies": sorted(set(pd.read_json(syn_dir / "records.jsonl", lines=True).policy.astype(str))),
            "replayed_null_policies": sorted(set(pd.read_json(null_dir / "records.jsonl", lines=True).policy.astype(str))),
            "unaffected_arms": "retained from registered same-seed outputs",
        }
    report_stem.with_suffix(".json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    report_stem.with_suffix(".md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["amend5"]:
        amend5()
    elif sys.argv[1:] == ["amend5", "--mopeinterval-corrected"]:
        amend5(mopeinterval_corrected=True)
    else:
        main()
