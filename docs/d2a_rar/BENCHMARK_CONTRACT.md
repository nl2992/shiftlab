# Benchmark contract (WP2)

Branch `research/drift2act-rar-autoresearch-2026-11-07`, base `main@7354480a`, 2026-11-07. Code:
`src/shiftlab/bench/contract/`; tests: `tests/d2a_rar/test_contract.py`; configs:
`configs/d2a_rar/{cost_vectors,stream_families}.yaml`. This document is a protocol, not a result.
Nothing here is evidence about any method.

Provenance of reused harness semantics (read from code, ported conceptually, not copied verbatim):
GAVE-R `origin/research/gave-r-2026-11-06:docs/gaver/01_HARNESS_MAP.md` (round loop `se:run` =
release labels due at t, call method, charge, schedule at t+d; cost `loss + c*N_q + s*N_s`; Family-1/3
stream cells and Markov transitions `(p(1-rho), p+rho(1-p))`; RNG `default_rng([seed, tag, crc32(id)])`;
informative delay "Family 4"; `Truth` kept evaluator-side). Source files at `main@7354480a`:
`src/shiftlab/dive/switching_explore.py` (`run`, `score_actions`), `failure_atlas.py`,
`atlas_release_hook.py`. No other branch contains an event-driven simulator with a pending queue
(`git grep` over all refs for `release_time|pending` found only the dive/DSS code above).
What is new relative to those: a policy API over a frozen observable state, guarded evaluator objects,
a full action vocabulary with per-component charging, explicit clocks, pathwise caps, an audit log with
an independent verifier, precomputed per-round potential delays/missingness (common random numbers),
and null-status truth per stream.

## 1. Two suites

**Suite A, native reproduction.** Each controller (Drift2Act, RAR, Challenger, Gong-Zhang, ASI,
Sethi) is reproduced in its own paper's setting, with its own metrics, with no normalisation and no
common cost vector. Rules, binding on the d2a / rar / sota agents:

1. Report native tasks and native metrics exactly as the paper defines them; label each item
   `PAPER_RECONSTRUCTION`, `AUTHOR_CODE`, or `PARTIAL`. Never mix a reconstruction's numbers with the
   paper's reported numbers in one table without the label.
2. A reproduction record lists: paper version/URL, equations implemented (with section numbers),
   deviations, seeds, data checksums, and which paper claims were checked vs not checkable.
3. Theory and empirics are separate columns. A guarantee is restated with its exact assumptions
   (e.g. Drift2Act's Hoeffding certificate needs uniform random sampling from the window and bounded
   means; do not assert it under serial dependence, informative selection or delayed sampling).
4. Tuning of any hyper-parameter happens on the paper's own tuning split or a dev family; the native
   test split is read once per reproduction attempt. Failures to reproduce are recorded, not tuned away.
5. Suite A numbers are never used to rank methods against each other. Only Suite B does that.

**Suite B, common operational contract.** One simulator, one action vocabulary, one cost
accounting, one set of preregistered cost vectors. A controller enters through a
`COMMON_CONTRACT_PORT` adapter (`adapters.py`) that declares (i) its vocabulary subset, (ii) its claimed
null (`cond | marg | abs_risk | none`, key into `registry/null_assumptions.yaml`), and (iii) a fidelity
note listing every simplification relative to the native method (e.g. RAR's canary traffic split is
collapsed to a single model in force). Cross-method claims require Suite B and a null-matched pairing:
never compare an invalid-aggressive method with a valid-conservative one as if equal, and never score a
conditional-null method on marginal-null false promotions.

## 2. Observable state, policy API, action vocabulary

Policy API (`simulator.Policy`): `reset(env: EnvSpec)` and `act(state: ObservableState) -> Action | list[Action] | None`.
`EnvSpec` (public): horizon T, cost vector, budget caps, clocks, observation mode, delay-information
level, allowed action subset, hurdle h. The policy never receives a `Stream`, `EvaluatorTruth` or the
simulator.

