# Integrated pipeline development pilot: Q1 -> Target-Scout -> rollback

**Date:** 2026-10-26  
**Status:** exploratory development only; not calibrated, confirmatory, or suitable for a superiority claim.  
**Protocol:** [`integrated_benchmark_protocol.md`](integrated_benchmark_protocol.md) (design draft 0.1)  
**Output:** [`pipeline_dev_10_v7/`](../../outputs/shiftguard_unified/integrated_development/pipeline_dev_10_v7/)

## What ran

The CUDA pilot ran 10 matched seeds in each of five synthetic profiles on the NVIDIA GeForce RTX 4060 Laptop GPU, using PyTorch 2.9.1 with CUDA 13.0. Each 3,200-event stream used a frozen initial candidate family, a direct paired-cost bounded e-process over events 800–1,599, the existing Target-Scout scout/certification routine over events 1,600–2,399 after a Q1 trigger, and a fresh rollback process over events 2,400–3,199 after promotion. The global label cap was 640; the run enforced a 320-label Q1 cap, a predictable Target-Scout cap of up to 320, and a reserved 160-label rollback cap. Target-Scout query probability was set from the remaining budget before its block.

The `harmful_adaptation_at_monitor` profile is an explicitly modified integrated profile: it keeps the outcome law stationary and moves the all-positive policy update to event 800 so it falls inside the Q1 monitor. The original generator's harmful-policy update occurs at event 1,600 and therefore misses the Q1 monitoring window in this stage schedule. The profile names remain distinct in the manifest and should remain distinct in future reports.

## Preliminary outcomes

| Profile | Streams | Q1 triggers | Candidate promotions | Rollbacks | Mean labels | Mean incremental expected gain vs continue |
|---|---:|---:|---:|---:|---:|---:|
| Stationary | 10 | 0/10 | 0/10 | 0/10 | 317.2 | 0.00 |
| Benign nuisance shift | 10 | 0/10 | 0/10 | 0/10 | 317.2 | 0.00 |
| Boundary-local harm | 10 | 9/10 | 1/10 | 0/10 | 448.0 | 27.11 |
| Residual-variance shift | 10 | 0/10 | 0/10 | 0/10 | 317.2 | 0.00 |
| Harmful adaptation at monitor start | 10 | 10/10 | 0/10 | 0/10 | 466.8 | 0.00 |

The one promoted boundary-harm stream had evaluator-computed expected net gain of 271.07 and realized net gain of 251.95 over its 800-event deployment block after the switching charge. These are single-stream outcomes, not an estimate of average performance. Nine boundary-harm streams triggered Q1 but did not certify a candidate; all ten aligned harmful-adaptation streams also triggered without candidate promotion. No rollback crossing occurred, so the rollback stage's false-alarm behavior and reversal sensitivity remain untested here. The residual-variance profile had no Q1 trigger in this 10-seed screen despite a mean observed paired monitor contrast of 0.13; its power needs examination before calibration.

There were no monitor triggers in 20 stationary and benign-nuisance streams, which is only a small development check, not an error-rate calibration. Each profile has only 10 streams, and the selected positive stream makes the mean gain especially unstable. The pilot used immediate labels and a non-performative outcome stream. It did not compare periodic adaptation, unconditional promotion, the two-gate workflow, or a faithful published retraining baseline. Continue is the zero incremental-gain reference in this report.

## Reproducibility and checks

The output manifest records CUDA hardware, seed block `2026102700–2026102709`, stage boundaries, alpha split `0.02/0.015/0.015`, budgets, and source/protocol hashes. Independent spot checks confirmed 50 Parquet rows; the Parquet, summary CSV, and current runner hashes match the recorded manifest. The pathwise label maximum was 630, below the 640-label cap. `tests/test_integrated_pipeline.py` covers fresh-stage boundaries, total and stage caps, evaluator-oracle noninterference, and rollback taking effect only after the alarm event. Ruff, mypy, and the focused tests passed.

## Decision and next work

This pilot establishes that the component APIs can be wired into a common-stream prototype and exposes a plausible Q1-to-Q2 bottleneck: detection can occur, but the current frozen candidates and certification budget rarely support promotion. It does not establish that integration improves utility. Before independent calibration, add matched continue, periodic/always-promote, and two-gate comparators; include recurring/early-reversal deployment paths; test the native and aligned harmful-adaptation profiles separately; and assess Target-Scout certification under the transferred budget. Run a larger development screen, inspect why candidate certification is rare, then freeze the stage protocol and exact alpha family. The new-algorithm decision remains NO-GO until those comparisons and the high-priority baseline fidelity work identify a reproducible gap.
