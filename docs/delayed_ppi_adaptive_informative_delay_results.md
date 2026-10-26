# Adaptive delayed PPI under outcome-dependent response times: calibration results

**Status: completed independent null calibration, 2026-10-25, CUDA.** The frozen 250-seed design crossed three outcome-dependent delay profiles with two query rules and two monitor variants. The target stream is IID with `E[Z_t | G_(t-1)] = 0 <= epsilon`. The complete protocol is [`delayed_ppi_adaptive_informative_delay_protocol.md`](delayed_ppi_adaptive_informative_delay_protocol.md); seed-level metrics, Parquet summaries, checksums, and environment manifest are under [`outputs/delayed_ppi_adaptive_informative_delay_250/`](../outputs/delayed_ppi_adaptive_informative_delay_250/).

## Calibration gate

The frozen familywise 5% gate did **not** pass: 11/12 cells passed, but the evidence-directed full-stream arm with fixed 12-event delays had 5/250 escalations (2.0%). Its Bonferroni one-sided exact upper limit was 5.66%, above the registered 5% threshold. The observed rate is not itself concerning, and this finite-sample upper-limit failure does not contradict the conditional supermartingale argument; it means this block does not empirically clear the registered gate. Do not use that cell as a calibrated arm without a fresh, larger calibration. The other evidence-directed full-stream arms had 3/250 escalations (1.2%; upper 4.41%) under each informative profile; the fixed-start mixture had 0–2/250 per profile. Uniform-query arms had 0/250 in all profiles. Those limits are finite evidence for these generators, not proof.

| Delay profile | Query rule | Monitor | Escalations | Rate | Simultaneous one-sided upper | Gate |
| --- | --- | --- | ---: | ---: | ---: | --- |
| fixed12 | evidence-directed | full stream | 5/250 | 2.0% | 5.66% | Fail |
| positive_fast | evidence-directed | full stream | 3/250 | 1.2% | 4.41% | Pass |
| positive_slow | evidence-directed | full stream | 3/250 | 1.2% | 4.41% | Pass |
| fixed12 | evidence-directed | fixed-start mixture | 2/250 | 0.8% | 3.74% | Pass |
| positive_fast | evidence-directed | fixed-start mixture | 0/250 | 0.0% | 2.17% | Pass |
| positive_slow | evidence-directed | fixed-start mixture | 2/250 | 0.8% | 3.74% | Pass |
| all three profiles | uniform | either monitor | 0/250 per cell | 0.0% | 2.17% | Pass |

No cap or event-prefix failures occurred; all 3,000 registered stream-policy rows are present and each completed its registered event prefix. The evidence-directed arms used 139–175 labels per stream on average; the uniform arms used 472 labels and some stopped before all 2,400 events after exhausting the cap. Outcome-dependent delays changed the adaptive evidence and query paths, so equal paths across profiles were neither assumed nor required. Full results include processed-event counts and wall-time alarm delays.

## Interpretation and next step

This is a null calibration of the actual adaptive replay under finite outcome-dependent delays, with the response time kept out of the current query and evidence decision. It complements the zero-proxy fixed-propensity stress screen. The unresolved full-stream/fixed-delay cell is underpowered for the registered familywise upper-limit gate, not identified as an algorithmic validity violation. Freeze a disjoint, larger calibration of that exact cell before using it in a confirmatory power comparison; do not tune its query or betting parameters on this block. Persistent-sign dependence remains outside the stated null unless a proof-backed alternative is supplied.

No visual was planned or generated.
