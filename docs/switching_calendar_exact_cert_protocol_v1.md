# Exact certificate follow-up: fixed-calendar timing comparison

**Registered:** 2026-10-29, before the certification run. This upgrades only the numerical
mechanism-attribution comparison already frozen in
`switching_episode_composition_grid_protocol_v1.md`; it adds no cells, parameter values, policy
class changes, or efficacy endpoint.

## Question

The registered six-cell screen reports that the best robust planner restricted to a fixed query
opportunity calendar (1,2,3) has the same recovered cost as the unrestricted causal-game planner.
Those are feasible policy evaluations from floating-point LPs, not certified equality of optimal
values. Can we certify, in each cell, that a pathwise-budgeted fixed-calendar policy attains the
full unrestricted optimum to a stated rational tolerance?

## Frozen design

Retain `T=6`, `B=3`, fixed delay `d=2`, `alpha=1/10`, query fee `1/100`, switch fee `1/10`, prior
`P(S_1=1)=1/2`, and the six symmetric HMMs from the registered grid:

- transition rates `{1/10, 1/4, 9/20}`;
- emission pairs `{(1/10,9/10), (1/50,49/50)}`.

For each cell, (i) rebuild the unrestricted sequence-form LP with exact rational alternative
cost coefficients, (ii) use an LP solver only to propose a dual vector, (iii) rationalize and
verify every dual constraint with exact arithmetic, including a residual correction for
nonnegative learner realization variables, and (iv) independently evaluate the feasible policy
returned by the restricted calendar `(1,2,3)` robust planner. A certificate establishes equality
only when the feasible restricted-calendar upper cost lies within the verified unrestricted lower
bound plus the reported rational gap. The full unrestricted optimum is a lower bound on every
restricted policy class.

Stop and report any failed cell, nonzero separation, solver failure, or certificate gap above
`1e-8`. Do not change model cells, calendars, tolerances, or the exact alternative objective after
seeing results. This is an optimality/reference check; it does not test a new method, establish a
general calendar theorem, or open G2-G5.

## Verification and scope

Save rational dual vectors, exact residuals, feasible-policy costs/risks, source hashes and
reproduction commands under `outputs/switching_calendar_exact_cert_v1/results.json`. Provide a
second verifier that checks the saved certificates without invoking an optimizer. The output is
valid only for these six finite instances. A match would sharpen the attribution baseline and
motivate a separate growing-family theorem; it is not itself a novelty result or an efficacy
comparison.

## Executed result

The six-cell run completed. The restricted calendar planner uses only query opportunities
`(1,2,3)` and its recovered policy records were independently re-evaluated by exact forward
recursion for alternative cost and full causal-null risk. For each full unrestricted LP, the
optimizer supplied only a candidate dual; the checker reconstructs an exact opponent realization
plan, verifies all free-column equalities and learner-column inequalities with rational
arithmetic, and subtracts a rational upper bound on residuals. The resulting brackets are:

| Transition | Emissions | Fixed-calendar feasible cost | Certified unrestricted-to-calendar gap |
|---:|---:|---:|---:|
| `1/10` | `(1/10,9/10)` | `22083523/7812500` | `1/40000000000` |
| `1/10` | `(1/50,49/50)` | `13248619923/4882812500` | `583763339/3790747500000000000` |
| `1/4` | `(1/10,9/10)` | `14891/5000` | `0` |
| `1/4` | `(1/50,49/50)` | `46182709/15625000` | `11/500000000000` |
| `9/20` | `(1/10,9/10)` | `3` | `17/1000000000000` |
| `9/20` | `(1/50,49/50)` | `3` | `43/1000000000000` |

Every bracket is below `1.6e-10`, well inside the frozen `1e-8` stop threshold; the third cell
matches exactly. The verifier command
`uv run python scripts/certify_switching_calendar_value.py --verify` passed on the saved vectors
without invoking an optimizer. The generating command is
`uv run python scripts/certify_switching_calendar_value.py`; it also writes source hashes and
policy records. Ruff and Git whitespace checks passed.

For these six finite models, event-time flexibility beyond calendar `(1,2,3)` cannot improve
cost by more than the certified gaps under the same full causal-null risk constraint. This does
not show that calendar timing is irrelevant in general, that the restricted planner is
computationally efficient, or that it is a new algorithm. It sharpens the next search target:
remaining gains in this setup lie within the fixed-calendar test/action policy class, which still
needs a source-level comparison to sequential test design and robust constrained planning.
