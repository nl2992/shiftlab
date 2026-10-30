# G1 pivot screen: action-dependent outcomes

**Date:** 2026-10-29. **Status:** scoped novelty screen, not an algorithm, theorem, or
confirmation result. This screen follows the Phase C/D/E exits recorded in
`docs/lane_b_burst_allocation/C_PIVOT_MEMO.md` and the active gates in
`docs/budgeted_switching_research_goals.md`.

## Decision

Do not treat “the deployed model changes the outcome distribution” as a contribution. This is
already the core performative-prediction setting. A narrower candidate may proceed to a problem
contract only if it identifies (i) a counterfactual decision utility that remains meaningful when
deployment changes the outcome law, (ii) which outcomes are observed under each deployed policy,
and (iii) a finite-budget, delayed-feedback interaction that is not obtained by composing existing
performative/bandit learning, change detection, and switching-cost control.

No such interaction has been established yet. G1 remains open; G2–G5 stay held. This screen does
not authorize an implementation, efficacy sweep, or real-data claim.

## Primary-source boundary

- Perdomo et al., [Performative Prediction (ICML 2020)](https://proceedings.mlr.press/v119/perdomo20a.html),
  study prediction deployment changing the target distribution and give stability/convergence
  results for performative risk minimization.
- Jagadeesan et al., [Regret Minimization with Performative Feedback (ICML 2022)](https://proceedings.mlr.press/v162/jagadeesan22a.html),
  use samples from the distribution induced by the deployed model and derive regret bounds using
  exploration over distribution shifts.
- Chen et al., [Performative Prediction with Bandit Feedback (ICML 2024)](https://proceedings.mlr.press/v235/chen24al.html),
  study bandit feedback in performative prediction and provide sublinear-regret guarantees under
  their reparameterization assumptions.
- Vernade et al., [Non-Stationary Delayed Bandits with Intermediate Observations (ICML 2020)](https://proceedings.mlr.press/v119/vernade20b.html),
  combine nonstationarity, delayed rewards, and immediate intermediate signals, with regret
  guarantees when the final reward is conditionally stationary given the signal.
- Luo et al., [Efficient Contextual Bandits in Non-stationary Worlds (COLT 2018)](https://proceedings.mlr.press/v75/luo18a.html),
  provide interval, switching, and dynamic regret guarantees for policy learning across
  nonstationary environments.

These works do not, from the source-level summaries checked here, establish ShiftLab's exact
combination of a pathwise query cap, delayed action-dependent outcome feedback, global causal-null
any-promotion control, and reversible deployment with economic switching costs. That mismatch is
only an audit obligation; it is not a novelty claim. A candidate must compare against a resource-
matched combination of these methods and the existing two-law sequence-form oracle.

## Required next gate (F1)

Before proposing an algorithm, write a one-page task contract with:

1. A causal timeline: policy assignment/deployment, any induced environment response, utility
   realization, query request, and feedback release.
2. A target estimand (including the reference policy) and assumptions under which it is
   identifiable from the feedback that each action reveals.
3. A precise null event for unsafe promotion, its filtration, and the hard budget accounting rule.
4. A minimal two-policy instance on which a resource-matched performative/bandit plus
   change-detection/controller composition is provably suboptimal.
5. An eligible dataset or simulator with policy-dependent outcomes, point-in-time feedback
   availability, and defensible switching costs.

**Kill F1** if counterfactual utility is not identifiable, if the minimal instance collapses to a
standard performative bandit or delayed nonstationary bandit, or if the only real-data evidence
would be an unvalidated market-impact simulation. If F1 passes, freeze the comparator and instance
before deriving a method. The method must then pass G1 (a strict theorem-level advantage against the
strong composition) before any broad empirical study.

Historical promotion evidence and a forecast of current-regime utility remain distinct. Evidence
from a previously beneficial regime does not by itself certify benefit after reversal.

## Status correction from repository cross-check

The generic action-dependent-outcome route is not the next untested structure in this repository.
`docs/data_phase1.md` already documents an interactive performative environment, while
`docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` and
`docs/research_refinement_v1/COMPETING_RESEARCH_DIRECTIONS.md` record the G1/G3 audits for
selective and performative feedback. Those records identify a possible causal, randomized
regime-comparison estimand, but no fixed estimand, source-backed strict separation, or eligible
real-data task. Reopening that route would repeat an existing screen. Treat F1 above as a future
reopening checklist only; the active next step remains the G1 joint utility-risk compression
question, now developed in `switching_joint_risk_abstraction_derivation_v1.md`.
