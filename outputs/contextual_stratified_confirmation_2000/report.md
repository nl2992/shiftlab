# Contextual stratification independent confirmation

Status: **passed**; 2000 independent streams per scenario; seed root 91102024; device cuda.

The primary profile and criteria were fixed after the development screen: heterogeneous reversal, 80% query rate, 40% of the total two-phase stream as the hard label cap, paired 95% seed-bootstrap lower bounds above zero against both the global gate and continue, at least 0.5 harmful-group rollbacks per stream, more than 0.9 safe groups retained per stream, and no cap violations.

| comparison                      |   paired_mean |   ci95_low |   ci95_high |
|:--------------------------------|--------------:|-----------:|------------:|
| stratified - promotion_rollback |       30.5345 |    29.5355 |     31.5162 |
| stratified - continue           |       12.9957 |    11.5105 |     14.5128 |

Mean harmful groups rolled back per stream: 0.6825. Mean safe groups retained: 0.9995.

These criteria assess this registered synthetic case only. The procedures use standard Bonferroni composition of the existing gate; no novelty claim follows.
