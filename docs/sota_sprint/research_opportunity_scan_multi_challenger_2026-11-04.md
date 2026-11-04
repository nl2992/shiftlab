# Research direction correction and finite-cell theory frontier

**Status:** correction to the previous continuation scan; the multi-challenger direction and the
finite-cell C1-E query-timing mechanism are closed. No new algorithm or novelty claim is established
by this note.

## Correction: do not reopen multi-challenger shared-label acquisition

The previous version of this scan incorrectly nominated sequential replacement from a fixed model
library as the next research direction. The repository had already screened this in Lane B Phase E
and exited it. The Phase E record shows that disagreement-gated shared-label querying is covered by
IWAL / Model Picker; alpha-spending and e-BH handle multiplicity; and IWAL's pairwise rule covers
re-baselining among live candidates. The proposed covering-number gain was judged an elementary
chaining composition with at most a logarithmic-factor benefit. See [`LANE_CONTROL.md`](../lane_b_burst_allocation/LANE_CONTROL.md)
and [`E0b_chaining_search.md`](../lane_b_burst_allocation/E0b_chaining_search.md).

The feasibility lemma from the previous scan also contained a statistical error: a mixture
e-process threshold under a global null does not control false selection of a null challenger when
another challenger is genuinely better. The candidate-specific thresholds noted later in that
scan would address that multiplicity issue, but they do not restore novelty. Do not implement or
run the multi-challenger proposal from the superseded scan.

## Candidate considered at the time of this scan (subsequently closed)

The remaining theory route recorded after the C1/C2 empirical stop is C1-E: a persistence-aware
query policy for a finite-state HMM that may concentrate a fixed query budget in states where the
labels distinguish a favorable model from an unfavorable model. The proposed measurable outcome is
**label budget to a valid promotion by a specified wall-clock deadline**, under the model-conditional
likelihood-ratio gate, compared with fixed calendars and the best belief-state sensing policy.
This is a candidate analysis question, not a method result. The C1/C2 exploratory methods lost their
matched economic gates; C1-E survives only as an untested theorem/prototype question. See the
[theory targets](../switching_theory_targets_c1_c2_v1.md), [C1 proof record](../switching_c1_upper_bound_proofs_v1.md),
and [C1 source audit](../switching_c1_source_theorem_audit_v1.md).

