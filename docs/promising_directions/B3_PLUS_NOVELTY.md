# B3+ novelty: differentiation from the closest work

Reviewed 2026-11-02. Each external claim below was read from the cited source, not recalled.
The in-repository comparisons were read from the pinned implementation at `041bc26`.

## Updated boundary — 2026-11-08

Cao, [*The First-Order Value of Free Covariates in Budgeted Risk Monitoring* (2026)](https://arxiv.org/html/2611.00576), is the closest newly identified prior art. It studies free-covariate and label-history acquisition for anytime-valid, one-sided harmful-risk detection with paid labels. Its theory uses an expected source-prefix request budget and a single deployed model's binary loss relative to a risk threshold. This rules out broad novelty claims for budget-aware acquisition in sequential risk monitoring.

The remaining difference is a hypothesis to test, not an established novelty claim: P7s monitors paired utility between two frozen classifiers, supports promotion and rollback, and enforces a hard per-episode query cap with delayed feedback. Cao's paper does not establish this two-action replacement contract. A fair next comparison must adapt its label-history and covariate-triggered hybrid acquisition rules to the same paired stream, delayed release schedule, and hard cap, while leaving P3b's evidence process fixed. Compare P3b, P7s, and both adapted controls on stationary-positive, abrupt-reversal, and benign-covariate-shift episodes. Report net cost, false rollback, reversal-to-rollback delay, and cap violations; require zero cap violations and predeclare the error/delay constraints before evaluating P7s. Do not advance the novelty claim unless P7s saves cost at matched false-rollback and rollback-delay performance against both adapted controls.

Development update: the first 200-seed-per-scenario matched simulation is recorded in `B3_PLUS_CAO_DEVELOPMENT_FINDINGS_2026-11-08.md`. P7s saves cost in stable and benign-shift scenarios but loses on cost and rollback timing after abrupt reversal; the sentinel prototype and a small settled-rate sensitivity do not resolve the gap. No confirmatory run or novelty claim is warranted for the current method.

## Closest work, as actually read

### 1. P3b — this repository, `b1_certified_switching.py` (`kind="P3b"`)
Disagreement-gated paired IPW e-process with a propensity-matched bet cap. Acquisition is a
pure budget pacer: `q_t = clip(rem / (rate_t * (T - t)), p_min, 1)`. Promotion is the single
crossing `log W_t >= log(1/alpha)`. **No cost term appears anywhere in the decision.** The
switching cost `c_s` enters only the reported metric, never the policy.

### 2. P4 / P4w — same file (`self.k >= 1`)
Already cost-aware: `promote only if lb_value_t * min(hazard_mean, T - 1 - t) > c_s`, with
`lb_value_t` a lower confidence bound from a margin-null grid. **This is the real incumbent for
the promotion rule.** Any claim that "break-even promotion" is new would be false. P4's horizon
is a declared hazard prior, and it prices no future label spend.

### 3. CAMS — Liu, Xia, Stevens, Chen, *Contextual Active Model Selection* (NeurIPS 2024;
arXiv:2207.06030)
Queries with probability `z_t = max{1/sqrt(t), E(y_hat_t, w_t)}`, where `E` is a
**disagreement score** over the policy-weighted loss distribution; queried losses are
importance-weighted by `1/z_t`. Objective is **pseudo-regret / expected regret** against the
best policy in hindsight; the label budget is a hard constraint, not a cost in the objective.
Read from the source: no switching cost is modelled, the query rule does not use the remaining
horizon (`T` is hidden from CAMS in the experiments; `1/sqrt(t)` depends only on the current
round), delayed labels are not addressed, and there is **no deployment commitment** — the
deployed model is recomputed every round, so no notion of "promotion" or its price exists.

