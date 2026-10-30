# D1b: Binance split-clock task (2026-10-29)

**Verdict: the surrogate does not pass the 0.6 floor (sign agreement 0.563 on 2025 development
disagreement rounds), though it is better than chance and the delay gap is large (23 rounds).
Correlation is weak (0.18). This is a near miss, not a clear pass; the task is not frozen.** Whether
to relax or keep the floor is the lead's call (see section 6). Development data only (2025); the 2026
holdout guard is enforced and tested; the holdout was not read.

Code: `src/shiftlab/real_tasks/binance_split_clock.py`. Tests: `tests/test_binance_split_clock.py`
(10 pass; ruff clean). Raw numbers: `D1b_binance_split_clock_measurements.json`
(`python -m shiftlab.real_tasks.binance_split_clock <out.json>`).

## 1. Specification (written before measuring)

**Rounds and policies unchanged** (R1 B, A-R3): decision at each bar close (hour boundary, open + 1 h);
public `x` is calendar-only; incumbent is the 24-bar and candidate the 168-bar long/flat momentum
rule; 8,590 rounds on 2025.

**Fast label (existing).** `Z_fast = l_0 - l_1` with `P_a(t) = p_a(t)(C_{t+1}/C_t - 1)` and
`l = 0.5(1 - clip(P/0.10, -1, 1))`. Released at t+1: `d_f = 1`.

**Gold label (new).** The position held fixed over the next `H = 24` bars:
`P_a(t) = p_a(t)(C_{t+24}/C_t - 1)`, `l_a(t) = 0.5(1 - clip(P_a(t)/(0.10*sqrt(24)), -1, 1))`,
`Z_gold = l_0 - l_1`. The clip scale 0.10*sqrt(24) = 0.490 scales the 1-bar convention by the
random-walk horizon factor. `Z_gold = 0` exactly on agreement and `|Z_gold| <= 1` (tested). It is
available once the close of bar t+24 is archived, i.e. at the decision instant of round t+24:
`d_g = 24` (tested at ms precision; the last 24 rounds are unreleased). Idealisations: the position
is held for 24 bars although the policies would re-evaluate each bar; no fees in `Z` (as in A-R3);
no impact. So `Z_gold` is a horizon-loss label for the frozen-position question, not the P&L of the
running policy.

**Prices (imposed).** `c_g = 1` price unit (the existing primary query cost, 0.0005 in normalised
loss); `c_f = rho * c_g`, `rho` in {1/24, 1/8, 1/4}, primary 1/8. Interpretation: a fast query is a
one-bar mark-to-market check of the position; a gold query is the 24-bar P&L attribution. `rho = 1/24`
is a cost proportional to the number of bars reviewed; 1/8 and 1/4 charge a premium for the shorter
review. Labels are free in reality; the prices are imposed review capacity. `rho` is a design
parameter, not measured.

**Surrogate bias model.** `Z_fast` is the first-bar term of the same return that `Z_gold` accumulates,
for the position held at t. `E[Z_gold | Z_fast]` differs from `Z_fast` by the remaining 23 bars,
which carry (i) the momentum/continuation effect that is the economic content of the question, (ii)
a scale difference (24-bar returns have larger variance and a different clipping rate), and (iii)
the position drift (the real policies re-trade). Hence the fast label is a biased, noisy proxy.
**Promotion must use gold labels only**; the fast label may be used for tracking and rollback.

## 2. Contract plug-in

Same as D1: public `x` unchanged; each query names `(t, channel)`; the harness charges per channel at
request, and delivers each channel at its own release round (fast at t+1, gold at t+24) with a
channel tag; out-of-order rejection per channel. `harness_v2` supports one channel only; the
two-channel extension is D4 work, not done. `BinanceSplitTask` supplies `fast_paired`,
`gold_paired`, `fast_release_round`, `gold_release_round`.

## 3. Dependence statement and the promotion rule

**Overlap.** `Z_gold(t)` is a function of returns of bars t+1..t+24, so `Z_gold(t)` and `Z_gold(t+1)`
share 23 of 24 bars. Measured serial correlation of `Z_gold` over rounds (2025, all rounds): lag 1
0.774, lag 2 0.660, lag 12 0.171, lag 23 -0.050, lag 24 -0.061, lag 48 -0.054. So consecutive gold
labels are a single draw seen up to ~24 times.

