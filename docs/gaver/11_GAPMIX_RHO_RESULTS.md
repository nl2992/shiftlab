# GAVE-R WP1b: removing Gap-Mix's dependence limit (development/screening only)

Branch `research/gave-r-2026-11-06`. Follow-up to [WP1](10_GAPMIX_RESULTS.md). No confirmation seeds.
Seeds: registry block `gaver_wp1b_rho_mixture` = 101200000-101259999 (null 101200000-101209999, alt
101220000-101243999; seed = start + 1000*cell + replicate).

## 0. Pre-declaration (committed before any WP1b run)

### Question

With a declared `rho_bar=0.8`, `exact0.8_s4` is valid for rho<=0.8 and fails at rho=0.95 (FP .71-1.0). With
`rho_bar=0.95` fixed, power falls below the existing Markov LR. Is there a construction that is valid up to
rho=0.95 (ideally 0.99) and keeps most of `exact0.8_s4`'s power?

### Setting (identical to WP1)

`Family3CellSpec` Markov streams, T=1000, d=10, alpha=0.1, h=0.1, q0=0.55, uniform calendar, budgets
B=100 and B=250 (bt .1/.25). Declared null for everything below: stationary two-state round chain,
`p<=q0`, `rho in [0, 0.99]` (0.99 is the hard cap of the declared class), deterministic calendar,
constant delay, conditioning on each start's first label. Restart mixture `s4` (starts at event rounds
{0,.25T,.5T,.75T}) throughout. Only the first episode carries evidence (`episode_front`), so one evidence
object per stream.

* Null: rho in {0, .5, .8, .95, .99} x B in {100, 250}, 500 streams per cell (10 cells), one-sided 95%
  Clopper-Pearson UCB on "any promotion while regime non-favourable".
* Power: WP1's four alternatives (early persistent strong, late strong, transient strong, early medium;
  rho in {0,.5,.8}; B in {100,250}); 60 paired seeds per cell (24 cells, 1440 streams). Metric "detect" =
  promotion while the on-regime is active; paired bootstrap 95% CI.
* Primary success criterion (declared): a *valid* variant (null UCB <= 0.10 in all ten null cells, i.e.
  rho up to 0.95 required, 0.99 desired) whose pooled detection gain over `mlr_default8` is at least half of
  `exact0.8_s4`'s gain over `mlr_default8` on the same paired streams. Graded on the fair scale, not as a
  single pass/fail gate.

### Which constructions are valid (argument, written before looking at results)

Let `H(r) = {stationary chain, p<=q0, rho<=r}`. The nulls are nested: `H(0.5) < H(0.8) < H(0.95) < H(0.99)`.
`E^(r)` denotes the exact-gap Gap-Mix e-process with certified denominator over rho in [0, r]. It is a
test martingale (or dominated by one) under every member of `H(r)`, and in general **not** an e-process under
`rho* > r`.

1. **Plain mixture** `sum_k w_k E^(r_k)`, `r in {.5,.8,.95,.99}`. Under a truth with `rho*`, components with
   `r_k < rho*` are not e-processes (WP1 measured this at r=.8, rho*=.95: FP .71-1.0), so the mixture's
   expectation is not bounded by 1. Under `rho*=0.99` only the `r=0.99` component is valid. A mixture
   is therefore valid only if the weight on invalid components is zero, i.e. only if `rho*` is known.
   **Invalid for the declared range; run only as a negative control** (`mixnaive_eq`, `mixnaive_w`).
2. **Min over components** `min_k E^(r_k)`: `<= E^(0.99)`, which is valid, so it is valid, but it is pointwise
   dominated by the single `r=0.99` component; strictly no better than variant C. **Not run** (dominated).
3. **Nested/sequential test** of "rho<=r_k" rungs: a test valid for all of `H(0.99)` has to control the
   `rho=0.99` member, so any gain over `E^(0.99)` can only come from *data-dependent* information about
   rho. The remaining valid route is therefore to learn rho from the same released labels with an
   anytime-valid confidence sequence and pay for it with an alpha split. This is B/A-gated below.

