"""Small matched AnyRank development comparison for ShiftGuard Q2."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_target_scout_fixed_split import (  # noqa: E402 -- local script path bootstrap
    ALPHA,
    BUDGET_RATE,
    _make_config,
    _stream_for_seed,
)

from shiftlab.data.gpu.environment import environment, resolve_device  # noqa: E402 -- local script path bootstrap
from shiftlab.dive.budgeted_promotion import (  # noqa: E402 -- local script path bootstrap
    _budget_limited_prefix_length,
    _monitor_family,
    _monitor_scout_context_policy,
    _monitor_validation_context_policy,
)

PROTOCOL = ROOT / "papers/shiftguard_unified/anyrank_adaptation_protocol_v2.md"
ANYRANK_ROOT = ROOT / "tmp/AnyRank-source-audit"
OUTPUT_DEFAULT = ROOT / "outputs/shiftguard_unified/sota_reproductions/anyrank_shiftguard_pilot_v2"
SCENARIO = SimpleNamespace(
    name="candidate_context_heterogeneity",
    fn_cost=5.0,
    fp_cost=1.0,
    harmful_adaptation=False,
)
CELLS = ((0.50, 0.00, 0.10), (0.50, 0.10, 0.10))
CONTEXT_ALPHA = ALPHA / 2


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binary_decision_cost(actions: np.ndarray, outcomes: np.ndarray) -> np.ndarray:
    """Use the repository's action=1 positive-prediction cost convention."""
    actions = np.asarray(actions, dtype=int)
    outcomes = np.asarray(outcomes, dtype=int)
    return np.where(
        actions == outcomes,
        0.0,
        np.where(actions == 1, float(SCENARIO.fp_cost), float(SCENARIO.fn_cost)),
    )


def _common_future_gain(
    *,
    selected: dict[int, int | None],
    family: dict[str, Any],
    y: np.ndarray,
    start: int,
    switching_cost: float,
) -> tuple[float, float, bool]:
    """Score selected context policies on the common evaluator-only future slice."""
    contexts = np.asarray(family["contexts"][start:], dtype=int)
    indices = np.arange(start, len(y))
    net_expected = 0.0
    net_realized = 0.0
    changed = False
    switch_rate = switching_cost / max(1, len(indices))
    for group, candidate in selected.items():
        if candidate is None:
            continue
        use = contexts == group
        group_indices = indices[use]
        if candidate < 0:
            # -1 is the incumbent itself, whose gain and switch cost are zero.
            continue
        changed = True
        net_expected += float(np.sum(family["h_truth"][candidate, group_indices] - switch_rate))
        observed_gain = np.where(
            y[group_indices] == 1,
            family["z1"][candidate, group_indices],
            family["z0"][candidate, group_indices],
        )
        net_realized += float(np.sum(observed_gain - switch_rate))
    return net_expected, net_realized, changed


def _rank_context(
    *,
    rewards: np.ndarray,
    policy_names: list[str],
    alpha: float,
) -> dict[str, Any]:
    """Run the pinned authors' tie-aware candidate-versus-reference tests."""
    from multitest.sequential_graphical import SequentialGraphicalTest

    n_policies = rewards.shape[1]
    # The prespecified adaptation tests each challenger against incumbent col 0.
    hypotheses = [(0, index) for index in range(1, n_policies)]
    n_hypotheses = len(hypotheses)
    if n_hypotheses < 1:
        return {"winner": None, "ranked_pairs": 0, "times": {}, "hypothesis_count": 0}
    alpha_per_hypothesis = np.full(n_hypotheses, alpha / n_hypotheses)
    graph = np.full((n_hypotheses, n_hypotheses), 1.0 / (n_hypotheses - 1))
    np.fill_diagonal(graph, 0.0)
    runner = SequentialGraphicalTest(
        n_policies,
        [(0.5, 0.5)] * n_hypotheses,
        total_alpha=alpha,
        inference_mode="ranking",
    )
    with contextlib.redirect_stdout(io.StringIO()):
        result = runner.sequential_graphical_multitest(
            hypotheses,
            rewards,
            Nmax=len(rewards),
            alpha_per_hypothesis=alpha_per_hypothesis,
            weighted_G=graph,
            allow_transitive=False,
        )
    rejected_hypotheses, _, decision_times, _, _, _, _, directions = result
    certified_challengers = [
        hypothesis[1]
        for hypothesis in hypotheses
        if hypothesis in rejected_hypotheses and int(directions.get(hypothesis, 0)) == 1
    ]
    # Simultaneous tests establish that every eligible challenger improves on
    # the incumbent. The empirical-mean tie-break chooses among that set; it
    # does not certify a global best policy.
    winner = (
        max(certified_challengers, key=lambda index: float(rewards[:, index].mean()))
        if certified_challengers
        else None
    )
    return {
        "winner": winner,
        "ranked_pairs": len(rejected_hypotheses),
        "hypothesis_count": n_hypotheses,
        "decision_times": {
            f"{left}:{right}": (None if value == "N/A" else int(value))
            for (left, right), value in decision_times.items()
        },
        "policy_names": policy_names,
    }