**What this does to e-process validity.** Two separate problems.
1. *Conditional null.* The Paper-style null is `E[Z_t | H_t] <= 0`, with `H_t` the information at the
   decision of round t. A betting product `prod (1 + lambda_t Z_t)` in release order needs
   `E[Z_t | F] <= 0` for the information `F` available when label t is *delivered* (decision of
   round t+24). `F` contains prices up to bar t+24, i.e. the entire return that determines `Z_t`
   (for held positions Z_t is a deterministic function of public closes). The null at decision time
   does not transfer, and conditional on `F` the label is not random. Using every gold label
   therefore gives no validity claim at all, not merely a loss of power.
2. *Effective sample size.* Even with a valid null, 24 overlapping labels carry about one
   observation of information; treating them as independent inflates the evidence by up to ~24x in
   the log e-value.

**Rule (specified): non-overlapping certification.** A gold label enters the certifying e-process
only if its return window `(t, t+24]` does not intersect the window of any earlier certifying
label, enforced as follows.
- *Harness rule (adaptive, predictable):* a certifying gold query at t is allowed iff
  `t >= s + 24` where `s` is the last allowed certifying query (`greedy_nonoverlapping`; depends only
  on past requests). Its stake `lambda_t` is chosen at the decision of round t, before any of the
  window's bars occur.
- *Fixed-phase variant (non-adaptive):* only rounds with `index mod 24 = phi` are certifiable
  (`thinned_phase_mask`), with `phi` fixed before any outcome. Use this when the allocator
  cannot be trusted to be predictable or for the confirmatory run.
