# 08 Synthetic development record (2026-10-30)

All studies below are development studies on synthetic data, run under protocols registered before execution. None is confirmatory. Paths are relative to `docs/promising_directions/`. Costs are net cost per path (deployment loss + c_q x queries + c_s x switches), unit-free, from `results/b1/summary.json` and `results/b2/summary.json`.

## 1. A1: exact joint vs best-calendar separation (Lane A)

Protocol `protocols/A1-exact-separation.md` (commit `0d03912`). Solver: branch `research/risk-preserving-switching-approx-2026-10-29` at `2bd2e8e41639073c8d22ffb17ef0bcc68111e321`, two pinned files hashed in `results/a1/summary.json` `provenance`. Details in `04_EXACT_ORACLE_SEPARATION.md`.

Grid (fixed before execution):

| Part | Definition | Cells |
|---|---|---|
| Primary | T in {6,7,8}; B in {2,3,4}; d=2; transition in {1/20,1/10}; emissions in {(1/10,9/10),(1/50,49/50)}; alpha in {1/20,1/10}; c_s in {1/10,1/2}; c_q=1/100 | 144/144 completed |
| Secondary | same with d=1 | 144/144 completed (1 transient MemoryError, re-run alone, gap 0) |
| Adversarial | T=6, B=3, d=2, random rational parameters, seed 20261030 | 200/200 completed |

Sanity checks all passed (`results/a1/sanity.json`): T6B3d2 J = 22083523/7812500; calendar slots 1..T equal 1..T-d at T=6; T8B4 gap C*-J = 6744087/781250000; J <= C* in all checked cells.

Results (`results/a1/summary.json`):

| Set | Cells | Max relative gap | Cells with gap > 0 | Cells >= 0.05 | Cells >= 0.10 | J <= C* violations | Monotone-in-T slices with increase > 0.01 |
|---|---|---|---|---|---|---|---|
| Primary only | 144 | 0.003645 (10787546091/2959163041129) at T=8,B=4,d=2,trans 1/20,emissions (1/50,49/50),alpha 1/10,c_s 1/10 | 8 | 0 | 0 | 0 | 0 of 48 complete slices |
| Primary + secondary | 288 | 0.008741 (22608701046/2586568221299) at T=8,B=4,d=1, same other parameters | 23 | 0 | 0 | 0 | 0 of 96 complete slices |
| Adversarial | 200 | 0.0 | 0 | 0 | 0 | 0 | n/a |

Decision: KILL for the joint-acquisition method claim (both decision fields). Wall clock about 27 minutes on 2 workers (`04_EXACT_ORACLE_SEPARATION.md`). Nonzero gaps appear only at B=4, transition 1/20, near-perfect signal. Limits: T <= 8 only, one two-regime symmetric chain, J not independently dual-certified here, objective-misaligned acquisition not tested (`04_EXACT_ORACLE_SEPARATION.md`). The gap that exists is the known-POMDP timing adaptivity gap (`02_LITERATURE_AND_NOVELTY_AUDIT.md`).

Disclosed deviations: calendar slots 1..T-d (matches source runner); adversarial emission grid fixed to {11/20, 3/5, 7/10, 4/5, 9/10, 19/20, 49/50} because the protocol left it unspecified; outputs under `docs/` because `results/` is gitignored (`04_EXACT_ORACLE_SEPARATION.md`).

## 2. B1: certified switching (Lane B, development round 1)

Protocol `protocols/B1-certified-switching.md` (commit `1a742dc`, sha256 `98f85250a95ae6e31857760ca33f2ebe1dc0c042762469b7d8f84cd557a82757`). Implementation notes `results/b1/IMPLEMENTATION_NOTES.md`; script `scripts/promising_directions/b1_certified_switching.py`.

