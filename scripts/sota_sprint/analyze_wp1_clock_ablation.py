"""Summarize the post hoc WP1 label-clock vs timestamp-clock paired replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "rmm:gated_deployment+RMM"
WALLCLOCK = "rmm:gated_deployment+RMM_wallclock"


def summarize(rows, *, bootstrap_reps=20_000, bootstrap_seed=2026110405):
    by_key = {}
    for r in rows:
        by_key.setdefault((r["regime"], int(r["episode"]), int(r["seed"])), {})[r["policy"]] = r
    paired = []
    for (regime, ep, seed), policies in sorted(by_key.items()):
        if BASELINE not in policies or WALLCLOCK not in policies:
            raise ValueError(f"unpaired row: {(regime, ep, seed)}")
        paired.append(
            {
                "regime": regime,
                "episode": ep,
                "seed": seed,
                "delta_net": policies[WALLCLOCK]["net"] - policies[BASELINE]["net"],
                "baseline_net": policies[BASELINE]["net"],
                "wallclock_net": policies[WALLCLOCK]["net"],
                "baseline_promote": policies[BASELINE]["ever_promote"],
                "wallclock_promote": policies[WALLCLOCK]["ever_promote"],
                "baseline_labels": policies[BASELINE]["labels"],
                "wallclock_labels": policies[WALLCLOCK]["labels"],
            }
        )
    datasets = []
    for name in sorted({p["regime"] for p in paired}):
        ds = [p for p in paired if p["regime"] == name]
        eps = sorted({p["episode"] for p in ds})
        ep_delta = [
            float(np.mean([p["delta_net"] for p in ds if p["episode"] == ep])) for ep in eps
        ]
        datasets.append(
            {
                "dataset": name,
                "episodes": len(eps),
                "paired_episode_seed_rows": len(ds),
                "baseline_mean_net": float(np.mean([p["baseline_net"] for p in ds])),
                "wallclock_mean_net": float(np.mean([p["wallclock_net"] for p in ds])),
                "delta_net_wallclock_minus_label": float(np.mean(ep_delta)),
                "baseline_promotion_rate": float(np.mean([p["baseline_promote"] for p in ds])),
                "wallclock_promotion_rate": float(np.mean([p["wallclock_promote"] for p in ds])),
                "baseline_mean_labels": float(np.mean([p["baseline_labels"] for p in ds])),
                "wallclock_mean_labels": float(np.mean([p["wallclock_labels"] for p in ds])),
            }
        )
    cluster = np.asarray([d["delta_net_wallclock_minus_label"] for d in datasets], dtype=float)
    rng = np.random.default_rng(bootstrap_seed)
    idx = rng.integers(0, len(cluster), size=(bootstrap_reps, len(cluster)))
    boot = cluster[idx].mean(axis=1)
    return {
        "method": "paired timestamp-start-grid RMM minus label-clock RMM",
        "units": "event-level losses; episode is unit within dataset, datasets are source clusters",
        "n_datasets": len(datasets),
        "n_episodes": len(paired) // max(1, len({p["seed"] for p in paired})),
        "n_paired_episode_seed_rows": len(paired),
        "datasets": datasets,
        "equal_dataset_mean_delta_net": float(cluster.mean()),
        "cluster_bootstrap_95_ci": [float(x) for x in np.quantile(boot, [0.025, 0.975])],
        "cluster_values": cluster.tolist(),
        "bootstrap_reps": bootstrap_reps,
        "bootstrap_seed": bootstrap_seed,
        "limitations": [
            "post hoc, unregistered ablation on the five fresh UCI datasets with timestamps only",
            "five dataset clusters give a coarse cluster-bootstrap interval",
            "the timestamp-clock detector is given the fixed episode endpoint to place its finite start grid",
            "label delays remain event-count delays; timestamp-clock starts do not model label publication times",
            "no alpha calibration, multiplicity correction, or anytime guarantee is claimed",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "records", nargs="?", default="outputs/sprint2/WP1/clock_ablation_posthoc3/records.jsonl"
    )
    ap.add_argument(
        "--out", type=Path, default=Path("docs/sprint2/wp1/clock_ablation_posthoc3.json")
    )
    a = ap.parse_args(argv)
    src = Path(a.records)
    if not src.is_absolute():
        src = ROOT / src
    rows = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    result = summarize(rows)
    result["records_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
    out = a.out if a.out.is_absolute() else ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    md = [
        "# WP1 label-clock vs timestamp-clock RMM ablation",
        "",
        "Post hoc paired replay on the five timestamped fresh datasets (three policy seeds per episode).",
        "Positive ΔJ means timestamp-clock costs more.",
        "",
        "| Dataset | Episodes | Label-clock J | Timestamp-clock J | ΔJ | Label-clock promotes | Timestamp-clock promotes |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for d in result["datasets"]:
        md.append(
            f"| {d['dataset']} | {d['episodes']} | {d['baseline_mean_net']:.1f} | {d['wallclock_mean_net']:.1f} | {d['delta_net_wallclock_minus_label']:+.1f} | {d['baseline_promotion_rate']:.3f} | {d['wallclock_promotion_rate']:.3f} |"
        )
    md += [
        "",
        f"Equal-dataset mean ΔJ: **{result['equal_dataset_mean_delta_net']:+.2f}**; five-cluster bootstrap 95% CI **[{result['cluster_bootstrap_95_ci'][0]:+.2f}, {result['cluster_bootstrap_95_ci'][1]:+.2f}]**.",
        "",
        "Exploratory post hoc evidence only. Limitations are enumerated in the JSON; this does not cover cached streams or publication-time delays.",
        "",
    ]
    out.with_suffix(".md").write_text("\n".join(md))
    print(f"wrote {out} and {out.with_suffix('.md')}")


if __name__ == "__main__":
    main()
