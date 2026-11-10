# A3 / A4: fair factorial runtime ablation and the T=10, d=1 anti-persistent cell

**Registered:** 2026-11-10, before any harness code or runs. Synthetic only.

## Configurations (A3)

| id | Method |
|---|---|
| R0 | Exact decomposed reference, `FirstPromotionDecomposedGame.solve()`, unmodified |
| R1 | R0 + belief cache (memoise `_belief_from_history` by learner information; additive subclass, original untouched) |
| R2 | R1 + the same numeric representation FCG-fast uses, where mathematically legitimate. The builder documents exactly which quantities are float vs Fraction in FCG-fast and matches them |
| I0 | Learner-only IID relaxation (FCG-fast iteration 0) + exact causal verification + realization-space repair; stops after iteration 0 |
| F0 | FCG-fast as committed (`src/shiftlab/paper4/frontier_cuts_fast.py`) |
| F1 | F0 on cells where non-IID cuts are actually generated (reported separately; identical code) |

## Cells

| id | T | B | d | transition | emissions | role |
|---|---|---|---|---|---|---|
| C6 | 8 | 3 | 1 | 3/4 | (1/20, 19/20) | cuts fire (21) |
| S1 | 10 | 4 | 2 | 1/10 | (1/50, 49/50) | persistent; 0 cuts |
| T10D1 | 10 | 3 | 1 | 3/4 | (1/20, 19/20) | **A4 new cell**: anti-persistent, d=1, B=3, matched to C6 except T |

Prior 1/2, alpha 1/10, query fee 1/100, switch fee 1/10 throughout.

## Measurement

- One method, one cell, one repetition per **fresh process**.
- Recorded: learner-tree build, belief computation, LP, separation, exact certificate, policy recovery, total wall
  time, child peak RSS, learner and null histories, cuts, iterations, U and L.
- **Repetitions:** 5 per (method, cell), interleaved round-robin, on a quiet CPU. The lead runs this campaign only
  when no other agent is computing.
- **Summary:** median and min–max; paired ratios per repetition index.
- **Warm vs cold:** every run is cold (fresh process). No warm runs are reported.

## A4 feasibility (exploratory, before the campaign)

Run R0 and F0 once on T10D1 and record nodes, time, RSS and cuts. If R0 exceeds 200,000 nodes or 20 minutes, record
the bottleneck and use T=9, d=1 as the intermediate cell.

## Decision rules

- **Engineering improvement:** F0 or I0 median faster than R0 in every repetition pair.
- **Attributable improvement:** the gain survives against R1 and R2 (matched caching and numerics).
- **Attributable to cut generation:** F1 beats R2 on a cell with cuts.
- Otherwise record no meaningful advantage.
