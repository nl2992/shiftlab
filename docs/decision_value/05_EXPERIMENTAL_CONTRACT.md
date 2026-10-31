# Experimental contract and evaluation engine

Implements `00_MASTER_PROTOCOL.md`. Code: `src/shiftlab/decision_value/`; tests:
`tests/decision_value/test_engine.py`; CLI: `scripts/decision_value/run_synthetic.py`. Confirmation
seeds, thresholds and comparison sets are **not** frozen here yet; this file documents the
engine and development-stage smoke evidence only.

## Interfaces

| module | content |
|---|---|
| `contracts.py` | `CostContract(c_q, c_s)`, `FeedbackContract(q, d, max_queries)`, `EpisodeBatch(l0, l1, mask)` (operational), `EvaluatorTruth(mu0, mu1, regime, tau)` (evaluator only) |
| `synthetic.py` | `Family("s1"/"s2"/"s3", params).generate(seed, n, feedback, null=False)` -> `(EpisodeBatch, EvaluatorTruth)`; `null=True` gives the no-change generator (same acquisition/CRN) |
| `feedback.py` | `make_mask`, `LabelQueue` (fixed delay `d`), `clocks` (trace clocks) |
| `monitors.py` | `CUSUM, PageHinkley, BatchTest, SRBetting, KellyH2c`; `update(x, valid)`, `statistic`, `reset(mask)`, `threshold`, `spec()`; `Target` ('paired' / 'incumbent') |
| `controllers.py` | `Permanent, Hold(H), Reverse, NeverSwitch, AlwaysChallenger, CalendarBatch(K), StaticThreshold(W)` |
| `evaluation.py` | `simulate(batch, feedback, monitor, controller)` (no truth argument) and `score(sim, batch, truth, cost)`; `run_episode_batch` combines them |
| `oracles.py` | best static, best dynamic (2-state DP, expected and realised losses), regime clairvoyant |
| `calibration.py` | `calibrate_threshold`, `null_maxima`, nominal `log(1/alpha)` rule |
| `statistics.py` | paired bootstrap (10,000 resamples, shared episode resamples), relative difference, Holm, `classify_reversal` |
| `registry.py` | append-only JSONL `outputs/decision_value/manifests/run_registry.jsonl` |

All n episodes advance in lockstep (arrays shape `(n,)`); T=3000, n=500, five monitors + references
+ calibration runs in ~15 s on one CPU process.

## Synthetic families (Bernoulli losses, means clipped to [0,1])

- **S1** incumbent mean `p0 + Delta` on `[tau, tau+L)`, else `p0`; challenger `p0 + delta`; `tau ~ U{tau_lo..tau_hi}`.
- **S2** two-state Markov chain, stay probability `rho`, stationary start; bad state: incumbent `p0+Delta`, challenger
  `p0` (useful) / `p0+Delta` (useless) / `p0+Delta+0.05` (harmful); good state: incumbent `p0`, challenger `p0+delta`.
- **S3** persistent change at `tau`: incumbent `p0+Delta`. Challenger: *strong* `p0+delta`; *weak*
  `p0+delta+(1-weak_frac)(Delta-delta)` (advantage `weak_frac*(Delta-delta)`, default 0.3); *reversing* strong on
  `[tau, tau+L)`, then `mu0+delta`; *none* equals incumbent after `tau`; *common_shock* `p0+delta+Delta`.
- **Null** per family: no change (S2: always good state). `tau` is drawn anyway so the stream is CRN-aligned.
- `opportunity_t := mu0_t - mu1_t > 0` (evaluator-side). Independent uniforms for `l0`, `l1`; sub-streams
  (structure, losses, acquisition) spawned from one `SeedSequence`, so acquisition masks are identical across monitors.

## Clocks and information sets

Decision step `s` (0-indexed) uses only labels with release time `<= s-1`:

1. event `e = s-1-d` (if `mask[:, e]`) is shown to the monitor (Setting A: both `l0`, `l1`);
2. monitor update -> alarm -> controller picks `a_s` (`F_{s-1}`-measurable); optional monitor reset;
3. event `s` realises losses of `a_s`; if queried its label is released at `s+d`.

So a label for event `t` is first visible at decision `t+d+1`. With fixed `d` at most one label is released per
step, so event order is preserved. Traces (3 sampled episodes in `summary.json`) record query event, release time,
first-visible decision, monitor-update steps, alarm steps and switch steps. Variable delay is not implemented.
Monitors, controllers and `simulate` import no truth objects (checked by a test). Setting B/C are out of scope.

