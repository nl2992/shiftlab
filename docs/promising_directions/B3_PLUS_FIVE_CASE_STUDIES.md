# B3+ five real-world case studies

Frozen method **P7s** (commit `e846107`); screening rule pre-registered in
`B3_PLUS_SCREENING_PROTOCOL.md` before any new dataset was downloaded. Every number below is
generated from saved per-episode records, not transcribed.

## Main table

Primary configuration for all five: `T = 2000`, `B = 200`, `c_q = 0.05`, `c_s = 5`, 100 shared
query seeds, seed base `20261101`. Net cost = deployment loss + `c_q N_q` + `c_s N_s`. `P7s-P3b`
is paired on identical episodes and seeds. `eps worse` is the number of episodes in which P7s
cost **more** than P3b.

**Caption (required, protocol section 5).** These five are a *selected* set. **34 datasets were
considered and 5 selected**: 27 new candidates were registered (14 reached stream validation, 4
reached locked-window evaluation, 2 succeeded) plus the 7 original B3 streams (3 succeeded; 4
failed the "switching must beat never-switching" condition). The 7 datasets named in the
pre-registered queue produced **0** successes; both new successes come from 11 candidates added
after that queue was exhausted. This is **not** an unbiased success rate, and the method was not
evaluated only on these five.

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
