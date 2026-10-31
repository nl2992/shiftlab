# A3 registered protocol: certify calendar optimality at tight risk, and test B = 4

Registered 2026-10-31 after `2866b06`, before execution. This is a theory-verification and
development probe; it makes no method claim.

## Purpose

Theorem 7 and Proposition 6 in `13_A2_BRANCH_CONFLICT_THEORY.md` give sufficient conditions
under which a fixed calendar is exactly optimal. A3 checks those conditions on the actual
optimal joint policies at the programme's risk levels. It also asks whether a budget of B = 4
breaks the A2 pattern, since with one extra query a confirmation burst and a re-check might
both fit.

## Cells

The model families are the 54 used in A2: accuracy {9/10, 19/20, 49/50} × transition
{1/20, 1/10, 1/5} × prior1 {1/20, 1/10, 1/5} × cs {1/20, 1/5}. All runs use T = 8, d = 1,
cq = 1/100, solver `2bd2e8e`, and max_nodes 200,000.

- **Part 1 (B = 3):** alpha ∈ {1/20, 1/10}, 108 cells. This re-solves the joint planner only.
  The A2 gap is already known to be 0 here.
- **Part 2 (B = 4):** alpha ∈ {1/20, 1/10, 1}, 162 cells.

## Measurements per cell

Each cell solves the joint planner, recovers its behaviour policy, and enumerates every history
reachable under that policy exactly. The enumeration follows the method of A1c P5. Every label
sequence is reachable because both emission probabilities lie strictly between 0 and 1. The
following are recorded:

1. **Query support.** `Q(pi*)` and its size.
2. **Condition (P).** Promotion occurs with positive probability only on histories with B
   released labels, all of them positive.
3. **Condition (P').** There is no promotion on any history that contains a released 0 label
   before the promotion, and no query is issued after a promotion.
4. **Chain timing.** Whether the query times along the all-positive released history are
   deterministic.

How the certificates follow from these:

- Proposition 6 certifies `C* = J` when `|Q(pi*)| <= B`.
- Theorem 7 certifies `C_mix = J` when (P) holds. It certifies `C* = J` when (P) holds and the
  chain timing is deterministic.

A cell is called *uncertified* when neither Proposition 6 nor Theorem 7 applies. For every
uncertified cell, the best pure calendar C* is computed by full calendar enumeration, using
`a1_exact_separation.solve_cell`, and the gap g is reported.

## Caps and failures

- Workers: at most 2.
- Wall-clock: 3 hours for Part 1 and Part 2 together. Cells not finished within the cap are
  reported as not run.
- Failures: a cell that fails (node cap, LP time limit, or memory) is recorded as failed and is
  not retried with altered settings.

## Decision rules

### Part 1, B = 3

| Outcome | Condition |
|---|---|
| THEOREM EXPLAINS | Every completed tight cell is certified. The share certified by Theorem 7, by Proposition 6, and by neither is reported separately. |
| PARTIAL | Some tight cells are uncertified. Their structure is reported: support size and where promotion occurs. |

### Part 2, B = 4

| Outcome | Condition | Consequence |
|---|---|---|
| CALENDAR-OPTIMAL AT B=4 | g = 0 in every completed tight cell, whether by certificate or by computation | — |
| GAP AT B=4 | Some tight cell has g > 0 | A mixture check is required before interpretation. It must be registered separately. |

Part 2 also reports the alpha = 1 gaps (largest and count) as the unconstrained reference.