def _anyrank_select(
    *,
    family: dict[str, Any],
    y: np.ndarray,
    query_uniforms: np.ndarray,
    prevalence: float,
    signal: float,
    error: float,
) -> dict[str, Any]:
    start, end = int(family["validation_end"]), int(family["monitor_end"])
    monitor_length = int(family["monitor_length"])
    budget = int(np.floor(BUDGET_RATE * monitor_length))
    q_path = np.asarray(family["q_paths"][("uniform", BUDGET_RATE)], dtype=float)
    query_flags = np.asarray(query_uniforms[:monitor_length] < q_path, dtype=bool)
    processed = _budget_limited_prefix_length(query_flags, budget)
    relative_indices = np.flatnonzero(query_flags[:processed])
    event_indices = start + relative_indices

    # Rebuild the bank with one explicit incumbent reference and all alternative
    # candidate models. The candidate bank contains an incumbent_snapshot row;
    # omit that alias to avoid a structurally duplicated policy in AnyRank's rank.
    candidate_actions = np.asarray(family["actions"], dtype=int)
    candidate_names = [str(name) for name in family["candidate_ids"]]
    alias_rows = {i for i, name in enumerate(candidate_names) if name == "incumbent_snapshot"}
    source_candidates = [i for i in range(len(candidate_names)) if i not in alias_rows]
    actions = np.vstack(
        [np.asarray(family["incumbent"], dtype=int), candidate_actions[source_candidates]]
    )
    actions = actions[:, event_indices]
    policy_names = ["incumbent_reference"] + [candidate_names[i] for i in source_candidates]
    policy_to_candidate: list[int | None] = [None] + source_candidates
    contexts = np.asarray(family["contexts"][event_indices], dtype=int)
    outcomes = np.asarray(y[event_indices], dtype=int)
    switch_rate = 0.05 / max(1, int(family["deployment_length"]))
    decision_cost = _binary_decision_cost(actions, outcomes[None, :])
    switched = np.arange(len(policy_names)) != 0
    decision_cost += switch_rate * switched[:, None]
    max_event_cost = max(float(SCENARIO.fn_cost), float(SCENARIO.fp_cost)) + switch_rate
    reward_rows = 1.0 - decision_cost / max_event_cost
    if (
        not np.isfinite(reward_rows).all()
        or reward_rows.min(initial=0.0) < -1e-12
        or reward_rows.max(initial=0.0) > 1.0 + 1e-12
    ):
        raise RuntimeError("AnyRank reward input escaped its documented [0, 1] range")

    selected: dict[int, int | None] = {}
    winner_indices: dict[int, int | None] = {}
    group_results: dict[str, Any] = {}
    for group in (0, 1):
        use = contexts == group
        group_data = reward_rows[:, use].T
        ranking = _rank_context(
            rewards=group_data,
            policy_names=policy_names,
            alpha=CONTEXT_ALPHA,
        )
        winner = ranking["winner"]
        winner_indices[group] = winner
        selected[group] = None if winner is None else policy_to_candidate[winner]
        group_results[str(group)] = {
            "queried_events": int(use.sum()),
            "winner_index": winner,
            "winner_name": None if winner is None else policy_names[winner],
            "certified_pairwise_relations": int(ranking["ranked_pairs"]),
            "pairwise_hypothesis_count": int(ranking["hypothesis_count"]),
            "decision_times": ranking["decision_times"],
        }

    future_start = end
    expected_gain, realized_gain, any_candidate = _common_future_gain(
        selected=selected,
        family=family,
        y=y,
        start=future_start,
        switching_cost=0.05,
    )
    selected_ids = {
        str(group): (
            None
            if winner_indices[group] is None
            else "incumbent_reference"
            if winner_indices[group] == 0
            else candidate_names[selected[group]]
        )
        for group in selected
    }
    return {
        "method": "anyrank_full_information_contextual",
        "selected_candidates_by_context": json.dumps(selected_ids, sort_keys=True),
        "promoted": any_candidate,
        "harmful_postpromotion_promotion": bool(any_candidate and expected_gain <= 0.0),
        "expected_postpromotion_net_gain_common_holdout": expected_gain,
        "realized_postpromotion_net_gain_common_holdout": realized_gain,
        "labels_queried": int(query_flags[:processed].sum()),
        "label_budget": budget,
        "monitor_events_processed": processed,
        "pairwise_hypotheses_total": sum(
            int(item["pairwise_hypothesis_count"]) for item in group_results.values()
        ),
        "pairwise_relations_certified_total": sum(
            int(item["certified_pairwise_relations"]) for item in group_results.values()
        ),
        "contexts": json.dumps(group_results, sort_keys=True),
        "context_target_prevalence": prevalence,
        "context_signal_strength": signal,
        "context_proxy_error": error,
    }


