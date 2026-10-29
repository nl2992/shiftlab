# Capped planner against stronger calendar-opportunity baseline

2026-10-29. **Result:** the m=2 capped planner does not beat the stronger
calendar-opportunity baseline in any of the six previously exposed HMM cells.
The calendar planner has lower expected cost in three cells and ties in three.
This qualifies the earlier improvement over the simpler episode composition.

The precommitted `CAP_CALENDAR_PROTOCOL_V1.md` compares the original unrestricted
first-promotion oracle, m=2 cap with total B=3, and all 15 fixed sets of query
opportunities. The existing calendar planner may skip opportunities adaptively,
optimize randomized promotion and rollback and use the same HMM, delayed labels,
pathwise budget and causal-null constraint. The best calendar is selected for each
known model, as in the prior registered study. This is a strong model-aware
comparator, not an independent frozen deployed algorithm.

| Transition | Emissions | Best calendar | Calendar cost | Cap cost | Calendar minus cap |
|---:|---:|---|---:|---:|---:|
| 1/10 | 1/10, 9/10 | 1,2,3 | 2.826690944 | 2.84322368 | -0.016532736 |
| 1/10 | 1/50, 49/50 | 1,2,3 | 2.71331736 | 2.766322099 | -0.053004739 |
| 1/4 | 1/10, 9/10 | 1,3 | 2.9782 | 2.9782 | 0 |
| 1/4 | 1/50, 49/50 | 1,2,3 | 2.955693376 | 2.958624 | -0.002930624 |
| 9/20 | 1/10, 9/10 | empty | 3 | 3 | 0 |
| 9/20 | 1/50, 49/50 | empty | 3 | 3 | 0 |

All six cells and 90 calendar solves completed. The best calendar recovered
cost matched the full decomposed recovered cost in each cell. Each selected
policy's worst causal-null risk was evaluated exactly and any needed safe root
activation applied. Full exact fractions, 15 individual calendars per cell,
model parameters, risks, timings and source hashes are in
`cap_calendar_synthetic_v1.json`. The LP solutions are numerical and no exact
class-optimal dual certificates are supplied, so the result compares recovered
feasible policies; it is not a general dominance theorem. The present table's
rounded values are supported by the exact saved fractions.

`uv run --no-sync pytest tests/test_prepromotion_cap.py
 tests/test_causal_switching_game.py -q`: 17 passed. The calendar and capped
policies use existing model/risk evaluation code, not an independent implementation.
The calendar baseline optimizes full actions in the same model and may have a
higher computational cost; per-solve timings are recorded, but no repeated
end-to-end performance comparison against this full baseline was registered.
The cap's previously measured speed relative to the unrestricted decomposition
remains a separate computational observation.

**Decision:** do not claim a synthetic economic win against the articulated strong
baselines. The cap's three wins against the simpler episode composition are real
for those exact evaluated policies but do not survive this stronger comparator.
Retain the cap as a computational baseline and continue the original research
objective. Do not open reserved holdouts or describe real-data performance as
established. No new seeds or real-data rows were used here.
