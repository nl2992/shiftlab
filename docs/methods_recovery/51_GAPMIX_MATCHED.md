# Gap-Mix under matched assumptions (Track B decisive experiment)

Date 2026-11-08. Branch `research/methods-recovery-2026-11-07`. Development evidence only. Code:
`src/shiftlab/gaver/gapmix_matched.py`, `scripts/methods_recovery/gapmix_match.py`,
`tests/gaver/test_gapmix_matched.py`. Rows: `outputs/methods_recovery/gapmix_match/`.

## 0. Question

Gap-Mix (`exact0.8_s4`) beat the repo Markov LR (`mlr_default8`) by +36.7 detection points, but the two
use different null classes: Gap-Mix declares `rho <= rho_bar = 0.8` and takes its hindsight null supremum
over that class; `mlr_default8` is gap-blind and takes its supremum over ALL stationary 2-state chains
with `pi <= q0`. This study compares evidence processes that all use the SAME declared null class
(`p <= q0 = 0.55`, `rho in [0, 0.8]`) and therefore asks whether Gap-Mix's numerator/restart design adds
anything beyond the declared restriction and the standard universal-inference e-detector construction
(prior-art audit: `50_GAPMIX_NOVELTY.md`).

## 1. Pre-registered decision rule (written BEFORE any matched run; fixed)

Arms: `exact0.8_s4` (Gap-Mix), `mlr_default8`, `mlr_rb0.8`, `ui_gap_allstarts`, `thin10_s4` (gap-10 thinning).
Harness and cells: those of WP1 (`docs/gaver/10_GAPMIX_RESULTS.md`): `Family3CellSpec`, T=1000, d=10,
alpha=0.1, h=0.1, q0=0.55, uniform calendar, B in {100, 250}; null twin cells rho in {0, .5, .8}
(primary grid) plus rho = .95 (stress, outside the declared class, not used by the rule); 500 streams per
null cell; power cells = 4 alternative types (early, late, transient, early_med) x rho in {0,.5,.8} x
B in {100,250} = 24 cells, 60 paired seeds per cell (1440 pairs). Fresh seeds: registered blocks
`gapmix_match_null` (101900000-101909999) and `gapmix_match_power` (102000000-102029999).

Eligibility: an arm is eligible iff its one-sided 95% Clopper-Pearson null upper bound is <= 0.10 in EVERY
primary null cell (rho in {0,.5,.8} x B in {100,250}). An arm that is not formally valid under the declared
null (see section 3) is still reported, and is marked.

Rule. Gap-Mix continues as a Track-B candidate ONLY IF Gap-Mix is eligible and, against the best eligible arm
among {`mlr_rb0.8`, `ui_gap_allstarts`}, it wins on either criterion, pooled over the 24 power cells (paired
over the 1440 seeds, 2000-resample paired bootstrap, 95% percentile CI):

* cost: mean J/T of the comparator minus mean J/T of Gap-Mix is >= 3% of the comparator's mean J/T, and
  the CI of the paired difference excludes 0 (favouring Gap-Mix); or
* detection: Gap-Mix's detection probability exceeds the comparator's by >= 0.05 and the CI excludes 0.

"Best" is taken per criterion (lowest mean J/T; highest detection) among eligible comparators, which is the
more demanding reading for Gap-Mix. Otherwise Track B is CLOSED: the advantage is attributed to the
declared null restriction and the standard universal-inference construction. J/T is `cost / T` as logged
by the WP1 runner (loss + c N_q + s N_s). "Detect" = a promotion while the harmful-to-favourable on-regime
is active (WP1 definition). If an arm is sensitive to the choice of comparator, both contrasts are
reported separately; the rule's verdict uses the stated pooled best-of comparator. Secondary descriptive
(not part of the rule): per-type and per-B contrasts; contrasts vs `mlr_default8` and `thin10_s4`.

Deviations from this pre-registration, if any, are listed in section 7.

(Results, constructions and verdict are appended below after the runs.)

## 2. Constructions (all with the same null class: p <= q0 = 0.55, rho in [0, 0.8])

* `exact0.8_s4` (Gap-Mix, unchanged): 16-point fixed alternative mixture, exact P^g, certified hindsight null sup,
  4 fixed starts at event rounds {0, .25T, .5T, .75T}.
