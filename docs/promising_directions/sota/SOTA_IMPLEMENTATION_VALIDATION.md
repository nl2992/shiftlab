# SOTA implementation validation

Records what was checked, what reproduced, and what could not be reproduced. A port is only
usable as a comparator to the extent this document says it is.

## Summary

| Competitor | Numerically reproduces author code? | Safe to call by its published name? |
|---|---|---|
| CAMS / CAMS-MAX | **Yes**, exactly, immediate-feedback case | **Algorithm yes, system no** — see below |
| Model Picker | **Yes**, exactly, three stream settings | **Native yes; adapter must be named as an adapter** |

## 1. CAMS (author clone commit `6cbcc62fa289983d10c77637e4bd49f13c2248ed`)

**Reproduction.** Ran the author's `CAMS_identity` and `CAMS_test` against our `CAMSNative` on the
shipped VERTEBRAL data (124 instances, 6 models, 3 classes), three seed/budget pairs
(0, 12), (1, 30), (2, 1000), driving ours through the real simulator. The policy posterior `w_t`
agrees **to 1e-12 at every step**, and the budgeted query decisions and realised sampled-model
losses are identical lists. A manual run issued 28 labels with a moving `w`, so this is not a
degenerate pass.

**Ported from code, not from prose.** Two places where the author code differs from the paper's
description, and the code won:
- the learning rate is `eta_t = sqrt(P/t)`, **not** `sqrt(ln P / t)`;
- the query score is the author's **weighted entropy**, not max-variance (max-variance appears
  only in the context-free task 7).

**What cannot be reproduced, and the naming consequence.** The author's policy *training* code is
not in the repository: contextual policies ship only as precomputed advice matrices, and
`policy_list.txt` names MLP checkpoints that are not shipped. The random-policy rows used in the
author's main runs have no generator in the repo either. Our runs therefore use **our own**
development-trained contextual policy plus constant policies.

> Wherever results appear this must be written as **"CAMS with our development-trained contextual
> policies and constant policies"**, never as "CAMS". The algorithm is CAMS; the policy set is not.

**Adapter deviations** (all marked `# ADAPTER:` in code): deployment by `argmax w_t` keeping the
incumbent on ties, rather than sampling `I_t ~ w_t`, because sampling would pay a switch charge at
random every round; delayed labels updated with the propensity **and advice matrix frozen at
issue**; the hard cap suppressing the draw. CAMS defines no switching cost, so charging one is our
choice, and CAMS has no mechanism that defends against switching.

## 2. Model Picker

**Reproduction.** The author's `model_picker()` against our `ModelPickerNative` on three settings
— (2 models, 2 classes), (3, 4), (5, 3), each T=300. `z_t_log`, `z_t_budget` and
`hidden_loss_log` match **exactly**; the posterior log matches within 1e-12.

**Two defects in the reference implementation, reproduced rather than silently corrected:**
1. The cap is applied with an **off-by-one**: `np.sum(z_t_log) < budget` already includes the
   current round, so at most `budget - 1` queries are ever recorded. Pinned by a test.
2. It **never stops querying or updating at the cap** — with budget 25 it made 131–147 queries.
   Our hard cap is therefore an adapter decision, as the manifest predicted.

**The disclosure that matters most.** The pre-registered degeneracy check was run, and the answer
is yes in part. For two models disagreeing on a binary label, `p·loss_c` is the posterior mass of
whichever model is wrong for class `c`, so `u_t = tuning · q(1-q)`: **identical for both
disagreement patterns and carrying no information about the instance.** In our setting Model
Picker's acquisition is disagreement-gated sampling whose *rate* follows posterior balance and
`t`, and its celebrated instance-level query rule contributes nothing.

Empirically the adaptive rate is not merely a fixed schedule — the `eta_t` floor bound on only
4.7% of disagreement rounds — and against disagreement gating at a matched mean query count it
saved about 2% and 5% of prediction loss in two settings. So the *rate* helps a little; the
*instance selection* does not help at all here.