def _select_baseline_ids(result: dict[str, Any]) -> dict[int, int | None]:
    if not bool(result.get("promoted")):
        return {0: None, 1: None}
    raw = result.get("selected_candidates_by_context")
    if raw is None:
        # The pooled monitor returns one scalar candidate ID.
        candidate_id = result.get("candidate_id")
        return {0: candidate_id, 1: candidate_id}
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    return {int(group): candidate for group, candidate in parsed.items()}


def _score_baseline_common_holdout(
    *,
    result: dict[str, Any],
    family: dict[str, Any],
    y: np.ndarray,
    start: int,
) -> tuple[float, float, bool]:
    selected_ids = _select_baseline_ids(result)
    id_to_candidate = {str(name): i for i, name in enumerate(family["candidate_ids"])}
    selected: dict[int, int | None] = {}
    for group, candidate_id in selected_ids.items():
        selected[group] = None if candidate_id is None else id_to_candidate.get(str(candidate_id))
        if candidate_id is not None and selected[group] is None:
            raise ValueError(f"baseline selected unknown candidate {candidate_id!r}")
    return _common_future_gain(
        selected=selected,
        family=family,
        y=y,
        start=start,
        switching_cost=0.05,
    )


def run(*, seeds_per_cell: int, seed_offset: int, device: str, output: Path) -> dict[str, Any]:
    if seeds_per_cell != 3 or seed_offset != 20_310_000:
        raise ValueError(
            "the v2 corrective replay is frozen at three seeds per cell and seed offset 20310000"
        )
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    if not ANYRANK_ROOT.is_dir():
        raise FileNotFoundError(f"pinned official AnyRank source is missing: {ANYRANK_ROOT}")
    cost_probe = _binary_decision_cost(np.asarray([1, 0]), np.asarray([0, 1]))
    if not np.array_equal(cost_probe, np.asarray([SCENARIO.fp_cost, SCENARIO.fn_cost])):
        raise RuntimeError(
            "false-positive/false-negative mapping disagrees with canonical cost contract"
        )
    resolved = resolve_device(device, n=3200, d=16, chunk_size=2048)
    if resolved != "cuda":
        raise RuntimeError(f"the frozen data-generation protocol requires CUDA, got {resolved}")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output directory: {output}")

    rows: list[dict[str, Any]] = []
    for cell_index, (prevalence, signal, error) in enumerate(CELLS):
        for offset in range(seeds_per_cell):
            seed = seed_offset + cell_index * seeds_per_cell + offset
            print(
                f"cell={cell_index + 1}/{len(CELLS)} seed={seed} "
                f"prevalence={prevalence} signal={signal} error={error}",
                flush=True,
            )
            config = _make_config(
                n=3200,
                d=16,
                seed=seed,
                prevalence=prevalence,
                signal=signal,
                error=error,
                device=resolved,
            )
            family, y, query_uniforms, _ = _stream_for_seed(
                seed=seed,
                config=config,
                device=resolved,
                scenario=SCENARIO,
            )
            methods = [
                (
                    "pooled_fixed_mixture",
                    _monitor_family(
                        family=family,
                        y=y,
                        scenario=SCENARIO,
                        config=config,
                        query_name="uniform",
                        budget_rate=BUDGET_RATE,
                        estimator="direct_ipw",
                        query_uniforms=query_uniforms,
                        bound_mode="global",
                        monitoring_rule="fixed_mixture",
                    )[0],
                ),
                (
                    "source_validation_fixed_split",
                    _monitor_validation_context_policy(
                        family=family,
                        y=y,
                        scenario=SCENARIO,
                        config=replace(config, include_validation_context_policy=True).validate(),
                        query_name="uniform",
                        budget_rate=BUDGET_RATE,
                        query_uniforms=query_uniforms,
                    ),
                ),
                (
                    "target_scout",
                    _monitor_scout_context_policy(
                        family=family,
                        y=y,
                        scenario=SCENARIO,
                        config=replace(config, include_scout_context_policy=True).validate(),
                        query_name="uniform",
                        budget_rate=BUDGET_RATE,
                        query_uniforms=query_uniforms,
                    ),
                ),
            ]
            anyrank = _anyrank_select(
                family=family,
                y=y,
                query_uniforms=query_uniforms,
                prevalence=prevalence,
                signal=signal,
                error=error,
            )
            methods.append(("anyrank_full_information_contextual", anyrank))
            for method_name, result in methods:
                expected, realized, promoted = (
                    _score_baseline_common_holdout(
                        result=result,
                        family=family,
                        y=y,
                        start=int(family["monitor_end"]),
                    )
                    if method_name != "anyrank_full_information_contextual"
                    else (
                        float(anyrank["expected_postpromotion_net_gain_common_holdout"]),
                        float(anyrank["realized_postpromotion_net_gain_common_holdout"]),
                        bool(anyrank["promoted"]),
                    )
                )
                rows.append(
                    {
                        "seed": seed,
                        "cell": cell_index,
                        "prevalence": prevalence,
                        "signal": signal,
                        "proxy_error": error,
                        "method": method_name,
                        "promoted": promoted,
                        "harmful_postpromotion_promotion": bool(promoted and expected <= 0.0),
                        "expected_postpromotion_net_gain_common_holdout": expected,
                        "realized_postpromotion_net_gain_common_holdout": realized,
                        "labels_queried": int(result["labels_queried"]),
                        "label_budget": int(result["label_budget"]),
                        "selected_candidates_by_context": result.get(
                            "selected_candidates_by_context", result.get("candidate_id")
                        ),
                        "anyrank_pairwise_hypotheses_total": result.get(
                            "pairwise_hypotheses_total"
                        ),
                        "anyrank_pairwise_relations_certified_total": result.get(
                            "pairwise_relations_certified_total"
                        ),
                        "anyrank_context_diagnostics": result.get("contexts"),
                    }
                )
            temporary = output / "streams.partial.csv"
            pd.DataFrame(rows).to_csv(temporary, index=False)

    detail = pd.DataFrame(rows)
    expected_rows = seeds_per_cell * len(CELLS) * 4
    if len(detail) != expected_rows or detail.duplicated(["seed", "method"]).any():
        raise RuntimeError("pilot output is incomplete or duplicated")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("a method exceeded its registered label ceiling")
    if not detail["label_budget"].eq(detail["label_budget"].iloc[0]).all():
        raise RuntimeError("methods did not share a common label-budget ceiling")
    summary = detail.groupby(["cell", "signal", "method"], as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        expected_common_holdout_gain=("expected_postpromotion_net_gain_common_holdout", "mean"),
        realized_common_holdout_gain=("realized_postpromotion_net_gain_common_holdout", "mean"),
        mean_labels=("labels_queried", "mean"),
    )
    detail.to_csv(output / "streams.csv", index=False)
    detail.to_parquet(output / "streams.parquet", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    summary.to_parquet(output / "summary.parquet", index=False)
    summary.to_markdown(output / "results.md", index=False)
    (output / "streams.partial.csv").unlink(missing_ok=True)
    execution_snapshot = output / "reproduce_anyrank_shiftguard_at_execution.py"
    execution_snapshot.write_bytes(Path(__file__).read_bytes())

    anyrank_files = [
        ANYRANK_ROOT / "src/multitest/sequential_graphical.py",
        ANYRANK_ROOT / "src/multitest/inference_modes.py",
        ANYRANK_ROOT / "src/multitest/alpha_adaptive_nsm.py",
    ]
    dependency_versions = {}
    for package in (
        "nscore",
        "statistical-comparison-core",
        "sequentialized-barnard-tests",
        "numpy",
        "torch",
    ):
        try:
            dependency_versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependency_versions[package] = "unavailable"
    anyrank_commit = subprocess.run(
        ["git", "-C", str(ANYRANK_ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest = {
        "experiment": "anyrank_corrected_reference_comparison_shiftguard_replay",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "corrective_exploratory_matched_replay_not_confirmation",
        "protocol": {
            "path": PROTOCOL.relative_to(ROOT).as_posix(),
            "sha256": _sha256(PROTOCOL),
        },
        "configuration": {
            "seeds_per_cell": seeds_per_cell,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds_per_cell * len(CELLS) - 1,
            "cells": CELLS,
            "n": 3200,
            "d": 16,
            "device_requested": device,
            "device_resolved": resolved,
            "budget_rate": BUDGET_RATE,
            "hard_label_cap": True,
            "anyrank_inference_mode": "ranking",
            "anyrank_allow_transitive": False,
            "familywise_alpha": ALPHA,
            "alpha_per_context": CONTEXT_ALPHA,
            "paired_common_streams_and_common_holdout": True,
            "noncommercial_academic_use": True,
            "cost_contract": "action=1/outcome=0 is FP cost 1; action=0/outcome=1 is FN cost 5; corrected to match _binary_costs",
            "seed_reuse": "same six seed IDs as invalid v1 implementation replay; corrective development replay, not independent confirmation",
        },
        "anyrank_source": {
            "repository": "https://github.com/irom-princeton/AnyRank",
            "commit": anyrank_commit,
            "files": {p.relative_to(ANYRANK_ROOT).as_posix(): _sha256(p) for p in anyrank_files},
            "license": "MIT; dependencies statistical-comparison-core and sequentialized-barnard-tests are CC BY-NC 4.0",
        },
        "source_hashes": {
            "runner": _sha256(Path(__file__).resolve()),
            "runner_sha256_at_execution": _sha256(execution_snapshot),
            "runner_sha256_current": _sha256(Path(__file__).resolve()),
            "verifier_sha256_current": _sha256(ROOT / "scripts/verify_anyrank_shiftguard_pilot.py"),
            "baseline_runner": _sha256(ROOT / "scripts/compare_target_scout_fixed_split.py"),
            "budgeted_promotion": _sha256(ROOT / "src/shiftlab/dive/budgeted_promotion.py"),
        },
        "dependencies": dependency_versions,
        "environment": environment(),
        "files": [
            "streams.csv",
            "streams.parquet",
            "summary.csv",
            "summary.parquet",
            "results.md",
            execution_snapshot.name,
        ],
        "file_sha256": {
            name: _sha256(output / name)
            for name in (
                "streams.csv",
                "streams.parquet",
                "summary.csv",
                "summary.parquet",
                "results.md",
                execution_snapshot.name,
            )
        },
        "limitations": [
            "three streams per cell; corrected replay on seed IDs previously used by an invalid cost-mapping implementation",
            "star-shaped AnyRank adaptation tests bounded reward-distribution superiority over the incumbent, stronger than mean-cost improvement; it does not certify the globally best challenger",
            "shared labels score every frozen policy; original AnyRank active per-policy label-allocation savings are not evaluated",
            "IID synthetic data and independent uniform label queries only",
            "synthetic costs are imposed utility, not observed revenue",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))
    safe_output = str(output).encode("ascii", errors="backslashreplace").decode("ascii")
    print(f"output={safe_output}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-cell", type=int, default=3)
    parser.add_argument("--seed-offset", type=int, default=20_310_000)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    run(
        seeds_per_cell=args.seeds_per_cell,
        seed_offset=args.seed_offset,
        device=args.device,
        output=args.output,
    )


if __name__ == "__main__":
    main()
