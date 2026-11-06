"""Registered analysis of the Failure Atlas v2 fresh-seed validation (protocol Amendments 1-2).

    uv run python scripts/failure_atlas_v2_flq/analyze_validation.py

Input: outputs/failure_atlas_v2/validation_synth_wmaxfix_20261105 (full frozen seed schedule
rerun after correcting the adaptive-range bet-ordering issue; all current policies share each stream).
Writes docs/failure_atlas_v2_flq/results/validation_synthetic.md and the corrected run's summary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyze_atlas_v2 import boot_ci  # noqa: E402

OUT = HERE.parents[1] / "outputs/failure_atlas_v2/validation_synth_wmaxfix_20261105"
NULLS = ["V_null", "V_worse", "V_null_dep_r5", "V_null_dep_r8"]
STAT_ALT = ["V_better_a", "V_better_b", "V_better_c", "V_dep_better_r5", "V_near", "V_bursty"]
CHANGE = ["V_late_600", "V_reversal_1000", "V_recurrent"]
BOUND = 0.05 + 2 * np.sqrt(0.05 * 0.95 / 100)
PUBLISHED_CERT = ["gated_deployment", "gated_adaptive_range", "discern_style",
                  "discern_design_floor", "SMCS+retain-incumbent", "xu_acquisition_only"]
UNCERT = ["model_picker_adapter", "model_selector_causal", "online_llm_picker", "cams_adapter",
          "variance_min_ipw", "gong_zhang_paid_obs", "qiu_delayed_movement", "ryabchenko_capacity"]
PAIRS = [  # (host, repaired)  -- FLQ = QCE + front (Amendment 1); front-only on strong hosts
    ("gated_deployment", "gated_deployment+QCE+front"),
    ("discern_style", "discern_style+QCE+front"),
    ("SMCS+retain-incumbent", "SMCS+QCE+front"),
    ("xu_acquisition_only", "xu_acquisition_only+QCE+front"),
    ("gated_adaptive_range", "gated_adaptive_range+front"),
    ("discern_design_floor", "discern_design_floor+front"),
]
OURS = ["QSG", "QSG-r25", "gated_deployment+QCE+front", "discern_style+QCE+front", "SMCS+QCE+front",
        "xu_acquisition_only+QCE+front", "gated_adaptive_range+front", "P7s_settled"]


def load():
    return pd.read_json(OUT / "records.jsonl", lines=True)


def pdiff(d, reg, a, b):
    x = d[(d.regime == reg)]
    A = x[x.policy == a].set_index("seed")["net"]
    B = x[x.policy == b].set_index("seed")["net"]
    j = A.index.intersection(B.index)
    diff = (B.loc[j] - A.loc[j]).to_numpy()
    lo, hi = boot_ci(diff)
    return float(diff.mean()), lo, hi


def main():
    d = load()
    s = d.groupby(["regime", "policy"]).agg(net=("net", "mean"), promote=("ever_promote", "mean"),
                                            switches=("switches", "mean")).reset_index()
    net = s.pivot(index="regime", columns="policy", values="net")
    prom = s.pivot(index="regime", columns="policy", values="promote")
    cert = {p: bool((prom.loc[NULLS, p] <= BOUND).all()) for p in prom.columns}
    lines = ["# Failure Atlas v2: fresh-seed synthetic validation", "",
             "Seed base 2026110399, 13 registered regimes x 100 paired streams, v2 contract. "
             "Analysis registered in protocol Amendments 1-2 before rows were read. "
             f"Certified = promotion <= {BOUND:.4f} on every null ({', '.join(NULLS)}).", "",
             "## Certification check (promotion rate on the validation nulls)", "",
             "| policy | " + " | ".join(NULLS) + " | certified |", "|---" * (len(NULLS) + 2) + "|"]
    for p in sorted(prom.columns, key=lambda p: (not cert[p], p)):
        lines.append(f"| {p} | " + " | ".join(f"{prom.loc[r, p]:.2f}" for r in NULLS)
                     + f" | {'yes' if cert[p] else 'NO'} |")
    # primary: host vs repaired on stationary alternatives
    lines += ["", "## Primary: repaired minus host, stationary alternatives (paired, 100 streams)", "",
              "| host -> repaired | " + " | ".join(STAT_ALT) + " | CI<0 count |",
              "|---" * (len(STAT_ALT) + 2) + "|"]
    prim = {}
    for h, r in PAIRS:
        cells, wins = [], 0
        for reg in STAT_ALT:
            m, lo, hi = pdiff(d, reg, h, r)
            wins += hi < 0
            cells.append(f"{m:+.1f} [{lo:+.1f},{hi:+.1f}]")
        prim[f"{h} -> {r}"] = int(wins)
        lines.append(f"| {h} -> {r} | " + " | ".join(cells) + f" | {wins}/6 |")
    lines += ["", "## Same comparisons on change regimes and nulls (secondary, reported in full)", "",
              "| host -> repaired | " + " | ".join(CHANGE + NULLS) + " |",
              "|---" * (len(CHANGE + NULLS) + 1) + "|"]
    for h, r in PAIRS:
        cells = []
        for reg in CHANGE + NULLS:
            m, lo, hi = pdiff(d, reg, h, r)
            cells.append(f"{m:+.1f} [{lo:+.1f},{hi:+.1f}]")
        lines.append(f"| {h} -> {r} | " + " | ".join(cells) + " |")
    # secondary: best certified ours vs strongest published certified (certified only)
    pub_ok = [p for p in PUBLISHED_CERT if cert.get(p)]
    ours_ok = [p for p in OURS if cert.get(p)]
    lines += ["", "## Secondary: our certified variants vs strongest certified published method", "",
              f"Published certified methods passing the criterion: {', '.join(pub_ok) or 'none'}. "
              f"Our variants passing: {', '.join(ours_ok) or 'none'}. The strongest published "
              "method is chosen per regime on these same seeds (favours the comparator).", "",
              "| regime | strongest published (net) | best ours (net) | ours - published [95% CI] | "
              "best uncertified (net, promote on V_null) | never |", "|---|---|---|---|---|---|"]
    sec = {}
    for reg in STAT_ALT + CHANGE + NULLS:
        pb = net.loc[reg, pub_ok].idxmin() if pub_ok else None
        ob = net.loc[reg, ours_ok].idxmin() if ours_ok else None
        ub = net.loc[reg, UNCERT].idxmin()
        if pb and ob:
            m, lo, hi = pdiff(d, reg, pb, ob)
            sec[reg] = {"published": pb, "ours": ob, "diff": m, "lo": lo, "hi": hi}
            cmp_ = f"{m:+.1f} [{lo:+.1f},{hi:+.1f}]"
        else:
            cmp_ = "n/a"
        fmt = lambda p: f"{p} ({net.loc[reg, p]:.1f})" if p else "none"  # noqa: E731
        lines.append(f"| {reg} | {fmt(pb)} | {fmt(ob)} | {cmp_} | "
                     f"{ub} ({net.loc[reg, ub]:.1f}, {prom.loc['V_null', ub]:.2f}) | "
                     f"{net.loc[reg, 'CONTROL_never_switch']:.1f} |")
    lines += ["", "## Net cost, all policies", "", net.round(1).T.to_markdown()]
    (HERE.parents[1] / "docs/failure_atlas_v2_flq/results/validation_synthetic.md").write_text("\n".join(lines) + "\n")
    (OUT / "validation_summary.json").write_text(json.dumps(
        {"bound": BOUND, "certified": cert, "primary_ci_below_zero": prim, "secondary": sec},
        indent=1, default=float))
    print("\n".join(lines[: 60]))


if __name__ == "__main__":
    main()
