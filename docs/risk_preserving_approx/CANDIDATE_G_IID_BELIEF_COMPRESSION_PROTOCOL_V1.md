# Candidate G: exact belief-state compression of the IID relaxation

**Registered:** 2026-10-29 before the reachable-belief screen. This is one
development-only state-count test on a previously exposed T=10 synthetic case.
It does not access outcomes, seeds, real data or holdouts and does not run an LP.

## Hypothesis and model

Candidate B's IID relaxation replaces the unrestricted causal-null risk
constraints during candidate generation by the risk under an independent fair
queried-label process. Represent this relaxed two-law problem as a POMDP with a
static hidden root mode (alternative HMM versus IID fair labels), augmented by
the alternative regime, pending queried labels and their release times. A
belief over this finite hidden state, together with event time, remaining query
rights and deployment, is sufficient for scalarized alternative cost plus IID
first-promotion risk. Promotion terminates the IID risk component and delegates
alternative economic continuation to the existing exact DP. Returned policies
would still require exact full-history causal-null verification and safety
repair; this compression is only for the relaxed planner.

The exact reachable beliefs form a finite set for finite horizon. If their
number is materially smaller than the public-history information sets, a
belief-state occupancy LP or Pareto dynamic program may avoid Candidate B's
learner realization variables without changing the IID-relaxation optimum.

## Frozen screen

Use `T=10, B=4, d=2, alpha=1/10`, symmetric transition `1/10`, emissions
`(1/50,49/50)`, prior `1/2`, query fee `1/100` and switch fee `1/10`, matching
`IID_RELAXATION_T10_STRESS_PROTOCOL_V1.md`. Give the two hidden root modes equal
positive prior weight for the count screen. Enumerate reachable canonical exact
belief states over all legal pre-promotion query choices and released IID/alt
observations, merging only identical joint beliefs with the same time, remaining
rights and deployment. Count transitions and measure build time. Separately use
the registered Candidate B output's public-history and realization counts as
the baseline; do not rebuild or solve that reference LP.

Preserve output at `docs/risk_preserving_approx/candidate_g_iid_belief_screen_v1.json`
and refuse to overwrite it. Record protocol, runner, model and reference-output
hashes.

## Decision rule

Continue to a source-matched algorithm audit only if the exact belief graph has
at most half as many decision states as the 4,867 public-history states and is
built within 60 seconds. If it fails either condition, close this exact-belief
compression direction without optimizing any parameters. A pass is only a
feasibility result: prior art, exact scalarized/constrained optimality, cost,
full causal-null risk, dual lower bounds, policy extraction, and end-to-end
comparison remain mandatory before any method or utility claim. Candidate B's
existing synthetic calendar wins do not count as Candidate G results.
