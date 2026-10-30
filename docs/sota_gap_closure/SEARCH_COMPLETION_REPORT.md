# Search completion report (Phase 9)
Counting rule: a configuration = algorithm + all hyperparameters (calibrated thresholds excluded), deduplicated by hash. Seeds, worlds and repeated runs are never counted as configurations. For engine experiments a second, **behavioural** deduplication hashes each configuration's per-seed (alarm time, label count) vectors over all worlds of its experiment; identical hashes behave identically (e.g. `rel=hard, fallback=none` equals the parent; S05 `conservative` mixtures with u < .5 all collapse to u=.5).

| quantity | count |
|---|---|
| executed registry rows, previous phase (5,999 runs) -> distinct (algorithm, params) | **281** |
| engine configurations, this phase, distinct by parameters across all experiments | **565** |
| ... counted per experiment (same configuration re-run in another experiment counted again) | 780 |
| ... behaviourally distinct within experiments (per-seed outcome hash) | 711 |
| non-engine configurations (Q2 methods x (fraction, delay), Q3 policies, S07 method x variation, S11 policies, S12 methods), distinct | **259** |
| **total distinct configurations across the programme (parameter hash)** | **1105** |

Target in the mandate: 500-1,500 distinct *compatible, scientifically meaningful* configurations. The parameter-hash total is within that range; the behaviourally distinct engine count and the fact that many S03 / S05 / S07 cells vary one dial of a single method mean the count of *genuinely different algorithms* is far smaller (the principal algorithm families are the 26 listed below). No sweep was inflated with duplicate seeds; no successive-halving was needed (cells are cheap), and the full S03 grid (432 per parent) and the S06 delay-1 / fraction-.01 cells of v2 were not run.

## Coverage by objective and family (distinct configurations)
| objective | family | distinct configurations | source |
|---|---|---|---|
| Q1 | bet adaptation / gating | 65 | gap closure |
| Q1 | bet adaptation / gating + delay handling / validity repair | 6 | gap closure |
| Q1 | bet adaptation / gating + dependence-robust bet | 4 | gap closure |
| Q1 | bet adaptation / gating / allocation | 56 | previous phase |
| Q1 | budget pacing + bet adaptation / gating | 234 | gap closure |
| Q1 | classical sequential | 81 | previous phase |
| Q1 | confidence sequence | 18 | previous phase |
| Q1 | conformal martingale | 9 | previous phase |
| Q1 | delay handling / validity repair | 4 | gap closure |
| Q1 | dependence-robust bet | 2 | gap closure |
| Q1 | label allocation | 44 | gap closure |
| Q1 | label allocation + bet adaptation / gating | 113 | gap closure |
| Q1 | label allocation + budget pacing | 4 | gap closure |
| Q1 | label allocation + budget pacing + bet adaptation / gating | 41 | gap closure |
| Q1 | reliability gating | 120 | gap closure |
| Q1 | reliability gating + bet adaptation / gating | 120 | gap closure |
| Q1 | risk evidence (Brier) | 20 | gap closure |
| Q1 | risk evidence (cost) | 3 | gap closure |
| Q1 | risk evidence (e-process) | 72 | previous phase |
| Q1 | temporal aggregation (multi-start) | 36 | previous phase |
| Q1 | unlabeled drift detector | 9 | previous phase |
| Q2 | multiple-model certification | 96 | gap closure |
| Q3 | switching / intervention policy | 20 | gap closure |
| S07 | pool-based active inference | 126 | gap closure |
| S11 | computational approximation (amortised policy) | 9 | gap closure |
| S12 | computational approximation (drift tests) | 8 | gap closure |

## Not covered (declared)
* Risk-evidence types beyond Brier / decision cost (e.g. pinball, calibration-error evidence): not implemented.
* Temporal aggregation: discounting, SR multi-start (previous phase), multi-window mixture (F3); BOCPD, ADWIN-exact: not implemented.
* Budget pacing: dynamic-programming pacing at scale: not implemented (exact toy only).
* Multiple-model certification: published SeqMCS / CAMS: not available, source-inspired only.
Per-configuration results and failures: `outputs/gap_closure/*/perseed.parquet`, registry `outputs/gap_closure/registry.sqlite`; the previous phase's registries are untouched.
