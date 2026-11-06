# Calibrated E-SR evaluation results

**Protocol:** `srr_any_false_calibration_20261106_protocol.md` and the pre-outcome freeze
`srr_any_false_calibration_20261106_evaluation_freeze.md` (committed before these evaluation runs).
**Disposition:** the detector track fails its conjunctive economic gate and is closed; the result is
not confirmation of a new method.

## Independent null check

At the calibration-selected alpha 0.0005, candidate `E_srrSR:gated_deployment` promoted on 20/1,000
fresh `F0_null` streams (2.0%; one-sided 95% Wilson upper bound 2.87%). It passes the frozen
≤5% empirical operating-point gate. E_swcert promoted on 17/1,000 on the same underlying streams;
never-switch did not promote. The null result is empirical for this simulator and contract, not a
replacement for an applicable theorem.

## Paired reversal results

Candidate minus reference net cost; negative favors candidate. All paired contrasts use the frozen
200 shared streams per regime and two-sided 95% paired t intervals. Net cost includes prediction
loss, label cost 0.05, and switch cost 5.

| Regime | Policy | Net cost | Loss | Labels | Switches | Promotion episodes | Mean first promotion | Mean rollbacks |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| F3_reversal_1200 | E-SR alpha .0005 | 398.63 | 381.78 | 200.00 | 1.37 | 195/200 | 579.9 | 0.395 |
| F3_reversal_1200 | E_swcert alpha .05 | 394.79 | 379.05 | 199.71 | 1.15 | 164/200 | 535.6 | 0.330 |
| F3_reversal_1200 | never-switch | 375.89 | 375.89 | 0.00 | 0.00 | 0/200 | — | 0.000 |
| F3_reversal_800 | E-SR alpha .0005 | 390.03 | 371.93 | 200.00 | 1.62 | 174/200 | 534.8 | 0.750 |
| F3_reversal_800 | E_swcert alpha .05 | 391.72 | 376.09 | 199.64 | 1.13 | 144/200 | 445.1 | 0.410 |
| F3_reversal_800 | never-switch | 344.27 | 344.27 | 0.00 | 0.00 | 0/200 | — | 0.000 |

| Regime | Candidate minus reference | Net-cost difference [95% CI] |
|---|---|---:|
| F3_reversal_1200 | E_swcert | +3.84 [+0.12, +7.57] |
| F3_reversal_1200 | never-switch | +22.75 [+19.70, +25.79] |
| F3_reversal_800 | E_swcert | −1.69 [−7.09, +3.71] |
| F3_reversal_800 | never-switch | +45.76 [+42.46, +49.05] |

The candidate spends all 200 label requests in both reversal cells and makes more switches than
E_swcert. Lowering alpha achieved the separate null gate but did not create economic advantage;
the candidate's added query/switch cost outweighs its realized predictive benefit. It fails the
required savings gate in `F3_reversal_1200` and exceeds the 5-unit adverse-regime harm limit in
`F3_reversal_800`. Stop this E-SR threshold track without further tuning.

## Reproduction and artifacts

Run `uv run python research/scoped_method/analyze_srr_calibrated_evaluation.py` to regenerate
`evaluation_summary.json` from the four frozen raw outputs. The four `manifest.json` files record
the exact screen commands, source hashes, and run metadata; raw paired rows are in each adjacent
`records.jsonl`. SHA-256 values are recorded in `EVALUATION_HASHES.txt`.
