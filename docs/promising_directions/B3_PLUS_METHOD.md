# B3+ method specification

Policy name in code and results: **P7**. Reference: P3b, as implemented in
`scripts/promising_directions/b1_certified_switching.py` at commit `041bc26`
(class `Cert`, `kind="P3b"`).

## 1. Setting and objective

A chronological event stream of length `T`. A frozen incumbent `f0` and a frozen challenger
`f1` produce 0/1 losses `l0[t]`, `l1[t]`. The deployed action `a_t in {0, 1}` is chosen before
`Y_t` is seen. A label is obtainable only by paying for it, at most `B` labels per episode, and
a requested label is released `d` events later.

The realised net cost of a policy pi is

    C_pi = sum_t l_{a_t}[t] + c_q * N_q + c_s * N_s

with `N_q` requested labels and `N_s` deployment switches. Every variant below optimises this
same objective. Primary setting: `T = 2000`, `B = 200`, `c_q = 0.05`, `c_s = 5`.

## 2. Filtration and timing (unchanged from P3b, restated because B3+ depends on it)

At event `t` the policy performs, in this order:

1. **Issue.** Decide the query probability `q_t` and freeze the bet `lam_t`. Both may depend
   only on `F_{t-d-1}`: labels released strictly before this event. `q_t` and `lam_t` are
   written to a ring buffer of depth `d`.
2. **Release.** The label of event `s = t - d` becomes usable. Its importance-weighted paired
   increment `x_s = (l0[s] - l1[s]) / q_s` enters the evidence process with the bet `lam_s`
   that was frozen at issue time.
3. **Decide.** Promotion or rollback takes effect from `t + 1`.

Disagreement gating: `x_s` is structurally zero unless `f0` and `f1` disagree at `s`, so only
disagreement events are ever queried. The propensity floor `q_t >= p_min = 0.05` applies to
every eligible disagreement event while budget remains.

## 3. What P3b does, exactly

**Acquisition (pacer).** With `rem` labels left, `ndis` disagreements seen, and prior
`(prior_rate = 0.25, prior_w = 20)`:

    rate_t = (ndis + prior_rate * prior_w) / (t + prior_w)
    q_t    = clip( rem / max(rate_t * (T - t), eps), p_min, 1 )        if rem > 0, else 0
    ask_t  = disagree_t AND (u_t < q_t)

This is pure budget pacing. It depends on the stream only through the disagreement rate. It is
blind to how close the deployment decision is, and to whether a label could still change it.

**Evidence.** A paired IPW e-process with a propensity-matched bet cap:

    y_s     = sgn(a_s) * x_s,  sgn = +1 while deployed on the incumbent, -1 after promotion
    lam_t   = clip( mu_t / (var_t + mu_t^2), 0, q_t / 2 )     (mu, var from discounted stats)
    log W  += log(1 + lam_s * y_s)

**Promotion.** Promote (or roll back, by the mirrored test) as soon as

    log W_t >= log(1 / alpha),  alpha = 0.05.

The certificate tests `H0: E[D] <= 0` for the paired advantage `D = l0 - l1` on the current
segment. It says only that the challenger **has been** better. It carries no statement about
whether switching **pays for itself** over the remaining horizon. For `kind = "P3b"` the
cost-aware branch is inactive (`self.k = 0`).

**For contrast, the repository's existing P4 (`kind = "P4"`, `self.k = 1`) does already gate on
economics:**

    promote only if  lb_value_t * min(hazard_mean, T - 1 - t) > c_s

where `lb_value_t` is a lower confidence bound on the advantage obtained from a grid of margin
nulls `H0_m: E[D] <= m`, `m in {0, step, ..., (M-1)*step}`, each run as its own wealth process
and read off at threshold `log(k / alpha)`. B3+ must be stated against P4, not only against
P3b, or its promotion rule is not new.

## 4. B3+ (P7)

Two changes. Both are small, both are measurable, and each is independently ablatable.

### 4.1 Break-even promotion with an explicit future-cost term (candidate A)

Replace P4's fixed persistence prior `min(hazard_mean, T - 1 - t)` with the **realised
remaining horizon**, and subtract the label spend the policy still expects to incur:

    H_eff_t      = T - t
    Cq_future_t  = c_q * min(rem_t, rate_t * (T - t) * p_min)
    V_hat_t      = LCB_t * H_eff_t - c_s - Cq_future_t

    promote  iff  log W_t >= log(1/alpha)   AND   V_hat_t > 0

`LCB_t` is P4's existing `lb_value()`, reused unchanged. The two differences from P4 are:

- **(i) horizon.** `T - t` is `F_t`-measurable and exactly known in this protocol; it is not a
  declared hazard prior. Under a shorter horizon the same evidence buys less, so promotion is
  correctly withheld late in an episode.
- **(ii) future label spend.** Promotion commits the policy to continued certification spend
  (rollback monitoring). `Cq_future_t` prices that. P4 ignores it.