- *Why this is valid:* with disjoint windows, label s is delivered exactly at the decision of
  round s+24, which is the next certifying opportunity. If `H_t` is the full history through the
  decision of round t (all closes up to bar t), then `Z_s` is `H_t`-measurable for the next certifying
  `t >= s + 24`, so the filtration is `H_{s+24}` and each factor is predictable with respect to the
  filtration at its own decision time; the product is a supermartingale under the decision-time
  null `E[Z_t | H_t] <= 0` with `lambda_t` `H_t`-measurable and in the admissible range. The
  update order is event order with fixed delay (the R3 delayed-update note's setting) and no
  intermediate labels are skipped inside a block. This is a design argument under the stated
  assumptions, not a verified guarantee, and it inherits the R3 limits: the held-position
  null is not the null of the running policy, and no real-data calibration is claimed.
- *Cost of the rule:* at most `n_rounds / 24 = 358` certifying labels per year (about 143 of them on
  disagreement rounds under fixed-phase thinning, 141/148 for phases 0/7), and certification lags
  by 24 bars plus waiting. Fast labels (non-overlapping, d=1) may drive tracking, rollback and
  query-allocation statistics but never promotion.
- *Non-certifying uses:* extra gold labels inside an open window may be bought as descriptive value
  estimates (the harness must mark them non-certifying); they are never multiplied into the e-process.

## 4. Development measurements (2025, 3,420 disagreement rounds with a gold value)

| Quantity | Value |
|---|---|
| rounds / disagreement share | 8,590 / 0.399 |
| fast / gold delay (rounds) | 1 / 24; gap 23 |
| share of `Z_fast` exactly 0 on disagreement | 0.0003 |
| Pearson / Spearman corr(`Z_fast`, `Z_gold`) | 0.177 / 0.160 |
| **sign agreement, all gold-nonzero rounds (primary)** | **0.563** (n=3,419) |
| sign agreement, both nonzero | 0.563 |
| by half-sample (first / second half of disagreement rounds) | 0.557 / 0.569 |
| fixed-phase thinned subsamples (phi=0 / phi=7), n=141 / 148 | 0.617 / 0.568 |
| slope of `Z_gold` on `Z_fast` / intercept | 0.163 / 0.0012 |
| mean `Z_gold` / mean `Z_fast` / bias (fast - gold) | 0.00145 / 0.00137 / -0.00008 |
| sd `Z_gold` / sd `Z_fast` | 0.0338 / 0.0366 |

Reading. The surrogate has information (the full-sample binomial SE for 0.563 is 0.0086, but the
3,419 pairs overlap heavily, so the effective sample is about 24 times smaller and the SE is nearer
0.04; the thinned subsamples give 0.62 and 0.57 with SE about 0.04). The best defensible statement is
"between 0.55 and 0.62, point estimate 0.563, below the 0.6 floor". The slope 0.16 is the
attenuation of a noisy predictor: the first bar explains little of the 24-bar outcome, and the
means agree (bias near zero) because both are near zero.

### Delay saved versus extra samples (descriptive CUSUM/LR calculation)

Gaussian LR approximation: labels needed `n = ln(1/alpha) / KL`, `KL = delta^2 / (2 sigma^2)`,
`alpha = 0.05`. `delta` is a stand-in for a typical reversal size: the RMS over the 12 months of the
monthly mean of `Z` on disagreement rounds (fast 0.00294, gold 0.00688). That quantity is mostly
sampling noise (monthly SE of the fast mean is about 0.0022), so it is a scale, not an estimate of
a real reversal. `sigma` are the dev standard deviations above. Label supply: fast, one per
disagreement round (share 0.398 per bar); gold, one certifying label per 24 bars on disagreement
rounds (share/24 per bar under fixed-phase thinning).

| Channel | KL per label | Labels needed | Bars to collect | Price units (c_g = 1) at rho = 1/8 | Delay after last label |
|---|---|---|---|---|---|
| fast | 0.0032 | 930 | 2,337 | 116 | 1 bar |
| gold, thinned (valid) | 0.0208 | 144 | 8,701 | 144 | 24 bars |
| gold, overlap ignored (INVALID) | 0.0208 | 144 | 363 | 144 | 24 bars |

Reading. On these descriptive numbers the fast channel reaches the same nominal error level about
3.7 times sooner in calendar time than valid gold, at similar monetary cost at rho = 1/8, because the
fast stream is not constrained by the 24-bar overlap. The 24-bar delay itself is small next to the
collection time (8,701 bars), so for a reversal of this size the delay gap Delta*(d_g - d_f) is a
minor part of the total; the dominant effect is the *sample-supply* constraint of valid gold labels.
This also means a mixed rule is not obviously better than fast-only on statistical efficiency, and
fast-only cannot promote validly. The fast count is only an unbiased-detector count for the
fast estimand; detecting a change in the 24-bar estimand with the fast stream needs the bias model
(slope 0.16, i.e. more samples), which this calculation ignores.

## 5. Threats to validity

1. One asset, one year (2025), one sample path; the monthly shifts are mostly noise.
2. Both gold and fast are idealised held-position losses without fees or impact; `Z_gold` is not the
   running policies' P&L.
3. The sign-agreement CI is much wider than the naive binomial SE because gold labels overlap.
4. Clip scale sqrt(24) is a convention; a different scale changes the fraction of clipped labels and
   the sign agreement slightly (sign is unaffected by scale except through clipping ties).
5. 2025 was already exposed in R2; the fast-versus-gold agreement is not a confirmatory quantity.
6. The thinning rule is argued, not verified, and the held-position null differs from the null of the
   policies as actually run.
7. Imposed prices and `rho`.

## 6. Gate assessment

| Criterion | Result |
|---|---|
| Delay gap >= 1 round | Pass: 23 rounds |
| Sign agreement >= 0.6 (primary) | **Fail, near miss: 0.563** (0.62 / 0.57 on two thinned subsamples, SE ~0.04) |
| Correlation | Weak: 0.177 |
| Frozen | No |

Options for the lead (no choice made here): (a) apply the floor literally: no real-data task with an
informative fast channel exists, and D4 uses synthetic and semi-synthetic channels; (b) treat 0.563
(CI roughly 0.5 to 0.65) as "weakly informative" and carry the task into D2/D3 as a stress case
labelled low-quality-surrogate, with synthetic surrogate quality swept across the real value; (c)
test one pre-declared richer fast label (e.g. the first-k-bar cumulative return, k in {1, 4}) on the
2025 development data, accepting that it is a second look at the same exposed data. Any of these
changes the freeze text.

## 7. Freeze placeholder

Not frozen. If the task is carried forward, the freeze record will list this file, the module and its
tests, `D1b_binance_split_clock_measurements.json`, the pinned Binance archive receipts of R3, and
the pre-stated criteria of section 6. This document authorises no holdout opening.