The closest source is Kapoor and Nair, [*MDPs with a State Sensing Cost*](https://proceedings.mlr.press/v300/kapoor26a.html).
It formulates belief-dependent sensing as an expected discounted-cost MDP with an expanded state
and derives policy-gap bounds, but its source contract has no fixed-delay label-release mechanism,
pathwise total label cap, anytime false-promotion event, or promotion-sample-complexity rate. This
leaves a contract mismatch, not a novelty conclusion. Existing C1 audits already identify the
belief-sensing policy as a mandatory comparator.

## Concrete next gate

Before coding a policy or running another large grid, close the exact comparison target:

1. Use the two-state dynamics-only family in [`switching_c1_upper_bound_proofs_v1.md`](../switching_c1_upper_bound_proofs_v1.md),
   where one-step stationary label marginals coincide but transitions differ. This avoids a free
   covariate revealing the informative state and keeps the label channel genuinely hidden.
2. Fix a label-query budget `B`, fixed delay `d`, horizon `T`, confidence level `alpha`, and a target
   power/deadline `(1-gamma, W)`. Compare: the best fixed calendar; the best fixed-calendar burst
   schedule; a belief-dependent burst policy; and the exact finite-horizon belief-state DP with the
   likelihood-ratio gate. Report both budget use and wall-clock detection/promotion time.
3. State the source-backed lower bound using the same HMM and query contract. The exact
   belief-state sensing DP is an oracle comparator, not a policy the candidate can beat. A candidate
   policy must show a certified gap to that oracle and a meaningful sample-complexity improvement
   over fixed calendars; the theorem must explain why the latter improvement is not just the
   routine solution of the belief-MDP. A win over calendars alone is insufficient because it may
   merely show that adaptive sensing is useful, which is already established.
4. Preserve the fixed-delay, order-preserving release contract. Do not claim validity for
   outcome-dependent or arbitrarily reordered releases. Keep future utility after reversal outside
   the claim unless a persistence assumption is made explicit.

**Advance rule:** continue only if an exact small instance confirms a nonzero advantage over the
best fixed-calendar/burst schedule, while a tractable policy has a certified performance gap to
the exact sensing DP, and a source audit identifies a non-compositional rate result under the
hard-cap/delay/anytime-risk contract. Otherwise close C1-E and return to the project-level pivot
search. No large empirical sweep or confirmation is authorized by this note.

## Exact screen and prior-art disposition — 2026-11-08

The frozen exact screen is complete; see [protocol](switching_c1e_information_dp_protocol_v1.md)
and [results](switching_c1e_information_dp_results_v1.md). The adaptive belief-state optimum is
`0.0527964` nats against `0.0508064` for the best fixed calendar, a `3.92%` gain in one cell; the
best contiguous burst scores `0.0472589`. This establishes a small calendar gap but no tractable
policy with a certified oracle gap and no rate result beyond the established adaptive-sensing
formulation.

The source check found that finite-state HMM sensor scheduling by stochastic dynamic programming
is established prior work ([Evans and Krishnamurthy, 2001](https://doi.org/10.1080/00207170110089752));
adaptive active hypothesis testing is also established ([Nitinawarat, Atia, and Veeravalli,
2013](https://arxiv.org/abs/1203.4626)), as is active quickest detection under sampling control
([Xu and Mei, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10462384/)). These sources do not by
themselves settle every hard-cap, delay, and promotion-risk detail, but the current screen has not
isolated a non-compositional theorem contribution there. **Close C1-E as a method lead**; retain the
exact calculation as a negative/diagnostic result. Do not spend a larger simulation budget on this
cell or describe the calendar gap as novelty.

## Current project-level direction

No empirical method lead in the current B3+/scout/C1-E set has passed a source-matched SOTA gate.
The strongest remaining usable evidence is narrower: P7s reduces paid labels on three audited real
streams, while the matched Cao-style development comparison shows a reversal cost and delay loss.
Recent prior art makes the broad space narrower still: [Cao (2026)](https://arxiv.org/abs/2611.00576)
proves a first-order delay lower bound for label-history-only risk monitoring and analyzes free-
covariate triggers; [Drift-to-Action Controllers, ICLR CAO Workshop 2026](https://openreview.net/pdf?id=tcUgT2jE5W)
combines delayed active risk certificates with a drift-belief controller and costed interventions.
Neither is the exact paired fixed-model replacement contract, but they rule out broad novelty claims
for budgeted drift monitoring, risk certificates, or cost-aware intervention control.

The direct model-governance literature also includes Digalakis Jr. et al., [*The Challenger*
(2026)](https://arxiv.org/html/2512.18390), which already treats switch/discard/continue economics,
learning-curve timing, and oracle-relative regret for a growing challenger. Its full-feature samples
arrive and the challenger is retrained at decision epochs; it does not cover selective delayed labels
and an anytime paired monitor for two frozen models. This narrows, but does not by itself validate,
the project distinction.

The next direction is therefore a **real-data and estimand audit before new algorithm work**:
identify one deployment stream with event timestamps, outcome release timestamps, two frozen model
losses, query price, replacement price, and a hard label cap; then state a population-level estimand
and matched baseline that are not already covered by the Cao/Drift2Act controls. If no such stream
and contract can be assembled, the evidence package cannot support an empirical SOTA improvement;
return to a source-level theorem search instead of running another synthetic variant sweep.

The Criteo Attribution dataset is a possible first feasibility candidate, not a ready-made valid
trace: its publisher documents timestamped impressions, conversions, conversion timestamps, and a
30-day conversion window, but no actual label-ingestion timestamps. A replay would have to derive
positive release at conversion time and negative release at window maturity. Its transformed price
fields are not real annotation or switching prices, and user-level repeated records require
cluster-aware analysis. The full local structural audit passed timestamp ordering and 30-day
positive-delay checks, but found 370,386 repeated positive conversion-ID rows. A separate maturity
audit finds that only 544,424 of 16,468,027 labels (3.31%) mature before the final impression under
the 30-day rule. This leaves too little feedback for an informative within-stream switching
comparison, so close this dataset as a method-validation lead; retain it only for retrospective
prediction or explicitly extended-follow-up stress tests. This is consistent with delayed-conversion
work on label correction, elapsed-time sampling, and model-training freshness, which does not itself
establish paired fixed-model promotion under an anytime risk contract ([Yang et al., AAAI 2021](https://ojs.aaai.org/index.php/AAAI/article/view/16587)). See the
[structural feasibility report](criteo_delayed_outcome_feasibility_2026-11-08.md),
[maturity audit protocol](../../papers/shiftguard_unified/criteo_maturity_audit_protocol.md), and
[publisher dataset card](https://huggingface.co/datasets/criteo/criteo-attribution-dataset).

## Finite-cell power update — 2026-11-04

The four-query C1-E timing mechanism was checked against actual anytime first-promotion power in
[`switching_c1e_anytime_power_results_v1.md`](switching_c1e_anytime_power_results_v1.md). Across
the fixed alpha panel `{0.05, 0.10, 0.20}`, both the exact adaptive policy and the strongest fixed
calendar/burst had zero power. More strongly, the maximum LR over every four-query calendar and
outcome string is exactly `386611/245941`, below the smallest registered crossing threshold 5;
this proves zero power for every adaptive policy in that finite cell. It also shows the earlier
3.92% KL gain does not improve the promotion decision. Close this cell and do not enlarge it after
seeing the result.

**Decision after the real-data screen:** Criteo Attribution and CriteoPrivateAds do not meet the
observed-release and outcome-utility contract, and CRSP is already exposed with retrospective
clocks. Do not run another model-performance replay on these sources as if it were confirmation.
The remaining admissible work is (i) obtain an untouched stream with auditable outcome-release
times and a matched decision-cost definition, or (ii) make a source-level theorem search for a
non-compositional result under the exact paired fixed-model, delayed-feedback, hard-cap, promotion
and rollback contract. Any candidate theorem must beat the finite-state sensing and delayed
anytime-inference comparators already catalogued above before new algorithm implementation begins.
