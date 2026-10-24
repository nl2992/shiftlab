# Fixed multihorizon prior development results

The screen evaluated 18 methods over 18 alternative cells with 200 paired streams per cell and
five methods over 30 null cells with 500 streams per cell. Streams were generated on the RTX 4060
Laptop GPU. The exact executed code and metrics are checksummed in
[outputs/horizon_hedge_development/](../outputs/horizon_hedge_development/); the frozen design is
[horizon_hedge_sweep_protocol.md](horizon_hedge_sweep_protocol.md).

The center-weighted and uniform-weighted multihorizon hedges detected harm in 64.11% and 63.64% of
alternative cells. The nominal uniform prior reached 66.14%, while the nominal late Beta(2,1) prior
reached 68.31%. The center hedge was 2.03 percentage points below nominal uniform; the uniform hedge
was 2.50 points below. Both hedges had two Holm-significant losses against nominal uniform across
the 306-method-by-cell test family. This is a negative empirical result for the multihorizon hedge
under this design, despite its valid e-process construction.

The late Beta(2,1) prior at nominal horizon ranked first. It exceeded nominal uniform by 2.17
points on the macro-cell detection rate, had a worst-cell rate of 5.0% versus 3.0%, and produced
6 versus 26 total pre-onset escalations. Two of its 18 prespecified paired cell comparisons favored
it after Holm correction across the full 306-test family. Because it was selected using these
development outcomes, these gains are not confirmatory.

In the 30 null calibration cells, rates were at most 1.8% and the largest one-sided exact
Clopper–Pearson upper bound was 4.31% under simultaneous 95% Bonferroni coverage. The 500-stream
null block is a screening check, not final calibration.

## Research decision

Do not promote either horizon hedge. Freeze the standard nominal-horizon Beta(2,1) prior as the
single candidate for an independent confirmation, with uniform as the primary paired reference.
The candidate is a standard fixed mixture over valid start-time e-processes, not a novel algorithm.
The next protocol uses fresh null and alternative seeds, 2,000 streams per cell, a macro comparison
clustered by seed, and Holm-adjusted cellwise tests. If the confirmation fails its registered
criteria, retain uniform.

No figure was created. If a visual is added later, use PaperBanana as requested by the project
owner.
