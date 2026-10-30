# 01 Validity and information audit (synthetic)

Scope: the betting e-process `X_t = theta*proxy_t + (Q_t/q_t)(r_t - theta*proxy_t) - r0 - tol`, wealth `prod(1 + lambda_t X_t)`, threshold `1/alpha`, as used by `pprm_tight` and HG in the earlier phase.

## Checklist
| question | finding |
|---|---|
| Which conditional null is used? | Marginal no-harm: `E[R_t | F_{t-1}] <= r0 + tol`, expectation over the current covariate. This implies `E[X_t | F_{t-1}] <= 0` **only** for bets `lambda_t` that are `F_{t-1}`-measurable. A covariate-conditional null `R(x) <= r0` for every `x` would be strictly stronger and is not assumed. |
| Do wagers depend on current covariates? | **Yes in the earlier implementation (a defect).** The bet cap `0.5 / (proxy_t (1/q - 1) + r0 + tol)` uses the current proxy, i.e. the current covariate. Under a marginal null with heterogeneous conditional risk, `E[lambda(x) X] > 0` can hold. |
| Does a marginal no-harm null imply the conditional inequality needed? | Not for covariate-dependent wagers (above). For wagers that are functions of the past only, yes. |
| Is there a predictable nonnegative bound on the factor? | Yes after repair: `1 + lambda X >= 1 - cap` with `lambda <= cap / (theta_t pmax (1/q_floor - 1) + r0 + tol)`, using only the declared proxy range `pmax` and the inclusion-probability floor. |
| Does label timing preserve the claimed filtration? | Fixed known delay: yes. Random delay independent of outcomes: arrival-ordered product is valid under iid-like data. **Outcome-dependent delay: the arrived-subset product is not covered**; the in-order (`prefix`) release is valid for any delay mechanism because the wealth at any time equals the event-indexed martingale at a nondecreasing random index (Ville applies to the event-indexed process). |
| Does the gate use released information only? | Yes: the HG gate uses the discounted decision-cost increments of labels that arrived strictly before the current event (`BG` buckets), tested by `test_causality_*`. |

## Exact finite-support counterexample (no simulation)
`x in {0,1}`, `P(x=1)=0.5`, proxy `h=(0.05, 0.35)`, binary loss with conditional risks re-arranged to `(0.335, 0.065)` so the marginal risk equals `r0 = 0.20` exactly. Maximal admissible bet `lambda = c/bound`. Expected betting factor per step (a valid factor needs <= 1):

| q | cap_frac | E_factor_x_cap | E_factor_sup_cap |
|---|---|---|---|
| 0.05000 | 0.25000 | 1.01221 | 1.00000 |
| 0.05000 | 0.50000 | 1.02442 | 1.00000 |
| 0.05000 | 0.90000 | 1.04396 | 1.00000 |
| 0.10000 | 0.25000 | 1.02092 | 1.00000 |
| 0.10000 | 0.50000 | 1.04185 | 1.00000 |
| 0.10000 | 0.90000 | 1.07533 | 1.00000 |
| 0.20000 | 0.25000 | 1.03164 | 1.00000 |
| 0.20000 | 0.50000 | 1.06328 | 1.00000 |
| 0.20000 | 0.90000 | 1.11391 | 1.00000 |
| 0.50000 | 0.25000 | 1.03682 | 1.00000 |
| 0.50000 | 0.50000 | 1.07364 | 1.00000 |
| 0.50000 | 0.90000 | 1.13255 | 1.00000 |

The legacy covariate-dependent cap gives `E[factor] > 1` in every cell (up to 1.13); the repaired predictable cap gives exactly 1.00000 (`tests/gap/test_engine.py::test_exact_finite_support_cap`).

## Empirical size of the defect
Forced maximal bets (adversarial), valid re-arranged design (all risks in [0,1], marginal risk = r0), 3000 paths, T=2000:

| h | q | cap_mode | fa | ci | n |
|---|---|---|---|---|---|
| [0.02, 0.6] | 0.5000 | x | 0.0640 | [0.056, 0.073] | 3000 |
| [0.02, 0.6] | 0.5000 | sup | 0.0317 | [0.026, 0.039] | 3000 |
| [0.02, 0.6] | 0.2000 | x | 0.0430 | [0.036, 0.051] | 3000 |
| [0.02, 0.6] | 0.2000 | sup | 0.0383 | [0.032, 0.046] | 3000 |
| [0.02, 0.6] | 0.1000 | x | 0.0537 | [0.046, 0.062] | 3000 |
| [0.02, 0.6] | 0.1000 | sup | 0.0343 | [0.028, 0.042] | 3000 |
| [0.02, 0.6] | 1.0000 | x | 0.0410 | [0.035, 0.049] | 3000 |
| [0.02, 0.6] | 1.0000 | sup | 0.0410 | [0.035, 0.049] | 3000 |
| [0.05, 0.35] | 0.5000 | x | 0.0373 | [0.031, 0.045] | 3000 |
| [0.05, 0.35] | 0.5000 | sup | 0.0287 | [0.023, 0.035] | 3000 |

