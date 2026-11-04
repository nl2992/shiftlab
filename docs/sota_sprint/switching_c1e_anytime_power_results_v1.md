# C1-E anytime promotion-power screen — results v1

**Status:** exact finite-cell development result; closes the registered four-query C1-E timing
mechanism in this cell. It is not a general lower bound, new method, or SOTA claim.

The frozen contract is in [`protocol`](switching_c1e_anytime_power_protocol_v1.md), the exact
runner is [`screen_switching_c1e_anytime_power_v1.py`](../../scripts/screen_switching_c1e_anytime_power_v1.py),
and the machine-readable result is
[`result.json`](../../outputs/switching_c1e_anytime_power_v1/result.json) (generated artifact).

## Exact result

The screen reuses the two-state HMM pair from the earlier C1-E information screen: symmetric
transition switch probabilities 0.3 (alternative) and 0.1 (null), shared emissions
`P(+|0)=0.8`, `P(+|1)=0.2`, uniform stationary start, `T=20`, one-event label delay, and
request-time pathwise cap `B=4`. The policy promotes at the first likelihood-ratio crossing
`LR >= 1/alpha`. For this simple fixed null, the likelihood ratio over predictably queried labels
is a null martingale, so Ville's inequality gives the declared false-promotion bound.

| Alpha | LR threshold | Exact adaptive power | Best fixed-calendar power | Best burst power | Adaptive null crossing |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 20 | 0 | 0 | 0 | 0 |
| 0.10 | 10 | 0 | 0 | 0 | 0 |
| 0.20 | 5 | 0 | 0 | 0 | 0 |

The exact sensing DP has 379,225 memoized states and 271 reachable policy states. Because every
adaptive policy with at most four queries produces, on each realized path, one of the fixed
query calendars enumerated by the screen, the maximum LR over all fixed calendars and all their
outcome strings also bounds the LR attainable by any adaptive policy. That global maximum is
`386611/245941 = 1.5719664472`, attained by calendar `[14,16,17,19]` and outcomes `[−,+,+,−]`.
It is below the loosest registered threshold 5. Therefore zero promotion power is an exact
consequence of this finite information cap, not a Monte Carlo non-detection.

The tie-broken adaptive oracle queries four labels and obtains the same zero power as every
calendar. Thus the earlier 3.92% expected-transcript-KL advantage over the best fixed calendar
does not yield a promotion advantage under an anytime risk threshold in this cell.

## Decision

Close the four-query C1-E adaptation as a method lead. Do not expand this cell's horizon, label
budget, alpha grid, or model separation after inspecting the outcome. A different parameterized
screen would require a new frozen protocol and must first identify a non-compositional result
beyond controlled Markov hypothesis testing and finite-budget active testing. The result does not
close other HMM families or establish that every larger budget has zero power.

## Provenance

- Runner SHA-256: `e0091d01e99227b1d7f14a2d39e287746625522a8381974a2691d369c1fd28a8`.
- Protocol SHA-256: `5a8682322b3993490438ae5bbe397a08f69db5eac96e3e46504663967c920ba4`.
- The source-level comparator boundary is documented in
  [`switching_novelty_delta_v1.md`](../switching_novelty_delta_v1.md) and
  [`switching_three_named_works_source_audit_v1.md`](../switching_three_named_works_source_audit_v1.md).
