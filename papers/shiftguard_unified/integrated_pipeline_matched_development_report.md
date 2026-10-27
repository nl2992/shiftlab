# Matched integrated pipeline development comparison

**Date:** 2026-10-26  
**Status:** exploratory CUDA development only. No integrated null calibration, confirmatory run, or claim of comparative efficacy has been made.  
**Protocol:** [`integrated_benchmark_protocol.md`](integrated_benchmark_protocol.md), design draft 0.1.  
**Artifacts:** [`pipeline_matched_eventwise_dev_10_v1/`](../../outputs/shiftguard_unified/integrated_development/pipeline_matched_eventwise_dev_10_v1/)

## Design actually run

The runner compared five policies on the same generated stream for every seed: `continue`, scheduled promotion of the validation-ranked candidate, Q2 two-gate Target-Scout certification plus rollback, Q1-triggered fixed-fallback switching, and the full Q1 → Target-Scout → rollback pipeline. It used 10 seed IDs (`2026102700–2026102709`) in each of six profiles, for 60 matched streams and 300 method-stream rows. Profiles were stationary, benign nuisance shift, boundary-local harm, recurring regimes, residual variance change, and `harmful_adaptation_at_monitor`.

All streams had 3,200 events and an overall hard cap of 640 queried labels. Fit/validation used events 0–799; Q1 monitored 800–1,599; Target-Scout used 1,600–2,399; deployment/rollback used 2,400–3,199. The Q1 request probability was 0.40 with a 320-label cap. If Q1 triggered, its unused reservation could be transferred before Target-Scout by `B_scout=min(320,640-labels_monitor-160)`, and the scout/certification request probability was fixed to `B_scout/800` for that entire block. Rollback retained a 160-label reserve at probability 0.20. Target-Scout used its existing `eventwise_propensity` bound variant; because query probability is constant within each block, the eventwise bound is constant within that stage. The alpha allocation was 0.02 for Q1, 0.015 for promotion, and 0.015 for rollback. It has not been calibrated as a family on the composed workflow.

The `harmful_adaptation_at_monitor` profile keeps the outcome law stationary and applies an all-positive deployed-policy update at event 800. It is a separately named integrated variant because the native generator's policy update at event 1,600 falls outside the Q1 monitoring block. The Q1 fallback is a predeclared fixed source-score policy; it does not use evaluator probabilities.

## Results

| Profile | Q1 triggers, full pipeline | Candidate promotions, full | Candidate promotions, two-gate | Full expected / realized net utility | Two-gate expected / realized net utility | Q1-fallback expected / realized net utility | Mean labels, full / two-gate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stationary | 0/10 | 0/10 | 0/10 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 317.2 / 311.4 |
| Benign nuisance | 0/10 | 0/10 | 0/10 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 317.2 / 311.4 |
| Boundary-local harm | 9/10 | 7/10 | 8/10 | 198.08 / 185.87 | 227.22 / 215.36 | 659.84 / 651.66 | 540.3 / 435.7 |
| Recurring regimes | 9/10 | 0/10 | 0/10 | 0.00 / 0.00 | 0.00 / 0.00 | 437.75 / 426.66 | 432.0 / 311.4 |
| Residual-variance shift | 0/10 | 0/10 | 0/10 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 317.2 / 311.4 |
| Harmful adaptation at monitor start | 10/10 | 5/10 | 6/10 | 139.95 / 136.08 | 168.29 / 163.77 | 722.84 / 722.95 | 545.5 / 406.1 |

The utility is incremental to `continue`, includes switching/rollback charges, and is evaluator-computed from the known synthetic outcome law or realized outcomes. The 95% paired seed-bootstrap intervals below are descriptive and **not** adjusted for the many profile/method contrasts. With only ten streams per cell, they are highly provisional.

- On boundary-local harm, full pipeline minus two-gate expected utility was −29.14, interval [−100.02, 12.61]; realized utility difference was −29.50, interval [−102.285, 13.800]. The Q1 gate did not show an advantage and used about 105 more labels per stream on average.
- On aligned harmful adaptation, full pipeline minus two-gate expected utility was −28.34, interval [−85.03, 0.00]; realized difference was −27.69, interval [−83.085, 0.000].
- The full pipeline and two-gate had identical utility in the recurring and residual-variance screens because neither certified a candidate. Q1 fallback improved over continuing by +437.75 expected utility under recurring regimes, while the candidate-promotion methods did not intervene.
- The simple scheduled-promotion baseline had positive mean expected utility in all six profiles, including +44.75 in stationary and +107.18 under residual-variance change, but it promotes without certification. Its positive screen results show that the frozen candidate family may already contain a strong policy; they do not justify unguarded deployment or a general safety claim.
- No rollback occurred in any run. The run therefore supplies no evidence about false rollback, rollback delay, or reversal protection.
- There were no Q1 triggers in the 20 stationary/benign control streams, and no gated promotions in those controls. These small development counts are not an error-rate calibration.

## Reproducibility and interpretation

The source and metric hashes in the execution manifest were rechecked against the current worktree and match. The current protocol draft does not match its execution-time hash, and an exact protocol snapshot is missing; see the [provenance audit](integrated_run_provenance_audit.md). This further limits the run to exploratory evidence and must be corrected before any calibration or confirmation.

The manifest reports the RTX 4060 Laptop GPU, CUDA 13.0 / PyTorch 2.9.1, stage boundaries, methods, labels, source hashes, and protocol hash. The 300-row Parquet, summary, paired-contrast CSV, runner, and recorded hashes were verified; no run exceeded 640 labels. On 2026-10-26, `uv run pytest -q` passed repository-wide: **1,442 passed, 1 skipped** in 637.67 seconds. Focused Ruff and mypy checks also passed. This verifies the current checkout's tests; it does not calibrate the integrated procedure.

The development evidence points to a specific practical gap: the upstream harm gate adds label cost but has not improved utility over two-gate candidate certification; the fixed fallback works substantially better in the tested harm profiles; the candidate gate still misses recurring and residual-variance profiles; and rollback has not been challenged. Eventwise-propensity certification raises promotion rates over the earlier minimum-propensity pilot, but it requires new null calibration at the full pipeline level. These findings argue for a more discriminating, preregistered comparison of the monitor-triggered workflow, two-gate workflow, and fixed fallback before any new method development.

**Follow-up implementation smoke:** a distinct seven-policy runner now includes controller-gated versions of the two-gate and full Q1→Q2→Q3 arms. Its two-seed CUDA smoke run passed and is documented in [`integrated_controller_smoke_report.md`](integrated_controller_smoke_report.md). Those seeds overlap this pilot, the smoke run had no rollback events, and it supplies no new efficacy or error-rate evidence.

This study uses immediate labels, synthetic non-performative outcomes, a policy family fixed from initial training data, and only ten matched seeds per profile. It does not reproduce *When to Retrain*, ASI, Robust ASI, or RCCDA. It omits the `InterventionController`, delayed feedback, a genuine real-data downstream evaluation, and an actual reversal-after-promotion rollback case. The rollback state machine was not empirically exercised. All of those limitations remain open.

