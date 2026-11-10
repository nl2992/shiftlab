# 09 — Statistical certification (Workstream D)

Code: `scripts/paper1_scale25/stats/` (`certify.py` bounds, `ledger.py` attempt ledger and cohort certificate,
`sim_coverage.py`, `power_analysis.py`, `power_supp.py`, `init_ledger.py`; result tables in `results/`). Tests:
`tests/paper1_scale25/test_stats_certification.py` (26 tests). Ledger: [08](08_CONFIRMATION_LEDGER.md). Registration
template: [07](07_CONFIRMATION_PROTOCOL.md). Data for the power analysis: the 7 eligible fresh datasets of
[doc 20](../paper1_eqsdp/20_FRESH_CONFIRMATION_RESULTS.md) (`records_all.jsonl`, sha256 `32d1873e…d7254`, not
committed). All numbers below come from the committed scripts and `results/` tables. Nothing here is a confirmatory
result: it is machinery, simulation and a planning calculation.

## 1. Headline

- **Method.** Per dataset, a cluster-robust Fieller lower bound for the relative reduction `r_d`, taken as the minimum
  over two prespecified block lengths (`ceil(n^(1/3))` and `ceil(n^(1/2))`), with a `t_{n_blocks-1}` reference. The
  levels are `alpha_i = .05/(i(i+1))` by chronological attempt index. The cohort lower bound is the mean of the
  selected `L_d`. The union bound gives simultaneous validity for any selection, with no independence assumption.
- **Coverage (simulation).** Close to nominal when the paired gain has little serial dependence (as in the real
  data), conservative otherwise, and mildly anti-conservative only for strong dependence (AR coefficient 0.6). The
  Design-B simultaneous miss rate was 0.04–3.4% across scenarios, below .05 (section 4). Validity is asymptotic and
  simulation-supported, not a theorem.
- **Power.** Datasets with about 100 episodes need a point reduction of about **4.4%** each (per-dataset `L_25 >= 2.5`
  at `alpha_25 = 7.7e-5`; cohort of 25 at indices 1..25: **4.4%**, 4.7% at indices 8..32 after the 7 legacy
  indices). Datasets with about 40 episodes need about 7.2% at index 25 and cannot be certified at all beyond index
  about 40. The earlier rough figure of "3.5% or more" in doc 01 understates this by about 1 percentage point. The
  per-dataset requirement `L > 0` alone is cheap (1.8% at index 25 for `n >= 71`).
- **v1.** Cannot certify anything near the target. Against the strongest per-dataset reference, mean `r_hat` is
  0.375%, and mean `L` is -1.5% at indices 8..14; 1 of 7 datasets has `L > 0`. v1 against its parent EQ+cut has mean
  `r_hat` 0.433%.
- **More powerful valid alternatives** exist (section 6). The most useful: register a whole cohort in one batch and
  split the level equally (about 4.1% needed instead of 4.4%), and a pre-registered cohort-mean test (about 2.7%
  needed, but it needs independence across datasets and does not certify each dataset).

## 2. Estimand and bound

For dataset `d`, episodes `k = 1..n` are consecutive non-overlapping chunks of one chronological stream scored with
a shared fitted model pair. `b_k` = reference cost, `a_k` = new cost (each the mean over the 10 policy seeds of
`100 net/T`), `D_k = b_k - a_k`.

`r_d = 100 E[D] / E[b]`, estimated by `r_hat = 100 mean(D)/mean(b)`. `r_d` is a parameter of that stream
(conditional on the fitted pair and the realised stream), not a superpopulation quantity. Cohort `R(S) = mean_{d in S} r_d`.

**Bound.** Split the episodes into `n_B = floor(n/m)` contiguous blocks (sizes `m` or `m+1`). For `rho` in R put
`z_k(rho) = D_k - rho b_k`. The cluster variance of the mean of `z` is
`V(rho) = n_B/(n_B-1) * sum_j (Z_j - n_j zbar)^2 / n^2` (`Z_j` the block sums), and
`t(rho) = zbar(rho)/sqrt(V(rho))`. The one-sided `(1-alpha)` lower bound is the smallest `rho` with
`t(rho) <= t_{1-alpha, n_B-1}`. `t(rho)^2 = c^2` is a quadratic in `rho` (Fieller), solved in closed form. The bound is
`-inf` if the reference mean cost is not significantly positive. It inverts a test of the ratio itself, so it needs no delta-method
linearisation and stays defined when the SE is large.

