# A1d registered protocol: does the A1c gap survive public-coin mixtures of calendars?

Registered 2026-10-30 after A1c (`f32f4d7`) and before execution. This is a development and
theory probe. It makes no method claim.

## Confound in A1c

In every A1c cell the risk constraint binds: the raw risk equals alpha exactly, with
activation 1. The joint planner J(alpha) is the value of an LP, so it is convex and
nonincreasing in alpha, and it may randomize at any history. The A1c comparator C*(alpha),
the best *pure* calendar, is a pointwise minimum of per-calendar values and need not be
convex. The observed g(alpha) is non-monotone. At prior1 = 3/10, for example, g is 0.018 at
alpha = 1/5, 0 at 1/4 and 0.021 at 3/10, and the best calendar changes at each step.

A separable policy may flip a public coin at the root to choose between two calendar
policies, each solved at its own risk level. This needs no label information, so it keeps the
information matched. Risk is linear in the mixture, so the mixture has risk at most
lambda·a1 + (1 − lambda)·a2.

The question is whether this convexification removes the A1c "H-risk" excess.

## Comparator

`C_mix(alpha)` is the minimum, over calendars c1, c2, grid levels a1, a2, and lambda in [0, 1]
with lambda·a1 + (1 − lambda)·a2 ≤ alpha, of

    lambda·C_{c1}(a1) + (1 − lambda)·C_{c2}(a2),

where:

- `C_c(a)` is the calibrated total cost of `CalendarOpportunityGame` for calendar c at risk
  level a, with the same solver and settings as A1/A1c (`2bd2e8e`, slots 1..T−d,
  max_nodes 200,000).
- c ranges over every calendar with at most B slots.
- a ranges over the grid
  `A = {0, 1/20, 1/10, 1/8, 3/20, 1/6, 9/50, 1/5, 1/4, 3/10, 2/5, 1/2, 3/4, 1}`.

`C_mix` is computed as the lower convex envelope of the point set {(a, C_c(a))}, evaluated at
each target alpha. Because only grid levels are used, `C_mix` is an upper bound on the true
mixture optimum. The resulting gap `g_mix = (C_mix − J)/J` is therefore an upper bound on the
true mixture gap.

- J(alpha) is reused from A1c where available, and otherwise recomputed.
- Sanity check: `C_mix(alpha) <= C*(alpha)` (pure calendars are a special case), and J ≤ C_mix
  must hold at every target. A violation of J ≤ C_mix would mean J is not optimal over the
  mixture class, and is reported as a solver anomaly.

## Cells

- T = 9, B = 3, d = 1, transition 1/20, emissions (1/50, 49/50), cq = 1/100, cs = 1/20.
- prior1 in {1/10, 1/5, 3/10}.
- Target alphas are all A1c P1/P2 alphas.
- That is 93 calendars × 14 levels × 3 priors, about 3,900 calendar solves.
- At most 2 workers, with a 2-hour cap.

## Decision rule

| Outcome | Condition | Consequence |
|---|---|---|
| CONVEXIFICATION EXPLAINS | g_mix(alpha) ≤ g_mix(1) + 0.005 at every prior1 and target alpha < 1 | The A1c H-risk excess is an artifact of non-convex pure calendars. Lane A is closed: no risk-specific information-matched separation was found. |
| H-risk SURVIVES | Some g_mix(alpha) ≥ g_mix(1) + 0.005 | Proceed to an A2 theory attempt with the mixture comparator as the separable baseline. A method claim still needs the 10% threshold. |

Also reported: the full g_mix tables, the fraction of the A1c gap removed at each cell
`(g − g_mix)/g`, and the envelope's supporting (calendar, level) pairs.
