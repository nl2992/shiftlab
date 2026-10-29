# IID relaxation stress screen at T=10

Registered 2026-10-29 before execution. This is a single deterministic synthetic
stress instance for the existing Candidate B relaxation / exact-certification
pipeline. It does not allocate seeds or access real rows, CRSP or holdouts.

## Frozen instance and limits

- `T=10`, `B=4`, delay `d=2`, `alpha=1/10`.
- Query fee `1/100`, switching fee `1/10`.
- Symmetric HMM transition `1/10`, emissions `(1/50,49/50)`, prior `1/2`.
- Candidate IID LP: one IID fair-label first-promotion risk constraint; 60-second
  solver limit, HiGHS feasibility tolerances `1e-9`; learner tree limited to
  200,000 builder nodes.
- Robust decomposed reference: same parameters, 200,000 builder-node limit and
  solver limit inherited from the implementation (60 seconds).
- Fixed-calendar baseline: exact robust planner for every schedule of at most
  four queries among the feedback-useful slots `{1,...,8}` (163 schedules),
  with exact root safety calibration and the same alternative continuation.

## Measurements and verification

Record exact candidate cost, IID risk, independent full causal-null risk, exact
rational dual lower bound, certified value gap, repair activation, per-path query
cap, builder nodes, LP sizes, solve and end-to-end times, and process RSS deltas.
Record reference success/failure and resources. Exhaustively evaluate and retain
all calendar outcomes, select the least exact calibrated cost, and compare it with
the candidate. Independently recompute the candidate's alternative metrics and
full causal-null risk. Require lower bound `<=` feasible candidate cost and exact
risk `<= alpha` before calling its interval certified.

This screen is useful if the certified feasible candidate beats the best calendar
and its certified interval is narrow relative to that economic gain. Report
computational advantage only if comparable end-to-end measurements support it;
an omitted opponent tree or lower node count alone is insufficient. A failed LP,
node cap, wide interval, or non-winning policy is a preserved negative result.
No novelty, multi-instance theorem, synthetic efficacy gate or real-data gate is
claimed by this one instance. The procedure is a standard relaxation / exact
verification / safety-repair pattern pending any stronger source-matched result.
