# Family R results (Sprint 2)

This report consolidates the existing Family R artifacts; it does not add or rerun experiments.
Candidate-level dispositions and artifact links are in [ledger.json](ledger.json). The raw runs are
under the gitignored `outputs/sprint2/R/` directory. Their manifests record the code revision, config,
and source hashes.

## Evidence and scope

- Main development screen: `outputs/sprint2/R/dev_screen_a05`, 20 seeds per synthetic regime,
  seed base `2026110701`, alpha `.05`; it covers 11 null/alternative/reversal regimes and the R
  variants plus shared controls.
- Track E/V summary: `outputs/sprint2/R/analysis/trackE_V_a05.json`.
- Track R: `outputs/sprint2/R/analysis/risk_curves.json` and `.md`. Risk operating points are chosen
  from the tested alpha grid; the resulting curves/frontier are descriptive and selection-aware
  inference is not supplied.
- Real checks: `outputs/sprint2/R/analysis/real_a05.json` (fresh streams and twin streams). The
  streams do not have verified causal shift labels or application utilities.

Reproduction entry points are `outputs/sprint2/R/run_dev_screen.sh`, `run_trackR.sh`, and
`run_real.sh`. A representative development run is:

```sh
uv run python scripts/sota_sprint/screen.py --seed-base 2026110701 --workers 2 \
  --regimes F0_null,F0_worse,F5_dep_null_r8,F5_dep_null_r95,F0_better,F7_near_better,F9_bursty_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95,F3_reversal_800 \
  --policies D2,R2,R2-qc,R2-floor25,R3-base,R3-plugin,R3-near,R3-alloc,R3-plugnear,R4-both,R4-comb,R5,R5-nopen,R5-iidvar,R6:D2-floor25,R6:D2-always,A5b,cams_adapter,R:xu_acquisition_only@alpha,xu_acquisition_only,gated_adaptive_range+front,choe_ramdas_eb+front,SMCS+retain-incumbent,economic_replacement,R:economic_stop,gated_deployment,C6,CONTROL_never_switch \
  --seeds 20 --alpha 0.05 --out outputs/sprint2/R/dev_screen_a05
```

## Post-development Track-R coverage follow-up

The earlier Family-R risk curves had no held-out points for nine policies that had at least one
development-feasible alpha. The registered follow-up evaluates all 26 eligible policies on the same
new seed block, at all eight alpha values, over the four null and six alternative regimes. It ran
1,600 episode jobs and produced 41,600 policy records. The four policies without a feasible
development alpha remain without an operating point. This is a new simulator replicate on reused
generators, not independent real-data confirmation.

The run-level coverage and checksums are in
[R_trackR_coverage_followup_manifests.json](R_trackR_coverage_followup_manifests.json); the full
empirical cost-risk table is in
[R_trackR_coverage_followup.md](R_trackR_coverage_followup.md), and the interpretation and Pareto
points are in [R_trackR_coverage_followup_report.md](R_trackR_coverage_followup_report.md). The
development calibration map matches the previous Family-R map exactly. Evaluation point counts by
target are 12 at R5, 22 at R10 and R15, and 26 at R20–R30. The R5 frontier contains R3-alloc at
zero observed promotions and cost 391.5 [95% CI 386.9, 396.1], R3-base at 0.037 risk and cost
370.1 [363.3, 377.0], and H2 at 0.050 [95% CI 0.020, 0.122] risk and cost
366.9 [359.7, 374.1]. Alternative-cost intervals use Student-t critical values over the 20
per-seed means. These are panel-local
points with descriptive intervals; they do not establish a guarantee or general superiority.

Across the 83 policy-target cells also present in the earlier held-out report, median absolute
between-block differences were 0.013 in observed risk and 7.3 in alternative net cost. This is
descriptive seed-block variation, not an inferential comparison.

## Findings by candidate

| Candidate | Evidence-based disposition |
|---|---|
| **R1: D2 risk-cost frontier** | Track-R operating points exist for R20–R30; no selected operating point for R5–R15. Pareto points are conditional on the candidate/alpha grid, not a confirmatory frontier. |
| **R2: conditional-mean e-process** | The implementation verification note documents the conditional-mean null, filtration, weighting and freeze rule. R2 targets the conditional-mean null (V1); Markov-null promotion counts are out-of-class risk checks. R2 is not a general dependence-robust certificate. |
| **R3: alternative Markov evidence** | Markov variants had low promotion in the two tested Markov null regimes, but their dev alternative cost is high (R3-base mean J 393.6 versus D2 362.8). Evidence is limited to the declared Markov model class and tested generators. |
| **R4: dual evidence** | R4-both had zero promotions in the three tested null screens and mean alternative cost 399.4 (+36.6 paired vs D2). R4-comb had 0/20 promotions on F0 and rho=.8, 5/20 on rho=.95, and mean alternative cost 375.6 (+12.8 paired vs D2); it was cheaper than R4-both in this aggregate but retained a .25 rate on rho=.95. Neither variant dominated D2 across validity and cost. |
| **R5: risk-aware economic deployment** | Prior development-selected Track-R points were on the tested-grid Pareto set. A frozen alpha=.02, new-seed follow-up (100 seeds per regime) found promotions 15/100 [Wilson 95% CI .093–.233] on F0 null, 26/100 [.184–.354] on rho=.8 null, 24/100 [.167–.332] on rho=.95 null, and 0/100 on F0_worse. Across six alternatives, paired mean net cost was 10.23 lower than D2 (95% CI for advantage [8.05,12.41]); however R5 cost more than D2 on F1_late_800 (+7.49) and S_dep_better_r95 (+18.69). This fixed-alpha sensitivity is mixed evidence, not validation of the selected frontier or a guarantee. |
| **R6: joint risk/label budget** | The joint selector chooses no point through R15; it selects D2 at R20/R25 and R6:D2-always at R30. At R30 eval risk is .2875 [.1999,.3946], cost 358.17. No evidence shows improvement over D2 across targets; the high-risk point is not a safety improvement. |

## Comparator and validity qualifications

Historical outputs include `R:xu_acquisition_only@alpha` and in some comparisons call it a certified
published comparator. That label is incorrect: this is an acquisition adapter using ShiftLab's
certificate, not Xu et al.'s published risk-control method. It must be removed from published-certified
rankings. Existing raw results are retained; any revised “best comparator” contrast must be computed
as a clearly marked amendment and must account for comparator selection on development/evaluation
data. No claim here establishes superiority to published SOTA.

R2's specific conditional-mean proof audit is in
[conditional_mean_verification.md](conditional_mean_verification.md). In brief, its target differs
from query-conditional and marginal nulls; a V1 label does not imply validity under the Markov or twin
marginal nulls. Track-R confidence intervals and Pareto marks are based on the tested configuration
grid and do not adjust for selecting configurations from that grid.

## Assessment

The family provides useful negative and scoped positive evidence: R2 is a distinct conditional-mean
construction with explicit assumptions; R5 supplies a development-selected simulator risk-cost trade-off with elevated null promotions in the fixed-alpha follow-up; R3/R4
show that broader or combined evidence can incur substantial conservatism; R6 does not establish a
better joint budget frontier. No candidate has independent confirmation or supports a broad real-world
validity claim. **Continue** only with corrected comparator analyses and independent, preselected
validation; otherwise keep these results as development evidence.
