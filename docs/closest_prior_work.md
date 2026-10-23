# Closest prior work for ShiftLab's three tracks

This is an initial primary-source comparison, not a completed novelty review. The benchmark below
is deliberately baseline work. Before a paper claim, read the full papers, appendices, corrections,
code and exact assumptions, then compare the same estimand under the same feedback and adaptation
regime.

| Work | What it already addresses | What ShiftLab must not claim without a sharper gap |
|---|---|---|
| [Podkopaev & Ramdas, *Tracking the risk of a deployed model and detecting harmful distribution shifts* (ICLR 2022)](https://arxiv.org/abs/2110.06177) | Sequentially tracks a fixed deployed model's predictive risk increase against a source baseline using time-uniform inference; its stated settings include labels revealed after prediction and delayed batches. | “Anytime-valid predictive-risk monitoring under delayed labels” is already established. Compare exact loss/null and the proposed paired policy-cost estimand; do not treat the latter distinction alone as novelty until theorem scope and later work are checked. |
| [WATCH, *Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales* (ICML 2025)](https://proceedings.mlr.press/v267/prinster25a.html) | Weighted-conformal martingale monitoring of deployment shifts, with adaptation to covariate shift and sequential alarms. Strong overlap for shift and deployment monitoring. | Do not imply a generic conformal/e-process detector is new. Audit its target, shift assumptions, adaptive weighting, feedback access and harm definition against our exact decision-cost null. |
| [Zhang et al., *Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful Distribution Shifts* (ICML 2026)](https://proceedings.mlr.press/v306/zhang26g.html) | Combines synthetic/pseudo labels and a small true-label sample to construct anytime-valid lower bounds on running predictive risk; the paper states finite-sample type-I guarantees for its threshold rule. | Sparse-label predictive-risk monitoring is directly covered. The paper's stated result does not by itself establish our paired deployed-versus-reference action-cost guarantee; verify its complete formulation before making that distinction a contribution. |
| [Schirmer et al., *Monitoring Risks in Test-Time Adaptation* (NeurIPS 2025)](https://proceedings.neurips.cc/paper_files/paper/2025/hash/746960ad49ddb47248970a0e1404230c-Abstract-Conference.html) | Extends sequential confidence-sequence risk monitoring to updated predictors under test-time adaptation with no test labels. | Monitoring risk during TTA is already an active area. Paper 1 cannot claim general adaptive-predictor risk monitoring as new. Compare what loss proxy, update protocol, and action comparator are actually covered. |
| [Amoukou et al., *Sequential Harmful Shift Detection Without Labels* (2024 preprint)](https://arxiv.org/abs/2412.12910) | Replaces unavailable labels with a learned error-estimator proxy and proposes sequential mean/quantile tests; the paper states guarantees under assumptions on the proxy statistic. | Label-free harmful-shift detection is not an open blank. Any new claim must state proxy calibration/shift assumptions and show a gap beyond the existing method. |
| [Jang et al., *Sequential Predictive Two-Sample and Independence Testing* (ICML 2022)](https://proceedings.mlr.press/v162/jang22a.html) | Sequential two-sample testing for changes in distributions, providing a relevant reference for discrepancy monitoring. | Detecting that `P_t` differs from `P_0` does not show model degradation or policy harm. Use it as a discrepancy baseline, not evidence that harm was detected. |
| [Off-Policy Confidence Sequences (ICML 2021)](https://proceedings.mlr.press/v139/karampatziakis21a.html) | Time-uniform, nonparametric confidence bounds for contextual-bandit policy evaluation; the paper explicitly demonstrates gated production deployment/upgrades. | A policy gate based on logged bandit feedback and valid importance weights is already established. ShiftLab cannot claim a generic statistically certified candidate promotion gate without a substantially different estimand or feedback setting. |
| [Conformal Policy Control (ICML 2026)](https://proceedings.mlr.press/v306/prinster26a.html) | Uses a safe reference policy as a probabilistic regulator for a new policy and calibrates how much it can act under a declared risk tolerance, with finite-sample guarantees for bounded losses. | “Use a safe fallback to constrain a candidate policy under risk tolerance” is directly addressed. Test-time distribution change, net deployment cost, selection among many candidates, and rollback must be compared precisely before a narrower claim. |
| [Multiple-policy High-confidence Policy Evaluation (AISTATS 2023)](https://proceedings.mlr.press/v206/dann23a.html) | Gives high-confidence estimates for a fixed set of policies and sample-efficient evaluation using policy overlap. | Multiplicity across a prespecified candidate set and fixed-accuracy policy certification have prior solutions. It is not by itself a time-uniform, shifting-stream deployment gate. |
| [RCCDA: Adaptive Model Updates under a Constrained Resource Budget (NeurIPS 2025)](https://proceedings.nips.cc/paper_files/paper/2025/hash/e3d1b6d954a204267fd334cbaf9cd4af-Abstract-Conference.html) | Directly studies update scheduling under concept drift with a resource budget; its abstract reports update-frequency/cost guarantees using past losses and a threshold, with a Lyapunov drift-plus-penalty policy. | Budgeted model-update scheduling under drift is directly covered. Paper 3 needs to identify a distinct resource/decision tradeoff, such as joint label-query and intervention allocation under decision harm, and beat this class of update controllers. |
| [Zliobaite et al., *Active Learning on Data Streams* (2011)](https://proceedings.mlr.press/v17/zliobaite11a.html) | Online instance-level label requests under an explicit label budget while adapting to concept drift; explicitly notes that a fixed query region can miss changes elsewhere. | Online active labeling and drift adaptation are established. A new budgeted active-adaptation claim needs more than query heuristics or drift-triggered label spending. |
| [Korycki & Krawczyk, *Mining Drifting Data Streams on a Budget* (2021)](https://arxiv.org/abs/2112.11019) | Combines active labeling with self-labeling for drifting streams under limited labels. | Combining pseudo-labeling and active querying under drift is already explored; ShiftLab must show a distinct objective and guarantee. |

## Relationship to the initial implementation

The Phase 2 benchmark implements simple RBF-MMD², predictive-loss CUSUM, paired realized-cost CUSUM,
and one bounded full-feedback Hoeffding mixture e-process example. Empirical full-horizon thresholds
are calibrated from independent synthetic streams. These are transparent comparators, not a
reimplementation of the methods above and not state-of-the-art claims. In particular, the synthetic
benchmark has immediate complete labels, a fixed source rule, deterministic policies, and imposed
costs. It does not yet compare WATCH, PPRM, adaptive-predictor risk monitors, learned no-label error
estimators, or delayed/selectively observed paired feedback.

## Track-specific gap audit

1. **Anytime-valid Decision-Harm Gate:** strongest overlap is direct sequential predictive-risk
   monitoring plus methods for adaptive predictors and prediction-powered labels. Establish whether
   paired policy-cost monitoring with a predictable reference, action-dependent outcomes and actual
   feedback constraints has already been solved. The current e-process is only a bounded, full-label
   mathematical example under its stated conditional null.
2. **Statistically Certified Adaptation:** policy confidence sequences already support gated
   contextual-bandit upgrades, fixed candidate sets have high-confidence evaluation methods, and
   conformal policy control regulates a new candidate against a safe reference. A remaining gap
   would need to combine or extend these under a clearly different deployment-shift, delayed
   feedback, multiple adaptive candidates, deployment-cost, or rollback setting. Monitoring that
   an incumbent is failing alone does not certify a selected replacement's net benefit.
3. **Budgeted Active Adaptation:** stream-based active labeling, budgeted drift adaptation, and
   resource-constrained update scheduling all exist. Compare against query-by-committee/uncertainty
   and random-label baselines, self-labeling, fixed/dynamic label budgets, and update controllers.
   A potentially distinct scope is joint allocation of labels, monitoring compute, calibration,
   updates, switching and fallback under a decision-harm objective, but the combined setting needs
   a precise literature search and proof; a controller built around existing alarms is not itself a
   contribution.

No novelty conclusion is made here. This note narrows the next task: build matched baselines and
perform a theorem/assumption-level comparison before proposing new algorithms.
