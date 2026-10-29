# Capped planner versus episode composition: synthetic development results

2026-10-29. **Result:** the m=2 capped planner has lower expected cost than the
best screened episode-composition policy in three of six previously exposed
known-HMM cells, and ties it in three. This is model-based development evidence,
not independent confirmation or an established methodological contribution.

The protocol `CAP_EPISODE_SYNTHETIC_PROTOCOL_V1.md` was committed before the
run. All six registered cells completed; each compares the full decomposed oracle,
the m=2 capped planner with total B=3, and the best of 15 fixed calendars times
three episode spending rules. The baseline is selected using the known model and
is the existing repository composition, not a faithful implementation of every
published robust-FSC or sequential-test competitor. The baseline values reproduce
all six values in `switching_episode_composition_grid_protocol_v1.md`. No random
seeds or real-data rows were used.

| Transition | Emission pair | Full recovered cost | Capped cost | Best episode cost | Episode minus cap | Cap minus full |
|---:|---:|---:|---:|---:|---:|---:|
| 1/10 | 1/10, 9/10 | 2.82669094 | 2.84322368 | 2.88176704 | 0.03854336 | 0.016532736 |
| 1/10 | 1/50, 49/50 | 2.71331736 | 2.76632210 | 2.819679568 | 0.053357468 | 0.053004739 |
| 1/4 | 1/10, 9/10 | 2.9782 | 2.9782 | 2.9782 | 0 | 0 |
| 1/4 | 1/50, 49/50 | 2.955693376 | 2.958624 | 2.959836896 | 0.001212896 | 0.002930624 |
| 9/20 | 1/10, 9/10 | 3 | 3 | 3 | 0 | 0 |
| 9/20 | 1/50, 49/50 | 3 | 3 | 3 | 0 | 0 |

Costs and differences are exact rational evaluations of recovered policies,
shown rounded in the table; raw fractions, risk, activation, timings, model and
source hashes are in `cap_episode_synthetic_v1.json`. All capped policies had
exact causal-null risk <=1/10; it was 1/10 in the first four cells and zero in
the last two. The baseline likewise passed exact causal-null checks. Its fixed
calendar has at most three requests. The full and capped LPs are numerically
optimized; these differences are between feasible recovered policies, not
certified optimality gaps. The full reference used 1,799 builder nodes per cell;
the cap used 574. These counts do not establish an end-to-end performance rate.

Validation: `uv run --no-sync pytest tests/test_prepromotion_cap.py
 tests/test_first_promotion_decomposition.py tests/test_causal_switching_game.py
 -q`: 20 passed. Existing baseline choices were evaluated by the same reference
forward and risk recursions used historically, so this is not an independently
implemented model check. The best calendar was selected on the same model used
for evaluation, and the six cells had already been inspected in prior work.

The outcome supports further research: in these cells the capped planner trades
some optimal-model utility for a smaller robust game while still outperforming
this episode composition in three cases. It does not establish the user's full
objective: source-matched strongest competitors, a useful general value bound,
new synthetic confirmation and a valid real-data comparison remain open. The
prior audit limits the pulled CRSP panel to retrospective predictive-loss
development with assumed clocks and costs; it must not be represented as a
prospective trading or untouched confirmation study.