**Confidence sequence (CS) for rho.** Under the null, for a fixed gap `g` and previous state `s` the successor
`Z_k | (Z_{k-1}=s)` is Bernoulli `a_{s,g}` independent of earlier history (Markov property, gaps fixed by the
deterministic calendar; the subsequence of such successors is i.i.d. by optional skipping). Moreover
`a_{1,g}-a_{0,g} = rho^g`. For each (gap, state) group with `n` successors we use one-sided Clopper-Pearson
bounds at level `eps = delta_g / (2 n (n+1))` (sum over n <= `delta_g/2`), with `delta_g = delta / (j(j+1))`
for the j-th distinct gap seen (sum <= delta). With probability `>= 1-delta`, simultaneously for all
times, gaps, and groups: `a_{1,g} <= UB`, `a_{0,g} >= LB`, so `rho^g <= UB_1-LB_0`, and
`rho <= min_g (UB_1-LB_0)^{1/g}` (running minimum; capped at 0.99 by the declaration). Call this `ub_t`;
the CS event is `G = {ub_t >= rho* for all t}`, `P(G^c) <= delta`.
Level split: `delta = 0.2 alpha = 0.02`, and the e-process alarm threshold is `1/(0.8 alpha)` = 12.5, so
the total failure probability is `<= 0.02 + 0.08 = 0.10` (Ville plus a union bound).

**B2, `exactcs_s4` (data-driven rho_bar, exact-gap).** At time t use the denominator sup over
`rho in [0, ub_t]` (cells covering `[0, ub_t]`). On `G`, `D_t(ub_t) >= D_t(rho*) >= L_t(theta*)`, so
`M_t / D_t(ub_t) <= M_t / L_t(theta*)`, and `M_t / L_t(theta*)` (numerator = fixed alternative mixture) is a
test martingale under `theta*` for every null member; the restart average of such martingales is one too.
So `P(exists t: E_t >= 1/alpha_2) <= P(G^c) + alpha_2 <= delta + alpha_2` by Ville's inequality. This is a
pathwise domination on `G`, not a predictable-plug-in argument, so it needs no predictability of `ub_t`.
Validity is exact for the declared contract (it inherits the WP1 caveats: stationary Markov null, closed-loop
and informative-delay validity unproven); the CS itself is conservative (union over n via `1/(n(n+1))`).

**A-gated, `gate_eq_s4` / `gate_w_s4` (discrete ladder, CS-gated mixture).** Components `E^(r_k)` for
`r in {.5,.8,.95,.99}`, fixed weights (equal; and `.15/.5/.2/.15`), read out as
`E_t = sum_{k: r_k >= ub_t or k = top} w_k E^(r_k)_t`. On `G` every included component has `r_k >= rho*` (the
top one by the declaration), hence is an e-process, so `E_t <= sum_{k valid} w_k E^(r_k)_t`, a test
supermartingale with initial value `<=1`; same Ville + union bound with the same alpha split. It is a
coarser, weight-penalised version of B2 and is run to answer the "mixture" question directly.

**B1, `envcs_s4` (data-driven rho_bar, envelope).** The envelope factor with `u_t = q0+(1-q0) ub_{t-1}^{g}` where
`ub_{t-1}` uses labels strictly before the current one (predictable). On `G`, `u_t >=` the true conditional upper
bound, so each factor has conditional expectation `<=1` (the WP1 argument), and the process coincides with the
supermartingale built from the true bound on `G`; same alpha split. Because the plug-in `r` is prequential this
needs only the one-step bound.

**C, `exact0.99_s4`** (composite rho nuisance over [0, 0.99]): the WP1 exact-gap construction with
`rho_bar = 0.99` (certified sup extended to 0.99; 198 cells of width 0.005). Valid on the whole declared class,
no alpha split.

