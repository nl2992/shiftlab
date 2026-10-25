# Volume-weighted context-alpha confirmation results

## Primary result

The independent confirmation passed its frozen practical-gain gate. Across the nine equally weighted prevalence/proxy-noise profiles and twelve cost/budget settings, volume-weighted alpha exceeded equal alpha by **1.484 realized utility units per 800-event stream** (paired hierarchical seed-bootstrap 95% CI **[1.375, 1.597]**). The predeclared minimum was **+1.0**, one false-positive cost unit in the simulator. All per-context hard label caps held.

The mean realized utility across the full confirmation factorial was 71.840 for volume-weighted allocation and 70.355 for equal allocation. These are averages over the registered synthetic design distribution, not application estimates. Profile-level paired means ranged from -0.516 to +5.362. The weak or negative profiles occurred when harmful prevalence was 50%; therefore the aggregate result does not imply that volume weighting is better for every prevalence/noise combination. Profile means are descriptive secondary outcomes with no multiplicity adjustment.

## Independent calibration

The separate calibration used 2,000 streams in each of 54 simultaneous cells, covering both allocation rules, nine prevalence/noise settings, stationary promotion nulls, per-context least-favourable rollback boundaries, and persistent-benefit controls. Every exact one-sided Clopper–Pearson upper bound was below 5%; the maximum was **1.967%** (21 familywise rollback events among 2,000 at-risk streams). All calibration label caps held.

This finite simulation checks the implementation under the registered bounded synthetic nulls. The statistical justification remains weighted Bonferroni composition of the existing per-context anytime-valid tests, conditional on the independent outcome-free pilot and each context's bounded conditional-mean null. The calibration does not establish validity under changing partitions, serial dependence, adaptive policy selection, or selective/delayed outcomes.

## Interpretation

This confirms the volume-weighted rule's average gain over equal alpha for the frozen 108-cell heterogeneous-reversal target and its +1.0 utility margin. It does not establish cellwise superiority, utility outside the simulator, or a new algorithm. The allocation rule is standard weighted Bonferroni; the result is about when this conventional allocation helps under the registered context-frequency and utility design.

The exact protocol and commands are in [the calibration/confirmation protocol](contextual_weighted_alpha_confirmation_protocol.md). Full stream-level metrics, cell/profile contrasts, manifests, source hashes, checksums, and environment records are in [`outputs/contextual_weighted_alpha_calibration_2000/`](../outputs/contextual_weighted_alpha_calibration_2000/) and [`outputs/contextual_weighted_alpha_confirmation_2000/`](../outputs/contextual_weighted_alpha_confirmation_2000/). No figure was generated; future research visuals must use PaperBanana and be checked against these outputs.
