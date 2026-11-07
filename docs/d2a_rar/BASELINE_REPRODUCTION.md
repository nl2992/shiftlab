# Baseline reproduction record

One section per baseline; each agent appends its own section (do not edit others').

---

## The Challenger — GSE / OSE / LSE (WP1c agent, 2026-11-07) — tier `PAPER_RECONSTRUCTION`

Paper: arXiv 2512.18390 (HTML). Author code: **none found** (HTML windows 0–219k scanned; last ~19k chars unread). Implementation:
`src/shiftlab/sota/challenger/{values,algorithms}.py`; tests `tests/d2a_rar/test_challenger.py` (12 tests, all pass:
`PYTHONPATH=<worktree>/src python -m pytest tests/d2a_rar/test_challenger.py -q`).

### What is implemented
Value formulas (Eq. 2, ΔV, discounted Remark 2.4), oracle V_ORACLE, Thm 3.1 stopping rule, Prop 3.2 asymptotic t†, GSE (Alg 1), OSE (Alg 2),
LSE (w=3) / LSEc (w=2) (Alg 3), with causal per-epoch deciders. Gap estimates Ĝ_k are *inputs* (the caller trains the challenger on (1−ρ)N and
estimates on ρN holdout; no learner is bundled).

### Reproduction vs paper
| Item | Paper | This repo | Status |
|---|---|---|---|
| ΔV = V_switch − V_discard = −c_s + n(T−t)(G−c) | Eq. 2 and text | unit test, exact | MATCH (algebraic) |
| Thm 3.1: stopping rule = argmax of (T−t)G(t); feasibility iff max Φ ≥ cT + c_s/n | theorem | brute-force check on 3 (T,α,g0) settings, unit-step grids | MATCH |
| Prop 3.2: t† ~ (g0αT/(g* n^α))^{1/(1+α)} (α=0.5, n=10, g*=0.10, g0=0.9, c=c_s=0) | asymptotic | oracle integer epoch / t†: T=1e3 → 1.091, 1e4 → 1.040, 1e5 → 1.019, 1e6 → 1.009 | CONSISTENT (ratio → 1 monotonically, ~T^{1/(1+α)} scaling) |
| Remark 4.3: LSEc slope ≥ unadjusted two-point slope | stated | unit test on 2 gap paths | MATCH |
| GSE decision cases, OSE sign rule, LSE no-look-ahead | Algs 1–3 | unit tests | MATCH to the transcribed rules |
| Qualitative claim (abstract): "GSE can discard prematurely, LSE near-oracle/more stable" | prose | stylised Monte Carlo below | SUPPORTS direction only |
| Lending Club numbers (oracle ≈ epoch 4 for E.1 LR, ≈ epoch 6 for E.2 LightGBM; regret tables) | Sec 5 | **not reproduced**: dataset not downloaded, tables not retrieved | NOT REPRODUCED |
| Discounted stopping rule Thm 7.3 / Prop 7.4 | appendix | not implemented | NOT IMPLEMENTED |

### Stylised Monte Carlo (own construction, NOT a paper result)
G(N) = 0.05 − 0.6·N^{−1/2}, n=1, T=163 400, paper epoch schedule N ∈ {500,1500,3500,7500,15500,31500,63500,127500}, ρ=0.5,
Ĝ_k = G + N(0,1)·sd/√(ρN_k), 2000 reps, seed 0; regret = V_ORACLE − realised (switch → V_switch at stop epoch; discard → V_discard). Oracle epoch index 3 (4th).
Mean regret (P(switch)): sd=1, c=0.0025 — GSE γ=1.92: 509 (0.98); GSE γ=0.1: 3974 (0.66); OSE@4: 60 (0.99); LSE: 1589 (0.82); LSEc γ=0.1: 809 (1.00).
sd=3, c=0.0025 — GSE γ=1.92: 3267 (0.66); GSE γ=0.1: 4412 (0.55); OSE@4: 1287 (0.80); LSE: 3021 (0.57); LSEc: 1332 (0.96).
(c=0.01 rows: same ordering; reproduce with `PYTHONPATH=src python scripts/d2a_rar/challenger_stylised_mc.py`.) Reading: GSE with a too-small γ discards often (P(switch) 0.55–0.66) as the paper warns; LSEc is far less γ-sensitive than GSE
and beats LSE(w=3); OSE is best here only because it is fixed at the oracle epoch (the paper notes OSE needs the epoch to match the T^{2/3} scale). GSE with the paper's tuned γ=1.92 beat LSEc at sd=1,
so the paper's "LSEc near-oracle/stable" claim is **not reproduced as an across-the-board ordering** in this stylised setting — only the γ-sensitivity direction is. This is a smoke check on an invented learning curve, not evidence for or against the paper.

### Interpretation choices (UNVERIFIED against the paper)
(a) LSE least-squares slope regresses gaps on training counts (1−ρ)N; (b) "gaps decrease across the window" implemented as last < first; (c) LSEc uses δ_k at both endpoints
(as printed in the retrieved text; δ_{k−1} on the earlier endpoint would make the slope larger); (d) <2 observed epochs ⇒ continue; (e) no slope floor; (f) GSE ρ default 0.5 (inferred; paper text did not state it);
(g) epoch schedule Λ, λ are not given in the retrieved text. Differences in any of these can change epoch-level decisions.

### Use in the benchmark
Native-setting baseline for *promotion timing of a learning challenger* (output: promotion). No null; scored by realised economic value vs oracle, never by false-promotion rates.


---

## Sethi et al. sequential Markov test (WP1d, 2026-11-07) - tier `PAPER_RECONSTRUCTION` (+ `COMMON_CONTRACT_PORT` sentinel)

Paper: PMLR 306 (sethi26a), PDF read incl. App. B.3/B.5/G; author code not read or run. Code `src/shiftlab/sota/sethi/`; tests `tests/d2a_rar/test_sethi.py`
(`PYTHONPATH=<worktree>/src python -m pytest tests/d2a_rar/test_sethi.py -q`); contract port `src/shiftlab/bench/contract/adapters_sethi.py` (monitor-chain stationarity sentinel, claimed null `none`).
Full table, conditions and open items: `baselines/SETHI.md` (bottom). Headline: Alg 1 reproduced exactly (beta_t, eps_t verified against Lemma B.6); App. G.1 matrices recomputed (pi_bad matches to 4 digits);
Q_good 0/100 false rejections at alpha=.05 (paper: none in 100), Q_bad 20/20 rejections, mean tau 2531 (slope D^M_inf = 0.0471 consistent with the boundary at t~2500). Tables 2-3, Mountain Car, Fields et al. NOT reproduced.
The inner infimum is solved through the Lagrangian dual (lower bound), so numerical error can only delay rejection. alpha-correctness MC tests have weak power because the boundary is conservative.

## Active statistical inference, mean estimator (WP1d, 2026-11-07) - tier `PAPER_RECONSTRUCTION` (native) / `COMMON_CONTRACT_PORT` (streaming)

Paper: arXiv 2403.03208 PDF incl. App. A (Ass. 1-3) and App. C; WSR arXiv 2010.09686 Thm 2 for the betting CS; author code not read or run. Code `src/shiftlab/sota/asi/`; tests `tests/d2a_rar/test_asi.py`;
port `src/shiftlab/bench/contract/adapters_asi.py` (claimed null `cond`, ours, MC-validated only). Details in `baselines/ASI.md` (bottom).
Batch (n=3000, n_b=300, 500 trials, alpha=.1): coverage active .932 / PPI .914 / classical .914; widths .0841 / .0890 / .0950 (order as in the paper, effect small). Sequential coverage within [.84,.96]. Streaming one-sided evidence: 0 alarms under conditional null with drift and delays (very conservative).
Real-data savings claims (Pew, ACS, AlphaFold) NOT reproduced. M-estimation not implemented. The Wald CI is asymptotic and not anytime-valid.

## Gong & Zhang paid observations (WP1d, 2026-11-07) - tier `PAPER_RECONSTRUCTION` (Algs 1-6) / `COMMON_CONTRACT_PORT` (label acquisition)

Paper: PMLR 306 (gong26i) PDF; constants read from rendered pages 4, 6, 7, 29, 30. No author code. Code `src/shiftlab/sota/gong_zhang/`; tests `tests/d2a_rar/test_gong_zhang.py`;
port `src/shiftlab/bench/contract/adapters_gong_zhang.py` (claimed null `none`); reproduction script `scripts/d2a_rar/gz_repro.py {phase|table2}`. Details in `baselines/GONG_ZHANG.md` (bottom).
Resolved vs the WP1c spec: observation probability has a SQUARE ROOT; gamma = 1/T; eta schedules and the Alg 2 threshold confirmed; Alg 4/5/6 transcribed.
Free-budget phase transition reproduced qualitatively on a small synthetic instance (below B0 regret falls exactly by c per extra free observation; above B0 it falls ~B^{-1/2} with the balanced eta).
**Discrepancy:** with Alg 2 line 2 as printed (ln|Pi| in the denominator) regret jumps up at the threshold on this instance; the balanced form (ln|Pi| in the numerator, our derivation) behaves as Thm 3.2 predicts.
Alg 3 on the Table-2 setting (our guess of the generator): 3004.8 (sd 88.8, 5 reps) vs the paper's 2899.75 +- 48.80. linUCB / Tucker et al. not implemented; Fig. 2-3 sweeps not reproduced.
