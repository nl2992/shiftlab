# 12 — Stage 1 single-component results (nine datasets, even episodes)

Run 2026-11-08 on `research/paper1-eqsdp-foundation-2026-11-08`, following the locked plan
`10_JOINTBAYES_PLAN.md` §4 Stage 1 and the Stage 0 headroom note `11_STAGE0_HEADROOM.md`.
Development data, even episodes only (377 episodes x 10 policy seeds = 3,770 jobs per policy),
so everything here is descriptive and selection-optimistic, not confirmatory. Odd episodes were not opened.
Every number comes from `scripts/paper1_eqsdp/stage1_analysis.py` output (tables `tables/stage1_*`).

## Stage-0 amendment (recorded before any Stage-1 run)

Label spend is 1.84% of J_ref while doubling the budget gains only 0.23-0.32% excluding fees
(11_STAGE0_HEADROOM.md). C1 is therefore re-targeted at the fee side: buy fewer labels where they cannot change a
decision. C2 and C5 are unchanged.

## Contract, reference and what a policy may see

B=200, c_q=.05, c_s=5, T=2000, delay as registered per dataset (100 on every dataset I ran). Reference baseline
`wald_l0.97_g0.2` (J_ref = 478.075, equal-dataset mean); arm R `EQSDp_l0.98_g0.3` (478.154). The reference rows are
read from the Stage-0 records (identical keys); candidates and controls are paired to them by (dataset, episode, seed).
Policies see only the event (t, predictions), the remaining budget, released paired losses, and the declared contract
(T, B, c_s, delay). Tests check that the policy module never references evaluator names.

## Policies as built (`scripts/paper1_eqsdp/stage1_policies.py`)

All subclass the frozen `EQSD`, draw labels from the same named random stream as arm R (`r("EQSD")`), and with their
extra mechanism inert equal arm R **exactly** (checked on all 3,770 jobs: `s1base`, `s1c1_r0_s0_h0`,
`s1c5_degenerate` max |net diff| = 0; arm R re-run vs Stage-0 records max |diff| = 0; `s1wald_inert` vs the
reference max |diff| = 0). Evidence is arm R's: discounted disagreement counts (lambda=.98) and Beta(k+1, n-k+1).

- **C1** (reachability gate + shadow price). After the arm-R draw says "buy", compute L = pending + 1 + h labels
  (in-flight labels are simulated, not observed). Find the least number of opposite outcomes after which arm R's own
  switch test passes at release time t+delay (equal-weight approximation of the discount weights) and take the
  Beta-binomial tail probability P(cross). Skip when P(cross) < rho0 (1 + s min(pressure,10)), where pressure =
  max(0, expected remaining disagreements / virtual remaining budget - 1). A skipped label is still bought with
  probability 0.1 (floor, prevents lock-in), and skipped draws are debited from the pacer's budget view (kappa=1) so the pacer
  does not simply catch up. If no outcome can pay back c_s before T, P(cross)=0, so the end-of-horizon stop is implicit.
  Grid: rho0 in {.01,.03,.1} x s in {0,1} x h in {0,6} = 12.
- **C2** (persistent advantage + option value). Arm R still proposes the switch (promotion or reversal); it is executed only
  if posterior V_now >= V_wait and V_now > 0. G(a,H) = a r E[min(tau,H)] - c_s - P(tau<H)(1+omega) c_s with a geometric
  advantage lifetime of hazard hz; V_now = E_post[G]; V_wait = (1-hz)^w E[max(0, G(a~, H-w))] with a~ from a
  Monte Carlo preposterior update (64 draws) using the labels expected in w events. It can only delay arm R's switches.
  Grid: hz in {1/500,1/1000,1/2000} x w in {50,150} x omega in {0,.5} = 12.
- **C5** (early adoption + conservative reversal). Promote when (2Q(g_t)-1) r (T-t) > c_s with g_t = .3 + (g_early - .3)(T-t)/T
  and posterior P(p<=1/2) <= cap; reverse with arm R's rule at the more extreme level g_rev.
  Grid: g_early in {.4,.5} x cap in {.15,.3} x g_rev in {.3,.15,.05} = 12.

