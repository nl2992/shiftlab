# Initial offline algorithm registry

This is an implementation inventory, not a claim that every comparator is reproduced.
The source labels below apply to this branch's proposed adapters. Existing module
docstrings alone do not establish VERIFIED_REPRODUCTION. No external paper was
retrieved for this checkpoint; paper titles and dates in GOAL.md remain supplied leads.

| Family | Local evidence / reusable code | Initial adapter provenance | Verification still required |
|---|---|---|---|
| MMD | `src/shiftlab/monitoring.py:rbf_mmd_squared`; explicit unbiased quadratic formula | SOURCE_INSPIRED_BASELINE | Verify primary formula and permutation contract; linear/RFF variants pending |
| C2ST | scikit-learn installed; no adapter audited | SOURCE_INSPIRED_BASELINE (planned) | Independent train/test split, test calibration, regularization grid |
| BBSD | No adapter audited | SOURCE_INSPIRED_BASELINE (planned) | Probability representation, multiple testing, source comparison |
| CUSUM | `monitoring.py:one_sided_cusum` | LOCAL_HEURISTIC until source check | Repeated-monitoring null calibration |
| ADWIN | Optional river dependency declared | SOURCE_INSPIRED_BASELINE (planned) | Installed version, source operations, bounded-loss contract |
| Page-Hinkley | No adapter audited | SOURCE_INSPIRED_BASELINE (planned) | Separate implementation and null calibration |
| BOCPD | No adapter audited | SOURCE_INSPIRED_BASELINE (planned) | Explicit hazard, predictive likelihood, run-length normalization |
| Podkopaev-Ramdas | Existing bounded risk/e-process components in `dive/eprocess.py` | SOURCE_INSPIRED_BASELINE (planned) | Source-specific risk reference and confidence construction |
| WATCH | No verified weighted-conformal adapter located | SOURCE_INSPIRED_BASELINE (planned) | Exact weights, conformal scores, calibration and assumptions |
| PPRM | `dive/pprm_risk_monitor.py`, `tests/test_pprm_risk_monitor.py`, `docs/pprm_paired_decision_benchmark.md` | SOURCE_INSPIRED_BASELINE pending audit upgrade | Check complete source reproduction; paired-cost adaptation differs from original estimand |
| PPE | `dive/prediction_powered_evalues.py`, 6 focused tests | SOURCE_INSPIRED_BASELINE pending primary-source check | Missing-label transform checked numerically; caller must prove base null and filtration |
| Paired sequential CS | `dive/eprocess.py`, multiple existing delayed/started mixtures | LOCAL_HEURISTIC for new adapter until contract audited | Signed paired costs, label availability, multiplicity, optional stopping |
| Sequential model confidence sets | No adapter audited | SOURCE_INSPIRED_BASELINE (planned) | Source elimination rule and simultaneous coverage |
| Prediction-powered paired certification | Existing signed-cost and PPE components | LOCAL_HEURISTIC (planned hybrid) | Shared labels, multiple candidates, predictable query and bet |
| CAMS | Existing delayed comparator family referenced by supplied specification | SOURCE_INSPIRED_BASELINE (planned) | Locate exact adapter, audit feedback and regret contract |
| ASI | `dive/robust_asi_fixed_horizon.py:budgeted_probabilities`; existing paired-cost scripts | SOURCE_INSPIRED_BASELINE | Estimator contract; pool versus stream; score learning |
| Robust ASI | `dive/robust_asi_fixed_horizon.py`; focused tests | SOURCE_INSPIRED_BASELINE pending source audit | Geometric path and L2 objective implemented; no arbitrary monitoring guarantee |
| PAI | No verified adapter located | SOURCE_INSPIRED_BASELINE (planned) | Without-replacement inclusion probabilities and adaptive updating |
| Balanced Active Inference | No verified adapter located | SOURCE_INSPIRED_BASELINE (planned) | Cube method versus explicitly labeled approximate balancing |
| RPOQ | `dive/rpoq_exact.py`; exact small-instance tests | ORACLE_ONLY when supplied DGP parameters | Observable state, null model, horizon/state scaling |
| Growth-aware querying | `dive/rpoq_next/growth_alloc.py`, screen_a.py; `docs/rpoq_next/PRIOR_ART_DELTA.md` | LOCAL_HEURISTIC or ORACLE_ONLY depending inputs | Known prior-art overlap; no claim of novel growth objective |
| Switching controls | Existing `dive` and `contract` implementations | LOCAL_HEURISTIC until individual audit | Delayed pending state, rollback, intervention and compute costs |

## Negative and invalid historical evidence

The PPRM paired-decision document explicitly invalidates older block results due to
an indexing bug. Those results stay preserved and must never enter a valid-method
leaderboard. The corrected studies and their remaining power limitations must be
distinguished. The RPOQ-next prior-art delta records a close growth-oriented querying
predecessor and states that Candidate A's core idea is not new. Neither result is
overridden by this programme.

## First diagnostic adapter

`smoke_worker.py` reuses PPE and bounded-mean e-process modules with an IID Bernoulli
loss, nominal risk 0.2, immediate labels, and 20% expected query fraction. PPE's
constant nominal proxy makes its factor identical to direct IPW betting after
matching the effective coefficient. This is a numerical integration identity,
not evidence of algorithmic improvement or a faithful reproduction of a whole paper.
