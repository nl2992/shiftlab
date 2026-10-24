# Residual-variance monitoring power grid: protocol

## Purpose

Diagnose why the registered residual-variance condition produced almost no alarms at label rates 0.20 and 0.40. The grid varies the generator's residual-scale severity and the outcome-label query rate, retaining the existing fixed risk proxy and three anytime-monitor implementations. It is a stress diagnostic; it does not establish error control, a theorem, or a new method.

## Data-generating condition and decision target

The `residual_variance` condition uses the `target_variance` generator. For a generated event with shift weight `w`, the generator multiplies the noise scale by `1 + severity * w`; the conditional mean is unchanged. The deployed classifier is held fixed, while the reference is the source policy. Decision loss uses the registered 5:1 false-negative/false-positive costs, and the monitor tests whether paired deployed-minus-reference cost exceeds the configured margin `epsilon = 0.10`.

The evaluator knows the generated conditional outcome probability and computes the true paired expected cost. The learner's proxy is a logistic classifier fit on the first 12.5% of the stream, frozen before monitoring. Outcome labels are independently sampled at each requested rate, subject to the existing hard label-cost budget. All three monitors use identical generated paths, proxy outputs, query randomness, costs, event order, alpha (0.05), margin, and stopping horizon within each severity/seed/rate cell.

## Registered grid

- Severities: 0.75, 1.5, 2.25, 3.0, 4.5.
- Query rates: 0.20, 0.40, 0.60, 0.80, 1.00.
- 100 paired synthetic seeds per severity/rate cell, seeds 31,102,026–31,102,125.
- Stream size: 2,400 events; CUDA generator requested, with CPU-compatible path retained.
- Monitors: fixed-mixture bounded-mean e-process, predictable Kelly, and plug-in empirical-Bernstein.
- Output: 7,500 per-method rows (5 severities × 5 rates × 100 seeds × 3 monitors).

Run from the repository root:

```powershell
uv run python -m shiftlab.dive.residual_variance_power_grid --device cuda --seeds 100
```

The run writes per-stream CSV and Parquet, a grouped summary, and a manifest with source and output hashes under `outputs/residual_variance_power_grid/`. Use `--device cpu` on a machine without CUDA. The `offline_*` columns use evaluator truth solely to diagnose proxy error and signal strength. They are outputs for analysis and are never passed into model inputs, queries, or monitor updates.

## Interpretation limits

Each cell has 100 streams and serves as a diagnostic power curve. This grid contains no newly calibrated null family, no finite-sample type-I-error claim, and no proof that the null conditional-mean assumption holds event by event. Querying is randomized independently of the current outcome, but querying is truncated by the hard cost budget. The 1.00 rate is the full-label reference arm, not an operational low-cost strategy. Do not use the observed alternative pre-onset alarms as a null false-alarm estimate.

## Reproduction details

The complete per-stream data and group summaries are preserved in `outputs/residual_variance_power_grid/`. The manifest records the CUDA device/runtime, environment, seed range, generator configuration, source-code SHA-256 values, and Parquet SHA-256. Results are descriptive Monte Carlo outcomes and should be regenerated, not manually edited.
