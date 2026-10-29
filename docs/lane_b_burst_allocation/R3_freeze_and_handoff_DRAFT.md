# R3: freeze and handoff for the real tasks (DRAFT, not frozen)

**Status: draft, 2026-10-29.** Freezing waits on the Codex pre-freeze recheck of Amendment A-R3, which
was blocked by Codex's usage limit at tick 16. Nothing here is frozen, and neither holdout has been
opened.

## Freeze contents (to be hashed with `shiftlab.freeze.write_freeze`)

The protocol is `docs/lane_b_burst_allocation/R1_task_specs.md`, including amendments A-B2, A-R3
and the hour-07 lead decision. The frozen files are:

- `src/shiftlab/real_tasks/__init__.py`, `opsd_reserve.py`, `binance_momentum.py`,
  `r2_dev_measurements.py`
- `src/shiftlab/contract/interface.py`, `harness.py`
- `src/shiftlab/data/real/binance.py`, `src/shiftlab/freeze.py`
- `tests/test_real_tasks.py`
- `docs/lane_b_burst_allocation/R1b_verified_refs_and_assumptions.md`
- `configs/seed_registry.yaml`

Raw-data pins are recorded in the protocol, not hashed in Git:

- OPSD `data/raw/opsd/2020-10-06/hourly.csv`, with its receipt SHA-256;
- the 21 Binance ETHUSDT 1h zips, with their receipts.

## What Lane A gets

| Task | Information contract | Holdout | Supports | Does not support |
|---|---|---|---|---|
| OPSD reserve (primary) | Label-limited auditor: calendar `x`, the two actions, disagreement, price; paired reserve-loss `Z` released 2 local days later; missing labels are missing feedback | 2020-01-01 to 2020-09-30 (Berlin), opened once | Retrospective reserve-loss replay of budgeted, delayed monitors and switching rules under declared clocks and imposed costs | Anytime-validity calibration, causal onset, economic certification, profitability |
| Binance momentum (secondary) | Same contract; gross clipped signal-loss `Z` released after 1 bar; switch cost `k = f/(2·0.10)` | 2026-01 to 2026-09, opened once | Clipped signal-loss comparisons under idealised execution | The same, plus market impact and execution realism |

## Known limitations to carry forward

- **Labels are free in reality.** The budget is an imposed review capacity.
- **OPSD values may be revisions**, and the licence is an assumption.
- **The 2020 holdout was not chosen blind.** The disturbance is public knowledge.
- **The v1 harness lacks label delay and missing feedback.** Lane A's evaluator must add the declared
  delays before any delayed-switching claim.
- **On development data Binance has near-zero mean `Z`, and the smoke run produced no alarms**, so a
  detectable effect is unlikely.

## Opening rule

Each holdout opens once, through a guarded `locked` mode that requires a passing freeze check and
writes an `O_EXCL` marker, as E4 does. Lane A, or this lane, may open a holdout only after its own
method protocol is frozen.
