# Fixed-alpha E-SR reversal screen — results

**Status:** development falsification of an existing method, not confirmation or a new-method claim. Frozen protocol: `research/scoped_method/pilots/srr_reversal_20261106_protocol.md`.

## Null calibration gate

The unchanged `E_srrSR:gated_deployment` at global alpha 0.0005 was run on 1,000 fresh iid `F0_null` streams (seed base `7110601401`, horizon 2,000, label budget 200, delay 100). It promoted on 18/1,000 streams (1.8%); one-sided 95% Wilson upper bound is 2.6328%, below the frozen 5% gate. This is empirical evidence on the registered iid null generator, not an anytime guarantee for E-SR.

- Raw calibration SHA-256: `2caffad305b53b9cb06d318755f4ea39ba9b24ed1600d02e2d344dfb9b1e602b`
- Manifest SHA-256: `ef2843d93f4503b0eea23c37b9d6074122dc1b0e225b45ffdb59e98c4adb5d19`

## Fresh 30-stream development evaluation

The evaluation used 30 paired streams/cell (seed base `7110601402`), four cells, and the same 2,000 horizon, 200-label budget, 100-event delay, label price 0.05, and switch cost 5. Global alpha 0.0005 was passed to all alpha-aware methods. Costs below are loss + label spend + switch spend. Paired intervals are two-sided t intervals over 30 shared streams.

| Regime | Candidate net cost | Never-switch | Candidate minus never [95% CI] | E_swcert | Candidate minus E_swcert [95% CI] | Candidate promotions / rollbacks |
|---|---:|---:|---:|---:|---:|---:|
| `F3_reversal_1200` | 389.60 | 366.43 | +23.17 [+16.41,+29.93] | 387.98 | +1.63 [−9.83,+13.08] | 29/30; 0.50 mean rollback |
| `F3_reversal_800` | 383.30 | 341.47 | +41.83 [+34.14,+49.53] | 362.15 | +21.15 [+7.83,+34.47] | 27/30; 0.77 mean rollback |
| `F0_better` | 365.83 | 419.80 | −53.97 [−64.74,−43.20] | 424.55 | −58.71 [−72.87,−44.56] | 30/30; 0 rollbacks |
| `F0_null` | 373.70 | 363.97 | +9.73 [+9.19,+10.28] | 373.95 | −0.25 [−0.80,+0.29] | 1/30; 0 rollbacks |

On the primary worthwhile reversal, predictive loss was 372.27, label expenditure 10.00, and switching expenditure 7.33, yielding net cost 389.60. Its mean first promotion was event 532.8 among promoters. The candidate failed the frozen economic gate: it did not save at least five units over never-switch and was materially worse on the adverse reversal. The positive persistent-alternative result does not undo the reversal failure or establish a universal advantage.

This indicates the published E-SR restart method at this fixed empirically qualified iid-null operating point does not close the reversal gap. `E_swcert`, E_rb, RMM and PFA-SR also do not beat never-switch in this cell at the matched global alpha. `economic_replacement` is uncertified and not a risk-qualified resolution. The omitted `R:economic_stop` baseline is being checked in a separate supplemental exploratory panel specified before its outcomes; no novel-method conclusion should be made until that comparison is recorded.

## Reproduction and provenance

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F0_null --policies E_srrSR:gated_deployment --seeds 1000 --seed-base 7110601401 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_reversal_20261106/calibration
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F3_reversal_1200,F3_reversal_800,F0_better,F0_null --policies CONTROL_never_switch,E_swcert,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,PFA-SR:gated_adaptive_range,economic_replacement,E_srrSR:gated_deployment --seeds 30 --seed-base 7110601402 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_reversal_20261106/evaluation
```

- Evaluation records SHA-256: `d76d5c0146eb25dc1f0d5b7c94357b7c49a9e90fee51f22013b8734869552659`
- Evaluation manifest SHA-256: `86142721aeed8f23ce54d72d9b08ff0d8ecb16153c34a2d4df36677d9cc4d0bc`

The run is development evidence. The fixed-alpha calibration was opened before alternatives and passed; the target outcomes were opened once under the frozen protocol. No real dataset or locked source was accessed.
