# Feature-dependent intervention independent confirmation

## Entry gate and frozen design

This confirmation may run only after `outputs/feature_intervention_calibration_2000/manifest.json`
reports `status=passed`. The runner checks the calibration status, horizon, query propensity, budget,
alpha, intervention costs, and disjoint seed range before generating alternatives.

Use the development-selected mechanism-test setting `q=.80`, a 40% pathwise label cap, `H=400` per
phase, `alpha=.05` split equally across the two gates, and promotion/rollback costs `.05` in the same
units as the paired decision loss. Labels cost `.01` utility units each. Use 2,000 streams per
scenario from seed offset `78102024`, distinct from development (`76102024`) and calibration
(`77102024`). Generate with CUDA. Keep the candidate fixed before each stream.

The registered confirmation alternatives are:

- `harmful_adaptation`: candidate benefit in shadow, then candidate harm in deployment.
- `boundary_local_harm`: no candidate benefit in shadow and benefit only after the shift, testing
  the opportunity cost of frozen pre-deployment certification.
- `persistent_benefit`: benefit in both phases, testing resource cost when rollback is unnecessary.

## Endpoints and retention rules

The primary mechanism endpoint is paired expected net utility of `promotion_rollback` minus
`promotion_only` under `harmful_adaptation`, with a seed-cluster bootstrap 95% interval. Retain the
rollback mechanism for this simulator only if the lower endpoint exceeds zero and all caps are
respected. Secondary endpoints include its expected net utility versus `continue`, rollback rate and
time, promotion rate, labels, realized utility, and all matched comparisons under the other two
profiles.

End-to-end decision success is separate: it requires a positive paired utility difference versus
`continue` under harmful reversal, not merely a gain over promotion-only. If rollback reduces harm
but does not beat `continue`, report the rollback mechanism as confirmed and the integrated policy as
not utility-improving. Report all nondetections and the future-only benefit case. These alternatives
are generated only after the calibration gate passes; no parameter is tuned on these results.

## Command

```powershell
uv run shiftlab-dive-feature-intervention-confirm `
  --calibration-manifest outputs/feature_intervention_calibration_2000/manifest.json `
  --seeds 2000 `
  --seed-offset 78102024 `
  --horizon 400 `
  --query-rate 0.80 `
  --budget-rate 0.40 `
  --device cuda `
  --output-dir outputs/feature_intervention_confirmation_2000
```

The runner records the calibration-manifest hash and source hashes, paired stream metrics, summary,
seed-cluster contrasts, exact command, and environment. It generates no figures. Conclusions remain
limited to immediate randomized labels, the frozen binary policy pair, independent events, the
registered bounded cost law, and the stated simulator.
