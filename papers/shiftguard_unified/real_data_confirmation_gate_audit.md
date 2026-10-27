# Real-data confirmation gate audit

**Audit date:** 2026-10-26/27  
**Purpose:** assess the Phase F requirement for meaningful final evaluation on at least two distinct real-data task families, including at least one actual downstream decision or resource-allocation procedure.  
**Conclusion:** the task-family-count requirement is now met by two protocol-frozen, task-specific evaluations. The complete ShiftGuard system is **not** confirmed on real data, so Phase F remains partial and the programme remains open.

## Evidence by task family

| Family | Frozen evaluation | Decision/resource procedure | Result | Integrity evidence | Limits |
|---|---|---|---|---|---|
| **EIA electricity forecasting** | Chronological 2026-01-01 through 2026-10-19 CISO/ERCO event-time test; training through 2024 and calibration in 2025. Protocol v1 was frozen before scoring 2026. | Frozen, weekly, monthly, and error-triggered Ridge refitting under assumed 0/24/168-hour feedback delays. Reports forecast risk and refit/update resources separately; no cost conversion. | Every adaptive schedule lowered RMSE/MAE versus frozen in both authorities and all three delay conventions. Weekly used 41 updates/authority; monthly used 9; trigger used 9–38. Benefit size was strongly authority-specific. | Original source/protocol/runner/readiness hashes match. A separate CUDA process reproduced all 24 summary rows exactly except machine-dependent `fit_seconds`, and reproduced monthly metrics, paired block intervals and report byte-for-byte. Reproducibility record: [`EIA verification`](../../outputs/shiftguard_unified/independent_real_data/eia_2026_v1/reproducibility_verification.json). | Event-time replay only; publisher release times are unknown. Delays are assumptions. The 42-week-block intervals are descriptive and not multiplicity-adjusted. CISO and ERCO are two authorities within one source, not independent deployment replications. The replay evaluates retraining-resource allocation and predictive risk, not electricity-system utility or online error control. |
| **Upworthy headline-package choice** | Official ShiftLab-unopened holdout, partitioned by week; exploratory partition used for training and hyperparameter selection. Protocol v1 was frozen before holdout acquisition. | Text-only selector chooses one randomized headline package per experiment; compare its observed aggregate CTR with uniform choice over offered packages. | On 3,808 eligible tests, equal-test selected CTR was 0.014455 versus 0.013453 for uniform choice. Difference: 0.001002 (0.1002 percentage points); week-clustered 95% interval [0.000850, 0.001170]. | Source, protocol, runner, and implementation hashes are pinned. A separate verifier refit the policy and reproduced all per-test contrasts and the 10,000-replicate bootstrap exactly. Record: [`Upworthy verification`](../../outputs/shiftguard_unified/real_data_development/upworthy_policy_v1/independent_verification.json). | Public and project-relative, not globally secret. Old CSV lacks the 2024 `Problem` flag; a conservative date buffer was used. Aggregate CTR is the only observed utility; no individual feedback clock, sequential claim, revenue, or deployment cost. |

The two task families are substantively distinct: one is chronological electricity forecasting with model-update resource allocation; the other is randomized digital headline-package selection with a measured click outcome. Both protocols were frozen before their corresponding final-period/split metrics were computed. EIA's replay is reproducible but not an independent implementation or a second deployment replication; Upworthy's holdout was not globally hidden. The evidence is therefore best described as **two source-specific external evaluations**, not broad generalization evidence.

## Gate determination

- **Two real-data task families with meaningful frozen evaluation:** met at the component/task level (EIA 2026 and Upworthy holdout).
- **At least one actual downstream decision or resource-allocation task:** met at the narrow task level. Upworthy measures an actual package-choice outcome; EIA compares real refit schedules and reports update counts and forecast risk on a new-to-ShiftLab period.
- **Unified monitor–certify–intervene system confirmed on real data:** not met. No task supplies the full common feedback, policy-loss, delayed-label, resource-cost, and promotion/rollback contract needed to evaluate every stage together.
- **Prospective validity, common net-utility frontier, or general deployment benefit:** not met. EIA availability times and electricity utility are unknown; Upworthy does not provide revenue or feedback timing. Do not convert either source's native outcomes or resource counts into an invented common currency.

Accordingly, the minimum number of task-family evaluations is no longer the blocker. The remaining Phase F work is claim-specific: freeze the precise system or component claims, verify the remaining task-compatible published baselines, and determine whether any real source can support an end-to-end promotion/resource decision. If not, the final manuscript must state that the integrated method is supported only by controlled synthetic evidence and present real-data findings as component-specific external checks. The working manuscript scope is selected; publication-level differentiation, any required additional real-data experiment, and the complete manuscript remain open.

## Reproduction commands

```powershell
uv run python scripts/verify_eia_2026_reproducibility.py --overwrite-verification
uv run python scripts/verify_upworthy_policy.py
```

The EIA command replays on CUDA when available and refuses to overwrite the audit record. The Upworthy command reconstructs from the already-opened holdout without retuning. Neither command designates these public historical data as globally untouched.
