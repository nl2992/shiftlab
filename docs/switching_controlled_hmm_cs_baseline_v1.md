# Controlled-HMM confidence-set gate: safety comparator

**Date:** 2026-10-29. **Status:** baseline theorem and contract clarification; not a novel method,
acquisition rule, regret theorem, or empirical result.

## Controlled hidden-state contract

Let the unknown but fixed parameter be `theta*` in a finite set `Theta`, with prior weights
`pi(theta)>0` for every `theta`. At event `t`, the learner chooses deployment action `A_t` and
query indicator `Q_t` from the observable history `F_{t-1}`. Conditional on current latent regime
`Z_t`, observed pre-action context `X_t`, and action `A_t`, the model specifies

```text
P_theta(Z_{t+1} | Z_t, X_t, A_t)
P_theta(Y_t | Z_t, X_t, A_t)
P_theta(D_t | Z_t, X_t, A_t, Q_t),
```

where `D_t` is the label release delay. Assume bounded utility, known deployment fees, a finite
horizon, correct model specification, and absolute continuity of observed transcript laws. The
learner sees `Y_t` only if it queried that event and the label has actually been released. Pending
and unqueried outcomes and latent states are marginalized in the likelihood. Query requests reserve
against the hard pathwise budget at request time. The action/query randomization kernels are known
and do not depend directly on `theta` except through the observable history. Any informative delay
or missingness must be included in the joint model above; treating it as ignorable without that
assumption is invalid.

For each current observable history and deployment state, define `Delta_t(theta)` as the
model-conditional remaining-horizon expected net value of following the challenger strategy versus
the reference strategy from now on. This is a policy-level counterfactual: it propagates the
latent-state belief under each strategy's action-dependent transition kernel and includes all
future switching fees. It is not an instantaneous reward contrast and not a realized latent-state
sign. Fix the economic hurdle `h` before analysis.

## Likelihood confidence set

Let `L_t(theta)` be the likelihood of the learner-observable transcript through event `t`, including
the realized actions, query decisions, release indicators/times and only released queried outcomes.
Correctly condition on the predictable action/query kernels and integrate over hidden states,
unqueried outcomes, and outcomes still pending. Define

```text
E_t(theta) = sum_{theta' in Theta} pi(theta') L_t(theta') / L_t(theta)
C_t        = {theta in Theta : E_t(theta) < 1/alpha}.
```

Under the true fixed model `theta*`, each likelihood ratio `L_t(theta')/L_t(theta*)` is a
nonnegative likelihood-ratio martingale on the observable filtration (or a supermartingale when
the transcript is coarsened). Thus `E_t(theta*)` is a nonnegative mean-one martingale and Ville's
inequality yields

```text
P_theta*(exists t : theta* not in C_t) <= alpha.
```

Use the gate `promote at t only if inf_{theta in C_t} Delta_t(theta) > h`; if `C_t` is empty,
abstain. On simultaneous coverage, every promotion has true-model `Delta_t(theta*) > h`, so

```text
P_theta*(exists promotion t with Delta_t(theta*) <= h) <= alpha.
```

This is model-conditional current policy-value safety under the fixed controlled-HMM. It does not
control misspecification, arbitrary parameter drift, realized statewise harm, or regret. After a
reversal, the forecast changes only when new released observations or other declared observables
change the filter; old evidence alone is not a current-value forecast. Keep the current `Delta_t`
estimate and confidence-set provenance separate from any historical promotion e-process.

The hard query cap is guaranteed only if the acquisition component reserves each request and counts
pending labels. This gate says nothing about how to acquire efficiently. A possible baseline is
finite-horizon constrained planning on `(posterior over (Z,theta), pending-delay queue, remaining
budget, incumbent, promotion state)`, with the above gate imposed on deployment actions. That is
standard belief-state/control machinery and is a required comparator, not a contribution.

## Source boundary and candidate test

This is the direct controlled-action extension of the repository's delayed-HMM predictive CS
screen, using a standard likelihood-ratio confidence sequence plus model-based policy evaluation.
Related established sources include Bayraktar–Ludkovski on hidden-Markov optimal switching,
Hardwick–Stout on response-adaptive designs with switching costs, and adaptive-experiment inference
for sequential treatment assignment. See `switching_hmm_predictive_cs_candidate_v1.md`,
`switching_hidden_markov_optimal_switching_prior_audit_v1.md`,
`switching_response_adaptive_switching_prior_audit_v1.md`, and
`switching_g1_intersection_task_contract_screen_v1.md` for source-scope records.

**Novelty verdict:** the confidence-set gate is a safe comparator. It is a standard confidence-set
containment argument, and a planner over the augmented belief/queue/budget state is standard
constrained control. No superiority over that planner has been shown. Any acquisition candidate
must beat it and the exact small-instance oracle in decision regret or a proved complexity/value
tradeoff, under identical controlled kernels, delayed feedback, label cap, randomization, and fees.
Do not run an efficacy grid for this baseline alone.
