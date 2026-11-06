"""The seven ranked leaderboard views of the sprint brief (section 12), development vs validated.

Development views use the family-isolated gate re-screen (`outputs/sota_sprint/gate/<F>`, 20 seeds,
dev base); each family screened its own environments, so cross-family development ranks use only the
environments every family shares (F0_better, F0_null, F1_late_800, F3_reversal_800, F5_dep_null_r8).
Validated views use the 100-seed / 1000-null-seed validation records. A policy counts as "safe" when
its null promotion is within the bound (Wilson upper bound <= .0936 on validated nulls; on dev, at
most 1/20 on every null environment, a screening proxy only).

    uv run python scripts/sota_sprint/leaderboard_views.py
"""

from __future__ import annotations

import json
import math
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "outputs/sota_sprint/gate"
VAL = ROOT / "outputs/sota_sprint/validation"
DOC = ROOT / "docs/sota_sprint"
SHARED = ["F0_better", "F0_null", "F1_late_800", "F3_reversal_800", "F5_dep_null_r8"]
DEV_NULLS = {"F0_null", "F5_dep_null_r8", "F5_dep_null_r95", "F0_worse"}
IDS = [f"{f}{i}" for f in "ABCD" for i in range(1, 7)]
REP = {"B1": "B1_r15", "D6": "D6:mp"}  # representative policy row for multi-setting candidates
HOSTS = {"C6": ("C6", "gated_adaptive_range", "C6@discern", "discern_design_floor"),
         "D6": ("D6:mp", "model_picker_adapter", "D6:cams", "cams_adapter", "D6:ms",
                "model_selector_causal"),
         "FLQ": ("gated_deployment+QCE+front", "gated_deployment")}
CHANGE = {"F1_late_800", "F3_reversal_800", "F4_recurrent", "F2_transient", "S_reversal_400",
          "S_late_1500", "S_transient_short", "F1_late_1200", "V_late_600", "V_reversal_1000",
          "V_recurrent", "W_late_1000", "W_reversal_700"}


def wilson_hi(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    return min(1.0, c + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n))


CORRECTION_TAG = "_wmaxfix_20261105"


def _load(dirs, corrected=False):
    frames = []
    for d in dirs:
        f = d / "records.jsonl"
        if not f.exists():
            continue
        old = pd.read_json(f, lines=True)
        new_path = d.with_name(d.name + CORRECTION_TAG) / "records.jsonl"
        if corrected and new_path.is_file():
            new = pd.read_json(new_path, lines=True)
            keys = ["regime", "ep", "seed", "policy"]
            if not set(keys).issubset(old) or not set(keys).issubset(new):
                raise ValueError(f"missing exact leaderboard correction keys: {d}")
            policies = set(new.policy)
            previous = old[old.policy.isin(policies)]
            if previous.duplicated(keys).any() or new.duplicated(keys).any():
                raise ValueError(f"duplicate leaderboard correction keys: {d}")
            joined = previous[keys].merge(new[keys], on=keys, how="outer", indicator=True,
                                           validate="one_to_one")
            if not (joined["_merge"] == "both").all():
                raise ValueError(f"unmatched leaderboard correction rows: {d}")
            old = pd.concat([old[~old.policy.isin(policies)], new], ignore_index=True)
        frames.append(old)
    return pd.concat(frames, ignore_index=True) if frames else None


