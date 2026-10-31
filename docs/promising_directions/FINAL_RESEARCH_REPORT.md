# Final research report: ShiftLab promising directions (2026-10-30)

Branch `research/shiftlab-promising-directions-2026-10-30`, forked from `9cb4a1d6053e809665fc7e43040fcaafa14d75e2`.
All paths are relative to `docs/promising_directions/` unless stated. Every number below is taken from the
sources named beside it. Nothing here is confirmatory. The adversarial review (`11_ADVERSARIAL_REVIEW.md`) was
written by a Claude Sonnet instance from the same session as the artifacts; it is a critic role, not an
independent or human review.

## 1. Executive decision

**Classification: BENCHMARK / NEGATIVE-RESULT PIVOT.** This is the orchestrator's decision.

Basis (`12_NOVELTY_DECISION.md`, `04_EXACT_ORACLE_SEPARATION.md`, `08_SYNTHETIC_DEVELOPMENT.md`, `11_ADVERSARIAL_REVIEW.md`):

- No defensible new method was found.
- Lane A (joint acquisition + switching) is closed at the programme's risk levels (alpha in {0.05, 0.10}). A
  residual is INCONCLUSIVE at alpha = 1/5 (A1b: 0.500% at T=6 rising to 4.641% at T=11; zero gap at alpha = 1/10 for T=9..11).
