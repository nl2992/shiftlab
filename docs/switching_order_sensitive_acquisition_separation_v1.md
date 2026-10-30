# Order-sensitive label acquisition under delayed switching

**Date:** 2026-10-29. **Status:** exact finite counterexample separating economic query value
from order-insensitive observed-loss priority; not a scalable algorithm or a full G1 pass.

## Claim

Under one two-state recurrent HMM, two delayed-observation histories with the same observed-loss
multiset, same current observed loss, same remaining query budget, and same time can require
different acquisition actions under the same hard budget, switch cost and global causal-null risk
constraint. Therefore an acquisition rule based only on the current decision-loss score and an
order-insensitive empirical quantile of past scores cannot be optimal on this family. The relevant
state is the order-sensitive posterior over future policy value.

This is a strict separation from a scalar score-priority gate of the kind audited for ADOWIP. It
does not separate from Bayesian value-of-information planning, a POMDP, or the exact sequence-form
oracle; those remain the strongest novelty objections.

## Contract

- Horizon `T=6`, fixed release delay `d=1`, and request-time pathwise query budget `B=4`.
- Two-state alternative HMM with `P(S_{t+1}=1|S_t=0)=1/4`,
  `P(S_{t+1}=1|S_t=1)=3/4`, prior `P(S_1=1)=1/2`, and binary paired outcome `Y_t` satisfying
  `P(Y_t=1|S_t=1)=9/10`, `P(Y_t=1|S_t=0)=1/10`.
- Outcome `Y=1` means policy 1 has one unit lower loss than policy 0 (`Z=loss_0-loss_1=+1`);
  `Y=0` means `Z=-1`. Each query reveals the paired losses. Query cost is `c=1/1000` and a
  deployment switch costs `k=13/20`.
- Query at events 1, 2 and 3, with each label released one event later. No promotion occurs before
  event 4. At event 4 compare one remaining query with a one-time switch decision. A no-query switch
  at event 4 is held through events 4–6; a query at event 4 arrives at event 5, after which a switch
  is held through events 5–6. Event 4 is the final query opportunity in this constructed episode;
  no new labels can be requested at events 5–6. This makes the label budget's final right expire
  after event 4, rather than letting a policy silently move the query to another event.
- Promotion at either branch is randomized independently with probability `1/5`. It is attempted
  only on prefix `011` (immediate at event 4) or on prefix `101` followed by `Y_4=1` (after the
  delayed query, at event 5). All other histories stay with policy 0.

The randomization makes the policy's risk event explicit. For any full-history causal null with
`P(Y_t=1 | full past, predictable query)<=1/2`,

`P(011) <= 1/4`, and `P(1011) <= 1/8` individually, but these events share the first outcome and
cannot both attain their separate bounds. Writing `p=P(Y_1=1)`, their combined contribution obeys

`P(011)+P(1011) <= (1-p)/4 + p/4 = 1/4`.

Thus worst-case any-promotion risk is exactly `(1/5)(1/4)=1/20=alpha`; endpoint enumeration in the
checker confirms the exact supremum. Earlier queried labels do not prompt an intervention. The
request cap is respected on every path: three initial queries and at most one event-4 query.

## Exact economic comparison

Consider histories `h_A=101` (`+,-,+`) and `h_B=011` (`-,+,+`). Both have score multiset
`{0,1,1}` if the current incumbent's observed 0/1 decision loss is used as the score, and both
have current score `1`. An empirical-quantile priority rule with any order-insensitive score
summary therefore faces the same query decision at both histories.

The HMM filters differ because the order differs:

| History | `P(S_3=1 | history)` | Safe best action at event 4 |
|---|---:|---|
| `101` | `54/65` | query once, then possibly switch |
| `011` | `33/35` | switch immediately; do not query |

For a no-query switch held at events 4–6, expected gross advantage before the switch fee is
`7 b/4 - 7/8`, where `b=P(S_3=1|history)`. After subtracting `k`, the best nonnegative value is
`max(0,7b/4-7/8-k)`. At `h_A` this is zero; at `h_B` it is `1/8`.

If event 4 is queried, its label arrives at event 5. The expected best future value before query
cost, conditional on the event-3 belief, is `339/26000` at `h_A` and `363/14000` at `h_B`. With
the `1/5` promotion lottery and `c=1/1000`, the conditional net values are:

| History | Query net value | Immediate safe-switch value | Choice |
|---|---:|---:|---|
| `101` | `209/130000` | `0` | query |
| `011` | `293/70000` | `1/40` | switch now, no query |

The exact rational checker is `scripts/check_switching_order_sensitive_acquisition.py`; run
`uv run python scripts/check_switching_order_sensitive_acquisition.py`. It independently recomputes
the HMM posteriors and decision values, enumerates endpoint causal-null kernels, and checks the hard
cap and exact risk.

## Research consequence

This counterexample demonstrates why a delayed switching acquisition score must account for
order-sensitive current-regime belief, remaining hold horizon, switch cost, pending feedback, and
the remaining risk/budget state. It is a mechanism-design diagnostic and a precise separation from
order-insensitive loss-priority gates. It is not itself a new algorithm: finite-horizon POMDP/VOI
planning and the full sequence-form oracle can represent this example exactly. G1 remains open until
a scalable acquisition rule or growing-family theorem separates from those methods under matched
information, risk, delay and cost. G2–G5 remain held; no efficacy sweep or real-data run follows from
this constructed example.

The causal-risk randomization here is distinct from economic belief: a historical safe-test event
does not certify future profitability after an unobserved reversal.
