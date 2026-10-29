"""Run only the frozen WP2 G1 learner-slice screen; never simulate a monitor."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from shiftlab.data.gpu.environment import environment
from shiftlab.dive.adg_growth_prescreen import PrescreenConfig, learner_slice
from shiftlab.dive.stratified_growth_prescreen import (
    REGISTERED_BUDGETS,
    REGISTERED_K,
    evaluate_slice,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/stratified_harm_monitor_development_protocol.md"
OUT = ROOT / "outputs/stratified_growth_prescreen_20"
MATCHED = (
    "chugg_subgroup_composition",
    "stratified_common_bound",
    "stratified_proportional_query",
    "pooled_same_query_global_bound",
    "pooled_uniform_correct_bound_U1",
    "gated_pooled_HT_G1f",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return "-Infinity" if value < 0 else "Infinity" if value > 0 else None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(json_safe(value), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def decide(summary: pd.DataFrame) -> dict:
    trials = []
    for (budget, K, allocation), block in summary.groupby(["budget_rate", "K", "allocation"]):
        local = block[block.working_law.eq("localized_harm")].set_index("arm")
        homogeneous = block[block.working_law.eq("homogeneous_harm")].set_index("arm")
        candidate = local.loc["stratified_candidate"]
        incumbent = local.loc[list(MATCHED), "mean_growth"]
        strongest = float(incumbent.max())
        ratio = float(candidate.mean_growth / strongest) if strongest > 0 else None
        gated_h = float(homogeneous.loc["gated_pooled_HT_G1f", "mean_growth"])
        homo_ratio = (
            float(homogeneous.loc["stratified_candidate", "mean_growth"] / gated_h)
            if gated_h > 0
            else None
        )
        eligible = bool(candidate.all_feasible and candidate.mean_pooled_centered_mean > 0)
        trials.append(
            {
                "budget_rate": float(budget),
                "K": int(K),
                "allocation": allocation,
                "positive_pooled_eligible": eligible,
                "candidate_mean_growth": float(candidate.mean_growth),
                "strongest_incumbent": str(incumbent.idxmax()),
                "strongest_mean_growth": strongest,
                "growth_ratio": ratio,
                "homogeneous_over_gated": homo_ratio,
                "passes": bool(
                    eligible
                    and ratio is not None
                    and ratio >= 1.5
                    and homo_ratio is not None
                    and homo_ratio >= 0.8
                ),
            }
        )
    return {
        "gate": "G1",
        "passes": any(row["passes"] for row in trials),
        "inference": "analytic development screen; no detection or null-calibration claim",
        "trials": trials,
    }


def main() -> None:
    match = re.search(
        r"\*\*Freeze commit:\*\* `([0-9a-f]{40})`", PROTOCOL.read_text(encoding="utf-8")
    )
    if match is None:
        raise RuntimeError("protocol is not frozen")
    git("rev-parse", "--verify", match[1] + "^{commit}")
    sources = [PROTOCOL, Path(__file__), ROOT / "uv.lock"] + sorted(
        (ROOT / "src/shiftlab").rglob("*.py")
    )
    for path in sources:
        git("diff", "--exit-code", "HEAD", "--", str(path.relative_to(ROOT)))
        if not git("ls-files", "--", str(path.relative_to(ROOT))):
            raise RuntimeError(f"uncommitted source: {path}")
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite {OUT}")
    manifest = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git("rev-parse", "HEAD"),
        "dirty_paths": git("status", "--porcelain").splitlines(),
        "device": "cpu",
        "hardware": environment(),
        "seeds": list(range(58700000, 58700020)),
        "scenario": "boundary_local_harm",
        "learner_events": [0, 800],
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "launch.json", manifest)
    start = time.perf_counter()
    config = PrescreenConfig(seed_offset=58700000, device="cpu")
    rows = []
    for seed in manifest["seeds"]:
        stream = learner_slice("boundary_local_harm", seed, config)
        for budget in REGISTERED_BUDGETS:
            for K in REGISTERED_K:
                rows.extend({"seed": seed, **row} for row in evaluate_slice(stream, budget, K))
        print(f"completed learner slice {seed}", flush=True)
    with (OUT / "rows.jsonl").open("w", encoding="utf-8") as target:
        for row in rows:
            target.write(json.dumps(json_safe(row), allow_nan=False) + "\n")
    scalar = pd.DataFrame(
        [
            {
                key: row[key]
                for key in (
                    "seed",
                    "budget_rate",
                    "K",
                    "allocation",
                    "working_law",
                    "arm",
                    "feasible",
                    "pooled_centered_mean",
                    "max_component_growth",
                    "expected_spend",
                    "target_spend",
                )
            }
            for row in rows
        ]
    )
    scalar.to_csv(OUT / "stream_summary.csv", index=False)
    summary = (
        scalar.groupby(["budget_rate", "K", "allocation", "working_law", "arm"])
        .agg(
            seeds=("seed", "nunique"),
            mean_growth=("max_component_growth", "mean"),
            all_feasible=("feasible", "all"),
            mean_pooled_centered_mean=("pooled_centered_mean", "mean"),
            mean_expected_spend=("expected_spend", "mean"),
            mean_target_spend=("target_spend", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(OUT / "summary.csv", index=False)
    decision = decide(summary)
    decision["maximum_identity_error"] = max(row.get("identity_error", 0.0) for row in rows)
    write_json(OUT / "decision.json", decision)
    manifest.update(
        runtime_seconds=time.perf_counter() - start,
        rows=len(rows),
        recorded_at_utc=datetime.now(UTC).isoformat(),
        outputs_sha256={p.name: digest(p) for p in OUT.iterdir() if p.is_file()},
    )
    write_json(OUT / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "passes": decision["passes"],
                "rows": len(rows),
                "runtime_seconds": manifest["runtime_seconds"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
