# 02. Claim verification (H2c lineage)
Replay performed from the frozen per-cell file `outputs/h2c_next/g5_confirmation_cells.csv` (the per-seed parquet could not be read here because `pyarrow` is not installed in this environment; cell means are sufficient for the checks below). Outputs: `outputs/icml_sprint/d1_replay.json`, `g5_estimand_split.csv`.

| claim | status | evidence |
|---|---|---|
| D1: H2c − better of (cost-only discounted, cost-only ONS) = +0.086 / +0.094 | **EMPIRICALLY_CONFIRMED (replayed)** | cell-only bootstrap (14 harm cells, 20000 resamples): +0.086 [0.061, 0.110], H2c ahead in 13/14 cells; +0.094 [0.065, 0.123], ahead in 14/14. Consistent with the published two-level interval; the claim is about this synthetic family only. |
| H2c e-process valid under the cost null (fixed or independent delay) | **PROVED_AND_CHECKED (target = zero-tolerance conditional null)** | bounded increments, predictable bet, uniform support cap; same argument as the restart proof and the exact finite-support test. |
| Cost-null false alarms low, "benign FA .036 / .067" | **INVALID_OR_COUNTEREXAMPLED as stated (estimand mismatch)** | see below |
| Brier-null methods "alarm on 16–33% of no-harm cells" | **INVALID as stated** | see below |
| Brier guidance causes the gain | **DEVELOPMENT_ONLY + EMPIRICALLY_CONFIRMED on G5** | ablation additive; no theorem. |
| Superiority over published methods | **UNVERIFIED** | no published comparator was reproduced. |
| Novelty | **UNVERIFIED** | see doc 03. |

## The estimand mismatch (new finding)
The tested H2c null is the zero-tolerance cost null E[cost_t | F_{t−1}] ≤ c0 (tol = 0). The generator labels a cell `benign` when the decision-cost increase is **below 0.10**, which includes cells where cost really did go **up**. Splitting the 18 benign/null cells of the frozen confirmation by the true sign of the harm:
| cell class (H2c) | 10% labels | 20% labels |
|---|---|---|
| true null holds (harm ≤ 0), 13 cells | alarm rate **.009** | **.012** |
| null false (0 < harm < 0.10), 5 cells | .066 | .131 |
For the other methods (alarm rate in harm ≤ 0 cells / in 0 < harm < 0.10 cells): HG (Brier) .008 / .313 (10%) and .014 / .538 (20%); Brier ONS .029 / .48 and .039 / .607; cost-SR (empirical) .043 / .133 and .043 / .204; cost-only discounted Kelly .013 / .045 and .019 / .080; cost-only ONS .024 / .062 and .033 / .088.
**Consequences.** (i) The reported "benign false alarm" mixes true false alarms (≈ 0.01 for H2c, below α = 0.05 by a wide margin) with detections of small real cost increases. The ".067 near the limit" caveat was therefore an artefact of the cell labelling, and the true size of the H2c test is far below α. (ii) The claim that Brier-null methods "alarm on benign shifts" is largely wrong: where the decision cost does not increase, HG alarms at 1%; it alarms heavily where cost rises modestly (it is **more** powerful than H2c at detecting small harm: .31/.54 vs .07/.13). The "decision-aware" selling point of H2c rests on the economic threshold 0.10, which H2c does not use (tol = 0). To exploit it one must test a null with tolerance ε = 0.10, which changes every power number and has not been run. (iii) The cost-SR-versus-H2c power comparison inherits the same labelling issue.
**Verdict.** The frozen D1–D3 results stand as stated, but their interpretation ("decision-harm-aware with benign false alarm ≤ .067; Brier methods over-alarm") does not. The defensible H2c claim is narrower: *among zero-tolerance cost-null e-processes, Brier-guided discounted Kelly is the most powerful of those implemented.*
