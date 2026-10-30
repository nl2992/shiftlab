# Regret / cost frontiers (mean net regret over the 6 scenarios, by cost setting)
| cost | cert_gated | cert_switch | frozen | hg_switch | hysteresis | periodic_retrain | ph_switch | rolling_recal | best |
|---|---|---|---|---|---|---|---|---|---|
| all0 | 91.060 | 91.060 | 108.308 | 96.074 | 94.312 | 82.054 | 92.807 | 37.038 | rolling_recal |
| allmax | 147.165 | 147.306 | 108.308 | 150.472 | 150.767 | 192.314 | 149.789 | 132.297 | frozen |
| base | 102.594 | 102.591 | 108.308 | 107.160 | 105.913 | 107.106 | 104.539 | 58.339 | rolling_recal |
| query=0 | 92.472 | 92.469 | 108.308 | 97.108 | 95.861 | 97.054 | 94.487 | 48.288 | rolling_recal |
| query=0.05 | 143.079 | 143.076 | 108.308 | 147.368 | 146.121 | 147.314 | 144.747 | 98.547 | rolling_recal |
| retrain=0 | 102.594 | 102.591 | 108.308 | 107.160 | 105.913 | 92.106 | 104.539 | 47.089 | rolling_recal |
| retrain=0.2 | 102.594 | 102.591 | 108.308 | 107.160 | 105.913 | 152.106 | 104.539 | 92.089 | rolling_recal |
| rollback=0 | 102.545 | 102.542 | 108.308 | 107.105 | 105.760 | 107.106 | 104.345 | 58.339 | rolling_recal |
| rollback=0.2 | 102.888 | 102.737 | 108.308 | 107.327 | 106.371 | 107.106 | 105.123 | 58.339 | rolling_recal |
| switch=0 | 101.246 | 101.230 | 108.308 | 106.181 | 104.517 | 107.106 | 103.053 | 58.339 | rolling_recal |
| switch=0.01 | 101.516 | 101.502 | 108.308 | 106.377 | 104.796 | 107.106 | 103.351 | 58.339 | rolling_recal |
| switch=0.2 | 106.534 | 106.674 | 108.308 | 110.098 | 110.101 | 107.106 | 108.998 | 58.339 | rolling_recal |

* Label cost dominates (`query=0.05`: every adaptive policy costs ~40 more than at base, frozen is unaffected); with expensive labels frozen and rolling recalibration (cheap per action but label-hungry) are the frontier points.
* Retrain cost matters only for periodic retraining and rolling recalibration (trigger-based policies never retrain).
* Switch / rollback cost moves triggered policies by < 10 units across the whole mandated range, because the harm avoided per switch is ~100-200 units.
* No policy dominates across scenarios; the policy ranking at base costs is rolling recalibration < certified promotion ~ hysteresis ~ PH < HG < frozen in persistent-harm scenarios, and frozen < everything else in `no_worthwhile`.
