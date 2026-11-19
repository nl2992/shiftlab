# IID-calibrated promotion policies under a causal null: exact results

**Date:** 2026-11-17. Protocol: `PROTOCOL.md` (fixed before the run). Code: `scripts/paper4_continuation/rbdp/iid_failure/`
(`iidlib.py` evaluator and policies, `runner.py`, `crosscheck.py`, `run_study.py`, `analyze.py`). Raw rows:
`results/settings.jsonl` (492 settings x 7 policies = 3444 rows), `results/summary.json`, `results/crosscheck.json`,
`results/shuffle_fits.json`, `results/skipped.jsonl`. Nothing was edited in existing files. No figures.

## Result in one paragraph

Policies whose promotion event is monotone in the label count and whose queries do not depend on labels (P1 fixed-sample test,
P2 count-based SPRT) and the two safe-by-construction references (P6 e-process gate, P7 RB-DP causal) had causal risk equal
to alpha (ratio 1.000) in all 348 non-shuffled settings. The belief-adaptive policies did not: P3 (HMM-filter threshold) exceeded alpha in 252/348
settings and P4 (myopic VOI) in 252/348, up to 4x and 8x alpha; P5 (the exact IID-optimal policy) in 240/348, up to 4x. Every
violation is on an anti-persistent chain (synthetic or the three real fits). All 96 persistent synthetic settings have ratio 1.000 for
every policy. Time-shuffled refits removed the failure for most, not all, chains (see controls). The count-based tests are not
shown to fail, as the protocol anticipated.

## Choices not fixed by the protocol (stated here, set before the run)

- **Cost model** = the RB-DP solver's: step cost P(Y_t=1 | belief) before promotion, query cost c = 0.01 (also the VOI threshold in P4),
  switch cost k = 0; after promotion the solver's own continuation (greedy on its grid J tables, evaluated on exact beliefs).
  Prior: stationary law of the chain (as in the real-data solver_params). Solver: `lattice_exact=True`, `n_beta=201`.
- **Grid reading:** "t01, t10 in {0.6,0.75,0.9} (anti) and {0.1,0.25} (persistent controls)" read as the 3x3 anti grid (9 pairs) plus the 2x2
  persistent grid (4 pairs); no mixed pairs. 13 pairs x 2 e0 = 26 chains, x alpha {0.05,0.1} x B {2,3,4} x T {12,20} = 312 synthetic settings,
  ordered chain (anti then persistent, t01 outer), e0, alpha, B, T. Chain type = sign of 1 - t01 - t10.
