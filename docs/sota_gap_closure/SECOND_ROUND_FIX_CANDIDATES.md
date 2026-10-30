# Second-round fix candidates (preregistered before running `scripts/gap/e14_fixes.py`)

Selected from the observed failure matrix (`UPDATED_FAILURE_MATRIX.md`, `CROSS_METHOD_WEAKNESS_CLUSTERS.md`). Each fix is applied to at least two parents
(`pprm`, `HG`, and the decision-cost e-process `cost`) and tested on **new development worlds** (seed block 80000+, parameters different from every earlier pool).

| fix | targeted failure | mechanism | parents | validity status |
|---|---|---|---|---|
| F1 floored allocation | cap-floor penalty of non-uniform querying (S04/S05/S06: growth/variance/pacing lose 0.1-0.2 power vs uniform) | variance allocation with propensity floor q >= frac/2 so the predictable bound is only 2x worse than uniform | pprm, HG, cost | valid (predictable floor, x-free cap); identical to S05 conservative mixtures when the floor is 0.5 |
| F2 long-run-variance bet | false alarms under clustered / autocorrelated / GARCH dependence (HG 0.19 at cluster-400, 0.09 on the G4 null) | Kelly denominator uses a Bartlett long-run-variance estimate of the arrived increments (100 lags) | pprm, HG, cost | **heuristic**: no anytime-validity proof under dependence; empirical size only |
| F3 multi-window mixture | transient / recurrent harm (HG power 0.34-0.62 at 20% labels) | equal-weight average of three e-processes with bet discount 1, 0.99, 0.95 sharing one query matrix | pprm, HG, cost | valid (average of test supermartingales) |

## Acceptance rules (declared now)
* **F1**: mean power gain over the uniform parent >= +0.03 on the new iid harm worlds for >= 2 of 3 parents, non-harm false alarm change <= +0.02, no null-world false alarm > 0.07.
* **F2**: on the new dependence null worlds the maximum false-alarm rate falls to <= 0.07 (Wilson upper bound <= 0.09) for >= 2 of 3 parents, while mean power on the iid harm worlds loses <= 0.05.
* **F3**: mean power gain >= +0.05 on the transient/recurrent worlds for >= 2 of 3 parents with non-harm false alarm change <= +0.02.
A fix is reported as "improves multiple parents" only if its rule is met on >= 2 parents. Fixes failing the rule stay in the registry. Selection is on development seeds only; survivors are frozen for `FINAL_SYNTHETIC_CONFIRMATION_PROTOCOL.md`.
