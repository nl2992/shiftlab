# Delayed evidence-directed PPI: independent null calibration results

**Gate: PASS.** The frozen calibration completed on the independent seed block 20280000–20280999, with 1,000 streams in each of the two controls for both the selected evidence-directed candidate and uniform querying (4,000 method-stream rows total).

Each of the four cells produced **4 false escalations / 1,000 streams (0.4%)**. The one-sided Clopper–Pearson limits used the predeclared Bonferroni cell level `0.05/4=0.0125`; every simultaneous upper limit was **1.124%**, below the 5% gate. All four cells passed. The implementation audit found all expected keys and seeds, 4,000 unique rows, zero label-cap violations, zero unresolved labels, and registered event counts equal to monitor updates. Source hashes for both the calibration runner and development module match the current files.

| Control | Method | Streams | False escalations | Rate | Simultaneous one-sided upper limit |
| --- | --- | ---: | ---: | ---: | ---: |
| Stationary | Uniform PPI | 1,000 | 4 | 0.40% | 1.124% |
| Stationary | Evidence-directed PPI | 1,000 | 4 | 0.40% | 1.124% |
| Benign variance decrease | Uniform PPI | 1,000 | 4 | 0.40% | 1.124% |
| Benign variance decrease | Evidence-directed PPI | 1,000 | 4 | 0.40% | 1.124% |

This is finite Monte Carlo calibration for the registered IID synthetic controls, frozen source proxy, query curves, propensity range, pathwise request cap, and delayed event-prefix implementation. The e-process validity argument still requires the declared event-history conditional-mean null, correct predictable propensities and bounds, conditional query randomization, frozen policy pair, correct label resolution, and prefix-only alarms. This calibration says nothing about power, serial dependence, non-random missingness, changing actions, or real costs. It does not establish the candidate's superiority or novelty.

The disjoint harm confirmation protocol was frozen before these results and is now eligible to run. It tests one candidate against uniform on fresh boundary-harm streams; calibration outcomes are not used to alter the candidate. Raw metrics, exact intervals, source hashes and runtime are in [`outputs/delayed_evidence_directed_ppi_calibration_1000/`](../outputs/delayed_evidence_directed_ppi_calibration_1000/), with the frozen [protocol](delayed_evidence_directed_ppi_calibration_protocol.md).
