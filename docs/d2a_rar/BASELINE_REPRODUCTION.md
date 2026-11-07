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

## Drift2Act (WP1a, 2026-11-07) - tier `PAPER_RECONSTRUCTION` (native, synthetic stand-in) / `COMMON_CONTRACT_PORT` (`abs_risk`)

Paper arXiv:2603.08578 (v1). No author code found; full record, spec, choices, metrics and mechanism in `baselines/DRIFT2ACT.md`
(sections 5-6). Code `src/shiftlab/sota/drift2act/`, tests `tests/d2a_rar/test_drift2act.py` (10) and
`tests/d2a_rar/test_adapter_drift2act.py` (4). **Camelyon17 / DomainNet NOT reproduced** (no local data, nothing downloaded).
Native attempt: a CPU-sized synthetic stand-in (8-d Gaussian binary stream, L=1500, covariate/concept/subgroup drift, delay 50,
B=3000, tau=0.2; not CIFAR), 40 episodes (seeds 1000-1039), calibration seeds 50000-50011, source `results/d2a_rar/drift2act/summary.md`.
Mean +- s.e.: ctrl_cert C_tot 97.84 +- 0.79 (C_act 29.86, C_label 67.98), V 353.9 +- 66.6, T_rec_post_harm 201.4 +- 36.7; alarm_only
C_tot 50.44, V 549.9 +- 69.9, T_rec_post_harm 653.8 +- 81.2; adapt_always C_tot 108.35 (C_act 60.00), V 426.3 +- 71.7. Paired vs
alarm_only ctrl_cert dV = -196.0 +- 47.2, dC_tot = +47.4 +- 0.9; vs adapt_always dV = -72.4 +- 68.2 (not significant).
**Reproduces (direction):** interventions lower V; ctrl+cert cheaper than adapt-always in action cost (29.9 vs 60.0).
**Does not reproduce:** V approx 0 for Controller+cert (ours 353.9 steps); certificate raising cost over the uncertified controller
(ours reverse: 29.9 vs 102.7 C_act); the min Acc_wg spread; baseline T_det (ours 230-270 vs paper 13-25). Mechanism: at tau=0.2 the
gate needs about 370+ in-window released labels (clean error 0.055), so it was open on 30% of steps and the controller abstained on
98.6% (12-episode log). **Metric artifacts:** controller T_det = 0 is "alarm already on" (alarm = any non-noop action or belief
shift; pre-onset alarm fraction 0.998), and raw T_rec = 0 in 77.5-82.5% of episodes because the model is still fine at onset (logistic
and periodic schedules start at alpha about 0), so `T_rec_post_harm` is reported. V is a step count over all 1500 steps. Evaluator bug
(unweighted 50% minority in R*) found and fixed; the bugged run is archived and unused. Contract port
`src/shiftlab/bench/contract/adapters_drift2act.py`: A0->continue, A3->query (windowed uniform audit; swappable request-size hook),
A2->switch(CANDIDATE), A4->retrain, A5->rollback, A6->abstain, gate-failure->alert; **A1 recalibrate unmapped**; z_t from proxies of the
scalar monitor and released losses; hand-specified untuned evidence. Reproduce commands and git commit: `baselines/DRIFT2ACT.md` 5.7.

## RAR - Retrain, Alert, or Rollback (WP1b, 2026-11-07) - tier `PAPER_RECONSTRUCTION` (native) / `COMMON_CONTRACT_PORT` (`none`)

Paper arXiv:2611.02251v1. No author artifact (Zenodo DOI reserved, not public); spec, parameter provenance (STATED vs CHOICE),
guarantee status and the mapping to code are in `baselines/RAR.md`. Code `src/shiftlab/sota/rar/`; native tests `tests/d2a_rar/test_rar.py` (23);
contract port `src/shiftlab/bench/contract/adapters_rar.py` (RAR + Cost-Aware Binary + Binary), tests `tests/d2a_rar/test_adapter_rar.py` (10).
All numbers below are from `results/d2a_rar/rar_repro.json` (gitignored), summarised by `scripts/d2a_rar/rar_summarize.py` -> `results/d2a_rar/rar_summary.md`
and `scripts/d2a_rar/rar_crossover.py` -> `results/d2a_rar/rar_crossover.json`. These are descriptive reproduction checks on **reconstructed** streams
and a **reconstructed** controller, not confirmatory evidence and not a ranking of methods (Suite A rule 5).

