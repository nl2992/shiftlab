# WP1 comparator-class audit

**Date:** 2026-11-04. This post-run sensitivity preserves the registered protocol and raw records.

The registered seven-policy “best certified” panel includes `xu_acquisition_only`, which combines
Xu's acquisition with ShiftLab's test, and `choe_ramdas_eb+front`, a local Choe–Ramdas port. It also
omits `discern_design_floor`. Treat the registered best-comparator analysis as a common-contract
adapter-panel comparison, not a complete published-certificate ranking.

The strict analysis now evaluates all six members of `bench.CERTIFIED_PUBLISHED`. The originally
missing `discern_design_floor` port was replayed on all 348 real WP1 episode-seed combinations
(1,044 jobs; three seeds, original real-run seed base) and joined as a separate supplemental record
file. On the 10 late-improvement episodes, `gated_adaptive_range+front` remains the lowest-cost
published certificate port, RMM has 0/4 hosts clearing the registered interval rule, and the verdict
remains **NOT_SUPPORTED**. The comparison is selected on the same episodes and does not adjust for
selection.

The earlier delay/budget/switch-cost sensitivities used a reduced pool. This is now completed for
the six strict ports on the frozen 26 late/reversal episodes (10 late episodes, 5 source clusters;
16 reversals), with three seeds and matched seeds across policies. The additional runs evaluated
`gated_deployment`, `gated_adaptive_range`, and `discern_style`; `discern_design_floor` was already
run separately, while `gated_adaptive_range+front` and `SMCS+retain-incumbent` came from the original
sensitivity records. The six policies were merged by `(stream, episode, seed, policy)`, and duplicate
keys were rejected. Results remain descriptive and selected-subset; comparator selection is same-
sample and the RMM interval does not exclude zero in any listed setting.

| Setting | Best strict comparator (late class) | RMM gated − selected best, mean [95% cluster CI] |
|---|---|---|
| B=100 | `gated_adaptive_range+front` | −11.81 [−63.02, +75.59] |
| B=400 | `gated_adaptive_range` | −38.40 [−61.95, +3.76] |
| delay ×0.5 | `gated_adaptive_range+front` | −44.18 [−77.07, +12.76] |
| delay ×2 | `gated_adaptive_range+front` | −28.24 [−59.50, +25.82] |
| c_s=2 | `gated_adaptive_range+front` | −40.22 [−71.20, +9.93] |
| c_s=10 | `gated_adaptive_range+front` | −34.09 [−63.38, +13.74] |

These runs change one factor at a time around B=200, native delay and c_s=5. They do not cover
stationary/null episodes at altered settings, and do not expand the number of independent late source
clusters.

## Reproduction

```sh
uv run python scripts/sota_sprint/late_real.py run --streams all --policies discern_design_floor --seeds 3 --seed-base 2026110803 --workers 2 --out outputs/sprint2/WP1/strict_extra_discern_design_floor
uv run python scripts/sota_sprint/late_real.py report --primary outputs/sprint2/WP1/primary --twin outputs/sprint2/WP1/twin --sens outputs/sprint2/WP1/sens_* --supplemental outputs/sprint2/WP1/strict_extra_discern_design_floor --classes outputs/sprint2/WP1/classes.json --strict-published-subset --out docs/sprint2/wp1/strict_published_subset_20261104.json
```

The six full-panel altered-setting summaries are in `strict_published_subset_20261104.json` under
`sensitivity.sens_fullpanel_*`. Each `outputs/sprint2/WP1/sens_fullpanel_*` manifest lists its three
source runs and records exact seed, budget, delay, switch cost, and policy coverage.
