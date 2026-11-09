"""Stage 5 analysis: paired metrics, selection on even episodes, advance criterion.

  python stage5_analysis.py A|B|C   # even-episode selection steps (write selection_*.json)
Metrics: equal-dataset pooled paired mean, 95% percentile CI over per-dataset episode bootstraps
(2000; stage0_analysis.boot), dataset sign counts, dL/T in pp, labels, switches, decomposition,
paired worst-dataset mean, p95/p99/CVaR95 of per-episode dJ (dataset-equal weights).
Selection rule inside every grid: minimum pooled J among configurations with dL/T <= +0.1 pp vs
each reference (fallback: minimum J when none is feasible, flagged).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_analysis as s0a
import stage5_run as r5
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage5"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
DS = list(tr.NINE)
T = 2000
COMP = tr.COMPONENTS
COLS = ["net", "loss", "labels", "switches", *COMP, "regret"]
BASE = "wald_l0.97_g0.2"
CVAR_Q = 0.95


def load(split: str, passes=None) -> pd.DataFrame:
    parts = []
    for p in sorted((OUT / split).iterdir()):
        if p.is_dir() and (passes is None or p.name in passes):
            parts.append(pd.read_json(p / "records.jsonl", lines=True))
    d = pd.concat(parts, ignore_index=True)
    return d.drop_duplicates(["stream", "ep", "seed", "policy"])


def ep_table(d: pd.DataFrame) -> pd.DataFrame:
    return d.groupby(["stream", "ep", "policy"])[COLS].mean().reset_index()


def wide(e, pol):
    return e[e.policy == pol].set_index(["stream", "ep"]).sort_index()


def level(e, pol, col):
    w = wide(e, pol)
    return float(np.mean([w.loc[ds, col].mean() for ds in DS]))


def wq(x, w, a):
    o = np.argsort(x)
    cw = np.cumsum(w[o]) / w.sum()
    return float(x[o][min(np.searchsorted(cw, a), len(x) - 1)])


def cvar_up(x, w, a=CVAR_Q):
    o = np.argsort(-x)
    xs, ws = x[o], w[o] / w.sum()
    cw = np.cumsum(ws)
    tail = 1.0 - a
    k = min(int(np.searchsorted(cw, tail)), len(xs) - 1)
    wk = ws[: k + 1].copy()
    wk[-1] -= max(cw[k] - tail, 0.0)
    return float((wk * xs[: k + 1]).sum() / tail)


def paired(e, a, b) -> dict:
    """a - b paired by (dataset, episode)."""
    wa, wb = wide(e, a), wide(e, b)
    idx = wa.index.intersection(wb.index)
    per, diffs, wts = {}, [], []
    for ds in DS:
        ix = [i for i in idx if i[0] == ds]
        x = (wa.loc[ix, COLS].values - wb.loc[ix, COLS].values).astype(float)
        per[ds] = x
        diffs.append(x[:, 0])
        wts.append(np.full(len(x), 1.0 / (len(DS) * len(x))))
    r = s0a.boot(per)
    m, lo, hi = r["POOLED"]
    c = {k: i for i, k in enumerate(COLS)}
    jb = {ds: float(wb.loc[ds, "net"].mean()) for ds in DS}
    dsm = {ds: float(r[ds][0][0]) for ds in DS}
    jref = level(e, b, "net")
    dall, wall = np.concatenate(diffs), np.concatenate(wts)
    reg_a = np.concatenate([wa.loc[ds, "regret"].values for ds in DS])
    reg_b = np.concatenate([wb.loc[ds, "regret"].values for ds in DS])
    out = {
        "policy": a, "vs": b, "dJ": m[0], "dJ_lo": lo[0], "dJ_hi": hi[0],
        "dJ_pct": 100 * m[0] / jref, "dJ_pct_lo": 100 * lo[0] / jref, "dJ_pct_hi": 100 * hi[0] / jref,
        "n_ds_better": sum(v < 0 for v in dsm.values()), "n_ds_worse": sum(v > 0 for v in dsm.values()),
        "dLT_pp": 100 * m[c["loss"]] / T, "dLT_pp_lo": 100 * lo[c["loss"]] / T,
        "dLT_pp_hi": 100 * hi[c["loss"]] / T,
        "worst_ds": max(dsm, key=dsm.get), "worst_ds_dJ": max(dsm.values()),
        "worst_ds_pct": max(100 * dsm[ds] / jb[ds] for ds in DS),
        "p95_dJ": wq(dall, wall, 0.95), "p99_dJ": wq(dall, wall, 0.99),
        "cvar95_dJ": cvar_up(dall, wall),
        "cvar95_regret": cvar_up(reg_a, wall), "cvar95_regret_ref": cvar_up(reg_b, wall),
        "J": level(e, a, "net"), "J_ref": jref, "loss_pp": 100 * level(e, a, "loss") / T,
        "labels": level(e, a, "labels"), "switches": level(e, a, "switches"),
    }  # fmt: skip
    out["cvar95_regret_ratio"] = out["cvar95_regret"] / out["cvar95_regret_ref"]
    for k in ("labels", "switches", *COMP):
        out[f"d_{k}"] = m[c[k]]
    for k in COMP:
        out[f"lvl_{k}"] = level(e, a, k)
    out["ds_dJ"] = json.dumps(dsm)
    return out


def verdict(r1: dict, r2: dict) -> dict:
    """Advance criterion (doc 15 section 3) against both references; r1/r2 = paired rows."""
    c1 = all(r["dJ"] < 0 and r["dJ_hi"] < 0 for r in (r1, r2))
    c2 = all(r["dLT_pp"] <= 0.1 for r in (r1, r2))
    c3 = all(r["cvar95_regret_ratio"] <= 1.10 for r in (r1, r2))
    c4 = all(r["worst_ds_pct"] <= 1.0 for r in (r1, r2))
    return {"c1_mean_ci": c1, "c2_loss": c2, "c3_cvar": c3, "c4_worst_ds": c4,
            "advance": bool(c1 and c2 and c3 and c4)}  # fmt: skip


def feasible_best(e, names, refs):
    rows = []
    for n in names:
        ok = all(100 * (level(e, n, "loss") - level(e, r, "loss")) / T <= 0.1 for r in refs)
        rows.append((level(e, n, "net"), n, ok))
    feas = [x for x in rows if x[2]]
    pick = min(feas or rows)
    return pick[1], bool(feas), sorted(rows)


def grid_stats(e, names):
    j = np.array([level(e, n, "net") for n in names])
    return {"n": len(names), "J_best": float(j.min()), "J_median": float(np.median(j)),
            "J_worst": float(j.max()), "best_minus_median": float(j.min() - np.median(j))}  # fmt: skip


def nearest(e, names, target, col="labels"):
    return min(names, key=lambda n: abs(level(e, n, col) - target))


def cut_of(name):
    t = name.split("_c")[1].split("_")[0]
    return None if t == "none" else int(t)


def write_all(e, names, refs, path):
    rows = []
    for n in names:
        for i, rf in enumerate(refs):
            if n != rf:
                rows.append(paired(e, n, rf) | {"ref_role": ("eqsdp_cutoff", "wald_cutoff")[i]})
    pd.DataFrame(rows).drop(columns=["ds_dJ"]).to_csv(path, index=False)


def sel_A():
    d = load("even", ["A"])
    e = ep_table(d)
    assert d.groupby("policy").size().nunique() == 1
    wald_names = list(dict.fromkeys([BASE, *r5.WALD_NAMES]))
    eqref, eq_ok, eq_rows = feasible_best(e, r5.EQ_NAMES, [BASE])
    wref, w_ok, w_rows = feasible_best(e, wald_names, [BASE])
    refs = [eqref, wref]
    r2_names = sorted(n for n in set(d.policy) if n.startswith("s5evsi_") and "quantile" not in n)
    assert len(r2_names) == 12
    r2, r2_ok, r2_rows = feasible_best(e, r2_names, refs)
    q_names = sorted(n for n in set(d.policy) if "quantile" in n)
    write_all(e, sorted(set(d.policy)), refs, TABLES / "stage5_even_A_all.csv")
    cut = int(eqref.split("_H")[1]) if "_H" in eqref else None
    spec = r5.specs_A()[r2]
    sel = {
        "eq_ref": eqref, "wald_ref": wref, "eq_cutoff": cut,
        "eq_feasible": eq_ok, "wald_feasible": w_ok,
        "J_even": {n: level(e, n, "net") for n in dict.fromkeys([eqref, wref, BASE, tr.ARM_R])},
        "r2": {**{k: spec[k] for k in ("hz", "lam0", "cutoff", "rule")}, "name": r2, "feasible": r2_ok},
        "f0_eq_grid": {n: j for j, n, _ in eq_rows}, "f0_wald_grid": {n: j for j, n, _ in w_rows},
        "grid_stats": {"f0_eq": grid_stats(e, r5.EQ_NAMES), "f0_wald": grid_stats(e, wald_names),
                       "r2": grid_stats(e, r2_names)},
        "r2_grid_J": {n: j for j, n, _ in r2_rows},
        "quantile_pilot": {n: {"J": level(e, n, "net"), "labels": level(e, n, "labels")} for n in q_names},
    }  # fmt: skip
    (OUT / "selection_A.json").write_text(json.dumps(sel, indent=1))
    print(json.dumps(sel, indent=1))


def sel_B():
    sa = json.loads((OUT / "selection_A.json").read_text())
    refs = [sa["eq_ref"], sa["wald_ref"]]
    e = ep_table(pd.concat([load("even", ["A"]), load("even", ["B"])]).drop_duplicates(
        ["stream", "ep", "seed", "policy"]))  # fmt: skip
    hstar, r2 = sa["eq_cutoff"], sa["r2"]
    r1_names = [r5.r1_name(f, g, hstar) for f in r5.R1_F for g in r5.R1_G]
    r1, r1_ok, r1_rows = feasible_best(e, r1_names, refs)
    cal_names = [r5.cal_name(m, hstar) for m in r5.CAL_M]
    cal = nearest(e, cal_names, level(e, r1, "labels"))
    ent_names = [r5.ent_name(r2["hz"], r2["cutoff"], th) for th in r5.ENT_THETA]
    ent = nearest(e, ent_names, level(e, r2["name"], "labels"))
    cal_r2 = nearest(
        e, [r5.cal_name(m, r2["cutoff"]) for m in r5.CAL_M], level(e, r2["name"], "labels")
    )
    write_all(
        e, [*r1_names, *cal_names, *ent_names, cal_r2], refs, TABLES / "stage5_even_B_all.csv"
    )
    sel = {
        "r1": {"name": r1, "f": float(r1.split("_f")[1].split("_")[0]),
               "G": int(r1.split("_G")[1].split("_")[0]), "cutoff": hstar, "feasible": r1_ok},
        "r1_control_calendar": {"name": cal, "m": int(cal.split("_m")[1].split("_")[0]), "cutoff": hstar,
                                "labels": level(e, cal, "labels"), "r1_labels": level(e, r1, "labels")},
        "r2_control_entropy": {"name": ent, "theta": float(ent.split("_th")[1]),
                               "labels": level(e, ent, "labels"), "r2_labels": level(e, r2["name"], "labels")},
        "r2_extra_calendar": {"name": cal_r2, "m": int(cal_r2.split("_m")[1].split("_")[0]),
                              "cutoff": r2["cutoff"]},
        "grid_stats": {"r1": grid_stats(e, r1_names)},
        "r1_grid_J": {n: j for j, n, _ in r1_rows},
    }  # fmt: skip
    (OUT / "selection_B.json").write_text(json.dumps(sel, indent=1))
    print(json.dumps(sel, indent=1))


def sel_C():
    sa = json.loads((OUT / "selection_A.json").read_text())
    refs = [sa["eq_ref"], sa["wald_ref"]]
    r2 = sa["r2"]
    e = ep_table(pd.concat([load("even", ["A"]), load("even", ["C"])]).drop_duplicates(
        ["stream", "ep", "seed", "policy"]))  # fmt: skip
    kw = (r2["hz"], r2["lam0"], r2["cutoff"], r2["rule"])
    tail = [r5.r2_name(*kw, "tail", t) for t in r5.TAU]
    tonly = [r5.r2_name(*kw, "tail_only", t) for t in r5.TAU]
    r3, r3_ok, r3_rows = feasible_best(e, tail, refs)
    to = nearest(e, tonly, level(e, r3, "labels"))
    write_all(e, [*tail, *tonly], refs, TABLES / "stage5_even_C_all.csv")

    def tau(n):
        return float(n.rsplit("_t", 1)[1])

    sel = {
        "r3": {"name": r3, "tau": tau(r3), "feasible": r3_ok},
        "r3_ablation_tail_only": {"name": to, "tau": tau(to), "labels": level(e, to, "labels"),
                                  "r3_labels": level(e, r3, "labels")},
        "grid_stats": {"r3": grid_stats(e, tail), "tail_only": grid_stats(e, tonly)},
        "r3_grid_J": {n: j for j, n, _ in r3_rows},
    }  # fmt: skip
    (OUT / "selection_C.json").write_text(json.dumps(sel, indent=1))
    print(json.dumps(sel, indent=1))


def sel_D():
    sa = json.loads((OUT / "selection_A.json").read_text())
    refs = [sa["eq_ref"], sa["wald_ref"]]
    r2 = sa["r2"]
    e = ep_table(pd.concat([load("even", ["A"]), load("even", ["D"])]).drop_duplicates(
        ["stream", "ep", "seed", "policy"]))  # fmt: skip
    names = [r5.roll_name(r2, k) for k in r5.ROLL_K]
    roll, ok, rows = feasible_best(e, names, refs)
    write_all(e, [*names, r2["name"]], refs, TABLES / "stage5_even_D_all.csv")
    sel = {
        "roll": {"name": roll, "kmax": int(roll.rsplit("_k", 1)[1]), "feasible": ok},
        "vs_one_step_R2": paired(e, roll, r2["name"]) | {"ds_dJ": None},
        "grid_stats": {"roll": grid_stats(e, names)},
        "roll_grid_J": {n: j for j, n, _ in rows},
    }  # fmt: skip
    (OUT / "selection_D.json").write_text(json.dumps(sel, indent=1, default=float))
    print(json.dumps(sel, indent=1, default=float))


# ---------------------------------------------------------------------------------------------
# final tables (frozen configuration set): even and odd side by side
# ---------------------------------------------------------------------------------------------
FREEZE = ROOT / "docs/paper1_eqsdp/16_RECOVERY_FREEZE.json"
ARMS = ["R1", "R2", "R3", "R2_roll"]
CONTROLS = {
    "R1": ["R1_control_calendar"],
    "R2": ["R2_control_entropy", "R2_extra_calendar"],
    "R3": ["R3_ablation_no_tail", "R3_ablation_tail_only"],
    "R2_roll": ["R2"],
}


def final_tables(split: str, fz: dict):
    if split == "even":
        d = pd.concat([load("even", [p]) for p in "ABCD"]).drop_duplicates(
            ["stream", "ep", "seed", "policy"]
        )
    else:
        d = load("odd", ["run"])
    e = ep_table(d)
    refs = [fz["references"]["eqsdp_cutoff"], fz["references"]["wald_cutoff"]]
    roles = fz["roles"]
    rows, verd, vsc = [], {}, []
    for arm in dict.fromkeys([*ARMS, *(c for cs in CONTROLS.values() for c in cs)]):
        n = roles[arm]
        pr = [paired(e, n, rf) | {"role": arm, "ref_role": rr}
              for rf, rr in zip(refs, ("eqsdp_cutoff", "wald_cutoff"), strict=True)]  # fmt: skip
        rows += pr
        verd[arm] = verdict(*pr) | {"policy": n}
    for rf, rr in zip(refs, ("eqsdp_cutoff", "wald_cutoff"), strict=True):
        rows.append(
            paired(e, rf, refs[1 - refs.index(rf)]) | {"role": "REF_" + rr, "ref_role": "other_ref"}
        )
    for arm, ctl in CONTROLS.items():
        for c in ctl:
            vsc.append(paired(e, roles[arm], roles[c]) | {"arm": arm, "control": c})
    tag = f"stage5_final_{split}"
    pd.DataFrame(rows).drop(columns=["ds_dJ"]).to_csv(TABLES / f"{tag}.csv", index=False)
    pd.DataFrame(vsc).drop(columns=["ds_dJ"]).to_csv(TABLES / f"{tag}_vs_controls.csv", index=False)
    (TABLES / f"{tag}_verdicts.json").write_text(json.dumps(verd, indent=1, default=str))
    return pd.DataFrame(rows), verd, pd.DataFrame(vsc)


def final():
    fz = json.loads(FREEZE.read_text())
    out = {}
    for split in sys.argv[2:] or ["even"]:
        rows, verd, vsc = final_tables(split, fz)
        out[split] = verd
        cols = ["role", "ref_role", "J", "dJ", "dJ_lo", "dJ_hi", "dJ_pct", "n_ds_better", "n_ds_worse",
                "dLT_pp", "labels", "switches", "worst_ds_pct", "cvar95_regret_ratio"]  # fmt: skip
        print(split)
        print(rows[cols].to_string())
        print(vsc[["arm", "control", "dJ", "dJ_lo", "dJ_hi", "labels", "d_labels"]].to_string())
        print(json.dumps(verd, indent=1, default=str))
    return out


def main():
    if sys.argv[1] == "F":
        final()
    else:
        {"A": sel_A, "B": sel_B, "C": sel_C, "D": sel_D}[sys.argv[1]]()


if __name__ == "__main__":
    main()
