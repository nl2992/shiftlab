"""Analyze the preregistered WP1 post-development E_rb reversal sensitivity."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

HOSTS = ["gated_deployment", "discern_style", "SMCS+retain-incumbent", "gated_adaptive_range"]
REGIMES = ["F3_reversal_800", "W_reversal_700", "S_reversal_400"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    d = pd.read_json(a.run_dir / "records.jsonl", lines=True)
    p = d.pivot(index=["regime", "seed"], columns="policy", values="net")
    contrasts = {}
    per_seed = []
    for reg in REGIMES:
        for host in HOSTS:
            e, r = f"E_rb:{host}", f"rmm:{host}+RMM"
            vals = (p[e] - p[r]).loc[reg].dropna()
            m = float(vals.mean())
            se = float(vals.std(ddof=1) / np.sqrt(len(vals)))
            q = float(t.ppf(0.975, len(vals) - 1))
            contrasts[f"{reg}|{host}"] = {
                "mean_delta_J": m,
                "ci95_t": [m - q * se, m + q * se],
                "n": len(vals),
            }
    for seed in sorted(d.seed.unique()):
        vals = []
        for reg in REGIMES:
            for host in HOSTS:
                vals.append(
                    float(
                        p.loc[(reg, seed), f"E_rb:{host}"] - p.loc[(reg, seed), f"rmm:{host}+RMM"]
                    )
                )
        per_seed.append(float(np.mean(vals)))
    x = np.asarray(per_seed)
    mean = float(x.mean())
    se = float(x.std(ddof=1) / np.sqrt(len(x)))
    q = float(t.ppf(0.975, len(x) - 1))
    out = {
        "status": "POST_DEVELOPMENT_SENSITIVITY_NOT_CONFIRMATORY",
        "run_dir": str(a.run_dir),
        "regimes": REGIMES,
        "hosts": HOSTS,
        "primary": {
            "estimand": "per-seed equal-weight mean over 3 regimes x 4 matched hosts of E_rb net J minus RMM net J",
            "mean_delta_J": mean,
            "ci95_t": [mean - q * se, mean + q * se],
            "n_seed_blocks": len(x),
            "directionally_supportive": bool(mean < 0 and mean + q * se < 0),
        },
        "exploratory_host_regime_contrasts": contrasts,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
