# Arm-by-arm validity table (Stage 0, T0.7)

**Status: reviewed, 2026-10-28.** Drafted by a Sonnet subagent, spot-checked by the lead, then audited by Codex (read-only, xhigh) against the cited code; every Codex finding was lead-verified and applied (Section 12). Read-only audit of code and existing reports, plus one
tiny CPU check (Section 7). No experiment was run and no existing file was edited. Every claim
cites `file:line` in the working tree at the time of writing. Where something could not be
determined from code, the entry says "unknown, needs check".

This table finishes the proof obligation left open in `REFINEMENT_ROUND_2.md:99-113` and in
`ADVERSARIAL_REVIEW_2.md` (MAJOR 1: "Xu/PPE rows" and "the reference-policy training channel").
Calibration tables supplement these arguments and cannot replace them (review remedy). Lemma L
(`LEMMA_L.md`) is a pathwise identity and gives no validity; nothing below relies on it.

## 0. Setting, notation and the common arguments

- **Null (charter, `docs/research_charter.md:37-45`).** `Z_t = c(pi_t(X_t),Y_t) - c(pi_ref(X_t),Y_t)`.
  `H0: E[Z_t - eps | F_{t-1}] <= 0`, with `eps = 0.1` throughout (`gated_monitor_comparison.py:68,148`;
  `integrated_pipeline.py:51` `HARM_MARGIN = 0.10`; WP4 primary `EPSILONS = (0.1, 0.0)`,
  `eia_validity_analysis.py:24`). `|Z_t| <= C = 5` (max of FN, FP cost).
- `D_t = 1{pi_t(X_t) != pi_ref(X_t)}` is a function of `X_t` and the two policies, so it is known
  at decision time. `Z_t = 0` when `D_t = 0` (true by construction of the paired cost).
- `V_t` is the increment, `B_t` the normalising bound, `W_t = prod (1 + c V_t / B_t)` for stakes
  `c` in `(0.05, 0.1, 0.2, 0.4, 0.8)` (`predictable_bound_replay.py:10`, `eprocess.py:122`).

**CA-1 (HT / PPI unbiasedness).** Suppose `q_t` is `sigma(F_{t-1}, X_t)`-measurable, the anchor `A_t`
is `sigma(F_{t-1}, X_t)`-measurable, and the coin `U_t` is independent of `Y_t` given
`(F_{t-1}, X_t)`. Let `L_t = D_t 1{U_t < q_t}`. On `D_t = 1`,
`E_U[A_t - eps + L_t (Z_t - A_t)/q_t | F_{t-1}, X_t, Y_t] = Z_t - eps`. On `D_t = 0` the increment is
`-eps = Z_t - eps` because `Z_t = 0`. So `E[V_t | F_{t-1}, X_t, Y_t] = Z_t - eps` and
`E[V_t | F_{t-1}] = E[Z_t - eps | F_{t-1}] <= 0` under H0. The current disagreement `D_t` multiplies
`q_t` and this is harmless **only because `Z_t = 0` whenever `D_t = 0`**.

**CA-2 (bound).** If `B_t` is `F_{t-1}`-measurable and `|V_t| <= B_t`, each factor `1 + c V_t/B_t` is
nonnegative with conditional mean at most 1, so each component and the fixed mixture are test
supermartingales and Ville's inequality gives `P(sup W >= 1/alpha) <= alpha`. If `B_t` depended on
`X_t` or `D_t`, `E[V_t|F_{t-1}] <= 0` would **not** imply `E[V_t/B_t | F_{t-1}] <= 0`; this is the
failure mode the repository itself warns about (`eprocess.py:102-116`, `comparison_betting_engines.py:33-41`).

**CA-3 (stopping).** A stop determined by past spend or past label count only truncates a
supermartingale at a predictable time, which preserves validity (allocation equivalence is lost,
as in `LEMMA_L.md:67`).

## 1. Verdict summary

