# Calibrated restart detector on Failure Atlas late-improvement regimes

**Status:** fresh-seed development screen, not confirmation and not a new-method claim. Alpha is fixed at 0.0005 from the independent F0-null calibration/evaluation recorded in `srr_any_false_calibration_20261106/`; no candidate hyperparameter is retuned here.

## Question and operating region

Does the empirically calibrated conventional `E_srrSR:gated_deployment` baseline recover late challenger gains under the Failure Atlas F1 regimes, where evidence from before the change can delay promotion? The primary cell is `F1_late_800`; `F1_late_1200` measures a later-change boundary. Regime truth is evaluator-only.

The earlier calibration used the correct iid conditional null, fixed horizon 2,000, delay 100, label budget 200, label price 0.05 and switch cost 5. Comparisons reuse these exact conditions and the same generated paired-loss stream for each seed.

## Frozen comparator panel and criteria

Candidate: `E_srrSR:gated_deployment`, alpha 0.0005. References at alpha 0.05: never-switch; corrected Gated adaptive-range and front-loaded hosts; DISCERN-style and SMCS certificate ports; E_swcert; E_rb; matched-host RMM; canonical PFA-SR on adaptive-range and deployment hosts; and Qiu/Gong benchmark-inspired paid-feedback ports. Source fidelity status is in `docs/sprint2/SOTA_BENCHMARK_AUDIT.md`; Qiu/Gong are not author-native implementations or guarantee reproductions.

Use 100 fresh paired seeds at seed base `7110601103`, fixed across all cells and policies. Primary development gate on `F1_late_800`: candidate must save at least 5 net-cost units with a two-sided paired 95% t interval entirely below zero against each of Qiu, Gong, PFA-SR adaptive-range, Gated+front and never-switch. The candidate's `F0_null` screen must have a one-sided 95% Wilson upper bound for any promotion ≤0.05. Report all other prespecified methods and cells, including `F3_reversal_800` as a known adverse regime; do not conceal trade-offs or promote an application beyond this late-improvement operating region. This screen can only justify a separate frozen confirmation if all primary criteria pass.

Report predictive loss, requested labels and their cost, switches and their cost, promotion/rollback counts and timing, net cost, paired contrasts, null error, and exact manifests/hashes. No real or locked dataset is opened in this development screen.

## Reproduction commands

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F1_late_800,F1_late_1200,F0_null,F0_better,F3_reversal_800 --policies E_srrSR:gated_deployment --seeds 100 --seed-base 7110601103 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_late_improvement_20261106/candidate
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F1_late_800,F1_late_1200,F0_null,F0_better,F3_reversal_800 --policies CONTROL_never_switch,gated_adaptive_range,gated_adaptive_range+front,discern_style,SMCS+retain-incumbent,E_swcert,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,PFA-SR:gated_deployment,PFA-SR:gated_adaptive_range,qiu_delayed_movement,gong_zhang_paid_obs --seeds 100 --seed-base 7110601103 --workers 4 --alpha 0.05 --out research/scoped_method/pilots/srr_late_improvement_20261106/references
```