def views(df, nulls, safe_fn, label):
    alts = [r for r in df.regime.unique() if r not in nulls]
    out = {}
    cost = df[df.regime.isin(alts)].groupby("policy").net.mean()
    safe = {p: safe_fn(gg) for p, gg in df[df.regime.isin(nulls)].groupby("policy")}
    out["1_lowest_total_cost"] = cost.sort_values().round(2).head(15).to_dict()
    out["2_best_safe_efficacy"] = cost[[p for p in cost.index if safe.get(p)]].sort_values().round(2).head(15).to_dict()
    fb = df[df.regime.isin(["F0_better", "V_better_a"])]
    first = fb[fb.first_deploy >= 0].groupby("policy").first_deploy.median()
    prate = fb.groupby("policy").ever_promote.mean()  # median over promoting runs only means
    out["3_fastest_correct_detection_safe"] = first[[p for p in first.index if safe.get(p)
                                                     and prate[p] >= 0.5]].sort_values().head(15).to_dict()
    ch = df[df.regime.isin(CHANGE)]
    out["4_lowest_dynamic_regret"] = ch.groupby("policy").regret_expected_oracle.mean().sort_values().round(2).head(15).to_dict()
    # 5: labels used per unit of correct-decision value, among safe policies promoting on >= 80% of
    # the clear-advantage streams (matched decision quality)
    pr = fb.groupby("policy").ever_promote.mean()
    lab = fb.groupby("policy").labels.mean()
    q = [p for p in pr.index if pr[p] >= 0.8 and safe.get(p)]
    out["5_best_label_efficiency_matched_quality"] = lab[q].sort_values().round(1).head(15).to_dict()
    # 6: transferable improvement: mean (candidate - native host) over hosts, all regimes (nulls too)
    tr = {}
    piv = df.pivot_table(index=["regime", "ep", "seed"], columns="policy", values="net")
    for k, pairs in HOSTS.items():
        ds = [float((piv[a] - piv[b]).mean()) for a, b in zip(pairs[::2], pairs[1::2])
              if a in piv and b in piv]
        if ds:
            tr[k] = {"mean_over_hosts": round(float(np.mean(ds)), 2), "per_host": [round(d, 2) for d in ds],
                     "n_hosts": len(ds)}
    out["6_largest_transferable_improvement"] = tr
    # 7: overall research candidate: safe first, then cost; only sprint candidates
    cands = [p for p in cost.index if p[:2] in IDS or p.startswith(("A5b", "A1b", "X_", "B1_r"))]
    out["7_best_overall_research_candidate"] = sorted(
        [{"policy": p, "safe": bool(safe.get(p)), "alt_cost": round(float(cost[p]), 2)} for p in cands],
        key=lambda d: (not d["safe"], d["alt_cost"]))[:15]
    out["_basis"] = label
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adaptive-gate-corrected", action="store_true",
                    help="Substitute affected policies using exact-key same-seed correction runs.")
    ap.add_argument("--out-dir", type=Path,
                    help="Separate output directory; defaults to docs/sota_sprint/validation.")
    args = ap.parse_args(argv)
    global DOC
    if args.out_dir:
        DOC = args.out_dir
        DOC.mkdir(parents=True, exist_ok=True)
    res = {}
    dev = _load([GATE / f for f in "ABCD"], corrected=args.adaptive_gate_corrected)
    if dev is not None:
        shared = dev[dev.regime.isin(SHARED)].drop_duplicates(["regime", "ep", "seed", "policy"])
        res["development"] = views(shared, DEV_NULLS,
                                   lambda g: g.groupby("regime").ever_promote.sum().max() <= 1,
                                   "gate re-screen, 20 dev seeds, shared environments " + ",".join(SHARED))
    syn = _load([VAL / n for n in ("synth", "synth_b5", "synth_qce")],
                corrected=args.adaptive_gate_corrected)
    nul = _load([VAL / n for n in ("null1000", "null1000_b5", "null1000_qce")],
                corrected=args.adaptive_gate_corrected)
    if syn is not None and nul is not None:
        nn = set(nul.regime.unique())
        safe_val = {p: all(wilson_hi(int(g2.ever_promote.sum()), len(g2)) <= 0.0936
                           for _, g2 in g.groupby("regime")) for p, g in nul.groupby("policy")}
        syn = syn.drop_duplicates(["regime", "ep", "seed", "policy"])
        res["validated"] = views(syn, nn, lambda g: safe_val.get(g.policy.iloc[0], False),
                                 "validation: 100 fresh seeds; safety = Wilson ub on 1000-seed in-class nulls")
    if args.adaptive_gate_corrected:
        res["adaptive_gate_correction"] = ("exact-key same-seed replacement for affected policy rows; "
                                           "sensitivity, not independent confirmation")
    (DOC / "leaderboard_views.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    L = ["# Leaderboard: ranked views (brief section 12)", ""]
    if args.adaptive_gate_corrected:
        L += ["**CORRECTED-REPLAY SENSITIVITY:** affected rows were replaced by exact-key, same-seed correction records. "
              "This is not independent confirmation.", ""]
    for stage, v in ((k, v) for k, v in res.items() if isinstance(v, dict) and "_basis" in v):
        L += [f"## {stage} ({v['_basis']})", ""]
        for k, d in v.items():
            if k.startswith("_"):
                continue
            L.append(f"**{k}**: " + (", ".join(f"{p} {x}" for p, x in d.items()) if isinstance(d, dict)
                                     else ", ".join(f"{e['policy']} ({'safe' if e['safe'] else 'unsafe'}, {e['alt_cost']})" for e in d)))
            L.append("")
    (DOC / "leaderboard_views.md").write_text("\n".join(L) + "\n")
    print("\n".join(L)[:4000])


if __name__ == "__main__":
    main()
