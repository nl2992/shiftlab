# EIA-930 F8 BA consistency audit

This append-only audit recomputes equal-BA contrasts from the already opened 2026 replay's `ANALYSIS.json`; it does not inspect new outcomes or change the registered analysis. Negative candidate-minus-comparator values favor the fixed challenger.

| Comparator | Equal-BA difference | Cluster-level 95% t interval | BAs favoring candidate | Leave-one-BA-out mean range |
|---|---:|---:|---:|---:|
| CAMS | -12.239 | [-19.704, -4.774] | 11/11 | [-13.016, -9.105] |
| Online LLM Picker* | -9.191 | [-14.963, -3.419] | 11/11 | [-9.885, -7.272] |

*Descriptive comparator contrast; the registered selection-aware hierarchical interval remains authoritative for the best-panel comparison. The cluster-level t intervals describe heterogeneity across these 11 BAs and are not independent-provider uncertainty. All 11 BA-level point differences favor the fixed challenger against both comparators; every leave-one-BA-out equal-BA mean remains favorable.

This strengthens within-provider consistency for the F8 fixed-challenger control. It does not establish transfer to another operator or dataset, or identify a novel method. EIA-930 remains one source cluster; labels use retrospective revisions and simulated one-hour maturity, costs are hypothetical, and four aggregate progress rows were exposed during the original replay. Full differences, hashes, and limitations are in `BA_CONSISTENCY_AUDIT.json`.
