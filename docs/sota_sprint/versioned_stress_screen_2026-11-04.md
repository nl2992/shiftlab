# Versioned challenger stress screen — 2026-11-04

## Status and scope

This is exploratory development evidence, not a preregistered validation or a SOTA result. The
scenario definitions, seed base, and runner options were fixed in code before the run, but this
written protocol was added after the output was inspected. No parameter was tuned on a held-out
block because there is no held-out block in this screen.

Runner: [`scripts/sota_sprint/versioned_stress_screen.py`](../../scripts/sota_sprint/versioned_stress_screen.py).
Raw rows are local/ignored at
`outputs/sota_sprint/versioned_stress_dev_2026-11-04/records.jsonl` and
`outputs/sota_sprint/versioned_stress_reserved_dev_2026-11-04/records.jsonl`.

## Frozen setup

- 2,000 events per episode, 200-label hard cap, fixed 24-event feedback delay, and the repository
  cost contract (`CONTRACT` in `scripts/sota_sprint/bench.py`).
- Four scenarios, 100 independent seeds per scenario, base seed 2026110401 with non-overlapping
  100,000-wide scenario blocks.
- Incumbent error probability 0.40. Version 1 is active from event 0; version 2 activates at event
  800. Null uses 0.40 for both candidates. `late_better` uses 0.46 for v1 and 0.25 for v2.
  `degrade` and `recover` use 0.25 for v1 through event 649 and 0.55 afterward; v2 is 0.40 for
  `degrade` and 0.20 for `recover` after activation. Model errors are sampled independently given
  the labels; v2 copies incumbent predictions before activation.
- Compared the original per-version promotion gate against its dual promotion/rollback mode. The
  second run adds deterministic per-test label reserves: each version's version-level quota is
  split between promotion and rollback. Each label is charged once even if it updates multiple
  eligible tests. The alpha allocation remains split between the two tests as documented in the
  dual-monitor protocol.
- Each row records realized mean errors, label use, switches, decisions, and the oriented paired
  gains observed on the actual queried union. The latter is a diagnostic, not a proof of the
  conditional null.

## Results

Costs below are paired across identical stream seeds. Positive dual-minus-original differences are
worse for the dual monitor. Standard errors are descriptive episode-level Monte Carlo standard
errors; they do not adjust for scenario selection or support a confirmatory claim.

| Scenario | Original mean cost | Dual, no reserve | Difference (SE) | Dual, reserved | Difference (SE) | Rollbacks: no reserve / reserved |
|---|---:|---:|---:|---:|---:|---:|
| Null | 811.00 | 810.85 | −0.15 (0.15) | 805.60 | −5.38 (0.22) | 0 / 0 |
| Late better | 698.29 | 712.00 | +13.71 (3.93) | 759.32 | +61.03 (7.50) | 0 / 0 |
| Degrade | 823.79 | 865.17 | +41.37 (7.50) | 836.34 | −6.60 (8.32) | 4 / 0 |
| Recover | 560.50 | 570.89 | +10.39 (0.99) | 647.71 | +87.21 (11.06) | 0 / 0 |

Promotion counts out of 100 episodes (original / no-reserve dual / reserved dual) were 3 / 2 / 0
under null, 71 / 64 / 29 for late improvement, 75 / 63 / 29 under degradation, and 98 / 98 / 69
under recovery. The no-reserve rollback monitor acted in only four degradation episodes. The
reserved variant did not roll back in any scenario and missed many beneficial promotions.

The no-reserve variant used a mean 199–200 labels per episode. The reserved variant used 100.0,
111.8, 113.5, and 138.9 labels on null, late-better, degrade, and recover respectively; neither
variant exceeded 200. The reserve reduced null acquisition and false promotion in this screen, but
it cut promotion power and did not produce rollback evidence. No-reserve queried-union rollback
gains did not show reliable degradation evidence either. These results identify a budget/power
failure in this implementation, not a general impossibility result.

## Decision

Do not advance the versioned dual monitor as the promising method. Neither allocation is attractive
under this cost and delay contract: the unreserved version pays nearly the full query budget while
rarely rolling back, and the reserved version sacrifices too much promotion power without detecting
degradation. Keep it as a negative development result. The available evidence instead supports
continuing the repository's higher-value evidence-completion work and examining hard-budget,
delay-aware label acquisition only if it creates a measurable gain against valid same-contract
schedulers. A further algorithm claim needs a new protocol, disjoint seeds, strong baselines, and an
independent validity/novelty audit.

## Reproduction

```powershell
uv run python scripts/sota_sprint/versioned_stress_screen.py --seeds 100 --out outputs/sota_sprint/versioned_stress_dev_2026-11-04
uv run python scripts/sota_sprint/versioned_stress_screen.py --seeds 100 --out outputs/sota_sprint/versioned_stress_reserved_dev_2026-11-04
```
