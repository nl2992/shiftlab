# Applicability reports for the review-only sources

Three sources are mandatory to read and assess, not necessarily to implement. Each is read in
full where the method details are needed; the brief is explicit that an abstract is insufficient.

## A structural finding that affects the whole comparison

While assessing these, a pattern emerged that is more important than any single verdict.

**In a two-frozen-model binary classification task, the informativeness-based acquisition rules of
this literature collapse to the same thing: disagreement gating with a rate driven by posterior
balance.** They become blind to the instance.

- **Model Picker** (measured, see `SOTA_IMPLEMENTATION_VALIDATION.md`): `u_t = tuning · q(1-q)`,
  identical across both disagreement patterns.
- **Online LLM Picker** (derived below from its Eq. 10): `q_t = max{p(1-p) · H(p)/log 2, eta_t}`
  on disagreement, `0` on agreement.

The reason is structural, not incidental. With two models and a binary label there is exactly one
bit of instance-level information available before the label arrives — whether the models agree —
and every one of these rules already consumes it in its gate. Nothing is left for the score to
discriminate on.

**Consequence for our claims.** Against this family, a comparison in our setting is substantially
a comparison of *query-rate schedules and deployment economics*, not of instance selection. That
is a weaker contest than "we beat the state of the art in active model selection" would imply,
and it must be stated wherever these comparators appear. It also means a win for us would be
earned on economics, which is precisely what our method changes.

---

## 1. Online LLM Picker (arXiv:2610.01592) — APPLICABLE, implement, disclose degeneracy

Read: full HTML text, not the abstract.

**Method as published.** Query score (Eq. 10): with `l^k_{t,i} = 1 - d(f_i(x_t), f_k(x_t))` the
loss of model `i` were model `k`'s output the truth, `Var_k = Var_{i~p_t}[l^k_{t,i}]`, and
`H̄(p) = H(p)/log m` the normalised posterior entropy,

    q_t = max{ max_k Var_k * H̄(p_t), eta_t }   if max_k Var_k != 0, else 0
    Q_t ~ Bernoulli(q_t)

Updates occur only on queried rounds, importance weighted by the issue-time `q_t`:
`l̂_{t,i} = l^y_{t,i} Q_t / q_t`, `p_{t,i} ∝ exp(-eta_t L̂_{t-1,i})`, with
`eta_t = sqrt(log m / (t(V̂_t + eps)))` and `V̂_t` a bias-corrected EMA of the variance that
updates only on annotation. Recommendation is `argmax_i p_{t,i}`; there is one rule, not a
separate prediction and recommendation.

**Three mismatches with our task, all adapter-level rather than fatal:**
1. **Loss type.** Its loss is similarity-based (ROUGE-L or BERTScore), not 0/1. In our binary
   setting `d` becomes exact agreement, so `l^k_i = 1{f_i != f_k}`, which is a legitimate
   specialisation but not what the method was built or tuned for.
2. **Budget.** It enforces an **expected proportion**, not a hard cap; the paper itself is
   inconsistent, defining a maximum but tuning methods "to query the same number on average".
   Our hard cap is therefore an adapter, not an inherited property.
3. **Scale.** Formally valid at `m = 2` (`log m > 0`), but evaluated only on collections of 130+
   models. Its benefit at `m = 2` is untested by its authors.

**Degeneracy, derived.** With two models and a binary label, on disagreement
`l^0 = (0,1)` and `l^1 = (1,0)`, so `Var_0 = Var_1 = p(1-p)` and
`q_t = max{p(1-p) H(p)/log 2, eta_t}`; on agreement both variances are 0 and `q_t = 0`. The score
carries **no instance information**. This is the same collapse as Model Picker, reached by a
different route.

**Verdict: implement as `OnlineLLMPicker`**, with the three adapter notes above and the degeneracy
disclosed beside every result. It is a stream method with no revisiting, which fits our task
cleanly.

## 2. Expert Advice with Costly Observations (Reyzin, Saha, Wu, UAI 2026) — EXCLUDED, precisely

