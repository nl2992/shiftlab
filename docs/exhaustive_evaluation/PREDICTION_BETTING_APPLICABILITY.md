# Betting on predictions: source check and applicability

2026-10-30. Previous goal turn made progress (range follow-up committed). This continuation retrieves author code, executes its finite-sample statistic and closes the unchanged-method applicability question for the current general chronological contract. It does not complete native experimental reproduction or establish novelty.

## Sources and executed check

[Tenzer, Tolochinsky and Romano, Semi-Supervised Hypothesis Testing by Betting on Predictions](https://arxiv.org/html/2605.28533), v1, Sections3.1–3.4, Proposition3.1/3.2, Corollary3.3 and Theorem3.4 inspected in primary full text. Author repository https://github.com/elad-tolo/betting_on_predictions cloned at f99e196b0087128d7ffe0291df9e68042255eae8. Vendor source/data remain ignored. Bundled data were downloaded with the repository but were not opened or analyzed; downloading them does not create fresh evaluation evidence.

The implementation sequential_tests/imputed.py uses Eq2: (M+1)K0/(K0+sum Kj). We import the actual class and execute calc_statistic_finite_sample, with an allowed proxy-only prediction algorithm and gamma=log2. One binary unlabeled observation gives scores1 or2. For M=3, enumerate all16 observed/null score combinations exactly with rational arithmetic, for observed and simulated proxy probabilities in{1/5,1/2,4/5}. This is a component/formula check, not a reproduction of the paper's fitted classifiers or simulations.

Results: zero numerical difference from the author statistic across all9 distribution pairs. When the observed and simulated distributions match, expected factor is exactly1 in each of the3 matched cases. With observed proxy probability4/5 but simulator probability1/5, expected factor is5848/4375≈1.336686. Evidence: prediction_betting_exact_check.json; reproducible script check_prediction_betting.py (retained registration-style output guard).

This is a counterexample to **unqualified transplantation with a wrong simulator**, not to the paper's theorem. Set Y independent Bernoulli(.5) in both populations while shifting X fromBernoulli(.2) toBernoulli(.8), and let the arbitrary learner predict X. Y's marginal is unchanged, but X|Y has changed, so the paper's fixed-X|Y label-shift premise is false. Similarly the fixed-X concept-shift premise is false. A general conditional-mean no-benefit null need not prevent this nuisance change. The statistic can gain expectation under that null if one incorrectly retains the old simulator. A mean factor above1 alone is not a measured rejection probability or proof of a particular alpha violation.

## Why prediction robustness is different from null robustness

The paper permits poor predictions because observed and null-simulated batches undergo the same learning/scoring procedure. Exchangeability of those batches supplies the finite-sample argument. It needs labeled/unlabeled IID batches and independent null draws, not merely a trained probability score. Source implementation get_score_of_null_datasets samples and fits M null datasets per event; those fits and source-law estimation must count in compute/source-data accounting.

Sections3.2–3.3 assume fixed X|Y for marginal-label inference or fixed X for conditional inference. These hypotheses are distinct from our bounded paired conditional-mean inequality with arbitrary nuisance/context drift and adaptively missing/delayed outcomes. A generic paired loss is not automatically a binary label with either of these shift structures. Theorem3.4 explicitly adds a total-variation discrepancy term for an approximate null law; it does not make a plug-in null simulator exact. Calibration uncertainty cannot be silently ignored.

**Disposition: EXCLUDED_UNCHANGED_NULL_AND_SAMPLING_CONTRACT** from the general same-guarantee chronological paired-cost table. This is a scope exclusion, not a loss against our method, a missing-code claim or a complete family exclusion. In restricted simulator cells with a known full null law, a null-oracle operational comparison is possible; it must be separately labeled and given identical information or shown as a privileged reference. Before adapting to real data, specify an identifiable null family, source estimation uncertainty, independent batch/release semantics and all fitting costs. No such reduction is currently established for Bike/Beijing/Gas.

The method remains relevant prior art against claiming novelty from using predictions/unlabeled observations to increase evidence. The source check resolves a precise baseline obligation; it does not show that our full switching problem is novel.

## Next work and limits

Remaining direct inventory: distinct e-detectors/classical variants, observed-Markov applicability, robust-FSC/CPOMDP synthesis mapping, and the full native-versus-adapted active-RCPS distinction. The learned-query timing/range diagnostics still motivate a bounded pacing/evidence-recovery study, but generic mixtures/pacing/resets are known ingredients. A new≥500-combination round must retain strong equally paced references and be motivated by a concrete unresolved mechanism rather than omitted assumptions in a baseline.

No efficacy claim or new combination count follows from9 exact component cases. Reserved real windows remain closed. Ruff0.17.1 and all exact assertions passed. No paid compute, external messages, deployments or subagents. Goal remains active; exhaustive evaluation and novelty validation remain incomplete.
