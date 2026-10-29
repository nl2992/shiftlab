# R2: DEV measurements of the two frozen real-data tasks (Lane B)

**Date:** 2026-10-29. **Gate:** R2, revised for Amendments A-B2, A-R3 and A-R3b (see the end of
`R1_task_specs.md`). **Status:** development windows only; descriptive. Nothing here is a result, an
eligibility claim for confirmation, or a statement about any monitor's merit. Earlier versions of
this document (UTC-day OPSD rounds, raw-return public features, fees inside Binance `Z`) are
superseded.

**Windows touched.** OPSD UTC 2014-12-31T23:00 (local 2015-01-01) through local 2019-12-30
(train local 2015-16, penalty selection local 2017, development local 2018-01-01..2019-12-30).
Binance ETHUSDT 1h 2025-01..2025-12. **Not touched:** OPSD from local 2020-01-01 (UTC
2019-12-31T23:00), Binance 2026. Guard: `HoldoutAccessError` in `src/shiftlab/real_tasks/__init__.py`.
The OPSD loader refuses a later cutoff before opening the file and compares only the 19-character
timestamp prefix of each raw line; a line at or past the cutoff is never given to the CSV parser. The
Binance loader refuses any month `>= 2026-01` before opening any zip. Builders re-check every series,
window end and table end. Tests (`tests/test_real_tasks.py` and the v2 contract tests; 108 pass with `test_contract.py`) cover
the guard, clocks, DST lags, public-information contract, missing data, embargo, release sentinel,
bounds, determinism and `DelayedHT`; ruff clean.

Code: `src/shiftlab/real_tasks/{__init__,opsd_reserve,binance_momentum,r2_dev_measurements}.py`.
Reproduce: `python -m shiftlab.real_tasks.r2_dev_measurements --out R2_dev_measurements.json`
(about 20 minutes, almost all of it the 200-stream harness smoke). Aggregates are in
`R2_dev_measurements.json`. No data values appear in this document.

## What the code enforces

- **Public events carry calendar fields only.** `x` is a pure function of the round time (OPSD: day of
  week, two annual harmonics, local hours in the day; Binance: day of week, hour sin/cos). Tests
  scramble all outcomes and forecasts and check that `x`, round times and decision times are
  unchanged; only the actions (a deliberate public channel, computed from public data) react.
- **Label timing.** A label reaches the actions of no earlier round than its release round (tested by
  perturbing a day's actual load and a bar's close). The OPSD `L(D-1, 07:00)` feature is removed
  (A-R3b), so there is no earlier use. For each round near the four DST changes of 2018-19,
  perturbing every load of local day >= D-1 leaves all actions of rounds <= D unchanged.
- **OPSD (A.2/A.3 with A-R3).** Local-day rounds (23/24/25 hours), decision time 10:00 local D-1,
  labels at local day end + 1 h (`release_round` offset 2 on ordinary days). 24 ridge models by local
  clock hour (14 features: lags by local day and slot 2, 3 and 7 days earlier, each masked unless its
  source day was released strictly before the decision; weekday one-hot; annual harmonics), trained on local 2015-16, penalty chosen from {1,10,100,1000} on
  embargoed local 2017, then frozen (chosen 1.0, the grid minimum; the 2017 MSE rises monotonically
  with the penalty, so the optimum may lie below the pre-declared grid). Rolling `tau_D` over local
  days D-365..D-2. Loss = daily cost / 125.
- **Binance (B.2 as amended).** Positions from 24- and 168-bar momentum signs. `P = p r_{t+1}`,
  `l = 0.5(1 - clip(P/0.10, -1, 1))`, `Z = l_inc - l_cand` (no fee). Imposed `k = f/(2*0.10)` from the
  fee argument (0.005 at f = 0.001). Standalone turnover is a labelled diagnostic, not k. Decision =
  bar open + 1 h; label at the next boundary (d = 1); archived microsecond close stamps preserved.
- **Contract mapping.** `deployed_action` = incumbent, `reference_action` = candidate, `Z > 0` means
  the incumbent is worse. `EvaluatorOutcomes` (losses, `Z`, availability time, release round,
  `label_observed`) is separate from `PublicRounds`.
- **Release sentinel.** Labels never released in-stream are `UNRELEASED` and never delivered: every
  delivered OPSD label has d = 2 (2 terminal labels unreleased), every delivered Binance label d = 1
  (1 unreleased).
- **Sensitivities implemented, not run:** `label_slack_days=1` (d=3), `fixed_tau`.

## Counts (reported before outcome analysis)

| Block | Scheduled | Rounds | Notes |
|---|---|---|---|
| OPSD validation, local 2017 (penalty only) | 365 days | 364 | 1 purged by the embargo (2017-12-31); 0 unusable, 0 missing labels |
| OPSD development, local 2018-19 | 730 days | 729 | 1 purged (2019-12-31); 1 round unusable at decision time (missing incumbent value, no policy pair, no label); 0 further missing labels; 2 days of 23 hours and 2 of 25 hours |
| Binance 2025 | 8,760 bars | 8,590 | first 169 bars (warm-up including `p_{t-1}`), last bar (its label is the locked 2026-01 close); 0 clipped policy-bars |

## Disagreement, run lengths, paired loss (DEV, labelled rounds)

