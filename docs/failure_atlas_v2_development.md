# Failure Atlas v2: development stage and frozen candidates

2026-11-03. Development seeds 100-199 (seed base 20261103), 20 discovery regimes, 25 policies,
50,000 episode runs. Raw: `outputs/failure_atlas_v2/development-part{1,2}/` (part 1 was stopped
mid-regime and resumed with more workers; rows of the partially finished regime
F3_reversal_800 from part 1 were discarded and the regime rerun whole in part 2). Summary:
[development_summary.json](failure_atlas_v2_results/development_summary.json).

## Candidates

* **RMM (attachable, Path A)** — `scripts/failure_atlas_v2/restart_monitor.py`. Wraps a base
  policy with a label-clock weighted Shiryaev-Roberts e-detector over a grid of restart points
  (every 10 labels, uniform prior mass, total one; bets lambda in {.15,.3,.5}), keeps acquiring
  after the base's verdict, and on an alarm switches and restarts the base on the remaining
  horizon/budget. Base runs at alpha/2, detector at alpha/2 (halved per re-promotion).
* **LRMD (standalone, Path B)** — the same detector with all alpha, no base, the start prior
  w_first=.5 on the first start (rest uniform), and horizon-weighted acquisition
  q_t = min(1, 2 * remaining / (rate (T - t))) on disagreements.

Validity of both rests on the uniform conditional null (challenger never better on
disagreements given the past); see `label_clock.py` docstring. It does not cover
stationary-but-dependent nulls.

## Development results (mean net cost over regime families; lower is better)

| policy | all 20 | stationary alt (7) | late (4) | other change (4) | null (5) | F0_null promote | rho=.8 null promote |
|---|---:|---:|---:|---:|---:|---:|---:|
| Model Selector (no error control) | 371.20 | 354.04 | 374.76 | 384.50 | 381.72 | .96 | .93 |
| Model Picker (no error control) | 372.21 | 356.68 | 375.05 | 383.48 | 382.66 | .92 | .96 |
| **LRMD_w50 (frozen as LRMD)** | **380.01** | 383.95 | 380.00 | 394.00 | 363.30 | .05 | .25 |
| LRMD (uniform starts, k=2) | 381.35 | 390.37 | 375.42 | 395.17 | 362.42 | .03 | .24 |
| SMCS + RMM | 383.29 | 394.60 | 378.08 | 395.53 | 361.82 | .01 | .18 |
| LRMD_single (no restarts) | 383.30 | 381.32 | 400.13 | 397.53 | 361.22 | .03 | .19 |
| LRMD_w50_k1 (uniform pacing) | 383.36 | 394.78 | 377.34 | 396.14 | 361.96 | .02 | .13 |
| DISCERN + RMM | 385.74 | 400.48 | 377.94 | 398.00 | 361.54 | .00 | .12 |
| Gated + RMM | 386.45 | 402.01 | 378.62 | 397.88 | 361.79 | .00 | .10 |
| Gated + RMM, no restart of base | 386.49 | 402.01 | 378.62 | 397.96 | 361.89 | .00 | .10 |
| Gated + RMM, single start | 387.48 | 392.55 | 399.08 | 399.17 | 361.74 | .02 | .11 |
| Gated, front-loaded (strongest reading) | 387.49 | 394.31 | 402.05 | 396.88 | 358.79 | .01 | .05 |
| P7s (ours, prior) | 388.48 | 406.79 | 380.52 | 400.17 | 359.86 | .00 | .08 |
| never switch | 388.77 | 428.94 | 392.94 | 362.60 | 350.12 | .00 | .00 |
| Gated + RMM, no post-verdict acquisition | 389.10 | 409.50 | 378.36 | 398.96 | 361.24 | .01 | .04 |
| SMCS | 390.73 | 401.28 | 400.53 | 400.03 | 360.66 | .03 | .10 |
| Xu acquisition-only | 390.80 | 406.03 | 393.99 | 399.56 | 359.91 | .01 | .02 |
| Gated, label-clock evidence only | 392.61 | 409.95 | 399.87 | 396.81 | 359.19 | .00 | .01 |
| Gated | 396.93 | 432.51 | 402.92 | 374.78 | 360.07 | .00 | .00 |
| DISCERN | 398.38 | 437.85 | 402.92 | 372.59 | 360.10 | .00 | .00 |

## Attribution (Gated base unless noted)

* **Restart mixture** is what repairs late improvement: late-family cost 378.6 with it,
  399.1 with a single start, 402.9 for Gated. On stationary alternatives the single start is
  cheaper (392.6 vs 402.0), the price of spreading prior mass over restarts; LRMD's w_first=.5
  recovers most of it (383.95 vs 381.32 single, 390.37 uniform).
* **Post-verdict acquisition** contributes 2.6 overall (389.10 -> 386.45), mostly on
  stationary alternatives; it is also what feeds rollback.
* **Restarting the base** contributes nothing measurable (386.45 vs 386.49): after an alarm
  the base's own evidence is too weak to matter. This is why the standalone is stronger.
* **Label-clock evidence alone** (no restarts, base pacing) gives 396.9 -> 392.6;
  **front-loading alone** gives 387.5. Both are cheaper fixes to the IPW range problem than
  the restart mixture and must be beaten by it, which LRMD does on dev (380.0).
* **Horizon-weighted pacing** (k=2 vs 1): 380.0 vs 383.4.
* Wrapping the uncontrolled selectors does not help (Model Picker 372.2 -> 377.9 with RMM);
  they already switch quickly and RMM only adds forced labels and alarms.

## Recorded negatives

* **Dependence safety fails.** Every label-clock variant raises false promotion on the
  Markov null: rho=.8 .10-.25 and rho=.95 .44-.79 (Gated .00/.01). Label-clock evidence makes
  densely sampled persistent outcomes count as independent bets. The guarantee is stated for
  the conditional null only; dependence-robust use is not claimed.
* **Reversal, transient and recurrent regimes get worse** (other-change family 374.8 for
  Gated -> 386-398 with any repair; never-switch 362.6 is best there). Promoting on a genuine
  but temporary advantage and rolling back costs more than the advantage under c_s=5.
* LRMD_w50's F0_null promotion is .05 on 100 seeds, at the nominal level.

## Frozen for validation (selection rule declared before this table was read: lowest
mean development cost over all 20 regimes with F0_null promotion <= .05)

* Standalone: **LRMD = LRMD_w50** (pace k=2, w_first=.5, gap 10, lambdas .15/.3/.5, alpha .05).
* Attachable: **RMM** default (uniform starts, gap 10, alpha split .5, pace k=1), attached to
  Gated, DISCERN and SMCS.
* Ablations carried: LRMD_single, LRMD_w50_k1, Gated+RMM_single, Gated+RMM_noacq.

Validation primary family for the SOTA claim (fixed now): **late improvement and stationary
better** (V_late_*, V_better_*), versus the best error-controlled published comparator
including front-loaded Gated/DISCERN; nulls for safety; reversal/transient/recurrent are
reported as the known adverse region.
