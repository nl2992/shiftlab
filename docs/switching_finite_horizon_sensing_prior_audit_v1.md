# Finite-horizon utility-driven sequential sensing: prior audit

**Date:** 2026-10-28. **Status:** primary source and main theorem inspected; no novelty conclusion.

## Source and verified result

Ferrari, Zhao and Scaglione, *Utility Maximizing Sequential Sensing Over a Finite Horizon*,
arXiv:1705.05960v1 (2017), [primary preprint](https://arxiv.org/abs/1705.05960). I inspected the
full 17-page source, including its model, belief-state POMDP, Bellman recursion, Theorem 1,
threshold approximations and comparison discussion.

The paper studies a finite horizon with multiple binary hidden resources. Each resource has a
state-dependent exploitation reward or penalty; sensing costs time and a per-period cost, and only
one resource can be sensed at a time. The policy jointly chooses sensing-resource selection,
resource-specific stopping times, and the eventual exploit/discard decisions. Theorem 1 gives two
time-varying posterior thresholds for each resource, depending on remaining resources and time;
the resource-selection rule is coupled to the optimal stopping decisions. It also develops a
lower-complexity approximation because the full POMDP is generally difficult to solve.

## Novelty implication and contract delta

This is direct prior art for finite-horizon, utility-directed acquisition that prices the remaining
exploitation opportunity, together with threshold decisions and adaptive sensing-resource
selection. A rule that merely uses the remaining horizon or posterior value to choose which
candidate to query, when to stop, and whether to deploy is therefore not new.

The model uses static resource states and an immediate-sensing POMDP. It does not include a fixed
delay queue, a hard pathwise label cap with pending requests, a robust causal conditional-null
false-promotion event, or repeated reversible deployment with switching charges. Those features
leave a possible theorem target only if their interaction yields a guarantee or strict separation
beyond standard sequential sensing and robust constrained planning. No novelty follows from
listing the missing assumptions.

## Decision

Reject a generic posterior-threshold/value-of-information controller as the candidate method.
Keep the narrower question open: can delayed evidence and a pathwise finite label budget under a
causal conditional-null risk constraint yield a scalable risk-regret frontier for recurrent
reversible switching that existing sequential sensing, robust POMDP and delayed-learning
compositions do not already imply? Derive that result before implementing another controller or
running efficacy experiments.
