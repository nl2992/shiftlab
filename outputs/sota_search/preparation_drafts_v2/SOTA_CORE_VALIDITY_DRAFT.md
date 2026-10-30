# Conditional proof obligations for the current fixed-stake core

This is an algebraic audit of existing mechanisms, not a novelty claim or a proof
that every synthetic cell satisfies the required null. It is outside the running
source closure and does not change the registered screen.

## Information and null

Let H_{t-1} be a full event-time history containing the independent source sample,
all past generated outcomes and query randomization, and all delay information
available when current choices are made. The learner sees a subset of that history.
Let S_t denote current covariates and auxiliary proxy readings, which can be
correlated with the current outcome. Let Z_t be the bounded normalized target
score, |Z_t|<=1. Assume E[Z_t | H_{t-1}]<=0 for every t under the claimed null.

The current global stake lambda is fixed before S_t. Its history-predictability
would also suffice. The proxy h_t in [-1,1] and propensity q_t may depend on S_t
and learner-visible history, and q_t must be chosen before the true-label query
coin. Conditional on all that information and the potential outcome, the query
coin is Bernoulli(q_t), independent of the current true outcome.

## Query correction and the fixed-stake distinction

The factor is F_t=1+lambda*[h_t+Q_t*(Z_t-h_t)/q_t]. Conditional on S_t,Z_t,H_{t-1},
averaging over the coin gives E[F_t | S_t,Z_t,H_{t-1}]=1+lambda*Z_t. Because lambda
does not depend on S_t, averaging S_t and Z_t next gives E[F_t | H_{t-1}]<=1.

This remains true for an inaccurate, anti-informative or outcome-correlated cheap
proxy under the stated independent query design. It does not require the stronger
null E[Z_t | S_t,H_{t-1}]<=0. However, a stake lambda_t(S_t) cannot be moved outside
that expectation. Context-dependent bets would need a stronger conditional null
or a separate justification. A mean-zero two-context example can violate the
weaker null's factor bound if the larger stake is placed on the positive context.

For factors 1+lambda*z in [1-lambda,1+lambda], q_t>=2*lambda/(1+lambda) ensures
nonnegativity for all allowed proxy and outcome values. The current adapter uses
this floor. At a known exhausted budget it instead contributes F_t=1, not a
division by zero or uncorrected proxy. This is a predictable evidence stop.

## Delay, missing labels, starts and multiplicity

The event-time product is a nonnegative test supermartingale if the above
conditions hold. The learner reveals only a contiguous prefix of resolved factors.
Any prefix alarm is pathwise contained in an event-time wealth crossing, so delay
and permanently unresolved labels can reduce power without creating additional
crossings. This relies on never advancing past unresolved evidence or treating
latency as positive evidence. The repository's existing event-prefix proof records
this argument; it is not a new theorem here.

Each fixed-start product is one before its predetermined start. A fixed convex
mixture of these products preserves its mean bound. The current two-challenger
comparison allocates alpha/2 to each fixed pair, and the union bound controls
the familywise crossing event only under each pair's required null. Reweighting
mixture components using current context is not covered by this fixed-mixture
argument. Future adaptive weights need a separate construction.

## Q1 independent source uncertainty

For IID bounded source observations, the one-sided Hoeffding allowance controls
the source risk upper-bound failure event at .025. Conditional on a valid source
upper bound, a .025 target process gives a nominal .05 union-bound total only if
the target null is the declared conditional mean relative to that bound. The code
rejects a source-upper-plus-margin threshold above one. G3/G4 source dependence
is not covered by the IID allowance and therefore prevents an unconditional
claimed .05 theorem for the current source-reference adapter.

## What remains unproven

The generated stationary worlds have not all been shown to satisfy the full
history-conditional null. CUSUM is not governed by the PPE proof. PPRM's batch
contract, random subset sizes, cap truncation and source reference need separate
analysis. Current empirical source calibration, instantaneous decision harm and
running-average risk comparisons are different endpoints. This note establishes
only the conditional implication above; it does not validate a SOTA reproduction,
confirm a research improvement or establish new methodological priority.
