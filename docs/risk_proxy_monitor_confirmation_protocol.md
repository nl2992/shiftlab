# Independent monitor confirmation protocol

## Question and frozen comparison

The development monitor grid favored the fixed stake-mixture e-process over predictable plug-in
Kelly at 20% querying for boundary-local harm and harmful adaptation. This independent run tests
whether that paired detection advantage repeats. The methods are established valid monitors; this
is a baseline confirmation, not a novelty study.

Use the same frozen training-only logistic decision-risk proxy, cost pair, 0.10 materiality margin,
support-bound construction, 2,400-event stream, 12.5% training slice, and 20% query rate as the
development comparison. Compare only `fixed_mixture` and `predictable_kelly`. The query uniforms,
queried labels, realized spend, and stopping horizon are shared within each seed/scenario.

## Independent samples and primary rule

Use 2,000 seeds per null scenario (`stationary`, `benign_nuisance`) and 1,000 per alternative
(`boundary_local_harm`, `harmful_adaptation`), beginning at seed 20405024. The null and alternative
seed ranges are disjoint from each other and from all proxy and monitor development blocks.

The primary statistic is the fixed-mixture minus Kelly detection difference, averaged equally over
the two material-harm scenarios within each seed. Form a percentile bootstrap interval by resampling
seed clusters. Scenario-specific differences and intervals are secondary and unadjusted.

Advance the fixed mixture on this protocol only when (1) all four monitor-by-null cells pass a
one-sided exact Clopper-Pearson upper bound of 5%, with Bonferroni 95% familywise coverage; (2) the
primary seed-clustered 95% interval is entirely above zero; and (3) the scenario point estimates do
not favor Kelly in either registered alternative. This is a frozen retention rule, not a test of a
general power-optimality claim.

## Validity and limits

Both processes receive the same bounded prediction-powered paired-cost estimates. Their
supermartingale guarantees require the history-conditional mean null at every event, predictable
stakes, the known global support bound, and query randomization independent of the current outcome.
The simulation checks those implementations under the registered synthetic stationary and benign
nuisance nulls; the proof remains the source of anytime validity. Labels are immediate, the policy
pair is frozen, and evaluator change parameters are withheld from the learner.

The confirmation reports detection, delay, labels, spend, processed horizon, false alarms, and
nondegenerate paired-cost variance. No plot is prespecified. Use PaperBanana for any later research
visual and verify its values against the saved metrics.

## Reproduction

```powershell
uv run shiftlab-dive-risk-proxy-monitor-confirm --device cuda --null-seeds 2000 --alternative-seeds 1000 --seed-offset 20405024 --n 2400 --output-dir outputs/risk_proxy_monitor_confirmation
```
