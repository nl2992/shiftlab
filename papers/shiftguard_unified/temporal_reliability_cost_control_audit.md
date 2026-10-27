# Temporal reliability and cost-controlled intervention: source audit

**Audit date:** 2026-10-26  
**Source:** Naimur Rahman and Naazreen Tabassum, *Modeling and Controlling Deployment Reliability under Temporal Distribution Shift*, arXiv:2604.02351v1 (submitted 1 March 2026; preprint). [Primary source](https://arxiv.org/abs/2604.02351)

## What the paper studies

The paper treats deployment as nine chronological annual windows (2010–2018) on a 1.35M-row LendingClub credit-risk dataset. It defines a reliability state from AUC and ECE, summarizes year-to-year changes through L1 and downside-volatility metrics, and compares static, periodic recalibration, rolling retraining, and drift/reliability-triggered intervention. Its action-cost accounting assigns 0 units to no-op, 1 to recalibration, 5 to retraining, and 6 to both. The reported drift-triggered policy uses one retrain and two recalibrations (12 units) versus 9 retrains (45 units) for rolling retraining, while reporting a smoother overall reliability trajectory.

The source text is internally inconsistent about threshold provenance: §5.1 says all pre-2010 data construct drift and reliability thresholds, while §4.4/§5.6 describe reliability quantiles from static-deployment performance and drift-threshold candidates from the 2010–2018 evaluation horizon. Table 2 also lists one DTRC threshold pair, while the MORC-knee narrative reports a different pair. These differences need clarification or a code/version match before a faithful reproduction. The operational sequence uses current-window labels to measure reliability and chooses an update for a subsequent window. It assumes the annual outcome labels are available at the decision point; the paper identifies label delay/censoring as a limitation. The MORC policy family is swept using drift values observed across the full 2010–2018 horizon, and its knee is chosen on the resulting cost–volatility frontier. Thus, the selected frontier/knee is a retrospective policy-selection result on that horizon, not an independent prospective confirmation. Uncertainty is based on nine annual blocks, which the paper itself says is limited.

## Relationship to ShiftGuard

This is a close Q3 scope comparator for **drift-triggered intervention, multi-metric reliability trajectories, and explicit cost–stability trade-offs under temporal shift**. It makes a generic claim that cost-aware, state-dependent updates under temporal shift are new untenable. The result also reinforces that update frequency need not improve every reliability endpoint.

It is not a drop-in numerical baseline for the current ShiftGuard comparisons. Its objective is predictive reliability volatility (AUC/ECE) with a fixed, imposed update-cost scale. It does not test paired downstream decision harm, anytime-valid evidence, candidate discovery/certification, selective label budgets, or a composed monitor–certify–intervene system. Its annual fully observed label batches, single credit-risk history, and retrospective MORC frontier differ from ShiftGuard's event streams, assumed delayed feedback, EIA regression objective, and logged-bandit candidate-value task. No common estimand or resource unit has been established.

## Decision

- Include it in related work and in the Q3 fidelity/scope matrix as an **arXiv preprint, not a reproduced method**.
- Do not claim novelty for cost-aware or drift-triggered intervention, update-cost frontiers, or the general idea of adapting less often when reliability signals permit.
- Do not rank its numerical results against ShiftGuard's EIA, synthetic, or logged-bandit metrics.
- A quantitative comparison would need a supported binary time-indexed dataset, a strictly past-only threshold-selection/calibration procedure, independently held-out later periods, and matched label/update-cost definitions. The currently audited ShiftGuard tasks do not provide that complete contract.
- The preprint does not by itself eliminate a narrower contribution on sequential paired decision-harm monitoring or adaptive candidate certification, but any such contribution must be demonstrated against the direct statistical comparators already listed in the fidelity matrix.

## Evidence checked

The arXiv full text was inspected for problem definition, action timing, threshold selection, cost weights, results, and stated limitations. It reports annual labeled outcomes used for the current-window reliability state and next-window updates; the MORC threshold candidates and cost–volatility knee are derived from the same nine-year deployment horizon. No author-code reproduction was attempted.
