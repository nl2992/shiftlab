# P6 Beta(2,1) start-prior transfer screen (2026-11-07)

## Decision

**FAIL: stop this candidate lane.** The preregistered primary requirement was a paired 95% interval
below -5 net-cost units against both the uniform-start parent and `gated_adaptive_range+front`.
Against the parent, the estimate is only -1.05 (95% CI [-1.64, -0.46]). Although that interval
excludes zero, it misses the practical threshold by a wide margin. The second comparator clears the
threshold (-12.80, 95% CI [-15.63, -9.96]), but both contrasts were required. Per protocol, do not
run null advancement checks, tune another prior, or open the reserved real-data outcomes. The
registered lane ends here.

This is evidence against this fixed Beta(2,1) transfer under this deployment contract, not a claim
that all nonuniform start priors fail. The weighting construction is standard prior mixing and is
not novel. No real-world transfer, false-promotion guarantee, or new statistical guarantee is
established.

## Frozen run and artifact

Protocol: [`P6_BETA_START_PROTOCOL_20261107.md`](P6_BETA_START_PROTOCOL_20261107.md).

Run command:

```bash
uv run python scripts/sota_sprint/screen.py --kind synthetic \
  --regimes F1_late_1200,F1_late_800,W_late_1000,S_late_1500,F0_better,F3_reversal_800,S_reversal_400 \
  --policies P6_LRMD_Beta20,P6_LRMD_U,M_LRMD_SUI,gated_deployment,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,SMCS+retain-incumbent,choe_ramdas_eb+front,xu_acquisition_only,rmm:gated_deployment+RMM,E_srr:gated_deployment,E_srrSR:gated_deployment,E_glr:gated_adaptive_range,P7s_settled,QSG,qiu_delayed_movement,model_selector_causal,cams_adapter,CONTROL_never_switch \
  --seeds 100 --seed-base 2026110714 --workers 6 \
  --out outputs/sprint2/P6_Beta20_fresh_20261107
```

The run completed 700 jobs (100 paired seeds × 7 cells; 14,700 policy records) in 496.9 seconds.
Contract: horizon 2,000, pathwise query budget 200, label cost 0.05, switch cost 5, alpha 0.05.
Source hashes and the exact code revision are in the raw run manifest. Raw outputs are intentionally
kept under the ignored `outputs/` tree and are not committed:

- `outputs/sprint2/P6_Beta20_fresh_20261107/manifest.json`
- `outputs/sprint2/P6_Beta20_fresh_20261107/records.jsonl`

Paired intervals below are two-sided t intervals over the 100 shared episode seeds. The registered
seed block pairs methods within each regime. Costs are lower-is-better. These are synthetic
simulator results, not independent real-data confirmation.

## Primary and adverse results

| Regime | Candidate net | Candidate loss | Labels | Switches | Promoted episodes | Rollbacks | Mean first promotion, promoted episodes only | Δ vs P6 uniform (95% CI) | Δ vs gated adaptive range + front (95% CI) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F1 late 1200 (primary) | 373.68 | 359.74 | 199.80 | 0.79 | 79/100 | 0.00 | 1773.35 | -1.05 [-1.64, -0.46] | -12.80 [-15.63, -9.96] |
| F1 late 800 | 381.30 | 367.32 | 199.61 | 0.80 | 80/100 | 0.00 | 1608.01 | 0.77 [-0.74, 2.28] | -19.61 [-23.43, -15.79] |
| W late 1000 | 397.86 | 384.17 | 199.72 | 0.74 | 74/100 | 0.00 | 1688.62 | -0.27 [-0.76, 0.22] | -18.30 [-22.37, -14.24] |
| S late 1500 | 365.21 | 353.77 | 199.71 | 0.29 | 29/100 | 0.00 | 1935.24 | 0.09 [-0.32, 0.50] | 0.63 [-0.17, 1.43] |
| F0 better | 405.99 | 392.31 | 199.63 | 0.74 | 74/100 | 0.00 | 1439.70 | 16.94 [12.71, 21.17] | 43.27 [35.43, 51.11] |
| F3 reversal 800 | 380.73 | 368.30 | 199.67 | 0.49 | 31/100 | 0.18 | 743.19 | -8.35 [-14.27, -2.43] | -43.68 [-52.16, -35.19] |
| S reversal 400 | 325.41 | 315.12 | 199.80 | 0.06 | 3/100 | 0.03 | 441.33 | -2.42 [-5.54, 0.70] | -76.25 [-88.26, -64.25] |

The candidate used almost the entire label budget in every cell. On the primary target it promoted
in 79% of episodes; among those episodes, the mean first promotion was at event 1,773. It improved the target against the
published certificate-policy reference, but the fixed Beta weighting barely changed outcomes
relative to its own uniform-start parent. This is not sufficient evidence that the weighting itself
creates a useful scoped advantage. The same transfer was materially harmful in `F0_better` and
unfavorable against uniform P6 in the earlier `F1_late_800` and `F0_better` cells; the reversal cells
do not rescue the failed primary criterion.

On the primary cell, the candidate mean net cost ranked fourth among the 21 registered methods:
`E_srrSR:gated_deployment` 348.79, `qiu_delayed_movement` 350.37,
`E_srr:gated_deployment` 358.66, then `P6_LRMD_Beta20` 373.68. Those restart methods are useful
references but have different published guarantee scopes; their empirical ranking does not change
the frozen advancement rule. `xu_acquisition_only` remains only an acquisition adapter, not Xu et
al.'s published certificate.

## Completeness and limitation

The registered null checks (`F0_null`, `F5_dep_null_r8`, `F5_dep_null_r95`, 1,000 seeds) were not
run because the protocol's economic advancement gate failed. No reserved real-data outcomes were
opened. The screen supports a scoped negative result: this fixed reweighting does not provide the
required incremental economic advantage over uniform P6 under the declared late-improvement
contract. It does not diagnose the underlying late-improvement or rollback mechanisms, and it does
not satisfy independent real-world validation.

## Reproducibility and repository state

Candidate code and protocol were committed before the run as `4dd18999cb9c4b14609e142fe8a34ee6610caf5f`
on `codex/scoped-late-prior-followup`. A repository-wide CI workflow failed at Ruff because of
pre-existing lint findings across the repository; changed-file Ruff, the focused 41-test suite, and
`git diff --check` passed before the run. The run's raw manifest binds its source hashes to that
revision. The analysis used the same paired seed/episode outcomes from `records.jsonl`.
