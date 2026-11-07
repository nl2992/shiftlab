# GAVE-R WP5: integration (Gap-Mix x delay-gated PAVE) — results

Branch `research/gave-r-2026-11-06`. Development/screening only; no confirmation seeds.

## 0. Pre-declaration (written and committed BEFORE any WP5 run)

**Post-switch factor dropped.** The WP3 rerun (docs/gaver/30_FRESHCHECK_RESULTS.md) found FreshCheck
fails on value (equal-weight mean J/T: CUSUM .488, E_rb .489, FreshCheck .496). WP5 is therefore a
2x2 with the existing default rollback controller (Page-CUSUM, kappa=2, alpha spending
`alpha*2^-(j+1)`) in every arm. `GaverMethod` keeps an unused `rollback_hook` for later work.

**Frozen choices (from WP1/WP2, not tuned here).**
- Evidence: Gap-Mix `exact0.8_s4` (declared rho_bar=0.8, 4-start restart mixture); ablation: envelope
  `env0.8_s4`. Baseline evidence: frozen DSS spec `5b5c77b635e5` started-mixture e-process.
  Restart starts in episode j: `ep_start + f(T-ep_start)`, f in {0,.25,.5,.75}.
- Acquisition: frozen DSS acquisition (with its delay switch); or delay-gated PAVE = WP2 governor,
  reserve OFF, kappa=0.1, q=0.03, active only when `d >= 2T/(B+2)` (exactly where DSS falls back to
  uniform), DSS straddle rule otherwise. `uniform` is a reference arm.
