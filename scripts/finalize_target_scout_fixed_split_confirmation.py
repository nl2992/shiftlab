"""Add interpretable method-level summaries to the verified Q2 confirmation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_confirmation_v1"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    streams = pd.read_parquet(OUTPUT / "streams.parquet")
    summary = streams.groupby("method", as_index=False).agg(
        streams=("seed", "count"),
        promotions=("promoted", "sum"),
        harmful_promotions=("harmful_postpromotion_promotion", "sum"),
        promotion_rate=("promoted", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_expected_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_realized_net_gain=("realized_postpromotion_net_gain", "mean"),
    )
    if summary["streams"].ne(5400).any() or summary["harmful_promotions"].sum() != 0:
        raise RuntimeError("unexpected method counts or harmful promotions")
    if summary["mean_labels"].max() - summary["mean_labels"].min() > 1e-12:
        raise RuntimeError("method-level label budgets are not matched")
    summary.to_csv(OUTPUT / "method_summary.csv", index=False)
    summary.to_parquet(OUTPUT / "method_summary.parquet", index=False)
    report_path = OUTPUT / "results.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "## Matched promotion and label summary"
    if marker not in report:
        lines = [
            "",
            marker,
            "",
            "| Method | Promotions / 5,400 | Harmful promotions | Mean queried labels / stream | Mean expected future net gain | Mean realized future net gain |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row in summary.to_dict(orient="records"):
            lines.append(
                f"| {row['method']} | {int(row['promotions'])} | {int(row['harmful_promotions'])} | "
                f"{row['mean_labels']:.2f} | {row['mean_expected_net_gain']:.4f} | "
                f"{row['mean_realized_net_gain']:.4f} |"
            )
        lines.extend(
            [
                "",
                "All three methods used the same mean label count. Target-Scout selected on its scout slice and certified on the remaining slice, so its promotion and net-gain outcomes reflect that registered two-stage design. The expected-net-gain metric includes non-promoted streams as zero.",
            ]
        )
        report += "\n".join(lines) + "\n"
        report_path.write_text(report, encoding="utf-8")
    manifest["method_summary"] = summary.to_dict(orient="records")
    manifest["artifacts"]["results.md"] = sha256(report_path)
    manifest["artifacts"]["method_summary.csv"] = sha256(OUTPUT / "method_summary.csv")
    manifest["artifacts"]["method_summary.parquet"] = sha256(OUTPUT / "method_summary.parquet")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
