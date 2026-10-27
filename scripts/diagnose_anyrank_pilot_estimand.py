"""Post-hoc oracle-only diagnosis of AnyRank pilot selection failures.

This regenerates the six registered feature streams and candidate actions, but
does not pass evaluator probabilities or future outcomes to any selector. It
reports only aggregate mean-utility and reward-distribution support diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from compare_target_scout_fixed_split import _make_config, _stream_for_seed
from reproduce_anyrank_shiftguard import CELLS, SCENARIO
from scipy.stats import norm

from shiftlab.data.gpu.environment import environment, resolve_device

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "outputs/shiftguard_unified/sota_reproductions/anyrank_shiftguard_pilot_v1"
OUTPUT_DEFAULT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/anyrank_pilot_oracle_diagnostic_v2"
)
SEED_OFFSET = 20_310_000
SEEDS_PER_CELL = 3
REWARD_THRESHOLDS = np.linspace(0.0, 1.0, 11)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reward_distribution(
    *,
    action: np.ndarray,
    probability: np.ndarray,
    is_incumbent: bool,
    fn_cost: float,
    fp_cost: float,
    switch_rate: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Exact finite-design reward distribution integrating over binary Y|X."""
    switch = 0.0 if is_incumbent else switch_rate
    maximum = max(fn_cost, fp_cost) + switch_rate
    loss_y0 = np.where(action == 1, fp_cost, 0.0) + switch
    loss_y1 = np.where(action == 0, fn_cost, 0.0) + switch
    rewards = np.concatenate((1.0 - loss_y0 / maximum, 1.0 - loss_y1 / maximum))
    masses = np.concatenate((1.0 - probability, probability)) / len(action)
    support = np.unique(rewards)
    probabilities = np.asarray(
        [masses[np.isclose(rewards, value, rtol=0.0, atol=1e-12)].sum() for value in support]
    )
    if not np.isclose(probabilities.sum(), 1.0, atol=1e-12):
        raise RuntimeError("reward distribution does not sum to one")
    return support, probabilities


