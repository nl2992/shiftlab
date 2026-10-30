# Alternative-belief aliasing can destroy causal-risk-constrained value

**Date:** 2026-10-28. **Status:** exact counterexample to posterior-only compression; no novelty claim.

## Contract

Use horizon `T=5`, hard query budget `B=2`, deterministic label delay `d=1`, query price
`c=1/100`, switching cost `k=1/10`, and global causal-null promotion risk `alpha=1/10`.
The incumbent action is forced through rounds 1 and 2 while a challenger is evaluated; the only
promotion opportunity is at the start of round 3, after the two queried labels are released.
Thereafter the chosen action is held. Thus promotion receives three rounds of utility before the
horizon. This is a shadow-mode/evaluation lock, not an assumption about the hidden label path.

Under the known alternative, the hidden state is binary. Initially
`P(S_1=0)=9/10`, `P(S_1=1)=1/10`. The queried binary label is `Y_t=1{S_t=0}`. After round 1,
the state transitions to 0 with probability one and remains there. Hence the only alternative
label tapes are `11` with probability `9/10` and `01` with probability `1/10`. At the round-3
decision, the current-state posterior is `P(S_3=0 | history)=1` for both tapes. When `S_t=0`,
the paired losses are `l_t(0)=1`, `l_t(1)=0`; the challenger therefore earns one unit per future
round. The net value of promotion, before acquisition costs, is `3-k=29/10`.

The safety null is separate: at each queried event and after every full event history, its
conditional success probability is any value in `[0,1/2]`. This null controls promotion error;
the alternative HMM determines expected economic value.

## Proposition

Let `G=3-k=29/10` be the net deployment value per promotion before query cost. For any
`0<alpha<9/20`, a full-history safe policy has value at least
`(9/10) min(1,4 alpha) G - 2c`. Under the same fixed two-query calendar, every policy whose
decision state is only the current alternative posterior (plus common time, incumbent, budget
and pending-query state) has value at most `min(1,2 alpha) G - 2c`. The full-history lower bound
is strictly larger throughout this alpha range. At `alpha=1/10`, the respective values are
`128/125=1.024` and `14/25=0.56`, a gap of `58/125=0.464`.

**Proof.** Query events 1 and 2. At the round-3 decision, after both outcomes have been generated,
draw a fresh private coin and promote with probability `2/5` on label tape `11`; never promote
otherwise. For general risk level `alpha`, choose activation `min(1,4 alpha)`; under any causal null,

`P(Y_1=1,Y_2=1) = p_1 p_2(1) <= 1/4`,

so worst promotion risk is at most `alpha`. Under the alternative, tape `11` has probability
`9/10`, so promotion probability is `(9/10)min(1,4 alpha)`. Its value is at least
`(9/10)min(1,4 alpha)G-2c`.

For a posterior-only policy, both alternative histories `11` and `01` map to the same state at
the decision: current posterior is concentrated on state 0, both labels have arrived, the
incumbent is still installed, and both query rights are spent. It must therefore promote with the
same probability `beta` on both supported histories. Even granting it the most favorable
off-support behavior, let it promote only when the second label is 1. Under the null,
`P(Y_2=1)<=1/2`, so its worst promotion risk is `beta/2`; hence `beta<=min(1,2 alpha)`. Under
the alternative, `Y_2=1` always, so promotion probability is at most `min(1,2 alpha)`. After
paying the same fixed query cost `2c`, its net value is at most `min(1,2 alpha)G-2c`. The
difference is positive for `0<alpha<9/20`, and equals `58/125` at alpha `1/10`. QED.

Both policies use the same fixed queries at events 1 and 2, so this comparison isolates policy
memory rather than acquisition timing. The exact arithmetic is checked by
`scripts/check_switching_alt_belief_risk_alias.py`. It checks exact values at alpha
`{1/20, 1/10, 1/4, 2/5}`; output and script hash are stored under
`outputs/switching_alt_belief_risk_alias_v1/results.json`.

## Interpretation

This disproves a full-oracle approximation guarantee for policies that retain only the
alternative HMM posterior, even when that posterior is exact and the label/query clocks are
matched. The reason is that two histories with the same economic belief can have different
likelihood under the alternative and different relevance to the robust null-risk allocation.

It does **not** rule out finite-state controllers with extra risk-relevant memory: storing the
first label distinguishes the two histories in this example. It also does not establish that a
small memory state suffices for general nonmonotone promotion events, or that the counterexample
is an ICML-level novelty result. The exact alpha sweep shows a positive gap for every
`0<alpha<9/20` in this fixed model, but the sufficient one-bit memory is specific to this
two-label construction. Any compression theorem must quantify memory as horizon, budget, delay and
alternative complexity grow, then compare its utility with the full-history robust oracle; an
alternative-belief grid alone is insufficient.

## Risk slack does not repair posterior aliasing

At `alpha=1/10`, require the full-history policy to leave slack `eta=1/100`. Set its activation
probability on tape `11` to `gamma=4(alpha-eta)=9/25`. Its causal-null promotion risk is exactly
`gamma/4=9/100`, so the policy has the stipulated positive slack. Under the alternative, it
promotes with probability `(9/10)gamma=81/250`. Since `G=29/10` is the net deployment value per
promotion before query cost, its expected net value is

`(81/250)(29/10)-2/100 = 2299/2500`.

The posterior-only upper bound remains `14/25`: both supported histories share one posterior
state, so the policy must use the same promotion probability `beta` on them; the causal null
forces `beta/2<=1/10`, and the alternative has `Y_2=1` with probability one. The gap is therefore
`2299/2500-14/25=899/2500`, despite the full-history policy's `1/100` risk slack. Thus a risk
margin alone does not make posterior compression safe or economically accurate. A valid
approximation result needs a separate, uniform bound on its causal-null risk error and its
alternative cost error; only then can slack absorb the former. This remains a fixed two-label
counterexample and gives no growing memory lower bound or algorithmic novelty claim.
