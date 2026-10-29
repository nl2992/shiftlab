# Monotone terminal tests under two-state HMM alternatives: exploratory screen

**Date:** 2026-10-28. **Status:** fixed-cohort structural diagnostic; not a method or efficacy study.

## Question and contract

Does restricting a terminal one-shot promotion test to coordinatewise monotone rejection probabilities lose value in a simple recurrent-regime family? Fix queries at events 1 and 2, release each after one round, decide once at the start of event 3, then hold the selected action to the horizon. The pathwise query cap is 2. For each HMM alternative, the objective coefficient on tape `y` is its exact probability times the expected remaining loss improvement after promotion minus the switch charge. The safety null is the full-history conditional constraint `P(Y_t=1 | full past, public choices) <= 1/2`. Compare all randomized terminal tests against those satisfying the four coordinatewise monotonicity inequalities. Both classes use the same query calendar, so query fees are constant and omitted.

## Screen

`scripts/screen_switching_hmm_monotone_terminal_test.py` forms the HMM tape/payoff coefficients with `Fraction` arithmetic and solves one unrestricted and one monotone LP per cell. Each LP has all eight endpoint causal-null constraints; the monotone LP adds the four Boolean-lattice cover inequalities. The registered-in-code grid includes horizons `{3,6}`, 34 positive-persistence asymmetric transition pairs from a seven-value grid with `a+b<=1`, four values each for `theta0<1/2` and `theta1>1/2`, three prior probabilities, two risk levels, and four switch charges: 26,112 cells.

The numerical run reported 11,062 cells with positive unrestricted objective and no unrestricted-minus-monotone gap above `1e-7`; the largest displayed gap was zero. The result and script hash are in `outputs/switching_hmm_monotone_terminal_test_v1/results.json`.

## Interpretation and limits

This is evidence that the monotone restriction may be harmless for this narrow fixed-cohort, single-promotion HMM slice. It is **not** an exact optimality result: HiGHS solves the LPs in floating point, the grid is finite, and no adaptive query, repeated promotion, rollback, delay greater than one, or real data is included. The broader monotone-class separation under arbitrary signed future payoffs remains valid; positive-persistence HMM assumptions are doing substantive work here.

A possible exact route is: let `c(y)=P_alt(y)*v(y)` be the terminal expected net value coefficient. If `c` is coordinatewise nondecreasing, the boundary-IID risk-constrained terminal-test LP is a fractional knapsack whose threshold solution is monotone. By the causal-null monotone-event lemma, that test has the same risk under the full causal null as under IID Bernoulli(1/2). Since every causally safe test is IID-safe, this monotone test would attain the unrestricted causal-null optimum. The current HMM grid does not verify the required monotonicity condition, and the finite-grid LP match does not prove it. Derive a checkable HMM condition or produce an exact counterexample before using this reduction in an acquisition controller.

This terminal-test theorem would be a structural subroutine, not the requested acquisition-and-switching contribution. The one-shot economic test-design literature is already close prior art. G1/G2 remain open; no efficacy or real-data gate is passed.
