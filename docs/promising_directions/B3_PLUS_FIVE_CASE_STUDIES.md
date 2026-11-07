# B3+ five real-world case studies

Frozen method **P7s** (commit `e846107`); screening rule pre-registered in
`B3_PLUS_SCREENING_PROTOCOL.md` before any new dataset was downloaded. Every number below is
generated from saved per-episode records, not transcribed.

## Main table

Primary configuration for all five: `T = 2000`, `B = 200`, `c_q = 0.05`, `c_s = 5`, 100 shared
query seeds, seed base `20261101`. Net cost = deployment loss + `c_q N_q` + `c_s N_s`. `P7s-P3b`
is paired on identical episodes and seeds. `eps worse` is the number of episodes in which P7s
cost **more** than P3b.

**Caption (required, protocol section 5).** These five are a *selected* set.
**36 datasets were considered and 5 selected.** Breakdown, recomputed from
`research/b3_plus/dataset_discovery/dataset_registry.json`, which is the single source of truth:
29 new candidates were registered plus the 7 original B3 programme streams; **29 reached a
screening verdict** (7 of the new candidates are `NOT_RUN`, so they have none); **11 reached
locked-window evaluation** (4 new + all 7 original); **5 selected** (2 new + 3 original). The
4 original streams that are not selected failed the "switching must beat never-switching"
condition. The 7 datasets named in the pre-registered queue produced **0** successes; both new
successes come from candidates added after that queue was exhausted. This is **not** an unbiased
success rate, and the method was not evaluated only on these five.

| Dataset | Domain | K | P0 | P3b | P6 | **P7s** | P7s-P3b (95% CI) | labels P3b->P7s | eps worse | power |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spam | Text / email spam (Katakis) | 1 | 849.00 | 254.09 | 315.95 | **247.43** | -6.66 [-6.78, -6.54] | 200 -> 67 | 0/1 | seed, LOW |
| rialto | Image streaming classification | 16 | 202.06 | 103.73 | 122.91 | **98.42** | -5.31 [-5.98, -4.59] | 159 -> 53 | 0/16 | episode |
| weather | Environmental prediction | 3 | 504.00 | 475.77 | 465.56 | **472.57** | -3.20 [-3.33, -3.07] | 178 -> 114 | 0/3 | seed, LOW |
| openml_ldpa | Wearable activity recognition | 32 | 663.00 | 483.25 | 506.51 | **478.82** | -4.43 [-6.98, -2.64] | 181 -> 115 | 2/32 | episode |
| uci_occupancy | Room occupancy sensing | 4 | 481.25 | 177.63 | 236.45 | **176.62** | -1.01 [-1.03, -0.99] | 101 -> 81 | 0/4 | seed, LOW |

## Reading the table honestly

- **P7s beats P3b on all five**, every CI below zero. That is the claim the five cases support:
  the frozen method removes post-promotion certificate-maintenance spend.
- **P6, a fixed-sample binomial batch test, beats P7s on weather** (465.56 against 472.57), and
  beats P3b on the four non-selected streams too. So on one of our own five case studies a
  simpler comparator is the better policy overall. P7s overtakes P6 on spam, rialto, ldpa and
  occupancy. P6's validity rests on an assumed exchangeability of disagreement outcomes that the
  sequential procedure does not require; that asymmetry must be stated wherever P6 appears.
- **Only rialto (K=16) and openml_ldpa (K=32) are properly powered.** spam (K=1), weather (K=3)
  and uci_occupancy (K=4) use seed-level bootstraps, which measure query-randomisation variance
  and **not** episode variance. Three of five cases resting on seed bootstraps is the single most
  attackable feature of this evaluation.
- Labels fall on every case, by 67% (spam), 67% (rialto), 36% (weather), 36% (ldpa) and 20%
  (occupancy).

## Per-case mechanism

**1. spam** (K=1, LOW-POWER). Challenger advantage is large and immediate: P3b promotes at
`t ~ 244` and then spends the remaining ~1756 events buying labels at the paced rate. P7s stops
at the propensity floor once the decision is settled. Deployment behaviour is **bitwise
identical**; the whole -6.66 is `c_q N_q`.

