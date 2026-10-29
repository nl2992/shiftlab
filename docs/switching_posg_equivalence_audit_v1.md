# Exact-game equivalence audit for budgeted delayed switching

**Date:** 2026-10-28. **Status:** primary-source audit; confirms a generic game-theoretic
representation, not a novel method or an unresolved positive novelty claim.

## Question

Does the exact finite-horizon acquisition-and-switching problem used in the recent oracle
comparisons escape established robust partially observed control and sequential sensing, or is
the sequence-form LP simply a generic solver for a constrained stochastic game?

## Contract to represent

The learner chooses requests and deployed actions using only released paired labels and its public
history. Requests reserve one unit of a pathwise budget immediately; labels release at their
declared times (the current registered cell uses a fixed delay). The alternative-model objective
is expected cumulative decision loss plus query and deployment-switch charges under a known HMM
label law. A separate null player chooses each queried binary label's conditional success
probability in `[0, 1/2]` after seeing the full event history, including labels that are still
pending for the learner. The safety payoff is the indicator of at least one promotion. Thus the
learner's safety constraint is a worst-case reachability constraint, not a posterior probability
under the economic HMM. Those two probability models must remain separate.

## Exact representation and limitation

For a finite horizon, finite action/label alphabet, bounded integer delay and finite budget, this
is a finite extensive-form game with imperfect private monitoring: the learner's information sets
hide unreleased labels, while the null player sees the complete history. Augment the physical state
with the HMM regime (for the alternative objective), queued labels and release times, remaining
budget, deployed model, and an absorbing “promotion occurred” flag. The null's conditional label
kernel is an adversarial action. The learner maximizes expected alternative utility subject to the
upper bound on null reachability. The resulting finite realization-plan LP / constrained
partially-observable stochastic game exactly represents the registered objective; this is the
interpretation already used by the repository's small-cell sequence-form oracles.

The representation is not itself an algorithmic contribution. Full history and realization-plan
sizes grow exponentially in horizon in the generic case. A standard belief-state POMDP is not a
drop-in solver: the learner's belief under the alternative does not encode the null player's hidden
history, and a single-model chance constraint does not enforce a supremum over the causal null
strategy. Likewise, a likelihood ratio from labels released before a regime reversal is historical
evidence and cannot certify current or future benefit after reversal. A valid decomposition must
carry (i) alternative-model regime belief for economic forecasting and (ii) robust null reachability
for false-promotion control as distinct state quantities.

## Prior-source findings

1. **Robust partially observable control already includes adversarial nature and asymmetric
   information.** Rasouli and Saghafian's RPOMDP paper derives dynamic programming under
   rectangularity and connects the model to zero-sum games with imperfect private monitoring. Its
   Theorems 3–4 distinguish a perfect decision maker from an imperfect one; the latter recursion
   must account for past nature choices not observed by the decision maker. This overlaps the
   information asymmetry and adversarial-kernel structure here. It does not establish the exact
   ShiftLab result: the risk is a separate reachability constraint, and queued labels, pathwise
   request budget, HMM economic objective and repeated costed deployment actions need to be encoded
   in the state/game. That encoding is generic state augmentation, not evidence of novelty.
2. **Constrained POMDP planning already treats expected utility under a chance constraint.** RAO*
   is a finite-horizon policy-search algorithm for expected performance with execution-risk
   constraints. Its single stochastic model is not the history-adaptive worst-case conditional-null
   player above. Merely naming the constraint “false-switch risk” does not distinguish it; the
   relevant delta is the imperfect-information adversary and the dual economic/safety laws.
3. **Online adaptive acquisition with finite maximum samples and error constraints is prior art.**
   Li et al. jointly optimize sequential stopping and posterior-dependent sensor selection under
   type-I/type-II error and expected sensor-usage constraints; their finite-horizon formulation
   also imposes a maximum sample count. Their Theorem 3 establishes the Lagrange-multiplier
   characterization of the constrained optimum. This closes generic claims about online evidence
   acquisition, stopping, or a finite sample cap. It is not equivalent to our repeated-switching
   game: the hypotheses are stationary and simple, the error constraints are terminal testing
   errors, usage is constrained in expectation, observations are immediate, and deployment does
   not repeatedly reverse with economic switching costs.
