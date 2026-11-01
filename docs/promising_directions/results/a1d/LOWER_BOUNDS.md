# A1d two-sided mixture-gap bounds (added 2026-11-01)

Computed by `scripts/promising_directions/mixture_bounds.py` from `calendar_values.jsonl`.

## Why bounds are needed

The original A1d `g_mix` values are grid upper bounds only. See the correction in
`13_A2_BRANCH_CONFLICT_THEORY.md`, Remark 1.

## Validity check

All 279 calendar cost curves (3 priors × 93 calendars) were checked on the 14-level grid. Every
curve is nonincreasing and convex. Those are the two properties the lower bound relies on.

## Relative mixture gap bounds `[lower, upper]` at T = 9

| prior1 \ alpha | 1/10 | 3/20 | 1/5 | 1/4 | 3/10 | 1/2 | 1 |
|---|---|---|---|---|---|---|---|
| 1/10 | [0, 0] | [.0090, .0090] | [.0286, .0286] | [.0507, .0507] | [.0502, .0519] | [.0480, .0580] | [.0162, .0162] |
| 1/5 | [0, 0] | [.0046, .0046] | [.0146, .0146] | [.0257, .0257] | [.0403, .0404] | [.0468, .0473] | [.0120, .0120] |
| 3/10 | [0, 0] | [0, 0] | [0, 0] | [0, 0] | [.0081, .0198] | [−.0130, .0560] | [.0092, .0092] |

## Conclusion

The A1d H-risk result is established with proven lower bounds:

- prior1 = 1/10, alpha = 1/4: the mixture gap is at least 5.07%, against 1.62% unconstrained.
- prior1 = 1/5, alpha = 1/2: the mixture gap is at least 4.68%, against 1.20% unconstrained.

At prior1 = 3/10 the lower bound is weaker, and at alpha = 1/2 it is inconclusive (the lower
bound is negative).
