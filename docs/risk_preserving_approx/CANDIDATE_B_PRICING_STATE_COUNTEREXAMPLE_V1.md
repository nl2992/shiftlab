# Candidate B pricing state: exact public-history counterexample

**Date:** 2026-10-29. **Decision:** a pricing DP cannot merge public learner
histories using only time, remaining budget, deployment, and a belief over the
hidden root mode/regime/pending labels when the null response may be an arbitrary
full-history strategy. This falsifies that proposed compact state, not all policy
generation or all structured null-response classes.

## Claim tested

For fixed dual weights and fixed active causal-null responses, Candidate B proposes
to solve a hidden-root partially observed control problem. The candidate compression
would retain a belief over the root mode and physical latent state (including
pending labels) while dropping the complete public learner transcript. The required
claim is that this belief and the usual time/budget/deployment variables determine
all future pricing rewards and transition laws.

## Two-history construction

Use delay one, a stationary uninformative alternative (`emission0 = emission1`),
and a single null mode whose response was `p=1/2` on both prior query histories.
Compare two event-3 learner histories, with deployment fixed at incumbent:

- `h_A`: query at event 1, skip event 2, and observe a positive label from event 1
  released at event 2;
- `h_B`: skip event 1, query at event 2, and observe a positive label from event 2
  released at event 3.

At the event-3 decision, both histories have one query used, the same remaining
budget, no pending labels, the same current deployment and time, and the same
belief over the hidden root/null mode. The alternative is chosen uninformative so
the event-time of the single positive label does not change its hidden-state
posterior. The null mode's physical state is also empty after release. But the
public transcripts differ in the event at which the query and positive result
occurred.

An allowed fixed history-adaptive null response can choose `p=0` for a query at
event 3 after `h_A` and `p=1/2` after `h_B`. If the learner queries at event 3 and
promotes at event 4 exactly when that label is positive, the continuation
promotion risks are respectively 0 and 1/2. Therefore the proposed belief state
does not determine the transition kernel or continuation value. The distinction
is available to the causal null because it observes the full history; the learner
still observes only its own released transcript.

## Consequence and boundary

An exact pricing state must retain either the public history or a sufficient
automaton state for every active null response's future continuation. The general
causal-null family permits arbitrary history-conditioned responses, so no compact
state-size bound follows from the physical belief dimension alone; the required
response-memory representation can grow with the full pre-promotion history. This
does not rule out compression when active null responses are proven to have a
bounded automaton or a sufficient statistic with a uniform bound. No such bound is
currently available for the sequence-form dual responses.

The candidate-column LP reformulation remains exact, and standard constrained-POMDP
column generation remains a relevant baseline. Its missing pricing-complexity lemma
is now concrete: derive a response-continuation quotient whose state count is
provably smaller than the learner realization form, or stop this direction. Do not
implement a belief-only pricing DP; it would evaluate a different, restricted null
family. No efficacy, real-data or novelty claim is made by this counterexample.
