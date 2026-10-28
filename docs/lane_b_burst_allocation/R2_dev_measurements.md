# R2: DEV measurements of the two frozen real-data tasks (Lane B)

**Date:** 2026-10-28. **Gate:** R2. **Status:** development windows only; descriptive. Nothing here is a
result, an eligibility claim for confirmation, or a statement about any monitor's merit.

**Windows touched.** OPSD UTC 2015-01-01..2019-12-31 (train 2015-16, penalty selection 2017,
development 2018-19). Binance ETHUSDT 1h 2025-01..2025-12. **Not touched:** OPSD 2020, Binance 2026.
The guard is in code (`HoldoutAccessError`, `src/shiftlab/real_tasks/__init__.py`). The OPSD loader
refuses `end >= 2020-01-01` before opening the file and stops reading at the first row with a
timestamp at or past the cutoff (only that row's timestamp prefix is compared; its values are never
parsed or stored). The Binance loader refuses any month `>= 2026-01` before opening any zip. The
builders re-check every series and window end. Tests in `tests/test_real_tasks.py` cover the holdout
guard (including a loader run on a file whose 2020 rows hold unparseable text), clocks and
availability by perturbation, bounds and determinism: 21 tests pass, ruff clean.

Code: `src/shiftlab/real_tasks/{__init__,opsd_reserve,binance_momentum,r2_dev_measurements}.py`.
Reproduce: `python -m shiftlab.real_tasks.r2_dev_measurements --out R2_dev_measurements.json`
(about 20 minutes, almost all of it the 200-stream harness smoke). Aggregates are in
`R2_dev_measurements.json`. No data values appear in this document.

## Implementation notes (what the code enforces)

- **OPSD (spec A).** 24 per-hour-of-day ridge models, closed form, train-only standardisation, 15
  features (lags 2, 3, 7 days; `L(D-1, 07:00)`; day-of-week one-hot; two annual harmonics; no holiday,
  no weather, no ENTSO-E forecast value). Fitted on 2015-2016, penalty from {1,10,100,1000} by 2017
  validation MSE, then frozen. The chosen penalty is 1.0, the grid minimum, and the 2017 MSE rises
  monotonically with the penalty, so the optimum may lie below the pre-declared grid. That is recorded,
  not changed. Rolling `tau_D` is the 0.90 quantile of hourly actuals over days D-365..D-2 (364 days),
  used for both policies and both losses. Round = delivery day; action = 24-bit mask; loss = daily
  cost/120. Decision time `T_D` = D-1 10:00 UTC; label available D+1 01:00; `release_round` = first
  round whose decision time is at or after that.
- **Binance (spec B).** Positions `p = 1{ln(C_t/C_{t-m}) > 0}`, m = 24 (incumbent) and 168 (candidate),
  closes only. `P_a(t) = p_a(t) r_{t+1} - f |p_a(t) - p_a(t-1)|`, `l = 0.5(1 - clip(P/0.10, -1, 1))`,
  f = 0.001. Decision time = bar close (`open + 1 h - 1 ms`); the label is the next bar's close, which
  is the next round's decision instant, so d = 1 by construction.
- **Contract mapping.** `deployed_action` = incumbent, `reference_action` = candidate, so `Z > 0`
  means the incumbent is worse. `PublicRounds` holds time, features, both actions and the
  disagreement count. The evaluator-side `EvaluatorOutcomes` (losses, `Z`, label availability time,
  release round) is a separate object. `RealTask.public_events()` yields contract `PublicEvent`s.
  Imposed `CostParams` (budget, c and k grids from R1) ride on the task.
- **Sensitivities implemented but not run:** `label_slack_days=1` (d=3), `drop_lag07`, `fixed_tau`.

## Counts and exclusions (reported before outcome analysis)

| Block | Calendar days / bars | Rounds | Excluded |
|---|---|---|---|
| OPSD validation 2017 (penalty only) | 365 | 365 | 0 |
| OPSD development 2018-19 | 730 | 728 | 2 (missing actual or incumbent value); 0 calendar-irregular, 0 candidate-feature, 0 tau-window |
| Binance 2025 | 8,760 bars | 8,590 | first 169 bars (warm-up including `p_{t-1}`), last bar (its label is the locked 2026-01 close); 0 clipped policy-bars at the 0.10 scale |

## Disagreement, run lengths, paired loss (DEV)

| | OPSD dev (728 rounds) | Binance dev (8,590 rounds) |
|---|---|---|
| Disagreement rate | 0.217 | 0.399 |
| Disagreement rounds | 158 | 3,428 |
| Runs of consecutive disagreement rounds | 54 | 554 |
| Run length mean / median / p90 / max | 2.93 / 3 / 5 / 5 | 6.19 / 2 / 17.7 / 62 |
| Mean run if disagreements were iid at the same rate | 1.28 | 1.66 |
| P(disagree at t given disagree at t-1) | 0.658 | 0.838 |
| Share of disagreement rounds in runs >= 3 / >= 10 | 0.766 / 0 | 0.883 / 0.653 |
| Mean paired loss Z, disagreement rounds | 0.0332 | 0.00174 |
| SD of Z, disagreement rounds | 0.147 | 0.0367 |
| Share of disagreement rounds with Z > 0 / Z < 0 | 0.563 / 0.424 | 0.537 / 0.463 |
| Mean Z on disagreement rounds, first half / second half | -0.042 / +0.109 | 0.00255 / 0.00092 |
| Range of Z | [-0.333, 0.500] | [-0.478, 0.222] |
| Mean Z over all rounds | 0.0072 | 0.00084 |

**Bursty or not.**
- **OPSD:** clustered but short. Disagreement runs are 2-3 times longer than iid at the same rate
  and never exceed 5 consecutive days (a workweek-sized block, as A.7 anticipated). No run reaches 10.
