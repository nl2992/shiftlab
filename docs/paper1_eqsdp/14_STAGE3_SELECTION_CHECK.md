# 14 — Stage 3 selection check (odd episodes, run once)

Run 2026-11-08 on `research/paper1-eqsdp-foundation-2026-11-08`. The frozen candidate, frozen new reference, arm R and
`wald_l0.97_g0.2` were run once on the **odd** episodes of the nine datasets (374 episodes x 10 policy seeds = 3,740 jobs per
policy; per dataset: sf 50, kc 40, montgomery 24, dallas 50, dc 50, austin 50, cincinnati 33, oakland 27, sandiego 50) with the
same contract (B=200, c_q=.05, c_s=5, T=2000) and the same seed derivation (seed base, dataset hash, episode index, policy seed), so an
episode keeps its seeds whichever parity runs it. Nothing was retuned after seeing these episodes, and no Stage-4 confirmation data were
built, fetched or opened.

**Freeze order.** The freeze commit `167f5ae8d083b231a76572426da3f5b69f9cb9d6` (content: `13_STAGE2_FREEZE.md`,
`stage2_frozen_config.json`, code tree `scripts/paper1_eqsdp` = `3d0fd97a656b…`) was committed 2026-11-08 21:41:46 -0500 and was already contained in
`origin/research/paper1-eqsdp-foundation-2026-11-08` when `stage3_run.py` started at 21:41:59 -0500 (13 s later; `outputs/paper1_eqsdp/stage3/start.json`).
`stage3_run.py` refuses to start unless that is true. The odd-episode records were written after that start.

## Result under the fixed rule

Rule (from the plan, restated in doc 13): freeze-to-confirm iff paired dJ < 0 (candidate minus frozen new reference) with the 95% episode-bootstrap CI
excluding 0 (upper end < 0) and dL/T <= +0.1 pp.

**Verdict: FAIL.** dJ = **+1.074** (+0.225% of J_ref0) with CI [-1.495, +5.071], i.e. the point estimate is the wrong sign, the CI includes 0, and dL/T = **+0.121 pp**
[-0.009, +0.322] exceeds the 0.1 pp limit. The candidate is **not** frozen-to-confirm; per the plan Stage 4 is not run.

| candidate vs | dJ [95% CI] | % of J_ref0 [CI] | datasets better/worse | dataset-level t (p, two-sided) | dL/T (pp) [CI] | labels (cand / comparator) |
|---|---|---|---|---|---|---|
| **frozen new reference `s2armr_H1100`** (primary) | **+1.074 [-1.495, +5.071]** | +0.225% [-0.314, +1.064] | 8 / 1 | +0.41 (p=0.69) | +0.121 [-0.009, +0.322] | 46.6 / 70.9 |
| arm R `EQSDp_l0.98_g0.3` | -3.255 [-6.407, +1.139] | -0.683% [-1.344, +0.239] | 8 / 1 | -1.01 (p=0.34) | +0.196 [+0.040, +0.414] | 46.6 / 176.0 |
| `wald_l0.97_g0.2` | -3.271 [-6.467, +1.186] | -0.686% [-1.356, +0.249] | 8 / 1 | -0.92 (p=0.38) | +0.139 [-0.020, +0.362] | 46.6 / 176.0 |

Equal-dataset J on the odd episodes: candidate 473.494, new reference 472.420, arm R 476.750, `wald_l0.97_g0.2` 476.765 (J_ref0 = 476.765).
Switches: candidate 1.159, new reference 1.182. Full table with all components and CIs: `tables/stage3_comparisons.csv`;
numbers in `outputs/paper1_eqsdp/stage3/summary.json`.