> This must be stated wherever Model Picker appears as a comparator. It means the comparison is
> weaker than "we beat Model Picker" would suggest: in a binary two-model deployment task, Model
> Picker is close to a well-tuned disagreement sampler.

## 3. A bug this exercise found in our own simulator

Both agents independently hit it, which is why it is recorded here rather than quietly patched.
With `delay=0`, `run_episode` drained `pending[t]` at the **start** of event `t` and then filed
the delay-0 request into that same, already-drained slot, so **no label was ever delivered** and a
learner silently never learned. Both ports saw an adapter that never switched.

Fixed by rejecting `delay < 1` with an explanatory error, because within one event the prediction
and the request have both already happened by the time the label exists, so delay 0 has no meaning
in this loop: immediate feedback is `delay = 1`. Two regression tests pin it.

This is the clearest argument for the common-simulator design: a silent correctness failure in
shared infrastructure surfaced twice, from two independent directions, before any comparison was
run on it.

## 4. Outstanding

- The hard cap's effect on Model Picker is measured only on two small synthetic cases.
- No comparison between any competitor and our method has been run. No performance claim exists.

---

# Round 2: variance minimisation, Xu acquisition, SMCS, Online LLM Picker

## The central structural finding: four independent collapses

The degeneracy flagged in round 1 is not a quirk of Model Picker. **Four methods, derived or
measured four different ways, reduce to the same behaviour in a two-frozen-model binary task.**

| Method | How established | What it reduces to |
|---|---|---|
| Model Picker | measured | `u_t = tuning · q(1-q)`; identical for both disagreement patterns |
| Online LLM Picker | derived from Eq. 10, test-verified | `q_t = max{p(1-p) H(p)/log 2, eta_t}`; 0 on agreement |
| Variance minimisation | measured against author code | score `= 1[disagree]` **exactly**; the surrogate cancels out |
| Xu et al., acquisition-only | derived | `\|D\|=1` on disagreement, so the variance score is constant: gated uniform sampling |

The variance-minimisation case is the starkest: with hard predictions, 0/1 loss and two classes,
`|l_1(c) - l_2(c)| = 1[pred_1 != pred_2]` for **both** values of `c`, so the score is
`1[disagree] · sum_c p_c = 1[disagree]` whatever the surrogate predicts. The surrogate — the whole
point of the method — drops out algebraically. With three or more classes it does matter
(a surrogate of (.7,.2,.1) scores 0.9 where (.1,.1,.8) scores 0.2), so this is specific to our
binary setting and not a defect in the method.

**Why.** Before the label arrives, a two-model binary task exposes exactly one bit about the
instance: do the models agree. Every one of these rules spends that bit in its gate, leaving the
score nothing to discriminate on. This is a property of the *task*, not of the methods.

**What it means for our claim.** Against this family our comparison is substantially about
**query-rate schedules and deployment economics**, not instance selection. Any result must say so.
It also means these comparators are close to a well-tuned disagreement sampler, which makes
"beats the state of the art in active model selection" an overstatement we will not make.

## Variance minimisation (clone `33f6fab5f50d470bc2957a3ed1c4e86d94d82f5d`)

**Reproduction: yes.** Score and LURE match the author's numba functions at `rtol=1e-12` for
(2 classes, 2 models), (3,2) and (4,3); a full 40-step `run_model_selection` with the author's
sampler injected gives identical draw order, `q`, and LURE rows. The RNG stream itself is not
bit-matched (our rejection sampler uses numpy). **Validation requires numba**: without it 4 tests
skip, so run `uv run --with numba pytest tests/promising_directions/test_sota_variance_min.py`.

