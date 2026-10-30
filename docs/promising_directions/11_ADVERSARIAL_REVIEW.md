# 11 Adversarial review of A0/A1 and B1/B2

Reviewer disclosure: this review was written by a Claude Sonnet instance from the same session that
produced the artifacts. It is a separate critic role, not an independent reviewer. It shares the
author's training and blind spots. Nothing here was checked by a human or an external model.
Review target: worktree HEAD `041bc26`. Nothing was committed or edited besides this file.

Scratch code (not in the repo) is in
`C:/Users/nigel/AppData/Local/Temp/claude/C--Users-nigel--claude-spares-spare-pRRYr0/7448219d-2c99-41aa-a896-938dd5442ee1/scratchpad/`:
`a1_probe.py` (exact solves), `val.py` (null validity), `marg.py` (marginal null), `bl.py` and `cmp.py`
(extra baselines), `alt.py` (alternate generator). All outputs below come from running these. The
A1 numbers use the pinned solver `2bd2e8e` imported directly, with my own `Forced` subclass.

## Q1. Is Proposition A0(i) correct?

Verdict: UPHELD as stated, but it is close to a tautology and the surrounding text overstates what
A1 tested.

Evidence.
- Statement (i) is true. `G_t` is defined as a sub-sigma-field of `H_t` that contains every generator
  of `H_t` apart from `A_{1:t-1}`. So `G_t = H_t` follows once `A_{1:t-1}` are shown to be functions of
  those generators. That is the induction, and it works.
- The action at `t` may depend on `Q_t` without breaking the induction. `Q_t` enters `H_{t+1}`
  explicitly. Labels released at `t` are already inside `H_t` (`R_s <= t`). The solver also lets
  `(action, query)` be chosen jointly at one information set (`CausalSwitchingGame.choices`), which
  is the same class.
- The proof needs an unstated assumption. Action randomisation must come from the public `U`. Section 1
  introduces `U_t` only for `Q_t`. If `A_t` uses its own coin, the induction fails unless that coin is
  added to the generator list.
- Root-mixture calibration does not need private randomisation. The root coin is a single shared
  public coin. On the inactive branch the policy never queries and never promotes
  (`continue_metrics`). Nature's information set contains the realised `(action, query)` history. So
  nature may see the coin, and the risk is still `a * sup r`, which is at most alpha.
- The real problem is that (iii) and A1 do not match. A0(iii) describes the calendar as
  "`G_t` = time". The A1 comparator `CalendarOpportunityGame` restricts only the set of query slots.
  The skip decision, the actions and all later releases are fully history-adaptive. In addition, the
  root-mixture "continue" branch queries nothing, so C* is effectively a coin-aware mixture of
  `{calendar, empty}`.
- A true open-loop calendar (queries forced at the slots, `G_t` = time) is a strictly weaker class.
  I implemented it as `Forced`. On the gaps below it is always at least as large as the skip-calendar
  gap, and often several times larger.

Required corrections.
- State in A0 that action randomisation is part of `U`.
- Say plainly that (i) is definitional.
- Rewrite (iii). Either define the "slot-set-restricted adaptive" class A1 actually used, or report the
  open-loop gap as well.

## Q2. Does the A1 comparator get information J lacks, or vice versa?

Verdict: UPHELD, with two small asymmetries that favour the calendar.

Evidence.
- C* is a restriction of the same sequence-form game (same information sets, same null opponent,
  same calibration). The decomposed J is the same game with the post-promotion part solved by belief
  DP. J <= C* held in all 488 cells, and many cells match exactly. The T6B3 and T8B4 sanity values were
  reproduced in exact rationals. I found no information advantage for J.
- Asymmetry 1: the calendar is chosen as `min` over all calendars after seeing the cell's cost. This
  is an oracle choice and favours the separable class.
- Asymmetry 2: the coin-aware empty branch (see Q1) saves up to `(1-a) * |cal| * cq` of query cost.
  That is at most about 0.04 here, which is small next to the J values near 1.2-4.
- Both asymmetries bias the gap downward, so they cannot create a false gap. They can only help the KILL.

Required correction. Disclose both asymmetries in `04`.

## Q3. Is the A1 KILL an artifact of the grid?

Verdict: WEAKENED. The KILL is a correct mechanical output on the registered grid. The registered
grid cannot support "no separation survives".

Evidence (new exact solves; skip-calendar relative gap `g`, open-loop forced-calendar gap in brackets):

