"""Audit and summarize the registered OPE LIL Markov development screens."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUNS = {
    "constant_predictor": Path("outputs/scout_context_ope_markov_development_v1"),
    "validation_predictor": Path("outputs/scout_context_ope_markov_development_v2"),
}
EXPECTED_ROWS = 25_920
EXPECTED_EVENTWISE_ROWS = 6_480
METHOD = "scout_context_policy_eventwise_propensity_bound"
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 21_900_060


def _load_run(name: str, root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    metrics = root / "metrics/scout_context_markov_development_streams.parquet"
    manifest_path = root / "reports/manifest.json"
    if not metrics.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"incomplete run artifacts under {root}")
    detail = pd.read_parquet(metrics)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(detail) != EXPECTED_ROWS:
        raise ValueError(f"{name}: expected {EXPECTED_ROWS} rows, got {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise ValueError(f"{name}: duplicate method/cell/seed rows")
    if int((detail["labels_queried"] > detail["label_budget"]).sum()):
        raise ValueError(f"{name}: hard label cap violation")
    ope = detail.loc[detail["alpha_allocation"].eq(METHOD)].copy()
    if len(ope) != EXPECTED_EVENTWISE_ROWS:
        raise ValueError(f"{name}: expected {EXPECTED_EVENTWISE_ROWS} eventwise rows")
    required = [
        "ope_lil_promoted",
        "ope_lil_lower_final",
        "ope_lil_width_final",
        "ope_lil_expected_postpromotion_net_gain",
    ]
    if ope[required].isna().any().any():
        raise ValueError(f"{name}: OPE comparison fields contain missing values")
    protocol = manifest["protocol"]
    protocol_path = Path(protocol["path"])
    actual_hash = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    if actual_hash != protocol["sha256"]:
        raise ValueError(f"{name}: frozen protocol hash mismatch")
    return ope, manifest


def _summarize(name: str, frame: pd.DataFrame) -> dict[str, object]:
    row: dict[str, object] = {"predictor": name, "streams": len(frame)}
    for label, subset in (
        ("null", frame.loc[frame["context_signal_strength"].eq(0)]),
        ("positive", frame.loc[frame["context_signal_strength"].gt(0)]),
    ):
        row[f"{label}_streams"] = len(subset)
        row[f"{label}_fixed_promotion_rate"] = float(subset["promoted"].mean())
        row[f"{label}_ope_promotion_rate"] = float(subset["ope_lil_promoted"].mean())
        row[f"{label}_fixed_expected_gain"] = float(
            subset["expected_postpromotion_net_gain"].mean()
        )
        row[f"{label}_ope_expected_gain"] = float(
            subset["ope_lil_expected_postpromotion_net_gain"].mean()
        )
        row[f"{label}_paired_gain_delta"] = float(
            (
                subset["ope_lil_expected_postpromotion_net_gain"]
                - subset["expected_postpromotion_net_gain"]
            ).mean()
        )
        row[f"{label}_mean_final_lower"] = float(subset["ope_lil_lower_final"].mean())
        row[f"{label}_mean_final_width"] = float(subset["ope_lil_width_final"].mean())
        row[f"{label}_mean_labels"] = float(subset["labels_queried"].mean())
    positive = frame.loc[frame["context_signal_strength"].gt(0)].copy()
    positive["paired_gain_delta"] = (
        positive["ope_lil_expected_postpromotion_net_gain"]
        - positive["expected_postpromotion_net_gain"]
    )
    seed_means = positive.groupby("seed")["paired_gain_delta"].mean().to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap = rng.choice(seed_means, size=(BOOTSTRAP_DRAWS, len(seed_means)), replace=True).mean(
        axis=1
    )
    row["positive_seed_cluster_delta"] = float(seed_means.mean())
    row["positive_seed_cluster_bootstrap_95_low"] = float(np.quantile(bootstrap, 0.025))
    row["positive_seed_cluster_bootstrap_95_high"] = float(np.quantile(bootstrap, 0.975))
    row["positive_seed_clusters"] = len(seed_means)
    return row


def main() -> None:
    summaries: list[dict[str, object]] = []
    provenance: list[str] = []
    for name, root in RUNS.items():
        frame, manifest = _load_run(name, root)
        summaries.append(_summarize(name, frame))
        cfg = manifest["configuration"]
        provenance.append(
            f"- `{name}`: seeds {cfg['seed_offset']}–{cfg['seed_end_inclusive']}; "
            f"protocol SHA-256 `{manifest['protocol']['sha256']}`; {len(frame):,} eventwise rows."
        )
    report = pd.DataFrame(summaries)
    output = Path("outputs/scout_context_ope_markov_comparison_audit")
    output.mkdir(parents=True, exist_ok=True)
    report.to_csv(output / "summary.csv", index=False)
    content = [
        "# OPE LIL comparator development audit",
        "",
        "Exploratory comparison only; no null calibration or SOTA claim.",
        "",
        *provenance,
        "",
        report.to_markdown(index=False, floatfmt=".5f"),
        "",
        (
            "The paired utility interval is a descriptive seed-cluster bootstrap across 72 positive-signal cells. "
            "Zero-signal promotion rates are diagnostics, not calibration. The OPE interval targets average "
            "conditional certification-period value; evaluator-known deployment utility additionally depends "
            "on transport from certification to deployment."
        ),
    ]
    (output / "report.md").write_text("\n".join(content) + "\n", encoding="utf-8")
    print(output / "report.md")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
