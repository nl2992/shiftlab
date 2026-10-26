# Independent replication: adaptive PPI under fixed 12-event feedback

**Status: frozen before execution.** This is a fresh, single-cell null calibration of the exact arm that did not clear the 250-seed 12-cell calibration: `evidence_a0p025_p0p5_eventwise` with the `full_stream` monitor and outcome-independent fixed 12-event label delay. The earlier block had 5/250 escalations and a familywise one-sided upper limit of 5.66%. This replication uses disjoint seeds and does not change the method, generator, horizon, label budget, or decision threshold.

## Design

- Generate 2,000 independent IID synthetic source/target streams on CUDA when available, seeds 20420000–20421999. Each stream has 1,200 source and 2,400 target events; the expected paired cost is zero conditional on the prior event history and `epsilon=0.05`.
- Run only the frozen evidence-directed query rule and full-stream predictable-bound PPI e-process, alpha 0.05, 20% nominal query rate, and 480-request hard cap. Use a fixed 12-event delay for every queried label. Continue after alarms where budget remains, and drain all pending labels through the contiguous event prefix.
- Keep the same source-trained proxy, eventwise support bound, stake mixture, and policy settings as the previous adaptive-delay protocol. No model or threshold is selected from this replication.
- Generate the streams on CUDA and parallelize independent replay chunks across four worker processes. Replay remains the existing event-sequential implementation; worker parallelism is only across independent streams.

## Gate

The sole primary gate is the exact one-sided 95% Clopper–Pearson upper limit for the false-escalation probability. It passes when the upper limit is at most 0.05 and all 2,000 seed rows are unique, the 480-label cap holds, no labels remain pending, and every registered event prefix is fully updated. This independent block can clear only the registered fixed-delay IID null cell. It says nothing about power, other delay profiles, persistent-sign dependence, other query/monitor combinations, or real data. If the gate fails, keep the cell uncleared and do not tune on this block.

No visual is planned. Use PaperBanana for any future research visual.

## Reproduction

```powershell
uv run shiftlab-dive-delayed-ppi-fixed12-replicate --device cuda --output-dir outputs/delayed_ppi_adaptive_fixed12_replication_2000
```