| Slice (exact) | T=6 | T=7 | T=8 | T=9 | T=10 |
|---|---|---|---|---|---|
| B=3, d=1, trans 1/20, e=(1/50,49/50), prior1 1/5, cs 1/20, alpha 1/5 | 0.50% (1.75%) | 0.80% (1.85%) | 1.18% (2.08%) | 2.89% (3.67%) | 3.89% (4.56%) |
| same but prior1 1/2, cs 1/10, alpha 1/5 | 0.71% | 1.21% | 1.85% | 2.36% | not run |
| grid-like (prior1 1/2, cs 1/10, alpha 1/10) | 0 | 0 | 0 | 0 | not run |

- Gaps grow monotonically with T, by about 0.5 pp per extra step. The registered grid stopped at T=8
  and saw only the first three columns of such a slice.
- The effect is switched on by alpha = 1/5. The registered grid used alpha in {1/20, 1/10} only. With
  prior1 = 1/2 and alpha = 1/10 the gap stayed exactly 0 through T=9. With alpha = 1/5 it grows. This
  is a grid artifact, not a structural zero.
- Over T = 6, 7, 8 the first slice rises by only 0.68 pp. That is under the protocol's 1 pp
  "monotone > 0.01" bar, so even if this slice had been in the grid, A1 would still have returned
  KILL. Extending to T=9 and T=10 gives 3.4 pp. The monotone-in-T criterion on three points is
  underpowered.
- Why the grid is weak. With d=2 and T <= 8 there are at most 3-4 adaptation rounds.
  The secondary d=1 gap was about twice the d=2 gap (0.87% vs 0.36%), which is consistent with the
  number of rounds, `T/d`, limiting the gap. The adversarial set used T=6, B=3, d=2, so it had only 4
  eligible slots and a calendar of 3. It was nearly vacuous.
- Targeted random search: 72 cells at T=7, B in {3,4}, d in {1,2}, asymmetric transitions, prior1
  in {1/20,1/5,1/2}, alpha up to 1/5. The maximum skip-calendar gap was 0.47% and the maximum
  open-loop gap was 2.5%. No cell reached 5%. A 48-cell batch at T=7 with weak emissions
  (1/5, 4/5) gave skip gaps of 0 everywhere.
- Most plausible family for a large gap: high alpha, near-perfect emissions, persistent chain, a
  prior that favours the incumbent, small cs, B=3, d=1, and T well beyond 8. The slice above reached
  3.89% at T=10. T=10 took 238 s, so T >= 12 needs the A3 approximation, which the project declined
  to enter.
- Caveat. alpha = 0.2 is probably not an operating regime anyone would deploy. The gaps (up to about
  4.6% open-loop) are below the 10% bar. The honest conclusion is "not yet decisive; the effect is
  real, grows with T, and the registered grid hid it", not "no separation exists".

Required corrections.
- Downgrade "Lane A closed" to "closed on the registered grid. A growing gap exists off-grid at
  alpha = 1/5 and has not been resolved."
- Add T=9 and T=10 slices, and an alpha = 1/5 column, to any rerun.
- Replace the three-point monotone rule with a fitted slope over at least four T values.

## Q4. Is the P3/P3b supermartingale valid in the implemented timing?

Verdict: UPHELD for the first-promotion claim. The tests actually run in B1/B2 did not probe it.

Evidence.
- Code reading. The bet `lam` is computed before the release of event `t-d` and uses only statistics
  from releases up to `t-d-1`. The cap `q/2` is fixed at issue. The increment `x` is stored at issue
  and applied at `t+d`. The sign `sgn` uses the deployment at release, which equals the deployment at
  issue, because any switch sets `seg = t+1` and drops events issued earlier (`live = s >= seg`).
  Dropping depends only on switch times, which depend on labels released before `t+d`, never on
  `Y_t`. `rem` and the pacer use only free past disagreement counts and past `Q`. I found no
  future-label leakage.
- The B1/B2 validity check was uninformative. W2 and W4 have `E[D] = -0.05` and `-0.10`, so they are
  slack nulls, and 0/500 promotions says little. The only boundary test was the unit test, at small
  scale.
- New boundary-null run (regime 4, `E[D]=0`, 20,000 paths, T=2000, alpha 0.05):

| Policy | B=200 | B=400 |
|---|---|---|
| P3 | 1/20000 | 0/20000 |
| P3b | 610/20000 = 3.05% (CP95 upper 3.26%) | 533/20000 = 2.67% (CP95 upper 2.86%) |

  P3b is valid but uses about 55-60% of the alpha budget, so it is not very conservative. P3 (cap
  `pmin/2`) almost never promotes even at the boundary, which is why B1 looked weak.
- New nonstationary null (20,000 paths per pattern; `E[D_t]` alternating between -0.2 and 0):
  per-step alternation, 50-step blocks, and iid random alternation. P3b false-promotion rates were
  1/20000, 0, 0 for B=200, and 0, 0, 0 for B=400. No violation.
