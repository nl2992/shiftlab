# Cao comparator development findings — 2026-11-08

## Scope and reproducibility

This is a 200-seed-per-scenario synthetic **development** comparison. It is not a confirmatory result, an exact reproduction of Cao (2026), or evidence that any method meets a false-rollback guarantee. The three scenarios use frozen paired binary losses, `T=2000`, `B=200`, delay 50, query price 0.05, switch price 5, and common random numbers across policies. The challenger advantage is +0.12 throughout stationary/benign episodes; it reverses from +0.12 to -0.12 at event 1000 in the reversal scenario. The benign covariate mean shifts by +0.8 at event 900 while utility remains unchanged.

Reproduce the default run with:

```powershell
uv run python scripts/promising_directions/b3_plus_cao_comparator.py --phase dev --n-seeds 200
```

The full per-seed record and code hashes are in `outputs/b3_plus_cao_comparator/dev.json`. Each acquisition adapter feeds the existing P3b paired e-process. Cao-L uses a directional label-history sleep controller; Cao-Hybrid ORs that controller with a previous-block covariate trigger. Their paired-utility adaptations and the zero-propensity sleep behavior are fully specified in `B3_PLUS_CAO_COMPARATOR_GATE_2026-11-08.md`.

## Default P7s development comparison

Cost differences are paired P7s minus control with percentile bootstrap intervals across seeds.

| Scenario | Policy | Mean cost | Mean labels | Rollback probability | Reversal-delay RMST |
|---|---|---:|---:|---:|---:|
| stationary-positive | P7s | 261.509 | 130.7 | 0/200 | -- |
|  | Cao-L | 264.481 | 186.5 | 0/200 | -- |
|  | Cao-Hybrid | 264.509 | 187.7 | 0/200 | -- |
| abrupt reversal | P7s | 342.918 | 196.1 | 0.782 | 732.7 |
|  | Cao-L | 333.263 | 195.1 | 0.858 | 632.6 |
|  | Cao-Hybrid | 333.925 | 195.8 | 0.871 | 638.7 |
| benign covariate shift | P7s | 266.337 | 130.2 | 0/200 | -- |
|  | Cao-L | 270.425 | 187.8 | 0/200 | -- |
|  | Cao-Hybrid | 271.120 | 199.8 | 0/200 | -- |

P7s costs less in stationary-positive and benign-shift episodes, but **fails the key reversal comparison**. P7s minus Cao-L is `+9.655` (95% CI `[6.19, 13.04]`) and minus Cao-Hybrid is `+8.993` (`[5.47, 12.49]`) in reversal episodes. At reversal, 85% of episodes have the challenger deployed for P3b/P7s/hybrid (84.5% for Cao-L). Among episodes with challenger deployed at reversal, P7s has lower observed rollback probability and a longer restricted mean delay. No rollback happened before the reversal in any method. There were zero cap violations for every policy; this is expected from issue-time budget decrement and is a mechanics check, not a statistical claim.

The sentinel prototype (`P7s-sentinel`) uses a directional label-history controller to restore acquisition after sleep while retaining P7s's settled floor. It improved rollback probability to 0.818 and RMST to 678 events, but did not clear the cost comparison: mean reversal cost 337.873, versus 333.263 (Cao-L) and 333.925 (Cao-Hybrid); paired differences are `+4.610` (`[2.04, 7.32]`) and `+3.948` (`[1.41, 6.45]`). It also loses most static-state savings (stationary-positive cost 264.596). It is not selected. An e-process-triggered sentinel at `log wealth >= 0` had reversal cost 342.535, rollback probability 0.806 and RMST 728; it likewise does not pass.

Development-only sensitivity over P7s's settled-state rate found no crossing of the Cao controls: settled floors 0.25, 0.50 and 1.00 increased reversal sampling, but costs remained above both controls; lower persistence discounts (gamma 0.90 and 0.80) worsened reversal rollback metrics. An e-process-triggered sentinel at `log wealth >= 0` also failed to improve reversal performance: cost 342.535 and RMST 728, with 162.1 labels in stationary episodes versus 130.7 for P7s. These settings are exploratory and were not evaluated on confirmatory seeds; raw records are in sibling `dev_*` output folders.

## Decision

**Do not run confirmatory seeds for the current P7s method or sentinel prototype.** The existing evidence supports a narrow static-regime query-saving effect, but the method fails the registered reversal gate against the adapted controls. The next useful research step is to derive an acquisition rule that preserves a minimum audit rate while using the *already valid paired rollback e-process* as an early-warning intensity signal, then evaluate that candidate only on new development seeds against the frozen comparators. Any candidate must beat both Cao adapters on paired net cost while matching the predeclared reversal rollback limits before a confirmatory protocol is opened. Until then, no claim of SOTA superiority or relative novelty is supported.
