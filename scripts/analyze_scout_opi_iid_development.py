"""Check the IID finite-class OPI development run and summarize matched outcomes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("outputs/scout_opi_iid_development_v2")
METHOD = "scout_context_policy_eventwise_propensity_bound"
EXPECTED_ROWS = 6_480
EXPECTED_SCOUT_ROWS = 2_160
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 22_100_060


def main() -> None:
    metrics = ROOT / "metrics/scout_opi_iid_streams.parquet"
    manifest_path = ROOT / "reports/manifest.json"
    detail = pd.read_parquet(metrics)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(detail) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise ValueError("duplicate method/cell/seed rows")
    if int((detail.labels_queried > detail.label_budget).sum()):
        raise ValueError("hard label cap violation")
    scout = detail.loc[detail.alpha_allocation.eq(METHOD)].copy()
    if len(scout) != EXPECTED_SCOUT_ROWS:
        raise ValueError(f"expected {EXPECTED_SCOUT_ROWS} scout rows, got {len(scout)}")
    if scout.opi_lil_promoted.isna().any() or scout.opi_lil_final_set_size.isna().any():
        raise ValueError("missing OPI decisions or candidate-set sizes")
    proto = manifest["protocol"]
    actual_hash = hashlib.sha256(Path(proto["path"]).read_bytes()).hexdigest()
    if actual_hash != proto["sha256"]:
        raise ValueError("frozen protocol hash mismatch")
    if not np.array_equal(np.sort(scout.seed.unique()), np.arange(22_100_000, 22_100_060)):
        raise ValueError("unexpected IID OPI seed block")
    if int(scout.opi_lil_stop_certification_events.notna().sum()) != 0:
        raise ValueError("unexpected OPI identification on the recorded development block")

    summary: list[dict[str, object]] = []
    for label, frame in (
        ("zero_signal_diagnostic", scout.loc[scout.context_signal_strength.eq(0)]),
        ("positive_signal", scout.loc[scout.context_signal_strength.gt(0)]),
    ):
        summary.append(
            {
                "slice": label,
                "streams": len(frame),
                "opi_promotion_rate": float(frame.opi_lil_promoted.mean()),
                "fixed_mixture_promotion_rate": float(frame.promoted.mean()),
                "opi_unique_identification_rate": float(
                    frame.opi_lil_stop_certification_events.notna().mean()
                ),
                "opi_final_set_size_mean": float(frame.opi_lil_final_set_size.mean()),
                "opi_labels_mean": float(frame.opi_lil_labels_used.mean()),
                "fixed_mixture_labels_mean": float(frame.labels_queried.mean()),
                "opi_expected_future_gain_mean": float(
                    frame.opi_lil_expected_postpromotion_net_gain.mean()
                ),
                "fixed_expected_future_gain_mean": float(
                    frame.expected_postpromotion_net_gain.mean()
                ),
                "opi_minus_fixed_gain": float(
                    (
                        frame.opi_lil_expected_postpromotion_net_gain
                        - frame.expected_postpromotion_net_gain
                    ).mean()
                ),
            }
        )
    positive = scout.loc[scout.context_signal_strength.gt(0)].copy()
    positive["gain_delta"] = (
        positive.opi_lil_expected_postpromotion_net_gain - positive.expected_postpromotion_net_gain
    )
    seed_means = positive.groupby("seed").gain_delta.mean().to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap = rng.choice(seed_means, (BOOTSTRAP_DRAWS, len(seed_means)), replace=True).mean(
        axis=1
    )
    boot_interval = np.quantile(bootstrap, [0.025, 0.975])
    output = Path("outputs/scout_opi_iid_comparison_audit")
    output.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(summary)
    table.to_csv(output / "summary.csv", index=False)
    report = [
        "# IID finite-class OPI comparison audit",
        "",
        "Exploratory development only; zero-signal rates are not null calibration.",
        "",
        f"Seed block: {manifest['configuration']['seed_offset']}–{manifest['configuration']['seed_end_inclusive']}; protocol SHA-256 `{proto['sha256']}`.",
        f"Rows: {len(detail):,}; eventwise scout rows: {len(scout):,}; duplicate keys: 0; cap violations: 0.",
        f"Per-stream OPI class size range: {manifest['configuration']['opi_candidate_count_range']}.",
        "",
        table.to_markdown(index=False, floatfmt=".5f"),
        "",
        (
            f"Positive-signal paired utility difference, OPI minus fixed mixture: {seed_means.mean():.5f}; "
            f"descriptive 95% seed-cluster bootstrap interval [{boot_interval[0]:.5f}, {boot_interval[1]:.5f}] "
            f"across {len(seed_means)} seed clusters."
        ),
        "",
        "The OPI policy-value CSs target the best fixed mapping in this IID-context finite class. The utility endpoint is evaluator-known post-identification value. This development screen neither calibrates OPI error nor establishes a future-real-world guarantee or novelty/SOTA claim.",
    ]
    report_path = output / "report.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report_path)
    print(table.to_string(index=False))
    print("positive paired gain delta", seed_means.mean(), "bootstrap", boot_interval)


if __name__ == "__main__":
    main()
