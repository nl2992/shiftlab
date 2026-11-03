# B2 disjoint-half comparator-selection diagnostic

`scripts/retrospective_audit/b2_crossfit_selection.py` reads the archived 500-seed `per_seed.npz` and computes equal four-world cost per seed. For each setting, it selects the lowest mean-cost P0/P1/P2 comparator on indices 0–249 and evaluates P3b on 250–499, then reverses the halves. The archived file and summary hashes, selected comparators, selection margins, and held-out reductions are recorded in `B2_DISJOINT_SELECTION_DIAGNOSTIC.json`.

| Setting | Selected in both halves | Half-selected comparator margin to runner-up (cost units) | Held-out P3b cost reductions | Historical full-sample reduction |
|---|---|---:|---:|---:|
| B200_cs5 | P2 | 3.743 / 4.275 | 10.130% / 10.273% | 10.202% |
| B200_cs20 | P0 | 2.062 / 1.665 | 9.673% / 9.617% | 9.645% |
| B400_cs5 | P2 | 6.135 / 5.708 | 7.827% / 7.927% | 7.877% |
| B400_cs20 | P0 | 1.740 / 2.107 | 7.510% / 7.835% | 7.673% |

Comparator identity is stable under this one post hoc two-fold split. This supports the narrower observation that the archived B2 average reductions do not depend on a comparator switch caused by halving these seeds. Both halves and the split design are now exposed, and P3b's design followed B1 diagnostics; these numbers are descriptive. The diagnostic does not repair the historical fixed-selected-comparator bootstrap's missing selection adjustment, test a distinct generator, change the per-world gate, or turn B2's registered **MIXED** decision into POSITIVE. A future efficacy claim needs a frozen selection/evaluation design with independent data and strong same-null comparators.