At default Kelly plug-in bets the cap rarely binds and the measured effect was undetectable (`validity_audit.json`, `hetero_shifted=True`: 0.020 legacy cap vs 0.018 repaired). **The defect is real but mild in the earlier experiments; the repair costs nothing**: on the G1 development pool (E1, 200 seeds x 19 worlds), repaired vs legacy:

| config | power | harm_before | fa_nonharm |
|---|---|---|---|
| HG|sup|0.1 | 0.583 | 139.570 | 0.043 |
| HG|sup|0.2 | 0.844 | 88.845 | 0.084 |
| HG|x|0.1 | 0.574 | 141.734 | 0.041 |
| HG|x|0.2 | 0.841 | 90.459 | 0.084 |
| pprm_tight|sup|0.1 | 0.514 | 160.847 | 0.049 |
| pprm_tight|sup|0.2 | 0.728 | 119.131 | 0.088 |
| pprm_tight|x|0.1 | 0.489 | 163.966 | 0.045 |
| pprm_tight|x|0.2 | 0.723 | 121.159 | 0.086 |

## Dependence is the larger validity gap
Marginal-null calibration (sizes under outcome dependence that leaves the marginal source law unchanged; 1000 paths each; Wilson 95%):

| scenario | arm | fa | ci |
|---|---|---|---|
| dep_iid | pprm_sup | 0.0170 | [0.011, 0.027] |
| dep_iid | HG_sup | 0.0170 | [0.011, 0.027] |
| dep_ar0.9_s1 | pprm_sup | 0.0220 | [0.015, 0.033] |
| dep_ar0.9_s1 | HG_sup | 0.0150 | [0.009, 0.025] |
| dep_ar0.98_s1.5 | pprm_sup | 0.0260 | [0.018, 0.038] |
| dep_ar0.98_s1.5 | HG_sup | 0.0400 | [0.029, 0.054] |
| dep_cluster100_s1.5 | pprm_sup | 0.0430 | [0.032, 0.057] |
| dep_cluster100_s1.5 | HG_sup | 0.0780 | [0.063, 0.096] |

Cluster-dependent outcomes inflate HG's false-alarm rate above alpha. The reason is exactly the condition above: `E[R_t | F_{t-1}]` differs from `r0` during a cluster although `E[R_t] = r0`.

## Outcome-dependent delay (naive vs in-order release)
| scenario | arm | fa | ci |
|---|---|---|---|
| G1_null_delay=fixed | HG_arrived | 0.0190 | [0.012, 0.029] |
| G1_null_delay=fixed | HG_prefix | 0.0190 | [0.012, 0.029] |
| G1_null_delay=uniform | HG_arrived | 0.0170 | [0.011, 0.027] |
| G1_null_delay=uniform | HG_prefix | 0.0160 | [0.010, 0.026] |
| G1_null_delay=outcome | HG_arrived | 0.0260 | [0.018, 0.038] |
| G1_null_delay=outcome | HG_prefix | 0.0210 | [0.014, 0.032] |
| G1_null_delay=outcome_rev | HG_arrived | 0.0130 | [0.008, 0.022] |
| G1_null_delay=outcome_rev | HG_prefix | 0.0150 | [0.009, 0.025] |
| G1_null_delay=heavy | HG_arrived | 0.0210 | [0.014, 0.032] |
| G1_null_delay=heavy | HG_prefix | 0.0090 | [0.005, 0.017] |
| G1_null_delay=burst | HG_arrived | 0.0160 | [0.010, 0.026] |
| G1_null_delay=burst | HG_prefix | 0.0160 | [0.010, 0.026] |

No empirical difference at these settings (the naive subset product is theoretically unprotected but the effect is below 1000-path resolution). In-order release pays head-of-line blocking under heavy-tailed delays (power 0.45 vs 1.00 in `G6|concept2|delay=heavy`, see `DELAY_STRESS_RESULTS.md`).

## Decision
* Repaired configuration (`cap_mode="sup"`, `release="prefix"`) is the only one used for claims in this study.
* HG keeps its stated null: **iid-like data, bounded losses, predictable bets, known or outcome-independent label timing**. It is *not* valid under dependent outcomes (measured), and no repair with a proof is offered; the long-run-variance scaling F2 is an empirical heuristic (see `SECOND_ROUND_FIX_CANDIDATES.md`).