Design:
- Stream: T=2000, 0/1 loss, label delay d=5, change point tau=600, disagreement rate 0.25 in every regime, agreement observed free so D_t=0 exactly on agreement.
- Costs/budgets: c_q=0.05; B in {200,400}; c_s in {5,20}; alpha=0.05; p_min=0.05; 500 seeds per (world, B, c_s) paired across policies; paired percentile bootstrap, 2000 resamples (`results/b1/summary.json` `meta`).
- Worlds (pre-change errors f0 0.10, f1 0.20): W1 useful-persistent (post f0 0.30, f1 0.12); W2 useless (0.30, 0.35); W3 reversing (as W1 until t=600+R, R~Geometric(mean 150), then f0 0.10, f1 0.30); W4 benign (no change).
- Policies: P0 never switch; P1 challenger from t=1; P2 incumbent-alarm discounted-Kelly switch (nominal 0.15); P3 certified switch with cap p_min/2; P4 persistence-aware (hazard 1/150, a known-persistence assumption); P5 oracle (headroom only); P4w unregistered exploratory, excluded from decisions.
- Decision rules fixed in advance: Q1 POSITIVE needs >= 10% world-averaged reduction vs BEST in every (B,c_s), paired CI excluding 0 in every setting, and no world > 10% worse; NEGATIVE if P3 no better than BEST in at least half the settings. Q2 SUPPORTED needs P4 beating P3 in W3 by >= 10% (CI excludes 0) and not > 2% worse in W1.
- Runtime 22.28 s, 8 tasks about 5 s each (`results/b1/summary.json` `meta`). Repo head at run: `5f082500ea544fd552f3ae9558c581b56d0068b8`.

World-averaged cost per policy (`results/b1/summary.json` `q1_settings`; P3 minus BEST is the paired mean difference with 95% bootstrap CI):

| (B, c_s) | P0 | P1 | P2 | P3 | P4 | P4w | P5 (oracle) | BEST | P3 - BEST [CI] | P3 relative reduction | 10% bar | CI excludes 0 | No world > 10% worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B200_cs5 | 347.68 | 458.17 | 343.20 | 331.71 | 341.65 | 357.49 | 281.65 | P2 | -11.49 [-13.15, -9.86] | 3.35% | no | yes | yes |
| B200_cs20 | 347.68 | 473.17 | 349.03 | 335.50 | 357.65 | 357.67 | 292.90 | P0 | -12.18 [-12.78, -11.57] | 3.50% | no | yes | yes |
| B400_cs5 | 347.68 | 458.17 | 340.62 | 340.13 | 348.98 | 367.55 | 281.65 | P2 | -0.49 [-2.16, 1.08] | 0.14% | no | no | no |
| B400_cs20 | 347.68 | 473.17 | 348.31 | 343.97 | 367.62 | 367.62 | 292.90 | P0 | -3.71 [-4.25, -3.10] | 1.07% | no | yes | no |

Per-world P3 vs BEST (relative; negative is better), from `p3_worse_than_best_by_world`: B200_cs5 W1 -4.90%, W2 -4.75%, W3 -0.75%, W4 +0.13%; B200_cs20 W1 -16.57%, W2 +2.07%, W3 +4.77%, W4 +5.01%; B400_cs5 W1 +13.80%, W2 -7.32%, W3 -3.77%, W4 +0.14%; B400_cs20 W1 -15.96%, W2 +4.14%, W3 +9.60%, W4 +10.00%.

Q2 (`results/b1/summary.json` `q2_settings`): P4 minus P3 in W3 mean -0.58, -0.94, -1.55, -2.07 (B200_cs5, B200_cs20, B400_cs5, B400_cs20); W3 relative gain 0.24%, 0.39%, 0.62%, 0.82% (bar 10%); W1 P4 worse by 10.45%, 22.33%, 9.50%, 23.93% (bar 2%).

Validity: P3 false-promotion 0/500 in W2 and W4 in all 8 cells; one-sided 95% Clopper-Pearson upper bound 0.005974 <= alpha=0.05. Budget violations 0. Efficacy interpretation not halted.

