# GAVE-R WP1: Gap-Mix results (development/screening only)

Code commits: evidence `d636765e`, runners `81c41c4e` (the runs used exactly these); summarizer and this
document added later. Branch `research/gave-r-2026-11-06`. No confirmation seeds used.

## What was implemented (`src/shiftlab/gaver/gapmix.py`)

- **1.1 Envelope e-process** (`EnvelopeStart`). `u_g(1)=q0+(1-q0)rho_bar^g`, `u_g(0)=q0`, gap `g` from the
  released event rounds; neutral factor if `r<=u` else `(r/u)^Z((1-r)/(1-u))^(1-Z)`. Predictor `r` is
  prequential from released labels only: a mixture of a plug-in (Krichevsky-style count per previous state)
  and two fixed bet fractions (0.5, 0.9 of the way from `u` to 1).
- **1.2 Exact-gap Markov LR** (`ExactGapStart`). Numerator: fixed mixture of 16 stationary chains
  `(p_a, rho_a)` with exact `P^g` skeleton transitions. Denominator: certified upper bound of the sup over the
  declared null `p<=q0, rho in [0, rho_bar]`. Certification: `rho` is cut into 0.005 cells; inside a cell each
  of the four transition probabilities is monotone in `lambda=rho^g`, so a per-term endpoint maximum bounds
  the cell; with those `lambda`s the log-likelihood is concave in `p` and is maximised by bisection (+1e-9).
- **1.3 Restart mixture** (`RestartMixture`): equal weights over starts at event rounds `{0, .25T, .5T, .75T}`;
  each start conditions on its first label; alpha is spent once on the mixture (`s4` = mixture, `s1` = start 0 only).
- Baselines wrapped in the same `episode_front` gate (calendar, alpha spending, `econ_ok`, rollback):
  iid started-mixture e-process (`iid_s1/s4`, and the repo default 32 label-index starts `iid_repo32`), existing
  `MarkovLREProcess` (`mlr_default8` = its own 8 starts, `mlr_s1`, `mlr_s4`), gap-4 and gap-10 thinning
  (`thin4_*`, `thin10_*`, applied to the same uniform calendar, so thin4 keeps ~all labels at B=250 and thin10
  keeps ~40% at B=250 / ~90% at B=100).

## Validity status

