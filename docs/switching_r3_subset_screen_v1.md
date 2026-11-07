# R3 screen: the five 4-of-5 contract subsets

**Date:** 2026-10-30. **Status:** paper screen under R2/R3; no experiment, no novelty claim. The log's 2026-10-30 re-screen records that these subsets were
never screened. Contract conditions: **S** selective paired labels, **D** release delay, **H** request-time hard budget (pending charged), **V** reversible
deployment value, **A** anytime false-promotion control.

**How to read "covered".** R2 closes a candidate only if a cited source theorem states the result, or directly implies it, under the same feedback, budget,
delay and risk contract. For a 4-subset the "same contract" is the subset itself. I found no single audited theorem that covers any 4-subset; what exists are
*compositions* of audited theorems. Under R2 a composition is not a kill, it is an R6 baseline the candidate must beat or be separated from. Source-verification
levels: "audited" = the repo audit records a primary-source theorem-level read (I relied on those records and did not re-read the papers); "log-only" = cited in a candidate/log entry
without a recorded theorem-level read (Arnold et al., Kapoor-Nair, Huang-Bickford Smith-Rainforth, Emmenegger-Mutny-Krause); "unverified here" = I did not open the audit.

| Subset | Dropped | Closest audited sources | Residual problem | Promise |
|---|---|---|---|---|
| 1 | S | Qiu et al. (delay + movement cost, no risk), DAL (restart, immediate), Shin-Ramdas-Rinaldo e-detectors + the repo's safe-composition derivation, Huang-Veeravalli finite-horizon QCD | delay-`d` safe promotion/rollback with an exogenous label stream | low |
| 2 | D | Li et al. active two-sample, Geng et al. sampling rights, Lau-Tay, Cheng et al., Gong-Zhang (hybrid free budget), Huang-Veeravalli | promotion/monitor budget frontier with immediate labels (C2 with `d=0`) | low |
| 3 | H | Chick-Forster-Pertile, Gong-Zhang paid observations, Reyzin-Saha-Wu UAI 2026, Kapoor-Nair (log-only), Helmeczi CPOMDP | priced-query version of C1 with expected-cost constraints | medium-low |
| 4 | V | Chick et al., Li et al., Prabhu et al., Li-Veeravalli usage-constrained, Geng et al., Digalakis (irreversible adoption), repo noisy lower bound | quantitative `(B,d,alpha)` promotion frontier for HMM alternatives (C1 (b)/(c)) | medium |
| 5 | A | Bayraktar-Ludkovski, Subramanian et al. (delayed POMDP information state, Thm 5), Chick et al., Kapoor-Nair (log-only), Gong-Zhang | scalable certified-gap planner for delayed budgeted sensing with switching | medium-low |

Details follow.

## Subset 1: drop S (labels not selected by the learner)

- **Sources.** With no selection, the label stream is exogenous (a fixed calendar or random arrival). Delay and movement-cost handling: Qiu et al. Algorithm 4 and
  Theorem 5.2 (audited) give delayed dynamic regret, but for unconstrained online convex optimization with no false-promotion event. Detection plus restart: DAL (audited) with immediate
  feedback. The risk side: the repo's safe-composition derivation (e-detector mixture, order-preserving delay, episode alpha spending) and Shin-Ramdas-Rinaldo (audited) cover anytime false-promotion
  control with delayed released labels. Reversible HMM switching with filtering: Bayraktar-Ludkovski (audited; no delay, no risk event). Finite-horizon false-alarm control with `O(log T)` latency: Huang-Veeravalli (audited).
- **R2 verdict.** No single source theorem states "delayed exogenous labels + anytime promotion control + reversible deployment value". The combination is the R6 baseline (e-detector + alpha spending + delayed
  CUSUM). Not killed by R2, but also not distinguished from it.
- **Structural remark.** H is meaningless without S: a hard *request-time* budget needs requests. So this "4-subset" degenerates to a 3-condition problem (D, V, A), which is the weakest in the table.
- **Residual problem.** Optimal stopping for promotion and rollback under delay with a risk constraint. By the lower bounds in `switching_theory_targets_c1_c2_v1.md`, `d` enters additively (`t >= d + kl/kappa`), so the delay-specific theory is thin.
- **Promise: low.** The interaction that made the contract new (acquisition coupled to risk and delay) is removed.

