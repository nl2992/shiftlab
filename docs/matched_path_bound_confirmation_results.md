# Matched-path eventwise-bound confirmation results

The frozen selected-schedule study ran on the RTX 4060 Laptop GPU, with CUDA stream generation and CPU NumPy event-order replay. The 12-event delay, frozen action pair and proxy, `q∈{0.05,0.80}` schedule, 480-label cap, stakes, and four harm doses were unchanged from the protocol. Fixed and eventwise arms shared their propensity path, requested labels, registered events, and processed event prefix on every stream. No cap, ordering, or support violation occurred.

## Independent null calibration

The calibration used 2,000 streams in each of two nonpositive-mean controls, crossed with the two bound modes. One-sided exact Clopper–Pearson limits use Bonferroni per-cell alpha 0.0125.

| Control | Bound | Alarms / 2,000 | Alarm rate | Simultaneous 95% upper limit |
|---|---|---:|---:|---:|
| Statewise exact-zero Markov null | Fixed | 15 | 0.75% | 1.31% |
| Statewise exact-zero Markov null | Eventwise | 48 | 2.40% | 3.29% |
| Statewise strict-negative control | Fixed | 10 | 0.50% | 0.98% |
| Statewise strict-negative control | Eventwise | 42 | 2.10% | 2.94% |

All four limits passed the frozen 5% gate. Eventwise betting alarmed more often than fixed betting, as expected for its tighter per-event ranges, while staying within the registered familywise limit.

## Disjoint harm confirmation

The confirmation used 2,000 paired streams per dose and the independent seed root. The equal-weight eventwise-minus-fixed detection gain was **5.4125 percentage points** (paired bootstrap 95% CI **[4.5875, 6.2500]**), exceeding the +2-point gate. Both bounds used exactly the same labels and event prefixes, so the paired label difference was identically zero (95% CI [0,0]). Evaluator-only expected exposure was **16.619 cost units lower** (95% CI **[-19.574,-13.771]**) under the assumption that an alarm immediately mitigates harm; this is not observed prevented loss.

| Harm effect | Fixed detection | Eventwise detection | Paired difference |
|---:|---:|---:|---:|
| 0.04 | 0.75% | 0.55% | -0.20 pp |
| 0.20 | 1.15% | 1.70% | +0.55 pp |
| 0.40 | 2.70% | 7.55% | +4.85 pp |
| 0.60 | 5.45% | 21.90% | +16.45 pp |

The eventwise method had 41/2,000 pre-onset alarms in every dose block (2.05%); these are nondetections in the primary endpoint. Results show the benefit is concentrated in stronger harms. Since the comparison fixes the query path, it isolates the eventwise support-bound effect for this schedule and DGP, unlike the earlier adaptive-system comparison. It does not establish superiority for arbitrary propensities, dependence, delay laws, or real-world tasks, and the betting construction is standard rather than a novel algorithm.

The registered retention rule passed. Full protocols and machine-readable evidence are in the [development protocol](matched_path_bound_ablation_protocol.md), [confirmation protocol](matched_path_bound_confirmation_protocol.md), [development grid](../outputs/matched_path_bound_ablation_60/), [null calibration](../outputs/matched_path_bound_calibration_2000/), and [confirmation](../outputs/matched_path_bound_confirmation_2000/). No visual was generated; tables and per-stream metrics fully report this result, and PaperBanana remains required for future visuals.
