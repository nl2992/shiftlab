# CRSP decision-policy retrospective replay protocol

**Status: frozen before this pilot.** This is the first real-data decision-policy diagnostic for ShiftLab. It asks whether a train-only return model changes a simple long-only decision relative to a same-day market-direction rule in the existing CRSP CIZ next-observed-return panel. It is not a test of online validity or evidence that the market changed causally.

## Task and decisions

- Use the checked-in panel task `crsp_ciz_next_observed_daily_return`: the target is the immediately next observed valid return for that PERMNO, with no skipped invalid next row. Sort decisions by PERMNO and current CRSP date; preserve the panel's train (2000–2014), validation (2015–2017), calibration (2018–2019), and test (2020–2025) assignments.
- Select 100 PERMNOs uniformly with a fixed seed from the **training-split universe only**, then include their train and test rows. Do not require future test presence to select the cohort. This bounded pilot is descriptive, not universe-representative.
- Fit standardized Ridge regression (alpha 1) on the selected training rows only. Impute each feature with its training median and scale with training means/standard deviations. The candidate action is long when the predicted next observed return is positive.
- The fixed reference action is long when the current-date CRSP value-weighted market return `vwretd` is positive. All its inputs are same-date learner features; neither policy uses the next return to choose an action.
- Evaluate only test rows. Convert simple-return outcomes to a risk-capped per-dollar utility by clipping each next return to [-10%, +10%]. Per-event cost is negative action times clipped return plus a transaction charge per unit of position turnover. Charge entry, every action change, and exit at the end of the test path for each PERMNO. Compare paired candidate-minus-reference cost at 0, 5, 10, and 25 basis points per turnover.

## Outcomes and uncertainty

Report test count, model RMSE versus a training-mean forecast, action rates, fraction of returns clipped, mean paired decision-cost difference by transaction-cost setting, and year-level paired costs. Negative candidate-minus-reference cost favors the candidate under the stated capped utility. Form 95% descriptive intervals by circular moving-block bootstrap of date-level paired cost sums and counts (20 trading-date blocks; 2,000 replicates). This captures some temporal clustering but not security-level selection, model-selection uncertainty, market-wide structural dependence, or uncertainty over the utility definition.

## Leakage and claim limits

The PERMNO cohort is sampled from train identifiers only. Model imputation, scaling, and fitting use training rows only. The action pair is fixed before test outcomes are read. The market benchmark and features are observed at the current date; the outcome is the next observed PERMNO return. The panel's date ordering is a retrospective daily-close convention, not verified historical WRDS publication time. CRSP returns are dependent across names and dates; costs are imposed sensitivity values and outcomes are clipped. Therefore results are retrospective performance diagnostics only. Do not report false-alarm control, sequential validity, causal drift attribution, trading profitability, or a deployment recommendation from this pilot.

No figure is planned. Any future paper figure must use PaperBanana and be checked against the saved metrics.

## Reproduction

```powershell
uv run python scripts/evaluate_crsp_policy_replay.py --root data --securities 100 --seed 20261025 --device cuda --output outputs/crsp_policy_replay_pilot_100
```
