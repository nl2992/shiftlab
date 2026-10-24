# Contextual stratified intervention results

## Finding

The registered synthetic calibration and targeted confirmation both passed. In the heterogeneous-reversal confirmation, the context-stratified gate improved realized net utility over the global gate by **30.53** units per stream (paired seed-bootstrap 95% CI **[29.54, 31.52]**) and over continuing with the incumbent by **13.00** ([11.51, 14.51]). The average stratified utility was 13.00; the global gate averaged -17.54 and `continue` was zero by definition. The stratified gate rolled back the harmful context in **1,365/2,000** streams (0.6825 per stream on average) and retained the safe context in **1,999/2,000** streams (0.9995 per stream). It queried an average of 302.18 labels under the 320-label cap; all observed streams respected the cap.

These results support context-local intervention for this deliberately balanced and learner-visible two-context synthetic case. The gate is a standard Bonferroni composition of the existing bounded e-process, not a novel algorithm. No general superiority claim follows.

## Independent calibration

The independent 2,000-stream-per-scenario calibration used seed root `90102024`; development used `80102024`, and confirmation used `91102024`. Eight prespecified one-sided Clopper–Pearson limits each used alpha `0.00625`, so they jointly cover the family at 0.05. Every risk set contained at least 2,000 streams, all eight cells passed the registered upper-limit rule of 0.05, and every hard label cap held. False-promotion counts were 10/2,000 and 14/2,000 for the global gate under stationary and benign-nuisance nulls, and 3/2,000 and 4/2,000 for the stratified gate. False rollback was 0/2,000 at the global boundary, 1/2,000 at the stratified boundary, and 0/2,000 under persistent benefit for either method. The largest simultaneous one-sided upper limit was 1.3157%.

The false-rollback denominator is the promoted risk set. Each rollback null is tested only for the matching policy family at its own least-favourable boundary. This calibration applies to the registered synthetic distributions, bounded gain, predictable query rule, fixed policy pair, horizon, costs, and alpha allocation.

## Interpretation and limitations

The DGP makes the context label directly observable, balanced, and stable. It does not test context discovery, rare contexts, unknown groups, multiple adaptive partitions, policy retraining, or changing feedback. The utility costs are simulator controls rather than application-derived prices. The result is a controlled demonstration that one global gate can obscure opposing context-specific effects, and that a standard context-wise composition can preserve a safe context while rolling back a harmful one under this setup.

The seven-scenario development grid, full independent calibration, and full confirmation artifacts (CSV/Parquet metrics, reports, source hashes, checksums, environment and seed manifests) are in [`outputs/contextual_stratified_grid_500/`](../outputs/contextual_stratified_grid_500/), [`outputs/contextual_stratified_calibration_2000/`](../outputs/contextual_stratified_calibration_2000/), and [`outputs/contextual_stratified_confirmation_2000/`](../outputs/contextual_stratified_confirmation_2000/). The full assumptions and reproduction commands are in the [protocol](contextual_stratified_intervention_protocol.md). No visual was required. Any future research visual must use PaperBanana and be checked against those machine-readable outputs.
