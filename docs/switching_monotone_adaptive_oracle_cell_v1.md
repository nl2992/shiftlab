# Monotone first-promotion policy matches the certified adaptive oracle cell

**Date:** 2026-10-28. **Status:** exact feasible-policy match to a certified value bracket; no novelty claim.

## Registered cell and comparison

Use the existing delayed reversal contract: `T=6`, pathwise query cap `B=3`, label delay `d=1`, false-promotion level `alpha=1/10`, query fee `1/100`, switch fee `1/10`, symmetric HMM transition rates `1/4`, emissions `(1/20,19/20)`, and prior good-state probability `1/2`. Compare the full causal sequence-form planner with the same planner plus coordinatewise monotonicity constraints on the first-promotion probability over potential label tapes. Both planners retain adaptive acquisition, rollback, the same causal conditional null and the same economic objective.

The unrestricted oracle's exact rational certificate gives

```text
576353749991/200000000000 <= C* <= 461083/160000,
```

with bracket width `9/200000000000 = 4.5e-11`. The monotone-constrained LP recovered the same feasible policy and exact cost as the certified unrestricted upper policy: `461083/160000`. Its exact causal-null promotion risk is `1/10`; expected query count is `1481/2000`, expected switches `3129/16000`, and total cost `461083/160000`.

## Recovered policy

The recovered policy activates with probability `2/5`. On an active path it queries event 1, queries event 2 after the first label is positive, and first promotes at event 3 after two positive labels. While deployed, it queries event 4 and rolls back at event 5 if that maintenance label is negative. The unrestricted and monotone-constrained LPs return identical query and rollback decision tables. As a separate exact check on the recovered behavioral policies, promotion probabilities were recomputed for all 64 potential label tapes using rational arithmetic; both recovered events have probability `2/5` exactly when the first two labels are `11`, and zero otherwise. All cover-relation checks pass. The first-promotion event is therefore exactly the increasing event `Y1=Y2=1`; later rollback affects economic control but cannot change whether that first promotion occurred.

The monotone feasible cost equals the exact unrestricted upper endpoint, so the restricted optimum and unrestricted optimum both lie in the same certified interval. The monotonicity restriction's value loss on this cell is therefore at most `4.5e-11`; this follows from the unrestricted lower certificate and the monotone feasible policy, not from treating either HiGHS objective as an exact optimum.

Reproduce in PowerShell from the repository root with `$env:PYTHONPATH='src;.'; python scripts/compare_switching_monotone_adaptive_oracle.py`. The exact output, including query/rollback summaries, all 64 rational promotion probabilities, monotonicity checks and source hashes, is in `outputs/switching_monotone_adaptive_oracle_v1/results.json`.

## Interpretation

This is a stronger, same-contract continuation of the fixed-cohort screen: monotone promotion retains adaptive query decisions and a later rollback, and has a certified value loss of at most `4.5e-11` in the registered recurrent-HMM cell. It gives one precise structural witness, not a growing-family theorem. The policy was recovered by optimizing the same cell, and the model is known to both planners. It neither proves that all optimal policies admit monotone promotion events nor shows an advantage over established scalable sequential-design methods. It does not pass G1/G2, and G3/G4 remain gated.
