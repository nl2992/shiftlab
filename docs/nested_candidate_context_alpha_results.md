# Nested candidate-by-context alpha allocation: independent validation

**Status:** calibration and confirmation passed for the registered gate-level
synthetic design. This is established weighted Bonferroni composition, not a new
testing algorithm.

## Design and assumptions

The simulator compares 13 frozen candidate utility processes. Validation outcomes
set candidate rank weights `alpha_r = alpha/[r(r+1)]`. An outcome-free pilot
sets either equal context weights or smoothed volume weights
`v_g=(n_g+0.5)/(n_0+n_1+1)`. Nested tests spend
`alpha_{r,g}=alpha_r v_g`; because candidate weights sum to less than `alpha`
and context weights sum to one, the familywise sum remains at most `alpha`.
The rank-only comparator applies the same candidate rank spending to a pooled
test. All tests use the same fixed-stake bounded e-process, independent 80%
querying, shared seed-specific gain paths, and a hard 20% or 40% label cap.

The gain processes have support `[-1,1]`; proxy context can misclassify a latent
two-group structure. The e-process relies on outcome-independent querying,
bounded gains, and the context-conditional nonpositive-mean null. Weights are
fixed before shadow outcomes. The simulator models candidate utility processes,
not fitted classifiers, real label outcomes, or data-dependent query policies.

## Development screen

The CUDA screen used 200 streams in each of 54 profile/prevalence/proxy-error/
budget settings (10,800 streams; 32,400 method rows). It covered homogeneous
benefit, two context specialists, and reversal after the shadow period; latent
prevalence was 0.1/0.5/0.9, proxy error 0/0.05/0.10, and the cap 20%/40%.

In the predeclared specialist profile, the equally weighted 18-setting average
realized-utility differences per 400-event deployment were:

| Contrast | Mean difference | Simultaneous development bootstrap interval |
|---|---:|---:|
| Nested volume − rank-only | +2.227 | [+1.343, +3.074] |
| Nested volume − nested equal | +2.187 | [+1.572, +2.857] |

Both clear the +1.0 development threshold. The result is heterogeneous: nested
volume was higher in 6/18 settings against rank-only and 6/18 against equal
context allocation; the positive macro average is not cellwise dominance.
Under homogeneous benefit, pooled rank-only promotion produced higher utility
than either nested rule at the 40% cap. Under benefit reversal, nested volume
reduced the rate of harmful future promotions relative to rank-only, while all
promoting strategies still had negative deployment value. At the 20% cap,
promotion was nearly absent across all methods.

## Independent null calibration

Calibration used 2,000 streams in each of 108 profile/prevalence/proxy-error/
cap/method cells: exact-zero nondegenerate and strict-negative nulls, three
prevalences, three proxy errors, two caps, and three allocation rules. Exact
one-sided Clopper–Pearson upper limits use simultaneous Bonferroni coverage.
All 108 cells passed the 5% upper-limit gate, all caps held, and the largest
simultaneous upper limit was **1.035%**. The largest observed streamwise
familywise crossing rate in any cell was **0.35%** (7/2,000). This checks the
simulator and implementation; the validity argument remains conditional on the
stated e-process assumptions.

## Independent confirmation

On fresh seeds, confirmation used 2,000 streams in each of the 18 specialist
profile/prevalence/proxy-error/cap settings (36,000 streams; 108,000 method
rows). The primary estimand equally averages the 18 settings. A hierarchical
paired bootstrap resampled streams within settings, with 97.5% two-sided
intervals for each of the two comparisons, giving at least 95% simultaneous
coverage. Both preregistered +1.0 margins passed:

| Contrast | Mean realized-utility difference per 400-event deployment | Simultaneous 95% interval | Gate |
|---|---:|---:|---|
| Nested volume − rank-only | +2.952 | [+2.675, +3.235] | Pass |
| Nested volume − nested equal | +2.510 | [+2.303, +2.720] | Pass |

All label caps held. At the 40% cap, mean realized deployment utility was
80.55 for nested volume, 75.54 for nested equal, and 74.62 for rank-only. At the
20% cap, promotion was virtually absent and mean utility was about −0.80 across
methods because queried-label cost remained. Utility differences were positive
in only 8/18 settings against rank-only and 9/18 against equal allocation, with
cell means ranging from −9.03 to +18.71 and −0.04 to +9.19, respectively.
The synthetic macro benefit is therefore real under the frozen target average,
but highly configuration-dependent.

## Limits and next step

Weighted Bonferroni and the fixed-stake e-process are established constructions;
the result does not establish novelty. The gate-level benchmark cannot show that
context alpha improves a fitted-model controller. The next experiment should
integrate the nested tests into the 13-candidate fitted hard-budget benchmark,
using learner-visible feature contexts and the same candidate policies, and
repeat disjoint null calibration and confirmation. Keep the global rank-only
gate and equal-context allocation as comparators. Test the entire decision rule
under the registered heterogeneity and reversal cases before making a method
claim.

Reproduce with:

```powershell
uv run shiftlab-dive-nested-candidate-context develop --output outputs/nested_candidate_context_development_200_v2 --seeds 200 --device cuda
uv run shiftlab-dive-nested-candidate-context calibrate --output outputs/nested_candidate_context_calibration_2000 --seeds 2000 --device cuda
uv run shiftlab-dive-nested-candidate-context confirm --calibration-manifest outputs/nested_candidate_context_calibration_2000/manifest.json --output outputs/nested_candidate_context_confirmation_2000 --seeds 2000 --device cuda
```

See the [protocol](nested_candidate_context_alpha_protocol.md) and the
checksummed development, calibration, and confirmation directories under
`outputs/nested_candidate_context_*`. No figure was needed; any future research
visual must be made with PaperBanana.
