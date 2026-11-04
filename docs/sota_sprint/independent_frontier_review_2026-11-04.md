# Independent research frontier review — 2026-11-04

## Git synchronization

Fetched the configured upstream with pruning. The local research branch and its upstream both resolve to
`f303d90bd40e2597f8095e95f4c44ecedaa1ea3e`; there were no remote commits to integrate. Existing local
tracked and untracked research changes were preserved.

## Result

No current method or theorem lead clears both the novelty and evidence gates. An independent lower-level
review identified the version-indexed challenger monitor as the closest candidate. Its proposed validity
argument freezes a challenger at activation, uses fresh post-activation paired outcomes, assigns summable
error levels across versions, and applies a version-wise test supermartingale with Ville's inequality.
That is a useful contract, but the proof is standard composition; no non-compositional rate or decision
advantage has been established. The corrected five-stream evaluation loses to version-aware Model Picker
on every exposed stream, and the dual-monitor stress result does not rescue it.

The source search further narrows the space. Karimi et al. already study active online identification among
pre-trained classifiers with high-probability guarantees ([AISTATS 2021](https://proceedings.mlr.press/v130/reza-karimi21a.html)).
Koning and van Meer study continuation/sequentialization of valid tests ([2025 preprint](https://arxiv.org/abs/2501.03982)).
*The Challenger* analyzes costed retraining and model replacement ([arXiv:2512.18390](https://arxiv.org/abs/2512.18390)).
ADOWIP studies delayed online adaptation with sealed feedback queues and exact update budgets, with regret
for its accepted-update subproblem ([arXiv:2606.25068](https://arxiv.org/abs/2606.25068)). These works have
different estimands and do not jointly solve ShiftLab's fixed-pair promotion problem, but that difference
alone is not a contribution.

An additional November 2026 source check closes two broader framings. RAR specifies a four-action
continue/retrain/alert/rollback state machine, delayed-label gates, and a two-stage canary with typed
rollback holds; its own results report heterogeneous performance and no uniform dominance
([Sadeghian et al., arXiv:2611.02251](https://arxiv.org/abs/2611.02251), submitted 2026-11-01).
The preprint *The Premise Is the Problem* proves that overlapping forecast targets can invalidate an
exchangeability-based sequential monitor and reports that adaptation can mask persistent change
([Han et al., arXiv:2610.07038](https://arxiv.org/abs/2610.07038), submitted 2026-10-04). It also explicitly
distinguishes exchangeability tests from e-processes for other nulls. Therefore neither a generic
multi-response controller nor a generic overlap/exchangeability failure claim is a viable project delta.
The remaining opening, if one survives a full proof and comparator audit, is narrower: conditional-mean
paired promotion/rollback certification with delayed selective labels and a pathwise cap, plus a useful
decision or rate advantage over source-matched delayed-inference and active-sensing baselines.

Other screened leads remain closed: the C1-E finite cell has zero anytime promotion power; the Criteo
Attribution replay has only 3.31% labels mature by the final impression and repeated positive conversion IDs;
the restart-mixture and versioned screens fail their frozen gates. Do not tune or confirm those candidates.

## Next eligible action

Run a theorem-only search for either (a) a decision-relevant lower bound under the exact paired fixed-model,
selectively labeled, delayed, hard-cap, global false-promotion contract, or (b) a non-compositional rate theorem
that beats standard delayed anytime inference and finite-state sensing comparators. Before implementing a
method, state the exact null, filtration, estimand, and bound, then check the proposed result against the
existing finite-state sensing DP and delayed-inference baselines. If no such result survives, close the current
algorithm frontier and focus on obtaining a stream with auditable event and label-release timestamps.

This review makes no SOTA claim and authorizes no new empirical confirmation. The existing uncommitted work
in this checkout remains untouched by the synchronization step.

## Follow-up audit — 2026-11-04

The follow-up inspected the current source-of-truth records rather than treating the candidate list above
as open by default:

- The delayed multi-proxy active-PPI note remains a hypothesis. Its construction is a standard composition
  and has no matched comparison against Hsu–Shekhar growth querying and AM-PPI routing.
- The contextual scout has now been compared on disjoint development blocks against both source-matched
  OPE LIL and empirical-Bernstein confidence sequences. Neither OPE boundary crossed on positive streams;
  this closes the scout's advantage claim for that design, without establishing the internal fixed-mixture
  method as SOTA. See `context_scout_ope_comparator_audit_2026-11-04.md` and
  `scout_context_ope_empirical_bernstein_gate_2026-11-04.md`.
- The one-step certification-exponent adaptation has completed full-stream reconstruction and independent
  verification. It promotes 270/300 alternatives versus MOPE's 279/300, with 16/1000 versus 11/1000 null
  promotions; the alternative paired contrast is not significant at two-sided 5% (p=0.0636). This is a
  source-faithful comparator study, not a new method result. The OBD application remains invalid for a
  real-data coverage claim because its IID/no-interference, feature-time and reward-release assumptions
  are not established.
- The Lane A exact finite-instance gaps remain solver evidence: the B=4, alpha=.10 calendar-mixture
  gap is 0.71–1.21% in six selected instances; larger 4.7–5.1% lower bounds require alpha >= .15.
  The original alternative-weighted additive branch risk is false for the implemented causal-null
  game. A corrected one-query recursion yields `r0 <= alpha`, `r0+r1 <= 2 alpha`, and a restricted
  continuation-bound template. But in a representative selected A3c cell, J queries at t=1 with
  probability 3/5 while the best calendar starts at t=2, so this template does not explain the
  measured gap. The growing-family argument remains withdrawn; no method/SOTA gate is met.
  A follow-up all-99-calendar robust LP-dual evaluation at a supporting risk price certifies
  1.1145% lower gap in that cell, independently checking the saved 1.1734% two-sided grid-hull
  lower bound. The recovered grid-mixture components have zero branch-continuation saving, so
  this numerical finite-cell certificate does not validate the proposed mechanism or reopen the
  method lead. LP tolerances apply.
  A second risk-price control confirms that the joint LP dual price gives zero because the joint
  and best-calendar penalized values coincide there; the positive certificate comes from the
  calendar-mixture frontier's supporting price.

**Revised next action:** generalize the robust continuation bound to policies with adaptive
first-query time and public mixtures of calendar supports, then check whether a separation survives
calendar convexification. Audit chance-constrained POMDP prior art only for a theorem that survives that step.
Require a plausible >10% gap at alpha <= .10 with a pathwise budget before any new empirical screen.
If the bound does not survive, retain Lane A only as a finite-instance solver finding and prioritize
data with observed release times and grounded costs.
