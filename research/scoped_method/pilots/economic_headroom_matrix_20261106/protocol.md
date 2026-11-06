# Economic headroom matrix — development pilot

**Status:** Prospective development screen; not confirmation and not a novelty claim. Freeze before
launch. The four preceding mechanism classes are represented by five cells so a temporary gain can
be both economically worthwhile and unfavorable under the same event-level effect magnitude.

## Question and regime construction

Does any already implemented deploy policy have material net-cost headroom over the strongest
applicable corrected published comparator in interpretable persistent, reversal, null, or scarce-label
conditions? This phase only decides whether an implementable gap remains; no new method is proposed.

Use the existing registered synthetic generators with fresh paired seeds `seed_base=2026110626`,
`seeds=30`, horizon 2,000, label delay as encoded by each regime, label budget 200 (or 100 for the
scarce cell), label price 0.05, and switch cost 5. Cells and rationale:

| Cell | Registry key | Prospective interpretation |
|---|---|---|
| A | `F0_better` | persistent positive advantage: 0.06/event, long-run switch should repay cost |
| B-worthwhile | `F3_reversal_1200` | +0.08/event for 1,200 events, then -0.08/event; positive cumulative gain before two 5-unit switches |
| B-unfavorable | `F3_reversal_800` | same effect size, but +0.08 for 800 then -0.08 for 1,200; negative cumulative gain even before switch costs |
| C | `F0_null` | no worthwhile challenger advantage |
| D | `F6_delay400_better@B100` | persistent +0.06/event, 400-event label release delay and a 100-label hard budget |

These event-level net-gain arithmetic checks are fixed independently of policy outcomes. The synthetic
oracle may use evaluator truth only to report an upper bound; no policy receives regime labels, future
losses, or oracle paths.

## Frozen policy panel and comparisons

Run identical streams, clocks, delays, budgets, costs, and policy-visible information for:

- `CONTROL_never_switch` (feasible economic reference).
- `gated_adaptive_range`, `discern_style`, and `xu_acquisition_only` (corrected, previously
  validated certificate/acquisition adapters; Xu adapter uses the ShiftLab certificate and is not
  Xu et al.'s published certificate).
- `E_rb:gated_adaptive_range` and `rmm:gated_adaptive_range+RMM` (existing rollback/restart methods).
- `E_swcert` (existing two-sided sequential certificate with union-bound anytime alarm allocation).
- `economic_replacement` (existing cost-aware decision reference, explicitly uncertified).
- `E_srrSR:gated_deployment` (published conventional e-SR port; diagnostic only because its stated
  guarantee is ARL, not probability of any false alarm).

Primary endpoint: paired net deployment cost = predictive loss + 0.05 × requested labels + 5 ×
deployment switches. Report paired mean difference and two-sided 95% paired t interval for each method
against the per-cell comparator chosen from prior corrected evidence, without selecting a comparator
from this pilot: `xu_acquisition_only` in A and D, `CONTROL_never_switch` in both B cells and C.
Also report loss, labels, switch count, first promotion, rollback timing, and promotion frequency in C.
Report all policy means as well as the selected contrasts. The expected-truth oracle is an upper bound,
not a feasible method.

For economic headroom, require a reduction of at least 5 net-cost units with the full paired interval
below zero on at least one prespecified worthwhile cell (A, B-worthwhile, or D), with no more than 5
units mean harm to never-switch on B-unfavorable and C. This is a development gate only; 30 seeds
cannot verify a 0.05 false-promotion rate. If only an uncertified comparator or the ARL-only SR port
appears better, there is no equal-safety headroom claim.

## Run and provenance

Command, executed only after this file is committed:

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes F0_better,F3_reversal_1200,F3_reversal_800,F0_null,F6_delay400_better@B100 \
  --policies CONTROL_never_switch,gated_adaptive_range,discern_style,xu_acquisition_only,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,E_swcert,economic_replacement,E_srrSR:gated_deployment \
  --seeds 30 --seed-base 2026110626 --workers 4 \
  --out research/scoped_method/pilots/economic_headroom_matrix_20261106/run
```

The source worktree's exact commit and SHA-256 hashes for run outputs are recorded in the result
manifest after execution. No real data or locked holdout is opened in this screen.
