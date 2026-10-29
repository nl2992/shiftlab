# Robust sequential testing for Markov processes: prior-art boundary

**Date:** 2026-10-29. **Status:** primary-source theorem-scope audit; closes generic Markov
sequential testing with distributional uncertainty, not the full budgeted switching objective.

## Primary source inspected

Fauß, Zoubir and Poor, “Minimax Optimal Sequential Hypothesis Tests for Markov Processes,”
*Annals of Statistics* 48(5), 2020, [arXiv:1811.04286](https://arxiv.org/abs/1811.04286).
I inspected Sections 2–6 of the full arXiv HTML, especially the uncertainty model, formulations
(2.16)–(2.17), Corollary 1, Theorems 5–8 and the corresponding least-favorable-distribution
recursions. Their processes have a time-homogeneous Markov sufficient statistic common to all
hypotheses. Conditional observation laws may vary within hypothesis-specific uncertainty sets at
each Markov state. They characterize optimal sequential stopping/decision rules and sufficient
conditions under which an adaptive least-favorable Markov law makes a test minimax optimal.

The objective is a weighted expected run length plus hypothesis-error probabilities, or worst-case
expected run length under bounds on error probabilities. The exact optimal-test statistic includes
likelihood ratios and the Markov sufficient statistic; the stopping rule compares a terminal
decision cost with expected continuation cost. This is direct prior art for robust Markovian
sequential testing and its dynamic-programming/statistic design. The audit is not an independent
verification of every proof condition.

## Relation to ShiftLab

This closes generic claims that a contribution arises from combining a recurrent HMM, adaptive
sampling/stopping, a robust conditional observation family, and a likelihood-ratio state. In the
first-promotion phase, ShiftLab also has a robust stopping problem whose continuation value is
computed under an economic HMM; that coupling needs a result beyond a standard optimal stopping
boundary attached to a known-model continuation value.

The source does not directly solve ShiftLab's full contract. It treats observed samples with an
immediate filtration, time-homogeneous stopping rules, and expected run length/error criteria. It
does not impose a pathwise request budget reserved at acquisition, a delayed queue whose outcomes
are visible to the null but hidden from the learner, a separate known alternative law scoring
recurrent deployment and rollback costs, or a single global probability-of-any-promotion
constraint. A finite-horizon delay/budget augmentation may be representable, but generic state
augmentation is not a novelty argument. The source's error-probability formulation and
least-favorable laws must not be silently equated with ShiftLab's exact causal-null event.

## Decision

Reject “Markovian robust sequential testing plus economic switching” as a contribution by itself.
The unresolved target remains a source-audited computational or decision-theoretic advantage for
the delayed, pathwise-budgeted, two-law continuation problem, with exact causal-null risk preserved
and objective/risk guarantees separated. No algorithm, efficacy result or real-data claim passes
G1 from this audit. The economic HMM's current-regime forecast remains distinct from historical
promotion evidence after a reversal.
