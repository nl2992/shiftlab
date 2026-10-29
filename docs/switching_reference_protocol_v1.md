# Delayed budgeted switching reference: correctness protocol

2026-10-28. Registered before implementation or execution. This is an established-ingredient
reference construction, **not a proposed novel method**, a faithful reproduction of Cheng et al.,
or evidence that G1 has passed. It uses uniform block queries, delayed Hedge weights and common
randomness to control switches for two actions. Its purpose is to make one nontrivial comparator
concrete and verify its information boundary. The G1 risk-constrained/dynamic target remains open.

## Contract and fixed checks

Horizon T=mL, m<=B<=T. Fixed known delay d>=1, two fixed policies, action-independent outcomes,
losses in [0,1], and no unqueried losses revealed. On each block's first round, incorporate labels
available at that round, update the deployment probability and sample one uniform query index
inside the block. Hold the action throughout the block. Charge each query at its event even if
its label arrives after T. Initial deployed action is 0. One independent uniform deployment coin
is reused across blocks; label-query randomness must never depend on that coin or the actions.

Before any efficacy experiment, implement and check:

1. Every trace requests exactly m labels, with no more than B outstanding plus resolved requests.
2. Changing unreleased outcomes cannot change past decisions. Reject early, duplicate, unqueried,
   nonfinite or out-of-range feedback and skipped/repeated round calls.
3. Labels arriving inside a block affect the next block only; labels available at its first round
   may affect that block. No label available after T enters a decision before T.
4. Changing only the deployment coin preserves every query time and probability path.
5. By exact finite enumeration for short streams, expected decision cost and switching cost
   satisfy the bound below. Numerical checks support implementation fidelity, not the proof.

Use CPU unit tests and exact enumeration only. No efficacy hypothesis, tuned parameters, fresh
confirmation seeds, real data, or method-comparison claims are registered here.

## Bound and proof (supporting result; no originality claim)

Let eta>0 and p_b=sigmoid(eta sum Z_s), where the sum includes queried scores that arrived
by the start of block b. Draw U independently of all query choices and outcomes, and deploy
1{U<p_b}. Let r=ceil(d/L), a conservative bound on the number of earlier blocks with a sample
still missing. If losses are an oblivious deterministic path (or action-independent randomness
independent of query/deployment coins), then

    E[J] - min_a sum_t l_t(a)
      <= L log(2)/eta + eta*T/8 + eta*T*r/4
         + k*(1/2 + eta*m/4) + c*m.

The fixed comparator in this display pays no initial switch cost. The G1 best fixed comparator
with an initial switch charge has no smaller cost, so the same upper bound also holds there.
This is not a bound against the S-switch dynamic oracle or a false-promotion guarantee.

Proof: write x_b for the paired loss at the uniform queried event and a_b for the true block
average. Let p*_b be ordinary Hedge using all previous x_i, including those not yet delivered.
Hedge's bounded-loss bound is log(2)/eta+eta*m/8. The sigmoid derivative is at most 1/4;
at most r earlier sample scores are missing, each of absolute value <=1. Thus
abs(p_b-p*_b)<=eta*r/4 and excess sampled loss contributes at most eta*m*r/4.
The current query location is independent of p_b, so expected mixture loss on x_b equals
mixture loss on a_b. A fixed comparator has the same unbiasedness property. Multiply by L.

Conditional on the entire query/outcome path, p_b is independent of U. Therefore the expected
number of action switches is p_1+sum_b abs(p_(b+1)-p_b). Since p_1=1/2, and each newly delivered
sample can change the sigmoid by at most eta/4, the total is <=1/2+eta*m/4. Every sample is
incorporated at most once. Add k times this bound and the deterministic c*m query charge. QED.

For m fixed, choosing eta to minimize A/eta+D*eta with
A=L log(2), D=T/8+T*r/4+k*m/4 yields
O(T/sqrt(m)+sqrt(d*T)+sqrt(k*T)+k+c*m), up to constants. This illustrates how much broad
fixed-comparator performance follows from standard primitives. No new-rate claim is warranted.
The displayed bound can exceed T and is not a promise of useful performance in every regime.

## Important exclusion

The proof's common randomness argument fails if acquisition or future losses depend on the
deployment coin through past actions: conditioning on the query/outcome path can then disclose
U. Any new action-dependent acquisition rule needs a new coupling argument or a different
switching analysis. This is a specific obstacle to jointly optimizing acquisition and deployment,
not an established novelty gap. A future candidate must also address dynamic regret and safety.

This does **not** forbid evidence-adaptive acquisition. In an action-independent environment,
let the query policy use only arrived evidence, pending-request metadata, its own independent
coins and deployment probabilities p_t. If it never reads realized actions or the deployment
uniform U, induction gives an observation/probability path independent of U. Conditional on
that path, 1{U<p_t} still has marginal p_t and switch probability abs(p_t-p_(t-1)), including
initial p_1 from deployed action 0. Thus a candidate can optimize expected deployment loss
plus k times the probability path's total variation without conditioning queries on sampled
actions. This is a supporting coupling identity, not an optimality theorem over all joint policies.
Our fixed-block regret proof above does not automatically extend to adaptive block/query choices.

Counterexample when the deployment coin leaks into querying: take U uniform, p_1=1/2,
A_1=1{U<1/2}. Query only if A_1=1; suppose that query returns deterministic positive evidence
before round 2, making p_2=3/4, while otherwise p_2=1/2. Reusing U gives P(A_2=1)=1/2,
whereas E[p_2]=5/8. Treating p_2 as the deployment marginal would be wrong. This algebraic
example is not a safety result and does not refute a published method.

Reproduce correctness checks with:

    python -m pytest -q tests/test_delayed_switching_reference.py tests/test_delayed_feedback.py

Execution result: 27 targeted tests passed in 4.36 seconds. Ruff check and format check passed
for the two new Python files; `git diff --check` passed. The exact-expectation test enumerates
64 length-6 binary paired-loss paths, eight query-location schedules each, for three delays;
deployment randomness is integrated analytically. These are correctness checks, not efficacy
experiments, statistical calibration, or evidence that this reference is the strongest method.
