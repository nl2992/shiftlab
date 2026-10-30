# Round 2 and real-development decision

## Execution

756 new, distinct, active pacing/guidance/allocation compositions completed 12 cases (9,072 configuration-case evaluations), with 96 paths per case and horizon 2,000. Together with round 1: **1,296 distinct configurations**. Corrected reruns/replays are not counted twice. Six references accompany every case.

These are exploratory composition evaluations, not 1,296 new algorithms or independent confirmation. No final holdout was opened. Source-calibrated cases use 300/1,000/5,000 independent calibration labels per simulated path, a Hoeffding upper bound at .01, and test alpha .04. Known-nominal cases retain alpha .04. Source calibration is counted separately.

## All-case ranking

Rank: empirical null screen <=.05, then equal-case mean shift-attributable harm before first alarm. With 96 null paths, this is triage, not a proven false-alarm rate. Query counts differ; full equal-label frontiers remain required.

```
     id  harm_to_alarm  post_power     labels  worst_null  guidance  gamma  cap allocation  restart     pace     guard  screen_eligible
R2_0056      30.882338    0.997685 399.966435    0.010417      0.00   0.98 0.75    uniform    False evidence       off             True
R2_0277      30.935093    0.998843 399.966435    0.010417      0.25   0.98 0.75    uniform    False evidence agreement             True
R2_0068      31.452384    0.997685 394.296296    0.010417      0.00   0.98 0.75   boundary    False evidence       off             True
R2_0313      31.658819    0.996528 394.296296    0.010417      0.25   0.98 0.75   boundary    False evidence agreement             True
R2_0601      31.702454    0.998843 399.966435    0.020833      1.00   0.98 0.75    uniform    False evidence agreement             True
R2_0610      31.767211    1.000000 399.966435    0.000000      1.00   0.98 0.75    uniform     True evidence agreement             True
R2_0286      32.141817    1.000000 399.966435    0.000000      0.25   0.98 0.75    uniform     True evidence agreement             True
R2_0502      32.146620    1.000000 399.935185    0.010417      1.00   0.90 0.75    uniform     True evidence agreement             True
```

Reference means:

```
                                 harm_to_alarm  post_power      labels
id                                                                    
PPRM_batched_CM_EB_cost_formula     150.264688    0.431713  400.000000
PR_PM_EB_cost_formula               105.554051    0.636574  393.081019
active_RCPS_FTL_cost_adapter         93.208889    0.707176  393.081019
matched_cost_parent                  33.566250    0.994213  393.081019
original_H2c_style                   42.481863    0.984954  393.081019
round1_top                           32.191829    0.997685  393.081019
```

The best grid mean is 30.882338, versus round-1 anchor 32.191829: **4.07%** development reduction. It is a cost-only paced configuration, not a guided winner. This is below the proposed 10% practical gate and is selected from 756 alternatives. No statistical or novelty success is established. Per-cell winners do not constitute a single deployable policy.

## Baseline interpretation

- Historical H2c anchor reproduced exactly for all 600 paths in the selected accurate/concept2 cell, at 10% and 20% labels, for H2c, discounted cost and cost-ONS. This validates reproduction, not new evidence.
- PR PM-EB uses the paper's Appendix E bounded-loss formula and predictable variance. PPRM uses equations 19/22/27, hard synthetic labels, one random label per five-event batch and a declared 32-point discrete mixing distribution. Both are formula-based cost/delay adaptations; neither is a full author experimental reproduction.
- PPRM observes batches, while betting candidates observe randomly queried events. Same maximum labels does not make those observation contracts identical. Its conservative running-average procedure has a different null structure from conditional cost betting. Inferiority here cannot establish general superiority over published PPRM.
- The active-RCPS FTL component parity remains verified only at delay1. Full learned sampling/grid inversion, empirical PH/CUSUM thresholds and remaining published families remain open.

## Real-data pilot: negative

Two frozen, training-only model banks were scored on development periods only. Calendar-only features; training median targets; no weather or target-lag leakage. Data are serial and release delays imposed. Source calibration bounds are descriptive assumptions here, not verified iid guarantees.

At query cost .001 and switch cost 1:

```
dataset             monitor  query_cost  switch_cost  total_cost  delta_vs_incumbent  queried_before_stop
beijing           H2c_style       0.001          1.0  876.197000            1.597000             1597.000
beijing    PPRM_batch_CM_EB       0.001          1.0  876.206000            1.606000             1606.000
beijing            PR_PM_EB       0.001          1.0  876.197000            1.597000             1597.000
beijing   R1_selected_blend       0.001          1.0 1088.170750          213.570750              170.750
beijing    RCPS_FTL_adapter       0.001          1.0 1034.069250          159.469250              581.750
beijing matched_cost_parent       0.001          1.0 1089.215500          214.615500              153.000
   bike           H2c_style       0.001          1.0  123.577125            0.577125              577.125
   bike    PPRM_batch_CM_EB       0.001          1.0  123.584000            0.584000              584.000
   bike            PR_PM_EB       0.001          1.0  123.577125            0.577125              577.125
   bike   R1_selected_blend       0.001          1.0  123.577125            0.577125              577.125
   bike    RCPS_FTL_adapter       0.001          1.0  123.577125            0.577125              577.125
   bike matched_cost_parent       0.001          1.0  123.577125            0.577125              577.125
```

Bike: all monitors abstained from switching, so they only added query cost. Beijing: the selected blended monitor and its cost parent switched to a worse challenger; RCPS did so on some query paths. H2c/PR/PPRM abstained and only added query cost. All nine preregistered cost scenarios are retained in per-path outputs, not selected by success. Query seeds replicate acquisition randomness on one stream, not independent real datasets.

This falsifies a useful net-benefit claim for **these frozen alarm-to-challenger controllers on these development tasks**. It does not falsify the underlying monitors or all possible future candidates. The challenger being worse is an observed failure to handle, not permission to replace it after inspecting the same evaluation and call the replacement confirmed.

## Shared bottlenecks and next iteration

1. Detection is not promotion certification: an incumbent-risk alarm does not establish that the candidate beats the incumbent after switching cost. Test a separately valid paired-benefit certificate using common queried outcomes, including harmful challengers and persistent/reversing benefits.
2. Calibration can remove much of a monitor's practical power. Compare total historical-plus-online label cost and consider the different paired-reference target explicitly, rather than assuming known source risk.
3. Propensity floors and budget pacing trade evidence range against label consumption. Best raw-power cells cannot replace a matched label-cost frontier.
4. Faster compact risk verification remains useful engineering. The primary robust-FSC text and author code are now located; product-state memory and robust verification already appear there. J's verifier-only speedup is not a new optimizer. The two-law synthesis/value-gap residual remains unresolved.

**Decision: RESTRICT current monitor/controller claims; continue with paired-benefit and action-set tests plus remaining source-faithful baselines.** No defensible new method is established. Fresh synthetic confirmation and reserved real evaluation remain closed until a candidate clears the scientific and development gates. The user's full goal remains ACTIVE.
