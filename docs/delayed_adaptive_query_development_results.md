# Delayed feedback with predictable variance-adaptive querying: development results

**Decision:** retain the variance-adaptive rule only as a label-saving comparator for low-variance benign changes. It did not improve harmful-shift detection in this screen and should not advance as a lead intervention method.

The frozen CUDA run completed on the NVIDIA GeForce RTX 4060 Laptop GPU with 60 matched stream seeds per scenario, 3,000 target events per stream, and 12-event maximum independent delay (360 method-stream rows). Both policies used the same query-uniform stream within each seed. All 360 rows had propensities in `[0.10, 0.40]`, all 3,000 event increments entered the resolved prefix, there were no duplicate keys, and no labels remained pending. Raw metrics, runtime details, configuration, code hash, and grouped summaries are in [`outputs/delayed_adaptive_query_development_60/`](../outputs/delayed_adaptive_query_development_60/); the frozen design is [`delayed_adaptive_query_development_protocol.md`](delayed_adaptive_query_development_protocol.md).

| Scenario | Policy | Alarm rate | Mean labels queried | Mean propensity | Mean post-onset alarm delay |
| --- | --- | ---: | ---: | ---: | ---: |
| Stationary | Uniform | 1/60 (1.67%) | 750.82 | 0.250 | — |
| Stationary | Variance adaptive | 1/60 (1.67%) | 750.82 | 0.250 | — |
| Benign variance decrease | Uniform | 1/60 (1.67%) | 750.82 | 0.250 | — |
| Benign variance decrease | Variance adaptive | 1/60 (1.67%) | 516.22 | 0.171 | — |
| Boundary-local harm | Uniform | 23/60 (38.33%) | 750.82 | 0.250 | 1,234 events |
| Boundary-local harm | Variance adaptive | 23/60 (38.33%) | 750.82 | 0.250 | 1,234 events |

The paired adaptive-minus-uniform label difference on benign variance decreases was **−234.60 labels per stream** (descriptive paired-seed bootstrap 95% interval **[−238.63, −230.62]**); the mean propensity difference was −0.0788. Alarm counts were identical in this 60-seed screen. On boundary-local harm, both methods had identical query counts, alarm events, and detection: 22 alarms occurred after onset (36.67% of all streams), one alarm before onset, and 37 streams did not alarm. The conditional mean post-onset delay among the 22 alarms was 1,234 events. The variance heuristic did not increase querying after this mean shift because the generator changes the sign balance while keeping contrast magnitude fixed, so its second-moment signal is essentially unchanged.

These alarm rates are descriptive; 60 null streams per scenario are not a calibration study and cannot establish 5% error control. The adaptive rule uses fewer labels only in the registered lower-variance benign scenario. It provides no evidence of better harm detection, equal-budget efficiency, safe deployment, or novelty. The existing event-time proof supplies validity only when the conditional-mean null, predictable propensity and bound, correct randomized feedback, and resolved-prefix alarm rule hold. The next useful step is to assess the rule under a frozen and more informative variance-localized harm family only if that family represents a scientific question, and to calibrate the null before any independent positive-signal confirmation. Do not promote it based on this screen alone. No figure was generated.
