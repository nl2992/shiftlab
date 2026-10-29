# Monotone promotion restriction can lose all safe economic value

**Date:** 2026-10-28. **Status:** exact finite counterexample; no novelty claim. This tests
whether the monotone-event risk reduction can support a uniform approximation to the unrestricted
causal-risk oracle.

## Contract

There are two binary queried labels `(Y1,Y2)`, both observed before a single terminal promotion
decision. The learner has a hard budget of two labels and may randomize over deterministic plans
up front. Query cost is zero, so any separation persists with free information. Promotion incurs
switch cost `k=1/20`. The global null permits any causal conditional success probability at most
`1/2` at each event time. The false-promotion constraint is `alpha=1/10`.

Interpret the displayed promotion payoff as expected net utility over a declared downstream
deployment horizon conditional on the observed two-label history. Labels are requested at rounds
1 and 2 and released at rounds 2 and 3 (fixed delay one); the decision is at round 3. This is a
predictive economic model, so it explicitly assumes that histories forecast future value. The
global-null guarantee remains only a bound on false promotion under the label conditional-mean
null; it is not a future-profit guarantee. No constraint in this example requires that the
forecasted downstream value be monotone in past label signs.

Under the declared alternative, `(Y1,Y2)` is `01` or `11`, each with probability `1/2`. The net
future value from promotion is `+1` on tape `01`, `-2` on tape `11`, and zero on other tapes.
This models evidence whose first sign predicts a reversal: the later positive outcome supports
deployment only after a negative first outcome. The alternative is intentionally allowed to have
temporal dependence; no IID alternative assumption is used.

## Proposition

Among all deterministic promotion events that are coordinatewise increasing in `(Y1,Y2)`, the
best alternative net value is zero (the no-promotion plan). Yet an unrestricted policy satisfying
the causal global-null risk constraint obtains expected net value at least `19/200`.

**Proof.** There are 16 Boolean events; six are coordinatewise increasing. Any increasing event
that contains tape `01` must contain its coordinatewise successor `11`. Promoting on both has
alternative gross value at most `(1/2)(+1)+(1/2)(-2)=-1/2`; the switch charge can only lower it.
An increasing event that excludes `01` has nonpositive gross value because its only possible
positive payoff is on `01`. Thus every monotone pure event has nonpositive value; upfront
mixtures retain this property, while no promotion attains zero.

Consider instead event `E={01}`. Under any causal null, its probability is
`(1-p1)*p2(0) <= 1/2`; equality is attained by `p1=0,p2(0)=1/2`. Activate this plan with
probability `alpha/(1/2)=1/5`, which gives robust false-promotion probability `1/10`. Under the
alternative, the plan promotes with probability `1/2`; its expected net value before activation
is `(1/2)(1-1/20)=19/40`. The safe mixture therefore obtains `(1/5)(19/40)=19/200`. QED.

This is a strict finite separation: the monotone restriction has zero value while a robustly safe
unrestricted policy has positive value. Hence no positive multiplicative approximation guarantee
for the monotone-event class can hold over this signed-future-value model family without an
additional assumption excluding reversal-predictive evidence.

## Checks and limits

`scripts/check_switching_monotone_class_separation.py` enumerates all 16 event functions, verifies
the six monotone events and computes each causal null supremum over the endpoint conditional
probabilities `{0,1/2}`. It checks the exact rational risk and value calculations above. Run:

    python scripts/check_switching_monotone_class_separation.py

Output and script hash are stored in `outputs/switching_monotone_class_separation_v1/checks.json`.
This checker validates the finite arithmetic; the proof covers the stated model. The example is
not a new acquisition algorithm, does not show that an assumption excluding reversals is
reasonable in finance, and does not establish that any source-audited prior lacks a matching
result. It falsifies the universal utility-preservation route for monotonicity. A viable direction
must either exploit a substantively justified alternative structure or preserve causal robustness
without assuming that beneficial histories form an increasing set.
