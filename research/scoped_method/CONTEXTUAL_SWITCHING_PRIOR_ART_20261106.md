# Context-aware switching route: prior-art and data boundary

**Status:** read-only research triage; no experiment or holdout opened. This is a novelty screen for the next possible Failure Atlas route, not a claim that any candidate works.

## Existing methods that constrain the claim

1. Dann, Gentile, and Pacchiano, [Data-Driven Online Model Selection With Regret Guarantees](https://proceedings.mlr.press/v238/dann24a.html), AISTATS 2024, studies online selection among a pool of base learners in stochastic environments with bandit feedback. Generic context-conditioned selection among model recommendations is therefore established prior art.
2. [Understanding the Role of Feedback in Online Learning with Switching Costs](https://arxiv.org/abs/2306.09588) analyzes observation budgets jointly with switching costs and gives minimax characterizations for bandit, full, and flexible feedback. Budget-plus-switching-cost accounting alone is not a novelty boundary.
3. [Smoothed Online Convex Optimization with Delayed Feedback](https://ijcai.org/proceedings/2025/758) analyzes delayed feedback with switching cost and a dynamic-regret guarantee. A generic delayed-feedback selector with an explicit switch penalty is also known.

These papers do not directly match the ShiftLab contract: two frozen classifiers, one paid delayed label reveals both models' losses, a policy must account for per-deployment switching expenditure, and the principal target is false-promotion risk under a conditional null. Their results are regret guarantees in online-selection/optimization settings, not anytime probability-of-false-promotion guarantees for a paired deployment monitor. That mismatch leaves a specific comparison question, not a novelty claim: can an applicable published selector or its direct adaptation exploit a predecision context while retaining calibrated paired-decision safety under the ShiftLab information and budget contract?

## Data boundary from current repository audits

- The reversal generator's target/adverse pair has no pre-800 context signal; its histories are identical through event 799. The context-aware idea cannot be evaluated as a causal predictor of reversal duration on this loss-only simulator.
- The prior Wild-Time feasibility audit finds HuffPost and arXiv can support chronological loss replay, but their published metadata does not establish authentic label-release chronology. HuffPost has already been opened; arXiv remains locked. Neither should be represented as a genuine delayed-feedback confirmation without source-side release evidence.
- The prior dataset inventory marks Criteo Attribution as a relative-clock replay with unverified publisher release times. Criteo's click target is immediate only under an imposed contract, while conversion uses a 30-day maturity window; neither supplies verified point-in-time release logs for this deployment claim.
- NOAA hourly precipitation's current repository audit found no eligible model pair with the required disagreement/headroom, and the archive is not a point-in-time prediction/label-release log. It is not a ready confirmation source.

## Gate before any new candidate or holdout

A context-aware candidate is worth implementation only if all of these are identified prospectively:

1. a covariate available before the deployment action that predicts persistence or model-specific competence;
2. a frozen pair of models whose predictions and train cutoffs can be reconstructed without leakage;
3. a target and release clock, with any imposed delay explicitly called simulated feedback;
4. a comparator that implements the closest published contextual online-selection method under the same paired observation budget and switching-cost contract;
5. a frozen development region and statistic that separate gains from the context signal from gains due only to a standard selector or oracle information.

The smallest next action is a targeted audit of one untouched chronological source's raw schema and source-side timestamp/label provenance, without loading its locked target labels. If it lacks a deploy-time context signal or a defensible label contract, close this route before implementing another wrapper.
