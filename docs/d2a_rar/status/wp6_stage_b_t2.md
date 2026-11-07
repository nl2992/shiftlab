# WP6 Stage B tranche 2 status (Amendment A1; auto-generated)

Updated: 2026-11-07T21:12:23+00:00  
Ledger head: `658969ba7bf8746d8bc266b380df9fa416f013582b156a99211a846f63eb5124` (60 records, 0 suite-v2)  
Branch commit: `9763eb7479509e844064791764fa9f74c8ac97e9`

Scope file: `results/d2a_rar/stage_b/tranche2_scope.json` - 41 selected (cap 140); scope counts {"ii": 14, "i": 33}; scope (iii) Q1 evidence excluded (42 Q1 identities not run).

* phase: warming references; experiments done this launch: 0 / 41; elapsed 0.0 min
* in flight: none
* last: 
* not run this launch: {}

## Decision counts (suite v2 ledger records)

none yet

## KEEP and near-KEEP

KEEP = section 4 satisfied under A1. near-KEEP = DISCARD only through the control-cell / host-ablation / complexity / simple-control criteria: valid under its claimed null, not invalid-aggressive, and an effect label other than 'none' on its best target cell against the per-cell strongest applicable comparator. dJ = J(candidate) - J(comparator), negative = candidate better, 95% paired bootstrap CI.

None.

## Mandate Q2 stop rule (candidates vs pending_cap / fixed_schedule on target cells)

* Q2-labelled records with a v2 result: 0; candidates whose paired CI is entirely below 0 against BOTH pending_cap and fixed_schedule on at least one target cell: **0**.
* No candidate beats both simple controls on a target cell with a paired CI excluding 0. Best (most negative) dJ per candidate is listed in the full table below.

## All suite-v2 records

| candidate | method | decision | effect | best target cell (comparator) dJ [95% CI] | simple controls beaten? | validity | v1-regression |
|---|---|---|---|---|---|---|---|

Ledger: `docs/d2a_rar/registry/EXPERIMENT_LEDGER.jsonl`; log: `results/d2a_rar/stage_b/stage_b_t2_run.log`.