### Variants run (all are `episode_front` gates, s4 restart mixture)

| name | construction | valid on rho<=0.99? | studies |
|---|---|---|---|
| `exact0.8_s4`, `exact0.95_s4`, `mlr_default8` | WP1 references (rerun on the new seeds) | no / yes / yes (as in WP1) | null, power |
| `exact0.99_s4` | C | yes | null, power |
| `exactcs_s4` | B2 | yes (alpha split) | null, power |
| `gate_eq_s4`, `gate_w_s4` | A-gated, equal / `.15,.5,.2,.15` | yes (alpha split) | null, power |
| `envcs_s4` | B1 | yes (alpha split) | null, power |
| `mixnaive_eq_s4`, `mixnaive_w_s4` | plain mixture, negative control | no | null only |

If time permits, one extra ladder `gate_fine_eq_s4` with `r in {.5,.65,.8,.9,.95,.99}` (equal weights) is added as a
declared exploratory variant; it is reported separately and not used for the primary criterion.

### Declared reporting rules

Report every variant, including negative ones. A variant is called *valid in this evidence* only if the null
UCB is <= 0.10 in all ten null cells; passing means not rejected at 500 streams per cell, not proved
(the proof is the argument above plus the stated caveats). The tests in `tests/test_gaver_gapmix_rho.py` check
the components of the argument (factor expectation, CS coverage, certified-sup equivalence), not the whole
pipeline.

## 1. Results

Code: `src/shiftlab/gaver/gapmix_rho.py` (imports `gapmix.py`, unmodified), runners
`scripts/gaver/run_gapmix_rho_{null,power,summarize}.py`, tests `tests/test_gaver_gapmix_rho.py`. Runs used
commits `6d9e71b2` (code) and `23dc2248` (per-stream sharing of evidence trajectories across methods, which is
numerically identical to private computation: tested to 1e-12). The first ~20 power chunks were computed
before that change with the same numbers. Outputs: `outputs/gaver/wp1b/{null,alt}/records.jsonl` (gitignored),
`null_summary.csv`, `alt_summary.csv`, `alt_pairs.csv` (force-added). 4 workers, resumable, launched detached.
Deviations from the pre-declaration: none in methods or settings. `exact0.8_s4` and `exact0.95_s4` are run with
the fast vectorised implementation (tested equal to the WP1 `ExactGapStart` to 1e-5 on the log-e-value) rather
than the WP1 class; `exact0.8_s4` reproduces WP1 (pooled detection .794 vs .795, gain over the Markov LR
+.365 vs +.367).

### Null false-promotion (k/500, CP95 upper bound)

