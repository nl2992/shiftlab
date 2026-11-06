"""Real-data analysis per docs/sota_sprint/fresh_real_protocol.md (fresh) and, descriptively, exposed streams.

Unit = episode (policy seeds averaged within an episode). Per dataset: paired Delta J (candidate -
comparator) with a 95% t-interval over episodes, the fraction of episodes improved, and a two-sided sign
test. Episodes are consecutive windows of one stream, so intervals are optimistic.

    uv run python scripts/sota_sprint/analyze_real.py
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
VAL = ROOT / "outputs/sota_sprint/validation"
DOC = ROOT / "docs/sota_sprint/validation"
CERT = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
        "discern_design_floor", "SMCS+retain-incumbent", "xu_acquisition_only", "choe_ramdas_eb",
        "choe_ramdas_eb+front"]
UNC = ["model_picker_adapter", "model_selector_causal", "online_llm_picker", "cams_adapter",
       "variance_min_ipw", "gong_zhang_paid_obs", "qiu_delayed_movement", "ryabchenko_capacity"]
CANDS = {"A5b": None, "X_A5C": None, "D1": "model_picker_adapter", "D2": "cams_adapter",
         "C2": "gated_adaptive_range+front", "C6": "gated_adaptive_range+front",
         "B2": "rmm:gated_deployment+RMM", "B5": "rmm:gated_deployment+RMM"}
CORRECTION_TAG = "_wmaxfix_20261105"
PAIR_KEYS = ["kind", "regime", "ep", "seed", "policy"]


def contrast(E, a, b):
    d = (E[a] - E[b]).dropna().to_numpy()
    se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float("nan")
    k = int((d < 0).sum())
    nz = int((d != 0).sum())
    return {"vs": b, "mean": round(float(d.mean()), 2), "lo": round(float(d.mean() - 1.96 * se), 2),
            "hi": round(float(d.mean() + 1.96 * se), 2), "K": len(d), "improved": k,
            "sign_p": float(stats.binomtest(k, nz, 0.5).pvalue) if nz else 1.0}


def load_run(run: str, corrected: bool = False) -> pd.DataFrame:
    source = VAL / run / "records.jsonl"
    old = pd.read_json(source, lines=True)
    new_path = source.parent.with_name(source.parent.name + CORRECTION_TAG) / "records.jsonl"
    if not corrected or not new_path.is_file():
        return old
    new = pd.read_json(new_path, lines=True)
    if not set(PAIR_KEYS).issubset(old) or not set(PAIR_KEYS).issubset(new):
        raise ValueError(f"missing exact pairing keys for {source.parent} or {new_path.parent}")
    policies = set(new.policy)
    old_rows = old[old.policy.isin(policies)].copy()
    if old_rows.duplicated(PAIR_KEYS).any() or new.duplicated(PAIR_KEYS).any():
        raise ValueError(f"duplicate keys in corrected real-data merge: {source.parent}")
    paired = old_rows[PAIR_KEYS].merge(new[PAIR_KEYS], on=PAIR_KEYS, how="outer", indicator=True,
                                        validate="one_to_one")
    if not (paired["_merge"] == "both").all():
        raise ValueError(f"old/corrected real-data keys differ for {source.parent}: "
                         f"{paired[paired['_merge'] != 'both'].head().to_dict('records')}")
    contract = old_rows.merge(new, on=PAIR_KEYS, suffixes=("_old", "_new"), validate="one_to_one")
    for field in ("alpha", "budget", "delay", "cs", "cq"):
        if f"{field}_old" in contract and f"{field}_new" in contract and not np.allclose(
                contract[f"{field}_old"].to_numpy(), contract[f"{field}_new"].to_numpy(), equal_nan=True):
            raise ValueError(f"contract mismatch in {field} for {source.parent}")
    return pd.concat([old[~old.policy.isin(policies)], new], ignore_index=True)


def analyse(run: str, corrected: bool = False) -> dict:
    df = load_run(run, corrected=corrected)
    out = {}
    for ds, g in df.groupby("regime"):
        E = g.groupby(["ep", "policy"]).net.mean().unstack()
        absent = [c for c in CERT + UNC if c not in E]
        if absent:  # fail closed (ARIS m3 re-audit): the comparator class must be complete
            raise KeyError(f"{run}/{ds}: comparators missing from records: {absent}")
        best_c = E[CERT].mean().idxmin()
        best_u = E[UNC].mean().idxmin()
        prom = g.groupby("policy").ever_promote.mean()
        cell = {"K": int(E.shape[0]), "best_certified": best_c, "best_uncertified": best_u,
                "mean": E.mean().round(2).to_dict(), "promote": prom.round(3).to_dict(),
                "contrasts": {}}
        for c, host in CANDS.items():
            if c not in E:
                continue
            cc = {"best_certified": contrast(E, c, best_c), "best_uncertified": contrast(E, c, best_u),
                  "never_switch": contrast(E, c, "CONTROL_never_switch")}
            if host and host in E:
                cc["host"] = contrast(E, c, host)
            cell["contrasts"][c] = cc
        out[ds] = cell
    return out


def md(res: dict, title: str) -> list[str]:
    L = [f"## {title}", "", "| dataset | K | candidate | vs best certified | vs host | vs best uncertified | improved/K (sign p) |",
         "|---|---|---|---|---|---|---|"]
    for ds, cell in res.items():
        for c, cc in cell["contrasts"].items():
            b = cc["best_certified"]
            h = cc.get("host")
            u = cc["best_uncertified"]
            L.append(f"| {ds} | {cell['K']} | {c} | {b['mean']:+.1f} [{b['lo']:+.1f},{b['hi']:+.1f}] ({b['vs']}) | "
                     + (f"{h['mean']:+.1f} [{h['lo']:+.1f},{h['hi']:+.1f}]" if h else "") + " | "
                     f"{u['mean']:+.1f} ({u['vs']}) | {b['improved']}/{b['K']} (p={b['sign_p']:.3g}) |")
    return L + [""]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adaptive-gate-corrected-dir", type=Path,
                    help="Write separate real-data analyses after exact-key substitution of corrected replay rows.")
    args = ap.parse_args()
    global DOC
    if args.adaptive_gate_corrected_dir:
        DOC = args.adaptive_gate_corrected_dir
    fresh = analyse("real_fresh", corrected=bool(args.adaptive_gate_corrected_dir))
    exposed = analyse("real_exposed", corrected=bool(args.adaptive_gate_corrected_dir))
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "real_results.json").write_text(json.dumps({"fresh": fresh, "exposed": exposed}, indent=1,
                                                      default=float) + "\n")
    correction_note = ("Same-seed adaptive-gate correction rows replace historical rows by exact stream, episode, seed, and policy keys; "
                       "this is a code-correction sensitivity, not independent confirmation. "
                       if args.adaptive_gate_corrected_dir else "")
    L = ["# Real-data validation", "", correction_note + "Fresh streams registered in aeb2d4f before any policy run (20 policy seeds, "
         "base 2026110604). Exposed streams are descriptive (10 seeds, base 2026110603). Unit = episode; "
         "consecutive windows, so CIs are optimistic.", ""]
    L += md(fresh, "Fresh, never-used streams (external validation)")
    L += md(exposed, "Previously exposed streams (descriptive only)")
    (DOC / "real_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
