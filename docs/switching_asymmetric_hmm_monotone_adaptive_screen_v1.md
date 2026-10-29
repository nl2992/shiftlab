# Asymmetric recurrent-HMM screen for monotone adaptive promotion

**Date:** 2026-10-28. **Status:** exploratory recovered-policy screen; no theorem or novelty claim.

## Question and protocol

Does the no-gap observation for monotone first-promotion policies persist beyond the symmetric six-round oracle and symmetric fixed-cohort sweep? The saved script `scripts/screen_switching_asymmetric_hmm_monotone_adaptive.py` compares unrestricted and coordinatewise-monotone first-promotion sequence-form LPs on 576 small known-HMM cells. It varies four `(T,B,d)` triples, all six ordered asymmetric transition pairs from `{1/10,1/4,1/2}`, four emission/prior tuples (including asymmetric emissions and priors), three alpha values, and two query/switch cost settings. Adaptive queries, fixed delay, pathwise budget, the same causal conditional-null constraint and the same expected economic objective are preserved.

Each LP is optimized numerically; the recovered behavioral policy is rationalized and evaluated exactly by the reference game. The output records both solver objectives, exact recovered-policy costs and null risks for every cell. It reports 576/576 equal recovered costs and no positive or negative recovered-cost differences. The run is reproducible with `$env:PYTHONPATH='src;.'; python scripts/screen_switching_asymmetric_hmm_monotone_adaptive.py`; results and source hashes are in `outputs/switching_asymmetric_hmm_monotone_adaptive_v1/results.json`. Ruff and `git diff --check` passed.

## Interpretation

This is not an exact comparison of optimal values: numerical optimizer output and rationalized behavioral recovery can conceal a small optimum gap. The screen neither proves monotone optimality for recurrent HMMs nor supplies a utility or memory guarantee. The prior exact arbitrary signed-future-value counterexample in `switching_monotone_class_separation_v1.md` still rules out a universal monotone-class approximation without a structural assumption. Preserve monotonicity only as a candidate tractability restriction when independently certified; do not make it the algorithm or claim. Global causal-null promotion risk remains distinct from benefit in the current regime or future profit after reversal.

## Decision

The expanded screen does not reveal a structural separation and therefore does not advance G1/G2. Stop spending effort on a broad numerical search for a monotone gap. Next, return to the registered G1 contract: formalize the exact future-value acquisition target under an explicit persistence/drift assumption and test an explicit reduction to costed POMDP/sequential experimental design, including proof-level source checks. Continue only if that yields a nontrivial bound or counterexample beyond those methods. G3/G4 remain held.