* `mlr_default8` (unchanged): gap-blind Markov LR, 8 label-index starts, sup over ALL 2-state chains with pi <= q0.
* `mlr_rb0.8` (new): same numerator, grid and 8 starts as `mlr_default8`; null sup restricted to homogeneous chains with
  pi <= q0 and lambda = 1 - a - b in [0, 0.8^g_min], g_min = smallest gap of the uniform calendar (0.8^9 at B=100,
  0.8^3 or 0.8^4 at B=250), computed with the Gap-Mix certified machinery (`certified_sup_batch`, one gap class, lambda cells
  of width .005). Validity argument: the universal-inference bound M / sup L <= M / L(theta*) needs the true law inside the
  class; a homogeneous class contains the skeleton only for a CONSTANT gap. The uniform calendar mixes gaps g and g+1, so the
  true skeleton is inhomogeneous and `mlr_rb0.8` has NO proof here. It is run as an empirical comparator, flagged UNPROVEN.
* `ui_gap_allstarts` (new): universal-inference e-detector (Wasserman-Ramdas-Balakrishnan 2020; Shin-Ramdas-Rinaldo 2023).
  Per start: numerator = product of exact gap-g transition probabilities of a predictable plug-in alternative (grid MAP of
  (p, rho) from labels of that start before each observation; alternative region p in [.60,.95], rho in [0,.90]; two
  pseudo-transitions at (.75,.4)); denominator = the same certified hindsight sup over the null as Gap-Mix; starts at every
  k-th label index, k = max(1, B//50) (about 50 starts: k=2 at B=100, k=5 at B=250). The e-detector is the equal-weight
  average of per-start e-processes (fixed number of starts, each 1 before its start), alarm at 1/alpha. Validity: chain
  rule with predictable q_k and sup >= L(theta*) give a nonnegative martingale per start (no iid; deterministic
  calendar, constant delay, as in Gap-Mix). The raw Shiryaev-Roberts SUM at threshold 1/alpha controls ARL, not the
  horizon false-promotion probability; the normalised average is the finite-horizon-valid form. Not proven for
  value-dependent requests or informative delay (same as Gap-Mix).
* `thin10_s4` (unchanged): iid started-mixture e-process on labels >= 10 rounds apart.

Unit tests (`tests/gaver/test_gapmix_matched.py`, 7 pass): batched sup equals the scalar certified sup row by row; restricted
sup bounds a brute-force grid and stays near the free sup; restricted LR evidence exceeds the free one on persistent data;
UI plug-in is predictable and a proper conditional law; UI null Monte-Carlo (E[e] <= 1.1, FP <= .17 at alpha .1); UI power
under an alternative; all arms run in the harness within budget.

## 3. Seeds and design

Null: `gapmix_match_null` 101900000 + 1000*cell_index + i, i < 500, 8 cells (rho {0,.5,.8,.95} x B {100,250}); rho=.95 is
outside the declared class (stress, not used by the rule). Power: `gapmix_match_power` 102000000 + 1000*cell_index + i, i < 60,
24 cells (1440 paired seeds). Cell definitions, streams and metrics are the WP1 ones (imported unchanged).

## 4. Null results, k/500 false promotions (one-sided CP95 upper bound)

| cell | exact0.8_s4 | mlr_default8 | mlr_rb0.8 (unproven) | ui_gap_allstarts | thin10_s4 |
|---|---|---|---|---|---|
| rho0 B100 | 11 (.036) | 4 (.018) | 9 (.031) | 8 (.029) | 12 (.039) |
| rho0 B250 | 6 (.024) | 5 (.021) | 10 (.034) | 5 (.021) | 11 (.036) |
| rho.5 B100 | 12 (.039) | 0 (.006) | 9 (.031) | 9 (.031) | 16 (.048) |
| rho.5 B250 | 2 (.013) | 2 (.013) | 2 (.013) | 2 (.013) | 19 (.055) |
| rho.8 B100 | 23 (.065) | 0 (.006) | 15 (.046) | 25 (.069) | 25 (.069) |
| rho.8 B250 | 25 (.069) | 2 (.013) | 4 (.018) | 27 (.074) | 15 (.046) |
| rho.95 B100 (stress) | 410 (.848) | 1 (.009) | 442 (.907) | 447 (.916) | 235 (.508) |
| rho.95 B250 (stress) | 498 (.999) | 3 (.015) | 479 (.972) | 498 (.999) | 191 (.419) |

All five arms have UCB <= 0.1 in every primary cell (max .074): all are ELIGIBLE. Beyond the declared class (rho=.95) every
arm declared at rho_bar=0.8 fails alike (`mlr_default8` is safe because it does not restrict the null), confirming the
advantage is paid for by the declared restriction.

## 5. Power (24 cells x 60 seeds = 1440 pairs; paired bootstrap 2000, 95% CI)

Pooled means, detection / J/T / labels used: Gap-Mix .801 / .3729 / 124; `mlr_default8` .454 / .4465 / 151;
`mlr_rb0.8` .784 / .3661 / 125; `ui_gap_allstarts` .850 / .3443 / 113; `thin10_s4` .693 / .3938 / 67.

| contrast (Gap-Mix minus comparator) | d detection [CI] | d J/T [CI] (negative favours Gap-Mix) | relative J/T gain of Gap-Mix |
|---|---|---|---|
| vs mlr_rb0.8 | +0.017 [+.001, +.033] | +0.0068 [+.0026, +.0108] | -1.9% |
| vs ui_gap_allstarts | -0.049 [-.064, -.035] | +0.0287 [+.0247, +.0326] | -8.3% |
| vs mlr_default8 | +0.347 [+.319, +.376] | -0.0736 [-.0800, -.0674] | +16.5% |
| vs thin10_s4 | +0.108 [+.087, +.129] | -0.0208 [-.0247, -.0171] | +5.3% |
| ui_gap_allstarts vs mlr_rb0.8 | +0.066 [+.052, +.081] | -0.0218 [-.0258, -.0180] | +6.0% (for UI) |

Gap-Mix minus `ui_gap_allstarts` detection by type: early 0.000, late -0.039 [-.061,-.017], transient -0.158 [-.197,-.119],
early_med 0.000 [-.036,.036]; by budget: B100 -0.053 [-.074,-.032], B250 -0.046 [-.065,-.026]. Gap-Mix minus `mlr_rb0.8`:
B100 -0.001 [-.024,.019], B250 +0.035 [.011,.060]; early_med +0.092 [.056,.131], transient -0.019 [-.064,.025].
All groups: `outputs/methods_recovery/gapmix_match/alt_pairs.csv`; per-cell: `alt_summary.csv`, `null_summary.csv`.

## 6. Verdict (pre-registered rule applied)

Eligible comparators: `mlr_rb0.8` and `ui_gap_allstarts` (UCB <= .1 everywhere). Best comparator on both detection and J/T is
`ui_gap_allstarts` (.850, .3443). Gap-Mix is WORSE than it by 4.9 detection points and 8.3% of J/T, CIs excluding 0 in the
wrong direction; against `mlr_rb0.8` alone Gap-Mix gains +1.7 points (below the 5-point bar) and loses 1.9% J/T. Neither
criterion is met. **Track B is CLOSED.** Gap-Mix's advantage over `mlr_default8` reproduces (+34.7 points, -16.5% J/T) but
is explained by the declared rho <= 0.8 null restriction (a trivial restriction of the gap-blind LR recovers 98% of the
detection) and the standard UI all-starts construction does better than the hand-set Gap-Mix design. The same-assumption
`ui_gap_allstarts` is a standard UI/e-detector instantiation (not a new contribution, `50_GAPMIX_NOVELTY.md`) and shares
Gap-Mix's limits (declared rho_bar, deterministic calendar, fails at rho=.95).

## 7. Deviations and caveats

* `mlr_rb0.8` validity is unproven (inhomogeneous gaps), flagged; the verdict does not depend on it (the UI comparator alone
  closes the track).
* UI hyperparameters (grid, pseudo-counts, k) were fixed a priori from the spec, not tuned; they could move the UI margin but
  the rule needs Gap-Mix to win.
* Development evidence at one T, d, alpha; rho=.95 stress cells run but not used by the rule; no multiplicity correction;
  bootstrap resamples pairs, ignoring cell clustering. Smoke runs (throwaway seeds 7100000+) are in `smoke_null/`.
* Seed blocks were added to `configs/seed_registry.yaml` by hand (not via `allocate`); overlap check passes.

## 8. Commands

```
export PYTHONPATH=<worktree>/src; export OPENBLAS_NUM_THREADS=1
python scripts/methods_recovery/gapmix_match.py run --kind null --workers 4 --max-rho 0.8   # then --max-rho 0.95
python scripts/methods_recovery/gapmix_match.py run --kind alt --workers 4
python scripts/methods_recovery/gapmix_match.py summarize
python -m pytest tests/gaver/test_gapmix_matched.py
```
(`scripts/methods_recovery/gapmix_match_all.ps1` chains these with a memory wait.) Nothing committed.
