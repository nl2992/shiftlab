# Registered sensitivity screen: episode composition across recurrent HMM cells

**Registered:** 2026-10-28 before execution. This is comparator development, not a new-method efficacy or confirmation study.

Keep the information/risk/economic contract from `switching_episode_composition_comparator_v1.md` fixed: T=6, B=3 pathwise, d=2, alpha=1/10, c=1/100, k=1/10, prior P(S0=1)=1/2, paired losses (Y,1-Y), same action/query clock, and the global causal conditional null. Compare the best over all fixed calendar subsets of the four eligible events and the three frozen episode alpha allocations (geometric, equal over B+1, frontloaded). Evaluate the same per-cell unrestricted causal-game LP, without monotonicity constraints. Do not alter action thresholds, controller, alpha allocations, query calendars, horizon, budget or fees after looking at results.

Predeclared HMM cells are the Cartesian product of symmetric transition rates {1/10,1/4,9/20} and emission pairs {(1/10,9/10),(1/50,49/50)}. These span more persistent through nearly uninformative transitions and moderate through strong observation signals. Every method uses the same known cell model for expected utility and forecast-driven action/rollback decisions; the episode test's conditional-null proof does not use that model. Exact causal-null risk and expected cost are evaluated for every candidate schedule. The best calendar is selected using the known model, so it is a model-aware development comparator, not a blind deployed baseline.

Report per cell: best schedule/spending rule, exact cost, worst null risk, expected queries, recovered oracle-policy cost/risk, and their cost difference. The oracle is a numerical LP reference without a rational dual certificate; do not call the difference a certified approximation error. A zero-promotion or no-query solution is retained as a valid result. All cells are run once; no replacements, tuning, Monte Carlo, inference claims or real-data evaluation are in scope.

Reproduction command: `PYTHONPATH=src python scripts/screen_switching_episode_composition_grid.py`. The run saves all cell outputs, per-cell source hashes and configuration to `outputs/switching_episode_composition_grid_v1/results.json`.
## Registered sensitivity-screen result

The six predeclared cells completed. For transition/emissions, the best fixed-calendar episode composition, its cost/risk, and its cost minus the recovered LP-policy cost were:

| Transition | Emissions | Best calendar | Composition cost | Null risk | Difference from recovered LP policy |
|---:|---:|---:|---:|---:|---:|
| 1/10 | 1/10, 9/10 | (1,3) | 2.88176704 | 1/10 | 0.055076096 |
| 1/10 | 1/50, 49/50 | (1,3,4) | 2.819679568 | 1/10 | 0.106362208 |
| 1/4 | 1/10, 9/10 | (1,3) | 2.9782 | 1/10 | 0 |
| 1/4 | 1/50, 49/50 | (1,3,4) | 2.959836896 | 1/10 | 0.00414352 |
| 9/20 | 1/10, 9/10 | empty | 3.0 | 0 | 0 |
| 9/20 | 1/50, 49/50 | empty | 3.0 | 0 | 0 |

The selected spending rule was frontloaded in the first four cells and geometric in the two no-switch cells. Every schedule/spending candidate passed exact worst causal-null risk and pathwise calendar-cap checks. The largest comparator gaps occur for the more persistent regimes; the intermediate-emission persistent cell is matched exactly by the simple composition. In the near-memoryless cells, the best fixed-calendar rule does not switch. These are development-model results, not evidence of a generally exploitable acquisition gap. The reference policy is recovered from a floating-point LP without a rational dual certificate, and best calendars are model-aware. Results and hashes: `outputs/switching_episode_composition_grid_v1/results.json`.

Reproduction and targeted validation passed: `PYTHONPATH=src python scripts/screen_switching_episode_composition_grid.py`; Ruff passed on the new comparison scripts and causal-game code; the causal-game targeted suite passed 12 tests; `git diff --check` passed. This does not satisfy G1: no candidate method or theorem has been selected. G2-G5 remain open.

### Predeclared decomposition follow-up (before execution)

For the same six HMM cells and fixed contract above, compare three layers: (i) unrestricted causal-game LP; (ii) the best causal-game LP over all 15 fixed opportunity calendars, where the learner may still adaptively skip each opportunity and jointly optimize queries/actions/randomization subject to the same robust risk; and (iii) the best episode composition already reported. This is a mechanism-attribution diagnostic, not a new cell/grid. It isolates lost value from restricting query opportunities to a calendar (i vs. ii) from lost value of the simple episode test/controller within a calendar (ii vs. iii). Use calibrated recovered-policy cost/risk for the fixed-calendar LPs; record raw LP objective and any safety activation. No candidate algorithm, efficacy claim, or post-hoc calendar change follows.

### Decomposition result

The six-cell follow-up completed. In every cell, the best fixed query-opportunity calendar achieved exactly the same calibrated recovered-policy cost as the unrestricted query-timing planner (zero displayed difference in exact rational recovered costs). The best calendars were (1,2,3) in the four models with signal and the empty calendar in the two transition-9/20 models. Because the calendar planner could still skip opportunities, choose actions, and optimize randomized robust tests adaptively at those times, this comparison isolates the value of access to non-calendar query times; it does not remove all acquisition adaptivity.

Thus the episode composition's positive gap in persistent cells was entirely within-calendar policy/test class in this screen, not query-opportunity timing. The strongest two cells have small gaps; larger gaps are confined to transition-1/10 models and the simpler episode policy. This pivots the next theorem target away from adaptive timing alone and toward robust sequential test/action compression under recurrent regimes. That area has substantial prior work and must pass a fresh source-level theorem comparison. The zero differences are numerical recovered-policy comparisons, not exact optimal-value equalities: HiGHS returned no rational dual certificate, and a recovered feasible cost is not a lower bound. Do not claim query timing is generally unnecessary.