**Primary rule.** `L = min( L_{m1}, L_{m2} )` with `m1 = max(2, ceil(n^(1/3)))` and `m2 = max(2, ceil(n^(1/2)))`
(for `n = 100`: 5 and 10). A minimum of lower bounds has a miss event contained in each component's miss event, so it
covers at least as often as the best calibrated block length. This protects against under-estimated dependence at
the price of power (section 5). The rule uses `n` only, so it is prespecified.

**Why not a bootstrap.** A studentised circular block bootstrap (`mbb_lower`) was implemented. Its resolution is
about `1/B`, so with `B = 20,000` it cannot go below `alpha ~ 1e-3`, but Design B needs `alpha_i` of `1e-4` and below
for `i >= 25`. In simulation at `alpha = .05` and `.01` it was not better calibrated than the block-t bound
(section 4). The block-t Fieller bound is therefore the analytic method used at tiny `alpha`; the bootstrap stays
as a sensitivity check where resolvable. The normal reference (`crit="normal"`) is *not* acceptable at tiny alpha
(section 4).

## 3. Design B, ledger and cohort certificate

- **Ledger** ([08](08_CONFIRMATION_LEDGER.md)). Attempts are indexed `i = 1, 2, ...` chronologically **at registration,
  before opening**, with `alpha_i = .05/(i(i+1))`. Every opened attempt counts, successful or not; registered but unopened
  attempts keep their index. The file is append-only with a sha256 hash chain. The Nov-9 doc 19/20 confirmation
  occupies indices 1..7 (legacy, excluded from cohorts).
- **Certificate** (`certify_cohort`). Success iff the selected set `S` has at least 25 distinct datasets (by
  `parent_source_id`), `L_d > 0` for all `d in S`, `R_lower(S) = mean_{d in S} L_d >= 2.5`, and the ledger validates.
  `S` may be chosen after seeing results.
- **Reporting.** Counts: registered, legacy-reserved, opened, positive (`r_hat > 0`), supported (`L > 0`), selected.
  Also the mean over *all* opened attempts with its simultaneous lower bound (mean of all `L_i`, including failures),
  and a descriptive cross-dataset t interval. The selected-cohort point mean is labelled as selected.

**Validity argument.** Let `E_i = {r_i >= L_i}` with `P(E_i^c) <= alpha_i`, where `alpha_i` and the parameter `r_i`
(dataset, window, method, reference) were fixed at registration, before that window's outcomes existed. Then
`P(union_i E_i^c) <= sum_i alpha_i <= .05`, whatever the number of attempts and however later attempts or the cohort
`S` were chosen (the schedule sums to `.05 N/(N+1) < .05` for any `N`). On the event `intersection E_i`, every
`S` has `R(S) >= mean_S L_d`. No independence between datasets or attempts is used. Adaptive continuation (opening more
attempts after seeing results) is covered, because the level of attempt `i` depends only on `i`.

**Assumptions the argument needs (and does not weaken):**
1. Each `P(E_i^c) <= alpha_i` is true. Here it is only asymptotic: it needs `(D_k, b_k)` to be stationary and weakly
   dependent with blocks long enough that block sums are nearly independent. A regime change inside a confirmation
   stream is part of the stream's `r_d` (the estimand is the stream mean), but strong trending dependence breaks the
   block-variance estimate.
2. Registration really precedes opening, and the dataset, window, method, reference rule and block rule are not
   altered after outcomes are seen. The ledger records the order and the chain makes interior edits detectable.
   Deleting trailing rows is not detectable by the file alone; the Git history anchors it.
3. The hidden choice of the reference is made without confirmation data. If the reference is the best of the panel on the
   *confirmation* window, `r_d` itself moves with the data and the claim becomes a claim against an oracle reference
   (very hard, and not what the bound certifies).
