# T1/T2/T5 held-out Track-R coverage follow-up

Registered 2026-11-05 before running this panel. The audit of the existing Family-T Track-R
artifacts found development calibration entries for the T1, T2 and T5 mechanisms but no corresponding
held-out operating-point rows for their primary transferable policies. T3's separate follow-up does
not cover these configurations. This protocol fills that panel gap; it does not revise the original
development selection or claim confirmatory evidence.

## Question and estimand

For each registered risk target R5/R10/R15/R20/R25/R30, what cost-risk operating points result when
the largest alpha on the fixed grid that meets the target on development null regimes is evaluated
on a separate seed block? Risk is the pooled promotion frequency across
`bench2.RISK_NULLS`; cost is mean `net` over `bench2.RISK_ALTS`, averaged per seed and episode using
the existing `risk_curves.py` implementation. Wilson 95% intervals are used for risk and 95% t
intervals over seed/episode means for cost. Pareto status is local to this follow-up's listed policies.
These are descriptive simulator estimates, not anytime-valid guarantees or real-world evidence.

## Policies

- T1 Model Picker transfer: `T:mp/a5b`, `T:mp/a5b+ad`, `T:mp/a5b+ad+rb`,
  `model_picker_adapter`, `D1`, `D6:mp`, `D2`, `A5b`.
- T2 Gated Deployment transfer: `T2:gated/a5b`, `T2:gated/a5b+front`,
  `T2:gated/env8`, `T2:gated/env8+front`, `gated_deployment`,
  `gated_adaptive_range+front`, `D2`, `A5b`.
- T5 shared wrapper transfer: `T:cams/a5b`, `T:mp/a5b`, `T:ms/a5b`,
  `model_picker_adapter`, `model_selector_causal`, `D2`, `A5b`.

The union is run once per alpha and seed block; duplicate policy names are deduplicated. The
cross-family Pareto table remains the authoritative combined frontier and will be refreshed with
these source rows after validation.

## Frozen execution

- Alpha grid: `bench2.ALPHA_GRID` = `.005, .01, .02, .05, .1, .2, .3, .5`.
- Regimes: all four `bench2.RISK_NULLS` and all six `bench2.RISK_ALTS`.
- Development: 20 seeds, base `2026111201`; calibration only.
- Evaluation: 20 separate seeds, base `2026111211`; no threshold retuning.
- Frozen runner: `scripts/sota_sprint/run_t125_trackr_followup.sh`; it calls
  `scripts/sota_sprint/screen.py` for every alpha/split and stores one run manifest per output.
  Analysis: `scripts/sota_sprint/risk_curves.py`.
- Full argv, source hashes, output hashes and raw-record checksums will be captured in the follow-up
  manifest index before reporting results.

No policy, regime, alpha, target or interval definition will be changed after inspecting the
evaluation outcomes. The seed blocks are new simulator replicates but do not create independent
real-data confirmation or erase prior development exposure to the mechanisms and regimes.
