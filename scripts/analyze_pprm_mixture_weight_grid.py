"""Report development power for fixed PPI block-e-process mixture weights."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

WEIGHTS = (0.1, 0.25, 0.5, 0.75, 0.9)
HARM_SCENARIOS = ("boundary_local_harm", "harmful_adaptation", "recurring_regimes")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_block_mixture_weights_development")
    )
    parser.add_argument("--block-size", type=int, default=20)
    args = parser.parse_args()
    metrics_path = (
        args.output_root
        / f"block_{args.block_size:02d}"
        / "metrics"
        / "hard_budget_comparison.parquet"
    )
    metrics = pd.read_parquet(metrics_path)
    pprm = metrics.loc[metrics.method.eq("pprm_block_adaptive")]
    if pprm.empty or pprm.seed.nunique() != 30:
        raise ValueError("expected 30 PPRM development streams per scenario")

    rows: list[dict[str, object]] = []
    for scenario, group in metrics.groupby("scenario", sort=True):
        if scenario in HARM_SCENARIOS:
            methods = [
                ("CM-EB block PPI", "single_e_detected", "single_e_false_escalation"),
                ("Eventwise frozen PPI", "single_e_detected", "single_e_false_escalation"),
                ("Eventwise updating PPI", "single_e_detected", "single_e_false_escalation"),
            ]
            for method_label, detected_col, false_col in methods:
                if method_label == "CM-EB block PPI":
                    subset = group.loc[group.method.eq("pprm_block_adaptive")]
                elif method_label == "Eventwise frozen PPI":
                    subset = group.loc[group.method.eq("uniform_proxy_frozen")]
                else:
                    subset = group.loc[group.method.eq("uniform_proxy")]
                rows.append(
                    {
                        "scenario": scenario,
                        "method": method_label,
                        "streams": subset.seed.nunique(),
                        "detections": int(subset[detected_col].sum()),
                        "false_escalations": int(subset[false_col].sum()),
                    }
                )
            subset = group.loc[group.method.eq("pprm_block_adaptive")]
            for weight in WEIGHTS:
                suffix = str(weight).replace(".", "p")
                rows.append(
                    {
                        "scenario": scenario,
                        "method": f"PPI fixed mixture w={weight:g}",
                        "streams": subset.seed.nunique(),
                        "detections": int(subset[f"pprm_mix_w{suffix}_detected"].sum()),
                        "false_escalations": int(
                            subset[f"pprm_mix_w{suffix}_false_escalation"].sum()
                        ),
                    }
                )
        elif scenario == "stationary":
            subset = group.loc[group.method.eq("pprm_block_adaptive")]
            rows.append(
                {
                    "scenario": scenario,
                    "method": "CM-EB block PPI",
                    "streams": subset.seed.nunique(),
                    "detections": 0,
                    "false_escalations": int(subset.single_e_false_escalation.sum()),
                }
            )
            for weight in WEIGHTS:
                suffix = str(weight).replace(".", "p")
                rows.append(
                    {
                        "scenario": scenario,
                        "method": f"PPI fixed mixture w={weight:g}",
                        "streams": subset.seed.nunique(),
                        "detections": 0,
                        "false_escalations": int(
                            subset[f"pprm_mix_w{suffix}_false_escalation"].sum()
                        ),
                    }
                )
    summary = pd.DataFrame(rows)
    analysis = args.output_root / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    summary_path = analysis / "mixture_weight_summary.csv"
    report_path = analysis / "mixture_weight_analysis.md"
    summary.to_csv(summary_path, index=False)

    lines = [
        "# Fixed PPI block-e-process mixture weight screen",
        "",
        "Development-only screen on 30 matched streams per scenario, n=6400, B=20, four labels per block, reliance cap 0.1, and a nominal 20% label-dollar budget. Each fixed weight mixes the CM-EB block process and the predictable positive betting process. No weight is selected for confirmatory evaluation from these data.",
        "",
        "|Scenario|Method|Streams|Detections|False escalations|",
        "|---|---|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['streams']}|{row['detections']}/{row['streams']}|{row['false_escalations']}/{row['streams']}|"
        )
    lines.extend(
        [
            "",
            "The best-performing tested weight is exploratory because the same development streams were used for the weight grid. A fresh seed block and null calibration are required before reporting a selected weight's power or error rate.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "analysis": "pprm_block_eprocess_mixture_weight_screen",
        "classification": "development_only_unadjusted",
        "block_size": args.block_size,
        "weights": list(WEIGHTS),
        "sha256": {
            "source": _sha256(Path(__file__)),
            "input": _sha256(metrics_path),
            "summary_csv": _sha256(summary_path),
            "report": _sha256(report_path),
        },
    }
    (analysis / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(report_path)


if __name__ == "__main__":
    main()