Matched controls (pre-listed, run in the same jobs): C1 (i) uniform thinning with keep-probability k and the same
pacer debit, (ii) hard end-of-horizon stop (no purchase if t+delay > T-H); C2 arm R with an additive hurdle margin
m (parent `margin`), matched on the promotion rate in not-better episodes; C5 arm R with a fixed larger gamma, matched on mean
first-deployment time on challenger-better episodes (never promoted counted as T).

## Commands

```
export OPENBLAS_NUM_THREADS=1
PY="<main checkout>/.venv/Scripts/python.exe"
$PY scripts/paper1_eqsdp/stage1_run.py --cand c1 --workers 16     # also c2, c5   (launched detached; roughly 10-20 min each)
$PY scripts/paper1_eqsdp/stage1_run.py --cand c1 --ext --workers 16   # extended controls + Wald-stop, ~1.5 min
$PY scripts/paper1_eqsdp/stage1_analysis.py                        # tables/stage1_*.csv, summary json
$PY -m pytest scripts/paper1_eqsdp/tests -q                        # 20 tests
```

## Headline (paired vs the reference `wald_l0.97_g0.2`; Delta J < 0 is better; % of J_ref)

95% CIs are percentile intervals over episode bootstraps (2,000 resamples) within dataset, averaged with equal
dataset weights. "Best" is best-of-grid on the same even episodes that are scored, so it is optimistic; the grid median
(the configuration nearest the median Delta J, and the median Delta J) is given beside it.

| cand | best config | best Delta J vs ref (units, %) [95% CI] | datasets better | Delta L/T (pp) | best vs arm R | grid median Delta J vs ref | verdict |
|---|---|---|---|---|---|---|---|
| C1 | `s1c1_r0.03_s0_h6` | -4.343 (-0.908%) [-5.766, -2.453] | 8/9 (1 worse) | +0.100 [+0.030, +0.197] | -4.422 (-0.925%) [-5.727, -2.718] | -3.221 (-0.674%), 11 of 12 configs < 0 | **continue** |
| C2 | `s1c2_hz1000_w150_o0.0` | -0.035 (-0.007%) [-0.320, 0.264] | 4/9 (5 worse) | -0.015 [-0.027, -0.001] | -0.114 (-0.024%) [-0.520, 0.301] | +0.183 (+0.038%), 1 of 12 < 0 | stop |
| C5 | `s1c5_ge0.4_c0.3_gr0.15` | -0.178 (-0.037%) [-0.893, 0.577] | 6/9 (3 worse) | -0.024 [-0.057, 0.010] | -0.256 (-0.054%) [-0.867, 0.394] | +0.297 (+0.062%), 2 of 12 < 0 | stop |

Arm R vs the reference: +0.079 (+0.016%) [-0.395, 0.555], 2 of 9 datasets better (a tie, as in Stage 0). The full grids are in
`tables/stage1_c{1,2,5}_grid.csv` (both comparisons), control grids in `stage1_c*_control_grid.csv`, and the best
configuration, arm R, matched controls and candidate-minus-control rows in `stage1_c*_best.csv`.

## Components that moved (best config minus reference, loss units per episode; negative is better)

Same Stage-0 decomposition via `trace_run`; the five components sum to Delta J.

| | labels | switches | late adoption | false promotion | reversal churn | label spend | residual | Delta J |
|---|---|---|---|---|---|---|---|---|
| C1 best | -135.2 | +0.082 | -0.092 | +2.263 | +0.333 | **-6.761** | -0.087 | -4.343 |
| C2 best | 0 | +0.052 | -0.453 | +0.209 | +0.223 | 0 | -0.014 | -0.035 |
| C5 best | 0 | +0.061 | **-2.206** | **+1.965** | +0.023 | 0 | +0.040 | -0.178 |
| control: C1 thinning k=.25 | -131.8 | -0.041 | +6.003 | +2.548 | -0.121 | -6.591 | -0.135 | +1.704 |
| control: C1 hard stop H=1500 | -141.1 | -0.016 | +1.234 | +3.133 | -0.037 | -7.056 | -0.202 | -2.927 |
| control: C2 hurdle m=12 | 0 | -0.011 | -0.561 | +0.676 | -0.009 | 0 | -0.130 | -0.024 |
| control: C5 gamma=.35 | 0 | +0.470 | -1.528 | +0.394 | +1.994 | 0 | +0.062 | +0.923 |

