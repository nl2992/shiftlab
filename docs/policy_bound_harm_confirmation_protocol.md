# Policy-specific-bound harmful-stream confirmation

**Protocol lock:** 2026-10-24. Run only after the independent policy-specific-bound null calibration passes its registered criterion. This is a comparison of query allocation policies, not a claim of a new monitor or a universal winner.

## Question and estimand

Under the same 20% hard label-dollar cap, does any adaptive query policy improve the probability that the fixed-mixture decision-harm monitor detects evaluator-confirmed harm relative to uniform querying, when each policy uses its own guaranteed propensity floor in the prediction-powered support bound?

The primary endpoint is detection by budget stopping among all evaluator-defined material-harm streams. A stream whose harm onset is not reached before budget exhaustion remains a nondetection and stays in the denominator. Report onset reachability separately. The statistical unit is the independently generated stream seed; time steps are not treated as independent replications.

## Frozen design

- 200 independent streams per scenario, seed block `55000000–55000199`, disjoint from prior runs and the 54M null-calibration block.
- Scenarios: `boundary_local_harm`, `recurring_regimes`, and `harmful_adaptation`. Report the material-harm denominator and onset reachability for every scenario; do not assume all generated streams qualify without checking evaluator metadata.
- Query policies: `uniform_proxy`, `variance_proxy`, `decision_value_proxy`, `cost_variance_proxy`, and `cost_stabilized_proxy`.
- Primary monitor: fixed stake-mixture e-process. Predictable-variance monitoring is a secondary established comparator; PM-EB is exploratory.
- `n=3200`, `d=16`, `epsilon=0.10`, `alpha=0.05`, target hard label-dollar budget rate `0.20`, `q_min=0.10`, `q_max=0.80`, maximum label tariff `2.5`, `common_eprocess_bound=False`.
- Uniform uses its actual propensity floor of `0.20`; each adaptive policy uses its guaranteed floor of `0.10`. Verify saved floors, realized query probabilities, and recomputed support bounds before analyzing detection.
- Use the same seed-level potential-outcome and query random numbers across policies. No tuning, seed replacement, early stopping, or threshold changes after viewing this block.
- Request CUDA for stream generation, run two independent process workers, and record the resolved device. Generate no figures; route future figures through PaperBanana when available.

## Analysis and decision rule

For the fixed-mixture primary monitor, compare each of the four adaptive policies with uniform in each of the three scenarios using one-sided exact McNemar tests on paired seed-level detection indicators. Apply Holm correction across all 12 tests at familywise `alpha=0.05`. Report all raw and adjusted p-values, detection proportions with Wilson 95% intervals, paired rate differences with seed-paired bootstrap 95% intervals, and discordant counts. Do not select a winner from unadjusted scenario-specific tests.

Also report the secondary PVA and exploratory PM-EB detection rates; delay among detections; all-stream and onset-reached denominators; realized labels and dollar spend; budget violations; monitor events processed; and stream-mean estimation RMSE. Hard dollar caps are matched, while event horizons can differ across policies, so show spend and processed events alongside detection and do not call this a pure fixed-horizon comparison. Report nondetections explicitly.

A query policy is supported as improving detection only if its Holm-adjusted one-sided test rejects in a prespecified scenario and the paired effect estimate is positive. Otherwise report the comparison as inconclusive or as no demonstrated benefit. A positive result supports only this registered simulator/cost/budget design. It does not establish superiority for real data, delayed or dependent labels, changing deployment policies, or unmeasured counterfactual costs.

## Reproduction

```powershell
uv run python scripts/analyze_policy_bound_null_calibration.py
uv run python scripts/run_policy_bound_harm_confirmation.py
uv run python scripts/analyze_policy_bound_harm_confirmation.py
uv run pytest tests/test_policy_bound_harm_confirmation.py -q
```
