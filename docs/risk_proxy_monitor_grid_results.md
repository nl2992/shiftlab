# Risk-proxy monitor comparison results

## Run and integrity checks

The CUDA run used the NVIDIA GeForce RTX 4060 Laptop GPU and a seed block disjoint from the proxy
stress screen. It evaluated **1,000 streams per null scenario/query-rate cell** and **300 per
alternative cell** across two null scenarios, four harm scenarios, two query rates, and three
monitor processes. The saved Parquet contains **19,200 rows**. Its SHA-256 matches the run
manifest. Every scenario/rate/seed has all three monitors; labels, spend, and processed horizon
match across them, and all hard label-dollar caps were respected.

The null calibration covers 12 monitor-by-scenario-by-rate cells. Each recorded 0 false escalations
out of 1,000. Bonferroni-adjusted one-sided exact 95% upper bounds are **0.547%** in every cell,
well below the 5% screen threshold. The paired-cost process is nondegenerate: mean centered
paired-cost variance was **0.738** under both stationary and benign nuisance shift, while the mean
un-centered expected excess cost was **0.079**, below the 0.10 harm margin. This is finite-sample
simulation evidence under the registered synthetic designs; the validity argument still relies on
the history-conditional null, predictable bounded proxies and propensities, and outcome-independent
query randomization.

## Power findings

At 20% querying, the fixed stake mixture detected 51.7% of boundary-local harms, versus 39.3% for
predictable Kelly and 0.3% for plug-in empirical Bernstein. The paired fixed-mixture advantage over
Kelly was **12.3 percentage points** (seed-clustered 95% interval **[8.7, 16.3]**). Under harmful
adaptation it was 63.3% versus 46.0% versus 0%; the fixed-mixture/Kelly difference was **17.3
points** (**[13.3, 21.7]**). Recurring-regime detection was 22.3%, 17.7%, and 0%, respectively.

At 40% querying, fixed-mixture and Kelly detection were near ceiling on boundary harm (98.3% and
98.0%) and harmful adaptation (100% each). Plug-in empirical Bernstein reached 68.3% and 84.7% in
those cases. It also trailed on recurring regimes (31.3%, versus 89.7% for fixed mixture and 89.3%
for Kelly). All three processes detected **0/297** residual-variance-harm streams at either query
rate. More querying does not repair this shared failure mode.

All alternatives in the screen had zero pre-onset alarms, but alternative-only false-escalation
counts are not calibration evidence. The observed null rates pass the registered simultaneous
Monte Carlo screen, and all three processes retain their stated supermartingale guarantees only
under their eventwise conditional-mean nulls. Paired power intervals across the 24 alternative
cells are unadjusted; interpret scenario-level wins as development evidence, not confirmatory
selection.

## Research decision

Keep the fixed stake mixture as the primary established monitor in the tested 20% and 40% designs.
Predictable Kelly is a valid adaptive comparator, but it did not improve on the fixed mixture here.
The tested plug-in empirical-Bernstein process was markedly conservative under the large global
PPI support bound and is not a useful primary monitor for these settings. These are implementation
and design findings, not a new method or theorem.

The next confirmatory step should freeze fixed-mixture versus predictable Kelly on a fresh seed
block for boundary-local and harmful-adaptation scenarios at 20% querying, with independent null
calibration. Keep residual-variance harm as a separate stress case and investigate why paired
decision-cost evidence is uninformative there before proposing a new process. All parameters and
the reproduction command are in [`risk_proxy_monitor_grid_protocol.md`](risk_proxy_monitor_grid_protocol.md);
metrics, null calibration, paired power intervals, code hashes, and runtime manifest are in
[`outputs/risk_proxy_monitor_grid/`](../outputs/risk_proxy_monitor_grid/).

No figure was generated. Use PaperBanana for future research visuals and verify every plotted value
against the saved metrics.
