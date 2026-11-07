# Risk-separated E-SR rollback — development results

**Status:** falsification pilot of an existing-method setting, not confirmation. The immutable protocol is `research/scoped_method/pilots/srr_risk_separated_rollback_20261106_protocol.md`. The candidate changes only post-promotion `alpha_rb` to 0.05 while retaining global promotion alpha 0.0005. The local code addition is `E_srrSR:rb05:gated_deployment` in `scripts/sota_sprint/fam_e.py`.

## Null gate

On 1,000 fresh iid `F0_null` streams (seed base `7110601405`), the candidate promoted on 17 streams (1.7%). The one-sided 95% Wilson upper bound is 2.514%, below the frozen 5% gate. This is empirical calibration for the registered iid generator; it does not convert the SRR method's ARL statement into an anytime P(any false promotion) theorem.

- Calibration records SHA-256: `3fded55825f373ec4a07217b345e8df9282a536fe597f3392963d61056164982`
- Calibration manifest SHA-256: `93a670500956eafc7d79587ef8befc18270dccd1e8691230aee921336a5e60db`

## Matched development panel

The evaluation used 50 paired seeds per cell (seed base `7110601406`), with horizon 2,000, delay 100, hard label budget 200, label cost 0.05, switch cost 5, and global alpha 0.0005 for alpha-aware comparators. Intervals below are paired two-sided t intervals over 50 common streams.

| Cell | Candidate net | Never-switch net | Candidate−never [95% CI] | Candidate−default E-SR [95% CI] | Candidate promotions; mean rollbacks |
|---|---:|---:|---:|---:|---:|
| `F3_reversal_1200` (primary) | 366.46 | 376.62 | −10.16 [−16.71,−3.61] | −31.40 [−37.36,−25.44] | 48/50; 1.04 |
| `F3_reversal_800` (unfavorable boundary) | 355.96 | 343.74 | +12.22 [+8.48,+15.96] | −37.32 [−43.31,−31.33] | 47/50; 0.94 |
| `F0_better` | 405.26 | 423.62 | −18.36 [−27.08,−9.64] | +34.48 [+25.50,+43.46] | 45/50; 0.64 |
| `F0_null` | 366.66 | 356.66 | +10.00 [+10.00,+10.00] | 0.00 [0.00,0.00] | 0/50; 0 |

On the primary cell, predictive loss was 346.06, label expenditure 10.00, and switching expenditure 10.40. The 1.04 mean rollback count (vs 0.32 for default E-SR) corresponds to the intended faster recovery. The candidate saves at least 5 units over never-switch with its paired interval below zero, and also beats the registered certified/restart baselines. However, it exceeds the frozen maximum 5-unit harm on `F3_reversal_800` by 7.22 units: the observed harm is +12.22 with a 95% interval entirely above zero. It also loses +34.48 [25.50,43.46] to default E-SR in `F0_better`. Therefore the joint protocol gate fails, and the candidate is not advanced to independent validation.

## Interpretation and novelty

This is a useful mechanism falsification: separating the post-promotion rollback threshold from the calibrated promotion threshold can improve economics for a long initial-benefit interval by reducing time left on the wrong model. It also incurs more switches and is harmful when the initial-benefit interval is shorter or persistent, and the null still incurs the fixed 10-unit query cost. The positive primary contrast is real development evidence, but it does not override the prespecified boundary-cell failure.

The adjustment is not a defensible novel algorithm claim. `RecoveryMonitor`/E_rb already separates promotion control from a more permissive post-promotion rollback test; two-sided sequential restart and rollback procedures are established. Active change detection, delayed-feedback budget allocation, and sensing under switching costs are also prior art. See [PHASE2_HEADROOM_RESULTS.md](../../../../docs/scoped_method_research_2026-11-06/PHASE2_HEADROOM_RESULTS.md) and the primary references listed there. The result is best reported as a benchmark/case study of operating-region trade-offs.

## Reproduction and limitations

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F0_null --policies E_srrSR:rb05:gated_deployment --seeds 1000 --seed-base 7110601405 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_risk_separated_rollback_20261106/calibration
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F3_reversal_1200,F3_reversal_800,F0_better,F0_null --policies E_srrSR:rb05:gated_deployment,E_srrSR:gated_deployment,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,E_swcert,B5,CONTROL_never_switch,R:economic_stop --seeds 50 --seed-base 7110601406 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_risk_separated_rollback_20261106/evaluation
```

- Evaluation records SHA-256: `4414ee126ef6d1a2b7f3f582d71b47bccd2ba97bb75530e973fdc6efa7ba6c0b`
- Evaluation manifest SHA-256: `fa775871d00253044e8c9f6d65887a3cb1d49d2b4616cd5fd47dee83bb3eaa2d`
- Focused regression check: `uv run pytest -q tests/sprint2/test_late_real.py` — 68 passed.
- Lint check: `uv run ruff check scripts/sota_sprint/fam_e.py tests/sprint2/test_late_real.py` — passed.

The candidate is not confirmed outside these synthetic generators. No real dataset was opened under this failed gate. The null test is an empirical iid calibration, not a theorem, and the 50-stream adverse cell has nonzero sampling uncertainty despite a clear paired harm signal.