### 4. Xu, Karampatziakis, Mineiro, *Active, anytime-valid risk controlling prediction sets*
(NeurIPS 2024; arXiv:2406.10490)
The closest work on **budgeted active labelling driven by an e-process**. Its labelling policy
maximises a lower bound on the **expected log-growth of the e-process** subject to a label
budget, with `q_t(X_t)` a function of the covariate computed from data before `t`; the
"pretrain" variant uses a pretrained estimate of the conditional standard deviation of risk,
evaluated at the current bound. Read from the source: the query probability is driven by
**estimated conditional risk variability, not by distance to a decision boundary**; decision
value, switching cost and economic break-even are not modelled; **labels are assumed available
immediately**, delay is not addressed; the null is `H0^beta: rho(beta) >= theta` for a risk
threshold; and **model switching / promotion between candidate models is not considered** — the
object calibrated is one model's own risk.

## The distinction B3+ actually rests on

Both CAMS and Xu et al. choose labels to buy **information**: disagreement in one case,
evidence log-growth (variance) in the other. Neither asks whether the information can change an
action whose price is known.

B3+ chooses labels by **decision relevance under an explicit switching price**: when even the
optimistic advantage cannot repay `c_s` within the realised remaining horizon
(`UCB_t * (T - t) < c_s`), no label can change this episode's deployment decision, so
acquisition drops to the propensity floor and the budget is left unspent. This is a
*deliberate refusal to maximise evidence growth* — the opposite of the Xu et al. objective —
and it is the mechanism from which the label savings come.

## Novelty matrix

Only differences present in the final selected method may be claimed. Entries marked
**(pending)** are hypotheses until the Phase 1 selection and the named experiment report.

| Component | Existing method | B3+ difference | Evidence |
|---|---|---|---|
| Label acquisition | P3b/CAMS: disagreement-driven. Xu et al.: maximise e-process log-growth under budget | Decision-relevance gating: spend only where a label could still flip an economically priced deployment decision; drop to the propensity floor when `UCB*(T-t) < c_s` | Acquisition ablation `P7b` vs `P3b`; labels-saved column **(pending)** |
| Sequential evidence | Paired IPW e-process with propensity-matched bet cap (P3b); margin-null grid LCB (P4) | **Reused unchanged.** No new evidence process is claimed | Nonnegative-wealth and equality-null calibration checks |
| Switching decision | P3b: certificate crossing only. P4: `LCB * min(hazard_mean, T-1-t) > c_s` | Realised remaining horizon `T - t` in place of a declared hazard prior, plus an explicit future label-spend term `c_q * E[future queries]` | Promotion ablation `P7a` vs `P3b` vs `P4ref` **(pending)** |
| Reversal handling | P3b/P4 mirrored-test rollback | **Not claimed.** Implemented as the `P7c` ablation and compared with P4; retained only if Phase 1 shows independent value | Reversal experiment **(pending)** |

## Behaviour that changes, and when it should help

At least one concrete behavioural difference, to be demonstrated rather than asserted:

**Late-episode refusal.** Given identical released evidence, P3b promotes the moment
`log W_t >= log(1/alpha)` regardless of how little horizon remains, paying `c_s` for a benefit
that cannot accrue. B3+ withholds promotion once `LCB_t * (T - t) <= c_s + Cq_future_t`.
Expected to be advantageous when `c_s` is large relative to the per-event advantage, when the
advantage is small (weather), or when certification completes late in the episode; expected to
be neutral when the advantage is large and arrives early (spam), where both promote
immediately.

**Hopeless-regime saving.** Where the challenger is not better, P3b keeps paying the pacer's
rate to the end of the budget. B3+ recognises that no label can change the decision and stops.
Expected to show as a reduced `c_q N_q` term on the four non-WIN streams, where the honest B3
result is that certified switching costs slightly more than never switching.

## Reduction check

Does B3+ reduce algebraically to an existing rule?

- Set `r_t == 1` and the break-even gate always true: **exactly P3b**.
- Set `r_t == 1` and `Cq_future == 0` and `H_eff = min(hazard_mean, T-1-t)`: **exactly P4**.
- The acquisition rule has no `r_t` setting that recovers CAMS (no policy-weight distribution)
  or Xu et al. (no log-growth objective, opposite sign of intent near a satisfied decision).