4. Inference is conditional on the fitted model pair and one realisation of the stream per dataset. It generalises
   to nothing beyond those streams, and the cohort claim is about the opened datasets, not about "datasets in general".

## 4. Coverage simulations

Generator: reference `b_k = 100(1 + cv_b x_k)`, gain `D_k = 100(r/100 + sd_D y_k)`, with `x`, `y` unit-variance AR(1) of
coefficients `phi_b = 0.55` and `phi_D`, innovation correlation 0.3, true `r = 2.5%`, `cv_b = .15`, `sd_D = .02`
(the real fresh data have `cv_b` .12–.32, `sd_D/mu_b` .01–.03, up to .08, and `phi_D` between -0.29 and +0.14 over the 21
dataset-reference series examined, so `phi_D` near 0 is the realistic case; `phi_D = .3, .6` are stress cases).
Innovations: Gaussian, Student-t5, centred lognormal (skew). 150,000 replications per cell
(`results/coverage_single.csv`). Cells show **miss rate / nominal alpha** (1 = exact; below 1 = conservative).

Primary bound (min over the two block rules), `n = 100`:

| `phi_D` | innovations | `alpha = .05` | `1e-3` | `1e-4` |
|---|---|---|---|---|
| 0 | Gaussian | 0.76 | 0.39 | 0.00 |
| 0 | t5 | 0.75 | 0.31 | 0.27 |
| 0 | lognormal | 0.35 | 0.01 | 0.00 |
| 0.3 | Gaussian | 0.90 | 0.49 | 0.13 |
| 0.3 | t5 | 0.92 | 0.61 | 0.47 |
| 0.6 | Gaussian | 1.24 | 1.33 | 1.40 |
| 0.6 | t5 | 1.24 | 1.31 | 1.67 |

For `n = 40` the ratios are similar or smaller (0.21–1.20 at .05; 0 to 0.79 at 1e-3 and 0 to 0.47 at 1e-4, with
`phi_D = .6` Gaussian/t5 giving 1.20, 0.79 and 0.47/0.40). At `alpha = 1e-4` an observed ratio near 1.4–1.7 means
about 21–25 misses against 15 expected in 150,000 replications; the absolute rate is `1.4–1.7e-4`.

Alternatives, same grid (full table in `results/coverage_single.csv`):

| method | what happens |
|---|---|
| cube-root block only | exact at `phi_D = 0` (0.99–1.00 at .05 and 1e-3), 1.5–1.8x at `phi_D = .3`, **5–8x at `phi_D = .6`** at small alpha |
| square-root block only | 1.0–1.4x at `phi_D = .3 / .6` for .05; 1.7–2.3x at `phi_D = .6` for small alpha |
| normal reference with cube-root blocks | **5.7x to 103x too many misses at `alpha = 1e-4`** for Gaussian/t5 innovations (n = 40: 22x to 103x), 2.7–23x at 1e-3 |
| iid episodes (blocks of 1) | fine at `phi_D = 0`, **18x to 310x too many misses** at `phi_D = .3 / .6`, alpha 1e-4 (Gaussian/t5) |

So the t reference and block clustering both matter, and the primary rule (the minimum) is the only variant that
stays near or below nominal everywhere except `phi_D = 0.6`.

**Studentised block bootstrap vs block-t** (600 replications, `B = 2000`, cube-root blocks, `results/coverage_mbb.csv`):
miss rates at `alpha = .05`: 4.2% vs 4.3% (n = 100, `phi_D = 0`), 7.3% vs 8.2% (`phi_D = .6`), 7.2% vs 7.2%
(n = 40, `phi_D = .3`); at `.01`: 1.3% vs 0.8%, 2.5% vs 2.8%, 2.0% vs 2.2%. The two are equivalent within Monte Carlo
error (600 replications, so ±1 point).