Proven (elementary, given the declared null: stationary two-state round chain, `p<=q0`, `rho in [0,rho_bar]`,
deterministic calendar, constant delay, conditioning on each start's first label):
the envelope factor has conditional expectation <=1 (checked on a grid in the tests, including the proposal's
worked numbers .91, .73432, .598318); the exact-gap statistic is numerator-mixture over a certified
upper bound of the null likelihood, hence dominated by a test martingale under every null member; fixed
convex mixtures over components and starts stay e-processes.

Not proven / empirical only: closed-loop validity when requests depend on observed values; informative delay;
non-Markov or non-stationary nulls; any `rho > rho_bar` (the declared `rho_bar` is an input, not estimated);
the looseness of the certified denominator (measured on random count tables: certified minus brute-force sup
0 to 0.72 nats, a conservatism, not an error); the gate's `econ_ok` and rollback are as in the existing baselines.
The "declared 0.8" variants match the largest rho the Atlas null grid contains below .95, so their null
result at rho<=0.8 is not evidence of robustness to a mis-declared `rho_bar` (see rho=0.95 below).

Tests: `tests/test_gaver_gapmix.py` (7 passed): worked numbers, expectation <=1 grid, Monte-Carlo mean e-value
<=1 for envelope and exact-gap, certified sup >= brute force, unreleased labels do not change actions,
all methods run within budget. Ruff clean. Searched other branches for gap-aware comparators (planner's
request): none exist (only `a1b_growing_family.py`, unrelated "exact gap along a parameter family", and the
existing `atlas_dependence_baselines.py` already used); nothing was ported.

## Setting

`Family3CellSpec` Markov streams, T=1000, delay d=10, alpha=0.1, h=0.1, q0=0.55 (hurdle boundary null twin:
`p=q0` in every round, autocorrelation rho). Budgets B=100 (bt=0.1, gap about 10) and B=250 (bt=0.25, gap
about 4). Uniform calendar. Null: rho in {0,.5,.8,.95}, 500 streams per cell (seeds 101000000 + 1000*cell + i,
registered WP1 null range). Alternatives (harmful off-regime p=.1, on-regime p=.9 for strong, .7 for medium):
early persistent (onset .3, to end, strong), late (onset .6, to end), transient (onset .3, length .3),
early medium; rho in {0,.5,.8}; B in {100,250}; 60 paired seeds per cell, 24 cells = 1440 streams
(seeds 101040000 + 1000*cell + i). Metric "false promotion" = any promotion while the regime mean is
non-favourable, as in the Atlas. "Detect" = a promotion while the on-regime is active. Upper bounds are
one-sided 95% Clopper-Pearson.

## 1.4 Null false-promotion (k/500, CP95 upper bound)

| method | rho0 B100 | rho0 B250 | rho.5 B100 | rho.5 B250 | rho.8 B100 | rho.8 B250 | rho.95 B100 | rho.95 B250 |
|---|---|---|---|---|---|---|---|---|
| iid_s1 | 20 (.058) | 20 (.058) | 19 (.055) | 35 (.092) | 44 (.112) | 144 (.323) | 195 (.427) | 325 (.685) |
| iid_s4 | 13 (.041) | 30 (.081) | 11 (.036) | 34 (.089) | 36 (.094) | 202 (.441) | 270 (.577) | 446 (.914) |
| iid_repo32 | 10 (.034) | 22 (.062) | 8 (.029) | 32 (.085) | 33 (.087) | 252 (.542) | 309 (.654) | 496 (.997) |
| thin4_s4 | 13 (.041) | 16 (.048) | 11 (.036) | 28 (.076) | 36 (.094) | 191 (.419) | 270 (.577) | 435 (.894) |
| thin10_s4 | 11 (.036) | 15 (.046) | 9 (.031) | 12 (.039) | 31 (.083) | 21 (.060) | 230 (.498) | 176 (.389) |
| mlr_default8 (existing) | 0 (.006) | 2 (.013) | 1 (.009) | 9 (.031) | 2 (.013) | 4 (.018) | 5 (.021) | 2 (.013) |
| mlr_s4 | 2 (.013) | 3 (.015) | 2 (.013) | 9 (.031) | 2 (.013) | 4 (.018) | 5 (.021) | 7 (.026) |
| env0.8_s1 | 18 (.053) | 6 (.024) | 17 (.051) | 2 (.013) | 33 (.087) | 21 (.060) | 357 (.747) | 489 (.988) |
| env0.8_s4 | 11 (.036) | 6 (.024) | 9 (.031) | 1 (.009) | 24 (.067) | 17 (.051) | 359 (.751) | 481 (.975) |
| exact0.8_s1 | 16 (.048) | 2 (.013) | 16 (.048) | 12 (.039) | 37 (.096) | 31 (.083) | 433 (.890) | 497 (.998) |
| exact0.8_s4 | 13 (.041) | 3 (.015) | 9 (.031) | 9 (.031) | 29 (.078) | 26 (.071) | 423 (.872) | 499 (1.000) |
| env0.95_s4 | 3 (.015) | 8 (.029) | 3 (.015) | 3 (.015) | 0 (.006) | 0 (.006) | 16 (.048) | 11 (.036) |
| exact0.95_s1 | 4 (.018) | 1 (.009) | 4 (.018) | 12 (.039) | 11 (.036) | 8 (.029) | 16 (.048) | 8 (.029) |
| exact0.95_s4 | 3 (.015) | 3 (.015) | 3 (.015) | 9 (.031) | 3 (.015) | 7 (.026) | 14 (.043) | 8 (.029) |

(`env0.95_s1` and `mlr_s1`, `thin*_s1`, `thin4_s1` are in `outputs/gaver/wp1/null_summary.csv`; all 18 methods
are there.) Observations: the iid gates (including the repo default and gap-4 thinning) are badly miscalibrated
at rho=.8 with B=250 (bound .42-.54) and at rho=.95; gap-10 thinning is acceptable to rho=.8 only. Every
gap-aware variant with declared `rho_bar=0.8` has bound <=0.1 for rho<=0.8 (worst: exact0.8_s1 at rho=.8
B=100, .096) and fails at the undeclared rho=.95 (expected, outside its null class). Variants declared at
0.95 are safe in all eight cells.

## 1.5 Power and delay (60 paired seeds per cell; pooled over rho and B)

Detection probability (delay from onset in rounds conditional on detection in brackets; labels used in evidence):

| method | early | late | transient | early medium | all 1440 | mean labels |
|---|---|---|---|---|---|---|
| iid_repo32 (invalid under dependence) | 1.000 [170] | .969 [167] | .922 [152] | .717 [371] | .902 [204] | 103 |
| iid_s4 (invalid) | .997 [245] | .894 [249] | .736 [200] | .683 [426] | .828 [274] | 118 |
| thin10_s4 | 1.000 [278] | .786 [279] | .594 [202] | .392 [473] | .693 [289] | 67 |
| mlr_default8 (existing) | .853 [438] | .392 [294] | .189 [248] | .278 [505] | .428 [395] | 152 |
| env0.8_s4 | .997 [249] | .897 [255] | .719 [198] | .278 [437] | .723 [256] | 130 |
| exact0.8_s4 | .997 [230] | .939 [243] | .789 [193] | .456 [458] | .795 [257] | 123 |
| exact0.8_s1 | .931 [303] | .511 [317] | .569 [213] | .028 [582] | .510 [285] | 143 |
| env0.95_s4 | .242 [543] | .025 [354] | .011 [238] | .047 [558] | .081 [520] | 173 |
| exact0.95_s4 | .858 [446] | .283 [339] | .122 [234] | .303 [502] | .392 [421] | 156 |

Restart mixture matters a great deal: start-0-only variants lose most late/transient power (e.g. exact0.8
.939 -> .511 on late; existing Markov LR .278 -> .000 with a single start).

Paired contrasts (detection-probability difference, bootstrap 95% CI, pooled over all 1440 pairs; cost =
total decision cost / T, negative favours the candidate):

| candidate vs comparator | d(detect) | d(cost) |
|---|---|---|
| exact0.8_s4 vs mlr_default8 | +0.367 [.342, .394] | -0.074 [-.080, -.068] |
| env0.8_s4 vs mlr_default8 | +0.295 [.265, .324] | -0.065 [-.071, -.059] |
| exact0.95_s4 vs mlr_default8 | -0.036 [-.054, -.019] | +0.006 [+.003, +.009] |
| exact0.8_s4 vs iid_repo32 | -0.107 [-.123, -.090] | +0.037 [+.032, +.041] |
| exact0.8_s4 vs exact0.8_s1 | +0.285 [.263, .309] | -0.049 [-.053, -.045] |

By type, exact0.8_s4 vs mlr_default8: early +0.144, late +0.547, transient +0.600, early-medium +0.178
(all CIs exclude 0; per-type table in `alt_pairs.csv`). exact0.95_s4 vs mlr_default8: early +0.006
(CI includes 0), early-medium +0.025 (includes 0), late -0.108, transient -0.067.

## Verdict (screening bar: null UB <= 0.1 at rho <= 0.8; useful power vs existing Markov LR)

Fair grading:
- **exact0.8_s4** and **env0.8_s4**: null bound <=0.078 / <=0.067 for rho<=0.8 at both budgets, and detection
  +36.7 / +29.5 points over the existing Markov LR with lower cost: *substantial* gain over the strongest
  in-repo valid comparator, conditional on a declared `rho_bar=0.8`. Exact-gap beats the envelope in power
  (+7 points pooled) but the envelope is the cheaper and has lower null bounds. Both **pass screening**.
- They fail at rho=.95 if `rho_bar` is declared 0.8 (FP .87-1.00). That is the price of a declared dependence
  range, not a bug: a wrong `rho_bar` is invalid.
- Declared `rho_bar=0.95`: safe everywhere but exact0.95_s4 is *small-to-negative* against the existing Markov LR
  (-3.6 points pooled, CI excludes 0; better only in early persistent cells at +0.6 points, not significant).
  At rho_bar=.95, gap 4 gives u=.917 and the envelope has almost no power (.08). So with a wide dependence
  range the stop rule applies: no useful power at these budgets beyond the existing comparator.
- Nothing here beats the invalid iid gates in power (they are 10 points better for exact0.8_s4 comparison)
  but those are not valid at rho>=.5, B=250. The valid, power-competitive option at rho<=.8 is
  gap-aware evidence with a declared `rho_bar=0.8` plus the restart mixture. Gap-10 thinning is a cheap
  strong baseline at rho<=.8 (UB <=.098) with detection .693 (about 10 points below exact0.8_s4, CI not computed).

Caveats: development/screening only, one T and delay; alt rho values <= .8 match the declared bound; the restart
mixture also helps the existing Markov LR (the existing `mlr_default8` is not at its best for late/transient
changes, partly explaining the large margin); no Holm correction; `s4` start times are event-round
fractions while iid/mlr use label-index fractions; thinning is applied to the same calendar rather than
re-planned at a matched label count. Next steps (not done): 2,000-stream null for exact0.8_s4 / env0.8_s4,
effect of mis-declared `rho_bar` (e.g. declare .8, truth .9), and integration with PAVE/FreshCheck (WP5).
Assessment: **continue** with envelope/exact-gap at declared `rho_bar=0.8`; **narrow** the dependence range
openly (rho<=0.8); do not claim robustness to rho=.95.

## Reproduce

```
PYTHONPATH=<worktree>/src python scripts/gaver/run_gapmix_null.py --workers 10    # ~3-6 h on a busy machine
PYTHONPATH=<worktree>/src python scripts/gaver/run_gapmix_power.py --workers 8     # ~2 h
python scripts/gaver/run_gapmix_summarize.py     # writes null_summary.csv, alt_summary.csv, alt_pairs.csv
```
Runs are resumable (`records.jsonl` per study in `outputs/gaver/wp1/{null,alt}`, gitignored). Interpreter:
the shift-research-starter `.venv`. The null/alt runs were launched detached with PowerShell `Start-Process`
and have finished; nothing is still running.
