# Radius-grid evaluator exposure endpoint

**Status: frozen development endpoint.** This endpoint tests whether validation-selected query
allocation changes downstream decision-harm exposure. It does not establish monitor calibration,
an intervention guarantee, or a new algorithm. The associated query policies and radius grid remain
those registered in [`robust_active_inference_radius_grid_protocol.md`](robust_active_inference_radius_grid_protocol.md).

## Estimand and fallback counterfactual

For event `t`, let

\[
\Delta_t = \mathbb E[C(\pi_{\mathrm{current}}(X_t),Y_t)
                 - C(\pi_{\mathrm{ref}}(X_t),Y_t)\mid X_t]
\]

be the evaluator-known expected paired decision-cost difference. The learner, acquisition policy,
and monitor cannot access `Delta_t`, the true harm onset, or oracle probabilities. Let `s` be the
registered evaluator harm-onset event relative to the monitoring stream, `a` the first primary
single-e alarm, and `m` the number of processed events. The evaluator counterfactual assumes the
reference policy is deployed immediately after the alarm event, or after the last processed event
when monitoring stops without an alarm. The event at which the fallback is triggered is included
in exposure:

\[
E_{\mathrm{fallback}} = \sum_{t=s}^{\tau}\Delta_t,
\qquad
\tau=\begin{cases}a,&a\text{ exists},\\m-1,&a\text{ does not exist and }m>0.\end{cases}
\]

Exposure is zero when the stream has no evaluator-defined harmful onset, no event is processed, or
the trigger precedes onset. The evaluator also records the full-horizon counterfactual
`E_full = sum_{t=s}^{H-1} Delta_t` and `E_full - E_fallback`, the paired excess cost avoided by
the assumed fallback. These are expected cost units, not dollars. Label spend remains a separate
budget outcome. An intervention cost is not specified by this simulator, so no net-utility score is
formed by adding incompatible units.

The endpoint treats budget stopping as an operational fallback trigger. That is an explicit
deployment assumption, not behavior currently performed by the monitor runner. It excludes the
cost of changing policies and any harm of the reference policy. False escalations and their fallback
events remain reported separately so a future intervention-cost sensitivity analysis can be added
once a defensible cost scale is specified.

## Comparisons and interpretation

Use matched generated streams, query uniforms, monitor assumptions, propensity support, and hard
label-dollar cap. Compare the six frozen radius fractions with uniform, variance, and cost-variance
querying. Report, jointly, fallback exposure, full-horizon excess cost, avoided excess cost,
false-escalation rate, onset reach, detection delay, realized label spend, labels queried, processed
events, and estimator RMSE. Treat the stream as the independent unit and cluster paired uncertainty
by seed; macro-average scenarios with equal weight. Do not interpret a lower exposure value as a
causal guarantee outside the synthetic evaluator and frozen fallback rule.

The existing 30-seed radius screen is development data and cannot be reused as an independent
confirmation set. First run the registered grid with the new endpoint as a development replay. If a
candidate is nominated, freeze its policy and intervention-cost sensitivity before collecting fresh
null-calibration and disjoint harm-confirmation streams. Require calibration under the stated null
process and report any early false fallback. Do not promote a radius based on RMSE alone or on the
new development replay.

No figure is required by this endpoint protocol. If a research visual is added later, it must be
created and checked with PaperBanana.
