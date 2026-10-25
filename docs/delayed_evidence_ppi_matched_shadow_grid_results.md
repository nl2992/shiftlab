# Delayed PPI fixed-start mixture: matched-acquisition development results

**Development nomination: PASS.** On 60 fresh seed clusters, the eight-start mixture improved post-onset detection while using exactly the same query schedules, labels, and event counts as the full-stream monitor within each paired stream. All 720 expected rows were present; no cap, delayed-prefix, or schedule-hash checks failed.

For the primary evidence-directed acquisition, the start mixture detected harm in 41/180 onset-by-seed observations (22.8%) versus 33/180 (18.3%) for the full-stream monitor. The seed-cluster paired gain was **+4.44 percentage points** (descriptive 95% percentile-bootstrap interval [+1.11, +7.78]); the paired observations had nine mixture-only detections and one full-stream-only detection. Label and event counts matched exactly in every pair.

| Onset | Start mixture | Full-stream monitor | Paired gain |
| --- | ---: | ---: | ---: |
| 25% (event 600) | 30/60 (50.0%) | 26/60 (43.3%) | +6.7 pp |
| 50% (event 1,200) | 9/60 (15.0%) | 6/60 (10.0%) | +5.0 pp |
| 75% (event 1,800) | 2/60 (3.3%) | 1/60 (1.7%) | +1.7 pp |

No pre-onset alarm occurred in these alternatives. Detection delay was not uniformly improved: the mixture was slower among early-onset detections, and faster by a small amount for the middle and late onset cells. Under uniform acquisition, the corresponding detections were 84/180 for the mixture and 25/180 for the full-stream monitor; this is secondary and development-only. The absolute late-onset detection rate remains low.

The matched query driver is the full-stream process; it sets the predictable evidence-directed propensity in both arms, and sampling continues to the common horizon after an alarm. The manifest records matching SHA-256 query-schedule hashes, exact label counts, and exact event counts for each pair. This separates monitor comparison from the label-use difference observed in the preceding closed-loop screen.

This result nominates the fixed monitor for independent null calibration. It is not confirmatory evidence and does not validate an end-to-end intervention. Convex mixtures of e-processes are standard; no novelty claim is made. See the frozen [protocol](delayed_evidence_ppi_matched_shadow_grid_protocol.md) and complete [seed-level artifacts](../outputs/delayed_evidence_ppi_matched_shadow_grid_60/).
