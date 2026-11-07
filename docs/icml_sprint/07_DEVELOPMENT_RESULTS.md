# 07. Development results

## Tolerance-aligned cost null (`scripts/sota_search/g5_tol_aligned.py`; fresh development seeds 140000+, 400 seeds per cell, 8 conditions × 3 shifts = 24 cells; `outputs/icml_sprint/g5_tol_aligned.csv`)
Null: E[cost increase] ≤ ε = 0.10, the same threshold used to call a cell harmful. Cells: harm > ε (14, null false), 0 < harm ≤ ε (null true but cost rises; 4 cells), harm ≤ 0 (null true; 6 cells). Only the five cost-null e-processes were run; the Brier-null methods (HG, Brier ONS) have no matching tolerance and are **not** compared here.
**Implementation defect, recorded.** The first run (`g5_tol_aligned_run1_guidance_tol_coupled.csv`) passed the cost tolerance to the Brier *guidance* statistic as well, which zeroed H2c's bet; H2c then appeared worse than the cost-only methods (power .024 / .047). That was a bug in `pp_cost_guided` (not a finding). The guidance statistic now always uses tolerance 0 (behaviour is unchanged when tol = 0, so all earlier results are unaffected). The numbers below are from the corrected run.
| labels | class | C0 cost parent | C1 cost disc. | C2 cost ONS | C3 guided ONS | **C4 H2c** |
|---|---|---|---|---|---|---|
| 10% | power, harm > ε | .021 | .067 | .074 | .064 | **.136** |
| 10% | alarm rate, 0 < harm ≤ ε | 0 | .001 | .002 | .005 | .006 |
| 10% | alarm rate, harm ≤ 0 | 0 | 0 | 0 | 0 | 0 |
| 20% | power, harm > ε | .063 | .185 | .134 | .079 | **.256** |
| 20% | alarm rate, 0 < harm ≤ ε | .001 | .002 | .001 | .001 | .006 |
| 20% | alarm rate, harm ≤ 0 | 0 | 0 | 0 | 0 | 0 |
Pre-shift alarm rate (all 24 cells, null true): ≤ .001 for every method. H2c is ahead of cost-only discounted Kelly and of cost-only ONS in **14 of 14** harm cells at both label rates (mean +0.069 / +0.071 over C1 and +0.062 / +0.122 over C2 at 10% / 20% labels).
**Reading.** (1) The within-class advantage survives the correct economic null; the sign of the earlier conclusion is not an artefact of the zero-tolerance labelling. (2) Absolute power is small because most harm cells sit only 0.01–0.27 above ε; the test is very conservative (empirical size ≈ 0.00–0.006 against α = 0.05). (3) The "decision-aware advantage over Brier-null methods" is **untested**: a matched-tolerance Brier comparator does not exist and was not built. (4) One bug was found in the process; the tests (15) cover the identity cases but not this tolerance coupling.