**LURE does not survive the move to a stream, and this is disclosed rather than papered over.**
LURE's unbiasedness needs sampling without replacement from a pool. The agent's first mapping was
biased by roughly 6x and was corrected; the corrected mapping has **no proof behind it** and shows
about +4% residual bias on one model in a 300-episode Monte Carlo (true 0.383, LURE-adapter 0.400,
plain IPW 0.370). Three classes, named distinctly as instructed:
- `VarianceMinNative` — the published pool algorithm. **May carry the published name.**
- `VarianceMinCausalAdapter` — report as "variance-min score with a LURE-style estimator adapted
  to a stream", **not** as the published method.
- `VarianceMinStreamingIPW` — a different estimator under its own name, per the explicit
  instruction not to call an IPW variant LURE.

## Xu et al. acquisition (clone `a67f85d603df2bb3e32ef007f445191923ebd990`)

**Reproduction: NOT possible, and the reason is recorded.** `Predictor.py:230` is a **syntax
error** as shipped (`self._beta_knots. if self._add_pretrain`), and `simulation.py` imports it at
load, so no entry point imports. `torch` is also absent and was not downloaded. The ported
arithmetic is therefore checked against hand computation only, never against author output. A test
pins the syntax error so the claim is falsifiable.

Validation that did run: issued propensities stay in `[q_min, 1]` so weights are bounded by
`1/q_min`; wealth factors stay >= 0.5 on adversarial streams (all +1, all -1, alternating, random,
predictor maximally wrong, greedy bet at the cap). The hard cap binds only mildly when the floor is
feasible and hard when `q_min ×` disagreement rate exceeds `B/T`.

**A suspected defect in the author's normaliser, flagged as unverified**: the loss
`1/c - dual·(target - mean Q)` with `c = exp(z)` has gradient `-(1/c + dual·Q) < 0` wherever `Q`
is unclipped, so descent only ever raises `c` and nothing pushes it back. If that reading is
right their normaliser collapses toward `q_min`. We could not run it to check, so it is recorded
as a reading, not a finding.

## SMCS (clone `ab0944e7fe0f7c1b25584548deb4e80a75ace251`)

**Reproduction: yes, cross-language.** The R harness runs the author's own `Simulation1.R:77-124`
unmodified via `Rscript` 4.6.1 and compares full `E_adj` trajectories over 300 steps at
`rtol=1e-12`; measured maximum relative difference **4.2e-15 to 4.7e-15**, which is R's
15-significant-digit output floor. Not degenerate: one model's `E_adj` reaches 1.4e9 and is
excluded at t=13. A golden vector guards the port when `Rscript` is absent.

**Null chosen**: the pairwise conditional `H_ij: E[L_i - L_j | F_{t-1}] <= 0`, matching our
two-model paired 0/1 comparison. The Sim3 time-averaged null is **BLOCKED** (`pracma` and
`NlcOptim` unavailable offline) — and that is the formulation intended for non-stationary streams,
which matters for the caveat below.

**Selective feedback breaks the native loss bound, and the fix is ours.** Importance-weighted
differences give `|d~| <= 1/q`, so the native `lambda = 1/2` produces **negative wealth** for
`q < 1/2` (demonstrated at `d = -20`, `q = 0.05`). Fixed with a predictable per-round bound
`c_s = 1/q_s`, hence `lambda_s = q_s/2`, keeping every factor in `[0.5, 1.5]`. Evidence then
accrues `q` times more slowly than under full feedback. Null coverage holds within `alpha + 3σ`
over 150 delayed, budget-capped streams.

**The caveat that may matter most for this comparator: cumulative is not current.** SMCS evidence
is an undiscounted running product and an excluded model can never re-enter. A test shows a
challenger excluded in regime 1 that then becomes better for 600 rounds and is **still excluded at
the end**. Our task asks which model is best *now*; SMCS answers which models have not been shown
worse *over all history*. That is a mismatch of estimand, not of tuning, and the deployment rule
has no rollback for the same reason. Report as **"SMCS inference + development-chosen
retain-incumbent rule"**, never as SMCS, and state that acquisition is the P7a pacer.

