# Fixed multihorizon prior development screen

## Motivation and mathematical scope

The start-prior robustness grid showed that fixed priors can trade power when the planned horizon is
short or long. A candidate response is to hedge horizon uncertainty with a prior fixed before each
stream. For each hypothetical horizon h, let E_(h,k) be the valid bounded-mean e-process that starts
at the kth prespecified location. Given fixed horizon masses ρ_h and within-horizon start masses
w_k, define

    E_t = sum_h ρ_h sum_k w_k E_(h,k),t.

If both sets of weights are nonnegative and sum to one, this remains an e-process under the same
filtration by linearity of conditional expectation. This is a standard convex-mixture construction,
not a novelty claim. No weights change after observing data.

## Frozen design

The two hedge candidates assign equal mass to horizon scales {0.5, 1.0, 1.5} around the nominal
expected queried-label horizon q*n, with n=3,000. Within each horizon, one uses Beta(2,2) mass
over eight equal-width start bins and the other uses uniform mass. Compare these with all five
screened Beta priors at each single scale {0.5, 1.0, 1.5} and full-stream betting.

The alternative cells cross query rates {0.10,0.25,0.50}, harm onset fractions {0.20,0.60,0.80},
and paired-cost increases {0.12,0.24}. Use 200 paired streams per cell and seeds
20282000–20282199; streams are shared across methods as common random numbers. Use the existing
uniform 0–6 independent delay law for wall-clock timing. The 18 alternative cells are descriptive
development conditions, not a final test set.

For null screening, cross stationary and benign-variance nulls with the three query rates, using
500 independent streams per scenario/query cell from seeds 20284000–20284499. Calibrate both
multihorizon candidates, nominal uniform and late fixed priors, and full-stream betting. Report
one-sided exact Clopper–Pearson upper bounds with simultaneous 95% Bonferroni coverage across these
30 method/null cells. This screen does not replace final 2,000-stream calibration.

## Analysis

The primary practical contrast is each multihorizon hedge against the uniform prior at nominal
horizon. Also report the full fixed-prior grid by horizon scale. Use exact paired two-sided McNemar
tests within each of the 18 alternative cells and Holm correction across all 17 non-reference
methods × 18 cells (306 tests). Rank candidates on the unweighted macro-cell detection rate and worst-cell
detection, but treat this as development-only selection. Report event and wall-time delays
conditionally on detection; nondetections remain censored.

If a hedge improves robustness without a material power loss in any important cell, freeze it and
run a separate large null calibration and disjoint alternative confirmation before recommending it.
The guarantee requires bounded contrasts, an eventwise conditional-mean null, predictable queries,
and delays independent of current outcomes.

## Reproduction

From the repository root, run:

    uv run shiftlab-dive-horizon-hedge-sweep --device cuda --seeds-per-cell 200 --null-streams 500 --alternative-seed-offset 20282000 --null-seed-offset 20284000 --output-dir outputs/horizon_hedge_development

The runner writes stream-level Parquet/CSV metrics, cell and paired summaries, a full environment and
code-hash manifest, and checksums. No visual is required; if one is added, use PaperBanana.