| | OPSD dev (729 rounds) | Binance dev (8,590 rounds) |
|---|---|---|
| Disagreement rate | 0.221 | 0.399 |
| Disagreement rounds | 161 | 3,428 |
| Runs of consecutive disagreement rounds | 53 | 554 |
| Run length mean / median / p90 / max | 3.04 / 3 / 5 / 5 | 6.19 / 2 / 17.7 / 62 |
| Mean run if disagreements were iid at the same rate | 1.28 | 1.66 |
| P(disagree at t given disagree at t-1) | 0.671 | 0.838 |
| Share of disagreement rounds in runs >= 3 / >= 10 | 0.739 / 0 | 0.883 / 0.653 |
| Mean paired loss Z, disagreement rounds | 0.0061 | 0.00135 |
| SD of Z, disagreement rounds | 0.139 | 0.0366 |
| Share of disagreement rounds with Z > 0 / Z < 0 | 0.478 / 0.516 | 0.529 / 0.470 |
| Mean Z on disagreement rounds, first half / second half | -0.052 / +0.064 | 0.00223 / 0.00048 |
| Range of Z | [-0.344, 0.480] | [-0.478, 0.222] |
| Mean Z over all labelled rounds | 0.0013 | 0.00054 |
| Agreement rounds with Z != 0 | 0 | 0 |
| Diagnostic standalone position switches, incumbent / candidate (not k) | n/a | 859 / 342 |

**Bursty or not.** OPSD: clustered but short. Runs are 2-3 times longer than iid at the same rate and
never exceed 5 consecutive days (a workweek-sized block); none reaches 10. Binance: dense with long
runs, rate close to the 0.38 back-of-envelope in B.5; median run 2 but 65% of disagreement rounds sit
in runs of 10 or more, longest 62 bars. Not the sparse-burst process of the toy model.

**Informativeness rule (A.7).** OPSD dev disagreement share 22.1% is inside [2%, 60%]: **informative
by the frozen rule**. This says nothing about harm. The negative-then-positive half-split of OPSD mean
Z is descriptive, not a test (161 serially dependent rounds).

**Is Z a function of the public stream? (disagreement rounds with labels)**

| Key | OPSD | Binance |
|---|---|---|
| Full key (x rounded + actions at t and 3 previous rounds): keys / repeated keys / repeated keys with varying Z | 161 / 0 / 0 (all unique) | 1,349 / 489 / 489 |
| Coarse key (differing units and action bit counts): keys / repeated / repeated with varying Z | 97 / 36 / 25 | 2 / 2 / 2 |

Z varies inside every repeated Binance key and inside 25 of 36 repeated OPSD coarse keys, so the
public stream does not determine Z. This is a measurement on one development sample, not a proof, and
the actions still carry indirect information about earlier outcomes from their release onward
(disclosed in A-R3 item 1).

## Contract-harness smoke (descriptive; not a result)

Settings, none from R1 (declared here): alpha 0.05, epsilon 0, `cost_bound` 1; 200 coin streams per
monitor (seeds 20261028+s, smoke only); one label = one price unit, so the budget is `B x rounds`
labels; pacer seeded from past data only (OPSD: the embargoed 2017 rounds; Binance: the first 720
development rounds, then excluded from the monitored stream). OPSD at primary B = 10% (72.9 labels),
Binance at B = 5% on the remaining 7,870 rounds (393.5 labels). The harness has no label delay, so
this is a d = 0 upper bound on information; it has no missing feedback (no affected disagreement
round on either task).

| Task | Monitor | Alarms (of 200) | Mean labels | Of which on agreements | Streams stopped by reserve rule | Mean max log-e (threshold 3.00) |
|---|---|---|---|---|---|---|
| OPSD | GatedHTFixed | 0 | 66.6 | 0 | 57 | 0.20 |
| OPSD | GatedHTPaced | 0 | 72.0 | 0 | 200 | 0.47 |
| OPSD | UniformHT | 0 | 69.7 | 54.7 | 117 | 0.07 |
| Binance | GatedHTFixed | 0 | 380.5 | 0 | 61 | 0.29 |
| Binance | GatedHTPaced | 0 | 392.6 | 0 | 187 | 0.29 |
| Binance | UniformHT | 0 | 386.8 | 233.5 | 120 | 0.15 |

No alarm occurred. UniformHT spends 78% (OPSD) and 60% (Binance) of its labels on agreement rounds.
This shows only that the streams, harness and baselines connect and are deterministic given the
coins; it ranks nothing and carries no power claim.

## Open items carried forward

1. **Public actions remain a channel**: policies consume unrestricted public history, the audit is
   a measurement, and unique OPSD full keys give no non-reconstructability evidence.
2. **Harness limits:** the v1 smoke here has no label delay and no missing feedback; the v2 harness
   and `DelayedHT` (missing label = increment -epsilon; out-of-order release raises) cover those, and
   validity of delayed updating is bounded by `R3_delayed_update_validity_note.md`.
3. **Not implemented:** CET/CEST string cross-check from `opsd.py` (the UTC calendar plus
   Europe/Berlin conversion is the only clock used). Zero irregular days found.
4. **Ridge grid boundary** (penalty 1.0) recorded, not changed.
5. **Ordinary risks from R1** remain: A2 revision look-ahead, A3 licence assumption, imposed costs.

## Continue / pivot / stop

**Continue to re-review and the freeze for both tasks.** (The OPSD numbers changed with the
local-slot lags of A-R3b: the candidate is now slightly weaker; the earlier positive mean was not stable.) OPSD is informative, has short clustered
disagreement blocks and a bounded `Z` whose mean on disagreement rounds is close to zero (0.006, sd 0.139; descriptive). Runs of at
most 5 days mean "burst" there is a workweek effect. Binance is dense with long runs and a near-zero,
noisy `Z`, so a net-gain test will be hard. No holdout was opened.