- **Binance:** dense with long runs. The rate is close to the 0.38 back-of-envelope in B.5. The median
  run is 2, but 65% of disagreement rounds sit in runs of 10 or more, and the longest is 62 bars. This
  is not the sparse-burst process of the Lane B toy model (R1 B.7 item 7 holds).

**Informativeness rule (A.7).** OPSD dev disagreement share 21.7% lies inside [2%, 60%], so the task is
**informative by the frozen rule** and may proceed to the freeze. This says nothing about harm. The
half-split of mean Z on OPSD disagreement rounds (negative, then positive) is descriptive, not a test:
158 serially dependent rounds are not evidence of a changepoint.

## Contract-harness smoke (descriptive; not a result)

Settings, none of them from R1 (declared here): alpha 0.05, epsilon 0, `cost_bound` 1; 200 coin streams
per monitor (seeds 20261028+s, smoke only, not registry seeds); one label = one price unit, so the
budget is `B x rounds` labels; pacer seeded from past data only (OPSD: the 2017 validation rounds;
Binance: the first 720 development rounds, which are then excluded from the monitored stream). OPSD at
primary B = 10% (budget 72.8 labels); Binance at primary B = 5% on the remaining 7,870 rounds (393.5
labels).

| Task | Monitor | Alarms (of 200 streams) | Mean labels bought | Of which on agreements | Streams stopped by the reserve rule | Mean max log-e (threshold 3.00) |
|---|---|---|---|---|---|---|
| OPSD | GatedHTFixed | 0 | 67.5 | 0 | 61 | 0.75 |
| OPSD | GatedHTPaced | 0 | 72.0 | 0 | 200 | 1.15 |
| OPSD | UniformHT | 0 | 69.7 | 54.9 | 114 | 0.16 |
| Binance | GatedHTFixed | 0 | 380.5 | 0 | 61 | 0.33 |
| Binance | GatedHTPaced | 0 | 392.6 | 0 | 187 | 0.33 |
| Binance | UniformHT | 0 | 386.8 | 233.5 | 120 | 0.16 |

No alarm occurred in any stream. At epsilon = 0 the mean maximum log-e stayed at or below about 1.15
(threshold 3.0). The paced rule uses almost all of the budget before the stream ends. UniformHT spends
79% (OPSD) and 60% (Binance) of its labels on agreement rounds. This shows only that the stream,
harness and baselines connect and are deterministic given the coins. It ranks nothing and carries no
power claim: a 728-round stream with mean excess 0.03 and sd 0.15 on disagreements, at this budget, is
far from the threshold.

## Spec deviations and findings to carry forward

1. **Binance `Z` is non-zero on some agreement rounds.** The frozen B.2 loss includes each policy's own
   standalone turnover fee, so when the two positions agree at `t` but differed at `t-1`, the fees
   differ. This happens on 554 of 5,162 agreement rounds (one per disagreement-run end) with
   `|Z|` at most 0.005 (= k). It breaks the contract's Assumption L (agreement implies `Z = 0`), and the
   harness sets the paired cost of a queried agreement to 0 without reading it. The stored `paired_cost`
   is spec-exact, so the smoke sees `Z` on disagreements only. The mean `Z` over Binance agreement
   rounds is about 2.5e-4 (derived from the aggregates above): small against the disagreement mean but
   not zero. A confirmatory protocol must either accept this or revise B.2 before the freeze. OPSD
   satisfies Assumption L exactly (tested).
2. **Binance round count.** 8,590 rounds, not "about 8,592": the first round is bar 169 (so that
   `p_{t-1}` exists for the 168-bar rule) and the last is `N-2` (the final December bar's label is the
   locked January 2026 close).
3. **No label delay in the contract harness.** `run_monitor` delivers feedback in the same event, so
   the smoke is a d = 0 information upper bound. The streams carry the true delay (`release_round`:
   d = 2 days for OPSD, d = 1 for Binance) for a later delayed harness. In OPSD, offset 1 appears right
   after an excluded day because release is defined by time, not round count.
4. **Price semantics.** Contract price is one label unit (`price_range = (1, 1)`), so `B` is a label
   count. The economic query cost c and switch cost k are separate fields for net-utility accounting
   and are not charged by the harness.
5. **Declared candidate edge feature.** `L(D-1, 07:00)` makes hour 7 of day s visible to round s+1's
   features before round s's 24-hour label is released at D+1 01:00. This is spec A.2 as written. The
   tests assert it is the only early use: perturbing hour 7 changes exactly round s+1 among the
   pre-release rounds, and perturbing the other 23 hours changes none.
6. **Calendar check.** The "strictly hourly" exclusion is a global hourly-gap check with day-level
   exclusion; the CET/CEST string cross-check from `opsd.py` is not implemented (UTC is the only clock
   used). No irregular day was found.
7. **Ridge grid boundary.** The selected penalty is the grid minimum (1.0); see above.
8. **Public feature vector.** OPSD `x` = 24 incumbent forecasts, 24 candidate predictions, `tau_D`,
   `L(D-1, 07:00)`. Binance `x` = 1-, 24- and 168-bar log returns and the 24-bar return sd. All are
   computable at the decision time (tested by perturbing later data).

## Continue / pivot / stop

**Continue to the freeze for both tasks, with these cautions.** OPSD is informative, has short
clustered disagreement blocks and a bounded `Z` with a positive mean on disagreements (descriptive).
Runs of at most 5 days mean "burst" there is a workweek effect, not the long episodes of the toy model.
Binance is dense with long runs and a near-zero, noisy `Z`, so a net-gain test will be hard (R1 B.7
item 4), and deviation 1 must be decided first. No holdout was opened.
