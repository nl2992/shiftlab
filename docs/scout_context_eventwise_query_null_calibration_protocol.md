# Eventwise scout null calibration with predictable query policies

**Status:** frozen 2026-10-25 before execution. This calibration tests the familywise
false-promotion rate for the frozen eventwise-propensity-bound scout under uniform and
variance-weighted covariate-adaptive querying. It does not test positive-signal power or utility.

## Conditional null and scope

At each target event the label is Bernoulli with probability exactly `1/6`, the FN/FP decision
threshold for FN cost 5 and FP cost 1. This holds in both latent contexts. A fixed candidate's
gross conditional expected decision gain is therefore zero event by event; the switching charge
is 0.05. The learner-visible context follows a stationary two-state Markov chain with prevalence
`{0.10, 0.50, 0.90}` and persistence `{0, 0.50, 0.80}`, with proxy error `{0, 0.25}`.

The eventwise scout, candidate family, train/validation/scout/certification split, alpha 0.05,
direct-IPW estimator, and 20%/40% hard label caps are frozen. Query probabilities are fitted on
the pre-monitor validation slice and then depend only on current learner-visible features and
pre-monitor fits; each label indicator is an independent Bernoulli draw with its known propensity.
There is no query adaptation to certification wealth or labels. The bound is the standard
bounded-betting construction with predictable `B_t = C/q_t + kappa`, not a new theorem.

## Frozen design and pass rule

- Query policies: `uniform` and `variance` only. The development screen found the registered
  `decision_value` propensity paths and all reported results exactly matched `variance`, so it is
  not counted as a distinct hypothesis in this calibration.
- 72 simultaneous cells: two query policies × three context prevalences × three persistence
  values × two proxy-error rates × two label caps.
- 1,000 independent seed streams per cell, seed block `21210000–21210999`, disjoint from the
  query-policy development block `20930000–20930059` and prior recorded experiment blocks.
  The seed is reused across cells for pairing; each cell's stream outcomes are independent across
  seed IDs.
- Familywise alpha is 0.05 with simultaneous one-sided exact Clopper–Pearson limits using
  per-cell alpha `0.05/72`. Every cell must have at least 1,000 streams, an upper limit no greater
  than 0.05, a true evaluator null flag on every stream, positive propensity support, and zero hard
  cap violations. All 72 cells must pass.
- Save row-level stream results, cell summaries, protocol/source/artifact hashes and environment.
  Any run with fewer than 1,000 seeds is smoke-only and cannot pass calibration.

Passing supports only false-promotion control for this conditional Bernoulli null, the listed
Markov context family, fixed pre-monitor query policies, immediate feedback and registered split.
It does not validate delayed or informative label availability, history-adaptive allocation,
conditional-null misspecification, real data, or positive-signal utility. Failure in any cell
blocks the separate positive-signal confirmation until a new development cycle and protocol.
No figure is planned; use PaperBanana for any future figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-eventwise-calibration `
  --seeds 1000 --seed-offset 21210000 --n 3200 --d 16 --device cuda --workers 6 `
  --query-policies uniform variance `
  --protocol docs/scout_context_eventwise_query_null_calibration_protocol.md `
  --output outputs/scout_context_eventwise_query_null_calibration_1000
```
