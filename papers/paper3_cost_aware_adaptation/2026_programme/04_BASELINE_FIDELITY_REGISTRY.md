# 04 Baseline fidelity registry (started by workstream A; other workstreams append)

Labels: NATIVE_SOURCE_FIDELITY / DOCUMENTED_ADAPTER / IN_HOUSE_HEURISTIC. No baseline here is a
native-source reproduction of a published method; none may be reported as "SOTA".

| id | code | label | provenance / deviation | tuned space (same 32-config budget each) |
|---|---|---|---|---|
| never | `baselines.NeverSwitch` | IN_HOUSE_HEURISTIC | reference | none |
| always | `baselines.AlwaysChallenger` | IN_HOUSE_HEURISTIC | reference | none |
| periodic | `baselines.PeriodicSwitch` | IN_HOUSE_HEURISTIC | reference | none |
| wald_paced | `baselines.WaldEconomic(acq=paced)` | DOCUMENTED_ADAPTER | arithmetic port of EQSDp arm-R-style Wald/LCB with discounting (paper1-eqsdp-foundation@5bda4e73); re-expressed on PolicyView; not the original code path | lam in [.9,.999], gamma in [.05,.5] |
| wald_cut | same + late-label cutoff `stop_h` | DOCUMENTED_ADAPTER | cutoff from stage1_policies.keep() | + stop in {5,10,15,20,30}% T |
| wald_any | same, acquisition in {paced, uniform, calendar} | DOCUMENTED_ADAPTER / IN_HOUSE (uniform, calendar) | superset search | + acq, stop in {None,...} |
| cusum | `baselines.CUSUM` | IN_HOUSE_HEURISTIC | two-sided CUSUM on released Z, paced acquisition, reset on switch | delta, h, stop |
| page_hinkley | `baselines.PageHinkley` | IN_HOUSE_HEURISTIC | same wrapper | delta, lam, stop |
| gate_wald | `baselines.Gate(Wald)` | IN_HOUSE_HEURISTIC | betting e-process gate over wald_paced; global-null validity only | Wald params, alpha in {.05,.1,.2}, lam_g in {.1,.25,.5} |
| economic_oracle | `oracle.OraclePolicy` | exact DP benchmark (known model) | not a comparator | n/a |
| A0 | `joint.policies.BeliefMPC` | IN_HOUSE_HEURISTIC | textbook online-belief MPC; Monte-Carlo rollouts; 2-regime HMM grid posterior (not a published method; closest: Chick et al. 2017, Monahan 1980 as problem class) | persist, pi0, Hmax, qmargin, amargin, base_margin |
| A1 | `QVOI` | IN_HOUSE_HEURISTIC | knowledge-gradient (KG*) style VOI over belief-grid switching DP with delay and pending queue | persist, pi0, lam_q, voi_mult, sw_margin, rho_mult |
| A2 | `Gate(QVOI)` | IN_HOUSE_HEURISTIC | core Gate over A1 | A1 space + alpha, lam_g |
| A3 | `DualPrice` | IN_HOUSE_HEURISTIC | Lagrangian-style prices + EVPI index + pacing reservation (not a proved primal-dual method) | persist, pi0, lam_q, lam_sw, kappa, eta, front, rho_mult |
| A4 | `learned.LearnedContinuation` (+Gate) | IN_HOUSE_HEURISTIC | MLP Q on causal features, TRAIN seeds dev[1000..1039] | margin_q, margin_a (+alpha, lam_g) |
| A5 | `RankReversal` | IN_HOUSE_HEURISTIC | batch action-flip probability query rule | persist, pi0, eps_flip, n_batch, h_min, sw_margin |

Fairness notes: the A-methods have more tunable dimensions (4-6) than CUSUM/PH (3), so a 32-config
random search is relatively weaker for them; this biases against A, not for it. Wald-family
baselines run in ~0.01 s/run and could be tuned far more cheaply; the budget was capped to equal
counts, not equal wall clock. Core Gate semantics (global-null only, no economic claim) apply to
every gated row.
