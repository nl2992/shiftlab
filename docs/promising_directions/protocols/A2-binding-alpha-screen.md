# A2 registered protocol: does the risk-specific timing gap exist at alpha in {0.05, 0.10}?

Registered 2026-10-30 after A1d (`f5f1d88`) and before execution. This is a development and
theory probe; it makes no method claim.

## Hypothesis

A1c P5 identified a branch-conflict mechanism. The risk constraint forces confirmation queries
in the branch where the first label is positive, and these collide with the delayed re-check
queries wanted in the negative branch. The union of the two branches' slot sets exceeds B, so
no fixed calendar serves both. A1c/A1d observed the effect only at alpha ≥ 3/20.

A2 asks whether model parameters exist for which the effect appears at the programme's declared
risk levels.

## A2a: screen (pure calendars)

Fixed settings:

- T = 8, B = 3, d = 1.
- cq = 1/100.
- Symmetric transitions.
- Emissions (1 − acc, acc).

Factors (54 families):

- acc in {9/10, 19/20, 49/50}
- transition in {1/20, 1/10, 1/5}
- prior1 in {1/20, 1/10, 1/5}
- cs in {1/20, 1/5}

Each family is solved at alpha in {1/20, 1/10, 1}, giving 162 cells. The runner is
`a1_exact_separation.solve_cell`, at solver `2bd2e8e` with max_nodes 200,000.

Screen statistic: `excess = g(alpha) − g(1)` for alpha in {1/20, 1/10}. Here g is the relative
gap between J and the best pure calendar.

Survivors are the families with excess ≥ 0.005 at either level. At most the top 3 by excess
are carried forward, with ties broken by larger g(alpha).

Caps: 2 workers and 1.5 hours.

## A2b: mixture check on survivors

For each survivor, at its surviving alpha level(s):

- Compute `C_c(a)` for every calendar c with at most B slots in 1..T−d, on the A1d grid
  `{0, 1/20, 1/10, 1/8, 3/20, 1/6, 9/50, 1/5, 1/4, 3/10, 2/5, 1/2, 3/4, 1}`.
- Form `C_mix` as the lower convex envelope of those values, exactly as in A1d.
- Evaluate `g_mix(alpha)` and `g_mix(1)`.

Caps: 2 workers and 1.5 hours.

## Decision rules

| Outcome | Condition |
|---|---|
| RISK SEPARATION AT PROGRAMME LEVELS | Some survivor has `g_mix(alpha) − g_mix(1) ≥ 0.005` at alpha in {1/20, 1/10}. |
| CONFINED TO LOOSE ALPHA | No survivor exists, or every survivor fails A2b. |

Also report g_mix(alpha) itself for each survivor, measured against the 10% practical
threshold.

## A2c: theory (written, no compute)

State and prove a branch-conflict lower bound on the calendar gap. Prove the mixture lemma that
carries a uniform per-calendar gap over to public-coin mixtures. Check both against the A1c P5
policies.

This step is a statement about a mechanism. It is not a growing-family theorem, and any part
that is not proved must be labelled conjecture.
