"""Run the registered G1 analytic growth pre-screen for the anchored, gated harm monitor."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.dive.adg_growth_prescreen import PrescreenConfig, mixture_rows, prescreen_stream

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/adg_growth_prescreen_20"
PROTOCOL = Path("docs/anchored_gated_harm_monitor_development_protocol.md")
SOURCES = (
    Path("src/shiftlab/dive/adg_growth_prescreen.py"),
    Path("scripts/run_adg_growth_prescreen.py"),
    PROTOCOL,
)
CANDIDATE = "adg_gamma_mix"
COMPARATORS = ("a1_ppi_symmetric", "a3_discern_gated")
RATIO_THRESHOLD = 1.5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def summarize(rows: pd.DataFrame) -> pd.DataFrame:
    alternative = rows[rows.law.eq("alternative") & rows.feasible]
    grouped = alternative.groupby(["scenario", "budget_rate", "target_excess", "arm"], sort=True)
    summary = grouped.agg(
        seeds=("seed", "nunique"),
        mean_growth=("best_growth", "mean"),
        sd_growth=("best_growth", "std"),
        mean_bound=("bound", "mean"),
        share_stake_at_cap=("stake_at_cap", "mean"),
        mean_spend=("expected_spend_per_event", "mean"),
        target_spend=("target_spend_per_event", "mean"),
        mean_labels=("expected_labels_per_event", "mean"),
        mean_q_gated=("q_gated", "mean"),
    ).reset_index()
    natural = rows[rows.law.eq("natural")].groupby(["scenario", "budget_rate", "arm"], sort=True)
    natural_summary = natural.agg(
        natural_mean_growth=("best_growth", "mean"),
        natural_max_growth=("best_growth", "max"),
        natural_mean_increment=("mean_increment", "mean"),
    ).reset_index()
    return summary.merge(natural_summary, on=["scenario", "budget_rate", "arm"], how="left")


def ratios(rows: pd.DataFrame, config: PrescreenConfig) -> pd.DataFrame:
    alternative = rows[rows.law.eq("alternative") & rows.feasible]
    wide = alternative.pivot_table(
        index=["scenario", "budget_rate", "target_excess", "seed"],
        columns="arm",
        values="best_growth",
    ).reset_index()
    wide["comparator_max"] = wide[list(COMPARATORS)].max(axis=1)
    wide["seed_ratio"] = wide[CANDIDATE] / wide["comparator_max"]
    wide["anchor_over_gating"] = wide[CANDIDATE] / wide["a3_discern_gated"]
    wide["gating_over_a1"] = wide["a3_discern_gated"] / wide["a1_ppi_symmetric"]
    keys = ["scenario", "budget_rate", "target_excess"]
    out = wide.groupby(keys, sort=True).agg(
        seeds=("seed", "nunique"),
        candidate_mean=(CANDIDATE, "mean"),
        a1_mean=("a1_ppi_symmetric", "mean"),
        a3_mean=("a3_discern_gated", "mean"),
        share_seeds_ratio_ge_threshold=(
            "seed_ratio",
            lambda v: float(np.mean(v >= RATIO_THRESHOLD)),
        ),
        median_anchor_over_gating=("anchor_over_gating", "median"),
        median_gating_over_a1=("gating_over_a1", "median"),
    )
    out["ratio_of_means"] = out.candidate_mean / out[["a1_mean", "a3_mean"]].max(axis=1)
    out["anchor_over_gating_of_means"] = out.candidate_mean / out.a3_mean
    return out.reset_index()


def main() -> None:
    config = PrescreenConfig().validate()
    started = time.perf_counter()
    rows: list[dict] = []
    for scenario in config.scenarios:
        for replicate in range(config.seeds):
            rows.extend(prescreen_stream(scenario, replicate, config))
    rows = mixture_rows(rows)
    runtime = time.perf_counter() - started
    frame = pd.DataFrame(rows)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT / "stream_rows.csv", index=False)
    summary = summarize(frame)
    summary.to_csv(OUTPUT / "summary.csv", index=False)
    ratio_table = ratios(frame, config)
    ratio_table.to_csv(OUTPUT / "ratios.csv", index=False)

    primary = ratio_table[
        ratio_table.scenario.eq(config.primary_scenario)
        & np.isclose(ratio_table.budget_rate, config.primary_budget)
        & np.isclose(ratio_table.target_excess, config.primary_excess)
    ].iloc[0]
    natural_rows = frame[frame.law.eq("natural")]
    infeasible = frame[frame.law.eq("alternative") & ~frame.feasible][
        ["scenario", "seed", "target_excess"]
    ].drop_duplicates()
    criterion = {
        "gate": "G1",
        "criterion": "mean G*(adg_gamma_mix) >= 1.5 * max(mean G*(A1), mean G*(A3))",
        "scenario": config.primary_scenario,
        "budget_rate": config.primary_budget,
        "target_excess": config.primary_excess,
        "seeds": int(primary.seeds),
        "candidate_mean_growth": float(primary.candidate_mean),
        "a1_mean_growth": float(primary.a1_mean),
        "a3_mean_growth": float(primary.a3_mean),
        "ratio_of_means": float(primary.ratio_of_means),
        "anchor_over_gating_of_means": float(primary.anchor_over_gating_of_means),
        "passes": bool(primary.ratio_of_means >= RATIO_THRESHOLD),
        "infeasible_alternatives": len(infeasible),
        "natural_rows": len(natural_rows),
        "natural_rows_with_positive_mean_increment": int((natural_rows.mean_increment > 0).sum()),
        "natural_rows_nonpositive_mean_with_positive_growth": int(
            ((natural_rows.mean_increment <= 0) & (natural_rows.best_growth > 1e-12)).sum()
        ),
    }
    (OUTPUT / "criterion.json").write_text(json.dumps(criterion, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "config": asdict(config),
        "git_head": git("rev-parse", "HEAD"),
        "git_dirty_paths": git("status", "--porcelain", "--", *map(str, SOURCES)).splitlines(),
        "source_sha256": {str(path): sha256(ROOT / path) for path in SOURCES},
        "outputs_sha256": {
            name: sha256(OUTPUT / name)
            for name in ("stream_rows.csv", "summary.csv", "ratios.csv", "criterion.json")
        },
        "rows": len(frame),
        "runtime_seconds": runtime,
        "learner_side_only": True,
        "monitor_runs": 0,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(criterion, indent=2))


if __name__ == "__main__":
    main()
