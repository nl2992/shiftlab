# Q3 baselines: mean net regret at base costs (120 seeds per scenario)
| policy | harmful_incumbent_delay50 | near_tied_flip | no_worthwhile | perm_beneficial | reversal | temp_beneficial |
|---|---|---|---|---|---|---|
| cert_gated | 207.1 | 53.4 | 10.1 | 184.4 | 107.4 | 53.2 |
| cert_switch | 207.1 | 53.4 | 10.1 | 184.4 | 107.4 | 53.2 |
| cert_uniform | 250.6 | 53.2 | 10.1 | 243.4 | 97.8 | 52.9 |
| frozen | 241.0 | 43.3 | 0.0 | 234.9 | 87.8 | 42.9 |
| hg_switch | 215.6 | 54.4 | 10.1 | 196.6 | 111.5 | 54.6 |
| hysteresis | 195.6 | 60.0 | 11.7 | 184.3 | 121.8 | 62.0 |
| periodic_retrain | 115.0 | 83.2 | 38.7 | 109.5 | 212.4 | 83.8 |
| ph_switch | 189.1 | 60.6 | 11.8 | 177.5 | 124.2 | 64.0 |
| rolling_recal | 40.7 | 72.9 | 40.8 | 40.6 | 73.7 | 81.2 |

Action statistics (all scenarios, base costs):

| policy | false_promotions | switches | rollbacks | labels | runtime_ms_per_seed |
|---|---|---|---|---|---|
| cert_gated | 0.00 | 0.27 | 0.01 | 101.21 | 0.68 |
| cert_switch | 0.00 | 0.27 | 0.01 | 101.21 | 0.61 |
| cert_uniform | 0.00 | 0.01 | 0.00 | 100.52 | 0.52 |
| frozen | 0.00 | 0.00 | 0.00 | 0.00 | 0.36 |
| hg_switch | 0.01 | 0.20 | 0.01 | 100.52 | 0.76 |
| hysteresis | 0.04 | 0.28 | 0.03 | 100.52 | 0.51 |
| periodic_retrain | 0.00 | 0.00 | 0.00 | 100.52 | 0.34 |
| ph_switch | 0.04 | 0.30 | 0.04 | 100.52 | 0.44 |
| rolling_recal | 0.00 | 0.00 | 0.00 | 100.52 | 0.37 |

Policies: frozen incumbent; periodic retraining (every 250 steps); rolling recalibration (every 100); Page-Hinkley-triggered promotion (threshold from the 95% null quantile of the horizon maximum, 300 null paths); HG-triggered promotion; paired-evidence-certified promotion (`cert_uniform` uniform labels, `cert_switch` disagreement-focused labels); hysteresis (PH + 20-step persistence + 150-step dwell); cost-gated certification (`cert_gated`: promote only when estimated remaining gain exceeds the switch cost). Triggered policies share one action (swap to the other model; swapping back to the previously deployed model is charged as a rollback). Exact first-promotion solver: only on the toy instance (`Q3_EXACT_ORACLE_COMPARISON.md`).
Observations: rolling recalibration has by far the lowest regret in persistent-harm scenarios at base cost but is the worst when nothing is worthwhile and when retrain cost is high; `cert_uniform` almost never certifies (cap-limited, 0.01 switches/seed) whereas disagreement-focused certification switches in ~27% of seeds at 10% labels; `cert_gated` equals `cert_switch` because costs are small relative to the gain.
