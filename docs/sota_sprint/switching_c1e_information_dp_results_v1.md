# C1-E exact information screen — results v1

**Status:** finite-cell exact development result; no SOTA or novelty claim.

The frozen HMM cell and calculation are specified in
[`switching_c1e_information_dp_protocol_v1.md`](switching_c1e_information_dp_protocol_v1.md).
The deterministic runner enumerated 6,196 fixed calendars and solved the belief-state sensing
dynamic program using exact rational beliefs (natural-log KL values).

| Quantity | Result |
|---|---:|
| Best fixed calendar (zero-based events) | `{0, 2, 3, 5}` |
| Best fixed-calendar transcript KL | `0.0508064456` nats |
| Best contiguous burst | `{0, 1, 2, 3}` |
| Best contiguous-burst transcript KL | `0.0472588756` nats |
| Adaptive sensing optimum | `0.0527964098` nats |
| Adaptive gain over best calendar | `0.0019899642` nats (`3.92%`) |
| Expected queries under adaptive optimum | `4.0` |
| Reachable policy states / all DP memoized states | `239 / 379,225` |

The adaptive optimum beats the strongest fixed calendar in this one cell, but the margin is small
and is ordinary finite-horizon adaptive sensing evidence. The calendar closes much of the gap to
the exact oracle; this does not support a novel method. The burst is not even the best fixed
calendar, which weakens a burst-only comparison. No C1-E advance follows. To continue, the next
useful screen would need a tractable policy with a certified guarantee under the same hard cap and
delay, plus a promotion-risk construction and a rate result beyond routine belief-state planning.

Artifacts and provenance:

- Runner: [`screen_switching_c1e_information_dp.py`](../../scripts/screen_switching_c1e_information_dp.py)
- Machine-readable output: `outputs/switching_c1e_information_dp_v1/result.json` (ignored)
- Runner SHA-256: `042be9fc875aa40474e61652ba5dc69382b3de72d0cd738495882d31b63d04ab`
- Frozen protocol SHA-256: `42e4590066d71798b59975e2958a810529f05d2df0b587a309c74a327cc59b5b`

Interpretation is limited to expected transcript information in the frozen cell. It says nothing
directly about power, false-promotion probability, deployment cost, or the performance of an
implementable approximation to the exact oracle.