4. **Delayed group-sequential testing already uses pipeline outcomes.** Hampson and Jennison
   optimize delayed-response group-sequential tests, including cost/sample-size objectives and
   response-dependent design elements. Adding delayed labels to a generic sequential test is not a
   novelty claim.
5. **Finite-horizon utility-aware sensing already couples value and acquisition.** Ferrari et al.'s
   finite-horizon sensing POMDP jointly chooses sensing, stopping and exploitation. Therefore a
   candidate based only on current posterior value, remaining horizon and query cost is also
   insufficiently distinct.

## Conclusion and next discriminating test

The audited literature closes broad ingredient claims. A follow-up exact Lagrangian reduction now
resolves the generic representation question: for each multiplier, a hidden root mode makes the
scalarized alternative-cost/null-risk game a one-sided partially observed stochastic game; see
[`switching_lagrangian_posg_reduction_v1.md`](switching_lagrangian_posg_reduction_v1.md). Strong
duality recovers the original constrained value. This does not prove that every existing solver
implements the same contract efficiently, nor does it establish a compact approximation or any
novelty. The remaining G1 boundary is specifically a proved structural compression/approximation
that improves on generic one-sided-POSG planning and the extensive-form LP. No such method is
nominated and G2–G5 remain held.

The next test is an exact reduction audit, not another small-policy-class gap: on a registered
growing family, instantiate a resource-matched baseline from (a) robust partially observable game
dynamic programming and (b) constrained sequential sensing with the same risk and request clocks.
First verify that each baseline's information sets, null observation, risk event, pending-label
queue, pathwise budget and switching charges match. If a method cannot represent one of these, mark
it an inapplicable comparator rather than a weak baseline. If the exact game reduces to the
augmented RPOMDP/POSG without a new structural theorem, pivot from “new exact controller” to a
specific scalable approximation with a certified error/risk-regret bound, or stop the novelty
hypothesis. In all cases, report post-reversal regime forecasts separately from the time-uniform
false-promotion guarantee.

## Sources inspected

- Rasouli and Saghafian, *Robust Partially Observable Markov Decision Processes*, HKS Working
  Paper RWP18-027, 2018. [Primary source](https://research.hks.harvard.edu/publications/getFile.aspx?Id=1696),
  especially Theorems 3–4 and the discussion of nature's information and imperfect monitoring.
- Santana, Thiébaux and Williams, *RAO*: an Algorithm for Chance-Constrained POMDPs, AAAI 2016.
  [MIT publication record](https://dspace.mit.edu/entities/publication/839ffa98-84e4-4d87-8b3d-1499a1f5cdcb).
- Li, Li, Wang and Liu, *Sequential Hypothesis Test with Online Usage-Constrained Sensor
  Selection*, arXiv:1601.06447. [Primary source](https://arxiv.org/abs/1601.06447), Sections II–III,
  Theorems 1 and 3.
- Hampson and Jennison, *Group Sequential Tests for Delayed Responses*, JRSS B 75(1), 2013.
  [Primary journal record](https://academic.oup.com/jrsssb/article-abstract/75/1/3/7075424),
  [author manuscript](https://people.bath.ac.uk/mascj/papers/HampsonJennison_2.pdf).
- Ferrari, Zhao and Scaglione, *Utility Maximizing Sequential Sensing Over a Finite Horizon*,
  arXiv:1705.05960. [Primary source](https://arxiv.org/abs/1705.05960).

Source access note: RAO* was audited through the MIT record/abstract in this pass, not its full
proof. This limits theorem-equivalence claims; the exact stochastic-game comparison remains
unresolved rather than passed.
