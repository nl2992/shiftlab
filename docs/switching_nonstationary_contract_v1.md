# Nonstationary delayed switching: information and safety contract

> **Risk design update:** The product statistic below is a valid sufficient mechanism, not the
> only admissible certificate. [The risk-frontier audit](switching_risk_frontier_audit_v1.md)
> demonstrates an equally error-controlled alternative and requires the next algorithm to
> compare under the actual risk constraint, including permitted randomization.

2026-10-28. Previous turn: progress (standard rollout was screened and excluded as novelty).
The stationary plan library is closed. This work defines the next nonstationary reference
state; it is not a new acquisition algorithm or an efficacy comparison.

## Working model and learner boundary

Let S_t in {0,1} be an unobserved Markov state. The learner knows a working model with
P(S_t=1|S_(t-1)=0)=a, P(S_t=0|S_(t-1)=1)=b and P(S_0=1)=p0. The state may repeatedly
reverse. Conditional on the hidden path, Y_t is independent Bernoulli(theta_(S_t)), with
0<theta0<1/2<theta1<1. Fixed policy losses are Y_t and 1-Y_t. Actions do not affect outcomes.
Parameters are model assumptions shared with applicable comparators, not evaluator oracle data.
The realized S_t and unqueried/future Y_t never enter the learner API.

At the start of round t, process feedback from requested events s with s+d=t, then choose the
action/query. Each query consumes one of B rights immediately, even if its label arrives after
T. Delay is a known fixed positive integer. Pending requests are kept by event time. No labels
may be scored early, omitted on their due round, supplied twice, or supplied when unrequested.

This research clock differs from `streaming_decision_contract.md`, whose same-clock requests
precede feedback. **No direct replay interoperability is claimed.** Before connecting the two,
an explicit clock adapter must map research start-of-round feedback to a time strictly before
the relevant action and pass boundary tests. Do not silently change the platform's ordering.

## Sufficient working-model state

For this model, retain the posterior p_r=P(S_r=1|arrived queried labels) at the latest observed
event r, its event time r, and the times of pending requests. Pending observations carry no
outcome information yet. At a later event s before assimilating its outcome, propagate

    p_s = a/(a+b) + (p_r-a/(a+b))*(1-a-b)^(s-r),

when a+b>0; p_s=p_r if a=b=0. Its predictive positive-label probability is
theta0+(theta1-theta0)*p_s. After observing Y_s, update p_s by Bayes' rule and retain that
posterior at s. A current-time forecast must propagate this posterior onward to current t;
using it as if the delayed label described S_t is incorrect. Pending *ages* determine future
information arrival, so count alone is not the full planning state.

This is standard hidden-Markov filtering with skipped observations. Adding it to a controller
is not by itself a methodological contribution. Working-model forecast quality can fail under
misspecification; it must not be confused with the testing guarantee below.

## Statistical risk retained, and what it does not control

Use the stronger explicit event-history null

    E[Y_s | F_(s-1), query coin at s] <= 1/2 for all s,

where F contains every earlier outcome (even if not yet learner-visible), past request/action
choices and independent private randomness available for the choice. Queries must be chosen
before Y_s. This is stronger than a null stated only relative to the observed delayed history;
the guarantee must not be extended to that weaker assumption without a proof.

At queried event s, choose p_bet=max(1/2, working-model predictive probability at s from older
queried outcomes). The one-step test factor after its label arrives is

    f_s = 2*p_bet if Y_s=1;  f_s=2*(1-p_bet) if Y_s=0.

Use factor 1 on unqueried events. Because p_bet>=1/2 and is event-history predictable,
E[f_s|past,query]<=1 under the null: the expectation is
1+(2*p_bet-1)*(2*E[Y_s|past,query]-1). Products form a nonnegative supermartingale in
event order. With fixed d, the visible evidence at round t is the product through t-d, so
Ville's bound also controls visible threshold crossings. If every 0->1 promotion requires
this evidence >=1/alpha, P(any promotion by T)<=alpha under this global null. Stopping queries
at the hard budget does not invalidate it. No inverse-propensity estimator is needed for this
conditional-null test; this does not identify a population risk from selected labels.

This guarantee tolerates a misspecified working HMM since it uses only the predictable bet
bound. It does **not** certify current benefit, a positive post-switch horizon or timely rollback
in a stream containing favorable and unfavorable regimes. The null is false on such a stream.
A forecast and an evidence value may legitimately point in opposite directions after reversal.
Using the global e-value as current economic permission would overstate the guarantee.

Predictable betting/test-martingale construction is established prior work; see
[Waudby-Smith and Ramdas, bounded means by betting, Section 4.2](https://academic.oup.com/jrsssb/article/86/1/1/7043257).
The method description was inspected. No novelty is claimed from the HMM-derived score,
product test or their composition. Repeated-switch economic regret and useful safe acquisition
are still the intended research obligations.

## Registered correctness checks, before implementation

Implement `src/shiftlab/dive/delayed_regime_information.py` with rational probabilities and
explicit request/release handling. Before using it in any controller:

1. Compare filtered current-state probabilities against brute-force hidden-path enumeration,
   for both symmetric and asymmetric transitions, skipped queries and multiple label patterns.
2. Check fixed-delay clocks, query-cap accounting, pending labels, duplicates and input validity.
3. Enumerate short binary outcome paths under an IID boundary null and a history-dependent null
   with conditional means <=1/2; verify visible expected wealth never exceeds 1 and crossing
   probability is bounded by alpha for an adaptive predictable query rule.
4. Exhibit a deterministic favorable-then-unfavorable sequence on which wealth remains above
   threshold while the current working-model forecast favors policy 0. This is a scope diagnostic,
   not a violation of the global-null theorem or a statistical efficacy experiment.

No full-factorial efficacy run, final seeds, real-data scoring or new-method nomination is
registered. The reference exposes only information and a test statistic, not an action controller.

## Verification and decision

Implementation and registered checks completed. The combined targeted suite reported **50 passed
in 3.14 seconds**; Ruff check/format and Git whitespace checks passed. The filtering checks
compare exact fractions to brute-force enumeration of the hidden state path, including asymmetric
transitions and skipped requests. Model inputs are normalized to exact fractions; invalid models,
feedback and request timing are rejected. The exhaustive short-null check covers two specified
null generators at T=8 and alpha=1/2; it is not empirical validation of all conditional-null laws.
The supermartingale argument supplies the stated general guarantee under its assumptions.

Reproduce the checks with:

    python -m pytest -q tests/test_delayed_regime_information.py tests/test_delayed_switching_reference.py tests/test_delayed_feedback.py

The favorable-then-unfavorable diagnostic is also recorded with implementation/test source hashes
at `outputs/switching_nonstationary_contract_v1/reversal_scope_diagnostic.json`. It deliberately
violates the global no-benefit null in its favorable segment. Historical wealth staying above a
threshold after reversal is therefore not a false-alarm-calibration failure. It demonstrates why
the global-null statement cannot be advertised as a current-benefit or rollback certificate.

**Decision:** this supplies a verified nonstationary information state and separates working-model
forecasts from valid global-null evidence. No novel mechanism is nominated. The next acquisition
derivation can use pending-event ages and Markov forecasts without receiving hidden states, but
must justify a new allocation advantage and its robustness/performance guarantee. A known-HMM
filter, likelihood product and ordinary constrained POMDP planner would remain established
ingredients. Dynamic regret, reversal efficacy and eligible real-data evidence remain unproved.
