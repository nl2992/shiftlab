# Order-sensitive label acquisition under delayed switching

**Date:** 2026-10-29. **Status:** rejected after exact payoff correction. The posterior histories
differ, but the registered economics do not produce different optimal acquisition actions.

## Claim

Two histories with the same observed-loss multiset do produce different HMM posteriors. The prior
version incorrectly converted those posteriors into future switching value: its formulas failed to
propagate the posterior through every future round before evaluating expected loss. Recomputing the
cash flows from the registered HMM shows that neither history warrants switching, and querying has
zero gross switching value in both. This example therefore does not separate an order-sensitive
acquisition rule from a score-priority rule.

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
| `101` | `54/65` | stay; do not query |
| `011` | `33/35` | stay; do not query |

For a no-query switch held at events 4–6, the correct expected gross advantage is
`sum_{j=1}^3 (2 p_j - 1)`, where `p_j=0.1+0.8 P(S_{3+j}=1|history)` is calculated by propagating
the HMM at each round. This gives `301/650` at `h_A` and `31/50` at `h_B`, both below the switch
fee `13/20`; the nonnegative net switch value is zero in both histories.

If event 4 is queried, its label arrives at event 5. For either possible label, the maximum gross
advantage from switching at event 5 and holding through event 6 is below the switch fee. The
expected gross value of the query for switching is therefore zero in both histories. With the
`1/5` promotion lottery and `c=1/1000`, the conditional net values are:

| History | Query net value | Immediate safe-switch value | Choice |
|---|---:|---:|---|
| `101` | `-1/1000` | `0` | neither |
| `011` | `-1/1000` | `0` | neither |

The corrected exact rational checker is `scripts/check_switching_order_sensitive_acquisition.py`; run
`uv run python scripts/check_switching_order_sensitive_acquisition.py`. It recomputes HMM forecasts
at each decision round, enumerates endpoint causal-null kernels, and checks the hard cap and exact
risk. The restricted sequence-form oracle replay is
`uv run python scripts/check_order_sensitive_candidate_against_causal_oracle.py`; it independently
optimizes the same timing/action class and chooses stay/no-query at both histories. The null-risk
calculation remains `1/20` for the hand-written lottery, but it does not change the economic result.

## Research consequence

The corrected result is a failed candidate, not evidence for a new method. The order-sensitive
posterior calculation is valid, but the selected switch cost and horizon make both query and switch
uneconomic. G1 remains open; do not use the earlier claimed value separation. G2–G5 remain held; no
efficacy sweep or real-data run follows from this constructed example.

The causal-risk randomization here is distinct from economic belief: a historical safe-test event
does not certify future profitability after an unobserved reversal.