- **P2:** H1 = IID Bernoulli(e1) vs 1/2; query t = 1..B; decisions only while new labels arrive (t <= B+1); only the upper boundary is used.
- **P3:** queries t = 1..B; promotion check at every t <= T on the belief given released labels; boundary tie randomised.
- **P4:** query iff VOI > 0.01, VOI = V(prop(beta)) - sum_y P(y) V(beta_y'), V(b) = min(pos(b), 1-pos(b)); promote iff beta > tau.
  P3 and P4 coincide in 220 of 492 settings (VOI always above 0.01 on the visited beliefs).
- **Calibration (P1-P4):** bisection over the sorted set of reachable threshold levels, then bisection on a tie-coin theta (fresh coin at each
  boundary node, so Lemma A applies exactly). IID risk equals alpha to 2.8e-17 in every setting for P1-P4 (and for P5).
- **P5/P7:** the solver's `mode="iid"` / `"causal"`, reported `risk_causal`, `risk_iid`, cost U. For P5 and P7 the solver's causal risk treats
  vertex mixtures as pre-drawn, an upper bound on the true worst case when a plan randomises at a node. The policy was not extracted.
- **P6:** my float re-implementation of the E4 gated planner; stake 1; th in {2,...,2^B}, the one with lowest repaired cost is reported;
  activation min(1, alpha*th), mixed with never-promote. Causal risk = activation x exact Lemma A risk of the gate policy (P6 causal ratio was 1.000 in every setting; IID ratio max 1.0).
- **Illustration tie-break:** many settings tie at ratio 4.0 for a chain; the first in file order (alpha 0.05, B 3, T 12 for the real chains) was taken.

## Cross-checks (run before the main study; `results/crosscheck.json`)

(a) Five small cells (T 3-5, B 1-2; anti and persistent), policies P1-P4: evaluator causal risk vs brute-force maximum over all 2^K deterministic
nulls (p in {0, 1/2} at each query node, explicit history tree). All 20 cases agree (abs diff < 1e-12; the printed values are identical).
K (query nodes) was 3, or 1 for B = 1, so this tests the recursion, not a deep tree. P3 gives 0.2 and 0.1 where the IID risk is 0.1 and 0.05.
(b) P5: the policy was not extracted. The solver's own values are reported (e.g. T12 B3 anti 0.9/0.9 e0 0.1 alpha 0.1: IID risk 0.1, causal risk 0.4). Consistency
check on all 492 settings: P5 cost <= cost of each IID-feasible P1-P4 (0 exceptions); never-promote cost C0 equals the solver's C0 (max diff 8.9e-14); P7 cost <= P6 cost (0 exceptions).
(c) IID risk of P1-P4 = alpha in all 492 settings (max |diff| 2.8e-17); P6 and P7 have IID risk <= alpha (max ratio 1.0, 1.0000000000000002).
(d) P6 gate cost: float DP vs `EProcessGatedPlanner.solve_gated` exact Fractions on 3 rational cells, 7 (cell, th) pairs: max abs diff 8.3e-14.
(e) Monte Carlo of the alternative HMM for P3 (200k runs, T 8, B 3): exact 3.94306 vs MC 3.94355 (se 0.0024, z = 0.20).

## Per-policy distribution of causal risk / alpha

**all_non_shuffled** (348 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/348 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/348 |
| P3_hmm_filter | 1.000 / 2.000 / 4.000 | 252/348 |
| P4_myopic_voi | 1.000 / 2.000 / 8.000 | 252/348 |
| P5_iid_optimal_pomdp | 1.000 / 2.000 / 4.000 | 240/348 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/348 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/348 |

**synthetic** (312 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/312 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/312 |
| P3_hmm_filter | 1.000 / 2.000 / 4.000 | 216/312 |
| P4_myopic_voi | 1.000 / 2.000 / 8.000 | 216/312 |
| P5_iid_optimal_pomdp | 1.000 / 2.000 / 4.000 | 210/312 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/312 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/312 |

**synthetic_anti** (216 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/216 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/216 |
| P3_hmm_filter | 2.000 / 3.625 / 4.000 | 216/216 |
| P4_myopic_voi | 2.000 / 3.250 / 8.000 | 216/216 |
| P5_iid_optimal_pomdp | 1.000 / 2.000 / 4.000 | 210/216 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/216 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/216 |

**synthetic_persistent** (96 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/96 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/96 |
| P3_hmm_filter | 1.000 / 1.000 / 1.000 | 0/96 |
| P4_myopic_voi | 1.000 / 1.000 / 1.000 | 0/96 |
| P5_iid_optimal_pomdp | 1.000 / 1.000 / 1.000 | 0/96 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/96 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/96 |

**real** (36 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/36 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/36 |
| P3_hmm_filter | 2.000 / 3.625 / 4.000 | 36/36 |
| P4_myopic_voi | 2.000 / 2.000 / 4.000 | 36/36 |
| P5_iid_optimal_pomdp | 1.000 / 2.000 / 4.000 | 30/36 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/36 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/36 |

**shuffled** (144 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/144 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/144 |
| P3_hmm_filter | 1.000 / 1.000 / 4.000 | 36/144 |
| P4_myopic_voi | 1.000 / 1.000 / 1.000 | 0/144 |
| P5_iid_optimal_pomdp | 1.000 / 1.000 / 1.000 | 0/144 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/144 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/144 |

**shuffled_anti** (36 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/36 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/36 |
| P3_hmm_filter | 2.000 / 3.250 / 4.000 | 36/36 |
| P4_myopic_voi | 1.000 / 1.000 / 1.000 | 0/36 |
| P5_iid_optimal_pomdp | 1.000 / 1.000 / 1.000 | 0/36 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/36 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/36 |

**shuffled_persistent** (108 settings)

| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |
|---|---|---|
| P1_fixed_sample | 1.000 / 1.000 / 1.000 | 0/108 |
| P2_count_sprt | 1.000 / 1.000 / 1.000 | 0/108 |
| P3_hmm_filter | 1.000 / 1.000 / 1.000 | 0/108 |
| P4_myopic_voi | 1.000 / 1.000 / 1.000 | 0/108 |
| P5_iid_optimal_pomdp | 1.000 / 1.000 / 1.000 | 0/108 |
| P6_eprocess_gate | 1.000 / 1.000 / 1.000 | 0/108 |
| P7_rbdp_causal | 1.000 / 1.000 / 1.000 | 0/108 |

(Group `all_non_shuffled` = synthetic + real. n counts settings; each setting is one (chain, alpha, B, T).) Chain types: synthetic_anti = 216,
synthetic_persistent = 96. All three real fits (Old Faithful duration c01, Faithful waiting P23, Geyser waiting P24) are anti-persistent (1 - t01 - t10 = -0.56, -0.51, -0.84), 12 settings each.

Frequencies of the ratio among all 492 settings: P3 {1:204, 2:96, 3:4, 3.25:46, 4:142}; P4 {1:240, 2:124, 2.5:2, 3.25:22, 4:96, 5:2, 6.5:2, 8:4}; P5 {1:252, 1.33:42, 2:148, 2.67:4, 3:1, 3.25:12, 4:33}.
Violations by policy and real chain (12 settings each): c01: P3 12, P4 12, P5 10; P23: 12, 12, 12; P24: 12, 12, 8 (maxima 4, 2 or 4, 4).

## The five illustrations (selected as the most extreme of 348 non-shuffled settings; not typical)

Rule: among P3, P4, P5 violations, the best setting for each of the three real chains, then the two best synthetic settings with distinct (t01, t10). Ratios are exact.

| # | setting | policy | IID risk | causal risk | ratio | cost | C0 (never) | P7 cost | other policies' ratio |
|---|---|---|---|---|---|---|---|---|---|
| 1 | c01_faithful, alpha 0.05, B 3, T 12 (t01 .930, t10 .631, e0 .115, e1 .98) | P3 | 0.05 | 0.20 | 4.0 | 7.3891 | 7.5664 | 7.3517 | P4 2, P5 2, P1/P2/P6/P7 1 |
| 2 | p23_faithful_waiting, alpha 0.05, B 3, T 12 (.906, .601, .02, .98) | P3 | 0.05 | 0.20 | 4.0 | 7.0076 | 7.1645 | 7.0141 | P4 4, P5 2, others 1 |
| 3 | p24_geyser_waiting, alpha 0.05, B 3, T 12 (.988, .847, .210, .98) | P3 | 0.05 | 0.20 | 4.0 | 7.2234 | 7.4983 | 7.2110 | P4 2, P5 2, others 1 |
| 4 | synthetic t01 .9, t10 .75, e0 .2, alpha 0.05, B 4, T 12 | P4 | 0.05 | 0.40 | 8.0 | 6.3292 | 6.3273 | 6.2652 | P3 4, P5 2.67, others 1 |
| 5 | synthetic t01 .9, t10 .9, e0 .2, alpha 0.05, B 4, T 12 | P4 | 0.05 | 0.40 | 8.0 | 5.9437 | 6.0000 | 5.9312 | P3 4, P5 4, others 1 |

Costs: in #1 and #3 the failing policy is more expensive than the safe P7; in #2 it is cheaper by 0.0065. In #4 the failing P4 costs more than never promoting (6.3292 vs 6.3273).
Across all violating settings, the failing policy is cheaper than P7 in 64/288 (P3), 47/252 (P4), 240/240 (P5, as it is the IID optimum); the largest saving over P7 is 0.20 (P3), 0.17 (P4), 0.25 (P5), on costs of 5-10.
(P3 violates in 288 of 492 settings counting shuffled ones; P4 252; P5 240.)

## Controls next to the illustrations

- **Persistent chains (synthetic, 96 settings):** causal risk / alpha = 1.000 for all seven policies, including P3, P4, P5. E.g. t01 = t10 = 0.1, e0 = 0.2, alpha 0.05, B 4, T 12: all 1.0.
- **Shuffled real streams** (5 shuffles per chain, seeds 20261117+k, refit with `real_data/fit.py` `fit_hmm`, 12 settings each; 12 refits ran, 3 skipped because the refit emissions
  do not straddle 1/2, which the solver requires: c01 shuf3 (e0 .566), P24 shuf1 (e0 .511), P24 shuf3 (e0 .518)). Of the 12 run chains, 9 refit as persistent, 3 as anti-persistent
  (P23 shuf3 lambda -0.27; P24 shuf0 -0.013; P24 shuf4 -0.082). Result over 144 settings: P4, P5 and every other policy: 0 violations. P3: 36 violations, all on the three shuffled chains that refit anti-persistent (ratio 4.0 in each of their 12 settings);
  0/108 on the nine persistent refits. So the failure disappears under shuffling for P4 and P5, and for P3 only when the refit is not anti-persistent; the shuffle does not always remove anti-persistence from the fit (weak apparent anti-persistence from 272-299 points).
  Refit parameters: `results/shuffle_fits.json`.

## Which policies were safe

Safe (ratio 1.000 in every run): P1, P2 (monotone count rules), P6, P7. Not safe on anti-persistent chains: P3, P4, P5. The statement "standard methods fail" is not supported;
the result is that belief-adaptive policies calibrated or optimised under the IID null exceed alpha by up to 4x (P3, P5) and 8x (P4) here. Note that P5, an exact IID constrained optimum, shows a failure; its cost is below P7's in all 240 violating settings (by up to 0.25), which is what safety costs here.

## Surprises, limits, not run

- The ratios fall on a few values (1, 2, 4, 8, 3.25...), because with B <= 4 the null gains by choosing p = 0 on a few nodes; they are exact, not rounded.
- P4 reaches 8x only at B = 4 on strongly anti-persistent chains; at B = 2 all violating P3 and P4 settings are exactly 2x.
- P3 and P4 are identical in 220 settings; P4 is a different policy only where VOI falls below 0.01.
- P5 shows no violation in 6/216 synthetic anti settings (chain 0.75/0.6, e0 0.2).
- 3 of 15 shuffle refits were not runnable (above). Phase 4 qualifier chains: not run (the runner takes `--extra-chains extra.json`, a list of `{"id", "solver_params", "stream"}`; none were provided). T = 20, B = 4 ran with no cap.
- P5/P7 causal risk comes from the solver's evaluator (upper bound under mixtures); P1-P4, P6 are exact by Lemma A on behavioural policies. The post-promotion continuation uses the solver's grid-greedy policy (not re-optimised).
- Shuffled-stream results depend on 5 permutations per chain; no further seeds were tried.