Decisions: Q1 MIXED; Q2 NOT SUPPORTED; validity OK (`results/b1/summary.json` `decisions`; `RESEARCH_LEDGER.md`).

Limiting factors: the P3 cap p_min/2 = 0.025 limits bets. B1 diagnostics (counterfactual reruns with delay 1, c_q=0, p_min=0.5) were not saved (`results/b1/IMPLEMENTATION_NOTES.md`), so no saved artifact supports a decomposition beyond the cost table above.

## 3. B2: propensity-matched cap (Lane B, development round 2)

Protocol `protocols/B2-propensity-cap.md` (commit `af14d5a`, sha256 `533a529ddda537ce8b925fdaf6b0b503cce46797ade2c7ca0d5a9b95202b6844`), registered after B1.

Explicit statement: **B2's single change was motivated by B1's post-hoc diagnostic. B2 is development round 2 on the same worlds, not confirmation.** The protocol itself states a positive result "is therefore not confirmation" and would authorise only a separately registered confirmation on a structurally distinct generator family (`protocols/B2-propensity-cap.md`).

Design: identical to B1 except (i) new policy P3b with bet cap lambda_t in [0, q_t/2] where q_t is the issued propensity (the |Z_t| <= 1/q_t bound keeps 1 + lambda_t Z_t nonnegative; rollback shares the cap); (ii) P4/P4w dropped; (iii) fresh seeds 20261101, 500 per cell; (iv) P2 cap check. P2's Kelly cap 3.0 versus propensity-matched rate/2 = 0.05 (B=200) and 0.10 (B=400): not lower, so P2b not added and BEST is over {P0, P1, P2} (`results/b2/NOTES.md`). B1 reproducibility: default-mode rerun matches the B1 summary after removing volatile `meta` fields (`results/b2/NOTES.md`). Runtime 5.93 s (`results/b2/summary.json` `meta`).

World-averaged cost per policy (`results/b2/summary.json` `q1_settings`):

| (B, c_s) | P0 | P1 | P2 | P3 | P3b | P5 (oracle) | BEST | P3b - BEST [CI] | P3b relative reduction | P3 relative reduction | 10% bar | CI excludes 0 | No world > 10% worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B200_cs5 | 347.50 | 457.40 | 343.49 | 331.61 | 308.45 | 281.28 | P2 | -35.04 [-36.81, -33.40] | 10.20% | 3.46% | yes | yes | yes |
| B200_cs20 | 347.50 | 472.40 | 349.37 | 335.38 | 313.99 | 292.53 | P0 | -33.52 [-34.25, -32.76] | 9.65% | 3.49% | no | yes | yes |
| B400_cs5 | 347.50 | 457.40 | 341.58 | 339.91 | 314.68 | 281.28 | P2 | -26.91 [-28.62, -25.30] | 7.88% | 0.49% | no | yes | yes |
| B400_cs20 | 347.50 | 472.40 | 349.43 | 343.73 | 320.84 | 292.53 | P0 | -26.66 [-27.36, -25.96] | 7.67% | 1.09% | no | yes | no |

Per-world costs, all policies (`results/b2/summary.json` `cells`), with P3b relative to BEST in that world from `p3b_worse_than_best_by_world` (negative is better):