So the promotion rule is a **refinement of the repository's own P4**, and the acquisition rule
is the component with no counterpart in any of the four. The contribution statement must be
written that way, and the paper must present P4ref as a baseline, not as unrelated prior work.

## Statement of what is and is not guaranteed

Established: the margin-null e-processes have nonnegative wealth factors under the
propensity-matched cap (`lam in [0, q/2]`, `|x| <= 1/q` give `1 + lam*y >= 1/2`); the issued
propensity is measurable w.r.t. information released before the event and bounded below by
`p_min`, so IPW increments are unbiased with bounded weights; the hard budget is pathwise
feasible; the ordered margin grid supports a time-uniform lower confidence bound at level
`alpha`.

**Not established:** that `LCB_t * (T - t)` is realisable future benefit. That reading needs
the persistence assumption `E[D_u | F_t] >= E[D_t | F_t]` for `u > t`, which is stated, probed
by the reversal experiment, and **not proved**. `V_hat_t > 0` is an economic decision criterion,
not a certificate about future returns. No minimax or universal-dependence claim is made.

## Sources

- Liu, Xia, Stevens, Chen. Contextual Active Model Selection. https://arxiv.org/abs/2207.06030
- Xu, Karampatziakis, Mineiro. Active, anytime-valid risk controlling prediction sets. https://arxiv.org/abs/2406.10490
- Setoudehtanzangi and McLachlan. Large Classification-Risk-Optional Label Acquisition (2026). https://arxiv.org/abs/2609.06873

## Prior-art and attribution correction — 2026-11-08

The broad statement above that neither CAMS nor Xu values labels by whether they can affect a decision is not a sufficient novelty argument. Setoudehtanzangi and McLachlan (2026) derive a cost-sensitive acquisition design for reducing leading classification risk using information aligned with active Bayes-boundary directions. The defensible distinction for P7s is narrower: it keeps incumbent/challenger classifiers fixed and reduces post-promotion sequential monitoring queries while retaining the paired evidence process and rollback floor. Decision-relevant label acquisition in general is prior art.

The old manuscript table did not name P7s, and its interpretation of the ablation was broader than the analyzed cases. P7b is the hopeless-state-only ablation; corrected P7s adds the settled-state gate. The checked-in S0 ablation records support this mechanism only on spam (K=1), rialto (K=16), and weather (K=3). The reproducible hash-checked analysis is `scripts/promising_directions/b3_plus_attribution_audit.py`, with results in `outputs/b3_plus_attribution_audit/report.md` and the scoped interpretation in `B3_PLUS_ATTRIBUTION_AUDIT_2026-11-08.md`. No novelty or SOTA conclusion follows from this reanalysis.

## Additional direct prior art: economic model replacement — 2026-11-08

Digalakis Jr. et al., [*The Challenger: When Do New Data Sources Justify Switching Machine Learning Models?* (arXiv:2512.18390v2, July 2026)](https://arxiv.org/html/2512.18390), is direct prior art for the broad model-replacement objective. It formalizes switch/discard/continue decisions with learning-curve, data-acquisition, retraining, and deployment costs; derives an oracle timing rule and an `O(T^(2/3) sqrt(log T))` regret result for reliable switching procedures; and evaluates greedy, one-shot, and look-ahead sequential evaluation on chronological credit-scoring data.

Its main setting grows a challenger as full-feature training data arrive and retrains/evaluates at decision epochs. It does not describe the B3+ contract of two frozen classifiers, selective label queries under a hard pathwise cap, delayed label releases, and a reusable anytime paired promotion/rollback monitor. These are potential scope distinctions, not novelty by themselves. The paper rules out claiming that economically priced sequential model switching or oracle-regret analysis is new. Any B3+ comparison should state its fixed-model monitoring target and provide a source-faithful comparison only where the incumbent assumptions can be mapped without replacing the paper's learning-curve problem with a different one.
