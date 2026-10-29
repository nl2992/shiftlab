# Episode-wise safe composition against the causal-game reference

**Date:** 2026-10-28. **Status:** exact finite comparator screen; no novelty claim.

## Contract and policies

Use T=6, pathwise query budget B=3 (including pending requests), fixed label delay d=2, alpha=1/10, query price c=1/100 and switch charge k=1/10. The known alternative is a two-state HMM with symmetric transitions 1/4, emissions P(Y=1|S=0)=1/50 and P(Y=1|S=1)=49/50, and prior P(S0=1)=1/2. Queried labels identify losses Y_t and 1-Y_t; unqueried labels are hidden. The safety null is the causal conditional constraint P(Y_t=1 | full past, current choices)<=1/2. The same HMM forecast model is available to both methods for expected-cost evaluation and control, but it is not used as a safety premise.

The implementable composition enumerates every fixed calendar subset of at most three eligible query events (events 1..4, so every selected label can arrive by T). While action 1 is installed, it requests at scheduled events to update the HMM forecast and rolls back if the remaining-horizon predictive gain of action 1 is below -k. In each inactive episode, the first scheduled opportunity activates a one-label positive-only promotion test with probability 2 alpha_j; a promotion additionally requires positive remaining-horizon HMM forecast net of k. Fresh episodes use alpha_j allocated by geometric spending, equal spending over B+1 possible episodes, or all alpha to the first episode. The geometric rule uses alpha_j=alpha/2^(j+1), so sum_j alpha_j=alpha. In episode j, the test's false-promotion probability is at most (2 alpha_j)(1/2)=alpha_j for every causal null, conditional on the episode history. Each episode can promote only after its randomized request and positive label; summing conditional risks gives the global bound. Query count is pathwise at most the calendar size, hence at most B. The working-model forecast controls only economic actions and rollback; it does not certify current benefit or enter the null-risk proof.

The comparator is the finite causal-game sequence-form LP from `causal_switching_game.py`, with the same action/query information, pathwise cap, delay, charges, HMM alternative cost and worst causal-null risk constraint. Its HiGHS result is a numerical solver reference; the recovered policy is exactly re-evaluated for risk and expected cost, but there is no rational dual certificate, so it is not described as a certified optimum.

## Result

The script `scripts/compare_switching_episode_composition.py` evaluated all 15 fixed calendars under each of the three spending rules using exact rational forward expected-cost and causal-null recursions. The best calendar was (1,3,4) in all cases.

- Geometric spending: cost 2.979918448; worst null risk 1/20; expected queries 1/5.
- Equal spending: cost 2.989959224; worst null risk 1/40; expected queries 1/10.
- Frontloaded spending: cost 2.959836896; worst null risk 1/10; expected queries 2/5.
- Continue/no switch: cost 3.
- Recovered unrestricted causal-game policy: cost 2.955693376; risk 1/10; expected queries 1.

The best screened composition is 0.00414352 cost units above the recovered LP policy (exact difference 25897/6250000), about 0.14% of the total cost. This small instance gives little economic headroom to a proposed acquisition improvement over a carefully chosen simple composition. Because the LP lacks a dual certificate and the calendar/spending class is narrow, this is neither a certified approximation ratio nor evidence that no larger gain exists under other recurrent models. All methods are evaluated in the same HMM alternative and causal-null contract; current-regime forecast and global-null risk remain separate.

Reproduce with `python scripts/compare_switching_episode_composition.py` from the repository root with `PYTHONPATH=src`. Full per-calendar metrics and script/source hashes are in `outputs/switching_episode_composition_v1/results.json`. This is a finite development comparison, not matched synthetic efficacy evidence, an independent proof review, or real-data evaluation. The fixed-calendar episode composition is established-baseline material, not the proposed method.

## Decision

The screened composition uses the entire null-risk allowance efficiently by frontloading it, and nearly matches the recovered robust planner in this registered cell. A new method must beat this stronger composition (and other scalable baselines) on a predeclared recurrent family, with a theorem-level risk/performance advantage. The result narrows rather than clears G1; no efficacy campaign is justified yet.
