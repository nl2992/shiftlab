# R1: frozen real-data task specifications (Lane B)

**Date:** 2026-10-28. **Gate:** R1. **Status:** specification only, written BEFORE any outcome-bearing
inspection. **Nothing here is a result or an eligibility claim for confirmation.**

## What was and was not looked at

Read: file lists, zip row counts per month (all 21 ETHUSDT months have complete calendars: 744, 672,
... totals 8,760 for 2025 and 6,552 for 2026-01..09, 15,312 in all), OPSD `datapackage.json` text
(field names, descriptions, `sources`, `temporal`, no `licenses` key), receipts. **No price, load,
forecast or return value was opened.** No policy action was computed. Disagreement densities below
come from rule definitions only (task A's cannot be estimated that way; see A.7).

The exposed state of the data is as in `R0_real_data_eligibility.md`: OPSD 2018 and 2019 are
descriptively exposed (train-only regressions and loss intervals); 2015-2017 and 2020-01..09 are
not. Binance has no outcome analysis in the repo beyond the one 2025-01 validation split.

## External references fetched (see `data/raw/lane_b_external_refs_2026-10-28/`, main checkout, Git-ignored)

| Item | Result | Status |
|---|---|---|
| ETHUSDT 1h 2025-01..2026-09 | 21 zips, publisher checksums verified (21/21 receipts), as supplied | verified |
| ENTSO-E day-ahead total load [6.1.B] publication rule | "D-1, at the latest 2 hours before the gate closure time of the day-ahead market in the bidding area" (ENTSO-E Transparency help centre); actual load [Reg. 543/2013 Art. 6(2)(a)]: no later than one hour after the operating period; day-ahead forecast Art. 6(2)(b): no later than two hours before day-ahead gate closure | **partially verified**: secondary text (search summary, legislation.gov.uk retained-EU copy). EUR-Lex returned an HTTP 202 WAF challenge to scripted fetch; not bypassed. No raw hash. Human confirmation against CELEX:32013R0543 Art. 6(2) required before freeze |
| Binance spot fee schedule | VIP 0 spot maker 0.100% / taker 0.100%; with BNB discount 0.075% | **unhashed, secondary**: scripted fetch got HTTP 202 WAF challenge; value read via a page summariser. A human must save the page (HTML) and record its SHA-256 before freeze. The schedule is current, not historical |

Receipts: `entsoe_load_publication_rule.receipt.json`, `binance_fee_schedule.receipt.json`. Their
`raw_page_sha256` is `null`; the stored hash is of my note file, not of the publisher page.

---

## Common contract mapping (`switching_problem_v1.md`)

Both tasks use the paired common-label contract. Round t has an action A_t in {0,1} (0 = incumbent,
1 = candidate), losses l_t(0), l_t(1) in [0,1], Z_t = l_t(0) - l_t(1), a free observable disagreement
indicator D_t (a function of the two policies' actions at decision time, never of outcomes), a query
Q_t in {0,1} that reveals both losses for round t at the start of round t+d (pending queries charged
at request), hard budget B, query cost c, switch cost k. Actions do not affect outcomes
(price-taker / no-impact in B; no market feedback in A). Labels are **free in reality in both tasks**,
so B and c are imposed (stated per task).

---

# A) OPSD German day-ahead load reserve decision (primary)

## A.1 Roles and information

- **Incumbent policy 0:** reserve decision from the published ENTSO-E day-ahead total-load forecast
  for Germany, column `DE_load_forecast_entsoe_transparency` of the OPSD 2020-10-06 snapshot
  (sha256 `6a7f2bc5...c8` per `hourly.csv.receipt.json`; the publisher checksum is **not** verified).
- **Candidate policy 1:** the same reserve rule applied to a frozen own forecast `f^C` (A.2).
- **Common outcome:** `DE_load_actual_entsoe_transparency` for the delivery hour.
- Only the first `utc_timestamp` UTC calendar is used (CET/CEST strings used only for the adapter's
  cross-check, as in `opsd.py`).

## A.2 Candidate forecaster (frozen)

- **Class:** ridge regression, one model per delivery hour-of-day (24 models, UTC hour), closed form,
  features standardised with training-window mean/sd only.
- **Target:** actual load at delivery hour h on day D.
- **Features and their availability** (decision time T_D = D-1 10:00 UTC, see A.4). Let L(d,h) be the
  actual load for UTC day d, hour h.
  1. L(D-2,h), L(D-3,h), L(D-7,h): complete days, published by D-1 01:00 UTC.
  2. L(D-1, 07:00 UTC): the latest hour whose publication (hour end + 1 h = 09:00 UTC) precedes T_D
     with a 1 h margin. Its use is a deliberate edge-of-availability feature; sensitivity in A.10.
  3. Calendar: day-of-week one-hot (7), sin/cos of day-of-year at two harmonics (4). **No holiday
     calendar** (an external dataset; omitting it is a declared weakness of the candidate).
  4. No weather, no wind/solar forecast, no price, no ENTSO-E forecast value as a feature (so the
     candidate is not a correction of the incumbent and the pair is not mechanically coupled).
- **Training window:** UTC 2015-01-01 00:00 to 2016-12-31 23:00. Ridge penalty chosen from
  {1, 10, 100, 1000} by validation MSE on UTC 2017-01-01 to 2017-12-31, then **no refit**. The model is
  frozen from 2016-12-31 on and ages through development and holdout. This is intentional: it
  makes staleness (a natural drift source) part of the task.
- Target days D whose features or target are missing are dropped from fit and from evaluation.
- Seed: none (closed form). Code and the exact feature matrix definition are frozen with the hash.

## A.3 Action rule and cost function

Adopt the repo convention in `src/shiftlab/dive/reserve_costs.py`: binary action per hour
(procure reserve = 1 when the forecast exceeds a threshold), shortfall cost 5 when actual load
exceeds the threshold and no reserve, idle cost 1 when reserve procured and actual load does not
exceed it, else 0 (`COST_SHORTFALL=5`, `COST_OVER_PROCUREMENT=1`, `TAU_QUANTILE=0.90`). **Declared
deviation:** the existing code uses one fixed tau for a whole stream (a training-window quantile).
Across 2015-2020 the load level is non-stationary (efficiency, structural change, the 2020
disturbance), so a fixed tau would make "high" days vanish or concentrate by year. Therefore

- **tau_D** = the 0.90 quantile of all hourly actual loads in the 364 complete UTC days ending at the
  last day published before T_D (days D-365 ... D-2), a predictable function of released outcomes.
  The same tau_D is used for both policies and for the loss of both policies on day D.

Hourly cost for action a and actual load y at hour h: `c_h(a) = 1{a=1,y<=tau_D} * 1
+ 1{a=0,y>tau_D} * 5`. These costs are **imposed research costs, not a tariff**; the 5:1 ratio
is inherited from the EIA conventions and is not grounded in any German procurement price.

**Round and loss.** One round = one delivery day D (24 hourly decisions made together at T_D).
`l_D(a) = (1/120) * sum_{h=0}^{23} c_h(a)`, which lies in [0,1] (max 24*5 = 120). Z_D = l_D(0)-l_D(1)
in [-1,1]; the hourly paired cost is exactly `paired_cost` in the repo. Observed-at-decision
disagreement indicator D_D = 1 if the incumbent and candidate action vectors for day D differ in at
least one hour; the count of differing hours is a secondary descriptive field.

## A.4 Clocks

| Clock | Definition | Basis |
|---|---|---|
| Event time | delivery hour start (UTC), day-round D = 00:00 UTC of D | OPSD `utc_timestamp` |
| Incumbent forecast publication | ENTSO-E deadline D-1 at most 2 h before day-ahead gate closure. Gate closure 12:00 CET gives a deadline of 10:00 CET (09:00 UTC winter, 08:00 UTC summer) | rule quoted above; partially verified |
| **Decision time T_D** | **D-1 10:00 UTC fixed year-round** (not earlier than the deadline in either season) | **declared conservative assumption**; actual per-row publication times are not in the data and the snapshot may hold later revisions |
| Actual-load availability | hour end + 1 h at the latest (Art. 6(2)(a)) | partially verified |
| Label availability for round D | day D's 24 actuals complete at D+1 01:00 UTC. That is after T_{D+1} = D 10:00 UTC, so visible first for the decision of round D+2 | derived |
| **Label delay in rounds** | **d = 2** (constant). Sensitivity d in {3} (a 24 h extra publication slack, e.g. revisions) | derived |
| Alarm reporting | an alarm raised from labels visible at T_t takes effect for round t; switching takes effect on that day's action vector. No intra-day switching | declared |

Round t's pending label is charged at request (query chosen for round t at T_t, since the queried
object is day t's realised load; the decision whether to query is made at T_t). This matches the
contract's "charged at request, visible at start of t+d".

## A.5 Windows, exclusions, forking-path declaration

| Block | UTC range | Use | Exposure |
|---|---|---|---|
| Train | 2015-01-01 .. 2016-12-31 | fit candidate | unexposed |
| Validation | 2017-01-01 .. 2017-12-31 | ridge penalty only | unexposed |
| Development | 2018-01-01 .. 2019-12-31 | algorithm development, density estimate, threshold-free smoke only | **descriptively exposed (2018, 2019)**; counts as development only |
| **Locked holdout** | **2020-01-01 .. 2020-09-30 (274 days)** | single confirmation look; opened once after the algorithm and all grids are frozen | unexposed |

Rolling tau needs 364+ days of history; for the first development day the history comes from 2017.
Holdout tau uses released actuals from 2019 and early 2020 only.

**Exclusions (declared now):** a delivery day is excluded if either series has any missing/non-finite
hour for that day, or the 364-day tau window has fewer than 90% non-missing hours, or the OPSD
timestamp calendar for the day is not strictly hourly (adapter-style check); no imputation. Excluded
days still advance the calendar clock (they are not removed from time), they simply produce no round.
No outlier removal. Exclusion counts per block are reported before any outcome analysis.

**Forking-path choice of the 2020 holdout.** Alternatives: (a) 2020-01..09 (chosen), (b) a pre-2020 block
such as 2017 (but then the validation year is lost and fit/eval order is not chronological in the
usual sense), (c) 2018/2019 (exposed). Reasons for (a): it is the only chronologically later
unexposed block in this snapshot, so it is a true out-of-sample future relative to training,
validation and development; the snapshot ends 2020-09-30 so the end date is not chosen by me. The
cost: it contains the spring-2020 demand disturbance that is public knowledge, so my choice is not
blind to a likely harmful period for the stale candidate. **I disclose that, I do not claim
the holdout was drawn without that knowledge**, and I will not select sub-windows after seeing results.
Pre-declared descriptive strata (no claims): Jan-Feb versus Mar-Sep. If a result depends on the
Jan-Feb versus Mar-Sep split only, it is reported as such.

## A.6 Imposed budget, query cost, switch cost (interpretation stated)

- **Query** = an analyst-audit of day t's realised-versus-forecast paired loss. In reality the
  actual load is public and free, so **B and c are an imposed information scarcity**, standing for
  analyst review or retraining-evaluation capacity. They do not represent a market price.
- **Budget B** as a fraction of non-excluded rounds: {5%, 10%, 25%}. Primary 10% (about 73 rounds in
  development, about 27 in holdout).
- **c** in raw cost units (1 = one idle reserve hour): {0, 1, 3}; c=0 is a sanity case. Primary 1.
  Normalised c/120.
- **k** (switch cost, reverting to the incumbent or promoting the candidate) in raw units
  {10, 25, 50}, i.e. 2-10 shortfall-hours; primary 25. It stands for the effort of validating and
  re-pointing the forecast of record. Normalised k/120. Imposed, not observed.
- All cells are fixed here; a result outside the grid is not confirmatory.

## A.7 Disagreement definition and expected density

- Per hour: actions differ iff the two forecasts lie on opposite sides of tau_D. Per day: D_D above.
- The two forecasters are a TSO model and a lagged-load ridge model, so each tracks load closely and
  disagreement requires a forecast pair straddling the 0.90 quantile. Disagreement is therefore
  **structurally confined to hours near the upper decile** (winter workday peak hours), which makes it
  concentrated and autocorrelated within a day and across consecutive workdays (a natural burst
  structure by construction, not a verified changepoint).
- **A numeric density cannot be derived from the rule definitions without values.** My prior
  expectation, labelled as a guess: a minority of days with D_D=1, mostly in cold months.
  Computing the density requires tau_D, which uses past actual loads (outcomes). **I did not compute
  it.** The development-window density (and the run-length distribution of D_D) is the first R2 task,
  on 2018-2019 only. The holdout density is not computed before the freeze. If development density
  is below 2% of days or above 60%, the task is declared uninformative and not run on the holdout.
- Disagreement alone says nothing about harm: Z_D conditional on D_D=1 is unrestricted; no
  harmfulness, onset or burst label is available, and none is inferred.

## A.8 Threats to validity

1. **Revisions/vintage:** the 2020-10-06 snapshot may contain later-revised actuals and forecasts;
   the as-published forecast at T_D is unverified. Optimistic look-ahead is possible for both series.
2. **Decision-time assumption:** T_D is a conservative declared clock, not per-row timestamps.
3. **Candidate weakness and uninformative pair:** the ridge model has no weather or holiday
   information and is frozen for years, so it may be dominated by the incumbent throughout; then
   there is no benefit regime and the task only exercises the false-switch side. Conversely, any
   candidate gain is not evidence of a better deployable model.
4. **Zone definition:** `DE` in OPSD for the early years may refer to a different bidding-zone
   aggregation than later years (the DE-AT-LU split occurred 2018-10-01; DE_LU price starts 2018-10).
   Not verified from metadata; a definitional break would affect both series' relation to the actual
   and could mimic drift. Report and treat as a threat, not a feature.
5. **2020 disturbance** (A.5), single holdout, 274 days, strong serial dependence: effective sample
   size small; bursts are few. Use calendar-block uncertainty.
6. **Rolling tau** is a modelling choice made to avoid level drift; it changes the ground truth of
   the loss over time and is not a documented procurement rule.
7. **Imposed costs** (5:1, c, k, B) drive all economic results.
8. **Licence:** the datapackage has no `licenses` field; ENTSO-E reuse terms unpinned. No
   redistribution of values; keep research-internal.
9. **Interference with Lane A's G4:** staleness and rolling tau make some "harm" a property of my
   frozen candidate, not of a pre-existing deployed-policy shift.

## A.9 Claims supportable and not

**Can support:** a replay on a real, dependent, calendar-clocked stream with a published incumbent and a
frozen candidate, a documented label-delay (d=2 rounds from the stated clock), exact budget accounting,
paired losses from a common outcome, matched-budget comparisons of allocation rules, and the
false-switch side under a real stream (the first-K clean weeks are near the null if the candidate has no
advantage, which cannot be confirmed).

**Cannot support:** application cost savings; causal harm or onset times; that disagreement bursts are
harmful; that the label is costly; real-time deployability (publication clock is declared); any
superiority claim from development tuning; general claims about forecasting practice.

## A.10 Pre-declared sensitivities (no other analyses count)

d in {2, 3}; L(D-1,07:00) feature removed; tau quantile fixed at 0.90 versus a fixed training-window
quantile (the repo's original convention, reported as a robustness row); B in {5,10,25}%, c, k grids.

## A.11 Freeze line

`SHA-256 (this file + feature/forecaster code + exclusion code + grid file, concatenated in that order): <PLACEHOLDER, to be computed at freeze>`

---

# B) Binance ETHUSDT 1h two-rule position replay (secondary)

## B.1 Roles and rules

- Spot long/flat only (no leverage, no shorting; keeps a world-realistic spot setting). Position
  p in {0,1} (fraction of a fixed notional N held in ETH).
- Let C_t be the close of bar t (decision at bar t's close). Log-return over m bars: ret_m(t) =
  ln(C_t / C_{t-m}).
- **Incumbent policy 0:** 24-bar momentum: p_t = 1 if ret_24(t) > 0, else 0.
- **Candidate policy 1:** 168-bar (7-day) momentum: p_t = 1 if ret_168(t) > 0, else 0.
- Both rules use closes only, **not outcomes of the next bar**, so actions are computable at
  decision time and the sign rule has no fitted parameter. Warm-up: the first 168 bars of the stream
  produce no round; warm-up bars may come from earlier months of the same stream.
- I deliberately did not take the momentum-versus-reversion pairing: a complement rule disagrees
  with probability 1 (trivial), and short-horizon reversal against 24-bar momentum has high
  disagreement (see B.5). A long-horizon momentum candidate has an interpretable role (slower trend
  following) and a lower disagreement rate.

## B.2 Loss and common-label assumption

- Label for round t: next-bar simple return r_{t+1} = C_{t+1}/C_t - 1.
- Position fee: fee rate f per unit traded notional per side. **Each policy's loss includes its own
  standalone turnover fee**, so losses are path-independent as the contract requires:
  `P_a(t) = p_a(t) * r_{t+1} - f * |p_a(t) - p_a(t-1)|`, and
  `l_t(a) = 0.5 * (1 - clip(P_a(t)/0.10, -1, 1))`. The scale 0.10 (10% per hour) is a declared
  clipping scale; the number of clipped bars is reported before analysis.
- **Common-label assumption (stated, not observed):** small notional; price-taker; execution at the
  bar-close price C_t; no spread, slippage, queue or market impact; full fills. One next-bar return
  scores both rules on the same event. Real fills would differ. This is an idealisation, so
  the result is a signal-quality replay, not a trading result.
- **Switch cost k:** a policy switch at round t makes the held position jump from p_{A_{t-1}} to
  p_{A_t}; the extra fee is at most f times the one-notional difference. Declare
  k = f (normalised: f/ (2*0.10) in loss units after the 0.10 scale, because l has range 1 over a P&L
  range of 0.2). It is an upper bound on the rebalance cost, charged at every A change whether or not
  the positions differ, which is conservative. The standalone-turnover fees inside l_t(a) are in
  addition and unavoidable.
- **Fee rate f:** primary 0.001 (0.100% taker/maker, VIP 0, per the fee page); sensitivity 0.00075
  (BNB discount) and 0 (sanity). Unhashed source, see references table; the current schedule is
  applied to 2025-2026 as an assumption.

## B.3 Clocks

| Clock | Definition |
|---|---|
| Event time | bar open (UTC), archived with exact calendar (open and close timestamps validated by `binance.calendar`; 2025+ microsecond precision) |
| **Decision time** | **bar t close (close time = open + 1 h - 1 ms)**, using features that need that bar's close; not the stored `event_time`, which is the bar open |
| Label availability | next bar's close = the next round's decision instant |
| **Label delay** | **exactly d = 1 round** (the label queried at round t is visible at the start of round t+1, when A_{t+1} is chosen) |
| Alarm reporting | an alarm raised at the start of round t+1 changes the position held over bar t+2; no intra-bar action |

The contract's "visible at the start of t+d" with d=1 means a query at round t is usable for the very
next decision. The simultaneity convention (release, then observe, then act) is stated and tested in R2.
Archive publication latency of the zip files is irrelevant for a replay.

## B.4 Windows and exclusions

| Block | Range (UTC) | Rounds | Exposure |
|---|---|---|---|
| Development | 2025-01 .. 2025-12 | about 8,592 after warm-up | one month (2025-01) previously processed by the repo for descriptive validation only; the rest not analysed |
| **Locked holdout** | **2026-01 .. 2026-09** | 6,552 | unexposed |

Holdout warm-up uses December 2025 closes (past). Stated alternatives and why not: using a calendar
year as holdout would need data past what exists; using 2026 as development leaves no later block;
the 9-month holdout is the entire available future, with the end date set by data availability.
Both months and splits are determined by data availability, not by outcomes, but the dev/holdout split
is calendar convenience and a regime change (2025 to 2026) is possible and not controlled.
Exclusions: any month failing the calendar check (none expected: all 21 zips have complete bar counts);
no imputation. Bars with |return| > 10% are clipped (counted), not removed.

## B.5 Disagreement definition and expected density

- D_t = 1 iff p_0(t) != p_1(t) (free at decision time; uses no outcome).
- **Expected density from rule definitions only:** under a driftless Gaussian random walk, the signs of
  ret_24 and ret_168 have correlation sqrt(24/168) = 0.378 (overlapping sums), so
  P(sign disagreement) = arccos(0.378)/pi = about 0.38. That is a back-of-envelope computation from
  the rules and a Gaussian driftless approximation; real returns are heavy-tailed, have drift and
  volatility clustering, so the realised rate will differ. **I did not compute actions on any data.**
- Consequences: disagreement is **dense (~40% of bars)**, with long runs (overlap makes D_t strongly
  autocorrelated), not the sparse rare-burst process of Lane B's toy model. Actions are computable
  on development features without outcomes (they use closes only), so the dev density and run-length
  distribution are a legitimate R2 first step; no holdout density before freeze.
- The task cannot supply an independent harm label for a burst; Z_t after fees is the only quantity.

## B.6 Imposed budget and query cost (honest interpretation)

All returns are public and arrive free. **B is an imposed review/audit capacity** (analyst-reviewed
bars or re-estimation compute) with budgets {2%, 5%, 10%} of rounds (about 170, 430, 860 per dev year;
primary 5%); c in normalised loss units {0, 0.0005, 0.002} (primary 0.0005) imposed, with no market
interpretation; a result that depends on c is not a cost-saving claim.

## B.7 Threats to validity

1. **Execution idealisation** (B.2): no spread, slippage, latency, impact; fees apply at close price.
2. **Regime change** between development (2025) and holdout (2026) unobserved by design; any single
   rule's profitability is dominated by market direction.
3. **Heavy tails and clipping**; volatility clustering violates exchangeability assumptions of bursts.
4. **Rules are trivial and highly correlated**, so both rules often agree; the switching benefit may be
   inherently tiny relative to the fee and k; this makes a net-gain test hard.
5. **Fee source unhashed**, current schedule assumed historical; maker/taker and VIP tier choice.
6. **Single asset, single exchange** (global Binance spot, ETHUSDT); one realised sample path.
7. **Dense disagreement** (~40%) differs from Lane B's sparse-burst premise; use caution transferring
   conclusions.
8. **Licence:** exchange data terms; research use, attribution retained, no redistribution of values.
9. Possible regime overlap with my own prior knowledge of pre-cutoff market events is unlikely to
   matter for signs of closes, but I have not seen the data; the holdout is also public.

## B.8 Claims supportable and not

**Can support:** acquisition-and-switching mechanics on a real, dependent, exactly clocked stream with
published switching-cost scale and delay 1; false-switch behaviour when the candidate has no benefit
(likely) and matched-budget comparison of allocation rules on a pre-frozen pair.

**Cannot support:** trading profitability; execution realism; causal harm; costly labels; any
statement about a natural onset; density-dependent claims about sparse bursts.

## B.9 Freeze line

`SHA-256 (this file + rule code + grid file): <PLACEHOLDER, to be computed at freeze>`

---

# Which task better supports Lane A's G4 items (a)-(e)?

| G4 item | OPSD (A) | Binance (B) |
|---|---|---|
| (a) point-in-time features and documented publication times | **Partial.** ENTSO-E publishes a documented deadline (partially verified). Per-row vintage times and revision history are not in the snapshot | **Strong for features** (a bar's close is deterministic). No revision issue. The archive is final data |
| (b) event and label availability times / fixed-delay service contract | **Partial but non-trivial:** d=2 derived from a regulatory rule | **Strong:** d=1 exact from the exchange's bar calendar |
| (c) both losses identifiable from a common outcome | Yes (realised load) | Yes under a stated no-impact assumption (idealised) |
| (d) application-grounded switching/query costs | **Weak:** reserve costs and k, c, B are imposed | **Partial for k only** (fee schedule, unhashed); c and B imposed; labels free |
| (e) licence and source hash | OPSD: no licence field, publisher checksum unverified; one raw SHA-256 | Binance: publisher checksums verified, MIT repo, data terms; fee page unhashed |

Verdict: **neither passes G4 alone.** Binance is better on (a), (b), (e) and on part of (d); OPSD
is better on a natural forecast-incumbent decision, a disagreement density that is plausibly sparse
and bursty, and a plausible drift mechanism, but is weaker on clocks and costs. If G4 requires
verified clocks and licence, Binance is the stronger *evidentiary* testbed; if it requires a
paired incumbent/candidate decision with sparse disagreement, OPSD is. The honest summary is to
report G4 as unmet in cost grounding in both and use the two tasks as complementary replays.

# Blockers and open items

1. Human confirmation of the ENTSO-E rule against EUR-Lex Art. 6(2); WAF blocked scripted fetch.
2. Human capture and SHA-256 of the Binance fee-schedule HTML.
3. OPSD/ENTSO-E reuse terms not pinned; OPSD snapshot revision status unknown; the `DE` zone
   definition across 2018-10 unverified.
4. Disagreement densities for both tasks are unmeasured; the development-window measurement is the
   first R2 step, and the density gates (A.7) are fixed here.
5. Freeze hashes are placeholders; no holdout may be opened before they are filled.

## Amendment A-B2 (2026-10-28, before any freeze; development data only)

R2 found that the frozen B.2 loss puts each policy's own turnover fee inside `Z`. As a result
`Z != 0` on 554 of 5,162 development agreement rounds (by at most 0.005). That violates the
contract's rule that an agreement has `Z = 0`.

**Amended B.2:** `Z_t` is the difference in position returns only,
`(a_cand,t − a_inc,t) · r_{t+1}` with the sign convention of B.2. When the two policies agree, the
positions are equal, so `Z_t = 0` exactly. Trading fees are charged through the switching and
turnover cost channel `k` (0.100% per side, from A4) in the net-utility accounting, not inside `Z`.

Lead decision, recorded under the user's standing instruction to proceed on best judgement. No
holdout was touched.

**Also disclosed:** the OPSD ridge penalty selected on 2017 is 1.0, the lower edge of the frozen
grid. The grid stays frozen as specified, so the optimum may lie below it.
