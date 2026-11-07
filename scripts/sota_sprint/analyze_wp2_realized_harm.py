#!/usr/bin/env python3
"""Decompose WP2's all-in realized excess economic cost against never-switch.

Reads existing WP2 records only. The recorded `harm` field is legacy naming for
J(policy)-J(never-switch), an all-in economic cost difference. This decomposes it
into prediction-loss, label-spending, and switching-cost components. It is not
application-level decision harm: these records do not encode causal application utility.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from bench import CONTRACT

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS = [
    "outputs/sprint2/WP2/run1_twin2",
    "outputs/sprint2/WP2/run3_synth",
    "outputs/sprint2/WP2/run4_fresh",
    *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "outputs/sprint2/WP2").glob("run2_*"))
      if (p / "records.jsonl").is_file()],
]
NBOOT = 2000


def cluster_id(row: pd.Series) -> str:
    if row["kind"] == "synthetic":
        return f"{row['regime']}|seed={row['seed']}"
    if row.get("split", -1) >= 0:
        return f"{row['regime']}|split={row['split']}"
    return f"{row['regime']}|episode={row['ep']}"


def read_runs(dirs: list[str]) -> pd.DataFrame:
    rows = []
    for relative in dirs:
        path = ROOT / relative / "records.jsonl"
        if not path.is_file():
            raise SystemExit(f"missing WP2 raw records: {path}")
        with path.open() as stream:
            for line in stream:
                r = json.loads(line)
                promos = r.pop("promos", [])
                promoted = bool(r.get("ever_promote", False))
                first_ei = int(promos[0].get("ei", 0)) if promos else 0
                harm = float(r["harm"])
                never_loss = float(r["net"]) - harm
                prediction_loss_delta = float(r["loss"]) - never_loss
                label_cost = CONTRACT["cq"] * int(r["labels"])
                switch_cost = CONTRACT["cs"] * int(r["switches"])
                if not np.isclose(prediction_loss_delta + label_cost + switch_cost, harm,
                                  rtol=1e-9, atol=1e-7):
                    raise ValueError(f"economic-cost decomposition mismatch in {relative}: {r}")
                r.update({
                    "run": Path(relative).name,
                    "first_promo_ei": float(promoted and first_ei == 1),
                    "any_promo_db_nonpositive": float(promoted and float(r["db"]) <= 0),
                    "all_in_economic_excess_cost_positive": float(harm > 0),
                    "all_in_economic_excess_cost": harm,
                    "prediction_loss_delta": prediction_loss_delta,
                    "prediction_loss_increase": float(prediction_loss_delta > 0),
                    "label_expenditure": label_cost,
                    "switching_expenditure": switch_cost,
                })
                rows.append(r)
    frame = pd.DataFrame(rows)
    frame["cluster"] = frame.apply(cluster_id, axis=1)
    return frame


def cluster_boot(g: pd.DataFrame, metric: str, rng: np.random.Generator) -> tuple[float, float, float]:
    cl = g.groupby("cluster", sort=True)[metric].mean().to_numpy(float)
    point = float(cl.mean())
    idx = rng.integers(0, len(cl), size=(NBOOT, len(cl)))
    samples = cl[idx].mean(axis=1)
    return point, float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=",".join(DEFAULT_RUNS),
                    help="comma-separated WP2 run directories; each must contain records.jsonl")
    ap.add_argument("--json", default="docs/sprint2/wp2/realized_harm.json")
    ap.add_argument("--markdown", default="docs/sprint2/wp2/REALIZED_HARM.md")
    args = ap.parse_args()
    dirs = [x for x in args.runs.split(",") if x]
    frame = read_runs(dirs)
    rows = []
    for i, (keys, g) in enumerate(frame.groupby(["run", "T", "delay_mult", "regime", "policy"], sort=True)):
        rng = np.random.default_rng(2026111200 + i)
        row = dict(zip(("run", "T", "delay_mult", "regime", "policy"), keys))
        row.update({"records": int(len(g)), "clusters": int(g.cluster.nunique())})
        for metric, label in (("ever_promote", "promotion_rate"),
                              ("first_promo_ei", "first_promotion_EI_rate"),
                              ("any_promo_db_nonpositive", "any_promotion_nonpositive_DB_rate"),
                              ("prediction_loss_increase", "prediction_loss_increase_rate"),
                              ("all_in_economic_excess_cost_positive", "all_in_economic_excess_cost_positive_rate"),
                              ("prediction_loss_delta", "mean_prediction_loss_delta"),
                              ("label_expenditure", "mean_label_expenditure"),
                              ("switching_expenditure", "mean_switching_expenditure"),
                              ("all_in_economic_excess_cost", "mean_all_in_economic_excess_cost")):
            point, lo, hi = cluster_boot(g, metric, rng)
            row[label] = [point, lo, hi]
        rows.append(row)

    result = {
        "title": "WP2 all-in realized excess economic cost decomposition (retrospective supplement)",
        "sources": dirs,
        "n_boot": NBOOT,
        "uncertainty": "Percentile bootstrap over independent clusters within each reported policy/regime/run cell: seed for synthetic, split for real twins, episode for fresh real.",
        "economic_excess_cost_definition": "J(policy)-J(CONTROL_never_switch) = prediction-loss delta + label expenditure + switching expenditure; the raw records retain the legacy field name harm.",
        "decision_harm_status": "Not identified: the records contain predictive losses and accounting costs, not causal application-level utility.",
        "rate_definition": "P(realized all-in excess economic cost > 0) per policy episode, with ties counted as not positive.",
        "limitations": [
            "This is an evaluator-side retrospective path outcome, not application-level decision harm, a prospective per-promotion test, or an estimate of expected economic value.",
            "T/delay variants re-window the same event streams and are not independent samples.",
            "The five real twin datasets are reused; split bootstrap uncertainty does not represent independent dataset generalization.",
        ],
        "rows": rows,
    }
    json_path = ROOT / args.json
    md_path = ROOT / args.markdown
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# WP2 all-in realized excess economic cost",
        "",
        "Retrospective evaluator-side supplement, generated from saved WP2 records. All-in excess economic cost is `J(policy) - J(CONTROL_never_switch)` and decomposes into prediction-loss delta, label expenditure, and switching expenditure. The historical raw-record field is named `harm`; that name does not mean application-level decision harm. These records do not identify causal application utility.",
        "",
        "The positive-cost rate complements the registered first-promotion EI measure and `hp_path`. Prediction-loss increase is reported separately from accounting costs. These are not prospective per-promotion tests, expected-value estimates, or validity guarantees. CIs bootstrap the independent unit within each cell (seed for synthetic, split for real twins, episode for fresh real). T/delay variants reuse event streams; twin datasets are not independent dataset replications.",
        "",
        f"Runs: {', '.join(dirs)}. Bootstrap replicates per cell: {NBOOT}.",
        "",
        "| run | T | delay × | regime | policy | clusters | EI rate | promote and DB≤0 rate | prediction-loss increase rate | mean prediction-loss Δ | mean label cost | mean switch cost | positive all-in cost rate | mean all-in ΔJ |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    def fmt(x: list[float]) -> str:
        return f"{x[0]:.3f} [{x[1]:.3f}, {x[2]:.3f}]"
    for r in rows:
        lines.append(f"| {r['run']} | {r['T']} | {r['delay_mult']:.2f} | {r['regime']} | {r['policy']} | {r['clusters']} | "
                     f"{fmt(r['first_promotion_EI_rate'])} | {fmt(r['any_promotion_nonpositive_DB_rate'])} | "
                     f"{fmt(r['prediction_loss_increase_rate'])} | {fmt(r['mean_prediction_loss_delta'])} | "
                     f"{fmt(r['mean_label_expenditure'])} | {fmt(r['mean_switching_expenditure'])} | "
                     f"{fmt(r['all_in_economic_excess_cost_positive_rate'])} | {fmt(r['mean_all_in_economic_excess_cost'])} |")
    lines += ["", "Machine-readable source-cell output: `realized_harm.json` (legacy filename and raw-record field names)."]
    md_path.write_text("\n".join(lines) + "\n")
    print(f"wrote {json_path} and {md_path}: {len(rows)} cells from {len(frame)} records")


if __name__ == "__main__":
    main()