**Simultaneous coverage** (`results/coverage_joint.csv`; 25 datasets with heterogeneous `n` in 30–100, `cv_b`, `sd_D`,
`phi_b`, `phi_D` up to 0.3 or 0.6, true `r` in 0–5; the primary bound at each dataset's `alpha_i`; 20,000 replications):

| scenario | attempt indices | any-miss rate | sum of alpha_i |
|---|---|---|---|
| typical, Gaussian, `phi_D <= .3` | 1..25 | 2.9% | 4.8% |
| typical | spread over 1..60 | 0.30% | 1.1% |
| stress, lognormal, `phi_D <= .6` | 1..25 | 1.3% | 4.8% |
| stress, lognormal | spread over 1..60 | 0.04% | 1.1% |
| stress, t5, `phi_D <= .6` | 1..25 | 3.4% | 4.8% |
| stress, t5 | spread over 1..60 | 0.41% | 1.1% |

The family miss rate is below .05 in every scenario, as the union bound requires when each bound is valid; a single
index in the t5-stress spread run had 2.0x its nominal rate, absorbed by the small share of the budget at that index.
Before the primary rule was adopted, the cube-root rule alone gave 6.1% and 7.6% in the typical and t5-stress
`1..25` scenarios. Those runs were overwritten by the final ones; they are the reason for the minimum rule.

What the simulations do not cover: nonstationary gains (a late-adoption method whose benefit is concentrated in a
few episodes), a very small number of episodes (n < 35 is excluded by the eligibility gate), and misspecification of
the reference series. A fitted pair that drifts across the stream is part of the stream. Report the sensitivity bounds
(cube-root only) next to the primary; if they disagree in sign, treat the dataset as unsupported.

## 5. Power analysis (real fresh data)

Standard errors of `r_hat` (cluster-robust, percentage points of the reference cost; `results/power/se_summary.csv`):

| dataset | episodes | median SE over 26 references | SE vs EQ+cut | `r_hat` vs EQ+cut | SE vs strongest | `r_hat` vs strongest |
|---|---|---|---|---|---|---|
| sf | 100 | 0.30 | 0.16 | 0.41 | 0.16 (EQ+cut) | 0.41 |
| dallas | 100 | 0.26 | 0.26 | 0.81 | 0.26 (EQ+cut) | 0.81 |
| dc | 100 | 0.89 | 0.27 | 0.56 | 0.65 (online_llm_picker) | 0.39 |
| sandiego | 97 | 0.21 | 0.13 | 0.71 | 0.13 (EQ+cut) | 0.71 |
| austin | 71 | 0.28 | 0.19 | 0.29 | 0.20 (model_picker) | 0.20 |
| kc | 40 | 0.35 | 0.21 | 0.07 | 0.34 (econF_mo5_m0) | -0.09 |
| cincinnati | 39 | 0.34 | 0.25 | 0.18 | 0.25 (EQ+cut) | 0.18 |

Typical SE is 0.2–0.35 points at 100 episodes and 0.3–0.35 at 40 episodes, but `dc` (a few heavy episodes) is
about 0.9. SE against a materially different method is larger than against the near-identical EQ+cut; the second
column is the relevant planning value for a v2. These SEs come from the episode-level variability of the actual
policies, and scale like `1/sqrt(n)`.

**Required point reduction.** Smallest `r_hat` for which the primary bound reaches the threshold, keeping each real
series' variability and dependence (shifting only the mean gain). Median over the 25 non-parent references, by
episode count (`results/power/needed_r_all.csv`):

| attempt index `i` | `alpha_i` | `n >= 71`: `L > 0` | `n >= 71`: `L >= 2.5` | `n <= 40`: `L > 0` | `n <= 40`: `L >= 2.5` |
|---|---|---|---|---|---|
| 1 | .025 | 0.63 | 3.16 | 0.94 | 3.48 |
| 2 | .0083 | 0.83 | 3.36 | 1.34 | 3.85 |
| 5 | .0017 | 1.12 | 3.66 | 2.05 | 4.61 |
| 10 | 4.5e-4 | 1.38 | 3.97 | 2.89 | 5.48 |
| **25** | **7.7e-5** | **1.83** | **4.43** | 4.57 | 7.20 |
| 40 | 3.0e-5 | 2.10 | 4.70 | not reachable | not reachable |
| 60 | 1.4e-5 | 2.38 | 4.98 | not reachable | not reachable |

"Not reachable": with about 5 blocks the `t_4` critical value is above 15 at these levels and the bound is infinite. A
dataset with about 40 episodes (sqrt rule: 5 blocks) is effectively unusable in Design B beyond index about 30–40. Use
longer confirmation windows (more episodes) or fewer, earlier attempts. Per-dataset spread at index 25, `L >= 2.5`
(median over references): sandiego 3.8, dallas 3.9, sf 4.4, austin 4.8, cincinnati 7.0, kc 7.7, dc 8.0.

**Cohort of 25 with a common true reduction** (mean `L >= 2.5`; `n >= 71` structures; `results/power/cohort_needed_n71.csv`):

| design | primary rule: needed common `r_hat` | cube-root only (sensitivity) |
|---|---|---|
| B, indices 1..25 | 4.36 | 3.86 |
| B, indices 8..32 (after 7 legacy) | 4.67 | 4.03 |
| B, 25 successes at random among 40 attempts | 4.96 | 4.08 |
| B, 25 successes at random among 60 attempts | 5.25 | 4.03 |
| A1: one pre-registered cohort, Bonferroni `.05/25` | 3.90 | 3.62 |
| B': batch registered together, `.025/25` each | 4.07 | 3.73 |
| no multiplicity, `.05` each (reference only) | 3.16 | 3.09 |

With datasets of 40 episodes included, the same cohort needs about 4.9% at indices 1..25 (primary rule,
`results/power/cohort_needed.csv`), and an unattainable value beyond index about 40.

**Reading.** The headline is **a point reduction of about 4.4% against the strongest reference on every one of 25
datasets of about 100 episodes** (5% if 60 attempts are opened), not 2.5%. The excess over 2.5% is the price of
simultaneous inference (a critical value of about 6.2 at df 9 and `alpha = 7.7e-5`, times an SE of 0.3). Against the
doc 01 headroom ceiling (total avoidable regret of the strongest reference vs the best fixed model about 6.1%, concentrated
in late adoption), 4.4% on every dataset would be more than 70% of all avoidable regret. That is a strong
signal that a 25-dataset all-positive certified 2.5% is a very ambitious target for any method aimed at the same
regret, independent of the statistics. The result is also sensitive to SE: halving the SE (four times the episodes)
would bring the requirement to about 3.4%.

**Monte-Carlo success probability** (`results/power/power_mc.csv`; each `r_hat_d ~ N(r, SE^2)`, t critical values at the
stated df, 25 datasets, success = all `L > 0` and mean `L >= 2.5`; 4000 draws; df 9 = about 100 episodes under the sqrt
block). The transition is sharp because the SE is common: at SE 0.25, df 9, success probability is 0 at true `r = 3.5`
for B and 0.80 for A1, and 1 at `r = 4` for both; at SE 0.40, df 9, it is 0 at `r = 4` and 1 at `r = 5` (B with 25 attempts), but at 60 attempts
only 0.54 at `r = 5`. Treat the table as "the true common reduction must be at least about 4.5–5.5% to have a good
chance"; heterogeneity (some datasets at 1%) lowers the chance further because the mean and the all-positive condition
both bind.

## 6. Alternatives and their validity

| alternative | needed `r_hat` (cohort of 25, `n >= 71`) | validity conditions | verdict |
|---|---|---|---|
| **B** (the brief): per-attempt `alpha_i`, per-dataset L, mean L | 4.4 (1..25), 4.7 after legacy | union bound only | valid, no independence; pays for an open-ended sequence |
| **B' batch**: all datasets registered at the same time share `alpha_j/M_j` with `alpha_j = .05/(j(j+1))` | 4.1 (M = 25, j = 1) | union bound; batch composition fixed at registration | valid, about 0.3 more power than B; recommended if registering a whole cohort |
| **A1**: one pre-registered cohort, Bonferroni `.05/K` | 3.9 (K = 25) | union bound; cohort fixed before opening, no later additions | valid and the most powerful of the "each dataset certified" designs; larger `K` helps |
| **A2**: cohort-mean bound at `.05`, no per-dataset gate | about 2.7 | independence (or a stated dependence model) across datasets; mean claim only | valid for the claim "mean reduction >= 2.5" only; does not say each dataset improved; the independence of datasets that share cost parameters is plausible but not proven |
| **Dev-screen allocation**: spend `alpha` only on datasets that pass a dev screen | same as A1/B' with a smaller `K` | screen uses development data only, independent of the confirmation outcome; screened-out datasets are not opened | valid and strictly cheaper; the cohort is then "screened datasets" and must be disclosed as such |
| **Closed testing / Holm on positivity** | helps only the `L > 0` gate | Holm gives familywise control of "which datasets improved"; it does not give simultaneous lower bounds on magnitude unless extended (sequentially rejective intervals) | partial; the 2.5% magnitude is the binding requirement, not positivity |
| **FDR (BH/BY)** | not applicable | controls the expected false share, needs PRDS or a log penalty | does not certify a magnitude (no lower bound on `r`) and an alarm does not establish harm reduction; not a substitute |
| **Longer confirmation windows** | scales as `1/sqrt(n)` | stationarity within the stream | the strongest lever: 4x episodes gives about 3.4 |

Recommendation: keep Design B as the brief's default, with the 7 legacy indices reserved; if the registration is a
single cohort, prefer **B' batch** (or A1) and state it in the protocol before registering. Report A2 as a secondary
claim ("mean reduction at least X, assuming independence"), never as the certificate. Prefer confirmation windows of at
least 100 episodes per dataset.

## 7. What the current v1 would certify

`results/power/v1_would_certify.csv`, 7 fresh datasets, EQ+pair (v1) vs reference, primary bound:

| reference | design (alpha) | mean `r_hat` | mean `L` | datasets with `L > 0` | certifies 25 / 2.5%? |
|---|---|---|---|---|---|
| EQ+cut (doc 19 H1) | B at indices 8..14 | 0.433 | -0.90 | 1/7 | no |
| EQ+cut | B at indices 1..7 | 0.433 | -0.33 | 2/7 | no |
| EQ+cut | A1 Bonferroni, K = 7 | 0.433 | -0.24 | 2/7 | no |
| per-dataset strongest reference | B at indices 8..14 | 0.375 | -1.48 | 1/7 | no |
| per-dataset strongest reference | B at indices 1..7 | 0.375 | -0.75 | 2/7 | no |
| per-dataset strongest reference | A1 Bonferroni, K = 7 | 0.375 | -0.58 | 2/7 | no |

(The strongest reference is chosen per dataset by mean `J` on the same data, a harsh and slightly reference-favouring
choice. Only 7 datasets exist, so no cohort of 25 is possible.) Under this method, v1's 7/7 negative signs from
doc 20 are consistent with a positive effect but the magnitude is certified as non-positive on most datasets once
dependence and 7-fold multiplicity are priced in. The legacy rows in the ledger record the retro-computed bounds
for EQ+pair vs EQ+cut at their reserved levels (positive on sf, dallas, sandiego; negative on kc, austin, cincinnati,
dc).

## 8. Recommendation and open items

1. Use **primary block-Fieller bounds** (section 2) with the ledger and certificate; report cube-root-only and bootstrap
   sensitivity.
2. Plan on a required per-dataset point reduction of about **4.4–5%** for `n ~ 100`; do not plan registration for
   datasets below about 70 episodes unless the batch design is used.
3. Register one cohort in one batch (B' or A1) when possible; keep Design B for incremental additions.
4. Increase episodes per confirmation window (the main lever) rather than loosening the bound.
5. Keep the claim honest: certified cohort lower bound `R_lower`, the full ledger counts, and the all-opened mean; a
   selected-cohort point mean is a winner's-curse figure.
6. Open: (i) a bound that uses an estimated dependence length from development data (could recover power if the gain
   is white, as observed); (ii) coverage under nonstationary gains; (iii) whether reference choice by development data
   needs its own error term; (iv) cluster-robust estimation by seed rather than by episode was not studied (the seed
   average is treated as one series).

Reproduce: `python scripts/paper1_scale25/stats/sim_coverage.py {single,joint,mbb} --out results/...`,
`python scripts/paper1_scale25/stats/power_analysis.py --records <records_all.jsonl> --out results/power`,
`python scripts/paper1_scale25/stats/power_supp.py <records_all.jsonl> results/power`, `pytest tests/paper1_scale25`.