Other rows of the same table (no candidate involved): the frozen **new reference beats `wald_l0.97_g0.2` on the odd episodes**:
dJ -4.345 (-0.911%) [-5.410, -2.926], 8/9 datasets, dL/T +0.018 pp [-0.036, +0.090]; it also beats arm R by -4.329 (-0.908%) [-5.312, -2.969], 8/9.
So the fair reference (arm R plus a hard label stop at H=1100, chosen on even episodes) generalises to the odd episodes. Arm R vs `wald_l0.97_g0.2`: -0.016 [-0.339, +0.303], 4/9 (a tie, as in Stage 0/1).

Per-dataset dJ (candidate minus new reference): sf -1.51, **kc +21.85**, montgomery -1.07, dallas -1.42, dc -2.55, austin -0.19, cincinnati -3.62, oakland -0.53,
sandiego -1.29. The candidate is slightly better than the new reference on 8 of 9 datasets (sign count 8/1) but the equal-dataset mean is dominated by kc_311.

Components of the primary difference (candidate minus new reference, loss units per episode; they sum to dJ): late adoption +1.718 [-0.354, +5.279],
false promotion +0.634 [-0.302, +2.092], reversal churn -0.082, label spend -1.218 [-1.313, -1.126], residual +0.023. Label spend falls as in Stage 2
(-24.4 labels), but the decision-side terms are worse than in the even episodes (even: late adoption -0.07, false promotion -0.31).

## Post-hoc diagnostic (descriptive, did not influence anything above)

On kc_311 the candidate is +21.85 worse than the new reference (late adoption +15.9, false promotion +7.6). One episode (odd index 39) contributes +607.8 of the
40-episode sum's 874 (+15.2 of the +21.85 mean): the candidate adopted the better challenger about 940 events later than the new reference (late adoption +610), and
another episode (index 37) has a false promotion of +217. The remaining 38 kc episodes are close (15 episodes worse by > 1, 23 better by > 1). Excluding kc_311 the mean dataset
difference would be -1.52 (the even-episode figure was -1.72), but that exclusion is post hoc, selects the outcome, and is not used for the verdict. Interpretation: the gate's
saving (about 24 labels) is stable across both parities, while the gate's risk, withholding labels exactly when an early adoption needs them, shows up as rare large losses
that the 10 even-episode kc_311 draws did not contain. This is a single heavy-tailed dataset, not enough to say the mechanism fails elsewhere, and not enough to rescue the claim.

## What this means (continue / pivot / stop)

- Selection check failed as pre-registered: do not freeze this candidate and do not open Stage-4 data for it.
- The only robust, replicated finding of Stage 1-3 is the **fee cut**: arm R plus a hard end-of-horizon label stop saves about 0.9% of J_ref0 on odd episodes at +0.02 pp loss, and
  this also held on even episodes (-0.64%). It is a one-line rule available to any reference policy, so it is a baseline correction, not a novelty claim.
- Over that fair reference the C1 gate gave -0.36% on even episodes (best of 80) and +0.23% (not significant, wrong sign) on odd episodes, with a loss increase above the limit.
  The two parities disagree in sign (no pooled test was run). A verdict of "pivot" for the label-gating line (a heavy tail on one dataset, a small average effect), with a "stop" for
  the 2% central-claim target: neither module B nor module G earned a place (B and the stop were left off by the BO; G's ablation was a tie and its add-back changed nothing).
- Optimism accounting: the even-episode gain (-1.72) shrank to +1.07 on fresh episodes of the same datasets, in line with the flat landscape seen in the BO (median feasible configuration -0.12).

## Reproduction

```
export OPENBLAS_NUM_THREADS=1
PY="<main checkout>/.venv/Scripts/python.exe"
$PY scripts/paper1_eqsdp/stage3_run.py          # guarded: freeze file committed, unmodified, pushed; odd episodes; ~1 min
$PY scripts/paper1_eqsdp/stage3_analysis.py     # tables/stage3_comparisons.csv, outputs/paper1_eqsdp/stage3/summary.json
```
Records: `outputs/paper1_eqsdp/stage3/run/records.jsonl` (not committed; `outputs/` is gitignored).
