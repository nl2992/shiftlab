# D1: OPSD split-clock task (2026-10-29)

**Verdict: the OPSD fast channel is not usable. The delay gap is exactly 1 round (the clock
condition holds), but the surrogate is uninformative: sign agreement 0.069 (floor 0.6) on
development disagreement rounds. Phase D's D1 exit applies: evaluate the Binance alternative
(outlined in section 6, not implemented). The task is not frozen.** Development data only; the 2020
holdout was not read.

Code: `src/shiftlab/real_tasks/opsd_split_clock.py`. Tests: `tests/test_opsd_split_clock.py`
(8 pass, ruff clean). Raw measurements: `D1_opsd_split_clock_measurements.json`.

## 1. Specification (written before measuring)

**Base task unchanged** (R1 A-R3/A-R3b): round D is a Berlin local delivery day; decision at D-1
10:00 local; public `x` is calendar-only; the gold label `Z_D` is the full-day paired reserve loss
(divided by 125), available at local day end + 1 h, so first usable at round D+2: `d_g = 2`.

**Fast channel.** `Zf_D` is the same paired reserve loss, with the same `tau_D`, actions and `/125`
scale, summed only over delivery hours whose local clock hour is 00..07. Hence `Z_D = Zf_D + R_D`,
where `R_D` is the paired loss over local hours 08..23.

**Fast clock.** ENTSO-E Art. 6(2)(a) (R1b): actual load is published at most 1 h after the
operating period. The last fast hour (07:00-08:00) is published by **09:00 local on day D**, one hour
strictly before the next decision (D 10:00 local). The fast label is delivered at the start of round
D+1: **`d_f = 1`**, gap `d_g - d_f = 1` round. The window cannot be extended: hour 08 would be
published at exactly 10:00, equal to the decision instant, and the A-R3b rule requires strict
precedence. `fast_available_utc` encodes the 09:00 local time with DST-aware conversion (tested on
both change days).

**Missingness.** The fast label is observed iff all fast-window actuals of D are finite and D is not
flagged by an archived-timestamp irregularity. Fast-observed is a superset of gold-observed. Both
channels equal 0 on agreement rounds, as in the contract.

**Prices (imposed).** Gold price `c_g = 1` price unit (the existing primary `c`: 1 raw idle-hour
unit, 1/125 normalised). Fast price `c_f = rho * c_g`, `rho` in {1/8, 1/4, 1/2}, primary 1/4.
Interpretation: a fast query is a partial review of the overnight and early-morning settled hours; a
gold query is the full-day settlement audit. Labels are free in reality; both prices stand for
imposed analyst-review capacity, as in R1 A.6. `rho` is a design parameter, not a measurement.

**Surrogate bias model.** `E[Z | Zf] - Zf = E[R | Zf]`: the surrogate is an unbiased proxy only if
the rest-of-day loss has conditional mean zero given the fast information, which nothing in the
data-generating process guarantees. Sources: (i) coverage, since disagreement hours sit at daytime
peak, outside the fast window (section 3); (ii) a time-of-day cost asymmetry between the policies;
(iii) snapshot revisions (A2). Rule fixed now: **a monitor may use `Zf` for descriptive tracking and
rollback triggers, but any promotion (a 0 to 1 switch whose validity is claimed) must be certified on
gold labels only.** A surrogate-only promotion rule is the invalid-promotion control of Phase D3.

## 2. Plug-in to the label-limited auditor contract

- Public `x`, actions and disagreement flags are unchanged; the fast channel adds no public field.
- A query names `(t, channel)` with channel in {fast, gold}. The harness charges per channel at
  request time (`c_f` or `c_g`, in the same price-unit budget); both channels of one `t` may be
  bought (price `c_f + c_g`); refusal on overdraw is as today.
- Each channel has its own release round: `release_f[t]` is the first round with decision time >=
  `fast_available_time[t]`; `release_g[t]` is as in the base task. The harness delivers a
  channel-tagged `Feedback(t, channel, paired_cost, propensity)` or `MissingFeedback(t, channel,
  propensity)` at that channel's release round; `PendingQuery` carries the channel. Out-of-order
  rejection (A-R3b) applies per channel; across channels order is unconstrained (the fast label of
  `t+1` arrives with the gold label of `t`).
- `harness_v2` supports one channel only. Extending it (channel field on the three payload types,
  per-channel `release_round`, `observed`, prices and pending spend) is D4 work and is **not done
  here**. `SplitClockTask` already supplies the evaluator-side arrays: `fast_paired`,
  `fast_observed`, `fast_release_round`, `fast_available_time`.

## 3. Development measurements

Windows (all development or earlier; `HoldoutAccessError` is enforced on the series, every window end
and every constructed timestamp, tested): local 2016 (candidate in-sample; a second sample only),
2017 (validation), 2018-01-01..2019-12-30 (development, 729 rounds, matching R2). Command:
`python -m shiftlab.real_tasks.opsd_split_clock docs/lane_b_burst_allocation/D1_opsd_split_clock_measurements.json`.
Ridge penalty 1.0 as in R2; development mean gold `Z` on disagreement 0.0061, sd 0.139, reproduces R2.

**Delay gap (all three windows):** gold delay {2}, fast delay {1}, gap {1} (-1 marks only unreleased
terminal labels). Effective gap: **1.0 round**.

**Surrogate quality on labelled disagreement rounds:**