**2. rialto** (K=16, episode bootstrap). The principal case. Promotion at `t ~ 425`, promotion
rate 1.00, zero rollbacks for both policies. Deployment loss identical per episode, labels
159 -> 53, gain -5.31 [-5.98, -4.59], and P7s is worse in **0 of 16** episodes.

**3. weather** (K=3, LOW-POWER). Small challenger advantage (P3b beats P0 by only 5.6%), so the
absolute gain is small (-3.20) though labels fall 36%. This is the case where P6 is better than
both P3b and P7s, which is reported rather than omitted.

**4. openml_ldpa** (K=32, episode bootstrap). The only properly powered *new* case, and the only
one where the gate **changes deployment behaviour**: deployment loss differs in 7 of 32 episodes,
switches in 5, and P7s costs more in 2 episodes (worst +3.13). On average deployment loss is
mildly better (-0.82/episode) and P7s rolls back *less* than P3b (0.017 against 0.047). Two
load-bearing caveats, both of which belong in the main text:
  - **Event order is inferred, not documented.** OpenML does not document columns V3/V4; they
    appear to be global ranks of the original timestamp and date string, corroborated by
    `Spearman(V3,V4) = 0.99999999999998` and by recording sequences being contiguous after
    sorting. This evidences a shared underlying order, not that the order is calendar time.
  - **The non-stationarity is largely a change of recorded person** (only 4 person changes across
    the sorted stream), not temporal drift within one deployment. It is a legitimate covariate
    shift but not the deployment-staleness story the other cases tell.

**5. uci_occupancy** (K=4, LOW-POWER). Weakest of the five, and labelled so wherever it appears.
Only 1 of 4 episodes promotes at all; P7s beats P3b by a measurable margin in just 1 of 4 and
ties in the other 3. Entire gain is label cost (-1.01) with zero deployment-loss and zero
switch-cost difference. Its narrow CI reflects query-seed variance only.

## What these five do not establish

- They do not show the method improves deployment **decisions**. On four of five cases deployment
  behaviour is identical and the gain is purely label cost; on ldpa the behavioural change is
  incidental and partly harmful.
- They do not characterise the mechanism's failure mode. No real stream here exhibits
  post-promotion reversal that the reduced monitoring handles worse on average; that risk is
  evidenced only by synthetic world W3, where the frozen setting is neutral and its rollback
  latency is strictly worse than P3b's. **This gap is open.**
- They are not evidence about datasets screened and discarded: 4 candidates are `NOT_RUN` for
  source-availability or tractability reasons and say nothing about the method.

## Validation of the five cases (goal section 8)

### Exact reproduction from saved seeds

Every case was re-run from scratch into a fresh output directory and compared against the
committed records. For spam, rialto and weather this re-ran the policies from the cached loss
streams; for openml_ldpa and uci_occupancy it re-downloaded the raw data, re-derived the event
order, re-binarised, re-selected the pair on train/dev windows and re-trained both models.

**Result: bit-exact on all five.** Every policy mean and **every per-seed cost** matched with
`max|diff| = 0.000e+00` (P0, P3b, P6, P7s). Reproduction is therefore established for the
pipeline end to end, not only for the policy given fixed losses.

One process note: a first reproduction attempt pointed at a scratch directory that already held
an earlier smoke-test run, so the runner refused to overwrite and the comparison silently used
stale files (which happened to match on P0/P3b/P6 and lacked P7s entirely). The check was redone
in a guaranteed-empty directory. A comparison that reads pre-existing files is not a
reproduction, and the runner's refusal to overwrite is what caught it.

### Independent query-randomisation batch

Re-run with seed base `20261103` in place of `20261101`, i.e. 100 entirely different query draws,
everything else identical.

| Case | `20261101` | `20261103` | worse episodes |
|---|---|---|---|
| spam | -6.661 [-6.77, -6.55] | **-6.581** [-6.72, -6.43] | 0/1 -> 0/1 |
| rialto | -5.310 [-6.00, -4.61] | **-5.309** [-5.96, -4.61] | 0/16 -> 0/16 |
| weather | -3.200 [-3.33, -3.07] | **-3.257** [-3.38, -3.14] | 0/3 -> 0/3 |
| openml_ldpa | -4.428 [-6.96, -2.60] | **-4.584** [-7.45, -2.68] | 2/32 -> 2/32 |
| uci_occupancy | -1.008 [-1.03, -0.99] | **-1.019** [-1.04, -1.00] | 0/4 -> 0/4 |