`ObservableState` S_t, frozen:

| symbol | field | content |
|---|---|---|
| m_t | `m`, `prev_m`, `retrained_ready` | model in force at the start of round t (0 incumbent, 1 candidate, 2 retrained), model retained for rollback, whether a retrained model exists |
| b_t | `b: BudgetView` | label used/cap/remaining, outstanding (pending) count, retrains/switches/rollbacks used, running retrain completion round, cooldown remaining |
| Q_t | `Q` | outstanding requests: label id, request round, release round only if `delay_info="exact"`; `.value` is a honeypot that raises `LabelNotReleased` |
| H_t | `H` | released labels, in delivery order (may be out of request order): id, request_t, release_t, observed losses `{model: loss}`, model at request, self-reported propensity |
| monitor | `x`, `x_hist` | unlabelled monitor signal of round t and read-only history; detector/belief state is the policy's own |
| labels | `available_labels` | = `len(H)` |

Action vocabulary (`query, continue, switch, retrain, alert, rollback, abstain`); each method declares
a subset (`EnvSpec.allowed_actions`; others raise `ActionNotAllowed`):

* `query(round=s, propensity=p, u_index=i)`: request the label of round s in `[t - max_lookback, t]` (default s=t,
  `ClockSpec.max_lookback=0`; Drift2Act's windowed audit sets it to its window). Released at `t + delay_s`
  (= max(t, s) + delay of round s); charged c_q at request, whether or not it ever releases (pending,
  beyond-horizon and missing labels are paid for, as in GAVE-R). The label reveals the loss of the model that
  **served** round s (routing-aware; all existing models in `shadow` mode). A round can be requested once; several
  queries per round are allowed. Out-of-window, future, repeated-round or malformed-propensity requests are refused and free.
* `route(target, fraction)`: canary traffic split (section 4b). Free.
* `continue`: explicit no-op, never charged.
* `switch(target)`: deploy model 0/1 (or 2 if a retrained model is ready and not already in force); c_s.
* `retrain`: start a retrain; completes after `retrain_duration`; c_r once, at start.
* `rollback`: return to `prev_m`; c_b. After a rollback `prev_m` is cleared (no ping-pong).
* `alert`: informational, no state effect; c_a.
* `abstain`: hand the round to a fallback; the round's loss is `fallback_loss`; c_h per abstained round (N_h counts rounds).

Feasibility (refused, logged with a reason, **never charged**): duplicate kind in the same round;
retrain while one runs or inside the cooldown; switch to the model in force or to an unready retrained model;
rollback with nothing to roll back to; more than one model-changing action in a round; a model change while
another is in flight; switch/rollback inside `switch_cooldown`.

Observation mode: `shadow` (a queried round reveals the loss of every existing model, enabling paired policy
comparisons) or `deployed` (only the model that served the label's round). In `deployed` mode the incumbent-vs-candidate
gain is **not identifiable** from labels; a method needing it must say which off-policy design it uses
(AGENTS.md rule on paired policy comparisons). Default for headline comparisons is `shadow`.

## 3. Objective and accounting

`J(pi) = sum_t l_t + c_q N_q + c_s N_s + c_r N_r + c_b N_b + c_a N_a + c_h N_h`, lower is better,
reported with the per-component breakdown (`RunResult.breakdown`).

Charging rules (enforced by `Ledger`, re-derived by `audit.verify_run`):

1. A cost is charged only for a **performed** action, exactly once per action id, at the vector's price.
2. **No switch/retrain double counting.** Every model change has exactly one initiating, paying action.
   `switch` pays c_s; `rollback` pays c_b; `retrain` pays c_r at start and its completion-deployment is
   free (`deploy_on_complete=True`; a `switch(2)` then is refused as `already_deployed`). If a study sets
   `deploy_on_complete=False`, the later `switch(2)` is a separate decision and pays c_s. Each `deploy`
   audit record carries `charged_to`; the verifier fails if two changes share a payer or a payer is unperformed.
3. The loss term uses the model actually in force (after lagged deployments), or `fallback_loss` on abstained rounds.
4. Hurdle h is a *decision* parameter published in `EnvSpec`; it is not a cost.

Safety constraints (absolute-risk requirement R_t <= tau, violation counts) are secondary metrics reported
beside J, never folded into J.

### Preregistered cost vectors (frozen, `configs/d2a_rar/cost_vectors.yaml`, sha256 verified at load)

| name | c_q | c_s | c_r | c_b | c_a | c_h | role |
|---|---|---|---|---|---|---|---|
| `label_cheap` | 0.01 | 0.5 | 10 | 1 | 0.1 | 0.05 | acquisition nearly free; stresses intervention economics (GAVE-R used c=0.01) |
| `balanced` | 0.05 | 2 | 30 | 5 | 0.2 | 0.1 | default headline vector |
| `label_dear` | 0.25 | 2 | 30 | 5 | 0.2 | 0.1 | expensive labels; stresses acquisition |
| `intervention_dear` | 0.05 | 10 | 100 | 25 | 0.5 | 0.2 | expensive change; stresses caution/rollback |

Per-round loss is in [0,1]; T=1000 unless a family says otherwise. These are stylised, not calibrated to any
real deployment; a result that holds only under one vector is reported as such. A new vector gets a new name;
existing ones never change (checksum guard). Real-dataset economics are never inferred from alarms (AGENTS.md).

## 4. Clocks

| clock | definition |
|---|---|
| request | round t at which `query` is issued for round t's label |
| observation | outcome of round t is realised at t; the system learns it only at release |
| release | `t + delay_t` (>= 1); potential delays and missingness are drawn per round **at stream creation**, so they are identical across policies (common random numbers) and independent of the policy's choices |
| deployment | `switch` effective at `t + deploy_lag`, `rollback` at `t + rollback_lag` (default 0) |
| retraining | `retrain` at t completes at `t + retrain_duration` (default 20 in the smoke env; set per study); the retrained model's loss series is `loss_retrain` |

Order within a round: retrain completion, due deployments, label deliveries (sorted by `(release_t, request_t)`),
policy decision, validation/charging, lag-0 deployments, loss.

Label-delay distributions (`DelaySpec`): `fixed`, `uniform[lo,hi]`, `geometric(mean)`, `lognormal(median,sigma)`,
`informative` (delay depends on whether the candidate is better, GAVE-R Family 4). Missingness (`MissingSpec`):
`none`, `bernoulli(p)`, `informative(p_fav, p_unfav)`.

### 4a. Retraining quality model (evaluator-side, documented, deliberately simple)

A retrain started at t uses the window `W_train = ClockSpec.w_train` (default 100), rounds `(t-W_train, t]`.
Let `e` = (number of **released** labels at t whose round lies in the window **and** in the same regime as round t) / W_train
(missing pre-history counts as unlabelled; labels from before the drift are contamination and do not count). The
completed model's loss rate is `q(e) = q_best + (q_poor - q_best) * (1 - min(1, e / e_sat))` with `q_best=0.25`,
`q_poor=0.6`, `e_sat=0.7` (RAR's theta_L), all in `StreamSpec`. Its loss on round t' is `1[retrain_u[t'] < q]` with a
stream-fixed uniform, so a model trained on more clean labels is pathwise no worse (common random numbers). `e` uses
simulator-side regime truth but only counts labels the policy actually received; the policy never sees q or the regime.
The audit's `retrain_start` record stores `label_fraction`, `clean_fraction` and `q`; `verify_run` recomputes q from
`clean_fraction` and re-derives every round's loss from the serving model. Consequence for Gate-2 economics: retraining
early on few clean labels is quick but buys a worse model. The functional form is an assumption, not a measured fact;
studies must report sensitivity to (q_poor, e_sat). Real-data retrain quality belongs to Suite A.

### 4b. Canary traffic split

`route(target, fraction=p)` sets a standing route: each round is served by `target` iff the evaluator-side draw
`route_u[t] < p` (else by the model in force); `route(..., 0)` clears it. p is the policy-declared, logged
propensity. The draw is a stream property (common random numbers), so the realised split is identical across
policies using the same p. Losses are charged per serving model; `route` has no cost term (RAR's C_a, C_r, C_b still
apply to its alerts, retrains and rollbacks). Any model change (`switch`, `rollback`, retrain deployment) cancels the
route, so RAR's stage 2 is a `switch`. The policy sees `state.route`, `state.served_hist` (who served past rounds) and
`state.routed_labels` (released labels per serving model); `RunResult.routed` gives rounds served, labels requested and
labels released per serving model. `verify_run` checks every logged round: served model = target iff `route_u < p`, and no
unlogged divergence between served and primary model.

## 5. Dependence, selection, informative missingness

* Dependence classes: `iid`; `markov(rho)` for the outcome chain, rho in {0, 0.5, 0.8} dev (0.95 stress only),
  transitions `P(Y=1|Y=1)=p+rho(1-p)`, `P(Y=1|Y=0)=p(1-rho)`.
* Out-of-order release (random delays) is part of the contract; policies receive labels in delivery order and
  must not assume request order.
* **Adaptive selection.** A policy's own query choices are adaptive; labels are observed only where it asked.
  Each query may declare a `propensity` p and a `u_index`; the simulator exposes per-round shared randomness
  `state.u` (16 i.i.d. uniforms). `verify_run` checks p in (0,1] and that every performed query with a declared p
  satisfies `state.u[u_index] < p`, so a randomisation claim that was not honoured fails the audit. This verifies that
  the claimed randomisation was used; it cannot verify that p equals the policy's marginal selection probability given
  its information. A policy that conditions on non-`u` information declares p=None, and the method's null-assumption
  entry must say selection is adaptive. Deterministic calendars declare no propensity.
  A method that treats queried rounds as an iid sample must say so in its null-assumption entry.
* **Informative missingness.** Never-released labels depend on the (evaluator-side) gain via `MissingSpec.informative`,
  and delays may depend on it via `DelaySpec.informative`. These streams are tagged in the family name and are
  reported separately; a method is not credited for validity on them unless its claimed assumptions cover them.
* Selective feedback in `deployed` mode (only the deployed model's loss is seen) is a distinct regime from `shadow`.

## 6. Statistical-null truth vs economic truth

`EvaluatorTruth` stores two separate things, both unreadable to policies:

* **Statistical-null truth** (for validity metrics). With gain `g_t = l_inc,t - l_cand,t` and hurdle h:
  H0cond: `E[g_t | F_{t-1}] <= h` for every history (for the Markov streams the sup over `Y_{t-1}` is exact);
  H0marg: `E[g_t] <= h`; absolute-risk: `R_t(incumbent) <= tau`. `truth.null_holds` gives, per stream,
  whether each holds on the **whole path**. Validity metrics (false promotion / false rollback rate) are
  computed only on streams where the method's *claimed* null holds, and a conditional-null method is never
  scored on the marg-null set (mandatory P2 correction). Example families: `iid_null_boundary` (cond and
  marg hold), `markov08_marg_null_only` (marg holds, cond fails), `iid_shift_d10` (neither).
* **Economic truth** (for J-regret): the realised loss arrays of every model, the regime path, and the true
  per-round benefit. It is used only by the evaluator (`verify_run`, regret vs an oracle). The hindsight
  oracle is labelled non-admissible; an admissible oracle (e.g. best fixed calendar) must be defined per study.

Alarms alone do not establish harm (AGENTS.md): metrics separate alarm, promotion and harm.

## 7. Budgets, audit, leakage

* Pathwise caps (`BudgetSpec`): label cap, pending cap, retrain/switch/rollback caps, cooldowns. Default
  `on_violation="raise"` -> `BudgetExceeded` at the first overspend; `"refuse"` logs and skips the action
  without charge (use this to evaluate a method that is *supposed* to respect budgets via its own logic;
  the audit still shows every refusal so silent clipping is visible).
* Audit log (schema v1, `audit.py`): JSONL records `request, release, action, deploy, retrain_start, retrain_done, leak, final`
  with fields listed in the module docstring. `verify_run(result, stream)` recomputes counts and J from
  performed actions, checks one payer per model change, checks every release is at exactly
  `request + potential delay` and never earlier, that missing labels never release, and that no leak was
  recorded. Run it in every paired experiment (`run_paired(verify=True)` does).
* Leak guards: evaluator objects derive from `Sealed`; any attribute read inside `policy.act` raises
  `LeakError` and is recorded, so a policy that swallows the exception still fails the run.
  Limitation: this catches accidental/lazy access, not adversarial code; confirmation runs should execute
  policies in a separate process that never receives evaluator objects (open question 2).

## 8. Seeds, pairing, dev vs confirmation

* A stream is a pure function of `(StreamSpec, seed)` (`make_stream`); every policy in a comparison is run on
  the same stream object per seed (`run_paired`), and results carry a stream fingerprint.
  `assert_paired`/`PairedRuns.diff` raise `UnpairedError` on differing seeds, order, spec or fingerprint.
* Paired CIs: percentile bootstrap over seeds of the mean paired difference (`paired_bootstrap_ci`, 2000
  resamples, fixed RNG). Effects are graded per the fair-evaluation standard, not a pass/fail 10% gate.
* Seed blocks (registered in `configs/seed_registry.yaml` as `d2a_rar_contract_smoke`, `d2a_rar_dev`, `d2a_rar_confirmation_reserved`; a test checks exact match and no overlap):
  smoke `110900000-110900999`, dev `110000000-110099999`, confirmation `120000000-120099999`.
* Dev families: `configs/d2a_rar/stream_families.yaml` (9 families). Confirmation families are held out:
  `load_family(..., split="confirmation")` raises `ConfirmationAccessError` unless `D2A_CONFIRMATION_UNLOCK=1`,
  and each unlocked access is appended to `configs/d2a_rar/confirmation_access.log`. The confirmation file
  `confirmation_families.yaml` does **not** exist yet; WP7 creates it at preregistration, with parameter values
  chosen outside the dev grid (new onset, delay, rho and missingness values, plus at least one held-out family
  type), and its hash is recorded in the preregistration. No tuning after a failed confirmation.
* Stage-A/B screens use dev families and the smoke/dev seed blocks only.

## 8b. WP2b changelog (2026-11-07)

Added: retrospective `query(round=)` with `max_lookback`; first-class `route` (canary split) with per-model routed-label
counts; retrain quality model keyed by clean labelled fraction in W_train; propensity verification via shared `state.u`;
independent per-round loss and serving-model verification in `verify_run`; seed blocks registered. Behaviour changes:
label observations in `deployed` mode follow the *serving* model; `Stream.loss_retrain` is replaced by `retrain_u`; the
smoke policy no longer declares a propensity (its calendar is deterministic).

## 9. Adapters

`adapters.py` defines `NativeAdapter` and stub `Drift2ActAdapter` / `RARAdapter` (status `STUB_NOT_PORTED`)
with a proposed action map (module docstring). The owning agents fill in `build(env) -> BasePolicy` as a
`COMMON_CONTRACT_PORT`; the stubs raise `NotImplementedError` until then. Policies are plain objects with
`reset`/`act`, so the Drift2Act/RAR code only needs to read `ObservableState` and return `Action`s.

## 10. Smoke check and known limits

`scripts/d2a_rar/run_contract_smoke.py` runs always-continue vs uniform-query + naive-switch (20 paired seeds,
T=1000, B=50) in about 0.7 s. It is an integrity smoke check, not evidence. Known limits: a stylised
retrain-quality model (4a); paired losses are revealed only in `shadow` mode; the monitor signal is a simple shifted Gaussian; policies get the full released-label
tuple each round (O(T) copy per round, fine for T <= ~5000); `abstain` fallback loss is a constant.
