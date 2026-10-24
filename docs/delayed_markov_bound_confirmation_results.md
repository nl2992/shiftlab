# Delayed Markov-volatility confirmation results

The frozen two-stage study ran on the NVIDIA RTX 4060 Laptop GPU. Stream generation used CUDA; the event-order monitor used the existing vectorized NumPy replay. All requested labels resolved, all tested rows respected the 480-label hard cap, and the event-prefix buffer completed without support or ordering violations.

## Independent null calibration

The calibration used 2,000 streams in each of two nonpositive-mean controls, crossed with fixed and predictable support-bound systems (four cells). Exact one-sided Clopper–Pearson upper limits use Bonferroni per-cell alpha 0.0125.

| Control | Fixed alarms / 2,000 | Predictable alarms / 2,000 | Predictable rate | Simultaneous 95% upper limit |
|---|---:|---:|---:|---:|
| Statewise exact-zero Markov null | 0 | 28 | 1.40% | 2.112% |
| Statewise strict-negative control | 0 | 25 | 1.25% | 1.930% |

The other two fixed-bound cells had zero alarms and the same exact upper limit, 0.219%. All four simultaneous upper limits were below the frozen 5% calibration gate. This is Monte Carlo evidence for the registered process and implementation; the formal guarantee remains conditional on the stated event-time martingale null and predictable-bound assumptions.

## Disjoint harm confirmation

The independent confirmation used 2,000 paired streams at each harm dose and the frozen 12-event outcome-independent delay. The primary equal-weight mean detection gain was **6.025 percentage points** (predictable minus fixed; paired stream bootstrap 95% CI **[5.325, 6.750]**), passing the +2-point gate. The predictable system used **130.264 fewer labels per stream** (95% CI **[-134.224, -126.377]**), passing the no-extra-label gate. Its evaluator-only expected exposure difference was **-22.702 cost units** (95% CI **[-25.529, -19.953]**), assuming mitigation at an alarm. That exposure is not observed or empirically prevented loss.

| Harm effect | Fixed detection | Predictable-bound detection | Paired difference |
|---:|---:|---:|---:|
| 0.04 | 0.00% | 0.65% | +0.65 pp |
| 0.20 | 0.10% | 2.00% | +1.90 pp |
| 0.40 | 1.60% | 7.90% | +6.30 pp |
| 0.60 | 5.70% | 20.95% | +15.25 pp |

The predictable system had 31 pre-onset escalations among 2,000 streams (1.55%) in each dose block; these count as nondetections in the primary endpoint. Their equality across doses follows from common random numbers and identical pre-onset data. Detection gains concentrate at the two stronger harms; the weak-dose detection rates remain low. The complete frozen retention rule passed, supporting this monitor-query system for the registered synthetic setting. The result does not isolate the bound as the sole cause because adaptive query paths differ, and it establishes no novelty or general superiority.

The exact protocols are [development](delayed_markov_bound_development_protocol.md) and [confirmation](delayed_markov_bound_confirmation_protocol.md). Stream-level Parquet, summaries, reports, code hashes, and checksums are in [development metrics](../outputs/delayed_markov_predictable_development_60/), [null calibration](../outputs/delayed_markov_predictable_calibration_2000/), and [disjoint confirmation](../outputs/delayed_markov_predictable_confirmation_2000/). No figure was generated; PaperBanana was unavailable and the numeric tables and stream metrics suffice for this result.
