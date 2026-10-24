# Independent confirmation results: history-predictable query bound

The preregistered CUDA confirmation completed on the RTX 4060 Laptop GPU with 4,000 paired stream IDs per scenario and 72,000 stream-arm rows. It used the seed block `27104027–27108026`, disjoint from development. The raw output consists of synthetic per-stream metrics only.

The candidate passed all prespecified retention gates. Its equally weighted, paired post-onset detection gain over the fixed-bound q-min 0.05 comparator across `delta={0.04,0.20,0.40,0.60}` was **3.95 percentage points** (95% paired-bootstrap CI **[3.47, 4.43]**), above the +2-point practical threshold. It used **135.46 fewer labels per stream on average** (95% CI **[-138.38, -132.52]**). Evaluator-known cumulative expected harm exposure was lower by **17.23 cost units** on average (95% CI **[-19.06, -15.50]**), under the registered assumption that an escalation triggers immediate mitigation.

All six one-sided, simultaneous 95% Clopper–Pearson calibration upper limits were at or below **2.25%**, below the 5% gate. The exact-zero mixed-sign null had 68/4,000 false escalations (1.70%) for the predictable arm, 1/4,000 (0.025%) for its fixed-bound comparator, and 61/4,000 (1.525%) for uniform. The strict-negative control had 59/4,000 (1.475%), 0/4,000, and 55/4,000 (1.375%), respectively. The familywise limits Bonferroni-adjusted across both controls and all three arms. These finite Monte Carlo results check the registered simulator; the formal guarantee still follows from the conditional-mean null and predictable-bound supermartingale argument.

| Aggregate harm effect | Fixed-bound detection | Predictable-bound detection | Paired gain (95% CI) | Paired label difference | Paired evaluator exposure-cost difference |
|---:|---:|---:|---:|---:|---:|
| 0.04 | 0.075% | 0.300% | +0.23 pp [ +0.05, +0.43 ] | -131.13 [ -134.03, -128.17 ] | -0.75 [ -0.94, -0.58 ] |
| 0.20 | 0.475% | 1.575% | +1.10 pp [ +0.73, +1.50 ] | -134.65 [ -137.73, -131.60 ] | -4.85 [ -5.85, -3.90 ] |
| 0.40 | 1.875% | 6.150% | +4.28 pp [ +3.53, +5.05 ] | -137.15 [ -140.28, -133.98 ] | -16.68 [ -19.10, -14.32 ] |
| 0.60 | 6.275% | 16.475% | +10.20 pp [ +9.00, +11.43 ] | -138.91 [ -142.03, -135.79 ] | -46.63 [ -51.01, -42.32 ] |

Dose-level intervals are descriptive and unadjusted across the four doses; the registered primary result is the equal-weight macro contrast. The predictable arm escalated before onset in 57/4,000 alternative streams (1.425%); the fixed-bound arm had none. Those early escalations remain non-detections in the primary denominator and make pre-onset cost a relevant deployment quantity. The evaluator exposure calculation does not measure realized or empirically prevented harm.

This supports the standard history-predictable bound and its registered evidence-directed query policy on this independent synthetic benchmark. It does not show that the component bound alone caused the gain: the two monitor-query systems can follow different propensity and stopping paths. It does not establish novelty, optimality, or external validity under dependent events, delayed or selective feedback, adaptive policy changes, repeated candidate search, or interventions that alter outcomes.

Reproduction and raw artifacts are in [the confirmation output directory](../outputs/history_predictable_bound_confirmation/), with the frozen design in [the protocol](history_predictable_bound_confirmation_protocol.md). The checksum manifest records code, configuration, runtime, and output hashes. No figure was generated because PaperBanana was unavailable in this environment.