## Online LLM Picker (no author code located; ported from the paper text)

Implemented from Eq. 10 and the algorithm box. **BLOCKED**: the value of `eps` in
`eta_t = sqrt(log m / (t(Vhat_t + eps)))` is not recoverable from the text, so `eps = 1e-8` is
**our** choice. It matters: until the first annotation `Vhat = 0`, `eta_t` is enormous and `q_t`
clips to 1. Measured consequence under our hard cap — median purchase at event 90 of 600, budget
exhausted by event 292, i.e. **the budget is front-loaded into the opening sixth of the episode**.
A different `eps` would change this, so every result for this comparator carries the caveat.

## Status

212 passed, 10 skipped; ruff clean across all SOTA files. Model Selector is still outstanding.
**No comparison between any competitor and our method has been run. No performance claim exists.**

---

# Round 3: Model Selector — and a fifth independent collapse

**Clone `6aa57e5750153bccb04c9e96946b726d14f5d3f1`.**

**A naming trap worth recording**: the authors register Model Selector internally as
`type: "model_picker"` (`src/model_selection/methods/model_picker.py`). It is **not** Karimi's
Model Picker, and every shipped config uses that name. Anyone comparing the two repositories
casually would conflate them.

**Reproduction: yes, exactly.** The author's `ModelSelector.run` was run unmodified (one numpy-2
shim) across 6 synthetic settings — including 2 models/2 classes, epsilon 0.50 where all scores
tie, and a budget exceeding the disagreement set so the back-fill path is exercised — plus two
seeds on the shipped `emotion_detection` data. Labelled indices and per-step rankings are
identical, with the author's global `np.random` stream reproduced draw for draw. The epsilon grid
search also matches: `success_avg` to 1e-12, identical `fastest` list, same chosen epsilon.

**Published rules preserved**, including the one most easily got wrong: the final selection rule
is **highest labeled-set accuracy**, not argmax posterior. A test sets epsilon 0.6, where the
posterior argmax is the *worst* model, and confirms the accuracy rule still returns the best one.

## The fifth collapse, and the most general one

With two models, every disagreement example presents the **same pair of hypothetical posteriors**
— one label rewards model 0, one rewards model 1, any other rewards neither — so expected
posterior entropy is a single constant across all disagreement examples. This holds **for any
number of classes, any posterior, and any epsilon**, which makes it stronger than the other four
collapses, all of which were specific to binary labels.

Verified by test: exact equality at K=2, equality to 1e-12 at K=3 and K=5. Consequences measured:
epsilon does not change *which* examples are queried, only the posterior; at K=2 the tie-break
draws reproduce uniform random sampling without replacement over the disagreement set, matched
index for index; and at K>2 the scores tie mathematically but differ by ~1 ulp (5.6e-17), so the
reference's `==` comparison selects from an arbitrary float-noise subset — information-free, but
not even uniform. With three or more models the collapse ends once the posterior moves.

**So in our setting Model Selector reduces to: random sampling of disagreements, posterior
arithmetic, and a labeled-accuracy final rule.** Its instance-level acquisition contributes
nothing.

## The causal adapter is not faithful, and we did not change the task to make it so

Algorithm 1 takes an argmin over a pool, which requires labelling an **earlier** event
retrospectively. Our simulator grants a label only for the event being processed. Making the
adapter faithful would mean adding a `target_event_id` to `QueryRequest` — which would change the
information structure **for every competitor**, not just this one.

Per the brief's explicit instruction ("if retrospective querying is forbidden, use a separate
compatible pool experiment rather than silently changing the task"), we did **not** make that
change. Instead:
- `ModelSelectorNative` — the faithful pool algorithm. **May carry the published name.**
- `run_block_pool_experiment` — the faithful algorithm on blocks of already-arrived events, with
  labels guarded so any read outside the block raises, and cost accounting matching `run_episode`.
