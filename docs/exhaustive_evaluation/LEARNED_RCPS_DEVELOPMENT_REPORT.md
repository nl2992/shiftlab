# Learned-query fixed-question RCPS adaptation: development results

2026-10-30. Previous goal turn: progress (native six-arm pilot/source audit committed). This continuation implements learned-query components, verifies author-component parity, checks delayed event semantics and runs a registered matched development diagnostic. No novel method or exhaustive SOTA completion is claimed.

## Implemented and verified

The fixed-question port includes the author's three-knot linear/clamped risk predictor, raw-risk squared-error training, COCOB, square-root variance querying,256-round dual history and source-as-written normalization objective. Beta is fixed at.5; the original multi-beta calibration/inversion problem is not reproduced. The predictor/query transport matches the author class on160 updates with replayed labels: maximum error2.22e−16 across query probabilities, CV predictions, both predictor weights and normalization. See learned_rcps_component_parity_v2.json. The earlier parity record is retained.

The paired adaptation maps gain Z to risk(1−Z)/2 and threshold(1−margin)/2. A fixed global propensity floor bounds the stake. Bet, propensity, predictor value and residual target are frozen at issue; only released queried outcomes train the predictors. All requests are charged immediately, including pending labels. Once budget is exhausted, new event factors become1 while pending factors still publish. Promotion ends acquisition. This is an explicitly changed contract from the native expected-rate task.

Six tests cover no-budget behavior, no early feedback, charging pending requests, pre-release action invariance under hidden-outcome changes, issue-time factor reconstruction, distinct variants and finite long-horizon behavior.27 relevant tests pass including existing paired controls and baseline tests. Ruff0.17.1 checks pass.

## Registered variants and limitations

The four learned arms cross raw-risk versus saved-residual² variance targets with source versus paper-payoff normalization. The latter retains the source's finite dual cap and explicitly projects normalization parameter c to[−20,20]; ratios are evaluated in log space. This projection is a declared numerical/algorithmic adaptation, not an exact native or full-paper implementation. An early test exposed overflow in the unprojected payoff variant; this was resolved before registration, with a long-horizon regression test. It does not establish that this is the intended or best published implementation.

Two uniform query controls share the learned CV predictor: floor.05 preserves the conservative common range bound, while floor.2 uses the tighter known uniform-propensity bound. The source's changing predictor-based minimum range bound is not transported; this remains an explicit efficiency/fidelity limitation. No competitor is claimed dominated by these conservative adaptations.

References are the previously frozen Kelly finalist, tuned FTL and both strict-calibrated CUSUM slacks. All share horizon2000, rate budget.2/cap400, delay5, alpha.05, margin.01, query cost.001, switch cost1 and fixed models. Uniform random arrays/outcomes are shared across arms. CUSUM uses its prior simulator-specific thresholds; it has no arbitrary-null guarantee.

Registration: learned_rcps_development_registration.json. Completed status: learned_rcps_development_status.json.8 cases ×256 independent paths =2048 shared streams, evaluated by10 methods. This is development, not confirmation or a new≥500-candidate round. All methods/negative cases are reported.

## Cost findings

Persistent cost is the equal-case mean over useful_initial/useful/late/small; reversal is separate. Maximum null promotion rate is descriptive over harmful/tie/harmful_after_shift, not a simultaneous safety pass.

| Adaptation/control | Persistent total cost | Maximum observed null rate | Late-benefit excess cost | Reversal excess cost |
|---|---:|---:|---:|---:|
| Raw risk/source normalization | 362.829 | 0 | +.101 | +.433 |
| Raw risk/projected paper normalization | 419.515 | 0 | +.400 | +.400 |
| Residual²/source normalization | 362.868 | 0 | +.101 | +.432 |
| Residual²/projected paper normalization | 418.980 | 0 | +.400 | +.400 |
| Uniform, floor.05 bound | 353.391 | 0 | +.393 | +.392 |
| Uniform, floor.2 bound | 288.461 | .02344 | +.393 | +3.201 |
| Kelly finalist | 202.702 | .02344 | −77.619 | +4.454 |
| Tuned FTL | 205.268 | .00781 | −82.599 | +7.953 |
| CUSUM slack.05 | 202.663 | .02734 | −83.158 | +1.556 |
| CUSUM slack.1 | 198.554 | .01953 | −88.646 | −2.924 |

None of the six learned/uniform adaptations improves persistent cost over the strong references. Low false promotions accompany low useful action; abstention is not evidence of practical superiority. This is a negative result for the declared port, not a claim that full active-RCPS fails in its own setting or that no efficient same-target variant exists.

## Verified bottlenecks

A post-hoc replay of the exact first late-case batch reproduces first-promotion times, paid labels and costs byte-for-byte at the array level. It inspects query timing without adding a new independent result; see learned_rcps_late_timing_diagnostic.json.

- Source normalization uses101.67 labels on average in that batch;26.10 are issued after the evaluator's late-benefit onset at1500. It never exhausts the hard budget before onset and never promotes. This is underspending/slow evidence, not exhaustion.
- The residual/projected-paper variant exhausts all400 labels before onset on **every one of128 paths**; it issues zero late-benefit labels and never promotes. Front-loading is directly established, not inferred from total spend alone.
- The tight uniform control retains94.07 late-benefit labels on average but still never promotes (maximum logwealth1.195 versus log20≈2.996). Acquisition timing alone cannot explain its failure. The large cost difference between floor.05 and floor.2 controls identifies range/stake conservatism as another bottleneck; predictor fitting, the risk transformation and the betting rule also differ from the direct-gain controls.

## Disposition and next bounded work

Stop an efficacy claim for these six adaptations. Retain them as source/fidelity diagnostics. Before independent confirmation or another large combination round:

1. Transport the source's predictable predictor-range bound at fixed beta and check factor/stake parity on a native trace. This addresses a known weakness in the current comparison rather than declaring a conservative baseline fully reproduced.
2. Test a budget-paced normalization that uses remaining horizon/pending requests, alongside equally paced uniform/CUSUM/FTL controls. Generic pacing is known composition; require a surviving source-level residual before a novelty claim. Budget management must not spend all labels before late regimes.
3. Recheck the same delay/reversal cases and failure modes. Successful clock/budget handling alone is insufficient: the tighter uniform control already shows evidence accumulation can still be the binding constraint.
4. Complete Hsu–Shekhar and prediction-guided betting applicability audits, plus the outstanding synthesis/Markov scope inventory. The numerical sweep minimum has not made this literature inventory complete.

No reserved real windows were read. No additional raw downloads, paid jobs, remote jobs or subagents. Exact source snapshots, registrations, per-path arrays and hashes preserve the negative result. Goal remains active.
