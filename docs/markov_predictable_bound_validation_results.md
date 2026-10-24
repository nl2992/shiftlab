# Markov volatility validation results

The frozen dependent-stream validation completed on the RTX 4060 Laptop GPU with 4,000 paired stream IDs per scenario and 72,000 stream-arm rows. The seed block `27108027–27112026` is disjoint from both prior blocks. Output and source hashes are recorded in [the manifest](../outputs/markov_predictable_bound_validation/reports/manifest.json).

The registered retention rule passed. Across four equally weighted harm doses, the history-predictable query arm improved paired post-onset detection over its fixed-bound comparator by **5.66 percentage points** (95% stream-bootstrap CI **[5.19, 6.14]**), exceeding the +2-point threshold. It used **134.45 fewer labels per stream** on average (95% CI **[-137.29, -131.65]**). The evaluator-known expected exposure-cost difference was **-21.23** (95% CI **[-23.10, -19.43]**) conditional on the evaluator's latent-state path and immediate mitigation at escalation.

All six simultaneous one-sided calibration upper limits were at or below **2.43%**, below the 5% gate. On the exact-zero Markov null, false-escalation rates were 1.55% for the predictable arm, 0.075% for its fixed comparator, and 1.85% for uniform. On the strict-negative control, rates were 1.40%, 0%, and 1.575%, respectively. Each cell used 4,000 streams; exact limits use Bonferroni correction across the six control-arm cells. This is Monte Carlo evidence for the registered process, not the proof of validity.

| Aggregate harm effect | Fixed-bound detection | Predictable-bound detection | Paired gain (95% CI) | Paired label difference (95% CI) | Paired evaluator exposure-cost difference (95% CI) |
|---:|---:|---:|---:|---:|---:|
| 0.04 | 0.10% | 0.325% | +0.23 pp [+0.05,+0.40] | -130.39 [-133.28,-127.52] | -0.73 [-0.92,-0.56] |
| 0.20 | 0.35% | 1.55% | +1.20 pp [+0.80,+1.60] | -133.23 [-136.21,-130.30] | -4.58 [-5.56,-3.66] |
| 0.40 | 1.475% | 7.00% | +5.53 pp [+4.78,+6.33] | -134.73 [-137.84,-131.74] | -18.02 [-20.38,-15.75] |
| 0.60 | 6.975% | 22.65% | +15.68 pp [+14.40,+16.98] | -139.43 [-142.46,-136.38] | -61.59 [-66.23,-56.98] |

The predictable arm escalated before onset in 53/4,000 alternative streams (1.325%); the fixed-bound comparator had none. Early escalations remain non-detections in the primary outcome. Dose intervals are descriptive and unadjusted across doses. Exposure sums the state-conditional expected cost contrast through the escalation event or last processed event; it is evaluator output, not observed prevented harm.

This validation supports the registered history-only q process under this particular Markov-volatility model, where the conditional-mean null is exactly zero in each latent regime state despite persistent context and cost-square moments. It does not establish robustness to arbitrary dependence, delayed or informative labels, adaptive policies, repeated candidate selection, or interventions that alter outcomes. Query paths also differ between the fixed and predictable systems, so the result does not identify the eventwise bound as the sole cause of the gain. The method remains a standard predictable-bound e-process, with no novelty claim.

See the [frozen design](markov_predictable_bound_validation_protocol.md), [full report](../outputs/markov_predictable_bound_validation/reports/validation_results.md), and [per-stream Parquet metrics](../outputs/markov_predictable_bound_validation/metrics/stream_metrics.parquet). No figure was generated because PaperBanana was unavailable in this environment.
