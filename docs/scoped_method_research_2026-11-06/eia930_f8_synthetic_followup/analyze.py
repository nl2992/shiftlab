"""Analyze the preregistered paired synthetic F8 follow-up."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RUN = Path(__file__).resolve().parent / "run"
OUT = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (RUN / "records.jsonl").read_text().splitlines() if line]
regimes = sorted({r["regime"] for r in rows})
summary = {}
for regime in regimes:
    rr = [r for r in rows if r["regime"] == regime]
    pols = sorted({r["policy"] for r in rr})
    by_policy = {}
    for policy in pols:
        p = [r for r in rr if r["policy"] == policy]
        by_policy[policy] = {
            "net_mean": float(np.mean([x["net"] for x in p])),
            "loss_mean": float(np.mean([x["loss"] for x in p])),
            "labels_mean": float(np.mean([x["labels"] for x in p])),
            "switches_mean": float(np.mean([x["switches"] for x in p])),
            "promotions": int(sum(x["ever_promote"] for x in p)),
        }
    indexed = {name: {r["seed"]: r for r in rr if r["policy"] == name} for name in pols}
    cand = indexed["fixed_challenger"]
    comp = indexed["cams_adapter"]
    seeds = sorted(set(cand) & set(comp))
    diff = np.array([cand[s]["net"] - comp[s]["net"] for s in seeds])
    rng = np.random.default_rng(2026110718 + regimes.index(regime))
    boot = np.mean(diff[rng.integers(0, len(diff), (20000, len(diff)))], axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    summary[regime] = {
        "n_paired_seeds": len(diff),
        "candidate_minus_cams_mean": float(diff.mean()),
        "candidate_minus_cams_ci95_percentile": [float(lo), float(hi)],
        "primary_gate_evaluated": regime == "F8_rare_better",
        "primary_gate_pass": bool(diff.mean() <= -5 and hi < 0)
        if regime == "F8_rare_better"
        else None,
        "methods": by_policy,
    }

manifest = json.loads((RUN / "manifest.json").read_text())
manifest["records_sha256"] = (
    __import__("hashlib").sha256((RUN / "records.jsonl").read_bytes()).hexdigest()
)
manifest["analysis"] = summary
(OUT / "ANALYSIS.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
with (OUT / "RESULTS.md").open("w") as f:
    f.write("# Fresh synthetic F8 follow-up results\n\n")
    f.write(
        "Paired bootstrap intervals resample the 100 fresh synthetic streams. The candidate is a fixed deployment control, not a learned method.\n\n"
    )
    for regime, result in summary.items():
        f.write(f"## {regime}\n\n")
        gate = (
            f" Primary F8 gate pass: {result['primary_gate_pass']}."
            if result["primary_gate_evaluated"]
            else " Adverse-cell diagnostic only; no success gate is applied."
        )
        f.write(
            f"Candidate minus CAMS: {result['candidate_minus_cams_mean']:.3f}; paired percentile 95% CI [{result['candidate_minus_cams_ci95_percentile'][0]:.3f}, {result['candidate_minus_cams_ci95_percentile'][1]:.3f}].{gate}\n\n"
        )
        f.write(
            "| Method | Net cost | Loss | Labels | Switches | Promotions |\n|---|---:|---:|---:|---:|---:|\n"
        )
        for name, m in sorted(result["methods"].items(), key=lambda kv: kv[1]["net_mean"]):
            f.write(
                f"| {name} | {m['net_mean']:.3f} | {m['loss_mean']:.3f} | {m['labels_mean']:.1f} | {m['switches_mean']:.2f} | {m['promotions']} |\n"
            )
        f.write("\n")
    f.write("## Interpretation\n\n")
    f.write(
        "These results evaluate a known static control on simulator-generated streams. The F8 cell is the only primary gate; null and reversal cells are adverse scope diagnostics. The apparent null-cell cost difference is not a calibrated type-I error estimate. Results do not establish a novel method or independent real-world transfer.\n"
    )
