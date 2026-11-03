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
