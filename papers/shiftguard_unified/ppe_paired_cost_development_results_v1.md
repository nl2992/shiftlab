# PPE paired decision-cost development results v1

**Status:** exploratory development only. Protocol:
[`ppe_paired_cost_development_protocol_v1.md`](ppe_paired_cost_development_protocol_v1.md).
CUDA output and seed-level metrics:
[`ppe_paired_cost_development_v1`](../../outputs/shiftguard_unified/sota_reproductions/ppe_paired_cost_development_v1/).

## Design and implementation check

The frozen 30-seed run evaluated 1,440 method-stream rows: two controls and
four alternatives, two query rates, four monitors, 30 seeds per scenario.
Synthetic generation used the NVIDIA GeForce RTX 4060 Laptop GPU with
PyTorch 2.9.1+cu130. The fixed PPE factor uses stake 0.1 and support
`[0.9, 1.1]`; the query floor is 0.18182, below both registered rates 0.20 and
0.40. The four methods shared the same stream, label path, event count, and
label spend within each scenario/seed/rate. The maximum label-cost cap was
respected.

## Findings

Across the four alternative profiles and both query rates, equal-weighted by
seed, PPE's detection rate was **66.25%**, compared with **54.58%** for the
fixed-mixture monitor, **52.08%** for predictable Kelly, and **24.58%** for
plug-in empirical Bernstein. The paired PPE-minus-fixed-mixture difference
was **+11.67 percentage points**, with a 95% seed-bootstrap interval of
**[+7.50, +15.83] points**. This pooled development contrast is unadjusted and
must not be treated as confirmatory evidence.

PPE and fixed mixture were tied at 96.7% for boundary-local harm and 100% for
harmful adaptation at query rate 0.40. At query rate 0.20, PPE detected
boundary-local harm in 26/30 streams versus 14/30 for fixed mixture, and
harmful adaptation in 30/30 versus 21/30. For recurring regimes, PPE detected
19/30 versus 11/30 at query rate 0.20 and 25/30 versus 26/30 at 0.40. All
methods detected 0/30 residual-variance streams because that profile changes
variance without crossing the registered mean-harm endpoint. This is an
expected endpoint distinction, not evidence of test failure.

There were zero PPE alarms in each 30-stream stationary or benign-nuisance
cell. However, the Bonferroni-adjusted one-sided exact 95% upper bound was
**17.49%** per cell across the 16-method/control/rate family, above the 5%
calibration target. The development sample is therefore insufficient to
establish the null operating point.

## Interpretation and next gate

These results support running the already-frozen disjoint confirmation; they
do not establish PPE superiority, statistical validity beyond its theorem
assumptions, or real-data performance. The paired-cost extension requires a
valid eventwise conditional-mean null, predictable proxy and propensity,
outcome-independent Bernoulli query selection, bounded identified paired
costs, and the same outcome revealing both policies' costs. The independent
1,000-seed-per-cell null calibration and 300-seed-per-alternative confirmation
are registered in
[`ppe_paired_cost_confirmation_protocol_v1.md`](ppe_paired_cost_confirmation_protocol_v1.md)
and are currently running. If the simultaneous null bounds fail, stop this
adaptation and diagnose the assumption mismatch before any new run.