- The marginal null fails, as `05` warns. Take a persistent latent regime with `E[D] = +0.18` w.p. 0.2
  and `-0.20` w.p. 0.8, so the marginal mean is -0.124. P3b promoted in 20.8% of paths (6,000
  paths), all of them in the positive regime. Any certificate claim must be written as
  conditional-null only.
- Multi-cycle caveat. Only the first promotion is covered. The `P3b` W3 rollbacks (up to 0.32 per
  path) are not covered by a pathwise bound.

Required corrections.
- Replace the W2/W4 validity gate with the boundary-null gate (done here, 3.05%).
- Report promotions per path separately from the first-promotion rate.
- Keep the conditional-null wording everywhere.

## Q5. Is P2 equally equipped? Does a stronger simple baseline beat P3b?

Verdict: REFUTED as a fair-baseline claim. The B2 "BEST" set contains a baseline weaker than a
trivial fixed-sample paired test.

Evidence.
- P2 queries uniformly at B/T, including agreements, where the paired difference is a structural
  zero. P2 also never rolls back and switches to f1 whenever the incumbent looks harmed (W2: cost
  516 vs 480 for P0). So BEST is P0 or P2.
- Baselines implemented on the B1 simulator, with the same streams, seed base 20261101, 500 seeds
  and 4 settings. My P3b numbers match B2's exactly (308.5, 314.0, 314.7, 320.8).
- P6 ("periodic validation then switch" / fixed-sample paired test): the P3b pacer, plain (not IPW)
  mean of D over non-overlapping batches of `nv` released disagreement labels. Switch when the batch
  mean exceeds `thr`; roll back on the mirrored signed mean; reset after each batch. No e-process,
  no anytime guarantee. Pre-chosen setting `nv = 25`, `thr = 0.3`, no tuning. I also ran a 3x3 grid
  of `nv` in {15, 25, 40} and `thr` in {0.2, 0.3, 0.4}.
- P2g: a disagreement-gated incumbent alarm, using the P3 pacer, an e-process on `l0` given
  disagreement against 0.35, and a propensity-matched bet cap `q/2`.

World-averaged net cost (equal weight over W1-W4):

| (B, cs) | BEST | P3b | P6 nv25 thr0.3 | P6 best-in-sample (nv15) | P2g |
|---|---|---|---|---|---|
| 200, 5 | P2 343.5 | 308.5 | 311.4 | 307.0 (nv15, thr0.4) | 317.0 |
| 200, 20 | P0 347.5 | 314.0 | 317.0 | 314.1 (nv15, thr0.4) | 321.8 |
| 400, 5 | P2 341.6 | 314.7 | 314.5 | 311.8 (nv15, thr0.4) | 328.4 |
| 400, 20 | P0 347.5 | 320.8 | 322.1 | 321.3 (nv15, thr0.4) | 333.9 |

- Reduction versus BEST: P3b 10.2%, 9.6%, 7.9%, 7.7%. P6 nv25 (untuned) 9.3%, 8.8%, 7.9%, 7.3%.
- Paired bootstrap, P6 nv25 thr0.3 minus P3b: +3.0 [2.4, 3.6], +3.0 [2.3, 3.7], -0.2 [-0.6, 0.2] and
  +1.3 [0.6, 1.9]. So P3b is significantly better in three settings, by about 1%, and ties in the
  fourth. With in-sample tuning (an optimistic bound for the baseline) P6 ties or beats P3b by up to
  2.8 cost units in B=400.
- The 10% bar. No simple baseline would pass either, but P3b passes it by a hair only in one
  setting, and P6 reaches 90% or more of P3b's gain over BEST everywhere.
- P2g loses to P3b by 7.8-13.7, mainly because it cannot roll back (W3: 283-333 vs 246-264).
- Conclusion. The headline gain comes from disagreement-gated paired querying plus switching on a
  paired statistic, not from the e-process machinery, the anytime-valid guarantee or the cap. This
  matches the repo's own claim that no component is new. The validity guarantee is the real
  (unpriced) benefit of P3b over P6.

Required corrections.
- Add a fixed-sample paired batch test and a disagreement-gated incumbent alarm to BEST, and say P2 is
  not an equally equipped baseline.
- Report the cost of the guarantee (P6 vs P3b) as a separate quantity from the gain over BEST.

## Q6. Is the P3b improvement a selection effect from B1 diagnostics?

Verdict: WEAKENED. The B2 protocol discloses the motivation, but fresh seeds do not remove the
selection.

Evidence.
- B1's P3 used cap `pmin/2 = 0.025`. The pacer's typical `q` is 0.4-0.8, so P3's bet was 8-30x
  smaller than the propensity-matched cap. The B1 "MIXED" result was dominated by that arbitrary
  handicap (boundary promotions 1/20000). The B2 change removes the handicap. It is not a new method
  idea. B2 was written after seeing B1's per-world costs, and the generator, worlds and parameters
  are unchanged. Only the seeds are fresh, so B2 is development round 2, as it says.
