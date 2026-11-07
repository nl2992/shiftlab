# P7s / Model Picker acquisition overlay: bounded falsification pilot

**Status:** prospective synthetic development screen; not confirmation. Freeze before implementation
and outcome generation. No real or locked data is opened by this pilot.

## Target and motivation

The Failure Atlas M1 scenario is late, persistent challenger improvement under a finite label
budget. In exposed OpenML-LDPA replay, P7s cost 478.35 while the Model Picker adapter cost 431.87;
P7s's frozen comparison gate failed. The unresolved engineering hypothesis is whether the Model
Picker's predictable disagreement-query propensity can accelerate P7s evidence acquisition before
promotion, while P7s's settled-decision pacing suppresses unnecessary post-promotion queries and
restores the extra query rate when released reversal evidence appears.

This is a familiar controlled-sensing / certified-selection composition, not presumed novel. Existing
D1 tests a Model Picker host behind a started-mixture promotion gate, but it does not reuse the P7s
certificate or preserve P7s rollback behavior. A favorable result would justify only a targeted
prior-art review and independent replication, not a novelty claim.

## Candidate definition (freeze)

Use unchanged P7s certificate, bets, thresholds, deployment, and rollback implementation. Add the
Model Picker query propensity as an independent extra disagreement draw while P7s has not promoted.
After promotion, add that extra draw only when the P7s released-evidence state signals reversal
(`pst >= 0`); when the challenger remains recently ahead (`pst < 0`), retain P7s settled pacing
alone. The combined issue-time propensity is

`q_t = 1 - (1 - q_P7s,t) * (1 - q_MP,t)`

when the overlay is active, and `q_t = q_P7s,t` when settled. Both component propensities use only
released labels through the policy filtration and current label-free predictions. Draw one query
with probability `q_t`; pass this same frozen `q_t` to P7s's inverse-propensity/e-process update and
to Model Picker's importance-weighted loss update. Apply the shared hard budget before sampling.
This issue-time propensity and delayed-release path are implementation invariants; any mismatch
invalidates the run.

One simplest ablation removes the post-promotion settled throttle but keeps the same combined query
propensity throughout. No parameter or threshold search is allowed.

## Frozen run contract

- Synthetic regimes: `F1_late_800` (primary), `F0_better`, `F3_reversal_800`, `F0_null`.
- 50 paired seeds/cell; seed base `7110601701`.
- Horizon 2,000; hard query budget 200; delay 100; label price 0.05; switch cost 5.
- Methods: candidate, no-settled-throttle ablation, unchanged P7s, Model Picker adapter, D1, Gated
  front-loaded, and never-switch. All replay the same evaluator-generated loss stream per seed.
- Report net cost and decomposition (predictive loss, labels, switches), query count and timing,
  promotions/rollbacks and timing, and null promotion counts. Paired 95% t intervals are over the
  50 shared synthetic seeds. No oracle information enters a policy.

## Development decision rule

The candidate survives only if, on `F1_late_800`, it saves at least 5 net-cost units versus both
Model Picker and unchanged P7s, with each paired 95% interval wholly below zero; on `F3_reversal_800`
and `F0_null`, its mean excess net cost versus never-switch is at most 5 units; and its `F0_null`
promotion count is at most 5/50. `F0_better` is reported as a trade-off check and cannot replace the
primary. These are screening thresholds, not formal safety validation. Any error, budget, propensity,
or chronology invariant failure stops the run. Failure of any development criterion ends this
candidate; passing permits only a separate prior-art review and frozen independent evaluation.

## Reproducibility

After implementation, record full source commit and SHA-256 values, exact command, environment,
raw rows, analysis code, and output hashes in this folder. Results must include all prespecified
cells and methods, including unfavorable outcomes.
