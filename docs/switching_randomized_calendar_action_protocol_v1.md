# Randomized calendar lottery with full action control: registered comparison

**Registered:** 2026-10-28 before implementation. **Purpose:** strengthen the deterministic-calendar baseline by jointly optimizing a private lottery over two calendar branches and each branch's complete action policy.

## Frozen cell and branches

Use the certified `T=6, B=3, d=1, alpha=1/10, c=1/100, k=1/10` recurrent-HMM cell, with symmetric transition rates `1/4`, emissions `(1/20,19/20)`, and prior `1/2`. Branch A makes no queries. Branch B queries at events `1,2,3`. At the outset the learner privately draws a branch; at event 1 the query choice reveals the branch to the causal-null adversary. Each branch gets a fully optimized action policy with promotion, holding, rollback and re-promotion under the same economic HMM. The shared unconditional false-promotion risk budget is `alpha`, and branch probability is accounted through scaled sequence-form realization weights.

Because the schedules differ at the first query choice, the null can use distinct conditional outcome laws after observing the branch. Thus the robust risk of a lottery is exactly the branch-probability-weighted sum of branchwise worst-case risks. No branch may exceed its weighted contribution merely because the schedule lottery was private before event 1. The alternative HMM determines expected utility; the null remains a separate conditional-mean adversary.

## Exact optimization and verification

Build both learner sequence forms and their separate null-response duals, link their root realization masses to a single probability simplex, and constrain the sum of the two branchwise robust-risk epigraphs by alpha. This is a joint LP over all lotteries and branch action policies, not a grid over lottery weights. Rebuild HMM cost coefficients with rational arithmetic, rationalize and check a dual lower bound, and independently reconstruct the recovered branch policies to verify exact costs, pathwise query use and weighted null risk. Compare the certified mixed-calendar value to the unrestricted adaptive oracle's feasible upper policy.

Run with `$env:PYTHONPATH='src;.'; python scripts/solve_switching_randomized_calendar_action.py`, then verify with `$env:PYTHONPATH='src;.'; python scripts/verify_switching_randomized_calendar_action.py`. Store the certificate and policies under `outputs/switching_randomized_calendar_action_v1/results.json`.

## Limits

This class allows a lottery between only the no-query and early three-query calendars. It is stronger than either deterministic calendar and allows full switching control, but it is not the complete randomized-calendar class and does not adapt acquisition to observed labels. A gap from the unrestricted oracle is a finite, precise separation from this class, not a scalable method or novelty conclusion. Keep false-promotion validity separate from current-regime benefit and post-reversal future utility.

## Result

The optimal mixture assigns probability `1/5` to no query and `4/5` to calendar `(1,2,3)`. In the early-query branch, the recovered full-action policy promotes only after `111`; its conditional robust-null risk is `1/8`, contributing `1/10` after the lottery. The no-query branch never promotes. The mixture requests `12/5` labels in expectation and obeys the pathwise cap of three. Its exactly rechecked expected cost is `4626223/1600000`.

The rational dual gives a lower bound of `2.891389374997` (rounded down); the feasible upper cost is `4626223/1600000`, with bracket width less than `3e-12`. A separate verifier checks the dual without an optimizer and independently evaluates the recovered branch policies and their mixture in the full causal game. The unrestricted adaptive oracle supplies a feasible cost `461083/160000`, so its advantage over this entire registered lottery class is at least `0.009620624997`.

Allowing full action control, including rollback and re-promotion, does not improve on the earlier terminal-test cohort lottery in this cell. This class still excludes other randomized calendars and label-contingent acquisition, so it is a finite comparison only. The exact equality with the fixed-cohort construction also suggests the gap here is caused by contingent acquisition timing rather than rollback value, but a formal attribution would require an action-matched adaptive acquisition ablation. No novelty or efficacy gate is passed.