- Lane B certified switching (P3b) cuts world-averaged net cost by 7.67% to 10.20% against the best of never / always / incumbent-alarm
  (B2). It ties an untuned fixed-sample paired batch test from the adversarial review (7.3% to 9.3% reduction; within
  0 to 0.9 percentage points of P3b, i.e. -0.2 to 3.0 cost units; critic's numbers, `results/adversarial_review/`). The tie suggests the gain
  comes mostly from disagreement-gated paired querying and a paired statistic rather than from anytime-valid sequential testing, but this is an inference. The 10% bar was met in one of four settings.
- H2c and HG are retained as component-level benchmarks (compositions of known ingredients; H2c reverses on exposed Gas; HG loses to PH/CUSUM and is invalid under dependence).

Why not the other classes:

- **GO / CONDITIONAL GO:** both require a candidate that passed its registered POSITIVE rule or a registered, specified path to one.
  A1 returned KILL, B1 and B2 returned MIXED, A1b returned INCONCLUSIVE. No confirmation was authorised (`09_FROZEN_CONFIRMATION.md`). The only
  unresolved lead (A1b at alpha = 1/5) needs a 20% false-promotion tolerance, which is not a programme risk level, and its increments are shrinking
  (x0.59, x0.75), so it is a theory question rather than a method lead.
- **NO-GO:** not claimed. Lane A's registered grid was shown to be weak (`11`, Q3), the paired certificate is valid under its conditional null
  (`05`), and the benchmark findings are real, so "nothing here is of value" would overstate. The A1b residual is open, not refuted.
- **BLOCKED:** work was not prevented by infrastructure. The blockers (section 9) limit real-data and baseline coverage, not the decision.

## 2. Research leaderboard

Lane codes follow `12_NOVELTY_DECISION.md` and `RESEARCH_STATE.json`. Costs are unit-free net costs per path. Metrics are never compared across rows.

| Lane | Scientific question | Best result | Strongest baseline | Exact numerical improvement | Uncertainty | Theorem status | Validity status | Novelty status | Real-data status | Compute | Limitations | Continue / stop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | Information-matched gap between joint acquisition+switching (J) and best slot-restricted calendar (C*) under the exact two-law risk game | A1: max relative gap 0.003645 (primary, 144 cells), 0.008741 (primary+secondary, 288 cells); 0 J<=C* violations. A1b at alpha=1/5: 0.500, 0.799, 1.178, 2.885, 3.889, 4.641 % for T=6..11; alpha=1/10, T=9..11: 0 | C* (`results/a1/summary.json`; `results/a1b/cells.jsonl`) | Max 0.87% vs 5% and 10% bars: KILL. A1b INCONCLUSIVE (g(11)=0.0464 < 0.05; last increment 0.0075 >= 0.0025) | Exact rationals, no sampling noise. Known-model synthetic only | Proposition A0 proved (definitional once action randomness is public); no growing-family theorem | Solver certified T8 d=1 to 4.8e-12 in source branch; J not independently dual-certified here (`04`) | Gap = known-POMDP timing adaptivity gap (standard belief-DP); no novelty | None | A1 ~27 min on 2 workers (`04`); A1b T=10 took 238 s in the critic's run (`11`) | T<=8 (A1), T<=11 (A1b); one two-regime symmetric chain; T=12 exceeded registered node cap | **Stop** as method; theory residual only |
| B | Does a valid paired certificate cut net switching cost? | B2: P3b vs BEST 10.20, 9.65, 7.88, 7.67 % reduction (B200_cs5, B200_cs20, B400_cs5, B400_cs20) | Critic's untuned fixed-sample paired batch test P6 (nv=25, thr=0.3): 9.3, 8.8, 7.9, 7.3 % | P6 minus P3b cost: +3.0 [2.4,3.6], +3.0 [2.3,3.7], -0.2 [-0.6,0.2], +1.3 [0.6,1.9] (P3b cheaper in settings 1, 2, 4; tie in setting 3) | Paired bootstrap 95% CIs; B2 P3b-BEST: -35.04 [-36.81,-33.40], -33.52 [-34.25,-32.76], -26.91 [-28.62,-25.30], -26.66 [-27.36,-25.96]. Weaker-signal generator: 3.0 to 5.4% | Elementary supermartingale argument (`05`), not independently reviewed | Conditional-null only. Boundary null (20k paths): P3b 3.05% (B=200), 2.67% (B=400); marginal null 20.8% false promotion; first promotion only | Composition of IPW paired increments, structural zeros, predictable bets (Xu et al.; CAMS); no novelty claim | None; no admissible dataset (`10`) | B1 22.28 s; B2 5.93 s | One generator, four hand-weighted worlds, fixed delay 5; BEST omits CAMS-style, SR/CUSUM, economic retraining; B2 is development round 2 informed by B1 | **Stop as method**; keep as benchmark finding |
| B-Q2 | Does known-hazard persistence-aware promotion (P4) help under reversal? | P4 minus P3 in W3: relative gain 0.24, 0.39, 0.62, 0.82 % | P3 | Bar 10%: not met. W1: P4 worse by 10.45, 22.33, 9.50, 23.93 % (bar 2%) | 500 seeds, paired bootstrap (`results/b1/summary.json` `q2_settings`) | Proposition B0 (certificate does not imply profit) | Hazard 1/150 declared, so a plug-in | Plug-in decision theory | None | Included in B1 22.28 s | Dropped from B2 | **Stop** |
| C | H2c (cost-guided discounted betting): within-class power gain | G5: +0.086 [0.059,0.113] at 10%, +0.094 [0.063,0.125] at 20% | Per-cell better of C1 discounted Kelly / C2 cost-ONS. C7a is more powerful (H2c -0.19 / -0.13) but has no guarantee | Power 0.382 / 0.640; benign FAR 0.067 at 20%; null FAR max <= 0.027; harm cells won 13/14 and 14/14 | Cluster bootstrap, 4000 resamples; per-cell comparator chosen from realised means | Cost-null validity is DOC-ONLY; no supermartingale unit test | Analysis VERIFIED by rerun; simulation partial (one cell, 3.1 s, MC-consistent) | Composition; reduces to discounted Kelly (max abs dlogW 8.9e-16); novelty claim withdrawn upstream | Exposed Gas: H2c 242 to 824 events later than cost-only Kelly/ONS; unknown nominal gives power ~ 0 for n_cal <= 1000 | Analysis rerun only | Known nominal cost, fixed delay 5, one generator family, no published-paper reproduction of a comparator | **Retain as benchmark**; stop refinements |
| D | HG (decision-aware betting) and paired/dependence monitors vs classical detectors | e15: +0.029 [0.012,0.046] (Holm p 0.004) and +0.052 [0.020,0.090] (Holm p 0.003) vs PPRM parent | Page-Hinkley / CUSUM: HG -0.066 / -0.110 (n.s.) | Harm 15% / 25% lower relative, harm worlds only (raw -28.9 / -33.9). "~21/24" is a MISMATCH (raw units over all worlds) | Recomputed 0.0288 / 0.0518; Holm family 10 | Dependence bound alpha + eps(1+(T-1)delta) read, necessary condition on power; not independently reviewed | HG invalid under dependence (FAR up to .23); cap repair VERIFIED (18 tests) | Repaired composition; beats parent but not ONS or plain discounting | CRSP RPOQ exposed: -1.15 [-1.56,-0.76] (5%), -3.21 [-5.16,-0.87] (20%) log-wealth | Analysis rerun only | Synthetic; simulation not re-run | **Retain as reference**; stop generic betting refinements |
| E | Does disagreement (structural-zero) querying beat CAMS-style querying? | Structural-zero querying is used inside P3/P3b | CAMS-style / batch paired test | P6 reaches 90% or more of P3b's gain over BEST (`11`, Q5) | See lane B | Established components (`05`) | See lane B | Not novel; CAMS is the baseline (CAMS not implemented here; audit file missing) | None | None beyond lane B | CAMS read at abstract level only | **Stop**; treat CAMS as baseline |
| F | When does a conditional alarm justify action (action-set-aware regime harm)? | Inherited stylised result, cluster 333: incumbent 601.5, conditional alarm hold100 298.0, oracle 213.4; cluster 20: 595.9 / 527.5 / 250.9 | Regime-aware oracle / no-switch | Variant B (no useful fallback): conditional alarm +6 to +10% worse | 600 paths, stylised, no label cost | None | Critic: P3b false-promotes 20.8% of 6,000 paths under a persistent-regime marginal null | Conditional monitoring plus decision theory; explanatory | None | Not re-run | Inherited, DOC-ONLY | **Benchmark / explanatory only** |
| G | Scalable risk-preserving controller with a value guarantee | Abandonment controller class matches the sequence-form reference in all tested cells (inherited); streak-class gaps 0.7248% / 1.6114% were an incomplete-baseline artifact | Exact decomposed planner | A1b found no gap at alpha in {0.05, 0.10}, so nothing material to approximate | Exact | Not entered (A3 approximation declined) | n/a | n/a | None | Not entered | Not entered | **Stop** |

Notes on the lane B row: the sign convention in the "exact numerical improvement" cell follows `11`, Q5 ("P6 nv25 thr0.3 minus P3b: +3.0, +3.0, -0.2, +1.3", so P3b is the cheaper policy in settings 1, 2 and 4).
With in-sample tuning (an optimistic bound for the baseline) P6 ties or beats P3b by up to 2.8 cost units at B=400.

## 3. Main results (artifacts and sha256)

Never compare metrics across tasks. Each subsection stands alone. Artifacts are under `results/`. All studies are development, not confirmatory.

### A1: exact joint vs best-calendar (Lane A)

Protocol `protocols/A1-exact-separation.md` (commit `0d03912`, sha256 `35b0db11...edc64` as truncated in `04`). Solver `2bd2e8e41639073c8d22ffb17ef0bcc68111e321`.

| Part | Cells | J<=C* violations | Gap > 0 | Max relative gap |
|---|---|---|---|---|
| Sanity | 2 + 3 checks | 0 | n/a | reproduced 22083523/7812500 and 6744087/781250000 |
| Primary (d=2) | 144 | 0 | 8 | 0.003645 (10787546091/2959163041129) |
| Secondary (d=1) | 144 | 0 | 15 | 0.008741 (22608701046/2586568221299) |
| Adversarial (T=6,B=3,d=2, seed 20261030) | 200 | 0 | 0 | 0 |

Decision rule returned KILL. No cell reached 0.05 or 0.10. Wall clock about 27 min on 2 workers.

| File | sha256 |
|---|---|
| `results/a1/summary.json` | `5e121765c7550b9aff813bbc8c339e0cecda5b546ad6a85465126d3fe237a2b5` |
| `results/a1/primary.jsonl` | `1ddbfae75d405e6d77a3fc3a706d5ee6de0b19a7748a6362718285520b946d3d` |
| `results/a1/secondary.jsonl` | `bcc66db3d2a034bda7b629955fddd57db0bff2253799d68af1a9cd52e3524914` |
| `results/a1/adversarial.jsonl` | `ab72d15898c46bb3feef08b6798b89e368764954b77addc899fea586f16cafd2` |
| `results/a1/sanity.json` | `d619ce4a57cf03a6debf1d5cd457d0c7b41b7ed4f7176bcc02675909b9d21d2d` |

Disclosed asymmetries (`11`, Q2): the calendar is chosen as a minimum after seeing each cell (oracle choice), and the coin-aware empty branch saves up to about 0.04 of query cost. Both bias the gap downward. They can only help the KILL.

### A1b: growing family (Lane A)

Protocol `protocols/A1b-growing-family.md` (commit `e9c4fef`). Family: B=3, d=1, transition 1/20, emissions (1/50, 49/50), c_q 1/100, c_s 1/20, prior1 1/5.

| alpha | T=6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|
| 1/5 | 0.500% | 0.799% | 1.178% | 2.885% | 3.889% | 4.641% | not run (registered node cap exceeded) |
| 1/10 | - | - | - | 0 | 0 | 0 | - |

Mechanical decision INCONCLUSIVE: increments 0.0171, 0.0100, 0.0075; CONTINUE needs g >= 0.10 or g(T_max) >= 0.05 (0.0464 fails); KILL needs last increment < 0.0025 (fails). Best calendar moves from [1,2,3] to [2,3,4] at T >= 10. J <= C* in every solved cell.
The run crashed at T=12 (runner caught only MemoryError); T=12 was recorded as failed, not retried with altered settings; exception handling was then widened and the run resumed. `results/a1b/run1_crash.log` and `run2.log` are kept.

| File | sha256 |
|---|---|
| `results/a1b/cells.jsonl` | `0d8fe33dfe741c6bc48055375dc3a024b09fe9f8369e5b61014f733c41aaeb89` |

`results/a1b/provenance.json` records solver commit `2bd2e8e41639073c8d22ffb17ef0bcc68111e321` and file hashes (`causal_switching_game.py` `54b1347c3e213407b3feb09a801dc9ea40b3663fe6a4a227b7878b9b0a2d770a`; `decompose_switching_calendar_gap.py` `16dc05e76e94b8b02684609de767596a7ea0b5111e6dbf376ec741226777ece4`).

### B1: certified switching (Lane B round 1)

Protocol `protocols/B1-certified-switching.md` (commit `1a742dc`, sha256 `98f85250a95ae6e31857760ca33f2ebe1dc0c042762469b7d8f84cd557a82757`). T=2000, delay 5, c_q=0.05, B in {200,400}, c_s in {5,20}, alpha 0.05, 500 seeds, seed base 20261031, 2000-resample paired percentile bootstrap. Runtime 22.28 s.

| (B, c_s) | BEST | BEST cost | P3 cost | P3 reduction vs BEST | CI of P3-BEST |
|---|---|---|---|---|---|
| B200_cs5 | P2 | 343.20 | 331.71 | 3.35% | [-13.15, -9.86] |
| B200_cs20 | P0 | 347.68 | 335.50 | 3.50% | [-12.78, -11.57] |
| B400_cs5 | P2 | 340.62 | 340.13 | 0.14% | [-2.16, 1.08] |
| B400_cs20 | P0 | 347.68 | 343.97 | 1.07% | [-4.25, -3.10] |

Decisions: Q1 MIXED (max 3.5% vs 10% bar); Q2 NOT SUPPORTED; validity gate passed (0/500 false promotions in W2 and W4, Clopper-Pearson upper bound 0.005974), but the critic showed W2/W4 are slack nulls (E[D] = -0.05, -0.10), so that gate was uninformative.

| File | sha256 |
|---|---|
| `results/b1/summary.json` | `0062aec5eeba38caf93cdc69d307c9b957928ba0450b9911447566fc010a562e` |
| `results/b1/per_seed.npz` | `18d9d45ee81b08feaec04c06f4b4494648a00507b55a86409641cf8130994183` |
| `results/b1/IMPLEMENTATION_NOTES.md` | `49b1e3a074767a512b8fcacc6904cdd17e97a7cc95d2eabd0a577004cf007336` |

B1's counterfactual diagnostics (delay 1, c_q=0, p_min=0.5) were not saved (`results/b1/IMPLEMENTATION_NOTES.md`).

### B2: propensity-matched cap (Lane B round 2)

Protocol `protocols/B2-propensity-cap.md` (commit `af14d5a`, sha256 `533a529ddda537ce8b925fdaf6b0b503cce46797ade2c7ca0d5a9b95202b6844`). Seed base 20261101, 500 per cell. Runtime 5.93 s. **B2's single change was motivated by B1's post-hoc diagnostic: development round 2, not confirmation.**

| (B, c_s) | BEST | BEST cost | P3b cost | P3b reduction | P3b-BEST [95% CI] | 10% bar | All 3 criteria |
|---|---|---|---|---|---|---|---|
| B200_cs5 | P2 | 343.49 | 308.45 | 10.20% | -35.04 [-36.81, -33.40] | met | yes |
| B200_cs20 | P0 | 347.50 | 313.99 | 9.65% | -33.52 [-34.25, -32.76] | no | no |
| B400_cs5 | P2 | 341.58 | 314.68 | 7.88% | -26.91 [-28.62, -25.30] | no | no |
| B400_cs20 | P0 | 347.50 | 320.84 | 7.67% | -26.66 [-27.36, -25.96] | no | no (W3 +14.29%, W4 +10.02% vs BEST) |

Decision: Q1 MIXED. Oracle P5 costs 281.28 to 292.53. Validity: 0/500 in W2/W4 (slack nulls). Reproducibility: the B1 default-mode rerun matches B1 `summary.json` after removing volatile `meta` and all per-seed arrays bit-for-bit (`results/b2/NOTES.md`). No confirmation authorised.

| File | sha256 |
|---|---|
| `results/b2/summary.json` | `4af87b4fad2d9ca2ac5cfe32616728ba1fea0f0a3d98db06d38cbede2441b488` |
| `results/b2/per_seed.npz` | `a7263c0bbfea46d7fe1219e0835b108c7024763baf92a6a3cdd7c4da09c1eed3` |
| `results/b2/NOTES.md` | `8f276be61cb73d4abebd9001581f87a61d55a3e257515bf5764b71ddf09e25d4` |

### Adversarial comparison (critic scratch code, not in repo)

Same B1 streams, seed base 20261101. World-averaged cost, P3b vs critic baselines (`11`, Q5):

| (B, c_s) | BEST | P3b | P6 nv25 thr0.3 (untuned) | P6 in-sample best | P2g |
|---|---|---|---|---|---|
| 200, 5 | 343.5 | 308.5 | 311.4 | 307.0 | 317.0 |
| 200, 20 | 347.5 | 314.0 | 317.0 | 314.1 | 321.8 |
| 400, 5 | 341.6 | 314.7 | 314.5 | 311.8 | 328.4 |
| 400, 20 | 347.5 | 320.8 | 322.1 | 321.3 | 333.9 |

The scratch scripts (`a1_probe.py`, `val.py`, `marg.py`, `bl.py`, `cmp.py`, `alt.py`) live in a temporary scratchpad outside the repository; these numbers have no saved artifact in this repo.

## 4. Theoretical findings

Sources: `03_FORMAL_PROBLEM_AND_INFORMATION_CONTRACT.md`, `05_PAIRED_CERTIFICATION_THEORY.md`, `11_ADVERSARIAL_REVIEW.md`. None is independently reviewed. None is claimed as novel.

**Proposition A0 (information equivalence).** If the query rule's information `G_t` contains `X_{1:t}`, `U_{1:t}`, `Q_{1:t-1}` and every released label, then `G_t = H_t`, and history-adaptive acquisition plus optimal switching equals the joint class `Pi_J`. Hence an information-matched gap can only arise from (iii) coarser acquisition information (calendar or open-loop timing) or from optimisation-procedure effects (ii); a gap from a surrogate objective (iv) is classical value-of-information misalignment.
Critic's correction (`11`, Q1; adopted in commit `099e77a`): the proof needs every randomised action (promotion, rollback, root-mixture calibration coin) to draw its randomness from the recorded public `U`. If an action rule uses a private coin invisible to the acquisition rule, (i) can fail. Under that assumption (i) is close to a tautology. Further critic points: A1's comparator `CalendarOpportunityGame` restricts only the set of query slots, so it is a slot-restricted adaptive class and not the open-loop `G_t = time` class that A0(iii) describes. The open-loop gap is larger in the critic's slice (4.56% vs 3.89% at T=10; 2.08% vs 1.18% at T=8; 1.75% vs 0.50% at T=6). `03` has not been rewritten to define the slot-restricted class (open correction).

**Proposition B0 (certificate is not profit).** A level-alpha certificate that `D_s > 0` on average up to `tau` implies nothing about future benefit without a persistence assumption, a drift bound, or a rollback option. Counterexample: advantage `+delta` for `s <= tau*`, `-delta` afterwards, `tau*` unknown to the learner; switching at `tau` gives future benefit `delta(tau* - tau) - delta(T - tau*) - c_s`, negative when `tau* - tau < (T - tau*) + c_s/delta`, while the certificate stays valid. With persistence `m` and constant advantage `delta`, switching is profitable in expectation when `rho delta m > c_s + (1-rho) * (expected loss until rollback)`.

**Paired-certificate validity claim (`05`).** Setting: 0/1 loss, one incumbent and one candidate, `D_t in {-1,0,1}`, agreement `G_t` observed free with `D_t = 0` on agreement, query probability `p_t` that is `H_t`-measurable with `p_t >= p_min` off-agreement, IPW increment `Z_t = (1-G_t) Q_t D_t / p_t` released at `t+d`, bets `lambda_t in [0, p_min/2]` fixed at issue.
Under the fixed-delay conditional null `E[D_t | H_{t+d-1}^{(-t)}] <= 0` for every t, the wealth `W_n` is a nonnegative supermartingale, and Ville's inequality bounds first-promotion probability by alpha. B2's cap `q_t/2` preserves positivity because `|Z_t| <= 1/q_t`.
Scope limits: (1) outcome-dependent delays and post-issue covariates are not covered; (2) it is a conditional null, not a stationary marginal null (dependence-gate bound `alpha + eps(1 + (T-1) delta)`); (3) only the first promotion is covered; repeated promote/rollback needs alpha spending, and B1/B2 report wrong promotions empirically; (4) certificate does not imply profit (B0).

Critic's validity checks (`11`, Q4; 20,000 paths, T=2000, alpha 0.05, boundary null E[D]=0):

| Policy | B=200 | B=400 |
|---|---|---|
| P3 | 1/20000 | 0/20000 |
| P3b | 610/20000 = 3.05% (CP95 upper 3.26%) | 533/20000 = 2.67% (CP95 upper 2.86%) |

Nonstationary null (E[D_t] alternating between -0.2 and 0; per-step, 50-step blocks, iid random; 20,000 paths each): P3b 1/20000, 0, 0 at B=200 and 0, 0, 0 at B=400. No violation.
**Marginal null fails:** with a persistent latent regime (E[D] = +0.18 w.p. 0.2, -0.20 w.p. 0.8; marginal mean -0.124), P3b promoted in 20.8% of 6,000 paths, all in the positive regime. Any certificate claim must be written as conditional-null only. Unit test `test_p3b_boundary_null_false_promotion_rate` (2500 paths, asserts rate <= alpha + 3 SE) passed at `041bc26` but its rate was not saved as an artifact (`08`).

**Open proof obligations.**
1. Anytime-valid lower bound on future cumulative advantage `sum_{s=t+1}^{t+m} D_s` under a nonparametric persistence class. Under bounded drift kappa and past-mean lower bound LB over window w, `E[sum_{j=1}^m D_{t+j} | F_t] >= m LB - kappa m (w+m+1)/2` is elementary but does not identify kappa. A nontrivial result needs a quantitative minimax rate in kappa, B, d, c_s with matching bounds (`05`).
2. Independent review of the supermartingale argument, including the implemented timing (the critic read the code and found no future-label leakage, `11` Q4 and Q8; this is not formal verification).
3. Dependence: validity under dependent outcomes (HG fails with FAR up to .23); the H2c cost null has no unit test.
4. Multi-cycle promotion/rollback bound (alpha spending) for P3b.
5. Lane A: does the adaptivity gap scale with T at loose alpha, and why does tightening alpha to 1/10 remove it? Needs an analytical bound or a larger registered node cap.

## 5. Negative findings

1. A1: joint planner beats the best slot-restricted calendar by at most 0.003645 (d=2) and 0.008741 (d=1) over 288 exact cells; 0 of 200 adversarial instances show a gap.
2. A1b: gap needs alpha = 1/5; at alpha = 1/10 it is exactly 0 for T=9..11. Increments shrink (x0.59, x0.75). Verdict INCONCLUSIVE, not a method lead.
3. Streak-controller gaps of 0.7248% and 1.6114% against the sequence-form reference were an incomplete-baseline artifact (closed by abandonment controllers); they are not joint-vs-separable gains.
4. B1: certified switching with cap `p_min/2` reduces cost by only 0.14% to 3.50% and is worse than never switching under a weaker-signal generator (P3 -2.6% to -4.2% relative reduction, critic's alternate generator).
5. B2: P3b passes all registered criteria in one of four settings; at B400_cs20 it is 14.29% (W3, reversal) and 10.02% (W4, benign) worse than BEST.
6. B-Q2: known-hazard persistence-aware promotion gains 0.24% to 0.82% in the reversing world and loses 9.50% to 23.93% in the useful-persistent world.
7. The P3b headline gain does not need the e-process: an untuned fixed-sample paired batch test reaches 7.3% to 9.3%. The gain is generator-specific (3.0% to 5.4% under a weaker paired signal).
8. P3b's guarantee is conditional-null only: 20.8% false promotion under a persistent-regime marginal null (6,000 paths).
9. H2c: reduces exactly to discounted Kelly with a substituted moment ratio; guidance helps +0.03 to +0.14 only when Brier co-shifts and loses up to 0.59 when flat or opposed; reverses on exposed Gas (242 to 824 events later); power ~ 0 with unknown nominal at n_cal <= 1000; valid restart mixtures add only +0.003 / +0.009 / +0.023 (noise).
10. HG: not better than Page-Hinkley/CUSUM (-0.066 / -0.110, n.s.); does not beat ONS or plain discounting; invalid under dependence (FAR up to .23). "Harm reduction ~21/24" is a unit mismatch.
11. RPOQ on exposed CRSP: -1.15 [-1.56, -0.76] and -3.21 [-5.16, -0.87] log-wealth against uniform; sign flips with design (+0.215 vs -0.120 in synthetic worlds).
12. Gas: 12.342% challenger gain (3403 -> 2983 errors over 7977) is predictive headroom; the clairvoyant switching headroom is 0.972% (2955 vs 2984) with switch cost 1 and no label cost. Bike and Beijing show no headroom and raw data is absent.
13. Registered grid weakness (critic): the three-point monotone-in-T rule is underpowered and the adversarial A1 set (T=6, B=3, d=2) was nearly vacuous.

## 6. Publication assessment

No acceptance predictions are made.

| Venue type | Assessment |
|---|---|
| Method paper (ML or statistics main track) | **Not supported.** No registered POSITIVE rule was met. No component is new (`05`, `02`, `12`). The best Lane B result ties a simple baseline and is generator-specific. No real-data evidence. Lane A has no gap at programme risk levels. |
| Theory paper | **Not supported.** A0 is close to a tautology and B0 is elementary decision theory. The only candidate (growing-family adaptivity gap at loose alpha, or a minimax rate for certified switching) is unproved and not started. |
| Benchmark / negative-results paper (workshop or datasets-and-benchmarks style) | **The defensible option**, provided it states its scope honestly. It would contain: (a) the information-contract formalisation and Proposition A0 with the public-randomness assumption; (b) the exact A1/A1b separation study with all 488 A1 cells plus the A1b slice, including the grid-sensitivity finding (alpha = 1/5 versus programme levels) and the incomplete-baseline artifact; (c) the B1/B2 certified-switching benchmark with the critic's fixed-sample batch baseline and the cost-of-guarantee comparison (P3b versus P6), the cap lesson (3.5% to about 9% from propensity-matched caps), and generator sensitivity (3.0% to 5.4%); (d) validity-gate lessons (slack nulls are uninformative; boundary null 3.05% / 2.67%; marginal null 20.8%); (e) H2c and HG as component-level baselines with verified analysis-level reruns and their negative real-data and dependence results; (f) the real-data limitation (no admissible dataset). Prerequisites that are open: independent review of the critic role, faithful reproductions of the eleven missing comparators, a structurally distinct registered generator, and an unexposed real dataset with chronology and label-timing documentation. |
| Workshop short paper on the cap lesson | Possible in principle; it would have to report the P3b versus P6 tie and the weaker-signal generator result up front. |

## 7. Next research recommendations (at most three, ranked)

Any further work needs a new registered question and a new protocol. The loop terminated at a decision point.

1. **Benchmark release with the missing baselines (highest value, lowest risk).** Add CAMS-style disagreement acquisition with a non-certifying switching rule, an SR/CUSUM paired e-detector trigger, an economic retraining rule, state-independent adaptive acquisition, and standalone always-query and immediate-deploy rows, on a structurally distinct, pre-registered generator with fresh seeds. Evidence: P6 captures 90% or more of P3b's gain and BEST in B1/B2 omits these comparators (`07` section 3; `09` section 3; `11` Q5, Q6).
2. **Real-data admissibility audit before any real-data claim.** Run the action-headroom, chronology, leakage and dependence audits of `10` section 5 on datasets not yet exposed, with a go/no-go threshold stated before touching the test window. Evidence: the only recorded headroom number relevant to switching is 0.972% on exposed Gas, with no label cost; the other inventory datasets have no recorded assessment (`10`).
3. **Lane A theory residual only (not a method).** Prove or refute growth of the timing-adaptivity gap with T at loose alpha, and explain why alpha = 1/10 gives zero gap. Requires an analytical bound or a registered larger node cap (T=12 exceeded the cap). Evidence: A1b increments 0.0171, 0.0100, 0.0075 with g(11) = 4.641%; zero gap at alpha = 1/10 through T=11 (`12`). Treat as optional; stop if the gap plateaus below the 5% bar.

## 8. Reproducibility

- **Branch:** `research/shiftlab-promising-directions-2026-10-30`; fork point `9cb4a1d6053e809665fc7e43040fcaafa14d75e2`.
- **Commits** (`git log --oneline 9cb4a1d..HEAD`, newest first):

```
099e77a Make public-randomness assumption explicit in Proposition A0; close lane G
6ab2e05 Execute A1b growing-family test: inconclusive at alpha=1/5, zero gap at alpha=1/10; record lane decisions
e9c4fef Record adversarial review; register A1b growing-family protocol and runner
939d5bf Record matched comparisons, synthetic development, confirmation status, real-data limits
041bc26 Execute registered B2 propensity-cap rerun: Q1 mixed (7.7-10.2% net-cost reduction)
af14d5a Register B2 propensity-matched bet cap development protocol
d2e6574 Execute registered B1 certified switching study: Q1 mixed, Q2 not supported
5f08250 Record paired-certification validity statement and scope
1a742dc Register B1 certified-switching development protocol
b050f95 Execute registered A1 exact separation kill test: KILL (max gap 0.87%)
05956c7 Record literature and novelty equivalence audit
695a566 Record repository audit, evidence matrix, formal contract, H2c/HG reproduction status
0d03912 Register A1 exact joint-vs-calendar separation protocol
20544b7 Add resumable promising-directions research loop with smoke cycle
```

  This report is not committed by its author; the orchestrator commits it.
- **Environment:** Windows 11 Home; Python 3.13.1 system interpreter; exact solver worktree at `2bd2e8e41639073c8d22ffb17ef0bcc68111e321` (branch `research/risk-preserving-switching-approx-2026-10-29`); H2c analysis worktree `branch-research-h2c-strong-baselines-and-generalization-2026-10-30` at `60930a4`. No GPU is used.
- **Seeds:** A1 adversarial 20261030; B1 20261031 (default); B2 20261101; critic scratch runs seed base 20261101. A1 primary/secondary/A1b are exact rational solves with no sampling seed.
- **Execution provenance:** the loop (`research_loop.py`) itself ran only the smoke cycle `cycle-0001-C0-smoke` (plumbing, not scientific evidence). A1, B1, B2 were executed by subagents and A1b by the orchestrator directly, outside the loop scheduler, and recorded in `RESEARCH_LEDGER.md` with the sha256 values in section 3. The adversarial review was a separate critic role.

Commands (run from the repository root of this worktree, `C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-promising-directions-2026-10-30`):

```
# loop tests and status
python -m pytest tests/promising_directions -q
python scripts/promising_directions/research_loop.py status

# A1 (parts; outputs default to docs/promising_directions/results/a1; --workers is capped at 2)
python scripts/promising_directions/a1_exact_separation.py --part sanity
python scripts/promising_directions/a1_exact_separation.py --part primary --workers 2
python scripts/promising_directions/a1_exact_separation.py --part secondary --workers 2
python scripts/promising_directions/a1_exact_separation.py --part adversarial --workers 2

# A1b (writes docs/promising_directions/results/a1b/cells.jsonl and provenance.json)
python scripts/promising_directions/a1b_growing_family.py

# B1 (default seed base 20261031, 500 seeds, out dir results/b1)
python scripts/promising_directions/b1_certified_switching.py --seeds 500 --workers 2

# B2
python scripts/promising_directions/b1_certified_switching.py --b2 --seed-base 20261101 --seeds 500 --workers 2 --out-dir docs/promising_directions/results/b2

# H2c analysis-level recompute (inherited, from the h2c worktree)
cd ../branch-research-h2c-strong-baselines-and-generalization-2026-10-30; PYTHONPATH=src python scripts/sota_search/g5_confirmation_analysis.py

# artifact checksums
python scripts/promising_directions/verify_artifacts.py
```

Notes: the A1 solver path defaults to `a1.DEFAULT_SOLVER_ROOT` (the `2bd2e8e` worktree) and the runner verifies both pinned file hashes. The B1 raw `summary.json` sha256 cannot be reproduced byte for byte on a rerun because `meta` fields (`created_utc`, runtime, `repo_head`) are volatile; compare after removing `meta` (`results/b2/NOTES.md`). The H2c simulation was not re-run in full; only the analysis on the stored per-seed parquet (sha256 `ed5923e9486c6bc9c8a0d1497f68c74563a4221f5644721f508dfd7fbbf66ba7`; cells CSV `81c8e39d6afc29ce88a62a28d42395d11cc3661af2ff538e0978c0e04c1877b6`) and one cell (3.1 s) were checked. No manifest for the G5 simulation exists in that repository.

## 9. Terminal report

1. **Branch and SHA:** `research/shiftlab-promising-directions-2026-10-30`, report committed at `1a717bcd04a0fdc9b9908e430d8e27b3f39962d5` (branch tip is the following commit, which only fills in this SHA).
2. **Cycles completed:** 1 loop-scheduled smoke cycle (`cycle-0001-C0-smoke`, plumbing only) plus 5 registered research executions: A1, B1, B2, A1b and the adversarial review. A1, B1, B2 and A1b ran outside the loop scheduler and are recorded in `RESEARCH_LEDGER.md`.
3. **Implemented:** resumable research loop with state, smoke cycle and artifact verification (`research_loop.py`, `run_one_cycle.py`, `verify_artifacts.py`); A1 exact-separation runner; A1b growing-family runner; B1/B2 certified-switching simulator and policies P0-P5 and P3b; unit tests under `tests/promising_directions/` (the full suite was recorded as 19 of 19 passing at `041bc26`); documents `00` to `12` and four registered protocols.
4. **Executed:** A1 (488 exact cells plus sanity), A1b (10 planned cells; T=12 failed on the node cap), B1 (500 seeds x 4 worlds x 4 settings), B2 (same design, fresh seeds), adversarial review with critic reruns, H2c analysis-level recompute, HG e15 analysis recompute, one H2c single-cell simulation check.
5. **Strongest verified findings:** (a) exact A1 gap at most 0.003645 (d=2) and 0.008741 (d=1) with 0 J<=C* violations; (b) P3b cuts net cost 7.67% to 10.20% against best of never/always/incumbent-alarm in a development generator, all CIs excluding 0; (c) P3b false-promotion at the boundary null is 3.05% (B=200) and 2.67% (B=400) at 20,000 paths, within alpha = 5%; (d) the H2c G5 numbers reproduce at analysis level (+0.086 / +0.094).
6. **Strongest negative findings:** the P3b gain is matched by an untuned fixed-sample paired batch test (7.3% to 9.3%) and shrinks to 3.0% to 5.4% under a weaker paired signal; the certificate fails under a persistent-regime marginal null (20.8% false promotion); Lane A has zero gap at alpha = 1/10 through T=11 and only an INCONCLUSIVE shrinking-increment residual at alpha = 1/5; H2c reverses on exposed Gas and reduces to discounted Kelly; HG loses to PH/CUSUM and fails under dependence.
7. **Novel method found:** no.
8. **Real data:** none newly run; only inherited exposed results (Gas, CRSP) are cited, none confirmatory.
9. **Blockers:** no `claude` CLI on PATH; Bike and Beijing raw data absent; CRSP is exposed; exact solver node cap exceeded at T=12; published baselines (CAMS, Active RCPS full, PPRM faithful, PR monitoring, e-detector mappings, and others listed in `07` section 3) not faithfully reproduced.
10. **Report location:** `docs/promising_directions/FINAL_RESEARCH_REPORT.md` (uncommitted).
11. **Loop status:** terminated normally at a decision point (`stop_reason` `queue_empty`, `next_task` null in `RESEARCH_STATE.json`). Further work needs a new registered question.

## 10. Addendum after the report (A1c, A1d)

Lane A follow-up probes are recorded in `12_NOVELTY_DECISION.md` (A1c / A1d addendum) and
`RESEARCH_LEDGER.md`.

**A1c, alpha scan.** Under a binding false-promotion constraint, the joint planner beats the
best pure calendar by up to 6.1%. Without the constraint the gap is only 0.9–1.6%.

**A1d, public-coin calendar mixtures.** The gap survives convexification:

- g_mix is up to 5.8% at alpha between 1/4 and 1/2.
- That is an excess of up to 4.7 percentage points over the unconstrained gap.
- The registered decision is H-risk SURVIVES.

**What this changes.** Lane A moves from "closed" to "open theory lead". The lead is a
risk-specific timing-adaptivity separation, plausibly risk-ledger-dependent acquisition. Its
limits:

- One family.
- T ≤ 12.
- alpha ≥ 3/20, which is above the programme's 0.05/0.10 levels.
- All gaps are below the 10% practical threshold.
- No theorem.

**What it does not change.** The executive classification stays BENCHMARK / NEGATIVE-RESULT
PIVOT, and no method claim is made.

**Recommended next step (A2).** Two parts:

- Seek a growing-family lower bound on g_mix that vanishes when the constraint is slack.
- Check whether the effect persists at alpha in {0.05, 0.10} in families where those levels bind.

## 11. Addendum (A2)

**A2 screen.** 162 exact cells at T = 8, B = 3. At the programme's risk levels the gap between
the joint planner and the best fixed calendar is exactly 0 in all 54 families, at both
alpha = 0.05 and 0.10. This is non-vacuous: the optimum is a three-query confirmation burst that
does not depend on the labels. Without the constraint, the gap is positive in 31 of 54 families,
up to 4.37%. Decision: CONFINED TO LOOSE ALPHA.

**Theory.** `13_A2_BRANCH_CONFLICT_THEORY.md` proves the convexity of the value functions, a
lemma that bounds how much public-coin calendar mixtures can close the gap, and a branch
decomposition of each calendar's loss. These explain a three-regime picture:

- tight alpha: calendar-optimal;
- intermediate alpha: branch-conflict gap of at most about 5.8%;
- unconstrained: ordinary adaptivity gap.

**Lane A final status.** No method claim. There is a possible structural result: a conjectured
proposition that calendars are exactly optimal below a risk threshold. It needs a proof and a
literature audit. The executive classification is unchanged: BENCHMARK / NEGATIVE-RESULT PIVOT.
