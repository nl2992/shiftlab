#!/usr/bin/env python3
"""Summarize the frozen H2 Round-5 follow-up without treating real rows as independent sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[2]
POLICIES = [
    "H2",
    "D2",
    "A5b",
    "H1",
    "H2-iid_space",
    "H2-gateonly",
    "gated_adaptive_range+front",
    "CONTROL_never_switch",
]
NULL_POLICIES = ["H2", "H2-iid_space", "H2-gateonly", "D2", "A5b"]
REAL_POLICIES = ["H2", "D2", "A5b", "gated_adaptive_range+front", "CONTROL_never_switch"]


def frame(
    path: Path, policies: list[str], seeds: int, *, datasets: list[str] | None = None
) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)
    if set(df.policy.unique()) != set(policies):
        raise ValueError(f"policy coverage mismatch in {path}: {sorted(df.policy.unique())}")
    if datasets is not None and set(df.regime.unique()) != set(datasets):
        raise ValueError(f"dataset coverage mismatch in {path}: {sorted(df.regime.unique())}")
    counts = df.groupby(["regime", "ep", "seed", "policy"]).size()
    if not (counts == 1).all() or len(
        counts
    ) != df.regime.nunique() * df.ep.nunique() * seeds * len(policies):
        # Real datasets can have unequal episode counts; require complete policy/seed coverage per episode.
        expected = df.groupby(["regime", "ep"]).size()
        if not (expected == seeds * len(policies)).all():
            raise ValueError(f"incomplete or duplicate episode/seed/policy cells in {path}")
    return df


def t_summary(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    mean = float(x.mean())
    half = (
        float(student_t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))
        if len(x) > 1
        else float("nan")
    )
    return {"n": len(x), "mean": mean, "ci95": [mean - half, mean + half]}


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float]:
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    lower = 0.0 if k == 0 else max(0.0, float(center - half))
    upper = 1.0 if k == n else min(1.0, float(center + half))
    return [lower, upper]


def summarize(synth: Path, null: Path, real: Path | None) -> tuple[dict, str]:
    expected_synth = [
        "F0_better",
        "F9_bursty_better",
        "F1_late_800",
        "F3_reversal_800",
        "F5_dep_better_r8",
        "S_dep_better_r95",
        "F0_null",
        "F5_dep_null_r8",
        "F5_dep_null_r95",
    ]
    d = frame(synth, POLICIES, 100, datasets=expected_synth)
    syn = {"seed_base": 2026110801, "records": len(d), "by_regime": {}}
    for regime, rg in d.groupby("regime"):
        means = {}
        for policy, g in rg.groupby("policy"):
            detected = g.detect_delay[g.detect_delay >= 0]
            means[policy] = {
                "net": float(g.net.mean()),
                "promotion": float(g.ever_promote.mean()),
                "labels": float(g.labels.mean()),
                "delay_positive": float(detected.median()) if len(detected) else None,
                "nondetection": float((g.detect_delay < 0).mean()),
                "runtime_max": float(g.runtime_s.max()),
            }
        pairs = rg.pivot(index="seed", columns="policy", values="net")
        contrasts = {
            ref: t_summary((pairs.H2 - pairs[ref]).to_numpy())
            for ref in (
                "D2",
                "A5b",
                "H1",
                "H2-iid_space",
                "H2-gateonly",
                "gated_adaptive_range+front",
            )
        }
        syn["by_regime"][regime] = {"policy_means": means, "paired_H2_minus": contrasts}

    expected_null = ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95", "P_markov_null_r98"]
    ndf = frame(null, NULL_POLICIES, 1000, datasets=expected_null)
    nsum = {"seed_base": 2026110802, "records": len(ndf), "by_regime": {}}
    for (regime, policy), g in ndf.groupby(["regime", "policy"]):
        k, n = int(g.ever_promote.sum()), len(g)
        nsum["by_regime"].setdefault(regime, {})[policy] = {
            "promotions": k,
            "n": n,
            "rate": k / n,
            "wilson95": wilson(k, n),
            "mean_net": float(g.net.mean()),
            "mean_labels": float(g.labels.mean()),
        }

    result = {
        "protocol": "H2 Round-5 post-development follow-up",
        "synthetic": syn,
        "markov_null": nsum,
        "real": None,
        "limitations": [
            "Post-development, fixed simulator regimes and previously exposed sources; not independent confirmation.",
            "Real loss-stream results are descriptive and do not assign causal change labels.",
            "Wilson intervals quantify Monte Carlo uncertainty conditional on each fixed simulated regime.",
        ],
    }
    lines = [
        "# H2 Round-5 post-development follow-up",
        "",
        "## Synthetic 100-seed paired screen",
        "",
        "ΔJ is H2 minus comparator; negative favors H2. Intervals are paired t intervals across simulator seeds.",
        "",
        "| Regime | H2 J | Δ vs D2 [95% CI] | Δ vs A5b [95% CI] | H2 promotes | H2 labels |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for regime, info in syn["by_regime"].items():
        h = info["policy_means"]["H2"]
        cells = []
        for ref in ("D2", "A5b"):
            c = info["paired_H2_minus"][ref]
            cells.append(f"{c['mean']:+.1f} [{c['ci95'][0]:+.1f}, {c['ci95'][1]:+.1f}]")
        lines.append(
            f"| {regime} | {h['net']:.1f} | {cells[0]} | {cells[1]} | {h['promotion']:.3f} | {h['labels']:.1f} |"
        )
    lines += [
        "",
        "## Markov-null Monte Carlo screen",
        "",
        "Wilson intervals are per fixed null regime; V2 scope is stationary first-order Markov only.",
        "",
        "| Regime | Policy | Promotions / 1,000 | Rate [Wilson 95%] | Mean labels |",
        "|---|---|---:|---:|---:|",
    ]
    for regime, pols in nsum["by_regime"].items():
        for policy, x in pols.items():
            lines.append(
                f"| {regime} | {policy} | {x['promotions']}/{x['n']} | {x['rate']:.3f} [{x['wilson95'][0]:.3f}, {x['wilson95'][1]:.3f}] | {x['mean_labels']:.1f} |"
            )
    if real is not None:
        sources = [
            "rialto",
            "openml_ldpa",
            "airlines",
            "criteo",
            "bank",
            "elec2",
            "weather",
            "spam",
            "uci_occupancy",
            "metro",
            "beijing_pm25",
            "bike_hour",
            "appliances",
            "household_power",
        ]
        rdf = frame(real, REAL_POLICIES, 3, datasets=sources)
        by = (
            rdf.groupby(["regime", "policy"])
            .agg(net=("net", "mean"), promotion=("ever_promote", "mean"), labels=("labels", "mean"))
            .reset_index()
        )
        pivot = by.pivot(index="regime", columns="policy", values="net")
        rng = np.random.default_rng(2026110414)
        contrasts = {}
        for ref in ("D2", "A5b", "gated_adaptive_range+front", "CONTROL_never_switch"):
            vals = (pivot.H2 - pivot[ref]).to_numpy()
            boot = np.mean(rng.choice(vals, size=(20000, len(vals)), replace=True), axis=1)
            contrasts[ref] = {
                "equal_dataset_mean": float(vals.mean()),
                "cluster_bootstrap95": [
                    float(np.quantile(boot, 0.025)),
                    float(np.quantile(boot, 0.975)),
                ],
                "per_dataset": dict(zip(pivot.index.tolist(), vals.tolist())),
            }
        result["real"] = {
            "seed_base": 2026110803,
            "records": len(rdf),
            "n_sources": 14,
            "per_source": by.to_dict(orient="records"),
            "equal_dataset_paired_H2_minus": contrasts,
            "bootstrap_reps": 20000,
            "bootstrap_seed": 2026110414,
        }
        lines += [
            "",
            "## Real fixed-stream replay",
            "",
            "Three paired policy seeds per episode; sources receive equal weight in the summary.",
            "",
            "| Dataset | H2 J | D2 J | A5b J | Adaptive-range J | Never-switch J |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        rp = by.pivot(index="regime", columns="policy", values="net")
        for ds, row in rp.iterrows():
            lines.append(
                f"| {ds} | {row['H2']:.1f} | {row['D2']:.1f} | {row['A5b']:.1f} | {row['gated_adaptive_range+front']:.1f} | {row['CONTROL_never_switch']:.1f} |"
            )
        lines += [
            "",
            "Equal-dataset paired contrasts (H2 minus comparator), 14-source cluster bootstrap:",
            "",
        ]
        for ref, x in contrasts.items():
            lines.append(
                f"- vs {ref}: {x['equal_dataset_mean']:+.1f}, 95% CI [{x['cluster_bootstrap95'][0]:+.1f}, {x['cluster_bootstrap95'][1]:+.1f}]."
            )
    lines += ["", "## Limitations", "", *[f"- {x}" for x in result["limitations"]], ""]
    return result, "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", type=Path, required=True)
    ap.add_argument("--null", type=Path, required=True)
    ap.add_argument("--real", type=Path)
    ap.add_argument("--out", type=Path, default=Path("docs/sprint2/family_h/round5_h2.json"))
    a = ap.parse_args()
    j, md = summarize(a.synthetic, a.null, a.real)
    out = a.out if a.out.is_absolute() else ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(j, indent=2) + "\n")
    out.with_suffix(".md").write_text(md)
    print(f"wrote {out} and {out.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
