# T=8, B=4 adaptive-reservation comparison

Executed on 2026-10-29 under `T8_B4_CALENDAR_PROTOCOL_V1.md`. All six
deterministic HMM cells and all 342 calendar policies completed; exact cell and
policy metrics, costs, risks, solver residuals and source hashes are in
`t8_b4_calendar_v1.json`. The executed runner is preserved in
`t8_b4_calendar_executed_source_v1.txt`; the tracked runner differs only by a
lint cleanup.

The full decomposed reference strictly beats the best calendar in the two
`transition=1/10` cells, by `6744087/781250000` and
`11126044659/976562500000`. This confirms adaptive query timing has economic
value at B=4 in these two model-known development cells. However, none of the
restricted candidates captures that improvement: the `m=3` cap and every
registered e-process threshold lose to the best calendar in those cells.

| Transition | Emission pair | Best calendar | Full gap | m=3 cap gap | Gate 4 gap | Gate 8 gap | Gate 16 gap |
|---|---|---|---:|---:|---:|---:|---:|
| 1/10 | 1/10, 9/10 | [1,2,3,4] | -6744087/781250000 | 545156/48828125 | 69981647/781250000 | 428516/48828125 | 27124011/312500000 |
| 1/10 | 1/50, 49/50 | [1,2,3,4] | -11126044659/976562500000 | 41203152987/976562500000 | 37758243879/195312500000 | 27333257307/976562500000 | 527886357/3906250000 |
| 1/4 | 1/10, 9/10 | [1,2,4,5] | 0 | 0 | 0 | 447/125000 | 55999/2000000 |
| 1/4 | 1/50, 49/50 | [1,2,3,5] | 0 | 188679/39062500 | 188679/39062500 | 0 | 5881239/156250000 |
| 9/20 | 1/10, 9/10 | [] | 0 | 0 | 0 | 0 | 0 |
| 9/20 | 1/50, 49/50 | [] | 0 | 0 | 0 | 0 | 0 |

Gaps are exact recovered calibrated cost minus the best calendar cost. A
negative full-reference gap is an expected result: the unrestricted adaptive
planner is a stronger policy class than any fixed calendar. The `m=3` cap
loses both cells where this adaptive value appears. Gate thresholds 4, 8 and 16
also lose there. In intermediate persistence, the cap and threshold 4 match the
best calendar in one cell; threshold 8 matches it in the other. The high
persistence cells select no queries.

This is a bounded development result over previously exposed HMM parameters,
not independent confirmation. It identifies the missing behavior more sharply:
use of all four pre-promotion observations with history-dependent query timing,
while retaining a feasible promotion-risk strategy and post-promotion budget.
The registered cap/e-process candidates do not supply that policy. No synthetic
candidate wins the strongest calendar baseline here, so the real-data gate stays
closed and no novelty claim is advanced.
