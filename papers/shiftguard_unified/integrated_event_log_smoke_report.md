# Integrated event-log smoke run

**Status:** one-seed CUDA engineering smoke test; not calibration or confirmation.  
**Protocol:** draft v0.4 was captured with the run. The live protocol is draft v0.5.  
**Artifacts:** [`pipeline_eventlog_smoke_v1/`](../../outputs/shiftguard_unified/integrated_development/pipeline_eventlog_smoke_v1/).

The eight-profile, seven-method runner completed all 56 method-stream trials on the RTX 4060. It wrote 179,200 learner-visible events and 179,200 evaluator-only events (3,200 per trial for each log). The Parquet schemas are explicit and versioned in the runner; the manifest records row counts, schema descriptions, checksums, hardware, and exact source snapshots.

The event audit found no observed label on an unqueried event, no queried event missing its observed label, and no evaluator record marked learner-visible. The native harmful-adaptation profile did not trigger Q1 in this seed, consistent with its onset at event 1,600 immediately after the Q1 window. The post-promotion reversal profile reached Q1 and candidate-promotion paths in some methods; a single seed cannot estimate their operating characteristics.

Focused validation passed: 11 integration/controller tests, Ruff, and mypy. The event log improves auditability and supports later replay analysis, but it does not resolve the statistical gap: the composed Q1/Q2/Q3 procedure still lacks independent end-to-end null calibration, a frozen confirmation run, and a complete applicable-baseline comparison. The run is exploratory engineering evidence only.
