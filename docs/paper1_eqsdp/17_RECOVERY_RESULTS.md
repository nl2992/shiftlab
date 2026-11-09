# 17. Recovery factorial: results (even selection, odd check)

Protocol and advance criterion: doc 15 section 3; freeze: doc 16 (`16_RECOVERY_FREEZE.json`, commit 44d214c7).
Evidence class: development-data check only (odd episodes were run once; no retuning; no held-out data built).
All numbers come from `stage5_analysis.py F even odd` and `stage5_odd.py`.

**Timing.** Freeze commit 44d214c7 pushed 2026-11-08 23:09:52 -0500 (local HEAD equalled `origin/<branch>`).
Odd run started 23:10:04 -0500 (`outputs/paper1_eqsdp/stage5/odd/start.json`), finished 23:12:39 -0500.

## Verdict

No arm meets the advance criterion on odd episodes. Per doc 15's stop rule, the method search is closed.

## References (equal-dataset mean J)

| reference | even J | odd J |
|---|---|---|
| EQSDp arm R + cutoff `s2armr_H1100` | 475.022 | 472.420 |
| Wald + cutoff `s2wald_l0.98_g0.3_H1100` | 475.057 | 472.526 |

## Arms against both references (paired, equal-dataset mean dJ; negative is better)

Verdict flags: c1 = dJ < 0 with CI upper end < 0 against both references; c2 = dL/T <= +0.1 pp; c3 = CVaR95 of
per-episode regret <= 1.10 x reference; c4 = no dataset worse than +1% of its J. All four must hold against both.

| arm | ref | even dJ [95% CI] | odd dJ [95% CI] | odd dJ % | odd dL/T pp | odd CVaR95 dJ | odd CVaR95 regret ratio | odd worst-dataset % | odd labels | odd verdict (c1 c2 c3 c4) |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 | eqsdp_cutoff | -1.179 [-1.862, -0.437] | 0.116 [-1.051, 2.019] | 0.025 | 0.079 | 32.1 | 1.242 | 1.54 | 44.8 | no (0100) |
| R1 | wald_cutoff | -1.213 [-1.902, -0.470] | 0.010 [-1.178, 1.902] | 0.002 | 0.075 | 31.8 | 1.241 | 1.51 | 44.8 | no (0100) |
| R2 | eqsdp_cutoff | -1.036 [-1.817, -0.255] | 1.085 [-1.048, 4.110] | 0.230 | 0.166 | 57.9 | 1.508 | 2.96 | 35.0 | no (0000) |
| R2 | wald_cutoff | -1.071 [-1.865, -0.273] | 0.979 [-1.171, 4.017] | 0.207 | 0.162 | 58.0 | 1.507 | 2.93 | 35.0 | no (0000) |
| R3 | eqsdp_cutoff | -1.607 [-2.687, -0.774] | 0.197 [-1.075, 1.832] | 0.042 | 0.067 | 33.4 | 1.229 | 1.31 | 51.9 | no (0100) |
| R3 | wald_cutoff | -1.641 [-2.722, -0.794] | 0.092 [-1.175, 1.760] | 0.019 | 0.064 | 33.4 | 1.228 | 1.29 | 51.9 | no (0100) |
| R2_roll | eqsdp_cutoff | -1.389 [-2.817, -0.367] | 0.036 [-0.627, 0.815] | 0.008 | 0.023 | 17.6 | 1.078 | 0.54 | 63.7 | no (0111) |
| R2_roll | wald_cutoff | -1.423 [-2.837, -0.388] | -0.070 [-0.738, 0.731] | -0.015 | 0.019 | 17.6 | 1.077 | 0.51 | 63.7 | no (0111) |

On even episodes every arm passed c1 against both references, as expected from best-of-grid selection (gains of
0.22 to 0.34 percent). On odd episodes the point estimates are about zero or slightly positive and every CI spans 0.
R2 additionally breaches dL/T (+0.16 pp), CVaR (1.51) and the worst-dataset bound (2.96 percent). R2-roll is the best
behaved (dJ +0.04 / -0.07, CVaR ratio 1.08, worst dataset 0.54 percent) but is statistically indistinguishable from
the references while spending 64 labels versus 71.

## Matched controls (arm minus control; negative favours the arm)

| arm | control | even dJ [CI] | odd dJ [CI] | odd d_labels |
|---|---|---|---|---|
| R1 | R1_control_calendar | -0.575 [-2.178, 1.027] | -0.273 [-2.923, 3.330] | 3.1 |
| R2 | R2_control_entropy | -1.196 [-2.332, -0.071] | -2.931 [-7.133, -0.405] | 1.9 |
| R2 | R2_extra_calendar | -4.488 [-7.292, -1.993] | -2.602 [-5.849, 1.355] | -3.7 |
| R3 | R3_ablation_no_tail | -0.571 [-1.705, 0.230] | -0.887 [-2.383, 0.211] | 16.9 |
| R3 | R3_ablation_tail_only | 0.008 [-0.064, 0.052] | 0.015 [-0.041, 0.062] | 1.0 |
| R2_roll | R2 | -0.352 [-1.916, 0.770] | -1.049 [-3.481, 0.709] | 28.8 |

