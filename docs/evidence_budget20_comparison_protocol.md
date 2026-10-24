# Evidence-directed allocation at a 20% hard budget: frozen comparison

**Protocol lock:** 2026-10-24, before running seeds `20373024`–`20373083`. This is a fresh
independent evaluation of a single curve fixed from the separate 10% development grid; it is not a
grid-tuning block.

## Question and estimands

At a 20% target dollar budget, does the fixed near-uniform concave evidence curve improve
boundary-local decision-harm detection over uniform querying when both use a common e-process bound
and the same pathwise dollar cap? Secondary comparisons are with residual-variance allocation,
cost-aware Neyman allocation, and cost-stabilized Neyman allocation.

The primary outcome is the difference in boundary-harm detection rates between the preselected
evidence curve and uniform, over **all** generated boundary-harm streams; a budget-censored onset
counts as a nondetection. The practical improvement threshold is +0.10. Detection conditional on
reaching onset is reported separately. Secondary outcomes are paired seed-level stream-mean RMSE,
realized spend, label count, processed horizon, detection delay, and false escalation on stationary
and benign-nuisance controls. Control counts here are diagnostic only, not calibration.

## Frozen design

- Scenarios: `boundary_local_harm` (primary), `stationary`, and `benign_nuisance`.
- Methods: `uniform_proxy`, the single preselected `evidence_curve_a0.05_p0.5`,
  `variance_proxy`, `cost_variance_proxy`, and `cost_stabilized_proxy`.
- Sixty fresh seeds per scenario, starting at `20373024`; 3,200 generated events and 16 features.
  This block does not overlap the earlier urgency grid or 20% matched-bound seed block.
- Target dollar rate `0.20`, `q_min=0.10`, `q_max=0.80`, `alpha=0.05`, harm margin `0.10`,
  maximum tariff `2.5`, and `common_eprocess_bound=True`.
- The evidence policy uses activation fraction `0.05`, urgency power `0.5`, and linear budget taper
  power `1.0`. Its exact propensity is `q_t = q_min + (q_max-q_min) *
  clip(log(E_(t-1))/log(1/alpha)+0.05,0,1)^0.5 * remaining_fraction_t`.
- Uniform, variance, and Neyman policies are calibrated only on each stream's pre-monitor
  validation segment. All methods receive identical stream seeds and per-seed query uniforms.
  The hard dollar cap is calibrated from validation tariffs and is shared within each seed/scenario;
  the runner stops before opening an event if remaining spend cannot cover the known maximum tariff.
- Generate synthetic streams on CUDA and record software, hardware, device, configuration, source
  hashes, output hashes, and seed-level metrics. Do not generate figures; PaperBanana is unavailable.

## Analysis rules

Report exact binomial intervals for detection and control alarms. Use paired seed bootstrap intervals
for RMSE differences and paired t intervals for spend, labels, and horizon. List every method's
onset reachability, cap status, and propensity range. Do not omit budget-censored streams. Do not
interpret zero alarms among 60 controls as calibration. The evidence curve only advances if it has a
positive paired detection difference with uncertainty reported and a practically credible cost or
accuracy profile; a result below +0.10 is not evidence for the registered practical improvement.
Any broader method selection among the secondary comparators requires a new independent study.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20373024 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0.05_p0.5 variance_proxy cost_variance_proxy cost_stabilized_proxy --skip-figure --output outputs/evidence_budget20_comparison_60
```
