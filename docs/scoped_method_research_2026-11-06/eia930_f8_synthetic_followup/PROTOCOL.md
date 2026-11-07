# EIA-930 F8 fixed-challenger synthetic follow-up

**Purpose:** test whether the post-selection real replay lead is consistent with the registered
Failure Atlas F8 mechanism on fresh synthetic streams, and quantify its boundary under null and
reversal controls. This is not an independent real-data confirmation.

## Hypothesis and scope

The fixed-challenger control uses no feedback labels and pays one switch cost. On the Atlas
`F8_rare_better` regime (3% disagreement, challenger correct with probability .90 on disagreements),
it may save cost over CAMS by avoiding acquisition and promotion delay. This method assumes the
challenger is the intended target. The synthetic test does not make that assumption identifiable
from its unlabeled stream.

## Frozen protocol

- Fresh streams: 100 paired seeds per regime, seed base `2026110717`.
- Primary cell: `F8_rare_better`.
- Adverse cells: `F0_null` and `F3_reversal_800`.
- Contract: `T=2000`, `B=200`, label price `.05`, switch cost `5`, delay from each regime,
  alpha `.05`.
- Candidate: `fixed_challenger` (always deploy model 1; zero labels; one switch cost per episode).
- Primary comparator: `cams_adapter` (the lowest-cost Failure Atlas F8 discovery method). Secondary
  frozen panel: online LLM picker, causal Model Selector adapter, Model Picker adapter,
  Gong-Zhang, Qiu, Xu acquisition-only, SMCS, gated certificate, and never-switch.
- Primary endpoint: paired net cost, equal to prediction loss + label cost + switch cost.
- Primary evidence criterion, applied only to `F8_rare_better`: candidate saves at least 5 units per
  2,000 events versus CAMS with paired 95% interval below zero. `F0_null` and `F3_reversal_800` are
  descriptive adverse-cell diagnostics; no success gate or null error-rate claim is applied there.
  Report every method, all three regimes, null promotions, costs, labels and switches. No result is
  pooled across regimes.

This fixed policy is a known baseline, not a novel method. The F8 candidate is the declared
alternative cell; the null and reversal rows are adverse cases showing why the rule cannot be
applied universally. Do not infer that an online learner can know the F8 regime without a separate
pre-decision signal. No real holdout is opened by this synthetic screen.

## Reproduction

```bash
uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 100 \
  --seed-base 2026110717 --regimes F8_rare_better,F0_null,F3_reversal_800 \
  --policies fixed_challenger,cams_adapter,online_llm_picker,model_selector_causal,model_picker_adapter,\
gong_zhang_paid_obs,qiu_delayed_movement,xu_acquisition_only,SMCS+retain-incumbent,gated_deployment,CONTROL_never_switch \
  --extra f8_synthetic_extra --workers 4 \
  --out docs/scoped_method_research_2026-11-06/eia930_f8_synthetic_followup/run
uv run python docs/scoped_method_research_2026-11-06/eia930_f8_synthetic_followup/analyze.py
```
