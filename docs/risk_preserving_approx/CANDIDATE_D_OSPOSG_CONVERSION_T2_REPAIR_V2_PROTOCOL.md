# Candidate D T=2 compiler repair diagnostic v2

**Registered:** 2026-10-29, after preserving v1's failure. This is a diagnostic
revision, not a retroactive pass of v1 and not an efficacy test.

## Fixed model

Retain all v1 values: `T=2`, `B=1`, delay `1`, `alpha=1/10`, query cost
`1/100`, switch cost `1/10`, default HMM, multiplier `lambda=1`, discount
`gamma=0.9`. Keep the same independent scalarized sequence-form LP identity and
the original acceptance criteria: an optimal LP, HSVI root interval containing
the LP value, width at most `1e-4`, within the registered 30-second solver
limit.

## Sole converter change under test

Emit explicit reward entries, including numeric zero, for every state, legal
learner action in its information partition, and legal opponent action at that
state. Before HSVI, run an independent structural validator requiring:

- every legal `(state, player-1 action, player-2 action)` has a reward entry;
- every such triple has outgoing transitions summing to one within `1e-12`;
- each `(partition, player-1 action, observation)` maps to one target partition;
- root belief is normalized and supported on the declared initial partition.

Write all v2 artifacts into the fresh ignored directory
`.aris/runs/candidate_d_osposg_conversion_t2_repair_v2/`. Record source and
model hashes before solving. If structural validation fails, stop without
calling HSVI. If it passes, call the pinned Julia solver once using the v1
solver tolerances and time limit; preserve complete logs and exit status. Do not
change the model, acceptance threshold, time limit or solver settings after
seeing the output.

This check does not authorize T=6, a ShiftLab efficacy pilot, risk/cost policy
claims, a baseline superiority claim, real data, holdouts or confirmation seeds.