| # | Arm | Where | Verdict |
|---|---|---|---|
| 1 | `gated_ht_paced` | `gated_monitor_comparison.py:190-213` | **VALID** (CA-1..3; synthetic S3 design) |
| 2 | `gated_ht_fixed` | same, `:190` `pacer.fixed` | **VALID** |
| 3 | `gated_ppi_paced` | same, `:176,191-192,217` | **VALID** (adds past-only proxy ordering) |
| 4 | `gated_eb_paced` | same `:183,210`; `eprocess.py:314-383` | **VALID** (PM-EB algebra checked below) |
| 5 | `uniform_ppi` (+ `_common96p9`) | `hard_budget.py:279-628` | **VALID** |
| 6 | `variance_ppi` | same | **VALID** (`q_t` depends on `X_t`, bound constant) |
| 7 | `full_feedback` | `gated_monitor_comparison.py:424` | **VALID** (not a sampling scheme; labels every event) |
| 8 | Engine `fixed08` (default mixture) | `comparison_betting_engines.py:76-77` | **VALID** |
| 9 | Engine `fixed1` | `:78-84` | **VALID** (stake 1 can zero a component; mixture stays nonnegative) |
| 10 | Engine `plugin` | `:85-87`; `eprocess.py:232-311` | **VALID** |
| 11 | Engine `pm_eb` | `:88-90` | **VALID** |
| 12 | Engines `timans_approx_grapa`, `timans_grapa` | `:92-102`; `scripts/reproduce_timans_...py:69-126` | **VALID** (bets predictable; 100-calendar-event burn-in is a power issue, not a validity issue) |
| 13 | `ppe_uniform` | `gated_monitor_comparison.py:346-383` | **VALID, but an ALIAS** of `uniform_ppi` (single stake 0.9) |
| 14 | `xu_active` | same | **VALID, but an ALIAS** of `variance_ppi` (single stake 0.9 x Xu cap) |
| 15 | `ppe_gated` | `:411-423` | **VALID, but an ALIAS of `gated_ppi_paced`** (not of gated HT); the PPE module is never called |
| 16 | `ppe_fixed_stake` (older grid arm) | `risk_proxy_monitor_grid.py:241-286` | **VALID-CONDITIONAL**: predictor is fit on pre-monitor labels only (`:150-156`, `train_end < monitor_start`); provenance resolved in review |
| 17 | `feature_adwin` | `gated_monitor_comparison.py:37-59,475-495` | **DESCRIPTIVE-ONLY** (different target, no anytime-valid guarantee) |
| 18 | WP4 `ungated_ht`, `gated_ht_fixed`, `gated_ht_paced`, `gated_eb_paced`, `full_feedback` | `orientation_replay.py`, `eia_validity_analysis.py` | **VALID-CONDITIONAL**: mechanics verified by random orientation; the null against a moving weekly-refit reference is not verifiable |
| 19 | WP4 unmodified and injected analyses | `eia_validity_analysis.py:227-382` | **DESCRIPTIVE-ONLY** |
| 20 | `PPRMRiskMonitor` | `pprm_risk_monitor.py:99-153` | **VALID-CONDITIONAL for a different null** (running-mean predictive risk); **NOT ESTABLISHED / DESCRIPTIVE-ONLY** for the charter null |
| 21 | Integrated Q1 monitor | `integrated_pipeline.py:681-710` | **VALID** (ungated HT, constant `q = 0.40`) |
| 22 | Integrated Q2 scout + certification | `budgeted_promotion.py:1011-1241` | **VALID-CONDITIONAL for the code-defined null `E[I_t(g_t - s) \| F_{t-1}] <= 0`** (switch rate charged only on selected contexts, `:1152`). **NOT a full-cost net-benefit certificate** (`E[I_t g_t - s \| F_{t-1}] <= 0`); integrated utility charges the full switch (`integrated_pipeline.py:906`). Uniform-query path only |
| 23 | Integrated Q2 fixed-candidate certification | `integrated_pipeline.py:270-341` | **VALID** (after the cap, wealth cannot increase before termination) |
| 24 | Integrated Q3 rollback | `integrated_pipeline.py:826-861` | **VALID-CONDITIONAL**: candidate must be frozen at 2400 |
| 25 | Controller / `q1_fallback` / `scheduled_promote` | `integrated_pipeline.py:211-267,877-879` | **No utility or regret guarantee.** `q1_fallback` inherits Q1's false-escalation bound; controller promotion requires Q2 certification (`:797,877`; `controller.py:65`). `scheduled_promote` is **uncontrolled** |
| 26 | Q1 -> Q2 -> Q3 composition ("familywise <= 0.05") | `integrated_null_calibration_protocol_v1.md:10` | **CONDITIONAL, NOT YET ESTABLISHED**: a union bound over distinct error events is valid *if* each later stage is conditionally valid after earlier decisions (the protocol's own argument); that stage-conditional validity is the open obligation |

## 2. S3 gated arms (rows 1-4)

All four share `replay_gated` (`gated_monitor_comparison.py:136-236`). Costs are read only on
queried disagreements (`:193-194`); `gated_increment` returns `-eps` on agreements and raises if a
label is supplied for an agreement (`:73-76`).

| Field | `gated_ht_paced` | `gated_ht_fixed` | `gated_ppi_paced` | `gated_eb_paced` |
|---|---|---|---|---|
| Null tested | `E[Z_t-eps\|F_{t-1}]<=0`, immediate queried feedback | same | same | same |
| Increment `V_t` | `-eps` (agree); `-eps` (unqueried disagree); `Z_t/q_t - eps` (queried) (`:79-83`, anchor 0) | same | `pred(X_t) + (Z_t-eps-pred)/q_t` queried, `pred` unqueried disagree, `-eps` agree (anchor `= pred+eps`, `:192`) | same increments as HT paced, engine differs |
| `q_t` depends on | past 200-event window of `D*tariff` and validation seed (`:99,104`); **not** on `X_t`, `D_t` or `Y_t` | constant `min(1, target/mean(active*cost))` from validation `[400:800]` (`:100`) | as paced | as paced |
| Bound depends on | `5/q_t + eps` (`:191`) = function of `q_t` only | same, `q_t` constant | `(5+eps)(2/q_t - 1)` (`:191`) | engine is fixed `[-1,1]` on `V/B` (`:183,210`) |
| Bet and bound `F_{t-1}`-measurable | **Yes.** `q = pacer.propensity` is read at `:190` before `pacer.observe` at `:224`; the bound at `:191` uses only `q`; stakes are fixed constants (`eprocess.py:122`). `X_t`, `D_t` and `Y_t` do not enter `B_t`. | **Yes** (constant) | **Yes.** The anchor depends on `X_t` (`:192`) but only enters `V_t`, never `B_t` | **Yes.** PM-EB stake uses `n_updates` and past observations only (`eprocess.py:352-356,376-382`) |
| Query coin independent of outcome | `uniforms = default_rng(seed+9173).random(3200)` (`:282`), independent of the data generator; `query = active & (coin < q)` (`:193`) | same | same | same |
| HT / PPI unbiasedness | CA-1 with `A_t = 0`; relies on `Z_t = 0` on agreements. `replay_gated` does **not** assert this (only `orientation_replay.py:119` does); in S3 it holds by construction (`comparison_seed:273`, identical actions give identical costs) | CA-1 | CA-1 with `A_t = pred(X_t)+eps`; bias of a poor proxy does not matter for validity | CA-1 |
| Proxy / anchor uses only past labels | n/a | n/a | **Yes.** `proxy.predict` at `:192` precedes `process.update` (`:209-213`); `proxy.observe(features[i], observed-eps)` at `:217` runs only after the update and only if queried; refit every 20 observations (`proxy.py:91-95`), so event `t+1` sees labels `<= t`. Base fit uses events `[0,400)` and `[400,800)` (`comparison_seed:275-280`), disjoint from the monitored events `>= 800`. Clip guard `proxy.clip <= 5+eps` (`:179`) | n/a |
| Reference-training channel | `reference = _source_action(x,scenario)` (`comparison_seed:269`; `decision_harm_experiment.py:161-164`) is an analytic cost-minimising threshold. **No training. Frozen.** `deployed` is also analytic (`:266`); in `harmful_adaptation` it switches to action 1 at fixed index 1600 (`:267-268`), a predictable, deterministic change of `pi_t` | same | proxy is trained on pre-monitor paired costs only (above). `pi_ref` frozen as left | same |
| Stopping / reserve | `if budget - spent + 1e-12 < 2.5: break` (`:188`), past spend only, CA-3 | same | same | same |
| Calibration (S2) | 23/16,000 alarms; max simultaneous exact upper 0.764% (`outputs/gated_monitor_null/analysis/summary.csv`; `docs/gated_monitor_null_calibration_results.md`) | 28/16,000; 0.764% | 25/16,000; 0.764% | 0/16,000; 0.253% |
| Verdict | **VALID** | **VALID** | **VALID** | **VALID** |

**PM-EB check (`eprocess.py:366-383`).** With `x = (V/B+1)/2` in `[0,1]` and the null mean at most `1/2`,
the increment `stake*(x-1/2) - 4*(x-mu_prev)^2*psi(stake)`, `psi(l) = (-log(1-l) - l)/4`, with
`mu_prev` the prior smoothed mean (`:372-374`, updated after at `:378`), is the
Waudby-Smith and Ramdas predictable-EB form. Since the conditional mean is `<= 1/2`,
`exp(stake*(x-1/2)) <= exp(stake*(x-m_t))` with `m_t` the true conditional mean, and the standard EB
supermartingale inequality applies. Stake is capped at 0.5 (`:331-337`). This depends on the cited theorem, not on a
repository proof; the repository check is the S2 count above.

**Point (a), bound versus current context.** In none of the four arms does `B_t` contain `X_t` or
`D_t`. `D_t` enters only through `query = active & (coin<q)` (`:193`), which CA-1 covers.

**Point (b), PPI proxy ordering.** Verified in the table above (`:192` before `:209`; `:217` after).

**Remaining conditions (all arms in this section).** (i) The null is an assumption about the
data-generating process; in S2 it is imposed by the stationary and benign scenarios (Section 7);
(ii) immediate feedback; (iii) `Z_t = 0` on agreements; (iv) `|Z_t| <= 5`, enforced at `:195-196`.

## 3. Ungated and full-feedback arms (rows 5-7)

All three come from `hard_budget._one_method` (`hard_budget.py:279-628`) or the full-feedback replay
(`gated_monitor_comparison.py:424`).

| Field | `uniform_ppi` / `_common96p9` | `variance_ppi` | `full_feedback` |
|---|---|---|---|
| Null | `E[centered_t \| F_{t-1}]<=0`, `centered = Z - 0.1` (`comparison_seed:274`) | same | same |
| Increment | `h + (Z-eps-h)/q` if queried else `h` (`:561`, `estimators.py:8-30`); **every** event, no `D_t` gate | same | `centered_t` |
| `q_t` depends on | constant `target_rate` (`query.py:65-66,92-93`; the `_common96p9` variant only changes the bound) | `clip(m*sqrt(v(x_t)), q_min, q_max)` with `v` a validation-fit random forest and a validation-fit multiplier `m` (`query.py:78-94`, fit on `[400:800]`, `hard_budget.py:378-388`): a fixed function of `X_t` | 1 |
| Bound depends on | `prediction_powered_bound(clip, min_prop)` = `5.1(2/q_min-1)`, constant (`:419-425`, `estimators.py:39`) | same with `q_min = budget/2` | constant 5.1 (`:424`) |
| Bet and bound `F_{t-1}`-measurable | Yes (fixed stakes, constant bound) | Yes. `q_t` depends on `X_t` but **the bound uses only `q_min`**, so CA-2 holds. Range guard at `:545-546` | Yes |
| Coin independent | `common_uniforms[offset]` (`:552`), the same independent stream | same | none needed |
| HT / PPI unbiasedness | CA-1 with `D_t` replaced by 1 and `A_t = h_t`; no `Z=0` argument needed | CA-1; `q_t` is `sigma(X_t)`-measurable | no correction |
| Proxy past-only | `h_now = proxy_values[offset]` (`:494`) is read before the update (`:571`); `proxy.observe` runs at `:626` after all processes update and the lookahead predictions are recomputed only for `offset+1:` (`:628`). Proxy trained on `[0,400)`; residual model on `[400,800)` and **never refit** (`proxy.py:58-62`), so stale after shift (efficiency only) | same | none |
| Reference-training channel | `reference` analytic and frozen (`comparison_seed:269`); `classifier` (LogReg on `[0,400)`, `:281`) only feeds the query score `uncertainty`, not used by `variance`/`uniform` | same | same |
| Stopping | `if remaining + 1e-12 < config.max_label_cost: break` (`:486`), past spend only | same | none |
| Calibration | 0/16,000, upper 0.253% (`_common96p9`: 0/4,000, 0.184%, budget 0.20 only) | 0/16,000, 0.253% | 48/16,000, 0.764% |
| Verdict | **VALID** | **VALID** | **VALID** (labels every event, so it is an upper reference, not a budgeted arm) |

## 4. Comparison betting engines on S3 paths (rows 8-12)

`replay_engine` (`comparison_betting_engines.py:25-102`) takes `values/bounds` and checks support
only (`:72-73`); the docstring states it cannot establish predictability (`:33-41`). Validity is
inherited from the arm that produced `(values, bounds)` (Sections 2-3) **plus** the predictability
of the engine's bet. Engines are applied to every non-EB S3 path (`gated_monitor_comparison.py:444-460`).

| Engine | Bet | Predictable? | Notes |
|---|---|---|---|
| `fixed08` (default) | five fixed stakes, equal weights (`predictable_bound_replay.py:10`) | yes (constants) | `:76-77` |
| `fixed1` | the same grid plus stake 1.0 | yes | Stake 1 gives factor `1 + V/B`, which is 0 when `V = -B`. Nonnegative, so the mixture is still a supermartingale (`predictable_bound_replay.py:46-48`) |
| `plugin` | `clip(max(0,mean)/second_moment, 0, 0.99)` from past normalised values (`eprocess.py:281-288`, cap 0.99 at `comparison_betting_engines.py:86`) | yes, stake computed before the update (`:302-304`) | |
| `pm_eb` | see Section 2 | yes | used as the engine of `gated_eb_paced` |
| `timans_approx_grapa`, `timans_grapa` | bet from running mean/variance (approx) or argmax of past log-growth over `lambda in {0.1..1.9}` (grid) of `0.5 + 0.5*V/B` (`reproduce_timans_...py:45,98-107`); null mean 0.5 | yes: the history summaries are updated only after the factor (`:109-125`); `factor >= 0.05 > 0` (grid max 1.9 x 0.5) | local replay checked against official code to `2e-5` (`:176-181`) |

**Point (c), GRAPA burn-in on calendar events.** `if time < burn_in: bet = 0.0` (`:96-97`) uses
`time`, the index into the **processed event array** (calendar events, including agreements and
unqueried disagreements), with `burn_in = 100` (`comparison_betting_engines.py:101`). The bet is the
deterministic constant 0, hence predictable and valid. The cost is power: at budget rate `r` and
disagreement rate near 8-9% (Section 7) the first 100 calendar events contain only about
`100 * 0.085 * q` labels, so the engine is blind exactly when labels are scarcest. After burn-in, the
history statistics include the near-constant `-eps/B` scores from unlabelled events, and for
approx-GRAPA the plug-in `(mu-0.5)` is negative, so the bet is clipped to 0 until the labelled
scores raise the mean above 0.5 (`:102-103`). This is a validity-neutral but allocation-dependent
behaviour, and it interacts with the fixed-versus-paced contrast of H-B2.

**Calibration (S2).** `gated_ht_paced__fixed1` 60/16,000 (1.115%); `__plugin` 14 (0.613%);
`__timans_approx_grapa` 8 (0.449%); `__timans_grapa` 63 (1.047%); `full_feedback__fixed1` 80 (1.047%);
`uniform_ppi__timans_grapa` 1/16,000 (0.358%); remaining ungated engines 0.

## 5. Aliases and the standalone Xu / PPE modules (rows 13-16)

### 5.1 What the aliases are

- **`ppe_uniform` and `xu_active`** are computed through the real `prediction_powered_factor`
  (`prediction_powered_evalues.py:30-67`) and `xu_paired_betting_factor` (`xu_active_betting.py:47-93`)
  (`gated_monitor_comparison.py:354-371`) and then **asserted equal to `1 + 0.9 * V/B`**, the
  `uniform_ppi` / `variance_ppi` increment, to `1e-12` (`:373`). They are therefore the
  same increments as the PPI arms with a **single stake 0.9** instead of the five-stake mixture.
  Algebra: with `b = 0.9/(2/f-1)` and `f = q_min`, the PPE factor `proxy + (obs - proxy)/q` is affine in the
  score, so correcting the factor equals applying the stake to the corrected score.
  For `xu_active`, `lambda/(2B) = 0.9/(5.1(2/f-1)) = 0.9/bound`.
- **`ppe_gated`** is `1 + 0.9 * result.increments / result.bounds` of **`gated_ppi_paced`**
  (`:411-423`); the PPE module is **not called** on this path, so its propensity-floor check is not
  exercised. It is **not** algebraically identical to gated HT: it inherits the proxy anchor and the
  bound `(5+eps)(2/q-1)`, whereas gated HT has anchor 0 and bound `5/q+eps` (`:191`). Reading it as
  PPE with a predictable stake `lambda_t = 0.9 q_t/(2-q_t)` is exact and nonnegative, because the PPE floor
  `1.8q/(2-0.1q) <= q` for `q <= 2`. These three should be reported as aliases, not independent methods
  (`ADVERSARIAL_REVIEW_1.md:221`).

### 5.2 Validity entries

| Field | `ppe_uniform` | `xu_active` | `ppe_gated` |
|---|---|---|---|
| Null | as `uniform_ppi` | as `variance_ppi` | as `gated_ppi_paced` |
| Increment | `1 + 0.9 est/bound` (`:373`) | same | `1 + 0.9 V/B` (`:412`) |
| `q_t` depends on | const | `X_t` through the validation-fit RF (variance policy, `variance_power` default 0.5 matches Xu's `sqrt` allocation, `query.py:35`) | past window |
| Bound / bet depends on | constant `5.1(2/q_min-1)`, constant stake | same | `q_t` only |
| `F_{t-1}`-measurable | yes | yes | yes |
| Coin | independent (same stream) | same | same |
| Unbiasedness | CA-1 | CA-1 | CA-1 with anchor |
| Proxy past-only | online proxy updated after the update (`hard_budget.py:626`) | same | as `gated_ppi_paced` |
| Reference channel | frozen, analytic | frozen | frozen |
| Stopping | past spend (`hard_budget.py:486`) | same | `:188` |
| Calibration (S2) | 6/16,000, upper 0.533% | 0/16,000, 0.253% | **151/16,000, upper 1.953%**, the largest in the panel (24/2,000 in each of six cells) |
| Verdict | **VALID (alias)** | **VALID (alias)** | **VALID (alias of `gated_ppi_paced`)** |

### 5.3 Point (d), Xu minimum propensity versus the policy actually used

- Source restriction (theta = 1/2): `q_min >= lambda/(1 + lambda/2)`, equivalently
  `lambda <= 1/(1/q_min - 1/2)` (`xu_active_betting.py:27-44`; audit `docs/xu_active_betting_paper_to_code_audit.md`).
- Policy used: `AdaptiveQueryPolicy("variance")` clipped to `[q_min, q_max] = [budget/2, 0.8]`
  (`query.py:94`; `hard_budget.py:547` asserts the range).
- Stake used: `0.9 * xu_maximum_stake(floor)` (`gated_monitor_comparison.py:368`), i.e. 10% inside
  the cap. Required floor `lambda/(1+lambda/2) < floor`.
- Enforcement: `xu_paired_betting_factor` raises if `propensity < xu_minimum_query_probability(stake)`
  (`xu_active_betting.py:70-71`) on **every** event of the alias path (`:364-371`). So the clipped
  policy is checked per event, not assumed.
- Caveats. (1) Xu's own `xu_variance_query_policy` wrapper (`xu_active_betting.py:142-167`) is used only
  in tests (`tests/test_xu_active_betting.py:188`); S3 uses the underlying policy directly. (2) The
  residual-moment model is fit once on `[400:800]` while the proxy refits online, so the allocation is
  not Xu's optimum; this affects efficiency, not validity. (3) Xu et al.'s own theorem is IID-specific
  (audit, last paragraph); here validity rests on CA-1..3, not on that theorem. (4) The
  `XuActivePairedEProcess` class (`xu_active_betting.py:96-139`) is not used by S3.

### 5.4 Standalone `prediction_powered_evalues.py` / `ppe_fixed_stake`

`ppe_fixed_stake` (`risk_proxy_monitor_grid.py:241-286`): fixed stake `PPE_STAKE = 0.1`, base factor
range `[0.9, 1.1]`, floor `1 - 0.9/1.1 = 0.1818` (`ppe_paper_implementation_audit.md`, in
`papers/shiftguard_unified/`), constant `query_rate`. Unbiasedness is CA-1 with a constant `q`. The
audit says the proxy is "a frozen pre-monitor prediction"; in the code the proxy array `h` is
precomputed before the loop (`:228`), but I did not trace how `h` was built. **Unknown, needs check:**
that `h` was fit only on pre-monitor events. Reported calibration is outside this table's source
set (`papers/shiftguard_unified/method_decision.md:310`: 0/1,000 per cell in 16 cells).
This arm is a paired-cost adaptation, not a reproduction of the PPE paper (audit, "Fidelity decision").

## 6. `feature_adwin` (row 17)

| Field | Entry |
|---|---|
| Null tested | Stationarity of the feature mean, **not** `E[Z_t-eps\|F_{t-1}]<=0`. `same_null_harm_comparator = False` (`gated_monitor_comparison.py:493`) |
| Statistic | River ADWIN on `ndtr(x)` per coordinate, `delta = 0.05/(16*3200)` (`:49-51`), fed from event 0 and scored only from `monitor_start` (`:52-58`) |
| `q_t`, bound, bet | none; label-free |
| Reference channel | none |
| Anytime validity | The docstring states "delta alone is not a proof" (`:42`). ADWIN's guarantee is per-test, not an anytime-valid e-process bound over 3,200 x 16 tests; the Bonferroni-style `delta` is a heuristic. **Unknown, needs check:** a formal time-uniform statement. |
| Calibration | 0/8,000 in S2, upper 0.219%, but only the four **stationary** cells (same 2,000 streams reused across budgets). Benign-nuisance is a true feature shift (`feature_onset = 800`, `:516`) so it is not a null for this arm |
| Verdict | **DESCRIPTIVE-ONLY.** Its alarms are a sentinel and are not harm evidence (AGENTS.md, charter). It must not be matched against harm monitors as an equal-null comparator |

## 7. WP4 EIA arms (rows 18-19)

Arms (`eia_validity_analysis.py:21-22`): `ungated_ht`, `gated_ht_fixed`, `gated_ht_paced`,
`gated_eb_paced`, plus `full_feedback`, all via the vectorised `orientation_replay.replay_batch`
that is tested equal to the scalar `replay_gated`. `gated_ppi_paced`, Timans, PPE and Xu were **not
run** on EIA (protocol Section 3; `eia_real_data_validity_results.md`, "Limits").

| Field | Entry |
|---|---|
| Null tested | Registered (a): **random orientation**. Independent signs `S_t` swap deployed and reference so the monitor sees `S_t Z_t`, `E[S_t Z_t \| path, past]=0` (`orientation_replay.py:1-8,181`). This is a conditional-on-path symmetrisation: it tests the monitor mechanics on real covariates and dependence. It does **not** test `E[Z_t - eps \| F_{t-1}] <= 0` for the actual pair |
| Increment, `q_t`, bound | `ungated_ht`: constant `q = budget_rate` (`:160`), bound `5/q+eps` (`:163`), any event. Gated arms: pacer `q` computed from `active` and past tariffs, `pacer.observe` after use (`:72-78`), bound `5/q+eps` (`:168`). `gated_ht_fixed` has `q = 1` on all four paths (rehearsal disagreement rate 0.0015 and 0.0003, `eia_real_data_validity_protocol.md`), so the HT weighting is vacuous there |
| `F_{t-1}`-measurable | Yes, same arguments as Sections 2-3. Zero-cost-on-agreement is asserted (`:119`) and in the stream builder (`eia_paired_reserve.py:155`) |
| Coin independent | Own coins from `default_rng(5920xxxx + k)` (`eia_validity_analysis.py:37-56`), independent of data by construction |
| Proxy | none (no PPI arm) |
| **Reference-training channel** | **Moving reference.** `pi_ref` is a weekly-refit Ridge (`eia_paired_reserve.py:1-4,187-188`). It is refit on **monitored-stream labels** with a 24 h delay (`evaluate_eia_retraining_frontier.py:150-189`: labels with `arrival <= current_time` enter the refit at `:183`; `predictions[index]` is stored at `:195` after the refit). So `pi_ref(X_t)` is a function of stream data up to `t - 25 h` plus `X_t`, i.e. predictable in an event-time filtration that includes demand outcomes. `pi_t` (deployed) is **frozen**: a Ridge fit on events `<= 2024-12-30` for 2025/2026 and `<= 2023-12-31` for the 2024 rehearsal (`eia_paired_reserve.py:220-245`), so deployed training does not overlap the registered paths. The null being tested in the unmodified analysis is therefore "frozen Ridge is not worse than a moving reference by more than eps", a different statement from a null against a fixed reference. The monitors treat labels as immediate, while the reference uses 24 h delay (`results.md`, "Limits"; `ADVERSARIAL_REVIEW_2.md` MAJOR 3). The reference also consumes outcome labels beyond the monitor's query budget (`ADVERSARIAL_REVIEW_2.md:271`). `tau` uses `y[fit_full]` which includes the 2024 rehearsal year (`:224`); this touches only the rehearsal, not the registered paths |
| Stopping | `stop` from cumulative past spend (`orientation_replay.py:195-196`), CA-3 |
| Calibration | 68 cells, primary `eps = 0.1`: 0/1,000 alarms in every cell, largest exact upper 0.0030. `eps = 0` boundary check: up to 28/1,000, largest upper 0.0382 (`eia_real_data_validity_results.md`). Informative only for CISO-2026 (150 disagreements); the other three paths have 1-7 disagreements and are close to vacuous. At `eps = 0.1` the sign-symmetrised null has mean `-0.1`, strictly inside H0, so the primary pass is weak evidence |
| Verdict | **VALID-CONDITIONAL.** Condition: the stated conditional null holds for the actual (frozen vs moving) pair, which the data cannot verify; the random-orientation pass certifies the code, not the real-data null. Analyses (b) unmodified and (c) injected harm: **DESCRIPTIVE-ONLY** (injected harm is imposed, onset is seasonal, `docs/eia_real_data_validity_results.md`) |

## 8. PPRM (row 20)

`PPRMRiskMonitor` (`pprm_risk_monitor.py:99-153`) and `PredictableReliance` (`:156-223`).

| Field | Entry |
|---|---|
| Null tested | Running-mean predictive risk: average block conditional mean `<= source_upper_bound + tolerance` (`PPIBlockConfidenceSequence` docstring, `eprocess.py:386-397,425`). It "does not by itself test the stronger eventwise conditional-mean null" and "does not monitor paired decision cost" (`pprm_risk_monitor.py:1-8`) |
| Increment | `eta * mean(proxy_U) + mean(true_L - eta * proxy_L)` per round (`:59-61`), `eta` clipped to `[0, max_reliance]` |
| `q_t` / label design | None. The benchmark draws 1 labelled and 15 unlabelled events per round **independently** (`scripts/run_pprm_predictive_risk_benchmark.py:20,225-245`); it assumes L and U are exchangeable draws from the round distribution (`:50-51`). There is no HT coin. This does not transfer to an event stream with selective labelling |
| Bet `eta_t` | History-measurable: `choose` is called after the current samples are drawn (script `:225,243`) but reads only stored history and counts; `update` follows (`:192-223`; script `:246,263`). Window of 60 rounds |
| Bound | Support `[-eta_max, 1+eta_max]`, constant |
| Past-only proxy | Proxy loss is the disagreement with a fixed auxiliary predictor (script `:100-104`), no training. **Frozen** |
| Source bound | `source_upper_bound` must come from an independent nominal sample and a disjoint unlabelled pool; the class cannot check this (`:103-106`). In the script it is drawn once before the stream (`:129-160`) |
| Reference-training channel | The "reference" is the source risk bound, fixed before the stream; the model is frozen |
| Stopping | none (fixed `ROUNDS = 1200`) |
| Calibration | **No calibration of `PPRMRiskMonitor` itself is recorded here.** The 0/2,000 figure in `pprm_paired_decision_benchmark.md:262-270` belongs to the paired-cost block CM-EB/mixture monitors (`:266`), not to PPRM (review correction). Error levels: test 0.025 versus source-plus-test 0.05 (`scripts/run_pprm_predictive_risk_benchmark.py:44-45,168,183`) |
| Verdict | **VALID-CONDITIONAL** for its own null (needs L/U exchangeability and an independent source bound). For the charter's decision-harm null it is **NOT ESTABLISHED / DESCRIPTIVE-ONLY**: it targets predictive risk, which is a different quantity from `R_t(pi_t) - R_t(pi_ref)` |

## 9. Integrated pipeline (rows 21-26)

Constants: stages `800/1600/2400/3200` (`integrated_pipeline.py:37-42`); alphas 0.02 (Q1), 0.015
(Q2), 0.015 (Q3) (`:52-54`), **not** 0.05 each; margin 0.10; query rates 0.40 monitor and 0.20
rollback, caps 320 and 160 labels (`:43-49`). Coins `default_rng(seed+700001).random(n)` (`:671-672`),
indexed by absolute event, so each stage uses disjoint coins.

| Field | Q1 monitor (row 21) | Q2 scout + certification (rows 22-23) | Q3 rollback (row 24) |
|---|---|---|---|
| Null | `E[Z_t - 0.1 \| F_{t-1}] <= 0`, incumbent vs frozen source reference | `E[I_t (gain_t - s) \| F_{t-1}] <= 0` on the fresh block, `I_t` = context has a selected policy (Codex: not full-cost net benefit) | candidate not worse than incumbent by `0.05/800` |
| Increment | `observed_harm/0.40 - 0.1` if queried else `-0.1` (`:699-706`), ungated | `observed_gain/q - switch_rate` for contexts with a selected policy, 0 otherwise (`budgeted_promotion.py:1140-1152`; fixed-candidate `:307-313`) | `harm/0.20 - threshold` (`:855-858`) |
| `q_t` | constant 0.40 | constant `scout_rate` (`family["q_paths"]`, `:728-731`) | constant 0.20 |
| Bound | `cost_bound/0.40 + 0.1` constant (`:681-684`) | `outcome_bound/q + switch_rate` constant (`budgeted_promotion.py:1153`; `:295-298`) | `cost_bound/0.20 + 0.05/800` constant (`:826-829`) |
| `F_{t-1}`-measurable | yes | yes; stakes fixed (`budgeted_promotion.py:48`); the selected context map is fixed before the certification half starts (`:1095-1106` precedes `:1108`), scout and certification halves are disjoint events (`:1028`) | yes, provided `deployed_candidate` is fixed at 2400: it is `family["actions"][selected]`, precomputed (`:818-824`) |
| Coin independent | yes | yes | yes |
| Unbiasedness | CA-1 with `D=1`, no anchor | CA-1; selection used scout labels only | CA-1 |
| Proxy | none | none (`direct_ipw` estimator, `:589`) | none |
| **Reference / training channel** | Reference analytic (`_source_action`, `:676`). Incumbent analytic (`family["incumbent"]`, `budgeted_promotion.py:264`), with a **predetermined** switch to action 1 at index 800 or 1600 in the harm scenarios (`integrated_pipeline.py:608-621`). Candidate family trained on `[0,400)` and ranked on `[400,800)` (`promotion_grid.py:72-80,95-120`, `budgeted_promotion.py:268-290`), disjoint from every monitored event `>= 800`. **Frozen** | Candidates frozen before the monitor; the scout sees Q2-block labels only; the certification half is fresh. Candidate selection depends on scout labels, which is why the null must be stated for the *selected* map | The candidate is a frozen scout choice. `post_promotion_reversal` rewrites `y` for `t >= 2400` (`:646-657`), an evaluator-defined alternative |
| Stopping | `if q1_labels >= 320: break` before drawing the coin (`:697`), past count only, CA-3 | scout/cert: `_budget_limited_prefix_length` includes the event that reaches the cap and then stops (`budgeted_promotion.py:1001-1008`), a stopping time of past queries. Fixed-candidate: `if queried and labels >= budget: break` (`:304`) terminates at the next queried event once the cap is reached; between cap and termination only `-switch_rate` updates occur, so wealth cannot increase (review correction: an omitted HT factor could move wealth either way, so the earlier "only lowers wealth" argument was wrong) | `if rollback_labels >= 160: break` (`:850`) |
| Calibration | 0/1,000 in two cells (stationary, benign), simultaneous upper 0.4372% vs alpha 2% (`papers/shiftguard_unified/integrated_results.md:31-36`) | 0/1,000 false promotion after real selection, 0.4372% vs 1.5%; fixed-candidate 0/1,000, 0.2991% (`:58-62`). Eligibility used an evaluator-side pointwise null check | 0/1,000 false rollback for eligible beneficial deployments, 0.4372% vs 1.5% |
| Verdict | **VALID** | rows 22 **VALID-CONDITIONAL**, 23 **VALID** | **VALID-CONDITIONAL** |

**Decision rules and composition (rows 25-26), as corrected in review.**
- `_controller_decision` (`:211-267`), `q1_fallback` (`:877-879`) and `scheduled_promote` (`:766-774`)
  have no utility or regret guarantee. `q1_fallback` acts on a Q1 alarm, so its false-escalation rate
  inherits Q1's bound; controller promotion requires Q2 certification (`controller.py:65`).
  `scheduled_promote` is uncontrolled.
- The three error events (Q1 false escalation 0.02, Q2 false promotion 0.015, Q3 false rollback 0.015)
  are distinct, and all three nulls can hold at once (e.g. identical policies). A union bound
  `0.02+0.015+0.015` is a valid familywise statement **if** each later test is conditionally valid
  given earlier decisions, which is exactly the argument in
  `integrated_null_calibration_protocol_v1.md:10`. That conditional validity is not yet proved here;
  `REFINEMENT_ROUND_2.md:132` ("Not controlled; not claimed") stands until it is.

## 10. Tiny check run for this table (not part of the registered record)

CPU, 3 seeds, stationary and benign-nuisance (`_generate` as in `comparison_seed`, device cpu,
`n=3200`, `change_fraction=0.5`): mean paired cost over monitored events `[800:]` was 0.0921, 0.0525,
0.0546 (identical in both scenarios on these seeds), disagreement rate 0.080-0.088. So the S2 nulls sit
slightly inside the boundary `E[Z]=0.1` in the mean, which makes the S2 pass informative but not
extreme. Whether `E[Z_t - eps | F_{t-1}] <= 0` holds *conditionally* (per context, per pacer state) is
**unknown, needs check**. The script was a throwaway in the session scratchpad and is not
committed.

## 11. Open obligations

NOT ESTABLISHED, conditional or descriptive items that block a stronger claim:

1. **Conditional null in S2/S3.** The nulls are imposed by synthetic scenarios and checked only in the
   mean (Section 10). A per-context / per-pacer-state conditional check is unknown, needs check.
2. **Zero-cost-on-agreement.** `replay_gated` does not assert `Z_t = 0` where `D_t = 0`
   (`gated_monitor_comparison.py:136-236`); it holds by construction in S3 and is asserted only in
   `orientation_replay.py:119` and `eia_paired_reserve.py:155`. Add an assertion or a test (harmless
   if skipped, but it is the one fact that makes the `D_t * q_t` gating valid).
3. **WP4 moving reference (rows 18-19).** The real-data null against the weekly-refit reference is not
   verifiable; random orientation certifies mechanics only. Clocks for event occurrence,
   reference-training availability, monitor feedback and alarm reporting are not frozen
   (`ADVERSARIAL_REVIEW_2.md` MAJOR 3). WP4 monitors assume immediate labels while the reference uses 24 h
   delay.
4. **WP4 power of the null check.** Three of four paths have 1-7 disagreements; `gated_ht_fixed` has
   `q = 1` everywhere, so no HT weighting is exercised. Only CISO-2026 at `eps = 0` is informative.
5. **`ppe_fixed_stake` proxy provenance**: resolved in review. The predictor is fit on `[0, train_end)` with `train_end < monitor_start` (`risk_proxy_monitor_grid.py:150-156`).
6. **Aliases must be reported as aliases**, meaning the same increment path under a different betting engine (a single 0.9 stake), not equality with default-mixture wealth. `ppe_uniform` = `uniform_ppi`, `xu_active` = `variance_ppi`
   and `ppe_gated` = `gated_ppi_paced`, each at stake 0.9, are not independent methods
   (`ADVERSARIAL_REVIEW_1.md:221`). `ppe_gated` has the highest S2 alarm count (151/16,000, upper 1.953%)
   and never exercises the PPE module; its single-stake 0.9 with a wide bound is the likely reason
   (explanation not tested).
7. **Xu efficiency.** The residual-moment model is frozen at `[400:800]` while the proxy refits online;
   Xu's optimal allocation is therefore not attained. Validity is unaffected.
8. **`feature_adwin`** has no formal time-uniform guarantee and is a label-free sentinel for a different
   null. S2 covers stationary cells only (4 cells, reused streams). Keep it **DESCRIPTIVE-ONLY** and
   do not present it as an equal-null comparator.
9. **PM-EB, GRAPA and plug-in engines**: validity follows directly from predictable, admissible linear
   bets (review); no external theorem or calibration count is needed for validity, only for power. Their gated-arm validity additionally
   needs the bounds to be `F_{t-1}`-measurable (Section 2).
10. **GRAPA burn-in** (100 calendar events) is a power and allocation confound for the fixed-versus-paced
    contrast; report it as such.
11. **PPRM** tests a running-mean predictive-risk null with L/U exchangeability and an independent
    source bound; none of these carries over to the charter null. Report it only as a baseline for a
    different estimand.
12. **Q2 estimand.** The certificate tests `E[I_t(g_t - s) | F_{t-1}] <= 0`, not full-cost net benefit
    `E[I_t g_t - s | F_{t-1}] <= 0`. Example (Codex): selected mass 0.5, conditional gain 1e-4,
    `s = 0.05/800` gives certificate mean +1.875e-5 but full-cost net benefit -1.25e-5. Do not describe
    Q2 as certifying net benefit after switching cost unless the increment is changed. The generic
    eventwise path normalises by current `q(X_t)` (`budgeted_promotion.py:1128,1153,1156`) and needs a
    context-conditional null or a global bound; this table covers only the integrated uniform-query path.
13. **Integrated Q2/Q3** need the stated conditions (fresh block, frozen selection, candidate fixed at
    2400, null stated for the selected context map). Calibration used evaluator-defined eligibility and
    purpose-built null families (`integrated_results.md:50`), not a generic proof.
14. **Composition** of Q1, Q2 and Q3: valid as a union bound only once stage-conditional validity is
    shown; until then it is not claimed. Q3 must freeze the **policy rule**, not the realised future
    action vector, since actions depend on future covariates (`integrated_pipeline.py:819`).
15. **Dependence, delay, recurrence, and performativity** are outside every S2/integrated calibration
    (`integrated_null_calibration_protocol_v1.md:39`); the table is for the immediate-feedback,
    independent-block regime only.
16. **Arms not yet audited** (found in review): paired-cost block monitors and mixtures
    (`hard_budget.py:800,828,833,901`); `CertifiedPromotionRollback` (`controller.py:85,93,191,224`,
    which has its own conditional guarantees and requires caller-supplied unbiased estimates); and the
    `no_action` baseline (`gated_monitor_comparison.py:463`, no test). Add rows before any manuscript
    relies on them.
17. **Filtration and coin law.** State the filtration explicitly, and state that the query coin is
    conditionally uniform given `F_{t-1}` and `X_t`. Unbiasedness alone does not license
    current-context normalisation.
18. **Calibration is not certification.** Three-seed means do not establish the conditional null, and a
    per-context null is stronger than the charter requires. A finite calibration pass is evidence about
    the code under registered mechanisms, not proof.

## 12. Independent review record

- **Reviewer:** Codex CLI (`codex exec --sandbox read-only`, `model_reasoning_effort=xhigh`), 2026-10-28,
  audited HEAD `c3008a0` plus this draft. No raw data was read.
- **Overall verdict:** most S3 verdicts are defensible under the stated conditional null. "Continue after
  correcting the table; stop stronger net-benefit/composition claims until these obligations are
  resolved."
- **FATAL (to an interpretation, not to validity):** Q2 is not a full-cost net-benefit certificate (row 22,
  obligation 12). Lead-verified at `budgeted_promotion.py:1152` and `integrated_pipeline.py:906`.
- **MAJOR, all applied and lead-verified:**
  - the PPRM calibration was misattributed (row 20);
  - the composition argument was wrong (row 26);
  - the stopping explanation was wrong (row 23);
  - the controller verdict was too broad (row 25).
- **MINOR, applied:** the PPRM `choose()` timing; three line citations; the alias definition; the
  engine-validity source; Q3 rule freezing.
- **Missing items added:** obligations 16–18.
- **Codex agreed** with rows 1–15, 17–19, 21 and 24 as drafted.
