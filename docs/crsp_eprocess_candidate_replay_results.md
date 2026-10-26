# CRSP replay of synthetic-screened e-process candidates

## Findings

Four existing bounded-mean processes were replayed on the **same 1,507 daily paired-cost increments** from the full-cohort CRSP test set. No model was refit, no raw rows were reloaded, and all candidates used the same 5-bps utility, conservative bound `0.202`, and alpha threshold `log(20) = 2.996`.

None crossed the nominal e-value threshold. Maximum log-e values were 0.062 for the fixed stake mixture, 0.045 for predictable Kelly, 0.050 for plug-in empirical Bernstein, and 0.008 for the uniform eight-start mixture. The outcome path’s total candidate-minus-reference cost remains negative on average, so this indicates no evidence of an overall positive excess-cost mean against the specified comparator in this replay.

For retrospective ranking of evaluator-only next-20-date windows with positive mean paired cost, predictable Kelly had AUROC 0.491 and average precision 0.405. The fixed mixture scored 0.413/0.365, plug-in empirical Bernstein 0.413/0.365, and uniform-start mixture 0.417/0.366. Of 1,487 evaluable windows, 628 were positive (42.2% prevalence), so none of the processes ranked those windows above the prevalence baseline by average precision. Predictable Kelly’s AUROC was closest to chance, but it does not establish a useful forecast or a winner.

| Process | Max log-e | Threshold crossing | AUROC for next-20-date positive cost | Average precision |
| --- | ---: | --- | ---: | ---: |
| Fixed stake mixture | 0.062 | None | 0.413 | 0.365 |
| Predictable Kelly | 0.045 | None | 0.491 | 0.405 |
| Plug-in empirical Bernstein | 0.050 | None | 0.413 | 0.365 |
| Uniform eight-start mixture | 0.008 | None | 0.417 | 0.366 |

The uniform-start mixture’s advantage in one high-severity, high-feedback synthetic residual-variance grid did not transfer to this real-data ranking diagnostic. This is evidence against assuming its synthetic gain generalizes, not evidence that it is generally inferior. All procedures are standard, mathematically grounded e-processes; no new algorithm or theorem is claimed.

## Protocol and artifacts

The frozen [protocol](crsp_eprocess_candidate_replay_protocol.md) uses the verified daily aggregate in [`outputs/crsp_monitor_comparison_full/`](../outputs/crsp_monitor_comparison_full/). The new [runner](../scripts/replay_crsp_eprocess_candidates.py) verifies the input checksums and writes per-date traces, aggregate CSV/Parquet metrics, source/protocol hashes, and an output checksum file under [`outputs/crsp_eprocess_candidate_replay/`](../outputs/crsp_eprocess_candidate_replay/). The replay takes seconds and does not access raw CRSP rows.

## Limits

This is one retrospective, dependent market path. The e-process conditional-on-past null, date-level feedback filtration, and source publication times are not established, so the threshold remains a mathematical reference under assumptions and not a CRSP false-alarm guarantee. The overlapping future-window labels are retrospective evaluator labels. Results do not support real-data type-I error, detection power, causal attribution, trading, deployment, or novelty claims.

The useful algorithmic conclusion is modest: fixed-mixture remains a strong synthetic baseline, predictable Kelly did not materially improve real-path ranking, and the tested start-time mixture should not be promoted based on its synthetic result alone. Keep such candidates in future controlled simulation and prospectively timed data studies with independent null calibration.
