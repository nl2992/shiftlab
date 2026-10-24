# Event-prefix validity with delayed labels

**Status:** proof note for the existing frozen-policy PPI monitor. This is not a new e-process and does not extend the empirical confirmation beyond its registered data-generating process.

## Setup

Let `G_t` be the full event-time history immediately before event `t`. It may include past contexts, outcomes, query decisions, and any past delay/arrival information. Before observing `Y_t` or the current query coin, the learner chooses a predictable propensity `q_t` and computes a bounded proxy `H_t` from information allowed by the registered null. Let `Q_t` be an independent Bernoulli request with probability `q_t`, and let `Z_t` be the bounded paired decision-cost contrast. The PPI increment is

`X_t = H_t + Q_t (Z_t - H_t) / q_t`.

Assume `|Z_t|, |H_t| <= M`, `q_t >= q_min > 0`, and the conditional-mean null `E[Z_t | G_t] <= 0`. Assume query coins are independent of the current outcome conditional on `G_t`, and queried labels eventually resolve with their correct event index. Delays may be arbitrary, including dependent on `Z_t`, provided the delay for event `t` is not used to choose `q_t`, `H_t`, or `Q_t` before the query/outcome is generated. The monitor does not treat latency or non-arrival as evidence.

Then `E[X_t | G_t] <= 0` and `|X_t| <= B_t = M(2/q_t - 1)`. Since `B_t` is predictable, any bounded-mean betting factor valid for `[-B_t, B_t]` has conditional expectation at most one. The event-time wealth `E_n` is consequently a nonnegative supermartingale under the registered null, and Ville's inequality gives

`P(sup_n E_n >= 1/alpha) <= alpha`.

## Arrival-time alarm rule

At wall time `s`, define `N_s` as the largest event index for which every increment `1,...,N_s` has resolved. The learner updates wealth only through this contiguous prefix and may alarm only when `E_{N_s} >= 1/alpha`. For every realized path,

`{there is an arrival-time alarm} subset {sup_n E_n >= 1/alpha}`.

Thus the same false-alarm bound holds under arbitrary finite, possibly outcome-dependent delays. This argument does **not** claim that the event-time wealth is a supermartingale in the arrival-time filtration, nor that alarm latency or power is delay-invariant. Outcome-dependent delays can substantially change when evidence becomes available. If a label never resolves, the prefix can stall and power can be lost, while the alarm bound remains valid for alarms based only on the prefix that did resolve.

## Limits

The result requires all evidence increments to belong to one valid event-time sequence. It does not cover delay or non-arrival used as a statistical signal; query selection based on the current event's pre-outcome delay signal; selectively omitting pending labels while advancing the prefix; optional changes to the action pair or proxy; or a conditional-mean null that omits past information used by the policy. Serial dependence is permitted only if the stated conditional null and predictable-bound argument hold given the full history `G_t`. In particular, the iid result in the current experiment does not establish that condition for the project's Markov streams.

This is a pathwise stopping-set argument layered on an ordinary event-time e-process, not a new delayed-feedback testing method. The empirical delayed confirmation remains limited to iid events and deterministic, outcome-independent delay 12. A separate simulator with informative delays can assess latency and power, but is not needed for this false-alarm proof.

## Relation to existing work

Podkopaev and Ramdas (ICLR 2022) already formulate sequential risk monitoring for labels revealed after prediction, including batch-delayed labels. Their source/target confidence-sequence construction is a direct comparator for the risk-increase problem. Lindon and Kallus (ICML 2026) emphasize the importance of choosing an event-time filtration for delayed outcomes and staggered entry; their randomized-experiment estimand and construction differ from this PPI monitoring setting. The present note only isolates the simpler implication of checking a valid event-time process on its resolved prefix.

References: [Podkopaev and Ramdas (2022)](https://arxiv.org/abs/2110.06177); [Lindon and Kallus (2026)](https://proceedings.mlr.press/v306/lindon26a.html).
