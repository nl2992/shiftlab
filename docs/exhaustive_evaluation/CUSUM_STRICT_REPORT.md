# Stricter CUSUM calibration: independent follow-up

2026-10-30. Previous turn: progress (implemented/committed independent CUSUM baseline comparison). This continuation completed a separate registered comparison. Goal remains active; exhaustive coverage is not complete.

## Contract and provenance

Same four slacks, simulator, hard budget400, horizon2000, uniform query probability.2, delay5, benefit margin.01, query cost.001, switch cost1 and no rollback as the original CUSUM comparison. Only prospective changes: threshold-calibration quantile.975 and fresh world/query seed bases202640000/202641000. Calibration uses1000 independent paths per null; testing uses2000 per null and500 per alternative:11500 total paths, including8500 tests. The previous run was terminal before this began; no historical artifacts were overwritten.

The runner now accepts --profile strict; its original namespace remains protected by the existing registration. Original executed source snapshots remain unchanged. Registration includes source hashes and freezes all four slacks without alternative tuning. Results report all slacks; this is not a newly selected champion. Standard CUSUM is an adapted operational baseline, not a new method or a reproduction of a full author risk-monitoring pipeline.

## Results

Cost averages the four persistent cases equally; reversal is a separate stress case. The null bound is the maximum of three simultaneous one-sided bounds, Bonferroni over18 method/null cells.

| Method | Persistent mean total cost | Reversal excess versus never switching | Tie-null promotion rate | Maximum null upper bound |
|---|---:|---:|---:|---:|
| CUSUM slack0 | 230.917 | +35.049 | .0255 | .0369 |
| CUSUM slack.01 | 222.626 | +24.795 | .0245 | .0357 |
| CUSUM slack.05 | 204.088 | +.938 | .0310 | .0433 |
| CUSUM slack.1 | 200.113 | −4.530 | .0250 | .0363 |
| Kelly finalist | 204.103 | +4.550 | .0260 | .0375 |
| Tuned FTL | 206.205 | +8.579 | .0150 | .0242 |

All methods pass the registered empirical screen: every null upper bound <=.06. This is evidence only for the three tested simulator nulls; it does not certify arbitrary conditional-null validity, real serial dependence, or future benefit after reversal. Thresholds calibrated using known simulator nulls have information unavailable in a generic real deployment. No equal-general-guarantee claim is made.

All eight classical/reference cost contrasts are in cusum_strict_decision.json. Bonferroni95% family intervals use paired normal approximations over independent paths and equal-case weighting:

- Slack.1 versus Kelly: −3.990 cost units, interval[−4.796,−3.184], relative reduction1.955%.
- Slack.1 versus tuned FTL: −6.092, interval[−6.789,−5.395], relative reduction2.954%.
- Slack.05 versus Kelly: −.015, interval[−.720,.689], effectively tied.
- Both smaller slacks are substantially worse on persistent cost. These failures are retained.

No contrast passes the10% practical gate. Multiplicity adjustment was applied in the analysis across all eight contrasts; normal approximation and conditional-on-calibration interpretation remain limitations. This does not establish any new methodological contribution. It does remove support for a substantial empirical advantage of the existing betting finalist over the tested classical controls.

## Bottleneck interpretation and next work

The common weakness is costed action timing under delay and changing benefit. Accumulating more historical evidence can delay useful action; an irreversible promotion can incur reversal loss. CUSUM's local reset helps some cases without changing that structural limitation. Generic resets, rollback, and age-corrected intervals are established ingredients; merely combining them is not a novelty result.

Next priority is the remaining source/contract baseline inventory: full learned active-RCPS and Hsu–Shekhar querying, followed by prediction-guided betting applicability and robust-controller synthesis. Do not call partial formula adapters exhaustive SOTA comparisons. The next combination round must have a surviving source-level mechanism and a predeclared bottleneck test; the1836 effective tuples already evaluated satisfy the numerical minimum but do not complete the research objective.

Implementation checks: existing21 paired/baseline tests and new-profile Ruff0.17.1 checks; frozen-source hash verification; terminal run status and all34 per-path batch artifacts. Reproduction command: python scripts/exhaustive_evaluation/compare_calibrated_cusum.py --profile strict (registration now prevents overwriting). Analysis command: python scripts/exhaustive_evaluation/analyze_cusum_strict.py. Reserved real windows remain closed. No new raw downloads or remote jobs.