- Everything else is the unchanged DSS shell (promotion, econ check, rollback, hard budget clamp).
  Gap-Mix therefore runs inside the DSS shell with alpha_0 = alpha/2 = 0.05 (not WP1's full alpha).

**Arms.** evidence {dss, gapmix, env} x acquisition {dss, pave} = `gaver:<ev>:<acq>`; plus
`uniform` (alt cells). 2x2 primary = {dss,gapmix} x {dss,pave}; envelope arms are the ablation.
By construction delay-gated PAVE == DSS wherever the gate is off (all d in {1,10} with B/T<=0.1);
the acquisition factor is therefore identifiable only in gate-on cells (d=50, and d=10 with B=250),
and the interaction contrast is identically 0 elsewhere. Null cells with the gate off run only the
`:dss` arms (equality is asserted in tests/test_gaver_integrated.py).

**Alternative cells (60 paired seeds each, seeds 101190000+100*i).** The WP2 31-cell set: the 16
cycle-7 primary cells (5 family-1, 11 family-3) plus `fa.neighbours` of the two regression cells
(`on0.6_L1_strong_harmful_d50_b0.05_s0.1`, `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`),
de-duplicated. All have rho <= 0.8 (family-3 alternatives never include rho=0.95).

**Null cells (500 streams each, seeds 101170000+500*i), 29 cells.** Atlas dependence-null twins
(boundary null, favourable prob .55, autocorrelation rho): rho in {0,.5,.8,.95} x
{d in {1,10}, B/T in {.05,.1}} (16, gate off), {d=50, B/T in {.05,.1}} (8, gate on),
{d=10, B/T=.25} (4, gate on), plus the family-1 null twin of the d50/b.05 regression cell (iid).
rho=0.95 is out-of-class stress (Gap-Mix declared 0.8) and reported separately.

**Step 0 (PAVE null completion).** Raw ungated PAVE (reserve off, kappa .1, q .03) and DSS on the 16
dependence-null cells with B/T<=0.1, d in {1,10}: 500 fresh streams per cell, seeds
101160000+500*i (WP5 range; WP2's earlier 120-140 streams/cell used WP2 seeds and are not pooled).

**Metrics.** J/T = (loss + c N_q + s N_s)/T and its three components; null false-promotion (any
promotion with regime mean < -h... i.e. the Atlas `fp_regime`), reported with Clopper-Pearson 95%
one-sided upper bound (UCB); detection = promotion while the on-regime is active, and delay from
onset; labels used (queries). Paired bootstrap 95% CIs (4000 resamples over seeds within cell;
pooled contrasts = equal-weight mean over cells, seeds resampled independently per cell).
Relative gain = reduction of mean J/T relative to the reference mean. Grades: substantial >=10%,
meaningful 3-10% with CI excluding 0, small 1-3%, negligible <1%.

**Interaction contrast.** With J_ea = mean J/T of arm (evidence e, acquisition a), gain of evidence
= J_dd - J_gd, gain of acquisition = J_dd - J_dp, joint gain = J_dd - J_gp; interaction = joint -
(evidence gain + acquisition gain) = J_gd + J_dp - J_dd - J_gp (positive = synergy), per seed,
bootstrap CI, reported on gate-on cells and on all cells.

**Screening bar (00_PLAN).** Null UCB <= 0.1 at rho <= 0.8; at least a small paired gain over the
strongest in-repo comparator in target cells; not materially worse in neighbours; rho=.95 reported.

**Compute.** <= 8 workers, resumable partial CSVs in `outputs/gaver/wp5/{pavenull,null,alt}/rows.csv`.

**Amendment A1 (POST-HOC, added after the alt results were seen, before the null stage ran).**
On the planner's request a *valid* evidence reference is added: the existing Atlas Markov-LR
e-process (`atlas_dependence_baselines.MarkovLREProcess`, the evidence of `markov_lr_gate`) inside
the same DSS shell, arms `gaver:mlr:dss` and `gaver:mlr:pave`, on the same alt seeds and null
streams. Reason: DSS evidence is not valid under dependence (WP2: null UCB 0.269 at rho=.8), so
Gap-Mix's cost against it must also be read against a valid comparator. `episode_front` was also
added to the alt references (it was listed in the runner's references after the first alt pass).
These contrasts are labelled post-hoc in every table. Nothing else in Section 0 changed.


## 1. Verdict (read first)

**Screening verdict: the full GAVE-R combination (Gap-Mix x delay-gated PAVE) FAILS screening on value.
Gap-Mix passes on validity, delay-gated PAVE passes on a narrow niche, and the two do not add.**
Planner note: the post-switch (FreshCheck / E_rb) factor was dropped because WP3 failed on value
(equal-weight mean J/T: CUSUM .488, E_rb .489, FreshCheck .496; docs/gaver/30_FRESHCHECK_RESULTS.md).
Every arm keeps the existing default rollback (Page-CUSUM).

1. **Validity of Gap-Mix under adaptive acquisition (the key check): holds empirically.** In the DSS shell,
   with either DSS or delay-gated PAVE acquisition, 500 streams per cell, 29 null cells: worst
   Clopper-Pearson 95% UCB at rho <= 0.8 is 0.051 (`gapmix:dss`) and 0.055 (`gapmix:pave`), below the 0.1
   bar; the frozen DSS evidence's own worst UCB is 0.395 (rho .8, B/T .25, d 10) and 0.215 (rho .8, B/T .1,
   d 1). This is empirical, not a proof; at the out-of-class rho = 0.95 both Gap-Mix arms fail (UCB up to
   .998), as expected for a declared rho_bar = .8.
2. **Value: Gap-Mix costs J/T in the DSS shell.** Pooled over 31 alternative cells, `gapmix:dss` minus
   `dss:dss` = +0.0197 [+0.0176, +0.0217] (5.1% worse, CI excludes 0); worse in 28/31 cells. The comparator it
   loses to is the DSS iid evidence, which is not valid at rho >= .5 (null above). Against the valid
   Markov-LR evidence in the same shell (post-hoc amendment A1), Gap-Mix wins by 14.7% (*substantial*):
   Gap-Mix's value is "valid and far more powerful than the existing valid option", not "cheaper than DSS".
3. **Delay-gated PAVE alone: a meaningful niche gain, as WP2 found.** In the 9 gate-on cells (all d = 50,
   B/T .05-.1) `dss:pave` minus `dss:dss` = -0.0186 [-0.0237, -0.0137], 4.4% better (*meaningful*); regression
   cell `on0.6_L1_strong_harmful_d50_b0.05_s0.1`: .4095 -> .3584 (12.5% better). It is identical to DSS in the
   other 22 cells by construction. Its null UCB at rho <= 0.8 is <= 0.036.
4. **Interaction: sub-additive.** Gate-on cells: evidence gain -0.0049 [-0.0071, -0.0026], acquisition gain
   +0.0186 [+0.0136, +0.0235], joint gain +0.0073 [+0.0023, +0.0121]; interaction = joint gain - sum of gains
   = **-0.0064 [-0.0106, -0.0026]** (the joint gain is less than the PAVE gain alone; `gapmix:pave` is 2.8%
   worse than `dss:pave`, CI excludes 0). All 31 cells pooled: -0.0019 [-0.0031, -0.0007].
5. **Neither beats the strongest in-repo comparator.** `episode_front` is better than `gapmix:pave` pooled
   (GAVE-R worse by +0.0052 J/T [+0.0013, +0.0089]), and better than the frozen DSS in the gate-on cells and
   in the f3_rho0 regression cell (.3415 vs DSS .3964).
6. The two mandatory Atlas regression cells: the d50 cell is improved by PAVE alone (not by Gap-Mix); the
   f3_rho0 d1 cell is untouched by PAVE (gate off) and worsened 3.5% by Gap-Mix. The Atlas regression is not repaired.

**Decision-tree outcome** (report section "Decision tree after the first experiments", copy at
`C:/Users/nigel/Downloads/deep-research-report.md`). Its five branches: Gap-Mix safe + powerful
with PAVE neutral -> irregular-sampling sequential-evidence paper; PAVE wins strongly with Gap-Mix
neutral -> delayed active-acquisition paper; FreshCheck uniquely fixes reversal -> reversible
certification paper; all three help and the interaction helps -> full GAVE-R; all fail but the
Atlas trade-off survives -> feed the benchmark paper. Reading against the data: full GAVE-R is
ruled out (interaction -0.0064, CI excludes 0; FreshCheck failed WP3); "PAVE wins strongly" is
not met (meaningful only, one d = 50 cell family); FreshCheck is excluded. The closest branch is
**"Gap-Mix safe + powerful, PAVE neutral"**, but only in the qualified sense that Gap-Mix is safe
within a declared rho <= 0.8 under adaptive acquisition and substantially more powerful than the
existing *valid* evidence (+14.7%), while it is not cheaper than the invalid DSS default. Together
with WP1b (no rho-robust variant keeps the power) this supports a narrow evidence paper only if
the Sethi et al. prior-art overlap (WP4) leaves room; otherwise the measured results (Gap-Mix
validity/price of validity, PAVE d >= 2T/(B+2) niche) go into the decision-ranking benchmark
paper as baselines. Recommended default: the benchmark-paper branch, with the evidence-paper branch
kept open pending the prior-art check. The planner decides.

Interaction sign check (planner item 2): interaction = joint gain - (evidence gain + acquisition
gain) = (J_dd - J_gp) - (J_dd - J_gd) - (J_dd - J_dp) = J_gd + J_dp - J_dd - J_gp; positive =
synergy. An early `tables.md` printed the negation (+0.0064) under this label; the formula in
`run_gaver_analyze.py` was corrected (label was right), and every number here uses the corrected
sign: gate-on +0.0073 - (-0.0049 + 0.0186) = -0.0064.

## 2. Setup actually run

Code: `src/shiftlab/gaver/integrated.py` (`GaverMethod`), `scripts/gaver/run_gaver_factorial.py`,
`scripts/gaver/run_gaver_analyze.py`, `tests/test_gaver_integrated.py` (19 light tests: hard budget, released
labels only, delay gate, inactive-cell equality with DSS, rollback hook). Section 0 above is unchanged except
amendment A1 (post-hoc, committed before the null stage ran, in `8fe567a7`).

- Alternative cells: 31 cells x 60 paired seeds (101190000+100i); 9 are gate-on (all family-1, d = 50). The 22
  gate-off cells (d = 1, 10, B/T .05-.1) make `*:pave` identical to `*:dss` (verified: equal costs in every
  gate-off cell). Caveat: the 9 gate-on cells are one regression cell, its neighbours, and three primary cells
  of the same d = 50 family, so the acquisition and interaction evidence is effectively one cell family
  (d = 50, B/T <= .1).
- Null: 29 cells x 500 streams (101170000+500i). Gate-on null cells: d = 50 (rho x4, B/T .05/.1) and
  d = 10, B/T .25 (rho x4).
- Step 0 (PAVE null completion): 16 cells x 500 fresh streams (101160000+500i), raw ungated PAVE, reserve off.
- Deviations from Section 0: (a) `gaver:mlr:pave` was removed from the null stage mid-run (7 s/stream;
  compute); its ~550 partial rows are ignored; it remains in the alternative cells. (b) The first null launch
  was stopped and resumed; completed rows were kept. (c) No Holm correction; CIs are per contrast, bootstrap
  over seeds within cells, equal cell weights. (d) rho = 0.95 is out-of-class stress, reported separately.
- Not run: no FreshCheck factor; no 2,000-stream escalation (nothing passed on value); `env` is only an ablation.

## 3. Tables

### 3.1 Null false promotion, worst Clopper-Pearson 95% UCB (500 streams per cell)

| arm | worst UCB, rho <= .8 | at cell | worst UCB, rho = .95 (out of class) |
|---|---|---|---|
| dss:dss (frozen DSS) | 0.395 | rho .8, B/T .25, d 10 | 0.983 |
| dss:pave (gated) | 0.036 | rho .8, B/T .1, d 50 | 0.413 |
| gapmix:dss | 0.051 | rho .8, B/T .05, d 50 | 0.998 |
| gapmix:pave | 0.055 | rho .8, B/T .25, d 10 | 0.740 |
| env:dss / env:pave | 0.048 / 0.046 | | 0.968 / 0.625 |
| mlr:dss (post-hoc reference) | 0.021 | | 0.018 |

Step 0, raw PAVE (reserve off), 16 dependence-null cells, 500 streams each: worst UCB at rho <= .8 is **0.039**
(rho .8, B/T .1, d 10) vs DSS 0.196 (rho .8, B/T .1, d 1); at rho = .95 PAVE reaches 0.468 and DSS 0.738 (not
safe). The lower PAVE false-promotion rate mostly reflects promoting less often (WP2), not a certificate.
`mlr:dss` is valid even at .95 but detects only 22% of alternatives and costs +23% J/T versus DSS.

### 3.2 Alternative cells, pooled equal-weight J/T (negative diff = candidate better)

| contrast | all 31 cells | 9 gate-on cells |
|---|---|---|
| Gap-Mix alone (`gapmix:dss` - `dss:dss`) | +0.0197 [+0.0176, +0.0217], 5.1% worse | +0.0049 [+0.0027, +0.0070], 1.2% worse |
| PAVE alone (`dss:pave` - `dss:dss`) | -0.0054 [-0.0068, -0.0040], 1.4% better (small) | -0.0186 [-0.0237, -0.0137], 4.4% better (meaningful) |
| joint (`gapmix:pave` - `dss:dss`) | +0.0161 [+0.0138, +0.0186], 4.2% worse | -0.0073 [-0.0123, -0.0024], 1.7% better (small) |
| joint vs PAVE alone | +0.0215 [+0.0194, +0.0237], worse | +0.0114 [+0.0078, +0.0147], worse |
| interaction (joint gain - sum of gains) | -0.0019 [-0.0031, -0.0007] | -0.0064 [-0.0106, -0.0026] |
| [post-hoc] `gapmix:dss` vs `mlr:dss` (valid ref.) | -0.0704 [-0.0734, -0.0675], 14.7% better | -0.0339 [-0.0378, -0.0301], 7.4% better |
| `env:dss` vs `dss:dss` (ablation) | +0.0271, worse | -0.0037 [-0.0061, -0.0013], 0.9% (negligible) |
| `gapmix:pave` vs `episode_front` | +0.0052 [+0.0013, +0.0089], worse | +0.0067 [+0.0015, +0.0118], worse |

Per-cell grades (95% CI per cell): `gapmix:dss` vs `dss:dss`: 28 of 31 cells worse (23 with CI excluding 0),
none better; `dss:pave` vs `dss:dss` over the 9 gate-on cells: 2 substantial, 3 meaningful, 2 negligible,
2 worse. In the gate-on cells decision loss dominates J/T (query and switch cost < 0.001 each): J/T `dss:dss`
.4218, `dss:pave` .4032, `gapmix:dss` .4268, `gapmix:pave` .4146, `episode_front` .4079; detection `dss:dss`
.43, `dss:pave` .60, `gapmix:dss` .42, `gapmix:pave` .50, `episode_front` .53; queries 55.6 (DSS) vs 51.2
(PAVE). Over all cells Gap-Mix detects less than DSS evidence in the DSS shell (.714 vs .777), partly because
DSS's iid evidence is anti-conservative under dependence and partly because alpha is split (alpha_0 = .05).

## 4. Interpretation, limits, negatives

- Why Gap-Mix does not pay here: the frozen DSS evidence is optimistic under dependence (its null failure), so
  it detects earlier and often profitably in these simulated streams. Gap-Mix removes the false promotions
  but cannot beat an optimistic gate on J/T. Fair reading: validity at a price of 1-7% J/T against DSS, and a
  large gain over the other valid gate.
- Plausible reason the combination is sub-additive (not tested): PAVE's gain comes from earlier detection
  within a fixed budget; Gap-Mix needs more evidence per promotion, which removes part of that benefit.
- Limits: one T = 1000; fixed delays; the gate-on evidence is a single cell family; Gap-Mix validity under
  adaptive acquisition is empirical (500 streams, UCB about .05, which cannot rule out true rates of a few
  percent); no informative delay, no real data; boundary nulls only; no multiplicity correction; one post-hoc
  arm (mlr) and one post-hoc compute deviation, both flagged above. Raw outputs are gitignored:
  `outputs/gaver/wp5/{alt,null,pavenull}/rows.csv`, `tables.md`.
- Continue / pivot / stop: stop the joint method. Pivot to reporting (i) the Gap-Mix validity result within a
  declared rho_bar and (ii) the delay-gated PAVE niche as separate baselines for the benchmark paper. Any PAVE
  niche claim needs fresh seeds, more d >= 2T/(B+2) cells (d = 10 with B/T .25, and d = 50 with B/T .25 have
  no alternative cells here) and a 2,000-stream null.

## 5. Reproduce

```
cd "<worktree>"; PY=<shift-research-starter>/.venv/Scripts/python.exe
export PYTHONPATH="$PWD/src" PYTHONIOENCODING=utf-8
$PY scripts/gaver/run_gaver_factorial.py --stage alt      --workers 8
$PY scripts/gaver/run_gaver_factorial.py --stage pavenull --workers 8
$PY scripts/gaver/run_gaver_factorial.py --stage null     --workers 8   # hours on a shared machine
$PY scripts/gaver/run_gaver_analyze.py                                   # writes outputs/gaver/wp5/tables.md
$PY -m pytest tests/test_gaver_integrated.py -q
$PY -m ruff check src/shiftlab/gaver/integrated.py scripts/gaver tests/test_gaver_integrated.py
```
Commits: harness and pre-declaration `a52a52ae`; amendment A1 plus analysis script `8fe567a7`; null-stage
compute change `dfdb7cb8`; this document in the following commit. Seeds 101160000-101193099 (WP5 block).
Runs were launched detached (PowerShell `Start-Process`) and are resumable.

## Appendix: generated tables (from `outputs/gaver/wp5/tables.md`)

### Alternative cells (generated): 31 cells, seeds/cell 60-60
gate-on cells (9): on0.3_L1_strong_harmful_d50_b0.05_s0.1, on0.6_L0.6_strong_harmful_d50_b0.05_s0.1, on0.6_L1_medium_harmful_d50_b0.05_s0.1, on0.6_L1_strong_harmful_d50_b0.05_s0.05, on0.6_L1_strong_harmful_d50_b0.05_s0.1, on0.6_L1_strong_harmful_d50_b0.05_s0.5, on0.6_L1_strong_harmful_d50_b0.1_s0.1, on0.6_L1_strong_neutral_d50_b0.05_s0.1, on0.8_L1_strong_harmful_d50_b0.05_s0.1

#### Pooled J/T contrasts, all cells (n=31 cells); negative diff = candidate better

| contrast | diff [95% CI] | rel. gain | grade |
|---|---|---|---|
| Gap-Mix evidence alone (gapmix:dss vs dss:dss) | +0.0197 [+0.0176, +0.0217] | -5.1% | worse (CI excl. 0) |
| delay-gated PAVE alone (dss:pave vs dss:dss) | -0.0054 [-0.0068, -0.0040] | +1.4% | small |
| joint (gapmix:pave vs dss:dss) | +0.0161 [+0.0138, +0.0186] | -4.2% | worse (CI excl. 0) |
| joint vs Gap-Mix alone (gapmix:pave vs gapmix:dss) | -0.0035 [-0.0050, -0.0020] | +0.9% | negligible |
| joint vs PAVE alone (gapmix:pave vs dss:pave) | +0.0215 [+0.0194, +0.0237] | -5.6% | worse (CI excl. 0) |
| envelope evidence alone (env:dss vs dss:dss) | +0.0271 [+0.0247, +0.0294] | -7.0% | worse (CI excl. 0) |
| envelope + PAVE (env:pave vs dss:dss) | +0.0232 [+0.0204, +0.0261] | -6.0% | worse (CI excl. 0) |
| [post-hoc] mlr:dss vs dss:dss | +0.0901 [+0.0873, +0.0930] | -23.2% | worse (CI excl. 0) |
| [post-hoc] gapmix:dss vs mlr:dss | -0.0704 [-0.0734, -0.0675] | +14.7% | substantial |
| [post-hoc] gapmix:pave vs mlr:dss | -0.0739 [-0.0769, -0.0709] | +15.5% | substantial |
| [post-hoc] gapmix:pave vs mlr:pave | -0.0738 [-0.0768, -0.0708] | +15.5% | substantial |
| [post-hoc] mlr:pave vs mlr:dss | -0.0001 [-0.0002, -0.0000] | +0.0% | negligible |
| dss:dss vs uniform | -0.0335 [-0.0370, -0.0300] | +8.0% | meaningful |
| gapmix:pave vs uniform | -0.0174 [-0.0212, -0.0136] | +4.1% | meaningful |
| dss:dss vs episode_front | -0.0109 [-0.0143, -0.0076] | +2.7% | small |
| gapmix:pave vs episode_front | +0.0052 [+0.0013, +0.0089] | -1.3% | worse (CI excl. 0) |

Gains (J/T reduction vs dss:dss), all cells:
- evidence: -0.0197 [-0.0217, -0.0177]
- acquisition: +0.0054 [+0.0040, +0.0069]
- joint: -0.0161 [-0.0186, -0.0138]
- interaction = joint gain - (evidence gain + acquisition gain) (= J_gd+J_dp-J_dd-J_gp; positive = synergy, negative = sub-additive): -0.0019 [-0.0031, -0.0007]

#### Pooled J/T contrasts, gate-on (n=9 cells); negative diff = candidate better

| contrast | diff [95% CI] | rel. gain | grade |
|---|---|---|---|
| Gap-Mix evidence alone (gapmix:dss vs dss:dss) | +0.0049 [+0.0027, +0.0070] | -1.2% | worse (CI excl. 0) |
| delay-gated PAVE alone (dss:pave vs dss:dss) | -0.0186 [-0.0237, -0.0137] | +4.4% | meaningful |
| joint (gapmix:pave vs dss:dss) | -0.0073 [-0.0123, -0.0024] | +1.7% | small |
| joint vs Gap-Mix alone (gapmix:pave vs gapmix:dss) | -0.0122 [-0.0174, -0.0069] | +2.9% | small |
| joint vs PAVE alone (gapmix:pave vs dss:pave) | +0.0114 [+0.0078, +0.0147] | -2.8% | worse (CI excl. 0) |
| envelope evidence alone (env:dss vs dss:dss) | -0.0037 [-0.0061, -0.0013] | +0.9% | negligible |
| envelope + PAVE (env:pave vs dss:dss) | -0.0172 [-0.0231, -0.0119] | +4.1% | meaningful |
| [post-hoc] mlr:dss vs dss:dss | +0.0388 [+0.0352, +0.0423] | -9.2% | worse (CI excl. 0) |
| [post-hoc] gapmix:dss vs mlr:dss | -0.0339 [-0.0378, -0.0301] | +7.4% | meaningful |
| [post-hoc] gapmix:pave vs mlr:dss | -0.0461 [-0.0500, -0.0422] | +10.0% | substantial |
| [post-hoc] gapmix:pave vs mlr:pave | -0.0458 [-0.0497, -0.0419] | +9.9% | meaningful |
| [post-hoc] mlr:pave vs mlr:dss | -0.0003 [-0.0008, -0.0000] | +0.1% | negligible |
| dss:dss vs uniform | +0.0000 [+0.0000, +0.0000] | -0.0% | negligible |
| gapmix:pave vs uniform | -0.0073 [-0.0122, -0.0024] | +1.7% | small |
| dss:dss vs episode_front | +0.0140 [+0.0119, +0.0160] | -3.4% | worse (CI excl. 0) |
| gapmix:pave vs episode_front | +0.0067 [+0.0015, +0.0118] | -1.7% | worse (CI excl. 0) |

Gains (J/T reduction vs dss:dss), gate-on:
- evidence: -0.0049 [-0.0071, -0.0026]
- acquisition: +0.0186 [+0.0136, +0.0235]
- joint: +0.0073 [+0.0023, +0.0121]
- interaction = joint gain - (evidence gain + acquisition gain) (= J_gd+J_dp-J_dd-J_gp; positive = synergy, negative = sub-additive): -0.0064 [-0.0106, -0.0026]

#### Pooled J/T contrasts, gate-off (n=22 cells); negative diff = candidate better

| contrast | diff [95% CI] | rel. gain | grade |
|---|---|---|---|
| Gap-Mix evidence alone (gapmix:dss vs dss:dss) | +0.0257 [+0.0230, +0.0284] | -6.9% | worse (CI excl. 0) |
| delay-gated PAVE alone (dss:pave vs dss:dss) | +0.0000 [+0.0000, +0.0000] | -0.0% | negligible |
| joint (gapmix:pave vs dss:dss) | +0.0257 [+0.0229, +0.0283] | -6.9% | worse (CI excl. 0) |
| joint vs Gap-Mix alone (gapmix:pave vs gapmix:dss) | +0.0000 [+0.0000, +0.0000] | -0.0% | negligible |
| joint vs PAVE alone (gapmix:pave vs dss:pave) | +0.0257 [+0.0230, +0.0285] | -6.9% | worse (CI excl. 0) |
| envelope evidence alone (env:dss vs dss:dss) | +0.0398 [+0.0365, +0.0430] | -10.7% | worse (CI excl. 0) |
| envelope + PAVE (env:pave vs dss:dss) | +0.0398 [+0.0365, +0.0431] | -10.7% | worse (CI excl. 0) |
| [post-hoc] mlr:dss vs dss:dss | +0.1110 [+0.1072, +0.1148] | -29.7% | worse (CI excl. 0) |
| [post-hoc] gapmix:dss vs mlr:dss | -0.0853 [-0.0893, -0.0814] | +17.6% | substantial |
| [post-hoc] gapmix:pave vs mlr:dss | -0.0853 [-0.0891, -0.0813] | +17.6% | substantial |
| [post-hoc] gapmix:pave vs mlr:pave | -0.0853 [-0.0893, -0.0813] | +17.6% | substantial |
| [post-hoc] mlr:pave vs mlr:dss | +0.0000 [+0.0000, +0.0000] | -0.0% | negligible |
| dss:dss vs uniform | -0.0473 [-0.0520, -0.0424] | +11.2% | substantial |
| gapmix:pave vs uniform | -0.0215 [-0.0264, -0.0167] | +5.1% | meaningful |
| dss:dss vs episode_front | -0.0211 [-0.0262, -0.0164] | +5.4% | meaningful |
| gapmix:pave vs episode_front | +0.0046 [-0.0005, +0.0096] | -1.2% | worse (CI incl. 0) |

Gains (J/T reduction vs dss:dss), gate-off:
- evidence: -0.0257 [-0.0284, -0.0230]
- acquisition: +0.0000 [+0.0000, +0.0000]
- joint: -0.0257 [-0.0285, -0.0229]
- interaction = joint gain - (evidence gain + acquisition gain) (= J_gd+J_dp-J_dd-J_gp; positive = synergy, negative = sub-additive): -0.0000 [-0.0000, +0.0000]

#### Per-cell J/T (mean over seeds)

| cell | n | gaver:dss:dss | gaver:gapmix:dss | gaver:dss:pave | gaver:gapmix:pave | gaver:env:dss | gaver:env:pave | gaver:mlr:dss | gaver:mlr:pave | uniform | episode_front |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | 60 | 0.4026 | 0.4400 | 0.4026 | 0.4400 | 0.4425 | 0.4425 | 0.5680 | 0.5680 | 0.4819 | 0.4669 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.4129 | 0.4593 | 0.4129 | 0.4593 | 0.4908 | 0.4908 | 0.5673 | 0.5673 | 0.4824 | 0.4580 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | 60 | 0.3940 | 0.4107 | 0.3940 | 0.4107 | 0.4181 | 0.4181 | 0.5275 | 0.5275 | 0.3711 | 0.3333 |
| f3_rho0.5_on0.6_L0.6_strong_harmful_d10_b0.05_s0.1 | 60 | 0.3436 | 0.3502 | 0.3436 | 0.3502 | 0.3589 | 0.3589 | 0.4061 | 0.4061 | 0.3966 | 0.3836 |
| f3_rho0.5_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3065 | 0.3315 | 0.3065 | 0.3315 | 0.3484 | 0.3484 | 0.4126 | 0.4126 | 0.3823 | 0.3639 |
| f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3245 | 0.3494 | 0.3245 | 0.3494 | 0.3579 | 0.3579 | 0.4171 | 0.4171 | 0.3928 | 0.3768 |
| f3_rho0.8_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3304 | 0.3500 | 0.3304 | 0.3500 | 0.3462 | 0.3462 | 0.4217 | 0.4217 | 0.3912 | 0.3719 |
| f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.05_s0.1 | 60 | 0.3461 | 0.3511 | 0.3461 | 0.3511 | 0.3504 | 0.3504 | 0.4153 | 0.4153 | 0.3910 | 0.3760 |
| f3_rho0_on0.3_L0.6_medium_harmful_d1_b0.1_s0.1 | 60 | 0.5251 | 0.5309 | 0.5251 | 0.5309 | 0.5386 | 0.5386 | 0.5359 | 0.5359 | 0.5315 | 0.5277 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | 60 | 0.4298 | 0.4392 | 0.4298 | 0.4392 | 0.4401 | 0.4401 | 0.5632 | 0.5632 | 0.3805 | 0.3587 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3890 | 0.4263 | 0.3890 | 0.4263 | 0.4678 | 0.4678 | 0.5443 | 0.5443 | 0.4624 | 0.4434 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | 60 | 0.3964 | 0.4101 | 0.3964 | 0.4101 | 0.4268 | 0.4268 | 0.5126 | 0.5126 | 0.3736 | 0.3415 |
| f3_rho0_on0.3_L0.6_strong_neutral_d1_b0.1_s0.1 | 60 | 0.4043 | 0.4362 | 0.4043 | 0.4362 | 0.4664 | 0.4664 | 0.5229 | 0.5229 | 0.4894 | 0.4169 |
| f3_rho0_on0.3_L1_strong_harmful_d1_b0.1_s0.1 | 60 | 0.3596 | 0.3817 | 0.3596 | 0.3817 | 0.3914 | 0.3914 | 0.4842 | 0.4842 | 0.4164 | 0.3081 |
| f3_rho0_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3120 | 0.3333 | 0.3120 | 0.3333 | 0.3548 | 0.3548 | 0.4120 | 0.4120 | 0.3866 | 0.3673 |
| f3_rho0_on0.6_L0.6_strong_harmful_d1_b0.1_s0.1 | 60 | 0.3318 | 0.3588 | 0.3318 | 0.3588 | 0.3647 | 0.3647 | 0.4101 | 0.4101 | 0.3247 | 0.2938 |
| f3_rho0_on0.6_L1_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3056 | 0.3447 | 0.3056 | 0.3447 | 0.3670 | 0.3670 | 0.4127 | 0.4127 | 0.3981 | 0.3821 |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | 60 | 0.4423 | 0.5054 | 0.4423 | 0.5054 | 0.5100 | 0.5100 | 0.5867 | 0.5867 | 0.4790 | 0.4633 |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3666 | 0.4306 | 0.3666 | 0.4306 | 0.4624 | 0.4624 | 0.5449 | 0.5449 | 0.4657 | 0.4496 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | 60 | 0.4319 | 0.4412 | 0.4319 | 0.4412 | 0.4657 | 0.4657 | 0.5615 | 0.5615 | 0.4727 | 0.4426 |
| on0.3_L1_strong_harmful_d50_b0.05_s0.1 (gate on) | 60 | 0.4723 | 0.4649 | 0.4906 | 0.4784 | 0.4525 | 0.4768 | 0.6554 | 0.6552 | 0.4723 | 0.4354 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | 60 | 0.3243 | 0.3491 | 0.3243 | 0.3491 | 0.3620 | 0.3620 | 0.4111 | 0.4111 | 0.3858 | 0.3708 |
| on0.6_L0.6_strong_harmful_d50_b0.05_s0.1 (gate on) | 60 | 0.4048 | 0.4145 | 0.3560 | 0.3790 | 0.3949 | 0.3559 | 0.4216 | 0.4216 | 0.4048 | 0.3948 |
| on0.6_L1_medium_harmful_d50_b0.05_s0.1 (gate on) | 60 | 0.4626 | 0.4628 | 0.4605 | 0.4614 | 0.4625 | 0.4599 | 0.4629 | 0.4629 | 0.4626 | 0.4616 |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | 60 | 0.3346 | 0.3500 | 0.3346 | 0.3500 | 0.3581 | 0.3581 | 0.4188 | 0.4188 | 0.3980 | 0.3831 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.05 (gate on) | 60 | 0.4035 | 0.4110 | 0.3691 | 0.3963 | 0.3940 | 0.3750 | 0.4188 | 0.4188 | 0.4035 | 0.3937 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 (gate on) | 60 | 0.4095 | 0.4161 | 0.3584 | 0.3791 | 0.4067 | 0.3638 | 0.4231 | 0.4231 | 0.4095 | 0.3980 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.5 (gate on) | 60 | 0.4093 | 0.4135 | 0.3688 | 0.3946 | 0.3989 | 0.3757 | 0.4212 | 0.4212 | 0.4093 | 0.3984 |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 (gate on) | 60 | 0.3430 | 0.3729 | 0.3606 | 0.3706 | 0.3705 | 0.3617 | 0.4188 | 0.4184 | 0.3430 | 0.3213 |
| on0.6_L1_strong_neutral_d50_b0.05_s0.1 (gate on) | 60 | 0.6264 | 0.6200 | 0.6001 | 0.6094 | 0.6185 | 0.6111 | 0.6589 | 0.6567 | 0.6264 | 0.6023 |
| on0.8_L1_strong_harmful_d50_b0.05_s0.1 (gate on) | 60 | 0.2652 | 0.2652 | 0.2650 | 0.2625 | 0.2648 | 0.2617 | 0.2652 | 0.2652 | 0.2652 | 0.2652 |

Per-cell grade counts, gapmix:dss vs dss:dss: negligible: 1, small (CI incl. 0): 2, worse (CI excl. 0): 23, worse (CI incl. 0): 5
Per-cell grade counts, dss:pave vs dss:dss: meaningful: 3, negligible: 2, substantial: 2, worse (CI excl. 0): 1, worse (CI incl. 0): 1 (gate-on cells only)
Per-cell grade counts, gapmix:pave vs dss:dss: meaningful: 3, negligible: 1, small: 1, small (CI incl. 0): 2, worse (CI excl. 0): 20, worse (CI incl. 0): 4
Per-cell grade counts, gapmix:pave vs episode_front: meaningful: 12, negligible: 3, small: 1, small (CI incl. 0): 2, worse (CI excl. 0): 8, worse (CI incl. 0): 5
Per-cell grade counts, [post-hoc] gapmix:dss vs mlr:dss: meaningful: 1, negligible: 3, small: 4, substantial: 23
Per-cell grade counts, [post-hoc] gapmix:pave vs mlr:dss: meaningful: 3, negligible: 2, small: 1, substantial: 25

#### Components, detection, labels (equal-weight mean over alt cells)

| arm | J/T | loss | query cost | switch cost | queries | detect | mean delay |
|---|---|---|---|---|---|---|---|
| gaver:dss:dss | 0.3874 | 0.3869 | 0.0004 | 0.0001 | 45.0 | 0.777 | 287 |
| gaver:gapmix:dss | 0.4071 | 0.4065 | 0.0005 | 0.0001 | 48.5 | 0.714 | 308 |
| gaver:dss:pave | 0.3820 | 0.3815 | 0.0004 | 0.0001 | 43.7 | 0.826 | 285 |
| gaver:gapmix:pave | 0.4036 | 0.4030 | 0.0005 | 0.0001 | 47.2 | 0.736 | 304 |
| gaver:env:dss | 0.4146 | 0.4140 | 0.0005 | 0.0001 | 49.4 | 0.634 | 307 |
| gaver:env:pave | 0.4107 | 0.4101 | 0.0005 | 0.0001 | 48.1 | 0.656 | 301 |
| gaver:mlr:dss | 0.4775 | 0.4769 | 0.0006 | 0.0000 | 57.3 | 0.218 | 404 |
| gaver:mlr:pave | 0.4774 | 0.4768 | 0.0006 | 0.0000 | 55.9 | 0.219 | 404 |
| uniform | 0.4210 | 0.4202 | 0.0006 | 0.0001 | 62.9 | 0.634 | 328 |
| episode_front | 0.3984 | 0.3976 | 0.0006 | 0.0001 | 62.9 | 0.722 | 307 |


### Null false promotion, factorial (generated)

k/n (Clopper-Pearson 95% one-sided UCB)

| cell | gaver:dss:dss | gaver:dss:pave | gaver:env:dss | gaver:env:pave | gaver:gapmix:dss | gaver:gapmix:pave | gaver:mlr:dss |
|---|---|---|---|---|---|---|---|
| dep_rho0.5_bt0.05_d1 | 4/500 (0.018) | - | 1/500 (0.009) | - | 1/500 (0.009) | - | 0/500 (0.006) |
| dep_rho0.5_bt0.05_d10 | 6/500 (0.024) | - | 1/500 (0.009) | - | 0/500 (0.006) | - | 0/500 (0.006) |
| dep_rho0.5_bt0.05_d50 | 3/500 (0.015) | 2/500 (0.013) | 9/500 (0.031) | 12/500 (0.039) | 7/500 (0.026) | 12/500 (0.039) | 0/500 (0.006) |
| dep_rho0.5_bt0.1_d1 | 13/500 (0.041) | - | 0/500 (0.006) | - | 2/500 (0.013) | - | 1/500 (0.009) |
| dep_rho0.5_bt0.1_d10 | 5/500 (0.021) | - | 0/500 (0.006) | - | 0/500 (0.006) | - | 0/500 (0.006) |
| dep_rho0.5_bt0.1_d50 | 3/500 (0.015) | 0/500 (0.006) | 3/500 (0.015) | 6/500 (0.024) | 2/500 (0.013) | 6/500 (0.024) | 0/500 (0.006) |
| dep_rho0.5_bt0.25_d10 | 18/500 (0.053) | 2/500 (0.013) | 0/500 (0.006) | 9/500 (0.031) | 4/500 (0.018) | 10/500 (0.034) | 3/500 (0.015) |
| dep_rho0.8_bt0.05_d1 | 52/500 (0.129) | - | 10/500 (0.034) | - | 10/500 (0.034) | - | 0/500 (0.006) |
| dep_rho0.8_bt0.05_d10 | 32/500 (0.085) | - | 4/500 (0.018) | - | 6/500 (0.024) | - | 0/500 (0.006) |
| dep_rho0.8_bt0.05_d50 | 7/500 (0.026) | 4/500 (0.018) | 16/500 (0.048) | 14/500 (0.043) | 17/500 (0.051) | 14/500 (0.043) | 0/500 (0.006) |
| dep_rho0.8_bt0.1_d1 | 92/500 (0.215) | - | 9/500 (0.031) | - | 13/500 (0.041) | - | 1/500 (0.009) |
| dep_rho0.8_bt0.1_d10 | 48/500 (0.120) | - | 9/500 (0.031) | - | 12/500 (0.039) | - | 2/500 (0.013) |
| dep_rho0.8_bt0.1_d50 | 8/500 (0.029) | 11/500 (0.036) | 9/500 (0.031) | 11/500 (0.036) | 6/500 (0.024) | 11/500 (0.036) | 0/500 (0.006) |
| dep_rho0.8_bt0.25_d10 | 179/500 (0.395) | 5/500 (0.021) | 8/500 (0.029) | 15/500 (0.046) | 12/500 (0.039) | 19/500 (0.055) | 5/500 (0.021) |
| dep_rho0_bt0.05_d1 | 3/500 (0.015) | - | 0/500 (0.006) | - | 0/500 (0.006) | - | 0/500 (0.006) |
| dep_rho0_bt0.05_d10 | 2/500 (0.013) | - | 0/500 (0.006) | - | 0/500 (0.006) | - | 0/500 (0.006) |
| dep_rho0_bt0.05_d50 | 3/500 (0.015) | 1/500 (0.009) | 6/500 (0.024) | 9/500 (0.031) | 8/500 (0.029) | 10/500 (0.034) | 0/500 (0.006) |
| dep_rho0_bt0.1_d1 | 5/500 (0.021) | - | 1/500 (0.009) | - | 1/500 (0.009) | - | 2/500 (0.013) |
| dep_rho0_bt0.1_d10 | 2/500 (0.013) | - | 1/500 (0.009) | - | 0/500 (0.006) | - | 0/500 (0.006) |
| dep_rho0_bt0.1_d50 | 9/500 (0.031) | 7/500 (0.026) | 9/500 (0.031) | 13/500 (0.041) | 5/500 (0.021) | 11/500 (0.036) | 1/500 (0.009) |
| dep_rho0_bt0.25_d10 | 9/500 (0.031) | 2/500 (0.013) | 4/500 (0.018) | 3/500 (0.015) | 2/500 (0.013) | 5/500 (0.021) | 2/500 (0.013) |
| f1null_d50_b0.05 | 0/500 (0.006) | 0/500 (0.006) | 0/500 (0.006) | 0/500 (0.006) | 0/500 (0.006) | 0/500 (0.006) | 0/500 (0.006) |
| dep_rho0.95_bt0.05_d1 | 310/500 (0.656) | - | 219/500 (0.476) | - | 223/500 (0.484) | - | 0/500 (0.006) |
| dep_rho0.95_bt0.05_d10 | 227/500 (0.492) | - | 187/500 (0.411) | - | 190/500 (0.417) | - | 0/500 (0.006) |
| dep_rho0.95_bt0.05_d50 | 45/500 (0.114) | 62/500 (0.151) | 92/500 (0.215) | 100/500 (0.232) | 90/500 (0.211) | 86/500 (0.202) | 0/500 (0.006) |
| dep_rho0.95_bt0.1_d1 | 352/500 (0.738) | - | 275/500 (0.587) | - | 286/500 (0.609) | - | 2/500 (0.013) |
| dep_rho0.95_bt0.1_d10 | 278/500 (0.593) | - | 227/500 (0.492) | - | 245/500 (0.528) | - | 4/500 (0.018) |
| dep_rho0.95_bt0.1_d50 | 256/500 (0.550) | 146/500 (0.327) | 322/500 (0.680) | 159/500 (0.354) | 393/500 (0.816) | 174/500 (0.385) | 1/500 (0.009) |
| dep_rho0.95_bt0.25_d10 | 486/500 (0.983) | 188/500 (0.413) | 477/500 (0.968) | 294/500 (0.625) | 497/500 (0.998) | 353/500 (0.740) | 0/500 (0.006) |

| arm | worst UCB rho<=.8 | at cell | worst UCB rho=.95 | min n |
|---|---|---|---|---|
| gaver:dss:dss | 0.395 | dep_rho0.8_bt0.25_d10 | 0.983 | 500 |
| gaver:dss:pave | 0.036 | dep_rho0.8_bt0.1_d50 | 0.413 | 500 |
| gaver:env:dss | 0.048 | dep_rho0.8_bt0.05_d50 | 0.968 | 500 |
| gaver:env:pave | 0.046 | dep_rho0.8_bt0.25_d10 | 0.625 | 500 |
| gaver:gapmix:dss | 0.051 | dep_rho0.8_bt0.05_d50 | 0.998 | 500 |
| gaver:gapmix:pave | 0.055 | dep_rho0.8_bt0.25_d10 | 0.740 | 500 |
| gaver:mlr:dss | 0.021 | dep_rho0.8_bt0.25_d10 | 0.018 | 500 |

Mean null J/T by arm: gaver:dss:dss: 0.5283, gaver:dss:pave: 0.5149, gaver:env:dss: 0.5306, gaver:env:pave: 0.5139, gaver:gapmix:dss: 0.5301, gaver:gapmix:pave: 0.5136, gaver:mlr:dss: 0.5358


### Step 0 table: raw (ungated) PAVE null completion, reserve off

k/n (Clopper-Pearson 95% one-sided UCB)

| cell | dss | pave_raw |
|---|---|---|
| dep_rho0.5_bt0.05_d1 | 3/500 (0.015) | 3/500 (0.015) |
| dep_rho0.5_bt0.05_d10 | 3/500 (0.015) | 3/500 (0.015) |
| dep_rho0.5_bt0.1_d1 | 11/500 (0.036) | 2/500 (0.013) |
| dep_rho0.5_bt0.1_d10 | 3/500 (0.015) | 8/500 (0.029) |
| dep_rho0.8_bt0.05_d1 | 43/500 (0.109) | 6/500 (0.024) |
| dep_rho0.8_bt0.05_d10 | 27/500 (0.074) | 6/500 (0.024) |
| dep_rho0.8_bt0.1_d1 | 83/500 (0.196) | 10/500 (0.034) |
| dep_rho0.8_bt0.1_d10 | 55/500 (0.136) | 12/500 (0.039) |
| dep_rho0_bt0.05_d1 | 2/500 (0.013) | 3/500 (0.015) |
| dep_rho0_bt0.05_d10 | 3/500 (0.015) | 3/500 (0.015) |
| dep_rho0_bt0.1_d1 | 5/500 (0.021) | 6/500 (0.024) |
| dep_rho0_bt0.1_d10 | 6/500 (0.024) | 10/500 (0.034) |
| dep_rho0.95_bt0.05_d1 | 298/500 (0.633) | 94/500 (0.219) |
| dep_rho0.95_bt0.05_d10 | 264/500 (0.566) | 131/500 (0.296) |
| dep_rho0.95_bt0.1_d1 | 352/500 (0.738) | 135/500 (0.305) |
| dep_rho0.95_bt0.1_d10 | 283/500 (0.603) | 215/500 (0.468) |

| arm | worst UCB rho<=.8 | at cell | worst UCB rho=.95 | min n |
|---|---|---|---|---|
| dss | 0.196 | dep_rho0.8_bt0.1_d1 | 0.738 | 500 |
| pave_raw | 0.039 | dep_rho0.8_bt0.1_d10 | 0.468 | 500 |

Mean null J/T by arm: dss: 0.5414, pave_raw: 0.5482