## Subset 2: drop D (labels released immediately)

- **Sources.** Active selective labels with a finite label budget and anytime Type-I control: Li et al. active sequential two-sample testing (audited; terminal test, IID pool, immediate). Sampling rights
  and quickest detection: Geng-Bayraktar-Lai (audited; one change, geometric prior). Observation-switching QCD with an observation-dependent two-stage design: Lau-Tay (audited; asymptotic, ARL false alarms).
  Hard observation cap with switching costs: Cheng et al. (audited; regret vs fixed action). Paid observations with a finite free-observation budget: Gong-Zhang (audited; Theorems 3.1-3.2 give a budget phase transition). Controlled sensing with false-detection and sensing-switch costs: Prabhu et al. (audited).
- **R2 verdict.** Not killed by one theorem; Li + Geng/Lau-Tay + Cheng form the composition baseline. This is the most heavily occupied subset: every non-delay ingredient has an audited primary source.
- **What changes without delay.** The distribution-free impossibility (identical pre-action histories, `d>=1`) weakens: after one released label the learner can act on information about the current regime, so first-opportunity power is the only casualty. The frontier lower bounds lose only the `d` offset.
- **Residual problem.** Promotion/monitor budget frontier with immediate labels (C2 at `d=0`). Its candidate theorem, the combined `klP/kP + (1-gP) klR/kR <= B`, is a standard KL combination; the open part is the unknown-onset monitoring floor (Conjecture C2-C), which is the Geng/Lau-Tay territory.
- **Promise: low.** Dropping D removes the one condition that makes sparse-label information structurally different, and lands in the densest part of the audited literature.

## Subset 3: drop H (priced queries, no hard cap)

- **Sources.** Delayed economic sampling with per-sample cost, a maximum sample size and one-time adoption cost: Chick-Forster-Pertile (audited; stationary Gaussian, one adoption, Bayesian). Paid observations with regret
  including observation expenditure: Gong-Zhang, Reyzin-Saha-Wu UAI 2026 (audited summaries). Costed sensing as a belief-state MDP with suboptimality bounds: Kapoor-Nair (log-only). Decision-focused acquisition:
  Huang-Bickford Smith-Rainforth (log-only). Expected-resource constrained POMDPs: Helmeczi et al. (audited, expected budgets), which is exactly the Lagrangian relaxation of a hard cap.
- **R2 verdict.** Not killed by a single theorem, but the *priced* version is the Lagrangian dual of the hard-cap problem and sits inside constrained-POMDP and costed-sensing theory. Any
  Lagrangian result transfers to a hard cap only with a duality-gap statement; the repo's hidden-root one-sided-POSG reduction handles the risk side.
- **Residual problem.** Replace the pathwise cap by an expected-cost price `lambda`: lower bound `kl(1-gamma||alpha) <= kappa * E[N]` (the chain-rule inequality in expectation form), upper bound by the same
  e-process gate. The delay then enters through `E[N_released]`, not through a `min(B,.)`. C1 (a) is unchanged; (b)/(c) become cleaner (no cap geometry) but also less contract-specific.
- **Promise: medium-low.** A useful *relaxation* to get closed forms, but the hard cap is where the repo's distinct lower bounds live (`min(B, t-d)`); the priced version is more covered.

## Subset 4: drop V (irreversible deployment: first promotion only)

- **Sources.** This is the contract of the first-promotion solver and the noisy lower bound. Delay + hard sample cap + one-time adoption, no risk event: Chick et al. (audited). Selective labels + finite budget + anytime
  Type-I + power: Li et al. (audited; IID pool, immediate). Controlled sensing with false-detection constraint and a converse: Prabhu et al. (audited; stationary, immediate, no total cap). Usage-constrained sequential tests: Li-Veeravalli (audited; expected usage). Sampling rights: Geng et al. Irreversible adoption with look-ahead: Digalakis et al. (audited; delayed labels and cap outside the theorem).
  Repo-internal: noisy lower bound, uniform-calendar bounds, safe-composition and first-promotion XP solver.
