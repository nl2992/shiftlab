"""Analyze the corrected, matched Family-H fresh-real comparator screen.

The inferential unit for a fixed stream is the episode; policy seeds are averaged
within episode. Overall summaries weight the five datasets equally and resample
episodes within each fixed dataset. They describe these exposed streams, not
generalization to new datasets. Comparator selection is reported descriptively;
all fixed-comparator contrasts are retained.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from bench import CERTIFIED_PUBLISHED


CANDIDATES = ["H1", "H2", "H3", "H4", "H5", "H6-r10"]
PUBLISHED_CERTIFICATE_PORTS = list(CERTIFIED_PUBLISHED)
SUPPLEMENTAL = ["xu_acquisition_only", "choe_ramdas_eb+front"]
INTERNAL_REFERENCES = ["D2", "A5b", "CONTROL_never_switch"]
DATASETS = ["metro", "beijing_pm25", "bike_hour", "appliances", "household_power"]


def _bootstrap_mean_ci(values: np.ndarray, n_boot: int, rng: np.random.Generator) -> list[float]:
    if len(values) < 2:
        return [float("nan"), float("nan")]
    ix = rng.integers(0, len(values), size=(n_boot, len(values)))
    b = values[ix].mean(axis=1)
    return [float(v) for v in np.quantile(b, [0.025, 0.975])]


def analyze(records: Path, *, n_boot: int = 20_000, seed: int = 2026110417) -> dict:
    d = pd.read_json(records, lines=True)
    required = {"regime", "ep", "seed", "policy", "net", "labels", "ever_promote", "detect_delay"}
    missing_cols = required - set(d.columns)
    if missing_cols:
        raise ValueError(f"missing columns: {sorted(missing_cols)}")

    expected_policies = set(CANDIDATES + PUBLISHED_CERTIFICATE_PORTS + SUPPLEMENTAL + INTERNAL_REFERENCES)
    if set(d.policy.unique()) != expected_policies:
        raise ValueError(
            f"unexpected policy set; missing={sorted(expected_policies - set(d.policy.unique()))}, "
            f"extra={sorted(set(d.policy.unique()) - expected_policies)}"
        )
    if d.duplicated(["regime", "ep", "seed", "policy"]).any():
        raise ValueError("duplicate regime/episode/seed/policy records")
    rng = np.random.default_rng(seed)
    out: dict[str, object] = {}
    for dataset in DATASETS:
        g = d[d.regime == dataset]
        present = set(g.policy.unique())
        absent = expected_policies - present
        if absent:
            raise ValueError(f"{dataset}: missing policies {sorted(absent)}")
        expected_seeds = set(range(20))
        cache = Path(__file__).resolve().parents[2] / "data" / "sprint_fresh_losses" / f"{dataset}.npz"
        with np.load(cache) as losses:
            expected_episodes = set(range(int(losses["l0"].shape[0])))
        episode_ids = set(g.ep.unique())
        if episode_ids != expected_episodes:
            raise ValueError(
                f"{dataset}: episode coverage mismatch; missing={sorted(expected_episodes - episode_ids)[:10]}, "
                f"extra={sorted(episode_ids - expected_episodes)[:10]}"
            )
        expected_cells = {(p, ep) for p in expected_policies for ep in episode_ids}
        observed_cells = set(zip(g.policy, g.ep))
        if observed_cells != expected_cells:
            raise ValueError(
                f"{dataset}: incomplete policy/episode coverage; "
                f"missing={list(expected_cells - observed_cells)[:5]}"
            )
        bad_coverage = g.groupby(["policy", "ep"]).seed.apply(lambda s: set(s) != expected_seeds)
        if bad_coverage.any():
            raise ValueError(f"{dataset}: expected seeds 0..19 for every policy/episode")
        n_ep = len(episode_ids)
        # Average stochastic policy seeds within an episode before resampling.
        g = g.copy()
        g.loc[g.detect_delay < 0, "detect_delay"] = np.nan
        ep = g.groupby(["ep", "policy"], sort=True)[
            ["net", "labels", "ever_promote", "detect_delay"]
        ].mean().unstack("policy")
        result: dict[str, object] = {"episodes": n_ep, "seeds_per_episode": 20, "candidates": {}}
        for candidate in CANDIDATES:
            cand = ep["net"][candidate].to_numpy()
            contrasts: dict[str, object] = {}
            for comparator in PUBLISHED_CERTIFICATE_PORTS + SUPPLEMENTAL + INTERNAL_REFERENCES:
                delta = cand - ep["net"][comparator].to_numpy()
                contrasts[comparator] = {
                    "candidate_minus_comparator_mean_net": float(delta.mean()),
                    "episode_bootstrap_95ci": _bootstrap_mean_ci(delta, n_boot, rng),
                }
            row: dict[str, object] = {
                "mean_net": float(cand.mean()),
                "mean_labels": float(ep["labels"][candidate].mean()),
                "mean_promotion_rate": float(ep["ever_promote"][candidate].mean()),
                "mean_detection_delay_promoted_only": float(
                    ep["detect_delay"][candidate].replace(-1, np.nan).mean()
                ),
                "contrasts": contrasts,
            }
            point = {c: float(ep["net"][c].mean()) for c in PUBLISHED_CERTIFICATE_PORTS}
            row["lowest_mean_cost_certificate_port_descriptive"] = min(point, key=point.get)
            row["certificate_port_mean_costs"] = point
            result["candidates"][candidate] = row
        out[dataset] = result

    # Equal-dataset estimands; resample episodes inside each fixed dataset.
    equal_dataset: dict[str, object] = {}
    for candidate in CANDIDATES:
        entry: dict[str, object] = {}
        for comparator in PUBLISHED_CERTIFICATE_PORTS + SUPPLEMENTAL + INTERNAL_REFERENCES:
            arrays = []
            for dataset in DATASETS:
                g = d[d.regime == dataset]
                ep_delta = g.pivot_table(index="ep", columns="policy", values="net", aggfunc="mean")
                arrays.append((ep_delta[candidate] - ep_delta[comparator]).to_numpy())
            point = float(np.mean([a.mean() for a in arrays]))
            boots = np.zeros(n_boot)
            for a in arrays:
                ix = rng.integers(0, len(a), size=(n_boot, len(a)))
                boots += a[ix].mean(axis=1) / len(arrays)
            entry[comparator] = {
                "equal_dataset_mean_candidate_minus_comparator": point,
                "within_dataset_episode_bootstrap_95ci": [float(v) for v in np.quantile(boots, [0.025, 0.975])],
            }
        equal_dataset[candidate] = entry

    return {
        "status": "POST_DEVELOPMENT_DESCRIPTIVE_REPLAY_ON_REUSED_FRESH_STREAMS",
        "source_records": str(records),
        "seed_base": 2026110701,
        "datasets": DATASETS,
        "candidate_policies": CANDIDATES,
        "published_certificate_ports": PUBLISHED_CERTIFICATE_PORTS,
        "supplemental_non_published_certificate_comparators": SUPPLEMENTAL,
        "internal_references": INTERNAL_REFERENCES,
        "replicates": 20,
        "uncertainty_unit": "episode, after averaging paired policy seeds within episode",
        "overall_estimand": "equal mean over the five fixed datasets; bootstrap resamples episodes within each dataset",
        "limits": [
            "All streams were already exposed to development; this is not independent confirmation.",
            "Intervals quantify episode resampling within these fixed datasets, not generalization across datasets.",
        "Episode bootstrap intervals treat episodes within each dataset as exchangeable; temporal dependence can make these intervals optimistic.",
            "The lowest-cost certificate port is selected on these same data and is descriptive only; fixed-port contrasts are reported separately.",
            "Ports implement a common contract and are not author-native reproductions; Xu and Choe-Ramdas are supplementary adapters, excluded from the published certificate pool.",
        ],
        "by_dataset": out,
        "equal_dataset_contrasts": equal_dataset,
        "bootstrap_replicates": n_boot,
        "bootstrap_seed": seed,
    }


def to_markdown(result: dict) -> str:
    lines = [
        "# Family H corrected fresh-real comparator screen",
        "",
        "Post-development matched replay on five reused fresh-real streams, 20 paired seeds per episode.",
        "The six published certificate ports are the primary fixed comparator set. Xu acquisition and the Choe–Ramdas adapter are shown separately.",
        "",
        "All estimates are descriptive for these exposed streams. Episode bootstrap intervals average seeds within episode, treat episodes within dataset as exchangeable, and do not generalize across datasets.",
        "",
        "## Equal-dataset paired cost differences",
        "",
        "Candidate minus comparator net cost; negative favors the candidate. The selected lowest-cost port is not used as an inferential comparator.",
        "",
        "| candidate | comparator | equal-dataset ΔJ | episode-bootstrap 95% CI |",
        "|---|---|---:|---:|",
    ]
    for candidate, comps in result["equal_dataset_contrasts"].items():
        for comparator, item in comps.items():
            lo, hi = item["within_dataset_episode_bootstrap_95ci"]
            lines.append(
                f"| {candidate} | {comparator} | {item['equal_dataset_mean_candidate_minus_comparator']:+.2f} | [{lo:+.2f}, {hi:+.2f}] |"
            )
    lines += ["", "## Per-dataset descriptive winner among tested certificate ports", "", "| dataset | candidate | lowest-mean-cost port | candidate mean J |", "|---|---|---|---:|"]
    for dataset, ds in result["by_dataset"].items():
        for candidate, c in ds["candidates"].items():
            lines.append(
                f"| {dataset} | {candidate} | {c['lowest_mean_cost_certificate_port_descriptive']} | {c['mean_net']:.2f} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", type=Path)
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    ap.add_argument("--bootstrap", type=int, default=20_000)
    ap.add_argument("--seed", type=int, default=2026110417)
    a = ap.parse_args()
    result = analyze(a.records, n_boot=a.bootstrap, seed=a.seed)
    a.json.parent.mkdir(parents=True, exist_ok=True)
    a.json.write_text(json.dumps(result, indent=2) + "\n")
    a.markdown.parent.mkdir(parents=True, exist_ok=True)
    a.markdown.write_text(to_markdown(result))
    print(json.dumps({"status": result["status"], "datasets": len(result["by_dataset"]), "candidates": CANDIDATES,
                      "ports": PUBLISHED_CERTIFICATE_PORTS, "replicates": result["replicates"]}, indent=2))


if __name__ == "__main__":
    main()
