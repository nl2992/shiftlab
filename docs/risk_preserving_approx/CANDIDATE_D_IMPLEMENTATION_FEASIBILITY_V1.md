# Candidate D HSVI implementation feasibility

**Date:** 2026-10-29. **Status:** a relevant external implementation is available;
strategy extraction and exact certification are not yet integrated. No ShiftLab
efficacy run has been performed.

## Pinned implementation

Inspected the public MIT-licensed Julia project
[`brozjak2/HSVIforOSPOSGs.jl`](https://github.com/brozjak2/HSVIforOSPOSGs.jl)
at commit `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d` (checkout in the ignored
branch-local cache `.aris/runs/hsvi-osposg-upstream`). It is an unofficial
implementation of the 2017 OS-POSG HSVI algorithm and cites the extended 2023
Horák et al. paper. Its finite `.osposg` model supports state partitions,
player-specific actions, observations, probabilistic transitions, rewards and
an initial belief, so the finite microstage game has a plausible input route.

The package's `solve` returns a `Recorder` containing lower/upper values, gaps,
timings, value-vector counts and exploration depths. The stage LP routines
compute local player strategies, but the solve loop uses them for exploration;
there is no extracted learner controller or implementation of the 2023
gadget-based strategy-extraction Algorithms 5/6 in the public interface. A
value-gap result alone cannot supply the two exact-risk-bracketing policies
required by Candidate D. A faithful adapter must implement and retain that
strategy gadget, enumerate the resulting finite-horizon controller for
independent evaluation, and include extraction and verification costs.

## Environment and validation status

Julia was absent from `PATH`. Julia 1.13.3 was installed per-user, and the
upstream project declares compatibility with Julia 1.8. Its complete
`Pkg.instantiate(); Pkg.test()` suite finished with 53 passed and 1 failed. The
failure is the upstream `solve` test: on its 143-state, 21-partition,
2,671-transition pursuit-evasion game, the 60-second call returned a value width
of `33.75048`, failing the test's required width `< 1.0`; the independent
reference-value containment assertion passed. This is a timeout/convergence
failure in the default GLPK configuration on this host, not evidence that all
model sizes fail. Do not claim this package is validated or rely on its default
stopping result as an epsilon certificate. The checkout remains unchanged;
Julia packages are installed in the user depot, outside the tracked worktree.

## Decision

The point-based solver and finite state model make an empirical state/belief
search advantage plausible, but the failed default convergence test weakens that
case. Retain at most one tightly bounded pilot as an established-algorithm
baseline. This is not a novelty result. Before a ShiftLab pilot, implement the
paper's strategy extraction in a branch-local adapter, test it on an
independently solvable toy OS-POSG, and preregister the exact ShiftLab
comparison. Stop if the extracted learner strategy cannot be independently
evaluated under all causal-null histories or if full-game state construction
itself approaches the decomposed oracle's tree.

Any eventual comparison must include solve, controller extraction, multiplier
search, exact rationalized risk verification, alternative cost/continuation
verification, and root-mixture recovery. The existing exact decomposed solver
and Candidate B remain the central comparators; the generic sequence-form oracle
is required where it completes. No real data, reserved holdouts, new seeds or
confirmation set is in scope before G1–G3 pass.
