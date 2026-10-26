# CRSP full-cohort retrospective monitor comparison

## Result

The frozen train-only Ridge long/flat policy was evaluated on **7,621,543 test events from 7,350 PERMNOs over 1,507 dates (2020–2025)**. Against the fixed same-date `vwretd > 0` comparator, its 5-bps capped paired cost was lower by **0.0003357 per event**. The two-way product bootstrap (PERMNO clusters × circular 20-date blocks, 2,000 replicates) gave a descriptive 95% interval **[-0.0006550, -0.0000415]**. This supports a retrospective cost difference under this imposed utility; the interval does not include model refitting, release-time, utility-definition, or sequential-validity uncertainty.

The monitor comparison does **not** identify a strong decision-harm monitor on this one historical path. For evaluator-only labels that mark positive mean paired cost in the *next* 20 test dates, paired-cost CUSUM AUROC was 0.422, the bounded excess-cost log-e AUROC was 0.413, predictive-loss CUSUM AUROC was 0.505, and sampled feature MMD AUROC was 0.551. MMD average precision was 0.488 against a positive-window prevalence of about 0.414. The MMD result is weak descriptive ranking evidence, not a selected winner. Paired-cost CUSUM and the bounded e-process did not cross their respective thresholds; predictive-loss CUSUM first crossed on 2020-03-20 and exceeded its empirical threshold on 96.4% of test dates; MMD first crossed on 2020-03-27 and exceeded its calibration-window threshold on 15.9% of dates.

| Monitor | First threshold crossing | Fraction above threshold | AUROC for next-20-date harm | Average precision |
| --- | --- | ---: | ---: | ---: |
| Paired-cost CUSUM | None | 0.0% | 0.422 | 0.365 |
| Bounded excess-cost e-process | None | 0.0% | 0.413 | 0.365 |
| Predictive-loss CUSUM | 2020-03-20 | 96.4% | 0.505 | 0.431 |
| Sampled RBF MMD² | 2020-03-27 | 15.9% | 0.551 | 0.488 |

These retrospective outcomes underline that feature change and predictive-loss alarms do not imply decision harm. The MMD score ranks future positive-cost windows only slightly better than chance; the decision-cost monitors did not predict those windows in this run. Threshold crossings are summaries of this particular path, not false-alarm estimates.

## Protocol and artifacts

The model was fit on all 19,662,345 training observations using exact train-only median imputation and scaling. Calibration used 2,178,352 2018–2019 events; all 7,350 test names were included without test-presence cohort selection. CUDA was used for Ridge sufficient statistics, prediction, and the two-way bootstrap. MMD used a seeded 256-row sample per 20-date window. The paired-cost e-process uses the existing bounded-mean mixture at `epsilon=0`, with a conservative bound from clipped returns and binary turnover. No method was newly invented or tuned on the test outcomes.

The frozen [protocol](crsp_monitor_comparison_protocol.md), [runner](../scripts/evaluate_crsp_monitor_comparison.py), JSON report, aggregate CSV/Parquet summaries, 1,507-date monitor trajectory, and checksum file are in [`outputs/crsp_monitor_comparison_full/`](../outputs/crsp_monitor_comparison_full/). All seven checksums verify. The date trajectory stores aggregate daily metrics and hindsight evaluator labels, not security-level rows. No figure was produced.

## Limits and next work

The future-harm target is hindsight-only, overlaps across dates, and is evaluated on a single dependent market path. The empirical CUSUM/MMD calibration assumes behavior in 2018–2019 transfers to a much longer test horizon. The conditional-mean null required by the e-process, complete feedback, and predictable live decisions are not established by the panel. Calendar close ordering is not a verified release-time record; costs are imposed and returns clipped. Therefore the comparison cannot establish real-data type-I control, detection power, causal shift attribution, trading profitability, or deployment safety.

The companion [e-process replay](crsp_eprocess_candidate_replay_results.md) carries four synthetic-screened bounded-mean monitors onto the same saved CRSP daily cost series. The broader synthetic monitor grids already compare fixed, predictable-variance, start-mixture and empirical-Bernstein candidates under known shift and null mechanisms. The next algorithm screen should target their shared residual-variance power failure with a proof-compatible conditional-variance or stratified betting construction, then calibrate and confirm on fresh synthetic seeds. Keep real-data runs descriptive unless a defensible label-release clock and prospective evaluation target can be specified. Preserve separate claims for distribution shift, predictive degradation, and decision harm.