- **R2 verdict.** The XP solver is closed as a standalone method (reduction to robust POMDP/POSG, per `switching_first_promotion_xp_complexity_v1.md`; that closure was a model-class reduction and is invalid as a *sole* kill under the revised R2, but the doc's own conclusion that no strict
  separation was shown stands). A *frontier theorem* for the contract is not stated by any audited source: Prabhu gives asymptotic stationary IID converses; Li et al. give a terminal power analysis with immediate labels; Chick et al. have no safety event.
- **Residual problem.** The matching upper/lower bound for promotion delay under a hard cap, delay and anytime false-promotion control, now with an HMM alternative to make "current value" meaningful: Targets (a)-(c) of C1 in `switching_theory_targets_c1_c2_v1.md`. Note that with a fixed IID pair of laws the frontier is exactly
  Neyman-Pearson plus Wald (checked numerically: lower bound 94.7 labels versus 158 exact NP and about 220 for the anytime e-process in one cell), so the contract adds substance only through the HMM dependence, delay and cap together.
- **Promise: medium.** Best of the five. V is the condition whose removal costs the least in lower-bound structure (the lower bound is a first-promotion statement), while the safe-model gate (C1) still delivers a "current value" notion through the persistent-regime model.
- **Caveat.** Dropping V forfeits the reason the project cared about reversals; the dropped condition must be reported as a limitation (R3).

## Subset 5: drop A (no false-promotion guarantee)

- **Sources.** Bayesian optimal switching with an HMM filter and switching costs: Bayraktar-Ludkovski (audited). Delayed POMDP information state with exact Bellman recursion: Subramanian et al. Theorem 5 and Section 2.4 (audited). Delayed economic sampling: Chick et al.
  Costed sensing with policy-improvement suboptimality bounds: Kapoor-Nair (log-only). Paid observation regret: Gong-Zhang.
- **R2 verdict.** The model class is a delayed, budgeted POMDP; the exact planner is the R1 oracle (value upper bound, not beatable). Per R2, the POMDP reduction alone is not a kill; a kill requires a source theorem. Kapoor-Nair's suboptimality bound and policy improvement (log-only) is the closest and could be a kill for any generic scalable-planner claim; its theorem-level scope must be read.
- **Residual problem.** R1(a)-(c): a polynomial-in-`T` or anytime planner with a certified gap to the oracle and a registered improvement over the strongest scalable composition. The repo's symmetric-HMM monotonicity screen found zero gap in nine terminal-testing cells (fixed query horizon), which is a finite check and not a theorem.
  A structural (threshold/monotone) theorem for the delayed, capped, switching DP would be a genuine candidate; none is proved.
- **Promise: medium-low.** Mathematically the cleanest (pure control), but it discards the anytime-validity ingredient that separates the project from Bayesian experimental design, and it is the corner closest to the audited control literature.

## Ranking and recommendation

1. Drop V (C1 (b)/(c)): medium. Pursue as the theory track.
2. Drop A (certified-gap planner) and drop H (priced relaxation): medium-low. Keep as secondary: drop-H as an analysis device, drop-A only if a structural theorem appears.
3. Drop D and drop S: low. Do not pursue as contributions; their composition is an R6 baseline.

All ratings are paper-screen judgments and depend on the audits' summaries. The items most likely to change a rating (any could invalidate a "medium"): theorem-level reads of Arnold et al., Kapoor-Nair, and Huang-Bickford Smith-Rainforth; Brice et al./Bovy et al. complexity results; and whether Lau-Tay or Geng et al. contain a finite-sample hard-cap delay statement.

## Continue / pivot / stop

**CONTINUE** on subset 4 (with the HMM-conditional safety gate) as the screened R3 survivor; **PIVOT** away from subsets 1, 2 and 5 unless a structural theorem or a delay-specific separation appears; treat subset 3 as an analysis relaxation, not a candidate.
