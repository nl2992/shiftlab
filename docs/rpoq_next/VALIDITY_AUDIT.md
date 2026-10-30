# Validity audit

## Theory (what is and is not established)
- **Inherited validity (CONDITIONAL).** For any predictable propensity and bet, with `|λX| ≤ 1/2` and the stated conditional null `E[Y|G_t] ≤ 0`, the wealth is a nonnegative supermartingale (`docs/delayed_event_prefix_validity.md`). The growth allocator is predictable (it uses burn-in or pre-test estimates) so it inherits this. No new validity result was proved.
- **Not covered:** using the current event's delay to choose `q`; selectively dropping pending labels; a null that omits information used by the policy.

## Simulation checks actually run
| Check (from the mission list) | Status |
|---|---|
| IID null | Done: null crossing ≤ 0.031 in A2/A2b, ≤ 0.029 in A3 (all arms); unit test with a looser bound |
| History-adaptive conditional null | Partly: allocation depends on burn-in data; no adversarially history-dependent null tested |
| Fixed delays | Done (`d = 20`) |
| Random outcome-independent delays | **Not done** |
| Informative delays | **Not done** |
| Budget exhaustion | Done: spend ≤ 400 for every arm; unit tests |
| Missing / unresolved labels | Not done beyond the prefix mechanism |
| Strongly dependent / nonstationary alternatives | Nonstationary done (`het_onset`, `het_flip`); strong dependence **not done** |
| Proxy misspecification | **Not done** (a stale proxy appears in `het_flip` only) |
| Propensity clipping | Partly: `q_min` floor; no sweep |

## CRSP pipeline audit (mission §7)
| Item | Finding |
|---|---|
| Same-date `vwretd` in the reference action | The decision uses the close-date market return and trades the next close-to-close return. Executable only with at-close orders; slightly optimistic and not a point-in-time contract. Imposed convention |
| Point-in-time features | Panel features are same-date; no publication timestamps. Retrospective only |
| Predictable propensities | Yes for S6–R1: propensities are static functions of pre-test estimates or bins. The oracle rule is not predictable by design |
| IPW propensity matches the mechanism | Yes: `X` uses the same `q` as the query draw. Inactive (post-cap) events contribute `X = 0` and are excluded from statistics |
| Budget exhaustion and truncation | The cap is enforced causally per date. Realized spend differs by arm (R1: growth about 7–8% below uniform; the placebo at 20% far below), so label budgets are **not exactly matched** |
| Bet constraints use information at the right time | Per-event cap uses the event's own `q`; moments come from dates before the current date. Labels for date `d−1` are treated as available at the start of date `d`, which is the next-date convention; the next-day return actually realizes at the close of `d` (borderline) |
| Multiple rows per date | Processed jointly with common moments. Cross-sectional dependence means the per-event conditional null is not established; crossings are descriptive |
| **Uncertainty estimates** | Cohort-cluster bootstrap treats the 10 cohorts as independent, but they share dates and market shocks. **The intervals are anti-conservative.** The negative R1/S6 results are large relative to their intervals, but exact coverage is unknown. A date-block bootstrap needs per-date contributions that were not saved |
| Oracle allocation | A hindsight diagnostic that reads outcomes. Not a reachable ceiling and not a valid upper bound |

No substantive defect was found that changes a historical result's sign; the interval issue and the unmatched spend are documented caveats. The historical CRSP outputs were not modified.
