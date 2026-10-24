# Independent fixed-mixture monitor confirmation results

## Run and calibration

The fresh CUDA run used **2,000 streams per null scenario** and **1,000 per alternative** at 20%
querying, yielding **12,000 monitor-stream rows** for fixed-mixture and predictable-Kelly e-processes.
The new seed block is disjoint from all development blocks. The metrics checksum and all four
source hashes match the manifest. Methods received identical labels, spend, and processed-event
paths within each stream, and every hard budget was respected.

All four monitor-by-null cells had **0 false escalations out of 2,000**. With Bonferroni coverage
over those four cells, each one-sided exact 95% upper bound is **0.219%**, passing the frozen 5%
screen by a wide margin. This simulation evidence complements the conditional-mean e-process proof;
it does not replace the assumptions on the filtration, support bound, and query randomization.

## Independent power result

The fixed-mixture detector reached **56.35%** macro detection across boundary-local harm and harmful
adaptation, versus **42.95%** for predictable Kelly. The prespecified paired difference was **+13.4
percentage points**, with a seed-clustered 95% interval of **[+11.95, +14.90]** over 1,000 seed
clusters. Both scenario estimates favored the fixed mixture: **+10.1 points** for boundary-local
harm (95% interval **[+8.3, +12.0]**) and **+16.7 points** for harmful adaptation (**[+14.4, +19.0]**). The registered retention rule passed all three conditions, so retain fixed-mixture
monitoring as the primary method for this synthetic design at a 20% query rate.

The confirmation preserved the same resource path for both monitors: an average of **312 labels**,
about **$469** spend, and **1,561 events** processed per stream. It therefore supports a monitor
comparison at matched information and budget. The conclusion is limited to these two alternatives,
two synthetic nulls, this cost matrix, this materiality threshold, and immediate independent
Bernoulli labels. It is not a global optimality or novelty claim. Residual-variance harm remains an
unresolved shared failure from the broader monitor grid and needs a separate diagnostic. In the
development grid, its default-severity expected excess cost averaged about 0.117 against the 0.10
margin, so the positive signal was only about 0.017 per event. At severity 2.25 and 40% querying,
one of 36 streams detected; that tiny cell is too small to establish a severity trend. The next
diagnostic should map harm magnitude and label rate against conditional-mean signal and PPI
increment variance before proposing a monitor change.

The frozen design, retention rule, and command are in
[`risk_proxy_monitor_confirmation_protocol.md`](risk_proxy_monitor_confirmation_protocol.md).
Metrics, paired intervals, null calibration, hashes, and runtime metadata are in
[`outputs/risk_proxy_monitor_confirmation/`](../outputs/risk_proxy_monitor_confirmation/).
