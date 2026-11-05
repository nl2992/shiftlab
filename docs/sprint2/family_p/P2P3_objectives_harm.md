# P2 (conditional vs marginal objectives) and P3 (economic cost of false promotion)

**Runs.** `fam_p.py p2p3` produced `outputs/sprint2/P/p2p3/p2p3.json`.

* Synthetic first-order Markov episodes over a reduced, targeted grid at 12 seeds each: p in
  {.5, .65} crossed with rho in {0, .8, .95} and delay in {1, 100} (12 settings), plus p=.45 at
  rho in {.8, .95} and delay in {1, 100} (4 settings), for 16 settings total. This yields 10
  p<=.5 null settings and 6 alternatives; it is not the full 18-cell Cartesian grid. The evaluator
  keeps the sign path.
* Twin known-null streams: 40 evenly spaced episodes per dataset.
* Policies: A5b, D2, QSG, RMM(gated), gated_adaptive_range+front, P3_follow and never switch, plus
  the P1/P6 candidates on the twins.

## P2: definitions

* **V2 error.** The method promotes on an episode whose marginal p <= 1/2.
* **V1 error.** The method promotes at τ while the conditional advantage over the next 500 events is
  <= 0. That advantage is computed by the evaluator from the true (p, rho), given the method's own
  last released queried outcome and its age.
* **Realised post-promotion advantage.** A_H = Σ_{t=τ}^{τ+H-1} (l0_t - l1_t), using the
  half-open event window [τ, τ+H) and truncating at the episode end. This is an evaluator-side
  realised sum; it is distinct from the conditional-mean targets Cstate_H and Cpol_H.

## P2: results

V1 and V2 error rates on p <= .5 episodes, pooled over rho and delay (12 seeds × 10 null settings,
120 episodes per policy). V1 is the fraction of episodes with at least one promotion whose
policy-filtration conditional 500-event advantage `Cpol500` is <= 0; V2 is the fraction of episodes
with any promotion. Multiple promotions within an episode count at most once in either rate:

| policy | V2 | V1 |
|---|---|---|
| A5b | 0 | 0 |
| gated_adaptive_range+front | .175 | .067 |
| RMM (gated) | .308 | .125 |
| D2 | .308 | .142 |
| QSG | .358 | .183 |
| P3_follow | 1.0 | .60 |

* **V1 versus V2.** About half of each iid-certified method's marginal errors are not conditional
  errors: the promotion followed a favourable run that, given the information available, really
  did predict short-term advantage. The two error rates measure different hypotheses and are not
  interchangeable.
* **Which target predicts A_500.** The descriptive correlation of realized A_500 across promotions
  is similar for marginal target M, oracle-state conditional target Cstate, and policy-filtration
  conditional target Cpol:
  * .86 at rho = 0;
  * .71–.74 at rho = .8;
  * .24 for all three at (rho = .95, delay 1); at (rho = .95, delay 100), M=.52, Cstate=.53,
    and Cpol=.52.
  * For the policy-filtration target, the finite-horizon difference is
    `Cpol_H - M_H = 2·dis·(z-p)·rho^g·(1-rho^H)/(1-rho)`, where `z` is the last queried sign and
    `g` its age at promotion. This makes the difference small when the label is stale
    (`rho^g` is small). Correlation similarity is descriptive; it does not establish equality of
    the targets or their causal/economic adequacy.
* **Where the conditional target matters economically.** The mean A_500 after a promotion on p = .5
  nulls is +8.6 at (rho = .95, delay 1) but -2.9 at (rho = .95, delay 100) and about 0 elsewhere.
* **Twin real streams.** The marginal target is 0 by construction. Even so, every certified method's
  post-promotion A_500 is positive on average: A5b +19.2 (67% of promotions positive), GAR+front
  +13.1 (83%), RMM +6.1 (82%), D2 +9.2 (76%). This agrees with the sprint-1 twin finding.
* **Decision.**
  * At a single promotion, the economically relevant objective is the conditional,
    horizon-limited advantage.
  * That objective only departs from the marginal one when label delay is short relative to the
    persistence time, 1/(1-rho).
  * Under the tested synthetic contract (delay 100, rho <= .95), the M and Cpol correlations with
    realized A_500 are close in these samples. This does not make the V1 and V2 nulls equivalent.
    Their relevance still depends on the deployment estimand and available information.
  * On the reused real twin streams, selected promotions had positive mean realized A_500 for the
    four displayed certified methods (A5b +19.2, GAR+front +13.1, RMM +6.1, D2 +9.2). These
    conditional-on-promotion averages do not estimate persistence duration or establish transfer.

## P3: realised harm of erroneous promotions

ΔJ against never switch, cs = 5, on p <= .5 episodes that promoted (NaN = no promotion):

| policy | rho | p=.45, d=1 | p=.45, d=100 | p=.5, d=1 | p=.5, d=100 |
|---|---|---|---|---|---|
| D2 | .8 | 23.8 | 48.5 | 0.6 | 52.1 |
| D2 | .95 | -12.6 | 37.0 | -10.5 | 37.6 |
| QSG | .95 | -0.5 | 40.3 | -2.7 | 14.9 |
| GAR+front | .95 | -5.2 | 83.4 | -1.4 | 19.1 |
| RMM | .95 | 2.2 | 52.6 | 21.0 | 15.0 |
| P3_follow | .8 | 150.8 | 186.4 | 151.6 | 172.0 |

**Simple harm model.**

* harm per false promotion ≈ cs·(1 + rollbacks) + dis·(1-2p)·(time on the challenger) - persistence
  bonus.
* The persistence bonus is about dis·rho^d/(1-rho) per refresh. It is non-negligible only when the
  delay d is small relative to the persistence time.
* Measured in the displayed promoted cells: at delay 100, certified-method ΔJ ranges from +14.9 to
  +83.4. At rho=.95 and delay=1, outcomes vary by method and p (from -12.6 to +21.0); they are not
  uniformly near zero or negative.

**Where aggressive switching wins.** P3_follow is the uncertified follow-the-last-2-labels control.

* **Its margin against the best other policy, per (p, rho, delay, cs) setting:**
  * It wins at rho = .95 with delay 1 and cs <= 2 for every tested p (margins -11.6 to -79.5),
    and at the additional low-cost setting p=.50, rho=.80, delay=1, cs=.5 (margin -1.8).
  * At rho=.95, delay=1 and cs=5, it loses by +19.5 to +53.1. At delay=100 it loses across
    all tested p/rho settings: margins are +14.0 to +669.5 over the reweighted switch costs
    cs ∈ {.5, 2, 5, 20}. Across the full grid, the largest loss margin is +738.4 at
    p=.50, rho=0, delay=1, cs=20.
* **Best policy by setting:**
  * nulls (p <= .5): never switch, except (rho = .95, delay 1, cs <= 2) → P3_follow, and
    (rho = .95, delay 1, cs = 5) → D2;
  * alternatives: D2 at delay 1, QSG or D2 at delay 100.
* **Conclusion.** Under the frozen contract (cs = 5, delay 100), more aggressive switching is never
  economically better. In this finite sweep, it is better only in the specific short-delay,
  low-switch-cost settings listed above; do not generalize those cells into a broad operating rule.
  Cost-sweep rows are reproducibly reweighted from the fixed cs=5 trajectories in
  `P3_cost_sweep.json`; policies were not rerun at each switch cost.