### Setup (native, Suite A)
- Data: ELEC2 (`~/river_data/Elec2/electricity.csv`, 3,091,689 B, sha256 `c10a416790ef8ab96089e5adfd2febb7c9cec72bd80dfecb2342f2283b86b88a`, checked at load; 45,312 rows, first 1,000 = offline warm-up, 44,312 evaluated). Learner: river HoeffdingTree (defaults), refit from scratch per retrain; detector: river ADWIN delta=0.002; tau=800, W_train=2,700, W_ref=1,000, g=200, p1=0.2, W1=300, W2=600, theta_L=0.7, theta_R=0.05 (STATED); delta, kappas, W_cur, W_mon, q_t constants etc. are our CHOICES (`config.py`).
- Streams (4 seeds, 0-3; ELEC2 is one fixed real stream, so seeds only change the canary-routing phase, and policies without a canary have s.e. = 0 on `elec2`):
  - `elec2`: unmodified (native drift).
  - `semi_abrupt` (our reconstruction of the paper's Semi-Abrupt, Sec 5): labels flipped (y -> 1-y) from onset u ~ U[0.4T, 0.8T] to the end, features untouched (`streams.semi_abrupt`, rng 10000+seed; onsets 27,489 / 31,080 / 29,637 / 30,597).
  - `semi_rb_drift` (our reconstruction of S-RB-Drift, a transient corruption followed by drift): a block of 2,265 (=5% of T) consecutive instances has every feature resampled uniformly within the warm-up min/max (blatant corruption), then 1,500 instances later an abrupt label flip to the end (`streams.semi_rollback_then_drift`, rng 20000+seed; corruption starts 16,101 / 11,955 / 18,434 / 14,477). Block placement, size, gap and the corruption model are our choices, not the paper's.
- Policies: No-Response, Always-Retrain (every W_train), Binary (ADWIN -> retrain, immediate deploy), Alert-Only, Rollback-Only (Binary + canary + holds), Full RAR; plus Cost-Aware Binary (retrain on a flag iff max(0, A_pre - A_cur) * H_hat >= rho). U = correct - rho N_r - 0.05 rho N_a - 0.2 rho N_b; U for the cost-blind policies is exactly affine in rho (`utility_at_rho`); Cost-Aware Binary is re-run at each rho in {1, 10, 100, 1000}.
- Compute: 12 (stream, seed) cells, 1,259 s total on a loaded CPU box.

### Results: mean net utility U (mean +- s.e. over 4 seeds)

rho = 1

| stream | no_response | always_retrain | binary | alert_only | rollback_only | full_rar |
|---|---|---|---|---|---|---|
| elec2 | 26,602 +- 0 | 31,100 +- 0 | 31,052 +- 0 | 26,600 +- 0 | 32,016 +- 775 | 29,402 +- 184 |
| semi_abrupt | 23,266 +- 188 | 30,248 +- 256 | 30,290 +- 235 | 23,263 +- 188 | 30,028 +- 201 | 26,669 +- 627 |
| semi_rb_drift | 20,585 +- 315 | 29,252 +- 203 | 29,589 +- 235 | 20,583 +- 315 | 29,222 +- 304 | 24,355 +- 718 |

rho = 5

| stream | no_response | always_retrain | binary | alert_only | rollback_only | full_rar |
|---|---|---|---|---|---|---|
| elec2 | 26,602 +- 0 | 31,036 +- 0 | 30,940 +- 0 | 26,590 +- 0 | 31,971 +- 775 | 29,371 +- 182 |
| semi_abrupt | 23,266 +- 188 | 30,184 +- 256 | 30,178 +- 236 | 23,252 +- 188 | 29,985 +- 201 | 26,640 +- 626 |
| semi_rb_drift | 20,585 +- 315 | 29,188 +- 203 | 29,480 +- 235 | 20,573 +- 315 | 29,182 +- 305 | 24,329 +- 719 |

rho = 100

| stream | no_response | always_retrain | binary | alert_only | rollback_only | full_rar |
|---|---|---|---|---|---|---|
| elec2 | 26,602 +- 0 | 29,516 +- 0 | 28,280 +- 0 | 26,367 +- 0 | 30,898 +- 775 | 28,649 +- 136 |
| semi_abrupt | 23,266 +- 188 | 28,664 +- 256 | 27,494 +- 257 | 23,000 +- 190 | 28,968 +- 190 | 25,950 +- 613 |
| semi_rb_drift | 20,585 +- 315 | 27,668 +- 203 | 26,891 +- 236 | 20,345 +- 315 | 28,227 +- 322 | 23,720 +- 740 |

Cost-Aware Binary (U +- s.e.; mean N_r) against Binary and Full RAR at the same rho:

| stream | rho | CA-Binary U | CA N_r | Binary U | Full RAR U |
|---|---|---|---|---|---|
| elec2 | 1 | 32,513 +- 0 | 21.0 | 31,052 +- 0 | 29,402 +- 184 |
| elec2 | 10 | 32,606 +- 0 | 19.0 | 30,800 +- 0 | 29,333 +- 180 |
| elec2 | 100 | 31,371 +- 0 | 18.0 | 28,280 +- 0 | 28,649 +- 136 |
| elec2 | 1000 | 26,602 +- 0 | 0.0 | 3,080 +- 0 | 21,809 +- 396 |
| semi_abrupt | 1 | 31,468 +- 420 | 20.8 | 30,290 +- 235 | 26,669 +- 627 |
| semi_abrupt | 10 | 31,738 +- 336 | 20.2 | 30,036 +- 237 | 26,604 +- 626 |
| semi_abrupt | 100 | 29,508 +- 111 | 17.2 | 27,494 +- 257 | 25,950 +- 613 |
| semi_abrupt | 1000 | 23,266 +- 188 | 0.0 | 2,069 +- 469 | 19,414 +- 543 |
| semi_rb_drift | 1 | 30,428 +- 513 | 19.5 | 29,589 +- 235 | 24,355 +- 718 |
| semi_rb_drift | 10 | 30,071 +- 501 | 19.5 | 29,344 +- 234 | 24,297 +- 720 |
| semi_rb_drift | 100 | 28,950 +- 714 | 17.8 | 26,891 +- 236 | 23,720 +- 740 |
| semi_rb_drift | 1000 | 20,585 +- 315 | 0.0 | 2,366 +- 753 | 17,949 +- 1,038 |

Accuracy over evaluated instances: Full RAR 0.664 / 0.602 / 0.550 (elec2 / semi_abrupt / semi_rb_drift) against Binary 0.701 / 0.684 / 0.668 and No-Response 0.600 / 0.525 / 0.465 (`rar_summary.md`).

### Action counts per run (mean +- s.e.) and rollback causes

| stream | policy | N_r | N_a | N_b |
|---|---|---|---|---|
| elec2 | always_retrain | 16.0 +- 0.0 | 0 | 0 |
| elec2 | binary | 28.0 +- 0.0 | 0 | 0 |
| elec2 | alert_only | 0 | 47.0 +- 0.0 | 0 |
| elec2 | rollback_only | 10.2 +- 0.2 | 0 | 5.2 +- 0.9 |
| elec2 | full_rar | 6.5 +- 0.5 | 16.0 +- 1.0 | 1.5 +- 0.6 |
| semi_abrupt | always_retrain | 16.0 +- 0.0 | 0 | 0 |
| semi_abrupt | binary | 28.2 +- 0.2 | 0 | 0 |
| semi_abrupt | alert_only | 0 | 53.2 +- 0.8 | 0 |
| semi_abrupt | rollback_only | 10.0 +- 0.0 | 0 | 3.5 +- 0.6 |
| semi_abrupt | full_rar | 6.2 +- 0.2 | 16.2 +- 0.8 | 1.0 +- 0.4 |
| semi_rb_drift | always_retrain | 16.0 +- 0.0 | 0 | 0 |
| semi_rb_drift | binary | 27.2 +- 0.8 | 0 | 0 |
| semi_rb_drift | alert_only | 0 | 48.0 +- 0.9 | 0 |
| semi_rb_drift | rollback_only | 9.2 +- 0.2 | 0 | 4.0 +- 0.7 |
| semi_rb_drift | full_rar | 5.2 +- 0.5 | 18.2 +- 0.8 | 1.2 +- 0.5 |

Full RAR rollback causes pooled over the 4 seeds (`rar_summary.md`): elec2 R1_interim 3, R3 2, R1 1; semi_abrupt R1_interim 2, R3 2; semi_rb_drift R2 2, R1 1, R3 1, R1_interim 1. R2 (sustained corruption) appears only on the corruption stream (2 R2 rollbacks, none on the other two streams), as designed. N_r for Always-Retrain is exactly floor(44,312 / 2,700) = 16.

### Crossover window: rho range where Full RAR beats Binary, Always-Retrain and No-Response simultaneously
Computed in closed form from the seed-mean (n_correct, N_r + 0.05 N_a + 0.2 N_b) of each policy (`rar_crossover.py`; open interval).

| stream | our window (seed-mean) | per-seed windows (empty = None) | paper's window | verdict |
|---|---|---|---|---|
| elec2 | 203 < rho < 369 | (214, 348), (222, 384), (171, 394), (201, 356) | not transcribed | NOT COMPARED |
| semi_abrupt | 411 < rho < 470 | (295, 755), None, (416, 502), None | S-Abrupt 237-961 | window exists but is ~12x narrower and lies inside the paper's range; empty for 2 of 4 seeds: **partial mismatch** |
| semi_rb_drift | 512 < rho < 589 | (406, 763), (347, 986), None, None | S-RB-Drift 41-1013 | our window excludes the paper's low end (41-512) and is ~12x narrower; empty for 2 of 4 seeds: **mismatch** |

### Comparison with the paper's qualitative claims (RAR.md)
- "RAR does not dominate": **matches**. Full RAR is below Binary and Always-Retrain at rho = 1 and 5 on all three streams, and at rho = 100 on both semi-synthetic streams (paired by seed, `rar_summary.md`; the one exception is elec2 at rho = 100 vs Binary, +369 +- 136, which is real but small); it beats No-Response on all three streams for rho <= 100 and is below it at rho = 1000 (21,809 / 19,414 / 17,949 vs 26,602 / 23,266 / 20,585).
- Win windows: partial overlap on S-Abrupt, mismatch on S-RB-Drift (table above). Plausible causes (not tested): our reconstructed injectors, our CHOICE constants (delta, kappas, W_cur), and the 4-seed budget. We did not tune anything to hit the paper's windows.
- Canary removal raises utility on 11/13 streams at rho = 1: **NOT COMPARED** (the "Full RAR without canary" ablation is not a mode in `MODES`; Rollback-Only vs Binary is not the same contrast and is not claimed as such).
- H2 not supported; the paper's Table numbers (per-stream utilities, other 10 streams: Covertype, S-Gradual, etc.): **NOT COMPARED** (not transcribed; the other streams are not implemented or downloaded).

### Observations from the log (descriptive, our reconstruction)
- Alert-Only is indistinguishable from No-Response up to the alert bill: U differs by -2.3 (elec2), -2.7 (semi_abrupt), -2.4 (semi_rb_drift) at rho = 1, i.e. N_a x 0.05 rho. Alerts without action change nothing; as expected.
- Rollback-Only beats Full RAR on every stream for every rho in {0.1, 0.5, 1, 5, 100} (rho = 1000 was not computed for Rollback-Only), e.g. at rho = 1 by +2,615 +- 797, +3,358 +- 601, +4,867 +- 511 (elec2 / semi_abrupt / semi_rb_drift); the difference is nearly rho-independent (+2,618 at rho = 0.1) because it is an accuracy effect: the gates delay and suppress retrains (5-7 vs 9-10 retrains) and cost 6-11 points of accuracy (0.664 vs 0.723, 0.602 vs 0.678, 0.550 vs 0.660). In our reconstruction the gates are therefore net-negative relative to canary+holds alone; the paper's claim on this contrast was not transcribed, so no match/mismatch is stated.
- Cost-Aware Binary beats Full RAR at all 12 (stream, rho) cells, by +2,636 to +6,073 (semi_rb_drift rho = 1000: +2,636 +- 1,144), and equals No-Response at rho = 1000 (never retrains). It uses no canary and no rollback and still wins on semi_rb_drift, whose corruption block is our own construction.
- Full RAR's rollbacks per run (1.0-1.5) are far fewer than Rollback-Only's (3.5-5.2) because gating suppresses many marginal retrains; R1_interim is the most frequent cause on elec2 (3 of 6) and ties with R3 on semi_abrupt (2 each).
- Binary retrains 27-28 times against Always-Retrain's 16; ADWIN flags frequently on ELEC2's native drift. Per-stream Binary-vs-Always-Retrain difference is small (|diff| < 500) at rho <= 5.

### Contract port (Suite B) - `COMMON_CONTRACT_PORT`, claimed null `none`
`adapters_rar.py` expresses the state machine over `ObservableState`: ADWIN gate on served-model loss of released labels; Gate 2/3 as swappable `GateRule` objects (the same `ThetaLGate`/`ThetaRGate` classes as the native code); a swappable `LabelRequestPolicy`; stage 1 = `route(RETRAINED, p1)`, stage 2 = `switch(RETRAINED)`, commit by the paired z-test on shadow losses (unpaired fallback in `deployed` mode); failures -> `rollback`/route-clear; alerts A1/A2/A3/A_blocked/timeout -> `alert`; Alert-Hold-Soft with emergency override. Every deviation is listed in the module docstring; the material ones: R2/Hard hold not mapped; stage-1 abort is free (native charges C_b), commit costs c_s (native: none); R3 uses chance level instead of majority class; flag lifetime counted from the raise time; one replaceable retrained slot (no re-canary after a commit); requires `canary_clocks()` (`deploy_on_complete=False`) for a real stage 1. Cost-Aware Binary and Binary are ported as `CostAwareBinaryAdapter` / `BinaryAdapter`. Tests (10) cover audit pass, no leakage, label cap respected, routed canary committed (and, with scripted thresholds, stage-1 abort and stage-2 rollback), the deployed-mode fallback, and that swapping a gate or the label hook changes only the gated decision. Contract results are not part of this section: the port was only smoke-tested on one scripted drift family, no Suite B comparison was run.
`adapters.py` still carries the `STUB_NOT_PORTED` `RARAdapter`; the coordinator must wire `adapters_rar.RARAdapter`.

### Reproduce
```
cd shiftlab-d2a-rar-2026-11-07            # branch research/drift2act-rar-autoresearch-2026-11-07
export PYTHONPATH=$PWD/src
python scripts/d2a_rar/rar_repro.py --seeds 4 --out results/d2a_rar/rar_repro.json   # resumable, ~1,260 s
python scripts/d2a_rar/rar_summarize.py results/d2a_rar/rar_repro.json > results/d2a_rar/rar_summary.md
python scripts/d2a_rar/rar_crossover.py results/d2a_rar/rar_repro.json results/d2a_rar/rar_crossover.json
python -m pytest tests/d2a_rar/test_rar.py tests/d2a_rar/test_adapter_rar.py -q
```
Environment: Python 3.13.1, river 0.26.1. Code state: branch HEAD `2920475663330701cff5a23cf269a96fda87b244` plus **uncommitted** working-tree changes (the RAR files above are not yet committed); results were generated from that working tree. ELEC2 sha256 recorded in `rar_repro.json` `_meta` and verified at load.
