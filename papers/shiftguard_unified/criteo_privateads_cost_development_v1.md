# CriteoPrivateAds cost-sensitive development comparison (2026-10-26)

## Result

The frozen single-seed CUDA run completed in 403.6 seconds on the reproducibility rerun. It trained a hashed logistic incumbent on days 1–13, incrementally updated candidate models through days 18, 19, or 20 under assumed two-day, one-day, or immediate feedback, and scored days 21–25. The run used 72,004,608 training labels and scored 15,917,641 rows per model. Publisher validation days 26–30 were excluded. The output manifest records source and audit hashes, model hashes, GPU details, protocol assumptions, and artifact names; the reproduction command is listed below.

Under the imposed 0.5% target CTR weights, the frozen model's weighted log loss was 0.028087. Updated candidates ranged from 0.027441 to 0.027467 (descriptive reduction of about 2.2–2.3%). At false-negative/false-positive cost ratios of 1, 5, and 20, the updated candidates reduced weighted decision cost by about 0.000017, 0.00028–0.00031, and 0.00223–0.00229 per weighted example, respectively. Intercept-only recalibration produced much smaller changes. Unweighted Brier score was slightly worse for updated candidates, showing that improvement depends on the target-weighted estimand and loss choice.

These are aggregate descriptive metrics over five adjacent daily blocks, with one model initialization and no uncertainty interval. They do not establish statistical significance, a prospective intervention benefit, a causal bidding value, or any sequential error guarantee. The two-day maturity rule is assumed rather than observed at row level; ordering is only daily-block aggregate; the target CTR and cost ratios are research-imposed. This is development evidence only, on a previously available dataset, and cannot close the independent real-data confirmation gate.

## Reproduction

Run from the repository root:

```powershell
uv run pytest -q tests/test_criteo_privateads_cost_baseline.py
uv run python scripts/evaluate_criteo_privateads_cost_baseline.py --device cuda --batch-size 16384 --output outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026
```

The script streams source Parquet files and writes only aggregate metrics, checksums, protocol metadata, and a report. It refuses to overwrite an existing output directory. The CPU path is available with `--device cpu`; a bounded plumbing smoke run can use `--max-batches 1` and must be interpreted as `smoke_not_research`.

## Artifacts

- Output report: `outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026/report.md`
- Manifest: `outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026/manifest.json`
- Daily aggregate metrics: `outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026/daily_metrics.parquet`
- Summary metrics and paired contrasts: `summary_metrics.csv` and `paired_cost_contrasts.csv` in the same directory
- SHA-256 inventory for the output artifacts: `artifact_checksums.json` in the same directory
- Data/task limits: `criteo_privateads_task_contract.md` and the source/delay audit files referenced by the manifest

The second complete CUDA replay regenerates the summary metrics within an
absolute difference of `7.2e-8` from the first run, consistent with small
GPU reduction-order variation. The output checksum file verifies all five
aggregate artifacts, and an independent check verified the four input hashes,
35 unique day/model rows, 90 unique paired contrasts, and 15,917,641 scored
rows per model.