`Cq_future_t` uses the propensity floor as the lower bound on continued spend, which makes it a
conservative (under-)estimate of future spend and therefore makes promotion slightly easier,
not harder, than a full accounting would.

**Validity statement actually supported.** Each margin null `H0_m: E[D_t | F_{t-d-1}] <= m` has
a nonnegative-wealth e-process, because `lam in [0, q/2]` and `|x| <= 1/q` give
`1 + lam*y >= 1 - (q/2)(1/q) = 1/2 > 0`. The margin grid is ordered: wealth at margin `m` is
nonincreasing in `m`, so the rejected set is a prefix and a single threshold `log(k/alpha)`
controls the family; `lb_value` then reports `(c - 1) * step`, one grid step inside the
rejected prefix, which is conservative. This yields a time-uniform lower confidence bound on
the conditional mean advantage at level `alpha`.

**What it does not yield.** `V_hat_t > 0` is an *economic decision criterion*, not a
certificate about future returns. Reading `LCB_t * H_eff_t` as realisable future benefit
requires the persistence assumption

    E[D_u | F_t] >= E[D_t | F_t]  for u in (t, T],

i.e. the advantage does not decay over the remaining episode. That assumption is **stated, not
established**, and is exactly what the Phase 5 reversal experiment probes. No theorem is
claimed for it.

### 4.2 Decision-value-aware acquisition (candidate B)

This is the component with no counterpart in P3b or P4. P3b's pacer spends the budget at a
rate set only by the disagreement rate. B3+ multiplies it by a **decision-relevance factor**
computed from quantities already available at issue time:

    gap_t = c_s + Cq_future_t - LCB_t * H_eff_t          (distance to break-even; <0 means past it)
    UCB_t = upper confidence bound on the advantage from the same margin grid

    r_t = r_floor                     if UCB_t * H_eff_t < c_s        (cannot repay: give up)
        = clip(r_max * exp(-|gap_t| / (kappa * c_s)), r_floor, r_max)  otherwise

    q_t = clip( r_t * rem_t / max(rate_t * (T - t), eps), p_min, 1 )

Defaults: `r_floor = 0.25`, `r_max = 2.0`, `kappa = 1.0`. Behaviour:

- **Hopeless regime.** If even the optimistic advantage cannot repay `c_s` within the remaining
  horizon, no additional label can change the deployment decision this episode. Acquisition
  drops to the floor and the saved budget is simply not spent. This is where the label savings
  come from.
- **Near the boundary.** When `|gap_t|` is small the decision is genuinely uncertain and a label
  is decisive, so acquisition is boosted up to `r_max`.
- **Far past the boundary.** Once promotion is clearly warranted, additional evidence is
  redundant for the promotion decision and acquisition relaxes toward the floor (rollback
  monitoring is retained by the floor itself).

**Constraints this respects, by construction.**

1. `r_t` is a function of `LCB_t`, `UCB_t`, `rem_t`, `rate_t`, `t` only. All are measurable with
   respect to `F_{t-d-1}`. No unreleased or future label enters `q_t`.
2. `q_t >= p_min > 0` for every eligible disagreement event while budget remains, so every
   queryable event keeps positive propensity and the IPW increments stay unbiased with bounded
   weights.
3. The realised issue-time propensity `q_t` is stored per acquired label and is the value used
   both in `x_t = (l0 - l1)/q_t` and in the bet cap `q_t / 2`. The cap-to-propensity match that
   makes P3b's wealth factors nonnegative is preserved exactly.
4. The hard budget is unchanged: `ask_t` requires `rem_t > 0`, and `rem` decrements on request.
   `r_t` can only re-time spend within the budget, never exceed it.

### 4.3 Persistence (candidate C) - ablation, not a contribution

A rolling/discounted advantage test that postpones promotion when the challenger's edge is
weakening is close to what the repository's P4 already provides via its margin grid and
mirrored rollback. It is therefore implemented as an **ablation switch** on P7 and compared to
P4, and is not claimed as novel unless Phase 1 selection shows it carries independent value.

## 5. Variant table for Phase 1 selection

| Code | Promotion | Acquisition | Role |
|---|---|---|---|
| P3b | `log W >= log(1/a)` | budget pacer | reference |
| P4 | `LCB * min(hazard, T-1-t) > c_s` | budget pacer | existing cost-aware comparator |
| P7a | break-even `V_hat > 0` | budget pacer | candidate A alone |
| P7b | `log W >= log(1/a)` | decision-value | candidate B alone |
| P7 | break-even `V_hat > 0` | decision-value | full B3+ |
| P7c | break-even + persistence | decision-value | candidate C add-on |

Selection order is the Phase 1.3 order: net-cost improvement, then simplicity, then mechanism
clarity. A combination is retained only if its interaction adds measurable value over the better
single component.