| method | rho0 B100 | rho0 B250 | rho.5 B100 | rho.5 B250 | rho.8 B100 | rho.8 B250 | rho.95 B100 | rho.95 B250 | rho.99 B100 | rho.99 B250 |
|---|---|---|---|---|---|---|---|---|---|---|
| exact0.8_s4 (WP1 ref) | 10 (.034) | 3 (.015) | 11 (.036) | 5 (.021) | 24 (.067) | 36 (.094) | 423 (.872) | 499 (1.000) | 467 (.951) | 493 (.993) |
| exact0.95_s4 (WP1 ref) | 1 (.010) | 3 (.015) | 5 (.021) | 5 (.021) | 2 (.013) | 9 (.031) | 11 (.036) | 5 (.021) | 187 (.411) | 185 (.407) |
| exact0.99_s4 (C) | 1 (.010) | 3 (.015) | 5 (.021) | 5 (.021) | 2 (.013) | 9 (.031) | 4 (.018) | 4 (.018) | 0 (.006) | 0 (.006) |
| exactcs_s4 (B2) | 1 (.010) | 3 (.015) | 4 (.018) | 4 (.018) | 2 (.013) | 8 (.029) | 2 (.013) | 3 (.015) | 0 (.006) | 0 (.006) |
| gate_eq_s4 (A-gated) | 0 (.006) | 2 (.013) | 1 (.010) | 2 (.013) | 0 (.006) | 1 (.010) | 1 (.010) | 0 (.006) | 0 (.006) | 0 (.006) |
| gate_w_s4 (A-gated) | 0 (.006) | 0 (.006) | 0 (.006) | 0 (.006) | 0 (.006) | 1 (.010) | 1 (.010) | 0 (.006) | 0 (.006) | 0 (.006) |
| gate_fine_eq_s4 | 0 (.006) | 2 (.013) | 0 (.006) | 2 (.013) | 0 (.006) | 1 (.010) | 1 (.010) | 0 (.006) | 0 (.006) | 0 (.006) |
| envcs_s4 (B1) | 0 (.006) | 6 (.024) | 0 (.006) | 2 (.013) | 0 (.006) | 0 (.006) | 0 (.006) | 0 (.006) | 0 (.006) | 0 (.006) |
| mixnaive_eq_s4 (NEG control) | 7 (.026) | 6 (.024) | 14 (.043) | 14 (.043) | 26 (.071) | 402 (.833) | 468 (.953) | 500 (1.000) | 475 (.965) | 496 (.997) |
| mixnaive_w_s4 (NEG control) | 7 (.026) | 6 (.024) | 13 (.041) | 12 (.039) | 24 (.067) | 379 (.789) | 463 (.944) | 500 (1.000) | 474 (.963) | 496 (.997) |
| mlr_default8 (existing) | 1 (.010) | 1 (.010) | 2 (.013) | 3 (.015) | 1 (.010) | 3 (.015) | 3 (.015) | 2 (.013) | 0 (.006) | 0 (.006) |

* Every variant built on a valid argument (C, B2, A-gated, B1) has UCB <= 0.041 in all ten cells, including
  rho=0.99. They are extremely conservative at high rho (0-4 false promotions of 500).
* The plain mixture is invalid, as argued: FP .79-1.00 at rho=0.8 (B250) and rho >= 0.95; weighting toward 0.8
  does not help.
* `exact0.95_s4` fails at rho=0.99 (UCB .41); `exact0.8_s4` fails at rho >= 0.95 as in WP1.
* The CS bound is loose: mean final `ub` of `exactcs_s4` on null streams is .81 (rho 0, B250) to .95 (rho 0,
  B100), .93-.96 at rho .8, and .99 at rho >= .95 (a true rho of 0-0.5 is never certified below ~0.8). That is
  the mechanism behind the power result.

### Power (60 paired seeds x 24 cells = 1440 streams)

Pooled detection probability and paired contrasts versus `mlr_default8` (bootstrap 95% CI; the gain fraction is
the candidate's d(detect) divided by `exact0.8_s4`'s d(detect) on the same pairs):

| method | detect | d(detect) vs mlr_default8 | d(cost) vs mlr | gain fraction of exact0.8_s4 | valid on rho<=0.99 (null evidence)? |
|---|---|---|---|---|---|
| exact0.8_s4 (anchor) | .794 | +0.365 [+.340, +.392] | -0.076 | 1.00 | no (fails rho >= .95) |
| exact0.95_s4 | .397 | -0.033 [-.051, -.014] | +0.006 | -0.09 | no (fails rho .99) |
| exact0.99_s4 (C) | .370 | -0.059 [-.076, -.042] | +0.010 | -0.16 [-.22, -.11] | yes |
| exactcs_s4 (B2) | .357 | -0.072 [-.090, -.055] | +0.013 | -0.20 [-.26, -.15] | yes |
| gate_eq_s4 (A-gated) | .253 | -0.176 [-.196, -.157] | +0.027 | -0.48 [-.57, -.41] | yes |
| gate_w_s4 (A-gated) | .212 | -0.217 [-.237, -.195] | +0.032 | -0.59 [-.69, -.51] | yes |
| gate_fine_eq_s4 | .230 | -0.199 [-.220, -.179] | +0.031 | -0.55 [-.64, -.47] | yes |
| envcs_s4 (B1) | .035 | -0.394 [-.419, -.369] | +0.050 | -1.08 | yes |
| mlr_default8 | .429 | 0 | 0 | | yes |

