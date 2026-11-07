# 03 Formal problem and information contract

Status: definitions plus two elementary propositions. Proved here with complete arguments; they are
not reviewed by anyone else and are not presented as novel results. They fix what Lanes A and B may
claim.

## 1. Experiment

Event times `t = 1..T`. Model bank `{f_0 (incumbent), f_1..f_K (frozen candidates)}`. At time `t`:

1. Observe free information `X_t` (covariates, all model predictions, any free context).
2. Choose query probability `p_t in [0,1]` from released information. Draw `Q_t ~ Bern(p_t)` using
   recorded public randomness `U_t`. Pay `c_q Q_t` immediately. Pathwise hard budget:
   `sum_{s<=t} Q_s <= B` surely (a request that would exceed `B` is infeasible, not truncated later).
3. Freeze `p_t`, prediction outputs and any bet/control variate issued at `t` (issue-time
   predictability).
4. A label `Y_s` with `Q_s = 1` is released at `R_s = s + d_s`. In the anchor contract `d_s = d` is
   fixed; informative delays (`d_s` dependent on `Y_s`) are a separate stress case and are not covered
   by the Section 3 validity statements.
5. Choose deployed model `A_t in {0..K}` from released information. Pay deployment loss
   `l(f_{A_t}(X_t), Y_t)` (whether observed or not) plus switch cost `c_s 1{A_t != A_{t-1}}`.

Learner filtration: `H_t = sigma(X_{1:t}, U_{1:t}, Q_{1:t-1}, A_{1:t-1}, {(s, Y_s): Q_s = 1, R_s <= t})`.
The query decision at `t` is `H_t`-measurable; the action at `t` is measurable w.r.t. `H_t` plus
`Q_t` and the labels released exactly at `t`. Evaluator-only: latent regime path, change times,
unreleased labels, and oracle per-model losses.

## 2. Objectives (kept separate)

| # | Quantity | Definition | Lane |
|---|---|---|---|
| 1 | incumbent deterioration | `E[l(f_0,Y_t) | F_{t-1}] - U_0` | C, D |
| 2 | candidate-relative advantage | `D_t^k = l(f_0,Y_t) - l(f_k,Y_t)` (same acquired outcome) | B, E |
| 3 | conditional decision-cost excess | `E[L_t | F_{t-1}] - (U_0 + eps)` | C (H2c null) |
| 4 | stationary-marginal risk | `lim E[L_t]` under stationarity | F (closed as a monitor target) |
| 5 | future switching benefit | `E[sum_{s>t} (D_s^k) - c_s - rollback | H_t]` | A, B |
| 6 | false promotion | promotion while the causal null holds (no candidate is better in the declared sense) | A, B |
| 7 | regret | net cost minus that of a feasible switching oracle with matched information | A |

Two-law structure (Lane A, repository game): minimise expected total cost under the alternative
law, subject to worst-case false-promotion probability `<= alpha` over the causal-null family.
This is not replaced by an i.i.d. null anywhere in this programme.

## 3. Proposition B0 (certificate is not a switching guarantee)

Claim: a level-alpha anytime certificate that `D_s^k > 0` held on average up to time `tau` implies
nothing about item 5 without an assumption linking past to future advantage.

Counterexample. Let the advantage process be `D_s = delta > 0` for `s <= tau*` and `D_s = -delta`
for `s > tau*`, with `tau*` a stopping time unknown to the learner, and any certificate that
fires at `tau <= tau*` with probability one. Switching at `tau` yields future benefit
`delta (tau* - tau) - delta (T - tau*) - c_s`, which is negative whenever
`tau* - tau < (T - tau* ) + c_s/delta`. The certificate remains valid (its null never held before
`tau*`). Therefore any guarantee on item 5 needs at least one of: a persistence assumption (for
example, `P(advantage persists >= m steps | certified) >= rho`), a drift bound
`|E[D_{s+1} - D_s | F_s]| <= kappa`, or a rollback option with bounded cost plus monitoring after
promotion. With persistence `m` and constant advantage `delta`, the switch is profitable in
expectation when `rho delta m > c_s + (1-rho) * (expected loss until rollback)`. This bridge is
elementary decision theory, not a novelty claim.

## 4. Proposition A0 (when "joint vs separable" is an information gap)

Setting: Section 1, with randomisation from the public `U_t` (so randomised policies are
`H_t`-measurable functions of `U`).

Assumption (made explicit after adversarial review, `11_ADVERSARIAL_REVIEW.md`): *every* randomised
action (promotion, rollback, root-mixture calibration coin) draws its randomness from the recorded
public `U`. If an action rule uses a private coin invisible to the acquisition rule, (i) can fail.
The repository's root-mixture calibration needs no private coin. Under this assumption (i) is close to a
tautology. Its value is in pinning down which separations are informational, not in its depth.

Let `Pi_J` be all pairs `(q, a)` of query rules and action rules adapted as in Section 1. A
"separable" class fixes a sub-sigma-field `G_t subseteq H_t` that the query rule may use.

(i) If `G_t` contains `X_{1:t}, U_{1:t}, Q_{1:t-1}` and every released label, then `G_t = H_t`. Past
actions are `H_{t-1}`-measurable functions of those variables (by induction on `t`, using
public randomness for randomised actions). So the "label-history-adaptive acquisition + optimal
switching" class equals `Pi_J`. Its optimum equals the joint optimum, and the
same holds for the worst-case risk constraint because the feasible set is identical.

(ii) Hence an information-matched gap between a jointly optimised and a "separately optimised"
history-adaptive pair can come only from the optimisation procedure. An example is a
person-by-person (coordinate-wise) fixed point that differs from the team optimum, in the sense of
team decision theory. It is not a property of the information structure.

(iii) A gap that is a property of the information structure requires `G_t` to be strictly coarser
on released labels or free observations. The extreme case is a calendar or open-loop
acquisition (`G_t` = time only), where the gap is the adaptivity gap of acquisition timing.
Calendars that may skip slots are still `G_t` = time for the choice of *which* slots exist, while
the skip decision is part of the action rule.

(iv) A third kind of "separation" uses an acquisition rule tuned to a surrogate objective, for example
detection delay or posterior entropy, followed by optimal switching. The gap is then a
value-of-information misalignment and can be made arbitrarily large by construction. A
simple example: the surrogate keeps querying after a promotion that makes further labels
decision-irrelevant, and so exhausts `B` before a reversal. This is classical and is not a
contribution.

Proof of (i): `A_1` is a measurable function of `(X_1, U_1, Q_1, Y_1 1{R_1<=1})`. Suppose `A_{1:t-1}`
are measurable functions of the generating variables listed in `G_{t-1}` plus released labels.
Then `A_t` is a measurable function of `G_t` plus `Q_t` and the labels released at `t`. Therefore
`sigma(G_t, A_{1:t-1}) = sigma(G_t) = H_t`. The feasible policy sets coincide, and so do the
objective and constraint, which are functionals of the joint law induced by the pair. QED.

Consequence for Lane A: the only information-matched separation to test is (iii). The registered
A1 test (`protocols/A1-exact-separation.md`) measures exactly the timing adaptivity gap under the
exact risk game. Result (ii) means that "joint beats separately designed" claims elsewhere in the
repository must state which of (ii)–(iv) they are, or they are not information-matched.