| Quantity | 2016 (in-sample) | 2017 (valid.) | 2018-19 (dev.) |
|---|---|---|---|
| disagreement rounds | 97 | 87 | 161 |
| share with a differing hour in fast window | 0.031 | 0.161 | 0.106 |
| share of `Zf` exactly 0 | 0.969 | 0.839 | 0.894 |
| Pearson corr(`Zf`, `Z`) | 0.113 | 0.137 | 0.213 |
| Spearman | 0.036 | 0.187 | 0.111 |
| **sign agreement, all gold-nonzero rounds** (`Zf = 0` counts as a miss; primary) | 0.021 (n=94) | 0.151 (n=86) | **0.069 (n=160)** |
| sign agreement, both nonzero | 0.667 (n=3) | 0.929 (n=14) | 0.647 (n=17) |
| slope of `Z` on `Zf` / intercept | 2.53 / 0.110 | 0.91 / -0.026 | 3.13 / 0.012 |
| mean `Z` / mean `Zf` | 0.1101 / 0.0001 | -0.0294 / -0.0039 | 0.0061 / -0.0018 |
| bias (`Zf` - `Z`) | -0.1100 | +0.0256 | -0.0079 |
| sd `Z` / sd `Zf` | 0.131 / 0.0058 | 0.092 / 0.0138 | 0.139 / 0.0095 |

**Reading.** The position histogram of differing hours on the development window is
`[0 0 0 0 0 0 0 17 50 47 50 50 48 49 41 35 30 51 40 44 6 0 0 0]` (558 hours, position = hour index
within the delivery day): 3.0% of disagreeing hours fall in positions 0-7, because the two forecasts
straddle the 0.90 quantile only at daytime peak (R1 A.7 anticipated this concentration). So 89% of
fast labels are identically zero on disagreement rounds. Where nonzero (17 development rounds), the
sign is right 65% of the time, but that subset is small and conditioned post hoc; it cannot support a
decision rule. The slope (0.9 to 3.1) and intercept are unstable across windows, and the correlation
(0.11 to 0.21) is weak. The surrogate carries almost no information on whether the candidate helps.

## 4. Gate assessment

| Criterion | Result |
|---|---|
| Delay gap >= 1 round | Pass: exactly 1 round (`d_f = 1`, `d_g = 2`) |
| Surrogate informative (sign agreement >= 0.6, primary definition) | **Fail: 0.069 (dev), 0.151 (2017), 0.021 (2016)** |
| Frozen with a measured development surrogate-gold correlation | Not frozen; correlation measured (0.21 dev) but too weak |

Why choosing other hours does not help: the clock caps the information. Any hour published before D
10:00 local is hour 08 or earlier, while disagreement hours sit at 07-20. A later cut-off (e.g.
00-15) is available only after the next decision, so `d_f = 2 = d_g` and the delay gap vanishes. No
hour set satisfies both requirements. A different fast quantity (e.g. an hourly-error difference over
hours 0-7 instead of threshold cost) was not tested: it would be a surrogate chosen after seeing the
failure, and the underlying fact (the policies mostly agree overnight, so overnight outcomes say
little about peak-hour disagreement) is unchanged. Making the policies disagree overnight would
change the task, not measure it.

## 5. Threats to validity

1. The development windows were already exposed in R2; 2016 is in-sample for the candidate. The three
   windows share tau and the model, so they are not independent evidence.
2. Surrogate bias is structural (coverage), not noise; a pass at a different cut-off would still be a
   retrospective property of this pair of forecasters.
3. Prices and the partial-review versus settlement-audit interpretation are imposed; the real
   analogue has no measured cost.
4. Snapshot revisions (A2) may make the nominal 1 h publication clock optimistic. The fast channel's
   margin is 1 h: a 1 h slip gives `d_f = 2` and erases the gap. The gold channel has a full-day
   margin after day end.
5. The 0.6 sign-agreement floor is a screening rule from the task brief, not a calibrated test. The
   result (0.07) is far below it; the only figure above it is the small nonzero subset.
6. Descriptive diagnostics only: no calibration, causal onset or promotion-validity claim.

## 6. Binance alternative (outline only, not implemented)

- **Task:** the existing Binance momentum pair (`binance_momentum.py`), same public contract
  (calendar `x`, two actions).
- **Fast channel:** the 1-bar clipped signal-loss difference (sign or magnitude) of the disagreeing
  positions; available one bar after the decision (`d_f = 1`, the existing Binance label clock).
- **Gold channel:** the 24-bar cumulative clipped signal-loss label, available after 24 bars
  (`d_g = 24`, gap 23 rounds). This redefines the Binance gold horizon (currently 1 bar), so it is a
  new task spec rather than a relabelling.
- **To measure on 2025 development data before any freeze:** correlation, primary-definition sign
  agreement (floor 0.6), regression slope and bias of the 1-bar versus the 24-bar loss on
  disagreement rounds. Short-horizon momentum signals are weakly autocorrelated, so informativeness
  is not expected and must be measured. If it also fails, Phase D has no real-data task and D4 would
  rely on synthetic and semi-synthetic channels.
- **Overlap hazard:** 24-bar labels of consecutive rounds overlap, so gold labels are serially
  dependent and the harness's independence and ordering assumptions need an explicit statement.

## 7. Freeze placeholder

Not frozen. Status: **blocked** (surrogate uninformative). If a replacement task passes the same two
criteria, the freeze record will list this file, `opsd_split_clock.py` (or its replacement), the
tests, `D1_opsd_split_clock_measurements.json`, the OPSD raw hash pinned in the R3 freeze, and the
pre-stated criteria of section 4. This document authorises no holdout opening.