By alternative (d(detect) vs `mlr_default8`; early, early-medium, late, transient): exact0.8_s4 +.14, +.13, +.57,
+.62; exact0.99_s4 -.06, +.01 (CI includes 0), -.09, -.09; exactcs_s4 -.08, -.03 (CI includes 0), -.07, -.11.
`exactcs_s4` vs `exact0.99_s4`: -0.013 [-.023, -.004]; vs `exact0.95_s4`: -0.040 [-.052, -.028]. So the
data-driven bound costs a little relative to the fixed cap and gives no gain, consistent with the looseness
of the CS above.

## 2. Verdict

**WP1b is an ELIMINATED extension.** No variant that is valid on rho <= 0.99 comes close to the pre-declared
bar (at least half of `exact0.8_s4`'s gain over the Markov LR). The best valid variant (`exact0.99_s4`, C) has
a gain fraction of -0.16: it is worse than the existing Markov LR by 5.9 points (*meaningful* loss). The
mixture-style constructions are worse still (*substantial* losses: -18 to -22 points for the gated ladders,
-39 for the envelope). The data-driven bound does not rescue it because with 100-250 labels at gaps 4-10 the
confidence sequence cannot certify rho below ~0.8-0.95 even when the truth is 0 (final `ub` .81-.96), so it
behaves like a fixed rho_bar of ~0.95-0.99, which is where WP1 already found no power.

What the experiment establishes (evidence, not proof):
* Valid-by-construction rho-robust versions exist and pass the null in all ten cells, so the dependence
  limit can be removed formally; the price is the loss of the whole power advantage over the Markov LR.
* The power advantage of `exact0.8_s4` is bought by excluding rho in (0.8, 0.99] from the null. Plain
  mixtures over `rho_bar` do not interpolate: they are invalid (negative control).
* A mis-declared `rho_bar` is the dominant risk of `exact0.8_s4`: FP .87-1.00 at rho .95 and .95-.99 at .99.
* Not run: min-over-components (dominated by C, section 0). Not implemented: any construction without a
  stated validity argument.

Recommendation (unchanged from WP1): `exact0.8_s4` stays the recommended Gap-Mix evidence only with an openly
declared dependence range rho <= 0.8 (an assumption, not a robustness result); do not claim robustness to
rho = 0.95 or 0.99. When rho cannot be bounded by 0.8, `exact0.99_s4` or the existing Markov LR are the valid
choices and have similar power (C is 5.9 points lower). Continue/pivot/stop: **stop** this extension; WP1
stays **continue** with the narrowed range.

Caveats: development/screening only; one T, one delay; power alternatives only at rho <= 0.8 (as WP1);
the CS is a simple Clopper-Pearson union bound and a sharper (e.g. betting) CS could be tighter, but its width
is limited by the information in 100-250 binary labels per gap, so we do not expect it to certify rho well
below 0.9 (an expectation, not a measured result); no Holm correction; the validity arguments cover the
declared stationary Markov null, not closed-loop requests or informative delay.

## 3. Reproduce

```
PYTHONPATH=<worktree>/src python scripts/gaver/run_gapmix_rho_power.py --workers 4   # ~1.5 h on a busy machine
PYTHONPATH=<worktree>/src python scripts/gaver/run_gapmix_rho_null.py --workers 4    # ~1.5 h
python scripts/gaver/run_gapmix_rho_summarize.py    # null_summary.csv, alt_summary.csv, alt_pairs.csv
```
Runs are resumable. Interpreter: the shift-research-starter `.venv`.
