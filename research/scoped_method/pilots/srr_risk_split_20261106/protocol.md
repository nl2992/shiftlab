# E-SR promotion-risk split screen

**Status:** prospective operating-point development screen; not a new-detector or novelty claim.
Freeze the candidate source and this file before the null calibration below. The candidate is one
fixed configuration, `E_srrSR:split90:gated_deployment`, with global alpha `0.0005` and
`alpha_split=0.90`. All other detector, host, acquisition, delay, and cost code is unchanged.

## Failure Atlas scenario and hypothesis

Target Failure Atlas regime: `F1_late_800` (no challenger advantage through event 799, persistent
positive advantage thereafter; horizon 2,000, label delay 100, budget 200). Calibrated E-SR at the
default 50/50 base/detector split saves cost against the applicable certificate/restart panel, but
its promotion may be delayed by reserving half of the tiny empirical alpha budget for the host
certificate. Moving 90% of that same global budget to the faster restart detector may reduce late
promotion delay without increasing empirical probability of any false promotion beyond 0.05.
This is a single prespecified adjustment. There is no threshold or split grid and no second
candidate if it fails.

The split is defined by the existing `RestartMixtureMonitor`: promotion detector level is
`alpha × alpha_split / 2^j` on the `j`th promotion, and the host base level is
`alpha × (1-alpha_split)`. E-SR itself has an ARL guarantee, not a horizon-wise probability-of-any-
false-promotion guarantee. The candidate's error target is therefore evaluated empirically under
the registered iid conditional null; no theorem is added.

## Shared contract and methods

Horizon 2,000, hard pathwise label budget 200, feedback delay 100 events, query cost 0.05, switch
cost 5, common loss streams, identical policy-visible information. The policy sees only predictions,
released queried labels, remaining budget, and its state; no evaluator regime truth.

Primary candidate: `E_srrSR:split90:gated_deployment`, alpha 0.0005. The primary baseline is the
calibrated default `E_srrSR:gated_deployment` at alpha 0.0005. Matched secondary baselines are
never-switch, PFA-SR, RMM, E_rb, E_swcert, and corrected Gated+front under the common alpha-0.05
contract. Qiu and Gong ports remain included as secondary cost references, but they are not
author-native implementations or certificate methods and failed on the previously registered
iid null screen; they cannot be used as equal-safety primary controls.

## Calibration/evaluation separation

1. **Calibration only:** Run the fixed candidate on 1,000 fresh `F0_null` seeds at seed base
   `7110601201`. Pass only if the one-sided 95% Wilson upper bound on any candidate promotion is
   at most 0.05. Do not inspect alternative-regime outputs in this step. If it fails, stop this
   candidate and leave target evaluation seeds unopened.
2. **Independent operating validation:** only after calibration passes, freeze a short amendment
   recording the observed calibration count, hash and validity decision. Then run 1,000 fresh
   `F0_null` seeds at seed base `7110601202`, plus 100 paired seeds per alternative cell at seed
   base `7110601203`.
3. **Target pass gate:** On `F1_late_800`, save at least 5 net-cost units per 1,000 events, with a
   paired two-sided 95% interval below zero, against **each** of the default calibrated E-SR and
   the applicable matched certificate/restart baselines (PFA-SR, RMM, E_rb, E_swcert, and
   never-switch). Against the fastest selector ports, report all contrasts but do not claim equal
   safety.
4. **Scope/adverse gates:** In the independent null, require the one-sided 95% Wilson upper bound
   on any promotion `<=0.05`. In `F0_better` and both `F3_reversal_800` and `F3_reversal_1200`,
   candidate mean excess cost over never-switch must be no greater than 5, and candidate must not
   cost more than the default calibrated E-SR by 5 or more. Report all failures and full cost
   decomposition.

All criteria are conjunctive. Failure ends the candidate. Passing permits only a separately frozen
real-data replay. It does not establish novelty: asymmetric alpha allocation, SR detectors, and
restart tests are established components. A result explained by a matched alpha-allocation
baseline is an existing-method application result, not a distinct method contribution.

## Reproduction

Calibration:

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:split90:gated_deployment \
  --seeds 1000 --seed-base 7110601201 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_risk_split_20261106/calibration
```

Do not run the operating validation command before the calibration passes and its amendment is
committed. The exact evaluation policy list and commands will be recorded in that amendment.
