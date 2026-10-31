# 11 Experiment Type II: optimised-controller comparison (H6 and H1 under tuning)

**Label: development, synthetic (Setting C). Seeds < 7,000,000 only. Nothing here is confirmatory.**
Script: `scripts/decision_value/run_type2_tuning.py`. Engine unchanged. This section (Design) was written
BEFORE any evaluation-seed run; results are appended below it afterwards.

## 1. Question

Doc 06 found that with fixed, untuned controllers (Permanent / Hold(L/2)) a monitor beat the best simple
reference by >= MME in only 1 of 66 cells. Is "sequential monitors rarely beat simple deployment policies" an
artifact of those untuned controllers? Type II tunes the *whole system* (controller, controller parameter,
alarm level) for each monitor, and gives the simple-policy family a comparable tuning budget.

## 2. Design (frozen before evaluation)

**Cells (11), all paired target, c_q = 0, other parameters as in the originating experiment:**

| id | family | params | q | d | c_s | origin |
|---|---|---|---|---|---|---|
| th3_rho{0.995,0.999}_d{0,50}_useful | S2 | challenger_bad=useful | 0.2 | 0/50 | 2 | TH-3 |
| th3_rho0.999_d0_useless | S2 | challenger_bad=useless (negative control) | 0.2 | 0 | 2 | TH-3 |
| th4_L{400,1600}_d{0,50} | S1 | L as named | 0.5 | 0/50 | 5 | TH-4 |
| th2_strong, th2_weak | S3 | challenger=strong / weak | 0.2 | 50 | 5 | TH-2 (paired target) |

T = 3000, p0 = 0.2, Delta = 0.15, delta = 0.05 (family defaults).

**Monitor systems (32 per monitor, 160 total per cell):** monitors cusum, page_hinkley, batch, sr_betting,
kelly_h2c_inspired (engine defaults, as doc 06) x controller in {Permanent, Hold(H) for
H in {25,50,100,200,400,800}, Reverse} (8 controllers) x alpha in {0.01, 0.05, 0.2, 0.5}. Thresholds are the
(1-alpha) "higher" quantile of the null max statistic (n_cal = 6000, seed 5,000,000, same as doc 06; null data
are family-independent, so calibration is keyed on (monitor, q, d)). Reverse reuses the main threshold, as in the
earlier engine scripts.

**Simple-reference family (32 configs, no monitor, no calibration):** never; always;
CalendarBatch(K) with decision margin m (K in {25,50,100,200,400,800} x m in {0,0.01,0.02,0.05}: every K steps
move to the challenger only if the released window-mean advantage mean(l0)-mean(l1) exceeds m, move back only if
it is below -m, otherwise keep the current action; m = 0 is the engine CalendarBatch except for ties) = 24
configs; StaticThreshold(W) with margin m (W in {50,100,200} x m in {0,0.02}: engine rule plus the extra condition
buffer-mean-gap > m) = 6 configs. 2 + 24 + 6 = 32. The batch monitor with Hold is the "monitor-free
fixed-sample" analogue and is counted among the monitors.

**Seeds and selection.** Tuning seed = 100000 + cell index, n = 500 (CRN: every config in a cell sees the same
episodes). Selection criterion: mean expected net cost `cost_exp` (loss + c_s x switches; c_q = 0) on tuning
seeds. Per cell select (a) best config per monitor, (b) best monitor overall (= best of (a)), (c) best simple.
Evaluation seed = 200000 + cell index (fresh, disjoint), n = 2000; only selected configs (plus never, always,
oracles) are evaluated.

**Primary estimand (per cell):** Dsys = mean over eval episodes of [cost(best simple) - cost(best monitor
overall)] (positive = monitor system better), 95% paired percentile bootstrap (10,000 resamples), two-sided
bootstrap p; Holm correction across the 11 cells. MME = 1% of never-switch cost in the cell. Classification:
"monitor wins" iff Dsys >= MME, CI lower bound > 0 and Holm-adjusted p < 0.05; "simple wins" symmetric;
otherwise tie. Secondary: the same difference per monitor, fraction of headroom captured =
(never - cost)/(never - dynamic oracle) for each selected system, N_s, best static, dynamic oracle, and selection
optimism = tuning-seed cost minus evaluation-seed cost of the selected config (positive = selected config looks
better than it is).

**H1 under tuning:** per cell, Kendall tau between the tuned monitors' detection ranking (power_T at the chosen
alpha on eval seeds; also delay) and their tuned value ranking (never - cost) over the 5 monitors; plus the
engine protocol reversal classifier on the 20 ordered monitor pairs (power diff >= 0.05 with CI excluding 0 AND
cost disadvantage >= MME with CI excluding 0).

**Pre-declared verdict rules.** H6 ("simple policies are competitive") is *not an artifact of untuned
controllers* if the monitor system wins in <= 1 of the 10 non-control cells; it is *falsified under tuning* if the
monitor system wins in >= 4 of 10 non-control cells; 2-3 cells = mixed. H1 (detection ranking can reverse the cost
ranking) is *supported under tuning* if protocol reversals occur in >= 1 cell among the tuned monitors AND tau < 0
in >= 3 cells; otherwise *not supported / unresolved*. Negative control: in th3_rho0.999_d0_useless no system
should beat never-switch; a monitor win there is a pipeline red flag.

**Known limitations (declared up front).** (i) Selection over 160 configs on n = 500 is noisy; the winner's curse
is measured, not corrected. (ii) The simple family has 32 configs vs 160 monitor configs; comparing the best-of-160
to best-of-32 favours monitors by a max-of-more-draws effect on the tuning seeds, but evaluation is on fresh seeds,
so this only affects which config is picked, not bias of the reported cost. (iii) Hold/Reverse horizons are
tuned per cell, i.e. with knowledge of the cell's L / rho; this is an oracle-tuned monitor system, an upper bound
for monitors. (iv) One tuning/eval seed pair per cell; cells share monitor implementations, not independent.
