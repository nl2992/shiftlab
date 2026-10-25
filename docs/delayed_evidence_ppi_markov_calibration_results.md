# Delayed evidence-directed PPI: persistent-scale null calibration results

**Gate: PASS.** The fresh 1,000-seed calibration under Markov-persistent outcome scale completed with 4 false escalations in each of the two method cells.

The regime switched with probability 0.05 and selected outcome amplitude 0.55 or 1.0. Each sign remained independent and fair conditional on the full past and current regime, so the paired-cost conditional mean was exactly zero while its conditional variance persisted. The learner did not observe the regime. The stream retained delayed feedback uniform on 0–12, the frozen source proxy, evidence-directed candidate, uniform PPI control, and 480-label cap.

| Method | Streams | False escalations | Rate | Simultaneous one-sided upper limit |
| --- | ---: | ---: | ---: | ---: |
| Uniform PPI | 1,000 | 4 | 0.40% | 1.021% |
| Evidence-directed PPI | 1,000 | 4 | 0.40% | 1.021% |

The limits use one-sided Clopper–Pearson confidence `1-0.05/2=97.5%` per cell. Both are below the predeclared 5% gate. All 2,000 expected method-stream rows were unique, every label cap held, all labels resolved, and registered event counts equaled monitor updates. The manifest source hashes match the current generator and development module.

This extends finite calibration evidence to one specific dependent-scale process. It is not evidence for arbitrary temporal dependence: the sign innovations are still conditionally independent and fair, and the conditional mean does not drift. It does not test persistent directional outcomes, outcome-informative delays, power under Markov variance, or real-data costs. It does not change the novelty status of the established evidence-directed query and bounded-mean e-process components. Raw artifacts and runtime are in [`outputs/delayed_evidence_ppi_markov_calibration_1000/`](../outputs/delayed_evidence_ppi_markov_calibration_1000/), with the frozen [protocol](delayed_evidence_ppi_markov_calibration_protocol.md).