- `ModelSelectorCausalAdapter` — a *record gate*, not Algorithm 1. Must be reported as
  **"Model Selector, causal record-gate adapter"**. In our binary two-model setting it is not
  usefully different from paced disagreement sampling. A known wart is recorded: old events that
  can never be queried linger in the window as reference points and can block later events until
  they expire.

**BLOCKED**: the rule mapping grid-search output to the paper's per-dataset epsilons (Table 4) is
not in the repository; shipped configs use metric "all" while the code default `success_diff`
would crash on them. We expose `success_avg` (default) and `fastest`.

**Paper/code mismatch, code followed**: footnote 3 says the class distribution is "uniform over
the model predictions"; the code uses uniform over all classes. With two models both readings
give the same collapse.

---

# Round 3 summary: the acquisition literature does not transfer to this task

| # | Method | How established | Reduces to |
|---|---|---|---|
| 1 | Model Picker | measured | `tuning · q(1-q)`, instance-blind |
| 2 | Online LLM Picker | derived from Eq. 10 | `max{p(1-p)H(p)/log 2, eta_t}` |
| 3 | Variance minimisation | measured vs author code | `1[disagree]` exactly; surrogate cancels |
| 4 | Xu et al. (acquisition-only) | derived | gated uniform sampling |
| 5 | Model Selector | proved for all K, all posteriors, all epsilon | constant across disagreements |

Five methods. Five independent derivations. One conclusion: **in a two-frozen-model binary
deployment task, instance-level acquisition has nothing to work with**, because the single bit of
pre-label information is consumed by the disagreement gate every one of them already applies.

This is a finding about the task, and it is arguably worth more than the comparison it was
gathered to support. It also bounds what any win of ours could mean: against this family we can
only be competing on **query-rate scheduling and deployment economics**. That is exactly what our
method changes, so a win would be real — but it would not be a win over instance selection,
because none of these methods is doing instance selection here.

**Status: 6 of 6 mandatory competitors implemented, 5 numerically verified against author code.
212 passed, 10 skipped, ruff clean. No comparison has been run. No performance claim exists.**

---

# Round 4 (Failure Atlas v2, 2026-11-03): gated deployment and DISCERN-style

Neither has author code available; both are ports from the printed constructions
(`competitors/certificate_stops.py` docstring cites the sections). Their earlier absence from this
record was flagged by the Atlas v2 independent review.

- **DISCERN-style PrPl-EB fidelity bug, fixed.** Waudby-Smith and Ramdas (arXiv:2010.09686, eq. 14)
  define `psi_E(l) = (-log(1-l) - l)/4` together with `v_i = 4 (X_i - mu_hat)^2`. The port kept the
  factor 4 in `v_i` but dropped the `/4`, inflating the variance penalty fourfold. Verified against
  the extracted paper text; hand-computed test updated. After the fix: ever-miss 0.013 over 1000
  Bernoulli(.5) streams of length 1000 at delta .05.
- **Worst-case range is an adapter choice, not the papers'.** Both ports fixed the HT range at
  `1/p_min = 20` (gated `wmax`, DISCERN `c`). The issue-time propensity is predictable, so tighter
  ranges are legitimate. Two stronger readings were added (`scripts/failure_atlas_v2/strong_hosts.py`):
  `GatedAdaptiveRange` (MOPE bet set at `wmax_t = 1/q_t`, bet recomputed before each ingestion) and
  `DiscernDesignFloor` (declared `pi_min = .25`). In Atlas v2 validation both keep null promotion
  at <= .01 on all four nulls and are materially cheaper than the original ports on stationary
  alternatives. Any Atlas v2 SOTA comparison uses the stronger readings.
- **Not verified:** no numerical comparison against author code exists for either method; gated's
  appendix C-E constraint set and scalar betting variant were not ported (unchanged from before).
