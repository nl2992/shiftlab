# R3: freeze and handoff for the real tasks (DRAFT, not frozen)

**Status: ready for a task-contract freeze, 2026-10-29.** Amendment A-R3b is implemented and its
focused validation passed. The R2 development measurements were rerun after the amendments; no
holdout data were read. This freezes only the real-task contract and development evidence for a
later method-specific evaluation. It does not authorize opening either holdout.

## Freeze contents (to be hashed with `shiftlab.freeze.write_freeze`)

The protocol is `docs/lane_b_burst_allocation/R1_task_specs.md`, including amendments A-B2, A-R3,
the A-R3b correction, and the R2 disclosure. The freeze record must include at least:

- `src/shiftlab/real_tasks/__init__.py`, `opsd_reserve.py`, `binance_momentum.py`,
  `r2_dev_measurements.py`
- `src/shiftlab/real_tasks/v2_smoke.py`
- `src/shiftlab/contract/interface.py`, `harness.py`, `baselines.py`
- `src/shiftlab/contract/interface_v2.py`, `harness_v2.py`, `baselines_v2.py`
- `src/shiftlab/dive/eprocess.py`, `gated_monitor_comparison.py`, `reserve_costs.py`
- `src/shiftlab/data/real/binance.py`, `src/shiftlab/freeze.py`
- `tests/test_real_tasks.py`, `tests/test_contract.py`, `tests/test_contract_v2.py`
- `pyproject.toml`, `uv.lock`
- `docs/lane_b_burst_allocation/R1b_verified_refs_and_assumptions.md`
- `configs/seed_registry.yaml`
- `docs/lane_b_burst_allocation/R2_dev_measurements.json`
- `docs/lane_b_burst_allocation/R2_dev_measurements.md`

The freeze record itself is not yet written. Write it only after this document and the protocol
are committed, then run `shiftlab.freeze.check_freeze` against the committed tree.

Raw-data pins are recorded in the protocol, not hashed in Git:

- OPSD `data/raw/opsd/2020-10-06/hourly.csv`, with its receipt SHA-256;
- the 21 Binance ETHUSDT 1h zips, with their receipts.

## What Lane A gets

| Task | Information contract | Holdout | Supports | Does not support |
|---|---|---|---|---|
| OPSD reserve (primary) | Label-limited auditor: calendar `x`, the two actions, disagreement, price; paired reserve-loss `Z` released 2 local days later; missing labels are missing feedback | 2020-01-01 to 2020-09-30 (Berlin), opened once | Retrospective reserve-loss replay of budgeted, delayed monitors and switching rules under declared clocks and imposed costs | Anytime-validity calibration, causal onset, economic certification, profitability |
| Binance momentum (secondary) | Same contract; gross clipped signal-loss `Z` released after 1 bar; switch cost `k = f/(2·0.10)` | 2026-01 to 2026-09, opened once | Clipped signal-loss comparisons under idealised execution | The same, plus market impact and execution realism |

R2's main development findings are descriptive only. OPSD has 729 rounds, 22.1% disagreement, a
maximum disagreement run of 5 local days, and mean `Z=0.0061` on disagreement rounds (sd 0.139).
Binance has 8,590 rounds, 39.9% disagreement, maximum run 62 bars, and mean `Z=0.00135` on
disagreement rounds (sd 0.0366). The v2 harness smoke used 200 streams per monitor with no alarms;
it is a wiring check, not evidence of utility, calibration, or comparative performance. Results
and their limits are in `R2_dev_measurements.md`.

## Known limitations to carry forward

- **Labels are free in reality.** The budget is an imposed review capacity.
- **OPSD values may be revisions**, and the licence is an assumption.
- **The 2020 holdout was not chosen blind.** The disturbance is public knowledge.
- **Use contract harness v2 for delayed/missing-feedback replay.** Its delayed update claim is
  limited to fixed delay under a null valid given the full event-time history, and missing feedback
  requires the stated MAR condition; out-of-order labels are rejected. See
  `R3_delayed_update_validity_note.md`. This does not establish real-data null validity.
- **On development data Binance has near-zero mean `Z`, and the smoke run produced no alarms**, so a
  detectable effect is unlikely.
- **Policy actions are a public information channel.** The development key audit does not prove
  non-reconstructability; every method must receive the same channel and state its null relative to
  the declared filtration.
- **Evidence about the tested period does not certify current or future benefit after reversal.**
  Keep current-regime value forecasts separate from the false-promotion evidence accumulated under
  the statistical null.

## Opening rule

Neither task loader currently has an authorized locked mode: the current timestamp guards always
refuse holdout rows. Before either holdout can be read, implement and test a dedicated opening
runner that (1) verifies this task freeze and a separate, committed Lane A method freeze, (2) creates
an exclusive `O_EXCL` opening marker before any locked read, and (3) writes an immutable manifest
with the protocol/code/data hashes and exact window. Do not weaken the development loader's default
guard. A task-contract freeze alone does not permit opening; no holdout has been opened.
