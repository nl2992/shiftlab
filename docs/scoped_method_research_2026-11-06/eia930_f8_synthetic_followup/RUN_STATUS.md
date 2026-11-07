# Run status and deviations

- Frozen protocol was pushed in commit `4d4e190a`; published competitor import fix was pushed in `cfca3a68` before the successful run.
- First execution stopped before producing records because the extra module initially exposed only the fixed challenger and omitted the registered `gong_zhang_paid_obs` factory. The module was corrected to merge the existing `v2_extra.EXTRA` registry; the successful run below is a complete rerun, not a continuation.
- Successful command (from repository root):

```bash
uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 100 --seed-base 2026110717 --regimes F8_rare_better,F0_null,F3_reversal_800 --policies 'fixed_challenger,cams_adapter,online_llm_picker,model_selector_causal,model_picker_adapter,gong_zhang_paid_obs,qiu_delayed_movement,xu_acquisition_only,SMCS+retain-incumbent,gated_deployment,CONTROL_never_switch' --extra f8_synthetic_extra --workers 4 --out docs/scoped_method_research_2026-11-06/eia930_f8_synthetic_followup/run
uv run python docs/scoped_method_research_2026-11-06/eia930_f8_synthetic_followup/analyze.py
```

- 300 successful regime-seed jobs, 3,300 method-episode records (11 methods x 100 seeds x 3 regimes); output: `run/records.jsonl`, run manifest: `run/manifest.json`, derived summary and SHA-256: `ANALYSIS.json`.
- Primary F8 criterion passed: fixed challenger minus CAMS mean `-6.174`, paired percentile bootstrap 95% interval `[-6.857, -5.544]`. The fixed challenger is a conventional static deployment control; this does not support a novelty claim.
- Scope diagnostics: on `F3_reversal_800`, fixed challenger net cost `384.220`, while the best shown rule (never switch) is `344.770`; the fixed policy therefore incurs substantial reversal harm. On `F0_null`, fixed challenger is `363.310` versus never-switch `359.330`; the apparently large difference against CAMS is driven by CAMS' switches and is not a calibrated null type-I error estimate.
- No real confirmation, null calibration study, or independent source-cluster validation was performed. No failures or adverse cells were dropped.
