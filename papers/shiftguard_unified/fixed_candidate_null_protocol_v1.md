# Fixed-candidate certification null calibration protocol v1

**Status:** frozen supplementary implementation calibration; not an efficacy confirmation.  
**Date:** 2026-10-26.

## Question and null

Does the no-scout Q1→Q2 arm preserve the registered false-promotion threshold when the candidate is fixed before monitoring and certified on fresh outcomes? The learner tests candidate 0, frozen by initial validation, on events 1,600–2,399. Q1 uses events 800–1,599 and must trigger before Q2 begins. Labels are immediate, query uniforms are independent of features and outcomes, and total queried labels may not exceed 640.

Use the `calibration_candidate_null` generator profile. It installs non-identical candidates that differ from the all-positive incumbent only for score values above the Bayes decision boundary. There, conditional expected incumbent-minus-candidate gain is nonpositive; elsewhere gain is zero. Certification also subtracts the positive amortized switching cost. The false-promotion null is therefore satisfied pointwise for every event and remains true conditional on the Q1 trigger and the fixed candidate identity.

The registered method is `full_pipeline_fixed_certification`; candidate identity comes from initial validation, and no Q2 scouting data may be read. Count false promotion only on streams where Q1 triggers, the fixed candidate is non-null eligible under the independent evaluator calculation, and Q2 runs. Scan consecutive seeds from 2026116000 until 1,000 eligible streams, with a maximum of 3,000 attempts. The endpoint is the exact one-sided 95% Clopper–Pearson upper bound on the false-promotion rate; pass if it is at most alpha 0.015 and all streams obey the label cap.

This is a supplementary single-endpoint calibration. It is reported separately from integrated calibration v1 and does not change that protocol's four-cell confidence accounting. It diagnoses the registered synthetic implementation, not real-data validity, power, benefit, dependence, or delayed feedback.

## Reproducibility

Run `uv run python scripts/calibrate_fixed_candidate_null.py --device cuda --replicates 1000 --output outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1`, then run `uv run python scripts/verify_fixed_candidate_null_calibration.py --output outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1`. Retain every attempted stream, seed, eligibility reason, source/protocol hash, CUDA metadata, summary, and verifier output. Do not make figures from this calibration.
