# E-SR slower-pacing evaluation amendment — 2026-11-06

**Status:** frozen after the restarted candidate passed the registered iid-null calibration. This
is a synthetic development validation of a conventional pacing configuration, not independent
confirmation or a novelty claim.

## Calibration evidence

Protocol: `RESTART_PROTOCOL_20261106.md`. Raw records:
`calibration_restart1/records.jsonl` (1,000 streams; seed base `7110601701`); manifest:
`calibration_restart1/manifest.json`. Candidate `E_srrSR:pace_k0.5:gated_deployment` promoted on
20/1,000 streams. One-sided 95% Wilson upper bound: `0.0286818`, below the frozen `0.05` gate.
Raw-record SHA-256: `6132e89f98f7e6db32e14c7ad99f7a404f57da08604b7e73b5748f918dc6b7b9`.
This is a screening result under the registered iid `F0_null`, not a general validity guarantee.

## Frozen evaluation

Use independent null seed base `7110601702` with 1,000 `F0_null` streams and alternative seed
base `7110601703` with 100 paired streams in each of:

- `F1_late_800` (primary late-improvement target);
- `F0_better` (persistent-alternative control);
- `F3_reversal_800` and `F3_reversal_1200` (adverse reversal diagnostics).

Frozen panel, on identical generated streams and cost contract: candidate;
`E_srrSR:gated_deployment` (primary same-host ablation); `PFA-SR:gated_deployment`;
`rmm:gated_deployment+RMM`; `E_rb:gated_deployment`; `E_swcert`;
`gated_adaptive_range+front`; `qiu_delayed_movement`; `gong_zhang_paid_obs`; and
`CONTROL_never_switch`. Qiu and Gong are common-contract ports, not author-native replications or
equal-safety controls. Preserve each method's stated guarantee; do not equate ARL, nominal alpha,
and familywise error.

Horizon `T=2000`, pathwise budget `B=200`, label price `0.05`, switch cost `5`, delay `100`, and
global alpha `0.0005`. The primary endpoint is net cost = predictive loss + label expenditure +
switching expenditure. Report those components, promotions/rollbacks, first-promotion and
rollback times, labels used/left, and paired 95% intervals for each contrast. Report all cells.

The existing gate is conjunctive: on `F1_late_800`, candidate savings must be at least 5 units
per 1,000 events with paired intervals below zero against default E-SR and every applicable
stronger certified/restart comparator in the panel. On the independent `F0_null`, the one-sided
95% Wilson upper bound for any promotion must be at most `0.05`. On `F0_better` and both reversal
cells, excess cost versus both never-switch and default E-SR must not exceed 5 units per 1,000
events. If any gate fails, stop this candidate without retuning `k`, alpha, timing, or operating
cells. A pass is only permission to formulate a separate real-data replay protocol; it does not
establish novelty or independent transfer.

## Commands

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null \
  --policies E_srrSR:pace_k0.5:gated_deployment \
  --seeds 1000 --seed-base 7110601702 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_tail_pacing_20261106/evaluation_null_restart1

PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes F1_late_800,F0_better,F3_reversal_800,F3_reversal_1200 \
  --policies 'E_srrSR:pace_k0.5:gated_deployment,E_srrSR:gated_deployment,PFA-SR:gated_deployment,rmm:gated_deployment+RMM,E_rb:gated_deployment,E_swcert,gated_adaptive_range+front,qiu_delayed_movement,gong_zhang_paid_obs,CONTROL_never_switch' \
  --seeds 100 --seed-base 7110601703 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_tail_pacing_20261106/evaluation_alternatives_restart1
```

No evaluation outcome was opened when this amendment was committed.