Read: the paper itself (PMLR v337, pp. 5700-5715), problem setting on p. 5701-5702.

**Observation model, quoted in substance.** At each round the learner selects a subset
`S_t ⊆ [K]` of experts to observe; observing expert `i` costs `p_i ∈ [0,1]` and the learner pays
`sum_{i in S_t} p_i`. It must then choose `I_t ∈ S_t` to play, so `S_t` cannot be empty, and the
losses `{l_t(i)}_{i in S_t}` are revealed. Costs are fixed and known. `m-EXP3` samples a subset of
size `m` and `m-ELIM` is its stochastic-loss counterpart.

**Why it does not map to our task.** Four reasons, each sufficient on its own:

1. **The cost structure is inverted.** Their cost is **per expert and additive**: seeing every
   expert costs `sum_i p_i`, and the regret bound carries an explicit `(m-1)p̄T` penalty for
   breadth. In our task **one** label purchase at price `c_q` reveals **every** frozen model's
   loss simultaneously. The brief is explicit that we must not charge per classifier. Forcing a
   mapping by setting `p_1 = c_q` and `p_i = 0` otherwise would permit observing models 2..K for
   free *without buying a label*, which our task does not allow.
2. **Observation is compulsory.** `S_t` cannot be empty and the played expert must be observed, so
   every round costs at least `min_i p_i`. Our policy deploys on every event while buying labels
   on roughly 10% of them; the regime where our method operates is one their model forbids.
3. **No delayed feedback.** Losses are revealed in the round they are paid for.
4. **No deployment switching cost.** Changing the played expert is free, so the economics our
   method is built around are absent.

**Verdict: excluded, with the above as the stated reason.** Implementing `m-ELIM` here would
require changing its observation model into a different problem and would not constitute a
comparison against the published method.

## 3. Drift2Act (arXiv:2603.08578) — APPLICABLE ONLY AS A HEAVY RESTRICTION; artifacts missing

Read: abstract and method description.

**Method as published.** A controller that estimates drift type from unlabelled signals, uses a
small number of delayed labels to form a high-confidence upper bound on current risk, and then
acts: if the bound is within threshold it applies **low-cost actions (recalibration, test-time
adaptation)**; otherwise it abstains or escalates to **rollback or retraining**, subject to
cooldowns. Evaluated on WILDS Camelyon17, DomainNet and a synthetic drift stream.

**Compatibility with our action space.** Our task has **two frozen models** and exactly three
available actions: promote, roll back, query. Of Drift2Act's action set, recalibration, test-time
adaptation and retraining are all **unavailable by construction** — the models are frozen, which
is the premise of the task. What remains is its drift belief, its risk certificate and a
promote/rollback/query gate.

That is a **restriction of the controller to a strict subset of its action space**, removing
precisely the low-cost actions its escalation logic is designed to prefer. Its reported advantage
over "alarm-only monitoring" and "always-adapt" comes substantially from having a graded ladder of
cheap responses; a two-frozen-model task removes the ladder.

**Reproduction status.** No author code is linked from the arXiv page and none was located. The
gain models and belief components the controller needs would therefore have to be trained by us
on development data, which means any "Drift2Act" result here would be our reconstruction of a
described controller, not the published system.

**Verdict: assess, do not claim a faithful comparison.** If implemented, it must be named as a
**restricted reconstruction** and the missing action space stated. Per the brief, the exact
missing dependency is recorded: no public implementation, and no released gain/belief model
artifacts. We will not invent retraining benefits or handoff outcomes it never gets to demonstrate.

---

## Summary

| Source | Verdict | Name to use if it appears in results |
|---|---|---|
| Online LLM Picker | Implement | `OnlineLLMPicker (adapter; degenerate acquisition at m=2)` |
| Expert Advice with Costly Observations | **Excluded** | n/a — observation model does not map |
| Drift2Act | Restricted reconstruction only | `Drift2Act (restricted reconstruction, no author code)` |