def _survival(support: np.ndarray, mass: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    return np.asarray([mass[support >= threshold - 1e-12].sum() for threshold in thresholds])


def _diagnose_seed(
    *, seed: int, cell_index: int, prevalence: float, signal: float, error: float, device: str
) -> list[dict[str, Any]]:
    config = _make_config(
        n=3200,
        d=16,
        seed=seed,
        prevalence=prevalence,
        signal=signal,
        error=error,
        device=device,
    )
    family, _, _, x = _stream_for_seed(
        seed=seed,
        config=config,
        device=device,
        scenario=SCENARIO,
    )
    threshold = float(norm.ppf(1.0 - prevalence))
    latent_context = np.asarray(x[:, 0] >= threshold, dtype=bool)
    target_probability = np.where(latent_context, 1.0 / 6.0 + signal, 1.0 / 6.0 - signal)
    monitor_end = int(family["monitor_end"])
    contexts = np.asarray(family["contexts"], dtype=int)
    actions = np.asarray(family["actions"], dtype=int)
    incumbent = np.asarray(family["incumbent"], dtype=int)
    names = [str(value) for value in family["candidate_ids"]]
    alias_rows = {i for i, name in enumerate(names) if name == "incumbent_snapshot"}
    candidate_rows = [i for i in range(len(names)) if i not in alias_rows]
    switch_rate = 0.05 / int(family["deployment_length"])
    holdout_indices = np.arange(monitor_end, config.n)
    rows: list[dict[str, Any]] = []

    for group in (0, 1):
        use = contexts[holdout_indices] == group
        indices = holdout_indices[use]
        if not len(indices):
            raise RuntimeError(f"empty evaluator holdout context {group}")
        p = target_probability[indices]
        reference_action = incumbent[indices]
        reference_support, reference_mass = _reward_distribution(
            action=reference_action,
            probability=p,
            is_incumbent=True,
            fn_cost=float(SCENARIO.fn_cost),
            fp_cost=float(SCENARIO.fp_cost),
            switch_rate=switch_rate,
        )
        reference_survival = _survival(reference_support, reference_mass, REWARD_THRESHOLDS)
        candidate_results: list[tuple[int, float, bool]] = []
        for candidate in candidate_rows:
            action = actions[candidate, indices]
            support, mass = _reward_distribution(
                action=action,
                probability=p,
                is_incumbent=False,
                fn_cost=float(SCENARIO.fn_cost),
                fp_cost=float(SCENARIO.fp_cost),
                switch_rate=switch_rate,
            )
            candidate_survival = _survival(support, mass, REWARD_THRESHOLDS)
            dominates = bool(
                np.all(candidate_survival >= reference_survival - 1e-12)
                and np.any(candidate_survival > reference_survival + 1e-12)
            )
            gain = float(np.sum(family["h_truth"][candidate, indices] - switch_rate))
            # Independently recompute the expected net gain from action costs.
            expected_reference = np.where(reference_action == 1, (1.0 - p) * 1.0, p * 5.0)
            expected_candidate = np.where(action == 1, (1.0 - p) * 1.0, p * 5.0)
            direct_gain = float(np.sum(expected_reference - expected_candidate - switch_rate))
            if not np.isclose(gain, direct_gain, rtol=1e-10, atol=1e-8):
                raise RuntimeError(
                    "stored oracle contrast disagrees with direct expected-cost calculation"
                )
            candidate_results.append((candidate, gain, dominates))

        positive = [
            (i, gain, dominates) for i, gain, dominates in candidate_results if gain > 1e-10
        ]
        dominating = [(i, gain, dominates) for i, gain, dominates in candidate_results if dominates]
        best = max(candidate_results, key=lambda item: item[1])
        best_positive = max(positive, key=lambda item: item[1]) if positive else None
        rows.append(
            {
                "seed": seed,
                "cell": cell_index,
                "prevalence": prevalence,
                "signal": signal,
                "proxy_error": error,
                "context": group,
                "holdout_events": len(indices),
                "best_candidate_id": names[best[0]],
                "best_candidate_expected_net_gain": best[1],
                "positive_net_gain_candidates": len(positive),
                "positive_net_gain_and_fosd_candidates": sum(item[2] for item in positive),
                "fosd_dominating_candidates": len(dominating),
                "best_positive_candidate_id": None
                if best_positive is None
                else names[best_positive[0]],
                "best_positive_candidate_expected_net_gain": None
                if best_positive is None
                else best_positive[1],
                "best_positive_candidate_fosd": None if best_positive is None else best_positive[2],
                "diagnostic_scope": "evaluator_oracle_only_common_holdout",
            }
        )
    return rows


def run(*, device: str, output: Path) -> dict[str, Any]:
    pilot_manifest = json.loads((PILOT / "manifest.json").read_text(encoding="utf-8"))
    if pilot_manifest["configuration"]["seed_offset"] != SEED_OFFSET:
        raise RuntimeError("pilot seed block changed")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output: {output}")
    resolved = resolve_device(device, n=3200, d=16, chunk_size=2048)
    if resolved != "cuda":
        raise RuntimeError("registered generator requires CUDA")
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for cell_index, (prevalence, signal, error) in enumerate(CELLS):
        for offset in range(SEEDS_PER_CELL):
            seed = SEED_OFFSET + cell_index * SEEDS_PER_CELL + offset
            rows.extend(
                _diagnose_seed(
                    seed=seed,
                    cell_index=cell_index,
                    prevalence=prevalence,
                    signal=signal,
                    error=error,
                    device=resolved,
                )
            )
    detail = pd.DataFrame(rows)
    expected_rows = SEEDS_PER_CELL * len(CELLS) * 2
    if len(detail) != expected_rows or detail.duplicated(["seed", "context"]).any():
        raise RuntimeError("oracle diagnostic rows are incomplete or duplicated")
    summary = detail.groupby(["cell", "signal", "context"], as_index=False).agg(
        streams=("seed", "count"),
        mean_best_net_gain=("best_candidate_expected_net_gain", "mean"),
        streams_with_positive_candidate_fraction=(
            "positive_net_gain_candidates",
            lambda values: float((values > 0).mean()),
        ),
        mean_positive_candidate_count=("positive_net_gain_candidates", "mean"),
        mean_positive_and_fosd_count=("positive_net_gain_and_fosd_candidates", "mean"),
        mean_fosd_dominating_count=("fosd_dominating_candidates", "mean"),
        best_positive_fosd_rate=(
            "best_positive_candidate_fosd",
            lambda values: (
                float(values.dropna().astype(bool).mean()) if values.notna().any() else None
            ),
        ),
    )
    detail.to_csv(output / "oracle_streams.csv", index=False)
    detail.to_parquet(output / "oracle_streams.parquet", index=False)
    summary.to_csv(output / "oracle_summary.csv", index=False)
    summary.to_parquet(output / "oracle_summary.parquet", index=False)
    report = [
        "# AnyRank pilot: evaluator-oracle estimand diagnostic",
        "",
        "This post-hoc diagnostic regenerates the registered six pilot streams and evaluates the frozen candidates on the common post-monitor holdout using generator-known outcome probabilities. These evaluator quantities were not passed to the AnyRank selector. It asks whether positive mean net-gain candidates existed and whether they also strictly first-order stochastically dominated the incumbent's bounded reward distribution on the 11 threshold grid.",
        "",
        "The oracle cost calculations were independently recomputed from the candidate actions, conditional label probabilities, and declared 5:1 false-negative/false-positive costs; every value matched the stored expected paired-cost contrast within numerical tolerance. Results are aggregate diagnostics over six synthetic streams, not efficacy evidence or a new calibration run.",
        "",
        summary.to_markdown(index=False),
        "",
        "The table diagnoses comparator/estimand alignment only. The finite-design reward distributions are evaluator calculations and must not be used in any learner decision. The pilot remains underpowered and no promotion-rate inference is justified.",
    ]
    (output / "results.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    source_files = [
        ROOT / "scripts/diagnose_anyrank_pilot_estimand.py",
        ROOT / "scripts/compare_target_scout_fixed_split.py",
        ROOT / "scripts/reproduce_anyrank_shiftguard.py",
        ROOT / "src/shiftlab/dive/budgeted_promotion.py",
    ]
    files = [
        "oracle_streams.csv",
        "oracle_streams.parquet",
        "oracle_summary.csv",
        "oracle_summary.parquet",
        "results.md",
    ]
    manifest = {
        "experiment": "anyrank_pilot_evaluator_oracle_estimand_diagnostic",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "posthoc_oracle_only_diagnostic_not_learner_input",
        "pilot_manifest_sha256": _sha256(PILOT / "manifest.json"),
        "pilot_seed_block": [SEED_OFFSET, SEED_OFFSET + SEEDS_PER_CELL * len(CELLS) - 1],
        "cells": CELLS,
        "contexts": [0, 1],
        "reward_thresholds": REWARD_THRESHOLDS.tolist(),
        "device": resolved,
        "gpu": environment().get("gpu_name"),
        "source_hashes": {
            str(p.relative_to(ROOT)).replace("\\", "/"): _sha256(p) for p in source_files
        },
        "files": files,
        "file_sha256": {name: _sha256(output / name) for name in files},
        "limitations": [
            "six streams only; descriptive diagnosis",
            "finite-design conditional reward distributions are evaluator-only, not population-level proof of stochastic dominance",
            "the 11-threshold grid is the AnyRank implementation's bounded support grid",
            "does not calibrate the sequential procedure or establish efficacy",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    run(device=args.device, output=args.output)


if __name__ == "__main__":
    main()
