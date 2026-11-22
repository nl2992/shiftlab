# F3 real-data screen over 100 public time-ordered streams (protocol, locked 2026-11-17)

Status: written before any stream in this screen was built or any arm was run on it.

## Purpose

Count how many public, chronologically ordered streams support the F3 shield under the frozen
arms of `configs/paper3/f3_confirmation_arms_v1.json`, using the construction of
`scripts/sota_sprint/fresh_real.py`. Every built stream is tallied; none is dropped after results.

## Candidate pool (fixed, 100 streams)

Excluded: the 14 streams of the earlier F3 real-stream study and any dataset derived from them
(e.g. the Beijing city file of UCI 394 duplicates `beijing_pm25`).

| group | source | streams | label | delay (events) |
|---|---|---|---|---|
| forex | OpenML FOREX `*-hour-Close`, one per currency pair | 32 | OpenML `Class` | 24 |
| air_multisite | UCI 501 Beijing multi-site air quality, one per station | 12 | PM2.5 > train median | 24 |
| air_cities | UCI 394 five Chinese cities, excluding Beijing | 4 | PM_US Post > train median | 24 |
| seoul_bike | UCI 560 | 1 | rented bikes > train median | 24 |
| tetouan | UCI 849, one per zone | 3 | zone consumption > train median | 144 |
| air_quality | UCI 360 | 1 | CO(GT) > train median | 24 |
| openml_events | OpenML creditcard (1597), BitcoinHeist (45037), Homesite (46857), BAF_base (46793) | 4 | dataset label | 100 |
| electricity | UCI 321, clients in file order after dropping leading zeros, first 43 with at least 30,000 rows | 43 | 15-min load > train median | 96 |

Features: dataset columns plus calendar (hour, weekday, month) where a timestamp exists; for
electricity, calendar plus the load 96 and 672 steps earlier (available given the delay).
Leakage columns (components of the target) are dropped. Models, split (incumbent on the first
15%, challenger and preprocessing on the first 30%) and episodes (2000 events, at most 20 per
stream) are exactly those of `fresh_real.py`. If a source cannot be built (download or parse
failure, fewer than one episode), it is recorded as unbuildable with the reason.

## Arms, conditions, seeds

Arms: never, wald_cut, cusum, gate_wald, cusum_rb_h8, stoploss_h14, f3_pi1_h14, f3v2d_h14,
f3_pi1_h50, f3v2d_h50 (budgets R = 2k + h, k = 5). Conditions: clean, dropout_adverse,
delay_adverse (as `real_streams.py`). Policy seeds: 5 per episode from the dev block starting at
offset 61000. T = 2000, B = 200, c_q = .05. The confirmation block and sealed groups are not used.

## Support criterion (per stream)

A stream supports the shield if both hold:

- S1 (safety): every shield arm has zero runs above its own budget in all three conditions.
- S2 (utility): on clean feedback, the better of f3_pi1_h50 and f3v2d_h50 has mean J below never
  switching.

Also recorded, not part of the criterion: whether any comparator exceeded R = 24 in any
condition, the exposure ratio x, and mean J of every arm.

## Reporting

The tally is reported over every stream in the pool: supported / not supported / unbuildable,
overall and by group. Results are development evidence, not confirmation.
