# Bayesian online resource allocation: novelty boundary

**Date:** 2026-10-29. **Status:** primary-source scope audit; no new method claim.

## Source and inspected result

Ao, Chen, Simchi-Levi and Zhu, “Online Resource Allocation with Average Budget
Constraints,” arXiv:2402.11425 (2024; subsequently submitted to *Operations Research*). I
inspected the full arXiv PDF, including its abstract, model, contribution summary, and the
application to online false discovery rate control. Its online knapsack model makes an
irrevocable accept/reject decision for each arriving request. Accepted requests consume a cost
resource, and the constraint bounds running average cost; the available budget is replenished
exogenously and randomly. The objective is cumulative reward. The paper gives an O(sqrt(T)) regret
policy for general arrival distributions and a multilevel logarithmic-buffer policy with O(log^2(T))
regret for discrete arrival distributions, with sharper rates in non-degenerate cases. In the FDR
application, the decision accepts a candidate for secondary evaluation, reward is the discovery or
evaluation value, and cost is posterior probability of inefficiency.

The resource called a “budget” here is not a hard cap on the number of queried labels. It is a
running-average cost allowance with random exogenous replenishment. Decisions concern one-time
acceptance of arriving requests, rather than repeated reversible deployment of a model. The paper
does not model label-release delay, a shared pending-query pool, or ShiftLab's history-adaptive
causal-null promotion event.

## Consequence for ShiftLab

This closes a broad novelty claim around online allocation of an economic/error budget to candidate
model evaluations, and it supplies a useful reward-cost allocation baseline. A comparison must
state explicitly whether the resource is a query count, an alpha/error allowance, or average
posterior error cost; these are not interchangeable constraints. For the ShiftLab contract, adapt
the strongest applicable allocation policy to the same hard total query cap and feedback chronology,
and separately enforce the same global any-false-promotion guarantee. Do not infer that the paper's
regret theorem transfers to those changes.

The remaining distinction to investigate is the joint value of spending a scarce, delayed label
query and making a reversible deployment decision whose value can change after a regime reversal,
under one global false-promotion event. These differences identify proof obligations and a fair
comparator; they do not establish novelty. G1 remains open, and G2–G5 remain held.

Promotion-risk validity remains separate from current-regime value. Evidence that an update was
beneficial earlier does not certify that it remains beneficial following a reversal. Current-value
decisions need fresh evidence or an explicit persistence assumption.

## Provenance

- Official source: [arXiv record](https://arxiv.org/abs/2402.11425) and
  [full PDF](https://arxiv.org/pdf/2402.11425).
- Cached PDF: `outputs/switching_source_audit_v1/ao_etal_bayesian_online_multiple_testing_2024.pdf`.
- SHA256: `D5B15A5359179877E43032598C2FE53DDD0E1D41D268956D051A3FDD07028AFC`
  (935,264 bytes).
- Selected theorem-scope and application audit, not an independent reproof.
