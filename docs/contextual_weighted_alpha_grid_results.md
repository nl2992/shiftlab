# Contextual weighted-alpha robustness grid results

## Development screen

The CUDA factorial completed **324,000 stream-method rows** and **2,916 paired contrasts** across 324 cells (three profiles, three latent-harm prevalences, three proxy-noise rates, four intervention-cost settings, and three hard caps), with 200 seeds per cell. All label caps were respected. The full seed-level metrics, Parquet file, paired intervals, manifest, and environment record are under [`outputs/contextual_weighted_alpha_grid_200/`](../outputs/contextual_weighted_alpha_grid_200/).

Under heterogeneous reversal, averaged across the full prevalence/noise/cost/budget grid, expected net utility was 72.15 for volume-weighted alpha, 70.71 for equal alpha, 68.10 for rare-protected alpha, 63.94 for the global gate, and 0 for continuing. The paired realized-utility contrast of volume-weighted versus equal alpha averaged **+1.53**. It was positive in 68.5% of the 108 profile cells, but cellwise unadjusted 95% intervals had a positive lower bound in only 45 cells, a negative upper bound in 8, and included zero in the remaining 55. The rare-protected rule averaged **-2.56** versus equal alpha; its per-cell interval was positive in 4 cells, negative in 59, and included zero in 45. These comparisons are exploratory and are not corrected for selecting across cells.

The behavior changed with the decision environment. Under homogeneous reversal, continuing had the highest mean utility (zero by definition); all intervention strategies lost utility on average, even though some streams were rolled back. Under persistent heterogeneity, where both contexts benefit, the global gate averaged 129.70 expected utility versus 116.90 for equal alpha and 116.61 for volume-weighted alpha. Separate gates pay for more decisions and divide evidence across groups, which can be wasteful when neither group is harmful. This supports conditional use of context-local intervention, not a universal preference for stratification.

## Mathematical status

The per-context alpha-allocation rules are standard weighted Bonferroni compositions of the existing bounded e-process. Since pilot-derived weights are nonnegative, sum to one, and are fixed using an independent outcome-free sample, each stage's familywise false-escalation probability is at most its allocated alpha under the corresponding per-context conditional-mean null and predictable query rule. The pilot is shared across paired streams, so the simulation conditions on one realized pilot per profile; it does not quantify variation from repeating pilot acquisition.

The global gate is included as a utility comparator. Context-conditional expected gains vary and the current context is learner-visible, so the old global marginal-null guarantee is not calibrated or established by this run. These are utility outcomes, not error-control evidence. The allocation variants are standard statistical constructions; no novelty claim is made.

## Decision and limits

The modest average volume-weighted edge is inconsistent across cells and has not passed an independent, selection-aware comparison. No allocation is nominated as a winner. A follow-up should first set a practically meaningful utility margin and calibrate each candidate allocation under stationary and least-favourable per-context nulls on fresh streams. If the gain over equal allocation does not clear that margin on an independent block, retain equal alpha as the simpler default.

The simulator has two groups, a fixed partition, outcome-independent proxy noise, iid binary outcomes conditional on observed context, and fixed policies. It does not establish performance under serial dependence, changing partitions, context-dependent query selection, delayed or missing labels, multiple learned groupings, or application-derived intervention costs. No figure was generated; future visuals must use PaperBanana and be checked against the saved metrics.

The design and exact reproduction command are in the [protocol](contextual_weighted_alpha_grid_protocol.md).
