# Disjoint-seed replication of validation-selected contextual policy

**Status:** frozen 2026-10-24 before execution. This is an independent
synthetic development replication of a candidate rule selected after an earlier
exploratory screen. It is not a real-world study or a substitute for independent
null calibration.

## Question and decision rule

Repeat the validation-selected composite-policy comparison on seeds disjoint
from both prior context-alpha screens. Preserve the original DGP, candidate
family, validation selection rule, monitor, label caps, metrics and factorial.
The replication checks whether the prior negative result persists on new random
streams; do not pool it with the overlapping screen.

For each visible context, select the candidate with the highest fully labelled
validation paired gain after the exposure-prorated switching charge, provided
that value is positive; otherwise fall back to the incumbent. Freeze this
single mapping before monitoring and test its overall history-conditional net
gain with the direct-IPW fixed-stake mixture at alpha 0.05. This is established
sample-split testing, not a novelty claim. The null is aggregate over incoming
contexts; it does not provide a separate safety guarantee per context.

## Frozen design

- Fresh seed IDs `20261100`–`20261129` (30 matched seeds per cell), disjoint
  from the nested-alpha screen (`20261025`–`20261054`) and the prior composite
  screen (`20261026`–`20261055`).
- `n=3,200`, `d=16`; latent context prevalence 0.10/0.50/0.90; target decision
  signal 0/0.05/0.10; visible-proxy error 0/0.10/0.25.
- Uniform direct-IPW querying, fixed-mixture monitor, alpha 0.05, shared
  20%/40% pathwise label caps, and unchanged candidate family.
- Primary utility is evaluator-known future net paired decision-gain at the
  40% cap. Compare composite minus pooled rank and composite minus nested
  volume, equally averaging the 18 positive-signal prevalence/error cells.
  Use matched seed-block bootstrap intervals at 97.5% per contrast.
- Continue only if both lower confidence limits exceed the registered +1
  cumulative-utility margin. Otherwise retire this fitted candidate-selection
  branch. Passing would justify a separate independent null-calibration design,
  not an efficacy claim.

All intervals remain conditional on the simulator and stated iid feedback,
known positive query propensities, bounded cost increments, and fixed policies
during the monitor. The monitor does not cover delayed labels, serial dependence,
adaptive contexts, or action-dependent outcomes. No visual is planned; any
figure must use PaperBanana.

## Reproduction

```powershell
uv run shiftlab-dive-budgeted-context-grid policy-develop `
  --seeds 30 --seed-offset 20261100 --n 3200 --d 16 --device cuda `
  --protocol docs/validation_selected_context_policy_replication_protocol.md `
  --output outputs/validation_selected_context_policy_replication_30
```