| (B, c_s) | World | P0 | P1 | P2 | P3 | P3b | P5 | P3b vs BEST |
|---|---|---|---|---|---|---|---|---|
| B200_cs5 | W1 | 479.94 | 293.49 | 402.72 | 385.71 | 288.60 | 233.07 | -28.34% |
| B200_cs5 | W2 | 479.98 | 614.83 | 516.33 | 489.97 | 489.97 | 479.98 | -5.11% |
| B200_cs5 | W3 | 231.08 | 516.57 | 246.20 | 241.76 | 246.24 | 213.06 | +0.02% |
| B200_cs5 | W4 | 199.01 | 404.73 | 208.73 | 209.00 | 209.00 | 199.01 | +0.13% |
| B200_cs20 | W1 | 479.94 | 308.49 | 414.24 | 400.71 | 303.60 | 248.07 | -36.74% |
| B200_cs20 | W2 | 479.98 | 629.83 | 527.79 | 489.97 | 489.97 | 479.98 | +2.08% |
| B200_cs20 | W3 | 231.08 | 531.57 | 246.71 | 241.85 | 253.38 | 243.06 | +9.65% |
| B200_cs20 | W4 | 199.01 | 419.73 | 208.73 | 209.00 | 209.00 | 199.01 | +5.02% |
| B400_cs5 | W1 | 479.94 | 293.49 | 339.91 | 388.42 | 285.40 | 233.07 | -16.04% |
| B400_cs5 | W2 | 479.98 | 614.83 | 540.34 | 499.92 | 499.92 | 479.98 | -7.48% |
| B400_cs5 | W3 | 231.08 | 516.57 | 267.46 | 252.36 | 254.44 | 213.06 | -4.87% |
| B400_cs5 | W4 | 199.01 | 404.73 | 218.62 | 218.95 | 218.95 | 199.01 | +0.15% |
| B400_cs20 | W1 | 479.94 | 308.49 | 354.85 | 403.42 | 300.40 | 248.07 | -37.41% |
| B400_cs20 | W2 | 479.98 | 629.83 | 555.19 | 499.92 | 499.92 | 479.98 | +4.15% |
| B400_cs20 | W3 | 231.08 | 531.57 | 269.05 | 252.63 | 264.10 | 243.06 | +14.29% |
| B400_cs20 | W4 | 199.01 | 419.73 | 218.62 | 218.95 | 218.95 | 199.01 | +10.02% |

P3b behaviour (`results/b2/summary.json` `cells`, P3b): W1 promotion rate 1.0 in all settings; mean time to promotion 855.3 (B=200) and 781.1 (B=400) versus P3's 1390.9 and 1351.6 in B1. W3 promotion rate 0.238 (B=200) and 0.322 (B=400); mean rollbacks 0.238 and 0.322; mean switches 0.476 and 0.644. W2 and W4: no promotions. Mean labels about 199.8 (B=200) and 398.7 to 398.9 (B=400); budget violations 0.

Validity: P3 and P3b false-promotion 0/500 in W2 and W4 in every setting; Clopper-Pearson 95% upper bound 0.005974 <= alpha (`results/b2/summary.json` `validity_check`). The B2 protocol also required repeating the exact-null unit test with the new cap on a boundary null (E[D]=0); that test is `tests/promising_directions/test_b1_certified_switching.py::test_p3b_boundary_null_false_promotion_rate` (2500 paths, asserts rate <= alpha + 3 SE). It passed in the orchestrator's run of the full suite at commit `041bc26`, where 19 of 19 tests passed. The rate itself is not saved as an artifact.

Decision: Q1 MIXED. P3b passes all three criteria only in B200_cs5; it misses the 10% bar in the other three settings (9.65%, 7.88%, 7.67%), and at B400_cs20 W3 (+14.29%) and W4 (+10.02%) it is more than 10% worse than BEST (`results/b2/NOTES.md`; `RESEARCH_LEDGER.md`). The W3 (reversing) rollback cost is where P3b gives back value; the W1 gain comes from faster promotion.

## 4. Reading across rounds

- B1 and B2 use the same four worlds, a single generator, and a single fixed delay; seeds differ (20261031 vs 20261101) but the generator does not. B2 cannot count as evidence independent of B1's diagnostic.
- P5 oracle world-averaged costs (281.28 to 292.53 in B2) show remaining headroom; P3b closes part of the gap to the oracle but BEST in B2 is only the best of {P0, P1, P2}, not a published alternative (see `07_MATCHED_BASELINE_COMPARISONS.md`).
- Proof status: the supermartingale argument for P3 / P3b is an elementary written argument (`05_PAIRED_CERTIFICATION_THEORY.md`), not independently reviewed.
