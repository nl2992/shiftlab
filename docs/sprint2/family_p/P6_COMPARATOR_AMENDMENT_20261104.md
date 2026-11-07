# P6 corrected comparator-class follow-up (2026-11-04)

The registered 100-seed Round-5 P6 evaluation compared against `xu_acquisition_only`, which is
Xu's acquisition component plus ShiftLab's paired certificate, not Xu's published risk-control
certificate. That output is preserved at `outputs/sprint2/round5/P6_LRMD_U_eval/`; its prior
“best certified” label is invalid after the comparator-class correction.

Before running this amendment, freeze the following policy panel and regimes. The target is a
post-development descriptive comparison of P6 against methods classified as certificate-policy
comparators in `scripts/sota_sprint/bench.py`, plus internal mechanism controls and Xu adapter as a
separately labeled reference:

- Regimes: `F1_late_800`, `F1_late_1200`, `W_late_1000`, `F3_reversal_800`, `S_reversal_400`,
  `F0_better`, `F5_dep_null_r8`.
- Policies: `P6_LRMD_U`, `M_LRMD_SUI`, `D2`, `A5b`,
  `gated_deployment`, `gated_adaptive_range+front`, `discern_style`,
  `SMCS+retain-incumbent`, `choe_ramdas_eb+front`, `rmm:gated_deployment+RMM`,
  `xu_acquisition_only`, `CONTROL_never_switch`.
- 100 paired seeds, seed base `2026110815`, alpha .05, four workers. All methods share each
  regime/seed stream. The primary report is per-regime paired net cost and promotion rate. The
  certified-port comparator is selected among the registered certificate-policy comparators
  present in this run; this same-sample selection is descriptive and not selection-adjusted.
- This amendment is post-development, not independent or prospective confirmation. Method ports
  remain common-contract adapters, not author-native replications. Risk rates are empirical only.

Command:

```sh
uv run python scripts/sota_sprint/screen.py --regimes F1_late_800,F1_late_1200,W_late_1000,F3_reversal_800,S_reversal_400,F0_better,F5_dep_null_r8 --policies P6_LRMD_U,M_LRMD_SUI,D2,A5b,gated_deployment,gated_adaptive_range+front,discern_style,SMCS+retain-incumbent,choe_ramdas_eb+front,rmm:gated_deployment+RMM,xu_acquisition_only,CONTROL_never_switch --seeds 100 --seed-base 2026110815 --workers 4 --alpha 0.05 --out outputs/sprint2/round5/P6_corrected_comparators_100
```
