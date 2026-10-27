# Integrated state-machine null calibration protocol v1

**Status:** frozen development/calibration protocol; this is not an efficacy confirmation.
**Date:** 2026-10-26.

## Purpose and limits

Check the composed monitor, candidate-selection/certification, and rollback state machine for implementation errors under the conditional-mean assumptions used by its component e-processes. This Monte Carlo exercise is a diagnostic for the registered implementation. It does not replace the conditional supermartingale arguments, validate assumptions on real data, or establish power or economic benefit.

The three error events remain distinct: Q1 false escalation at alpha 0.02, Q2 false promotion at family alpha 0.015, and Q3 false rollback at alpha 0.015. The state machine's claimed familywise bound is at most 0.05 only when each component's null and filtration conditions hold and the later-stage tests remain conditionally valid after earlier decisions. Summing component alpha values is the mathematical argument; calibration checks code and the registered synthetic mechanisms.

## Frozen implementation and information contract

Use `integrated_pipeline.run_seed` with 3,200 events, CUDA generation, the existing 800/800/800/800 chronological blocks, immediate labels, and the 640-label pathwise cap. Candidate policies are frozen before the Q1 block. Q2 scouting and certification use separate halves of the 1,600–2,400 block. Q3 rollback uses only fresh 2,400–3,200 feedback. Evaluator truth is used only to label calibration nulls and compute metrics. Learner choices continue to use observed queried labels and the registered candidate scores.

Run four registered error cells with 1,000 eligible independent stream seeds each (Q1 has two 1,000-stream cells):

| Error event | Calibration cell | Null definition | Eligibility |
|---|---|---|---|
| Q1 | `stationary` | Stationary iid outcomes; incumbent/reference conditional paired-cost mean is at most the 0.10 margin. | Every stream. |
| Q1 | `benign_nuisance` | Large nuisance-coordinate shift begins before the Q1 monitor; the signal coordinates and conditional outcome law are unchanged, so paired decision harm remains at most 0.10. | Every stream. |
| Q2 | `calibration_candidate_null` | Q1 is triggered by the registered event-800 harmful policy change. A predeclared non-identical candidate family changes the all-positive incumbent only for feature scores at or above the Bayes cost threshold; there, its conditional expected incumbent-minus-candidate gain is nonpositive. Elsewhere it equals the incumbent. Fresh certification therefore tests a genuine composite null after Q1 has triggered. | Continue the seed block until 1,000 streams both trigger Q1 and select a candidate; count false promotion only on these streams. The evaluator must confirm the selected policy's certification-block expected net gain is at most zero. Stop after at most 3,000 attempts. |
| Q3 | `boundary_local_harm`, severity 3.0 | A candidate that passes Q1 and Q2 remains under the same stationary post-change law through deployment. Count rollback only for a promoted policy whose independent population evaluation establishes expected candidate gain at least the negative amortized rollback charge. | Continue the registered seed block until 1,000 eligible promotions, up to 2,500 streams. Eligibility uses a separate GPU-generated Monte Carlo covariate sample and a one-sided Hoeffding lower bound; it never uses deployment labels or rollback outcomes. |

The Q2 calibration family is a diagnostic construction, not a proposed candidate learner. For the `iid_regression` label law with sigma 0.3 and costs FN=5, FP=1, its score cutoff is `0.3 * Phi^-1(FP/(FN+FP))`. Each candidate switches from action 1 to 0 only on `[cutoff, cutoff + width]`, for registered widths from 0.03 to 0.30. This makes the challengers non-identical and pointwise non-improving while retaining label-noise variation for the independent certificate. The fixed widths and construction are applied before Q1 decisions and do not inspect labels or oracle probabilities.

For Q3 eligibility, evaluate the selected context-specific candidate rule on 100,000 independent standard-normal feature vectors generated with CUDA. Compute exact conditional expected costs under the post-change boundary-local DGP, then subtract the Hoeffding radius `M * sqrt(2 log(1/delta) / N)` with `M=max(FN,FP)` and `delta=1e-8`. A stream qualifies only if the lower bound on its per-event expected incumbent-minus-candidate gain is at least `-ROLLBACK_COST / deployment_length`. At most 2,500 candidates are examined, so the union bound on any eligibility misclassification is at most 0.000025. Record the eligible population gain, lower bound, sample size, and delta. This certification is only for the stated synthetic generator and selected policy.

## Seed blocks, estimates, and decision rule

Use disjoint deterministic seed blocks: stationary Q1 starts at 2026112000; nuisance-shift Q1 starts at 2026113000; Q2 starts at 2026114000; Q3 starts at 2026115000. For Q2 and Q3, scan consecutive seeds and retain the first 1,000 eligible streams, without inspecting promotion-error or rollback outcomes when selecting eligibility. Persist every attempted stream and its eligibility reason.

Report each cell's error count, denominator, exact one-sided Clopper–Pearson upper bound, and hard-cap violations. Use a Bonferroni-adjusted one-sided confidence level with total familywise confidence error 0.05 across the four cell endpoints. A cell passes the diagnostic only if its adjusted upper bound is no greater than that stage's alpha, all registered null/eligibility checks pass, every Q2 stream reaches the gate, and no run exceeds 640 labels. Any failure blocks integrated efficacy confirmation; do not tune the frozen state machine using these seeds.

Save per-stream metrics, per-cell summaries, protocol and source hashes, CUDA environment, run status, and independent verifier output under `outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v1/`. Use a separate pilot output directory and seed range for any development run. Do not make figures from this calibration; no visual deliverable is required.

## Known scope exclusions

This calibration covers the registered independent synthetic stage blocks and declared conditional-mean nulls only. Delayed feedback, dependent or recurring streams, performative outcomes, propensity misspecification, alternative cost matrices, and real data remain empirical stress settings requiring separate contracts. A pass cannot be described as a proof of the integrated claim or as evidence of efficacy.
