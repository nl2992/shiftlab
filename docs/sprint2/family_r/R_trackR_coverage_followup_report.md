# Family R Track-R coverage follow-up

This is a new simulator replicate on reused synthetic regimes, evaluated on one common seed
block. The development-selected alpha map is frozen to the original Family-R development
runs; the finalizer verified that the regenerated map matches the existing map. The run is
post-development descriptive evidence, not independent real-data confirmation or a formal
risk guarantee.

## Coverage and calibration

- 8 evaluation alpha runs; 1,600 episode jobs;
  41,600 policy records (5,200 per run).
- 26 policies with at least one development-feasible
  operating point; four policies with no feasible development alpha remain without a point.
- Held-out points by target: R5=12, R10=22, R15=22, R20=26, R25=26, R30=26.
- The registered target is calibrated from a development point estimate. Held-out rates and
  their Wilson intervals can exceed the target; these are empirical operating points only.

## Cost-risk Pareto points

The frontier is local to this 26-policy panel. Costs are mean alternative net costs with
95% Student-t intervals over per-seed means; risk is pooled over the four null regimes with Wilson
95% intervals.

| Target | Policy | Alpha | Held-out risk (95% CI) | Alternative net cost (95% CI) |
|---|---|---:|---:|---:|
| R5 | `R3-alloc` | 0.05 | 0.000 [0.000, 0.046] | 391.5 [386.9, 396.1] |
| R5 | `R3-base` | 0.5 | 0.037 [0.013, 0.105] | 370.1 [363.3, 377.0] |
| R5 | `H2` | 0.3 | 0.050 [0.020, 0.122] | 366.9 [359.7, 374.1] |
| R10 | `R3-alloc` | 0.05 | 0.000 [0.000, 0.046] | 391.5 [386.9, 396.1] |
| R10 | `R3-base` | 0.5 | 0.037 [0.013, 0.105] | 370.1 [363.3, 377.0] |
| R10 | `choe_ramdas_eb+front` | 0.1 | 0.087 [0.043, 0.170] | 367.7 [361.5, 374.0] |
| R10 | `H2` | 0.5 | 0.100 [0.052, 0.185] | 359.7 [352.4, 366.9] |
| R15 | `R3-alloc` | 0.05 | 0.000 [0.000, 0.046] | 391.5 [386.9, 396.1] |
| R15 | `R3-base` | 0.5 | 0.037 [0.013, 0.105] | 370.1 [363.3, 377.0] |
| R15 | `H2` | 0.5 | 0.100 [0.052, 0.185] | 359.7 [352.4, 366.9] |
| R15 | `R5` | 0.02 | 0.125 [0.069, 0.215] | 356.0 [350.6, 361.4] |
| R20 | `R3-alloc` | 0.05 | 0.000 [0.000, 0.046] | 391.5 [386.9, 396.1] |
| R20 | `R3-base` | 0.5 | 0.037 [0.013, 0.105] | 370.1 [363.3, 377.0] |
| R20 | `H2` | 0.5 | 0.100 [0.052, 0.185] | 359.7 [352.4, 366.9] |
| R20 | `R5` | 0.02 | 0.125 [0.069, 0.215] | 356.0 [350.6, 361.4] |
| R20 | `R2-qc` | 0.2 | 0.175 [0.107, 0.273] | 355.0 [349.8, 360.3] |
| R25 | `R3-alloc` | 0.05 | 0.000 [0.000, 0.046] | 391.5 [386.9, 396.1] |
| R25 | `R3-base` | 0.5 | 0.037 [0.013, 0.105] | 370.1 [363.3, 377.0] |
| R25 | `H2` | 0.5 | 0.100 [0.052, 0.185] | 359.7 [352.4, 366.9] |
| R25 | `R5` | 0.02 | 0.125 [0.069, 0.215] | 356.0 [350.6, 361.4] |
| R25 | `choe_ramdas_eb+front` | 0.5 | 0.188 [0.117, 0.287] | 351.4 [346.0, 356.9] |
| R25 | `R2-qc` | 0.3 | 0.200 [0.127, 0.300] | 351.1 [346.0, 356.3] |
| R30 | `R3-alloc` | 0.05 | 0.000 [0.000, 0.046] | 391.5 [386.9, 396.1] |
| R30 | `R3-base` | 0.5 | 0.037 [0.013, 0.105] | 370.1 [363.3, 377.0] |
| R30 | `H2` | 0.5 | 0.100 [0.052, 0.185] | 359.7 [352.4, 366.9] |
| R30 | `R2` | 0.5 | 0.175 [0.107, 0.273] | 351.2 [347.0, 355.5] |
| R30 | `R5` | 0.05 | 0.212 [0.137, 0.314] | 346.6 [341.2, 352.1] |
| R30 | `R2-qc` | 0.5 | 0.237 [0.158, 0.341] | 345.8 [340.9, 350.7] |

## Repeat-block comparison

Across 83 policy-target cells also present in the earlier Family-R held-out
report, the median absolute difference was 0.013 in risk
and 7.3 in alternative net cost; maxima were
0.100 and 11.4, respectively. This is descriptive
between-block variation on the same simulator regimes, not a significance test.

## Interpretation limits

The results fill held-out operating-point coverage for policies that were calibrated on
development data but omitted from earlier evaluation screens. They do not show general
superiority: R3-alloc reaches zero observed promotions at high alternative cost, while some
development-selected thresholds (including R2-floor25 at R10) exceed their nominal target
on evaluation. Reused generators and policies exposed during development limit claims to
this post-development simulator replicate. No application utility or causal shift label is
provided by these synthetic regimes.

Machine-readable operating points: `R_trackR_coverage_followup.json`. Per-run configs,
code revisions, source hashes, and output checksums: `R_trackR_coverage_followup_manifests.json`.
