# Candidate ledger (authoritative)

| ID | Target | Mechanism | Closest prior | Strongest comparator | Development result | Decision |
|---|---|---|---|---|---|---|
| N1 evidence-adaptive pacing | M1/M3 | pace by evidence state | DE-CuSum / CuSum-AC censoring; Premkumar–Kumar | uniform e-SR | closed on the methods-strategy branch (pacing minimax: no pacer beats uniform's worst case by more than 6%; bursting trades late onsets for early ones) | **stop** (not rerun) |
| N2 economic QSG (veto gate) | M2 | payback hurdle over a valid detector | Wan et al. 2023; Chick et al. 2017 | never switch | closed on the methods-strategy branch (the hindsight-optimal gate never beats never-switch on reversal) | **stop** |
| N3 reserve / recovery QSG | M3 | label reserve for rollback | E_rb, e-SR | e-SR at full alpha | certified rollback cannot beat never-switch on these reversal regimes even in hindsight; the budget is not the binding constraint | **stop** (certified variants) |
| D1 EQS | M2 (+M1) | front-loading + Beta-LCB payback + acquisition stop + rollback | horizon-pays rule | econ+front (tuned) | best EQS 358.0 vs econ+front 357.6; econ+front already sits at the delay floor | **stop** |
| D2 EQS-D | M3 + M2 | discounted QCE counts + Beta-quantile hysteresis + decision-at-stake acquisition | Gong–Zhang; hysteresis (Dixit; Bayraktar–Ludkovski) | Qiu / Gong–Zhang | −6.1 vs Qiu; the acquisition clause failed (−0.9, n.s.) | revise → D3 |
| D3/D4 EQSDp | M3 + M2 | D2 without the acquisition coupling | tuned Gong–Zhang; point estimate + margin | tuned Gong–Zhang | frozen D2 config on fresh seeds: −6.3 vs tuned Gong–Zhang; quantile vs best margin: −6.2 to −12.7 | **advance** |
| C3 EQSDp arms A/B | M3 + M2 | frozen | — | tuned Gong–Zhang, Qiu | **PASS**: A −4.8 / −5.7, B −8.8 / −9.7 (Holm-adjusted) | → novelty audit, then C4 |
| N4 dependence-aware QSG | M4 | adaptive spacing | thinning; QSG-env | xu+front | not run (GAVE-R WP1b eliminated rho-robust extensions) | deferred |
| N5 certified fast selector | M1+M2 | certification wrapper | certified hosts | — | subsumed: under this contract, certification at alpha=.05 costs 20–100 units (D0/D1) | deprioritised |
| N6 acquisition + recovery coupling | M1+M3 | joint label schedule | Lane A calendars | — | the D2 decision-at-stake clause is a direct test: no family-level gain | **stop** at this contract |
