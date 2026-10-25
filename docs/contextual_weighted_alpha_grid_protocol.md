# Contextual weighted-alpha robustness grid protocol

## Question and scope

This development grid asks whether alpha allocation across per-context promotion/rollback tests should be equal, proportional to observed context volume, or tilted toward rare contexts when context labels are noisy and intervention costs vary. All three procedures compose the existing bounded e-process by standard weighted Bonferroni. They are algorithmic comparators, not claimed novelties.

The grid is exploratory. It does not calibrate false promotion/rollback for the expanded context-noise and cost combinations, and it does not confirm a selected winner. Per-cell bootstrap intervals are unadjusted for grid search.

## Decision stream

Each stream has 400 shadow and 400 deployment events. The learner sees only a binary proxy-context label at each event. The evaluator generates a binary latent context and the outcome but does not expose latent labels or expected gains to any policy. The incumbent always predicts class 0 and the candidate always predicts class 1. With false-negative cost 5 and false-positive cost 1, paired gain is `+5` for outcome 1 and `-1` for outcome 0, so its support is `[-1,5]` and `E[g]=6 P(Y=1)-1`.

The shadow mean is +1 in both latent contexts (`P(Y=1)=1/3`). Deployment means for latent safe/harmful contexts are:

| Profile | Safe mean | Harmful mean |
|---|---:|---:|
| `heterogeneous_reversal` | +0.40 | -0.47 |
| `homogeneous_reversal` | -0.47 | -0.47 |
| `persistent_heterogeneity` | +0.40 | +0.15 |

The evaluator samples latent harmful-context prevalence `{0.05, 0.25, 0.50}` and symmetric proxy misclassification `{0, 0.05, 0.10}`. The resulting observed-proxy prevalence is `pi*(1-e)+(1-pi)*e`; the generated per-phase proxy-group count is rounded to the nearest integer. Within each observed proxy context, latent membership is drawn from the corresponding Bayes posterior. Thus, conditional on the observed group, the paired outcomes are iid with the registered group-specific mean. This supports per-context conditional-mean monitoring under the fixed partition.

An independent 500-event pre-stream pilot contains proxy-context labels only and no outcomes. Pilot counts are shared across the paired streams within a profile and are fixed before the shadow test. With counts `N_0,N_1`, allocations are equal weights `(1/2,1/2)`, volume weights proportional to `(N_j+1/2)`, and rare-protected weights proportional to `1/(N_j+1/2)`. These weights are normalized to sum to one and are fixed before any outcomes are observed. Conditional on this pilot, weighted Bonferroni remains valid if each group's e-process satisfies its bounded conditional-mean null.

Each context receives alpha `0.05*w_j`; its promotion and rollback stages each receive half. Summing across contexts and both stages gives total alpha 0.05 by Ville's inequality and the union bound. The promotion and rollback costs each vary over `{0, 0.05, 0.10, 0.20}` per context. Label price is 0.01; query probability is 0.80; shared hard caps are 20%, 40%, and 60% of the 800-event stream. Context-level query budgets are `floor(b*2*n_j)` for `n_j` events per phase and their sum cannot exceed the shared cap.

## Comparators and estimands

Methods are `continue`, one global promotion/rollback gate, and the three per-context allocation rules. All methods use paired outcome streams, common query-uniform paths across allocation, cost, and cap settings within each profile, the same overall alpha, and the same upper hard label cap. Context-stratified methods may use fewer labels because their per-context fixed budgets sum to no more than the shared cap.

Expected and realized net utility subtract the label cost and per-context promotion/rollback costs from cumulative paired gain. The evaluator-only summaries also count proxy groups with negative expected gain that were rolled back and positive-mean proxy groups retained.

The global gate is a utility comparator under these context-conditional profiles. Because the learner observes the current context and conditional paired-gain means differ across contexts, this run does not establish that the global gate's original marginal-null error guarantee remains valid here. No global-versus-stratified false-alarm comparison is claimed.

## Factorial and comparisons

The CUDA development run uses 200 seeds per cell, three profiles, three latent harmful prevalences, three proxy error rates, four intervention-cost multipliers, and three hard caps: 324 cells total. It records all five methods (324,000 stream-method rows) and nine paired comparisons per cell (2,916 contrasts). Seed-cluster bootstrap intervals use 1,000 resamples. Pairwise comparisons include each stratified rule versus global and continue, plus direct comparisons among allocation choices.

The volume-weighted rule is only a candidate for further study if it shows a practically meaningful, reproducible gain over equal allocation while satisfying a predeclared context-level error-control gate. No choice is selected from these same development intervals. Any calibration or confirmation must use new seed blocks and include the corresponding stationary and boundary nulls for every selected allocation policy.

## Reproduction

```powershell
uv run shiftlab-dive-contextual-weighted-alpha-grid --seeds 200 --seed-offset 92102024 --horizon 400 --true-harmful-prevalences 0.05 0.25 0.50 --proxy-error-rates 0 0.05 0.10 --intervention-cost-multipliers 0 1 2 4 --budget-rates 0.20 0.40 0.60 --device cuda --bootstrap-replicates 1000 --output-dir outputs/contextual_weighted_alpha_grid_200
```

Stream generation uses PyTorch CUDA when requested; the CPU path is retained. Metrics are stored as CSV and Parquet with paired contrasts, a report, code and data hashes, the exact command, and compute environment. No visual is required for the tabular grid. Any future research visual must be made with PaperBanana and checked against the saved metrics.