Arm R: mean labels 176.3, switches 1.37; C1 best: labels 41.1, switches 1.20. Mean wall time per run: arm R 0.038 s,
C1 0.075 s, C2 0.040 s, C5 0.039 s (the reference's time is not recorded in Stage 0).

## C1 — decision-reachability gating: continue, with a strong caveat on what drives the gain

- Mechanism signal is on the target: label spend falls by 6.76 (labels 176 -> 41); the price is +2.26 false promotion, +0.33
  churn and +0.10 pp loss. The net -4.34 (-0.91%) has a CI excluding 0 and 8 of 9 datasets better. All 6 s=0 and 4 of the 6 s=1
  configurations beat the reference with a CI excluding 0; the two weakest
  (rho0=.1, s=1) lose their gain (+1.0 and -0.56, CIs include 0) because a large shadow price starves the labels.
- **Most of the gain is a generic fee cut, not reachability.** The matched controls at the same label count:
  - uniform thinning (nearest k=.25, 44.5 labels): +1.70 vs the reference. Best C1 minus this control = -6.05 (-1.27%) [-7.15, -4.98].
    Random thinning at ~40 labels destroys the decision evidence.
  - hard end-of-horizon stop (nearest H=1500, 35.2 labels): -2.93 vs the reference (-0.61%) [-4.87, -0.55] — this simple rule keeps
    about two thirds of C1's gain. Best C1 minus this control = **-1.42 (-0.30%) [-2.44, -0.48]**, 8/9 datasets, while C1 buys 6 more
    labels. The neighbouring stop grids bracket C1's count (H=1300: 53.2 labels, -3.25; H=1500: 35.2 labels, -2.93), so linear interpolation at 41.1 labels
    puts the control near -3.03, i.e. C1 is about 1.3 units better than an equal-label stop.
  - Part of every stop's gain is free: purchasing in the last `delay`=100 events can never be released. `s1wald_stop_H0` (the reference with no
    purchases that cannot be released) gains -0.42 [-0.44, -0.40], 9/9 datasets.
- **Supplementary, not pre-listed: the reference with the same hard stop** (`s1wald_stop_H*`, same Wald rule and 0.97/0.2 tuning, no re-tuning).
  The best is H=1500: -3.36 (-0.70%) [-5.16, -1.08] vs the reference at 35.2 labels (H=1300: -2.99; H=1100: -3.06; H=700: -2.48; H=300: -1.77). Best C1 minus the Wald+stop at H=1500
  is -0.98 (-0.21%) [-2.05, -0.05], and minus H=1300 is -1.36 (-0.28%) [-2.43, -0.38]. So against a baseline that gets the same cheap fee cut, C1's
  incremental effect is about 0.2-0.3% of J_ref, with a CI that barely excludes 0 at H=1500, and it is the best of a 12-config grid. This is the honest size of the
  "reachability" contribution; the fee cut itself is available to any policy and should be added to the reference baseline for any later stage.
- Relation to prior failures: C1 does the opposite of D1 (ambiguity bursts add labels); it is not B1 (asymmetric levels). It does not degenerate into either.
  It is, however, close to "stop buying labels late", and the controls show that.
- Accuracy cost: Delta L/T = +0.100 pp [+0.030, +0.197] (best), +0.09 to +0.44 pp across the grid. The Stage-3 freeze limit is <= 0.1 pp, so the best sits on the edge.

Verdict: **continue** (Delta J < 0 with the CI excluding 0 for the best and for 10 of 12 grid configurations),
but carry forward Wald+hard-stop as the stronger reference and treat 0.2-0.3% as the effect size to beat in Stage 2.

