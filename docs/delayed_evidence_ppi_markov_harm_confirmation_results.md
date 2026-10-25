# Delayed evidence-directed PPI: Markov-scale harm confirmation results

**Gate: PASS.** The frozen candidate was tested on 1,000 disjoint Markov-scale harm streams after the separate persistent-scale null calibration passed. The run used the RTX 4060 Laptop GPU and passed all row, cap, delayed-prefix, and source-manifest checks.

| Method | Post-onset detections | Mean labels | Mean events processed |
| --- | ---: | ---: | ---: |
| Evidence-directed PPI | 146/1,000 (14.6%) | 164.439 | 2,333.901 |
| Uniform PPI | 75/1,000 (7.5%) | 468.189 | 2,336.521 |

The paired detection gain was **7.1 percentage points** (bootstrap 95% interval [4.7, 9.5]); there were 111 candidate-only and 40 uniform-only detections (one-sided exact McNemar `p=3.2369e-9`). The candidate used **303.750 fewer labels** on average (paired bootstrap 95% interval [−307.983, −299.401]). Three candidate streams alarmed before onset. Mean events processed were similar between arms, so the label reduction was not obtained by ending the stream earlier.

The confirmation used new seeds 20292000–20292999, distinct from the Markov null-calibration block. The outcome scale followed a two-state regime switching at probability 0.05 between amplitudes 0.55 and 1.0. Sign innovations were independent conditional on regime and had conditional mean zero before onset and +0.20 after event 1,200. Feedback delays were independent uniform draws from 0–12, and the hard request cap was 480. The learner did not observe the latent regime.

This is evidence of a paired advantage for the established evidence-directed query rule in this registered synthetic family, with modest absolute detection power. It does not establish validity for persistent sign dependence, informative delays, drifting conditional nulls, adaptive action policies, or real data. The query and e-process components are established methods; no novelty claim follows. The full seed-level CSV and Parquet, result summary, runtime, calibration-manifest hash, and source hashes are in [`outputs/delayed_evidence_ppi_markov_confirmation_1000/`](../outputs/delayed_evidence_ppi_markov_confirmation_1000/), with the frozen [protocol](delayed_evidence_ppi_markov_harm_confirmation_protocol.md).
