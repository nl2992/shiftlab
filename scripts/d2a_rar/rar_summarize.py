"""Summarise results/d2a_rar/rar_repro.json into markdown tables (means, paired differences, 2-SEM)."""

import json
import sys

import numpy as np

f = sys.argv[1] if len(sys.argv) > 1 else "results/d2a_rar/rar_repro.json"
with open(f) as fh:
    R = json.load(fh)
streams = sorted({k.split("|")[0] for k in R if k != "_meta"})
pol = ["no_response", "always_retrain", "binary", "alert_only", "rollback_only", "full_rar"]
for rho in ("1", "5", "100"):
    print(f"\n### Mean net utility U at rho={rho}\n")
    print("| stream | n | " + " | ".join(pol) + " |\n|" + "---|" * (len(pol) + 2))
    for s in streams:
        recs = [v for k, v in R.items() if k.startswith(s + "|")]
        print(
            f"| {s} | {len(recs)} | "
            + " | ".join(f"{np.mean([r['policies'][p]['U'][rho] for r in recs]):,.0f}" for p in pol)
            + " |"
        )
print("\n### Accuracy over evaluated instances (mean)\n")
print("| stream | " + " | ".join(pol) + " |\n|" + "---|" * (len(pol) + 1))
for s in streams:
    recs = [v for k, v in R.items() if k.startswith(s + "|")]
    print(
        f"| {s} | "
        + " | ".join(
            f"{np.mean([r['policies'][p]['n_correct'] / r['policies'][p]['n_eval'] for r in recs]):.4f}"
            for p in pol
        )
        + " |"
    )
print("\n### Full RAR minus comparator, paired by seed (mean +- SEM; * = |mean|>2 SEM)\n")
for rho in ("1", "100"):
    print(
        f"rho={rho}\n\n| stream | vs binary | vs rollback_only | vs always_retrain | vs no_response |\n|---|---|---|---|---|"
    )
    for s in streams:
        recs = [v for k, v in R.items() if k.startswith(s + "|")]
        row = []
        for c in ("binary", "rollback_only", "always_retrain", "no_response"):
            d = np.array(
                [r["policies"]["full_rar"]["U"][rho] - r["policies"][c]["U"][rho] for r in recs]
            )
            sem = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float("nan")
            row.append(f"{d.mean():+,.0f} +- {sem:,.0f}{'*' if abs(d.mean()) > 2 * sem else ''}")
        print(f"| {s} | " + " | ".join(row) + " |")
    print()
print(
    "### Action counts per run (mean): retrain/alert/rollback\n\n| stream | "
    + " | ".join(pol)
    + " |\n|"
    + "---|" * (len(pol) + 1)
)
for s in streams:
    recs = [v for k, v in R.items() if k.startswith(s + "|")]
    cells = []
    for p in pol:
        c = [
            np.mean([r["policies"][p]["counts"][k] for r in recs])
            for k in ("retrain", "alert", "rollback")
        ]
        cells.append("/".join(f"{x:.1f}" for x in c))
    print(f"| {s} | " + " | ".join(cells) + " |")
print(
    "\n### Cost-aware binary vs Full RAR (mean U; CA-Binary - Full RAR)\n\n| stream | "
    + " | ".join(f"rho={r}" for r in (1, 10, 100, 1000))
    + " |\n|---|---|---|---|---|"
)
for s in streams:
    recs = [v for k, v in R.items() if k.startswith(s + "|")]
    cells = []
    for rho in (1, 10, 100, 1000):
        d = np.array(
            [
                r["policies"][f"cost_aware_binary@{rho}"]["U"]
                - r["policies"]["full_rar"]["U"][
                    str(float(rho))
                    if str(float(rho)) in r["policies"]["full_rar"]["U"]
                    else str(rho)
                ]
                for r in recs
            ]
        )
        sem = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float("nan")
        cells.append(f"{d.mean():+,.0f} +- {sem:,.0f}")
    print(f"| {s} | " + " | ".join(cells) + " |")
print("\nRollback causes (all runs):")
from collections import Counter

for s in streams:
    cnt = Counter(
        c
        for k, v in R.items()
        if k.startswith(s + "|")
        for c in v["policies"]["full_rar"]["causes"]
    )
    print(f"- {s} full_rar: {dict(cnt)}")