- Alternate generator, same code path (disagreement rate 0.12, weaker paired signal, pre
  (0.10, 0.15), W1 post (0.25, 0.15), W2 post (0.25, 0.30), reversal (0.10, 0.20), 500 seeds, seed
  base 20261101, delay 5; delay 20 gave the same ordering). BEST was P0 (310.8) throughout. Relative
  reduction versus BEST: P3b +5.4%, +3.7%, +4.9%, +3.0%. P3 -2.6%, -3.5%, -3.2%, -4.2%. P6 nv25:
  +5.0%, +3.0%, +4.6%, +2.5%.
- So the 7.7-10.2% figure is generator-specific. With a weaker signal it falls to 3.0-5.4%, and the
  original cap is worse than never switching.

Required correction. Describe 7.7-10.2% as "development-generator estimate; 3.0-5.4% under a weaker
paired signal", and require a structurally distinct confirmation before any positive statement.

## Q7. Is a 7.7-10.2% gain meaningful, and is it novel?

Verdict: WEAKENED.

Evidence.
- Meaning. The gain is relative to P0 or P2 in a hand-built mixture. One of four equally weighted
  worlds (W1) carries the headroom (P0 480 vs P1 293). The oracle P5 gain over P0 is 55-66 units,
  and P3b captures about 60% of it. The world weights, the costs `cq` and `cs`, and the use of
  0/1 loss with an exactly known disagreement rate are all chosen by the author. This result is a
  stylised simulation of a mechanism, not evidence of economic value.
- Novelty. The ingredients are paired IPW increments with structural zeros, predictable bets,
  Ville's inequality and disagreement-targeted querying. These are close to Xu, Karampatziakis and
  Mineiro (active anytime-valid RCPS: IPW increment, predictable q with floor, NeurIPS 2024) and to
  the CAMS idea of querying informative (disagreement) points (Liu et al., NeurIPS 2024), plus fixed
  delay and a switch rule. The repo's own audit (`02`) marks CAMS as UNVERIFIED (abstract only, no
  audit file). I did not read either paper's proofs, so this is an abstract-level judgement. The
  repo's own statement ("makes no novelty claim") is the right one. Q5 also shows the improvement over
  BEST does not depend on the e-process.

Required correction. Keep "no novelty claim"; do not describe 7.7-10.2% as an economic effect.

## Q8. Future-label leakage or budget accounting errors?

Verdict: UPHELD (none found).

Evidence.
- `ndis` used by the pacer is updated after the step. `ask` uses `u` and `dis[t]`, both free at issue.
  Labels enter wealth and the bet statistics only after `t+d`. Pre-switch events are dropped.
- Budget: `rem` is debited at issue and `q = 0` at `rem = 0`. `max queries = B` in every boundary-null
  run (200 and 400). The summary reports 0 budget violations. Query cost `0.05 * queries` is included in
  all policy costs. P1's switch at t=1 is charged. P2 stops querying after its alarm, which is
  consistent with its definition.
- One caution: `dis = (l0 != l1)` is the "free agreement" signal. This equals prediction disagreement
  only for binary labels. In the simulator it is outcome-defined. It leaks nothing in the binary case,
  but the generator cannot represent multiclass cases where both models are wrong and disagree.

Required correction. Note the binary-label restriction in the B1 protocol text.

## Ranked list of the most serious issues

1. B2's BEST comparator is not equally equipped. A simple fixed-sample paired batch test (untuned)
   reaches 7.3-9.3% versus P3b's 7.7-10.2%, and an in-sample-tuned one ties P3b. The gain does not
   require the e-process (Q5).
2. The A1 KILL is grid-dependent. The registered alpha range hid a monotone growth in T (0.5% at
   T=6 to 3.9% at T=10, open-loop 4.6%), and the three-point T rule is underpowered (Q3).
3. A1's comparator is not the open-loop calendar that A0(iii) describes. It is a slot-restricted
   adaptive class with a coin-aware empty branch. The gap under the stricter class is up to 4.6% in
   the same slice (Q1).
4. B1's "weak" outcome and B2's gain are mostly one arbitrary cap choice. The 7.7-10.2% shrinks to
   3.0-5.4% under a weaker-signal generator, and P3 is worse than never switching there (Q6).
5. The B1/B2 validity gate tested only slack nulls. At the boundary P3b false-promotes at 2.7-3.1%
   (valid), but the marginal null fails at 20.8% (known), and only the first promotion is covered
   (Q4).
6. Economic and novelty claims rest on a stylised, author-weighted four-world generator and on
   closest priors that were read at abstract level only (Q7).
