# G1 audit: deadline-aligned acquisition is standard control

**Date:** 2026-10-30. **Status:** candidate killed before implementation; no algorithm, theorem,
or experiment is claimed.

## Candidate screened

The proposed rule was to spend scarce label requests preferentially when the remaining horizon,
known release delay, and switch/reversal costs make the evidence actionable before a deployment
decision expires (“deadline-aligned acquisition”). Its motivating intuition is sound: a label that
arrives after the last useful switch has less decision value, and a fixed-rate acquisition schedule
can spend budget on stale evidence.

## Information and decision state

Under a finite controlled-HMM with known release law, the observable decision state can be augmented
with the posterior over latent state and model parameter, the current deployment, remaining request
budget, and the queue of already-requested labels with their release times. For expected net value,
a finite-horizon Bellman recursion on this state chooses jointly whether to query and whether to
switch. The value of a query is its expected continuation value after the label is released, less
query cost; release delay and remaining decision horizon already enter that continuation value.
Thus deadline alignment is a heuristic approximation to ordinary belief-state control, not a new
acquisition principle. With a global any-promotion risk constraint, the exact comparator is instead
the constrained extensive-form/sequence-form game, as formalized in
`switching_two_law_game_duality_v1.md`; the constraint cannot generally be replaced by a local
Bellman threshold without proof. In either formulation, a heuristic cannot beat the exact finite
oracle on its own objective. With unknown models, a claimed gain needs a specified
approximation/learning regime and a bound against that planner or an information-theoretic lower
bound.

This state construction must reserve pending labels at request time and charge every switch under
the declared cost. It does not by itself imply anytime safety; the confidence-set gate and
current-value risk event remain separate. In particular, old evidence cannot be used as a
certificate of benefit after a regime reversal.

## Source-level novelty boundary

- Monahan, *Optimal Stopping in a Partially Observable Markov Process with Costly Information*,
  already formulates sequential sampling and stopping in a partially observed Markov process and
  gives optimal-value structure: [INFORMS primary article](https://doi.org/10.1287/opre.28.6.1319).
- Chick et al., *Bayesian Decision Theoretic Model of Sequential Experimentation with Delayed
  Response*, explicitly combine costly sampling, delayed outcomes, and an online deployment decision
  through Bellman equations: [JRSS B primary article](https://doi.org/10.1111/rssb.12201).
- Cheng, Zhou, and Ji characterize minimax regret for online learning with switching costs and a
  finite observation budget: [ICML primary paper](https://proceedings.mlr.press/v202/cheng23f.html).
  The paper's stated model is not the full delayed recurrent-HMM task, but rules out claiming that
  “budget plus switching cost” is itself new.
- Drift2Act explicitly combines active risk certification, delayed labels, budgeted interventions,
  and intervention costs: [primary arXiv record](https://arxiv.org/abs/2603.08578). Its work is a
  workshop paper and its exact contract differs, but the component-level overlap is direct.
- The repository's `switching_controlled_hmm_cs_baseline_v1.md` already specifies the augmented
  belief/queue/budget/incumbent planner as the required comparator, and
  `switching_query_conditioned_deployment_extension_screen_v1.md` shows that query-action coupling
  reduces to joint randomized control against the finite extensive-form oracle.

## Verdict and next gate

Kill deadline-aligned acquisition as a standalone method hypothesis. Do not implement a timing
heuristic or run an efficacy grid for it. Reopen only with a structural condition under which an
efficient implementable rule has a proved advantage over (i) the exact finite planner on small
instances, (ii) the risk-gated controlled-HMM planner, and (iii) relevant budgeted delayed-feedback
methods. A promising next *question*, not a selected algorithm, is whether global anytime false-
promotion control and post-reversal current-value safety impose a nontrivial minimax budget/regret
tradeoff under arbitrary recurrent regimes; first derive an information-theoretic lower bound and
compare it with change-point tracking and delayed risk-certification results. If the lower bound is
already implied by those sources or only restates the exact oracle, close this broader direction.

No efficacy or locked-holdout gate opens. The 2025 Binance data remain development-only, and any
account-utility replay requires its own frozen estimand. Safety certificates for historical
promotion and current-regime value after reversal are distinct quantities.
