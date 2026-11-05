"""Exploratory simultaneous paired-seed inference for P6 vs frozen comparator set.

Uses a paired-seed max-statistic bootstrap to avoid selecting one comparator on
these same evaluation seeds and then reporting an unadjusted interval for it.
It is not confirmatory: the run is post-development and the simulator regimes
are fixed synthetic settings.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

COMPARATORS = [
    "gated_deployment",
    "gated_adaptive_range+front",
    "discern_style",
    "SMCS+retain-incumbent",
    "choe_ramdas_eb+front",
]
CANDIDATE = "P6_LRMD_U"


def analyze(path: Path, n_boot: int, seed: int) -> dict:
    d = pd.read_json(path, lines=True)
    required = {"regime", "seed", "policy", "net"}
    if not required.issubset(d.columns):
        raise ValueError(f"missing columns: {sorted(required-set(d.columns))}")
    rng = np.random.default_rng(seed)
    out = {}
    for regime, g in d.groupby("regime", sort=True):
        p = g.pivot(index="seed", columns="policy", values="net")
        missing = {CANDIDATE, *COMPARATORS} - set(p.columns)
        if missing:
            raise ValueError(f"{regime}: missing policies {sorted(missing)}")
        p = p[[CANDIDATE, *COMPARATORS]].dropna()
        delta = np.column_stack([p[CANDIDATE].to_numpy() - p[c].to_numpy() for c in COMPARATORS])
        obs = delta.mean(axis=0)
        centered = delta - obs
        ix = rng.integers(0, len(delta), size=(n_boot, len(delta)))
        boot_means = delta[ix].mean(axis=1)
        # One-sided simultaneous upper bound for max_j E[delta_j], using a
        # centered paired-seed max bootstrap critical value.
        boot_centered = boot_means - obs
        crit = float(np.quantile(boot_centered.max(axis=1), .95, method="higher"))
        max_mean = float(obs.max())
        best_eval = int(obs.argmin())
        out[str(regime)] = {
            "n_paired_seeds": int(len(p)),
            "candidate": CANDIDATE,
            "comparator_set": COMPARATORS,
            "mean_candidate_minus_comparator": {c: float(v) for c, v in zip(COMPARATORS, obs)},
            "evaluation_best_comparator": COMPARATORS[best_eval],
            "best_comparator_point_contrast": float(obs[best_eval]),
            "max_comparator_point_contrast": max_mean,
            "simultaneous_one_sided_95_upper_bound_for_max_contrast": max_mean + crit,
            "candidate_beats_all_comparators_by_simultaneous_bound": bool(max_mean + crit < 0),
            "method": "paired-seed centered max-statistic percentile bootstrap",
            "bootstrap_replicates": n_boot,
        }
    return {
        "status": "POST_DEVELOPMENT_EXPLORATORY_SELECTION_ADJUSTED_SENSITIVITY",
        "source": str(path),
        "candidate": CANDIDATE,
        "comparator_set": COMPARATORS,
        "seed_unit": "paired synthetic run seed within regime",
        "interpretation": "The max-statistic bound addresses selection among this frozen comparator set within each regime. It does not adjust across regimes, candidate development, or other analyses, and does not make the post-development run confirmatory.",
        "regimes": out,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--bootstrap", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2026110816)
    a = ap.parse_args()
    result = analyze(a.records, a.bootstrap, a.seed)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
