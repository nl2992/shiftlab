# Adaptive PPI fixed-delay harm confirmation results

**Advancement gate: PASS.** The disjoint CUDA confirmation compared the evidence-directed query rule with uniform querying on 1,000 paired boundary-harm streams under fixed 12-event label delays. The frozen protocol and checksummed stream artifacts are in [`delayed_ppi_adaptive_fixed12_harm_confirmation_protocol.md`](delayed_ppi_adaptive_fixed12_harm_confirmation_protocol.md) and [`outputs/delayed_ppi_adaptive_fixed12_harm_confirmation_1000/`](../outputs/delayed_ppi_adaptive_fixed12_harm_confirmation_1000/).

| Query rule | Post-onset detections | Mean labels | Mean events processed |
| --- | ---: | ---: | ---: |
| Evidence-directed PPI | 82/1,000 (8.2%) | 169.867 | 2,400.000 |
| Uniform PPI | 41/1,000 (4.1%) | 471.746 | 2,360.697 |

The paired detection gain was **4.1 percentage points** (seed-paired bootstrap 95% interval **[2.2, 6.1]**); there were 69 evidence-directed-only detections and 28 uniform-only detections (one-sided exact McNemar `p=1.90e-5`). Evidence-directed querying used **301.879 fewer labels** on average (paired bootstrap interval **[−306.606, −296.962]**). Six candidate streams alarmed before onset; they remain counted as non-detections. Mean event-time delay among post-onset candidate detections was 777.7 events; mean wall-time delay was 789.6 events under the fixed 12-event feedback delay.

Every row key was unique; all 2,000 method-stream rows respected the 480-label cap, resolved all pending labels, and updated every registered event prefix. The result clears the frozen gate for this one fixed-delay boundary-harm alternative. It demonstrates better detection with fewer labels in this synthetic setting, not direct harm prevention, improvement at other shifts, robustness to persistent-sign dependence, or real-world performance. The query rule and e-process are established constructions; no novelty claim follows.

The 2,000-stream fixed-delay null calibration passed separately. It was selected to replicate one cell that missed the prior 12-cell calibration upper-limit gate; the replication validates that single cell and is not pooled with the 250-stream screen or used to claim a new simultaneous 12-cell familywise bound. No visual was generated.