## C2 — persistent-advantage belief + reversal option value: stop

- No configuration beats the reference with a CI excluding 0 (best -0.035, CI [-0.320, 0.264], 4/9 datasets). Grid median +0.183.
- The mechanism acts on what it targets, but the net is zero: the promotion rate in not-better episodes drops from 0.716 (arm R) to 0.595, and reversal
  churn falls (-0.78 vs arm R), but late adoption rises (+0.97 vs arm R; mean adoption time 267 vs 203 events) and false promotion is only -0.25 vs arm R.
- Matched control, arm R with an additive hurdle m=12 (promotion rate 0.600 vs C2's 0.595): -0.024 vs the reference. Best C2 minus control = -0.011 (-0.002%) [-0.530, 0.520],
  5/9 datasets. C2 is indistinguishable from "arm R made more conservative". It is the B1/E-type outcome the plan warned about.

## C5 — risk-aware early adoption + conservative reversal: stop

- Best -0.178 (-0.037%), CI [-0.893, 0.577], 6/9 datasets; grid median +0.297. Only 2 of 12 configs are below 0, and the two cap=.15, g_rev=.05 configs
  are significantly worse (up to +1.08 [0.15, 2.20]).
- Late adoption does move (-2.21 vs the reference) but false promotion rises by almost the same amount (+1.97); the best config's mean adoption time is 199 events vs arm R's 203, so the
  horizon-dependent quantile barely advances adoption: with delay 100 the first usable evidence arrives around t=200, where g_t is already near .3.
- Control (fixed larger gamma, nearest in adoption time within the pre-listed grid: gamma=.35, 177 events vs C5's 199): +0.92 [0.37, 1.46]. Best C5 minus this control = -1.10 [-1.79, -0.31]. That
  advantage is against a control that adopts earlier than C5 (so it is not a matched comparison) — arm R itself (203 events) is the closest match, and best C5 vs arm R is -0.256 [-0.867, 0.394], a tie.
  The reversal half is B1-style asymmetric hysteresis, which the screen had already found to tie.

## Selection and other caveats

- Best-of-grid on the scored episodes is optimistic: the median configuration is reported next to every best. For C1 the whole grid is mostly good (median -0.67%); for C2 and C5 the median is slightly worse than the reference.
- The reference was also selected on these even episodes; Wald+stop and C1 were tuned with only 12-14 settings each, but no other re-tuning of C1's `floor`, `kappa` or the horizon of the Beta-binomial approximation was done.
- Three episodes of three datasets were run with a few policies as a smoke check before launching; the grids were not changed afterwards.
- The Beta-binomial reach probability uses an equal-weight approximation of the discount and assumes the lookahead labels are bought; this is a heuristic gate, not a validity guarantee.
- Nothing here is confirmatory. The paper-1 null/validity claims are untouched: this is a cost-policy study under the fixed simulator contract.

## Deviations

1. The first C1 control grids (thinning k >= .4, stops H <= 700) could not reach C1's 30-47 labels, so they were extended after seeing the first C1 result (thinning to k=.05; stops to H=1750) and re-run (`c1_ext`). The control grids for C2 and C5 were not changed.
2. Supplementary Wald+hard-stop runs were added (not in the plan) because the first C1 comparison made a fee-cut-only baseline necessary.
3. `trace_run.py` (Stage 0 code) gained registry hook, `first_deploy`, `better`, `secs` fields; Stage-0 equality was re-verified on all 3,770 even-episode jobs.
4. Matching of controls uses the nearest grid point rather than interpolation; C5's control grid starts at gamma=.35.
5. The statistic "mean time to adoption" counts never-promoted episodes as T and averages over challenger-better episodes.

## Decision

Stage 1: **C1 continues**, C2 and C5 stop. Per plan §5 this does not stop the method search, but the only live
component is a label-fee reduction whose cheap form (a hard stop) is available to the reference. Stage 2 (combinations) has only one
surviving module, so the useful next step is to retune the reference and arm R with the same stop and re-test C1 against that, before any odd-episode (Stage 3) run.
