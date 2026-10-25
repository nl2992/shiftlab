# Delayed PPI fixed-start mixture: Markov-scale calibration results

**Calibration gate: PASS.** The exact matched-acquisition shadow design completed on 500 fresh persistent-scale Markov null streams. The two monitor cells were controlled simultaneously at familywise alpha 0.05 using Bonferroni-adjusted one-sided exact Clopper–Pearson upper limits.

| Monitor | Streams | False escalations | Rate | Simultaneous one-sided upper limit |
| --- | ---: | ---: | ---: | ---: |
| Fixed eight-start mixture | 500 | 1 | 0.20% | 1.109% |
| Full-stream predictable-bound e-process | 500 | 2 | 0.40% | 1.437% |

Both upper limits are below the registered 5% gate. All 1,000 expected monitor-stream rows had unique keys, no label-cap violations, no pending labels, and exact event counts. The full-stream query driver produced identical SHA-256 query-schedule hashes, label counts, and processed-event counts for each pair. Data generation and manifest capture used the RTX 4060 Laptop GPU; event-order monitor updates are sequential CPU work.

This finite calibration covers the primary evidence-directed query process under one Markov-persistent-scale null with fresh fair sign innovations, independent uniform delays 0–12, and the registered event-order filtration. It does not validate persistent directional signs, informative delays, changing conditional means, or real data, and Monte Carlo calibration supplements rather than replaces the e-process argument. See the frozen [protocol](delayed_evidence_ppi_start_mixture_calibration_protocol.md) and full [CSV/Parquet metrics and manifest](../outputs/delayed_evidence_ppi_start_mixture_calibration_500/).
