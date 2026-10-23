# Multiscale betting comparison protocol

## Candidate and guarantee

The current bounded-mean e-process mixes stakes `(0.05, 0.10, 0.20, 0.40, 0.80)`. Compare it with a fixed equal-weight mixture of 13 geometrically spaced stakes from `1/1024` to `0.99`. For bounded increments `X_t` satisfying `|X_t| <= B` and the conditional-mean null `E[X_t | F_{t-1}] <= 0`, each component

```text
E_t(eta) = product_{s <= t} (1 + eta * X_s / B)
```

is a nonnegative supermartingale for fixed `eta in (0, 1]`. Any fixed convex mixture of these components is also a nonnegative supermartingale, so Ville's inequality gives the same `alpha` crossing control under the stated assumptions. Expanding the stake support changes power across effect scales, not validity. It does not establish the assumptions for a data stream.

## Locked comparison

Evaluate both mixtures on exactly the same prediction-powered increments, query indicators, streams, policy versions, alpha, bound, and hard budget. Use a fresh 60-seed block with 60 seeds per scenario across `boundary_local_harm`, `residual_variance`, `recurring_regimes`, and `harmful_adaptation`; compare all five existing allocation policies. Do not select or retune the stake prior from these test outcomes. Include fixed and multiscale detection rates, onset reachability, false escalations, and paired seed-level detection discordances. Report descriptive uncertainty and make no general power or novelty claim.

The harmful-scenario run uses `n=3200`, `d=16`, a 20% validation-tariff budget, propensities `[0.10, 0.80]`, common e-process bounds, CUDA generation, and seed offset `20364022`. Its outputs are in `outputs/hard_budget_multiscale_stakes_60/`. A matched 60-seed run with the same seed offset covers `stationary` and `benign_nuisance`; completed outputs are in `outputs/hard_budget_multiscale_null_controls_validated_60/`. Detection outcomes are paired by seed and policy. For aggregate uncertainty, cluster on seed across all four harmful scenarios and five policies rather than treating those 20 outcomes per seed as independent.