Targets: `paired` `x = l0 - l1` (null `E[x] <= 0`); `incumbent` `x = l0 - r0`, `r0` = mean of released `l0` over the
first `cal=300` events (estimated, never the evaluator's value; monitor input is invalid during the window).

## Cost accounting

`cost_exp = sum_t mu_{a_t}(t) + c_q N_q + c_s N_s` (Rao-Blackwellised); `cost_real` uses realised losses.
`N_q` = number of queried events (`mask.sum`) for methods that use labels (monitors, calendar, static) and 0 for
never/always. `N_s` counts every change of action including the initial move from the incumbent (`a_{-1}=0`) and
reverts. `harm_before_switch = sum_{t < first switch} max(mu0-mu1, 0)`. Oracle costs use no labels (exclude `c_q`).
Headroom `H_T = E[never-switch - best dynamic]` (>= 0 since the dynamic class contains the static class);
`H_T(static) = E[best static - best dynamic]` is also reported.

## Calibration procedure

`calibrate_threshold` simulates `n_cal` (default 2000) null episodes on separate seeds (default 5,000,000) with the
same feedback contract, records the per-episode max of the statistic over the horizon, and returns the `(1-alpha)`
("higher") quantile, so `P(any alarm by T) <= alpha` (alarm iff statistic > threshold). Setting A inputs do not
depend on actions, so a monitor-only run suffices. The script re-checks the null alarm rate on fresh seed 5,000,001
(`null_alarm_rate_fresh_seed`). Nominal rule (`monitor@nominal`): `log(1/alpha)` on the log e-value scale, e-detectors
only, reported separately. Caveat: for SR betting the 1/alpha rule is an average-run-length guarantee, not
`P(any alarm by T) <= alpha`; the Kelly detector is an e-process from start 0, so `1/alpha` is a valid horizon-free
test of the null `E[x_t | F_{t-1}] <= 0` (given bounded `x`, predictable bets). Calibration is marginal for the
declared null generator (no-change, i.i.d. Bernoulli); it is not claimed under dependence or adaptation.
`Reverse` reuses the main threshold for its reverse monitor (not separately calibrated).

## Monitor fidelity table

| monitor | label | repo cross-check |
|---|---|---|
| `cusum` (k) | TEXTBOOK | equals `shiftlab.monitoring.one_sided_cusum(baseline_mean=0, baseline_scale=1, slack=k)` (tested, `allclose`) |
| `page_hinkley` (delta) | TEXTBOOK (running-mean form) | no repo implementation found; hand-computed values tested |
| `batch` (n_b) | TEXTBOOK fixed-sample one-sided z on non-overlapping windows (sd floor 0.05) | none; hand-computed |
| `sr_betting` (lambda grid) | TEXTBOOK Shin-Ramdas-Rinaldo e-detector `R_t=(1+R_{t-1})(1+lambda x_t)`, uniform mixture, log domain, lambda in [0,1) | none; hand-computed (`1.5, 3.75`) |
| `kelly_h2c_inspired` | **H2c-inspired (SOURCE_INSPIRED)**, predictable `lambda_t = clip(max(m,0)/v, 0, 0.5)` from discounted past released x, half-lives (16,64,256) | equals `shiftlab.dive.eprocess.MultiTimescaleStartedKellyEProcess(bound=1, starts=(0,))` log e-value (tested, atol 1e-10) |

Default hyperparameters (CUSUM k=0.02, PH delta=0.005, batch n_b=50, SR grid 0.05..0.8) are untuned placeholders.

## Tests (`tests/decision_value/test_engine.py`, 30 tests, ~6 s)

- *information flow*: operational modules contain no truth symbols/imports and `simulate` has no truth argument;
  flipping all losses of events >= e0 leaves alarms/actions at decisions `<= e0+d` unchanged for every monitor
  while the monitor state does change; perturbing truth changes scores but not actions; the incumbent reference
  risk depends only on the calibration window.
- *feedback*: first-visible decision is exactly `t+d+1` for d in {0,1,5,50}, trace update step agrees, event order.
- *budgets*: `N_q` = mask count, budget cap, negative `q/d/c/budget` rejected, never-switch pays no queries.
- *switch costs*: hand-computed scripted toy (3 switches, initial move counts, `c_q` term).
- *oracles*: DP equals brute force over all 2^9 paths; dynamic <= static <= never, `H_T >= 0`, dynamic <= clairvoyant on
  S1-S3; S2 clairvoyant equals dynamic at `c_s=0` and never-switch for a harmful challenger; analytical toy
  with known optimal schedule (never 20, always 15, dynamic 10, `H_T`=10, scripted schedule attains it).
- *replay*: same seed -> identical thresholds and records; different seed differs.
- *calibration*: empirical fresh-seed null alarm rate within 0.02 of 0.05 (CUSUM, PH, SR); nominal Kelly threshold valid.
- *fidelity*: CUSUM and Kelly vs repo; PH/SR/batch hand values; valid-mask and `reset(mask)` semantics for all monitors.
- *controllers*: Permanent, Hold (revert + reset), Reverse (switch back), Calendar, Static on deterministic toys.
- *generators*: shapes, structure of S1/S2/S3 variants, null, CRN acquisition.
- *statistics/registry*: bootstrap CI coverage of a known difference, relative-difference denominator, Holm,
  reversal classifier (3 cases), append-only registry, dev-seed guard (>= 7,000,000 refused without `--confirmation` and hash).

## Smoke run (smoke, development)

```
python scripts/decision_value/run_synthetic.py --family s1 \
  --params '{"p0":0.2,"delta":0.05,"Delta":0.15,"L":400,"tau_lo":800,"tau_hi":1200,"T":3000}' \
  --q 0.2 --d 50 --c-s 5 --c-q 0 --n 500 --seed-base 1000 \
  --monitors cusum,page_hinkley,batch,sr_betting,kelly_h2c_inspired --controller permanent \
  --references never,always,calendar:200,static:100
```
Run id `20261030T224957Z_s1_n500_s1000` (outputs gitignored under `outputs/decision_value/development/`), runtime 15.1 s,
single process, git base ce9d3ca plus uncommitted engine. n=500, calibration n_cal=2000, alpha=0.05, controller Permanent,
reference never-switch. Costs are `cost_exp` (mean +/- se); difference = method minus never-switch with bootstrap 95% CI.

| method | threshold | cost | N_s | diff vs never [95% CI] | power(T) | power in opportunity | power h<200 | power h<400 | censored delay | pre-tau false alarm |
|---|---|---|---|---|---|---|---|---|---|---|
| cusum | 12.78 | 691.6 (1.7) | 0.43 | +31.6 [28.4, 34.9] | 0.430 | 0.278 | 0.034 | 0.278 | 1312 | 0.006 |
| page_hinkley | 29.18 | 667.9 (1.0) | 0.12 | +7.9 [6.0, 9.9] | 0.122 | 0.042 | 0.014 | 0.042 | 1830 | 0.000 |
| batch | 2.06 | 676.6 (1.4) | 0.23 | +16.6 [13.9, 19.4] | 0.222 | 0.138 | 0.024 | 0.138 | 1640 | 0.012 |
| sr_betting | 6.80 | 680.8 (1.5) | 0.30 | +20.8 [17.9, 23.7] | 0.294 | 0.202 | 0.054 | 0.202 | 1531 | 0.010 |
| kelly_h2c_inspired | 0.921 | 676.6 (1.4) | 0.23 | +16.6 [13.9, 19.3] | 0.204 | 0.154 | 0.044 | 0.154 | 1651 | 0.030 |
| never | - | 660.0 | 0 | 0 | | | | | | |
| always | - | 755.0 | 1 | +95.0 | | | | | | |
| calendar K=200 | - | 708.2 (1.1) | 5.44 | +48.2 | | | | | | |
| static W=100 | - | 724.0 (0.5) | 1.00 | +64.0 | | | | | | |

Oracles: best static 660.0 (= never-switch), best dynamic 630.0, regime clairvoyant 630.0; headroom
`H_T` = 30.0 (expected losses; every episode identical because tau and L do not change the optimal gain), 43.2 on
realised losses. Fresh-seed null alarm rates: 0.062 (cusum), 0.049, 0.0545, 0.056, 0.050 (n=2000 each, se ~0.005).

Reading (descriptive only, not confirmatory): in this cell every monitor loses to never-switch under the Permanent
controller, because after the 400-step window the challenger is worse by delta and a permanent switch pays the loss
without reverting; with per-switch cost 5 the available headroom (30) is small relative to that downside. The
detection ordering (CUSUM > SR > Kelly/batch > PH on power) therefore is *not* the cost ordering (PH, which rarely
alarms, is cheapest), but this is one cell, one seed block, an untuned controller choice, and no reversal test was
applied. `StaticThreshold` as specified has no significance margin and switches on noise in every episode.

## Known caveats

- `power_h*`/delay/pre-tau metrics are computed on the raw alarm stream of the run with its controller; under Hold/Reverse
  monitor resets alter the stream relative to Permanent.
- Batch statistic persists as the last completed window's z until the next window or a reset.
- Percentile bootstrap resamples episodes only; episodes in a cell share one seed block and cells are not independent replications.
- Development seeds only; the seed guard refuses >= 7,000,000 without `--confirmation` plus a protocol hash.
