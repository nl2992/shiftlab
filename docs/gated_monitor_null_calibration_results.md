# WP1 S2: null calibration passed

The frozen S2 null calibration passed for the primary paced gated-HT arm and every
registered panel arm, so the disjoint S3 comparison is allowed. This result controls
only the registered synthetic stationary and benign-nuisance nulls; it is not a
real-data or universal validity guarantee.

The run used 2,000 streams in each scenario/budget cell, seeds 58300000–58301999,
for stationary and benign-nuisance scenarios and budgets {.02,.05,.10,.20}.
All 16,000 registered generation tasks completed on CUDA with five CPU replay
workers in 17,948.34 seconds. It started from clean committed implementation HEAD
`fcbc54e2bce1969802885c1d7c390c8f98476cd2`. Commands:

`uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage null --workers 5`

`uv run --no-sync python scripts/analyze_gated_monitor_comparison.py --stage null`

The primary `gated_ht_paced` results were:

| Null scenario | Budget | Alarms / 2,000 | Rate | Simultaneous exact upper bound |
|---|---:|---:|---:|---:|
| stationary | .02 | 0 | 0.00% | 0.253% |
| stationary | .05 | 1 | 0.05% | 0.358% |
| stationary | .10 | 4 | 0.20% | 0.613% |
| stationary | .20 | 6 | 0.30% | 0.764% |
| benign nuisance | .02 | 0 | 0.00% | 0.253% |
| benign nuisance | .05 | 2 | 0.10% | 0.449% |
| benign nuisance | .10 | 4 | 0.20% | 0.613% |
| benign nuisance | .20 | 6 | 0.30% | 0.764% |

Every upper bound is below the registered 5% gate. Confidence families contain
the eight scenario-by-budget cells within each arm. The largest upper bound anywhere
in the complete panel was 1.953% for the PPE gated source-factor alias (24/2,000);
the next largest was 1.115% for paced gated HT with the shared fixed1 engine
(11/2,000). No arm failed calibration. Source aliases and composed/adapted engines
retain the fidelity labels fixed in the protocol; passing calibration does not turn
an adaptation into a faithful published implementation.

Independent checks matched the three run-output hashes, both analysis-output
hashes, the analysis input hash, the frozen analysis source and all key executed
sources. The complete arm/cell table is in the ignored artifact directory
`outputs/gated_monitor_null/analysis/summary.csv`. Receipts:

| Artifact | SHA-256 |
|---|---|
| launch.json | bb289a598b3cd99d9c80e20bbd90bf781039f0d86b22f431b75fc1d08c09de9c |
| manifest.json | 8594b65f5a9dce71a47627ad36f20ad57333e9d137f853efea247f1d3829ad0b |
| streams.parquet | 17b719edb2826f25fe8cf6aecf09525814f628b01464221ee417d9ae7f27e7a2 |
| analysis/summary.csv | e34483bd66d377e51d7c0c31b7301ce25b873406e29a200ebc22e3162bfdd40c |
| analysis/decision.json | 8a3b4b9770f89596f0a4e492dfca70c835823cf2be07c4e3ca0101268f607722 |

The S3 comparison was launched only after this decision was obtained. Its seeds
and outputs are disjoint. No S3 result is inferred from calibration.