All five keep their sign, keep the CI entirely below zero, keep the same worse-episode count, and
agree in magnitude to within 1-3%. The effect is **not** an artefact of the particular query draw.

**What this does and does not fix.** It removes seed-dependence as an explanation, which matters
most for the three cases whose intervals are seed-level (spam, weather, occupancy). It does
**not** improve episode-level power: a second seed batch on a K=1 stream still has one episode.
The power caveat in the main table stands unchanged, and a fresh seed batch must never be
presented as additional episodes.

## Sensitivity across configurations (goal section 8), and a falsifiable test of the mechanism

`P7s - P3b` paired net-cost difference. S0 is primary (`B=200`, `c_q=0.05`, `c_s=5`);
S1 `B=400`; S2 `c_s=20`; S3 double delay; S4 `c_q=0.10`. Method frozen throughout.

| Case | S0 | S1 (`B=400`) | S2 (`c_s=20`) | S3 (2x delay) | S4 (`c_q=0.10`) |
|---|---:|---:|---:|---:|---:|
| spam | -6.661 | **-15.624** | -6.661 | -6.183 | -13.323 |
| rialto | -5.310 | -5.432 | -5.310 | -4.137 | -10.619 |
| weather | -3.200 | -5.881 | -3.200 | -3.171 | -6.399 |
| openml_ldpa | -4.428 | **-11.476** | -5.292 | not run | -7.729 |
| uci_occupancy | -1.008 | -2.795 | -1.008 | not run | -2.015 |

Every entry is negative: the method improves on P3b in **every case at every configuration
tested**, 23 of 23.

### The mechanism makes two exact predictions. Both were tested.

If the entire gain is the query-cost term `c_q N_q`, then the difference must be **invariant to
`c_s`** and **exactly proportional to `c_q`**.

| Case | S0 -> S2 (`c_s` x4) | S0 -> S4 (`c_q` x2) | verdict |
|---|---|---|---|
| spam | -6.661 -> -6.661 | -6.661 -> -13.323 (x2.000) | **holds exactly** |
| rialto | -5.310 -> -5.310 | -5.310 -> -10.619 (x2.000) | **holds exactly** |
| weather | -3.200 -> -3.200 | -3.200 -> -6.399 (x2.000) | **holds exactly** |
| uci_occupancy | -1.008 -> -1.008 | -1.008 -> -2.015 (x2.000) | **holds exactly** |
| openml_ldpa | -4.428 -> **-5.292** | -4.428 -> -7.729 (**x1.745**) | **fails** |

The prediction holds to the displayed precision on the four cases where deployment behaviour is
identical to P3b, and **fails on openml_ldpa** -- the one case where the gate changes deployment
behaviour (section 12 of `B3_PLUS_RESULTS.md`). The failure is therefore *predicted* by the
earlier finding rather than anomalous: on ldpa part of the difference is deployment loss and
switch cost, which do not scale with `c_q` and do respond to `c_s`.

This is the strongest internal evidence in the programme. A fitted effect would not reproduce an
exact scaling law on four datasets and then break on precisely the one dataset independently
shown to violate its premise.

### S1 is the configuration where the method matters most

Raising the budget to 400 roughly doubles to triples the gain on spam (-15.62), ldpa (-11.48) and
occupancy (-2.80), because a larger budget is simply more spend for P3b to squander after the
decision is settled: on spam P3b uses all 400 labels while P7s uses 87.5.

**rialto is the instructive exception** (-5.310 -> -5.432, essentially unchanged). Its
disagreement rate caps queries at about 165 even when 400 are available, so the budget never
binds and there is no extra waste to remove. The benefit therefore scales with *unspent budget
that P3b would otherwise consume*, not with the budget nominally granted. That is a sharper
statement of the mechanism than "saves labels", and it predicts where the method will and will
not help.

### S3 (double delay)

Gains persist and shrink slightly (spam -6.18, rialto -4.14, weather -3.17), with labels rising
(rialto 53.0 -> 76.4). A longer delay postpones the released evidence that lets the gate conclude
the decision is settled, so the policy spends longer at the paced rate. The method is not
excessively delay-sensitive. S3 was not run for the two new cases, and that is recorded rather
than interpolated.
