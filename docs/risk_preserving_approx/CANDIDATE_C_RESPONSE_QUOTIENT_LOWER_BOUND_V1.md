# Candidate C: lower bound for a universal causal-response quotient

**Date:** 2026-10-29. **Status:** proved for the stated quotient model; no
algorithm or general approximation lower bound is claimed. **Decision:** reject
universal history merging as the route to a compact exact pricing state. Continue
the research program with a different mechanism.

## Question

Can an exact response-continuation quotient merge public learner transcripts that
agree on time, remaining query budget, deployment, pending queue and the
alternative-HMM belief, while preserving every allowed full-history causal-null
response?

## Proposition

Fix a horizon `T >= 3`, one-step feedback delay, and an integer `q` with
`0 <= q <= T-2`. Let `B >= q+1`. Let the alternative have one absorbing hidden
state and a constant Bernoulli(1/2) queried-label emission. The learner draws a
uniform random `q`-subset of `{1,...,T-2}` at the outset, requests on that
calendar, and keeps the incumbent deployed. Under the null response taking
`p=0` on this prefix, the learner's event-`T-1` histories with all queried
labels zero are all reached with positive probability.

All these histories have no pending labels at event `T-1`, and have the same
time, query count, remaining budget, deployment, alternative belief and physical
hidden state. Their public request-time transcripts differ. There are
`N = binom(T-2,q)` such histories.

For any two distinct transcripts `h != h'`, an allowed causal-null strategy can
choose next-query success probability `0` after `h` and `1/2` after `h'` (and
any allowed values after other histories). Under the continuation “query at
`T-1`; promote at `T` iff the released label is positive,” conditional
first-promotion risks after `h` and `h'` are respectively `0` and `1/2`.

Therefore, for every deterministic quotient `phi` that merges any such pair,
there exists an allowed null strategy whose conditional next-response kernel
cannot be represented exactly by a single quotient-state response. If the
quotient uses one common response value for the merged histories, its worst-case
uniform absolute kernel error is at least `1/4`. Exact universal response-state
representations of this family require at least `binom(T-2,q)` states; for `q`
near `(T-2)/2`, this grows exponentially in `T`.

The quantifiers matter: `forall phi, exists nu` for a strategy-independent
quotient and a common response decoder. The result does not say that one fixed
null strategy defeats every possible quotient, nor that a null-specific encoding
must use the same number of states. Also, the robust continuation risk supremum
is `1/2` at either prefix; the proposition distinguishes conditional kernels
under a selected null strategy, not the historywise robust-risk suprema. It gives
no standalone robust-risk or economic-value separation. The test continuation
need not be alpha-safe when `alpha < 1/2`; this is a response-kernel statement,
not a lower bound within the feasible policy class.

## Proof

The full-history null may choose a separate conditional probability in `[0,1/2]`
at each generated history. It can realize an all-zero prefix by choosing zero
after every requested query. The random calendar gives every listed transcript
positive probability under this same prefix response. With delay one, every
request through event `T-2` has been released before event `T-1`. The singleton
alternative state and constant emission make the economic state identical at
all listed histories. Distinct query-time subsets give distinct public
transcripts. A response strategy assigning next-query rates zero and one-half
to a selected pair is admissible. The final
query is made at `T-1`, its outcome is released at the start of `T`, and the
stated promotion rule has conditional risk equal to that response probability.

If `phi(h)=phi(h')`, a common response value `r` for that quotient state must
serve both histories. Since
`max(|r|, |r-1/2|) >= 1/4`, the uniform conditional-kernel error cannot be below
one-quarter. Exactness therefore requires distinct quotient states for each of
the `N` transcripts. Finally,
`binom(T-2, floor((T-2)/2)) >= 2^(T-2)/(T-1)`, establishing exponential growth
along the central-budget sequence.

## Scope and prior-art boundary

This is a lower bound only for a **universal quotient of null response kernels**
that must represent every allowed response strategy. It does not prove that
every risk/value approximation needs that many states, and does not rule out
direct robust optimization, implicit separation, a policy-specific verifier,
or a theorem under additional structure that still compares against the full
oracle. It requires at least `ceil(log2 N)` bits in a deterministic state
encoding. For fixed `q`, `N` is polynomial in `T`; it is exponential in state
count only when `q` grows proportionally with `T`. Even then this is no more
than a cardinality bound for remembering query calendars, and is not a runtime
lower bound for other algorithms.

The alternative-posterior alias artifact independently shows that economic
posterior alone cannot preserve risk-allocation value. The signed future-value
counterexample independently rules out monotone-event restriction as a universal
repair. This proposition assumes neither monotone outcomes nor a monotone
promotion event.

The argument is a direct finite-history distinguishability proof, not a new
automata theorem. Rabin and Scott's Myhill–Nerode characterization says that
continuation-distinguishable histories require distinct deterministic automaton
states; see [*Finite Automata and Their Decision Problems*](https://www.cs.miami.edu/home/burt/learning/csc427.222/docs/rabin-scott.pdf),
Theorem 2 and Corollary 2.1. Here the same elementary idea is applied to
conditional response kernels rather than language acceptance. Chatterjee,
Doyen and Henzinger, [*Partial-Observation
Stochastic Games: How to Win when Belief Fails*](https://arxiv.org/abs/1107.2141),
Theorem 3.1, already establishes belief insufficiency and memory requirements
in one-sided partial-observation games. Horák et al., [*Solving Zero-Sum
One-Sided Partially Observable Stochastic
Games*](https://arxiv.org/abs/2010.11243), provide approximate value-function
machinery for one-sided POSGs, but not this quantitative quotient bound for the
two-law promotion-risk objective. The combinatorial transcript count is also
consistent with the standard perfect-recall extensive-form representation used
by the existing sequence-form solver.

**Novelty assessment:** no standalone method contribution. The useful outcome
is a sharper scope boundary: do not spend implementation time on a universal
history-to-null-response-state quotient. A distinct optimization or
approximation mechanism is still required.

## Provenance and next test

Inputs: `CANDIDATE_B_PRICING_STATE_COUNTEREXAMPLE_V1.md`,
`switching_alt_belief_risk_alias_counterexample_v1.md`,
`switching_monotone_class_separation_v1.md`,
`switching_two_law_game_duality_v1.md`, and the event order in
`switching_problem_v1.md`. No code, seed, data row or holdout was accessed for
this proof.

Next, test a policy-side or implicit-optimization mechanism that does not
require representing every null strategy as a quotient state. It must preserve
the full causal-null family and be compared with the full-history oracle on a
bounded synthetic instance before any scale-up. Real-data evaluation remains
behind the existing G1–G3 gates.
