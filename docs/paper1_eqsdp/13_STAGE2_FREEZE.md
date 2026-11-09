# 13 — Stage 2 (fair reference + constrained BO) and the FREEZE

Run 2026-11-08 on `research/paper1-eqsdp-foundation-2026-11-08`, following `10_JOINTBAYES_PLAN.md` Stage 2
and the Stage 1 note `12_STAGE1_RESULTS.md` (which found that a plain late-label stop gives Wald most of C1's gain).
**Even episodes only** (377 episodes x 10 policy seeds = 3,770 jobs per policy, nine datasets, B=200, c_q=.05,
c_s=5, T=2000, delay as registered). Odd episodes had not been run by any script at the time of the freeze
(`outputs/paper1_eqsdp/stage3` does not exist). Everything below is tuning evidence on the exposed development
episodes, selection-optimistic, not confirmatory. All numbers come from the scripts listed at the end.

## 1. Step 1 - fair re-tuned reference (84 Wald + 7 arm R + 4 thinning variants)

Grid (`stage2_ref_run.py grid`, 91 policies, 3,770 jobs): Wald lambda in {.95,.97,.98,.99} x gamma in {.1,.2,.3} x hard stop
H in {0 (unreleasable only), 500, 900, 1100, 1300, 1500, 1750}; arm R `EQSDp_l0.98_g0.3` x the same H. The 20 Stage-0 Wald
policies without a stop are also in the pool (116 policies in all). Uniform thinning k in {.5,.25} was run on the best
feasible Wald+stop and the best feasible arm R+stop (`H=1100`): k=.5 gives J +0.5 worse than the unthinned
`H=1100` versions (475.55 / 475.61; dL +0.23 pp, infeasible), k=.25 is much worse (J ~480.2, dL +0.53 pp), so thinning is not part of any reference.
Reference rule: lowest equal-dataset mean J subject to dL/T <= +0.1 pp versus `wald_l0.97_g0.2` (paired, equal dataset weights).
52 of 116 policies are feasible. Full table: `tables/stage2_ref_grid.csv`.

| | policy | J | dJ vs `wald_l0.97_g0.2` (%, 95% CI) | dL/T (pp) | labels | datasets better |
|---|---|---|---|---|---|---|
| original reference | `wald_l0.97_g0.2` | 478.075 | - | - | 176.3 | - |
| **new reference (constrained best)** | `s2armr_H1100` = arm R + stop H=1100 | **475.022** | -3.053 (-0.639%) [-4.551, -1.013] | +0.078 | 70.7 | 8/9 |
| best feasible Wald+stop | `s2wald_l0.98_g0.3_H1100` | 475.057 | -3.019 (-0.631%) | +0.078 | 70.7 | |
| unconstrained best | `s2wald_l0.97_g0.2_H1500` | 474.713 | -3.362 (-0.703%) [-5.163, -1.084] | +0.248 | 35.2 | 8/9 |
| arm R | `EQSDp_l0.98_g0.3` | 478.154 | +0.079 (+0.016%) [-0.395, 0.555] | -0.058 | 176.3 | 2/9 |

The new reference is the **stronger** reference every later comparison uses: it is arm R with the cheap fee cut, so the fee
cut is no longer a candidate advantage. (An H=0 stop alone, i.e. no purchase that can never be released, is worth only -0.42.)

## 2. Step 2 - constrained Bayesian optimisation

**Optimiser used: BoTorch 0.18.1** (`uv pip install botorch` into the main checkout venv took 2 s; torch 2.9.1 CPU use; imported at
once, well under the 10-minute limit): `qLogNoisyExpectedImprovement` on a `ModelListGP` (one `SingleTaskGP` with standardised
outcome per outcome: J and dL/T), outcome constraint dL/T - 0.1 pp <= 0 versus the new reference, 10 restarts x 512 raw samples.
Initial design: 20 scrambled-Sobol points (seed 20261108), then 60 BO iterations: 80 evaluations in all, 1,643 s of evaluation
(mean 20.5 s), each one full even-episode run (3,770 jobs, 16 workers). Objective: equal-dataset mean J. Every evaluation is
logged (`outputs/paper1_eqsdp/stage2/bo/evals.jsonl`; tables/`stage2_bo_evals.csv`).

**Search space (9 dims, mixed; `stage2_space.py`):** EQSDp lambda [.95,.995], gamma [.1,.5]; C1: rho0 {off} U [.005,.2] log, s [0,2],
lookahead h in 0..12, floor probability [0,.3] (Stage 1 grid widened about 2x); optional hard stop H in {none, 900, 1000, ..., 1600, 1750};
**module B** weight bw in [0,1] with 0 = ignore pending labels in the reachability lookahead (L = round(bw x pending) + 1 + h;
bw=1 is Stage 1 C1); **module G** strength gs in [0, 1.5], 0 = off: the lag-1 autocorrelation r of released disagreement outcomes is
estimated online by `DepWald`'s estimator (ported unchanged from `scripts/qsg_methods_search/next_method.py`) and the Beta
counts are divided by f = ((1+r)/(1-r))^gs. Toggles are continuous dims thresholded to "off" at the low end. Continuous relaxation is
used for the stop bins and the integer h. Tests (32 in total, `scripts/paper1_eqsdp/tests`) verify: the default module settings equal Stage 1
C1 exactly, gate-off + stop equals the Stage 1 stop control exactly, everything off equals arm R exactly, the budget is respected, runs are
deterministic, and the policy module never reads evaluator names.

**Outcome of the search.** 55 of 80 configurations were feasible; 30 of those were below the new reference's J. Sobol best feasible
474.113, BO best feasible **473.354** (evaluation 71). The median feasible configuration is only -0.118 below the new reference (quartiles
-0.60 / +1.08), the best-5 mean -1.26. So the landscape is flat around the reference, the gain is concentrated in a small corner,
and the best-of-80 number is optimistic (see caveats). Pareto frontier of (J, L/T) over all 80 evaluations: evaluations 71, 75, 78,
76, 73, 46, 63, 56, 37, 36 (J from 473.35 to 482.75, L/T from 23.26% to 23.11%); the joint frontier with the step-1 grid is
`tables/stage2_pareto.csv` (rows with `pareto=True`): the lowest-J points are all BO configurations; below L/T 23.13% the Wald/arm R + stop grid points
`s2armr_H500` (J 475.59) and `wald_l0.98_g0.5` (J 484.66) take over.

**BO best feasible (evaluation 71):** lambda=.9675, gamma=.2641, rho0=.0079, s=.7779, h=12, floor=.0765, stop none, **bw=0** (module B off),
gs=1.5 (module G at the upper bound of its range), J=473.354, dJ vs new reference -1.669, dL/T -0.002 pp.

### Ablations of the BO best (paired dJ = ablated - full, even episodes; `tables/stage2_ablation.csv`)

| module | in the BO best? | dJ [95% CI] | datasets (ablated better/worse) | dL/T (pp) | removal hurts? |
|---|---|---|---|---|---|
| B (pending-label weight) | already off (bw=0) | n/a | | | no (BO left it off) |
| stop | already off (none) | n/a | | | no (BO left it off) |
| G (dependence-calibrated belief) | on (gs=1.5) | **-0.055 [-0.309, +0.179]** | 4 / 5 | -0.013 | **no** (CI includes 0, point favours removal) |
| C1 gate (rho0 = 0) | on | **+4.474 [+2.659, +5.762]** | 1 / 8 | -0.132 | **yes** (+0.94%) |

Supplementary add-one check (not used for selection, `tables/stage2_addone.csv`; paired dJ = final + module minus final): adding B back (bw=1) dJ +0.357 [-0.03,
+0.80], bw=.5 +0.010, adding G at 1.0 -0.026 [-0.254, 0.210] and at 1.5 +0.055, adding a stop H=1300 +0.136 [-0.61, 1.01], H=1600 +1.832
[0.55, 3.26]. None helps; the fee cut is already provided by the gate (which implies an end-of-horizon stop when no outcome can pay back c_s).

**Selection rule (fixed in the task brief before running):** the final candidate is the BO best feasible configuration with every module
whose ablation does not hurt removed. Module G is removed. B and stop were off in the BO optimum. The **final candidate is the C1 gate on EQSDp
(Beta posterior), no B, no G, no stop**: i.e. Stage 1 C1 with `bw=0` (pending labels *not* counted in the lookahead) and re-tuned lambda, gamma, rho0, s, h, floor.

## 3. Even-episode result of the final candidate (J 473.298)

Paired by (dataset, episode); dJ < 0 better; CI = percentile over per-dataset episode bootstraps (2,000), equal dataset weights;
`tables/stage2_final_vs.csv`. For comparison the "full" BO best (G on, 473.354) is also in the CSV.

| comparator | dJ [95% CI] | dJ % of J_ref0 | datasets better/worse | dL/T (pp) [CI] | dataset-level t (p, two-sided) |
|---|---|---|---|---|---|
| **new reference `s2armr_H1100`** | **-1.724 [-2.473, -1.040]** | -0.361% [-0.517, -0.218] | **9 / 0** | -0.015 [-0.052, +0.018] | -6.42 (p=0.0002) |
| arm R `EQSDp_l0.98_g0.3` | -4.855 [-5.991, -3.337] | -1.016% [-1.253, -0.698] | 8 / 1 | +0.122 [+0.066, +0.196] | -5.53 (p=0.0006) |
| `wald_l0.97_g0.2` | -4.777 [-6.014, -3.123] | -0.999% [-1.258, -0.653] | 8 / 1 | +0.063 [+0.002, +0.144] | -3.65 (p=0.0065) |

(% of J_ref0 = equal-dataset mean J of `wald_l0.97_g0.2` = 478.075.) Labels 47.1 (new reference 70.7, arm R / Wald 176.3);
switches 1.205 (new reference 1.254).

Component decomposition via `trace_run` (final minus comparator, loss units per episode; the five components sum to dJ):

| vs | late adoption | false promotion | reversal churn | label spend | residual | dJ |
|---|---|---|---|---|---|---|
| new reference | -0.067 | -0.305 | -0.174 | **-1.180** | +0.002 | -1.724 |
| arm R | +1.016 | +1.318 | -0.660 | **-6.460** | -0.068 | -4.855 |
| `wald_l0.97_g0.2` | -0.410 | +1.777 | +0.344 | **-6.460** | -0.028 | -4.777 |

Reading: against the new reference the saving is again mostly fee-side (-1.18 label spend, -23.6 labels) plus a small decision-side gain (false
promotion -0.31, churn -0.17), at a loss change of -0.015 pp (not worse). Against the old reference the gain is the fee cut (-6.46); the decision side is a
small net cost (false promotion +1.3 to +1.8). The effect over the *fair* reference is about 0.36% of J_ref0: a small effect on the
fair-evaluation scale, below the 2% central-claim target in the plan, and the number is best-of-80 on the scored episodes.

## 4. Caveats (read before interpreting)

- **Optimism.** The final configuration is the best of 80 evaluations on the same 377 even episodes that score it, then simplified. The
  median feasible configuration beats the new reference by only 0.12, the top-5 mean by 1.26; the final -1.72 is above all of these. The honest
  forward expectation is lower, and the Stage 3 odd-episode run is the first unbiased look. The new reference was also tuned on a 116-policy grid
  on the same episodes, with the same effort that the candidate had in 80 evaluations (but with a 9-dim space).
- gs=1.5 sat at the upper bound of module G's range in the BO best, so G's tuning may be range-limited; it was removed by the rule anyway (its ablation is a tie).
- The BO uses a continuous relaxation of discrete choices (stop bins, h), and a 9-dim GP at 80 points is coarse.
- The new reference is arm R + stop (EQSDp), not a Wald policy, because the constraint (+0.1 pp vs `wald_l0.97_g0.2`) removed the stronger-fee-cut Wald stops
  (H=1300/1500 give dL +0.11..+0.25 pp). The unconstrained best (Wald lambda .97, gamma .2, H=1500, J 474.713) is worse in loss and is reported, not used.
- The C1 reachability gate is a heuristic (equal-weight approximation of the discount, Beta-binomial reach probability), not a validity guarantee. This is a
  cost-policy study under the fixed simulator contract; no Paper-1 null/validity claim is made.
- Deviations: (i) thinning was run on the best feasible Wald+stop and best arm R+stop at H=1100 (the reading of "the best stop") with arm R + stop thinning added to the
  registry; (ii) `trace_run.registry` gained the Stage 2 names (new names only); (iii) a worker initializer in `stage2_eval.py` retries the git calls of
  `b3_plus_policy.load_b1` because they fail intermittently with 16 simultaneous workers on this OneDrive path (no effect on any result); (iv) the first BO launch died after evaluation 19 (threadpoolctl cannot load a DLL under the non-ASCII path); botorch's
  `threadpool_limits` was replaced by a no-op (BLAS is single-threaded) and the run **resumed** from the JSONL checkpoint (evaluations 0-19 are the unchanged Sobol points);
  (v) the supplementary add-one check and the descriptive summary were added after seeing the BO best, and do not enter the selection.

## 5. FREEZE (committed and pushed before any odd-episode run)

**Final candidate** (`Stage2Policy`, `scripts/paper1_eqsdp/stage2_policies.py`; the machine-readable copy is `docs/paper1_eqsdp/stage2_frozen_config.json`, which
`stage3_run.py` refuses to run without, unless that file is committed, unmodified and contained in `origin/<branch>`):

```
lam=0.9675  gamma=0.2641  rho0=0.0079  s=0.7779  h=12  floor=0.0765  kappa=1.0 (default)
stop_h=None  bw=0.0 (module B off)  gs=0.0 (module G off)  thin=1.0
base: EQSDp stake=False, evidence = discounted disagreement counts, Beta(k+1, n-k+1), switch test at release time;
purchases drawn from the same named random stream as arm R (r("EQSD"))
```

**Frozen new reference:** `s2armr_H1100` = arm R `EQSDp_l0.98_g0.3` + hard end-of-horizon label stop H=1100 (no purchase when t + delay > T - 1100).

**Also run in Stage 3 (unchanged):** arm R `EQSDp_l0.98_g0.3`, and `wald_l0.97_g0.2`.

**Stage 3 test (fixed in `10_JOINTBAYES_PLAN.md`, restated):** on the odd episodes (same contract, same seed bases, the episode index kept
in the seed derivation: seed streams are keyed by (seed base, dataset hash, episode index, policy seed), so an odd episode has the same seeds whichever split runs it).
Primary: paired dJ = J(candidate) - J(frozen new reference), equal-dataset pooled, 95% percentile CI over per-dataset episode bootstraps (2,000 resamples);
**freeze-to-confirm iff dJ < 0 with the CI upper end < 0 and dL/T <= +0.1 pp** (point estimate, versus the new reference). Also reported: the dataset-level paired t-test
over the nine per-dataset mean differences, the sign count over nine datasets, the same comparisons against arm R and `wald_l0.97_g0.2`, and the component decomposition.
No retuning after seeing odd episodes. If the rule fails the result is reported as a failure and the Stage 4 data are not built, fetched or opened.

**Code identity.** Git trees at the freeze commit: `scripts/paper1_eqsdp` = `3d0fd97a656bbac23c78814632dd6802935de4ee`,
`scripts/qsg_methods_search` (frozen code, untouched) = `467e279d698fb1de649f785b3721ad30d59ef041`, `scripts/promising_directions` = `8ab716697c52fb6603ce213d6815d9bc62b3bc88`.
Blob ids: `stage2_policies.py` `ab3e3e6fff65`, `stage1_policies.py` `014681439ccc`, `stage2_space.py` `dc9c2c80c7d3`, `stage2_eval.py` `8d15d944da0b`,
`trace_run.py` `4baf41524cc8`, `stage3_run.py` `474e2801576a`, `stage3_analysis.py` `c84ac5a7852d`; `docs/paper1_eqsdp/stage2_frozen_config.json` `8763efcd803a`.
The freeze commit hash and time are in the final commit message / `git log` (the commit that adds `stage2_frozen_config.json`); `outputs/paper1_eqsdp/stage3/start.json` records the Stage 3 start time and that commit.

## Commands

```
export OPENBLAS_NUM_THREADS=1
PY="<main checkout>/.venv/Scripts/python.exe"
$PY scripts/paper1_eqsdp/stage2_ref_run.py grid                       # ~30 min detached, 91 policies
$PY scripts/paper1_eqsdp/stage2_ref_run.py thin s2wald_l0.98_g0.3_H1100_k0.5 s2wald_l0.98_g0.3_H1100_k0.25 s2armr_H1100_k0.5 s2armr_H1100_k0.25
$PY scripts/paper1_eqsdp/stage2_ref_analysis.py                       # new reference -> tables/stage2_ref_grid.csv, ref_summary.json
$PY scripts/paper1_eqsdp/stage2_bo.py                                  # BO, resumable, ~35 min detached
$PY scripts/paper1_eqsdp/stage2_final.py                               # ablations, selection, comparisons, Pareto
$PY scripts/paper1_eqsdp/stage2_addone.py ; $PY scripts/paper1_eqsdp/stage2_summary.py
$PY -m pytest scripts/paper1_eqsdp/tests -q                            # 32 tests
```