R2 beats the entropy control on both splits (odd CI [-7.13, -0.41]) and the label-matched calendar only on even
(odd CI includes 0). R1 does not beat its calendar on either split. R3's gain over R2 on even is carried entirely by
the tail rule: tail-only equals R3 (odd dJ +0.015, CI [-0.04, 0.06]). R2-roll is not distinguishable from one-step R2.

## kc_311 episodes 37 and 39: starvation check (odd, 10 seeds, means)

Labels bought in (200, 800] and first deployment, versus the EQSDp cutoff reference.

| ep | policy | labels (0,200] | (200,800] | >800 | total labels | first deployment (event, seeds that deploy) | never-deployed frac | mean net |
|---|---|---|---|---|---|---|---|---|
| 37 | R1 | 23.7 | 34.4 | 0.0 | 58.1 | 104.9 | 0.0 | 1010.6 |
| 37 | R2 | 24.0 | 24.4 | 4.5 | 52.9 | 104.9 | 0.0 | 1152.2 |
| 37 | R2_roll | 26.4 | 42.0 | 38.7 | 107.1 | 104.9 | 0.0 | 813.8 |
| 37 | R3 | 26.5 | 37.1 | 22.7 | 86.3 | 104.9 | 0.0 | 947.2 |
| 37 | REF_eqsdp_cutoff | 26.7 | 52.9 | 0.0 | 79.6 | 104.9 | 0.0 | 723.0 |
| 39 | R1 | 20.4 | 43.5 | 0.0 | 63.9 | 701.1 | 0.0 | 718.8 |
| 39 | R2 | 18.8 | 30.8 | 24.2 | 73.8 | 684.2 | 0.2 | 881.3 |
| 39 | R2_roll | 22.2 | 47.3 | 46.4 | 115.9 | 655.7 | 0.0 | 691.3 |
| 39 | R3 | 21.8 | 44.8 | 39.5 | 106.1 | 649.9 | 0.1 | 774.9 |
| 39 | REF_eqsdp_cutoff | 22.4 | 57.2 | 0.0 | 79.6 | 629.2 | 0.0 | 669.2 |

The mechanism changes behaviour: R2-roll and R3 buy 23-46 labels after event 800 (the cutoff reference buys none),
while R2 buys only 24-31 in (200, 800] against the reference's 53-57 and so remains starved relative to it. This does
not lower cost: on ep 37 every arm is worse than the reference (R2-roll 813.8, R3 947.2, R1 1010.6, R2 1152.2 versus
723.0), and first deployment is identical (104.9) for every policy, so ep 37 is not a late-adoption problem on these
seeds. On ep 39 first deployment is later than the reference for all arms (R3 649.9, R2-roll 655.7, R1 701.1, R2 684.2
versus 629.2), and R2 never deploys in 20 percent of seeds.

## Reading

- Best-of-grid selection on even episodes overstated the effect: even grid best-minus-median was 0.01 to 0.57 J
  units against claimed gains of 1.0 to 1.6, and the odd reversal is larger still.
- All odd CIs against both references include 0; the best odd point estimate is R2-roll versus Wald at -0.07 J
  (-0.015 percent), far from the 2 percent goal.
- The tail rule carries R3, and EVSI beats label-matched entropy but not a label-matched calendar on odd. This does
  not support a distinct economic-EVSI claim. Hard cutoffs, finite-horizon VOI, Bayesian optimal switching and CVaR have
  prior art (doc 15 novelty note); no novelty claim is made.

## Continue/stop call

Stop. No arm advances; close the recovery method search. Paper 1 keeps the benchmark, the decision-harm measures and
the corrected-baseline finding (cutoff fee fix). The held-out chronological data are not built.

## Deviations and caveats

- R2 uses the Bayes posterior-mean preposterior rule; the quantile rule starved (J 500.7-506.2, about 2 labels) and is a
  negative result (doc 16).
- R2-roll (bundle lookahead, kmax in {2, 3}) was built because R2 and R3 beat both references on even episodes. It is
  one implementation of "short joint rollout"; others were not tried.
- Odd episodes ran only the chosen configuration of each arm. Doc 16 said odd numbers would also be reported against
  the grid median; that was not done and does not affect any verdict.
- Criterion 3 is implemented as CVaR95 of per-episode regret versus the hindsight best fixed model, arm over reference;
  CVaR95 of the per-episode paired dJ is reported alongside.
- The `stage5_odd.py` guard confirmed the freeze commit is an ancestor of `origin/<branch>` before running.

## Reproduce

```
export OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8
python scripts/paper1_eqsdp/stage5_run.py A|B|C|D   # each followed by stage5_analysis.py <pass>
python scripts/paper1_eqsdp/stage5_freeze.py        # then commit and push 16_RECOVERY_FREEZE.json
python scripts/paper1_eqsdp/stage5_odd.py
python scripts/paper1_eqsdp/stage5_analysis.py F even odd
```
Tables: `docs/paper1_eqsdp/tables/stage5_*.csv`.
