# Propensity-floor diagnostic: results and interpretation

**Protocol:** [`propensity_floor_diagnostic_protocol.md`](propensity_floor_diagnostic_protocol.md)  
**Higher-floor run:** [`outputs/propensity_floor_diagnostic_qmin020_30/`](../outputs/propensity_floor_diagnostic_qmin020_30/)  
**Original 60-seed trace analysis:** [`outputs/monitor_signal_diagnostic_20_60_v2/analysis/`](../outputs/monitor_signal_diagnostic_20_60_v2/analysis/)  
**Status:** completed diagnostic; reused seeds, no confirmatory claim.

## Main finding: monitor support must match the sampling policy

The original 20% hard-budget run used a common PPI support bound of 96.9 for every method. The uniform policy's propensity is exactly 0.20 throughout, so its registered policy-specific bound is 45.9. Replaying the same uniform PPI increments with that predictable, policy-declared bound raises fixed-mixture crossings on the original 60 boundary-harm streams from 6/60 to 47/60. The predictable-variance process crosses in 41/60 under the 45.9 bound; plug-in empirical Bernstein crosses in 1/60. On stationary and benign-nuisance controls, these replays have zero crossings among 60 streams per method. The control counts are diagnostic only and do not replace independent null calibration.

This changes the interpretation of the original allocation comparison. Its common-bound result remains a valid matched-scale diagnostic, but the 6/60 uniform result is unnecessarily conservative for the known uniform propensity. The evidence curve uses `q_min=0.10`, so its 96.9 bound remains appropriate; its 4/60 common-bound count should not be described as evidence of superiority over a correctly bounded uniform monitor. The original output and trace are retained.

## Paired propensity-floor replay

The CUDA run used the first 30 seeds of the original block, unchanged scenarios, the same 20% hard dollar cap, and `q_min=0.20`. All 30 boundary onsets were reached in both floor settings. For the uniform policy, each event's propensity, query indicator, observed label, proxy prediction, PPI increment, and evaluator outcome is identical between runs. Its acquisition path is therefore unchanged; this comparison isolates the monitor bound. The higher-floor evidence-curve path also changes, because its acquisition rule depends on `q_min`.

The compact report in `outputs/propensity_floor_diagnostic_qmin020_30/reports/propensity_floor_comparison.md` gives paired detection counts under both the original common bounds and each policy-specific bound, plus predictable-variance and plug-in empirical-Bernstein replays. For uniform, both floor runs use the same correct 45.9 support bound, and its event paths match exactly. The comparison is a deterministic replay on reused seeds, not an independent evaluation.

For the evidence curve, moving `q_min` to 0.20 changes the monitor bound from 96.9 to 45.9 and changes querying and budget horizon. In this 30-seed boundary subset, fixed-mixture crossings under the registered bound are 4/30 at `q_min=0.10` and 8/30 at `q_min=0.20`; mean processed events are 2,376 and 1,841, mean queried labels 459.5 and 480.0, and mean spend $688.8 and $718.2. Every onset was reached. These numbers describe this paired block and do not establish a preferred floor.

## Limitations and next step

The bounded-mean monitor's validity still depends on the conditional null, predictable policy and proxy selection, the stated propensity floor, and the feedback filtration. The variance-adaptive and plug-in processes are existing comparator implementations; this replay does not provide independent calibration or prove that either is superior. The support bound must be registered from the policy's guaranteed propensity floor, never estimated from observed increments. The `q_min=0.20` evidence-curve comparison also changes both acquisition and the stopping horizon, so its detection difference cannot be attributed to the bound alone.

Next, preserve independent null calibration and evaluate uniform and adaptive methods with correctly registered method-specific support bounds from the outset. Confirm any power or cost conclusion on fresh seeds, with a prespecified horizon and monitoring rule. No figure was generated because PaperBanana is not available in the active environment.
