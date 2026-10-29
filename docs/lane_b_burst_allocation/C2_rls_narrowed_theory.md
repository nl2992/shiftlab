# C2: recurrence-locked switching (RLS) on the narrowed periodic-window family

**Date:** 2026-10-29. **Gate:** C2 (`LANE_CONTROL.md`, phase C), following the NARROW verdict in
`CODEX_C0_REVIEW_1.md`. **Status:** theory memo plus a development sanity check. Not reviewed by
Codex. No novelty claim, no confirmatory evidence.

**Verdict (decisive kill test): RLS is dead as a method candidate.**

- **The estimator is the duration-aware MLE forecaster's estimator.** On this family RLS's
  estimator is the exact likelihood of the duration-aware forecaster. Its MAP *is* that
  forecaster's MLE, and its planner is the forecaster's planner.
- **The only remaining difference is the query design.** A textbook Thompson-sampling design on
  the same posterior matches or beats RLS in all 12 primary cells (`B ∈ {30, 60}`). RLS's full
  Bayesian information-gain design wins by 2–10 units only at exploratory budgets 2–4× larger
  (section 7). Both designs are standard.
- **The gate is shared.** The phase-stratified e-process gate is the standard predictable-stake
  Ville argument, which every competitor uses unchanged.
- **The C0 kill criterion fires.** RLS is therefore a standard composition of estimator, planner,
  sequential design and e-process. That is the C0 kill criterion: "a contract-matched schedule
  learner or duration-aware controller attains the same rate by standard composition".
- **What remains are supporting results, not a method.** These are: (i) an all-policy jitter
  floor, (ii) a certification floor, and (iii) a localisation bound that holds for any
  predictable causal design.

**Proved / sketched / conjectured ledger:** section 8.

**Read for this memo:**
- `C0_candidates.md` and `CODEX_C0_REVIEW_1.md` (all items);
- `LANE_CONTROL.md` (phase C);
- `docs/switching_problem_v1.md`;
- the following checkpoints in `docs/budgeted_switching_research_goals.md`:
  - historical wealth vs current-regime value;
  - Cheng audit;
  - SRR e-detector;
  - fixed-calendar e-detector bound;
  - exact-oracle continuation (the fixed-calendar/action-oracle study);
  - IID delayed terminal testing;
  - delayed-POMDP information state;
  - uniform-calendar e-detector regret;
  - positive-prefix no-go;
- `scripts/lane_b/separation_check.py` and `configs/seed_registry.yaml`, for the seeds.

---

## 0. Response to every defect in CODEX_C0_REVIEW_1

| # | Codex item | Resolution here |
|---|---|---|
| 1a | `D_post` is a legitimate but too-restrictive comparator class | Dropped. Every comparison below is against **all causal policies under the same contract**, plus a φ-oracle and a jitter-clairvoyant reference (§1.4). |
| 1b | `D_post` loophole (switch one round early with a departing-segment label) | Moot. No restricted reactive class is used in any theorem. The reactive competitor appears only as an explicit algorithm (§6.1, §7). |
| 1c | No verified prior theorem; Periodic EXP4, Cheng, Waeber–Frazier–Henderson and Hayashi et al. are the closest | Periodic EXP4 is analysed and simulated (§6.2). Cheng is the hard-budget switching reference: its fixed-action comparator is weaker than the schedule comparator, and it is not re-simulated. Bisection and active change-point localisation are replaced by a causal design with its own proof (§2). They are not cited as giving the bound. |
| 2a | Wrong jitter geometry (accumulating dwell errors) | The model is fixed to **bounded, independent, non-accumulating per-boundary jitter**: `b_j = φ + jL + η_j`, with `η_j` iid uniform on `{-σ..σ}`. Accumulating dwell `b_j = φ + jL + Σ_{i≤j} ξ_i` is excluded explicitly (§1.1). |
| 2b | Future information in the bound | Every error term uses `φ̂_j`, which is built only from labels **released before period j's decisions** (§4). |
| 2c | Chronological bisection unproved; the posterior median may be in the past | The learner can query only the current round, and candidate probe times are restricted to `[t, t+L)`. Waiting and the delay `d` are charged in calendar time. The localisation theorem (§2, Theorem L1) holds for **any** predictable design of this kind. The informative adaptive design is a heuristic whose coverage is conjectured (L3), not proved. |
| 2d | The reactive lower bound needs repair (`1/(2r)` assumes a schedule) | Withdrawn. No reactive-class lower bound is claimed. The lower bounds in §5 are all-policy. |
| 2e | Certification: labels vs calendar, budget exhaustion, divergence against the null | §3: an exact anytime power curve, a budget-exhaustion probability, and an all-policy `kl(1-β, α)` floor against an explicit member of the causal null. Labels and calendar periods are separated. |
| 2f | Charge both learner and oracle switches | §1.4 and §4: per-boundary accounting is `Δ·E|η+e| + k` for the learner and `Δ·E|η| + k` for the oracle. Both pay `2k` per deployed period. |
| 2g | No proved "iff" transition | Dropped. Only explicit, conditional statements are made. |
| 2h | Matching lower bound `Ω(SΔ min{σ,d})` plus certification power | §5: proved **against the jitter-clairvoyant reference** (Proposition E1, `g(σ,d) ≥ min(σ,d)/4`). §5.2 explains why it **cannot** hold against the φ-oracle, so it does not separate RLS from any forecaster. |
| 3 | C3 constant-sum scope; Binance and OPSD arithmetic | Out of scope for C2; the corrections are accepted as stated in the review. The Binance figure is an evidence scale (about 70% power at 3,428 labels), not a minimum. The OPSD halves are descriptive. The C3 minimax dismissal was overstated. |
| 4a | Fix known period, latent offset, emission law and jitter model; prove causal localisation and promotion validity before an efficacy grid | Done (§1–§3). The grid in §7 is a small development sanity check, not an efficacy grid. |
| 4b | Kill if a schedule learner or duration-aware controller attains the same rate by standard composition | Applied in §6.3 and §7. **The kill criterion fires.** |

---

## 1. Problem statement and comparator (deliverable a)

### 1.1 Family `F(L, W, σ, Δ, d, B, c, k, α)`

- **Rounds.** `t = 0, …, T-1`, with `T = S·L` and `S` recurrences.
- **Offset.** `φ ~ Uniform{0, …, L-1}`, unknown to the learner. `L`, `W`, `σ` and `Δ` are known
  to every learner.
- **Windows.** Window `j` is `[φ + jL + η_j, φ + jL + η_j + W)`, with `η_j` iid
  `Uniform{-σ, …, σ}`, independent of `φ`.
  - **Bounded, independent, non-accumulating jitter.** Each boundary is displaced by at most `σ`
    from its nominal position `φ + jL`, and phase error does **not** accumulate. The accumulating
    dwell model is outside this family.
  - **Both edges move together.** The window has fixed length `W`, so its up and down edges share
    `η_j`.
  - **Assumption.** `W ≥ 2σ+1` and `L - W ≥ 2σ+1`, so windows are disjoint and each has a nonempty
    deterministic core.
- **Paired loss.** `Z_t = l_t(0) - l_t(1) ∈ {-1, +1}`. Given the state path, the `Z_t` are
  independent, with `P(Z_t = +1) = (1 + μ_t)/2`. Here `μ_t = +Δ` inside a window (the candidate is
  better) and `-Δ` outside.
- **No covariate.** `X_t` is constant, so the phase is latent. With a public phase the problem is
  calendar stratification; C0 row 73.

### 1.2 Contract (`switching_problem_v1.md`, unchanged)

Order of events at the start of each round `t`:
1. Release the labels requested at `t-d` (fixed delay, in request order).
2. Choose `A_t ∈ {0, 1}` and `Q_t ∈ {0, 1}`.

Rules:
- `Q_t` queries **the current round's** common outcome. No other round can be queried.
- The budget is `Σ_t Q_t ≤ B` pathwise, counted at request time, so pending labels count.
- Costs are `c` per query and `k` per switch, with `A_{-1} = 0`. Actions do not affect outcomes.
- Decisions are measurable with respect to released labels, past actions and queries, and private
  coins.
- **Objective, relative to never switching:**
  `J(π) = E[ -Σ_t A_t μ_t + c Σ_t Q_t + k Σ_t 1{A_t ≠ A_{t-1}} ]`.

### 1.3 Risk event

- **Causal null.** `H0: E[Z_t | F_{t-1}] ≤ 0` for every `t`, where `F_{t-1}` is the full history:
  all past outcomes, queried or not, and all coins. This is the full-history conditional null of
  the contract, "no benefit anywhere".
- **Requirement.** `sup_{P ∈ H0} P(∃t: A_{t-1} = 0, A_t = 1) ≤ α`.
- **Only the first promotion is risk-controlled.** Later switching is economic; this is the
  first-promotion decomposition, C0 K2.

### 1.4 Comparators

- **`Π`**: all causal policies satisfying §1.2–§1.3, with knowledge of `(L, W, σ, Δ)`. All
  competitors in §6 and §7 belong to `Π`.
- **φ-oracle (the main comparator; information deliberately stronger than the learner's).** It
  knows `φ` but not `η`, buys no labels, and is not gated. This follows Lane A's convention.

  **Lemma A1 (proved).** Let `P_in(u) = P(η ≤ u < η+W)`. Then `P_in(u) > 1/2` iff `u ∈ [0, W-1]`.
  - *Why.* At `u = 0` the event `η ≤ 0` has probability `(σ+1)/(2σ+1)`; at `u = -1` it has
    `σ/(2σ+1)`; the down edge is symmetric.
  - *Consequence.* Among schedules with two switches per period, the best one deploys the
    **nominal window** `[φ + jL, φ + jL + W)`. Its per-period net gain is
    `G = Δ(W - 2E|η|) - 2k`, where `E|η| = σ(σ+1)/(2σ+1)`.
  - *The alternatives are worse.* Never deploying earns 0. Staying on the candidate for a whole
    period earns `Δ(2W - L) < 0` when `W < L/2`.
  - *Oracle policy.* The φ-oracle deploys the nominal window if `G > 0` and never deploys
    otherwise.
- **Jitter-clairvoyant reference.** It also knows `η` and deploys exactly the realised windows,
  earning `ΔW - 2k` per period.

**Per-boundary accounting (for item 2f).** There are two boundaries per period.
- **φ-oracle:** `Δ·E|η| + k` per boundary. The `Δ·E|η|` term is jitter mismatch relative to the
  clairvoyant reference.
- **Learner that deploys the nominal window of `φ̂_j = φ + e_j`:** `Δ·E|η + e_j| + k` per boundary.

**Development constants (fixed before any run):** `L=24`, `W=8`, `S=20`, `T=480`, `Δ=0.4`,
`α=0.05`, `c=0.01`, `k=0.25`.

| σ | `E|η|` | `G` (oracle net gain per period) | oracle gain over `S=20` |
|---|---|---|---|
| 0 | 0 | 2.70 | 54.0 |
| 1 | 0.667 | 2.17 | 43.3 |
| 2 | 1.2 | 1.74 | 34.8 |

---

## 2. Causal localisation of φ (deliverable b)

### 2.1 Chronology

Only the current round can be queried. A "probe of residue `r`" planned at time `t` therefore
executes at the next `t' ≥ t` with `t' ≡ r (mod L)`, and its label is visible at `t' + d`.

Every design below chooses, at each `t`, whether to query `t` itself. It does so using released
labels only, and it may plan over candidate times `[t, t+L)`. "A posterior median in the past"
cannot occur. Waiting up to `L-1` rounds for a residue to recur, plus `d` rounds for release, is
charged in calendar time.

### 2.2 Deterministic cores and decisive sets

- **Cores.** Under hypothesis `φ'`:
  - the core-good set is `CG(φ') = {φ'+σ, …, φ'+W-σ-1} mod L`;
  - the core-bad set is `CB(φ') = {φ'+W+σ, …, φ'+L-σ-1} mod L`.

  On these residues the state does not depend on `η`.
- **Lemma B1 (proved).** Under truth `φ`, let a round be chosen predictably with residue in
  `CG(φ) ∪ CB(φ)`. Its label is Bernoulli with mean `±Δ`, known given `φ`, and independent of
  everything released before.
  *Proof.* The state is deterministic on cores, and emission noise is independent across rounds
  given the state path. ∎
- **Decisive set.** `D(φ, φ') = (CG(φ) ∩ CB(φ')) ∪ (CB(φ) ∩ CG(φ'))`. For circular distance
  `δ = |φ - φ'|_L ≤ L/2` and `L ≥ 2W`, direct interval arithmetic gives
  `|D(φ, φ')| = 2·min(δ - 2σ, W - 2σ)` when `δ ≥ 2σ+1`, and `D = ∅` otherwise.

  So deterministic labels distinguish hypotheses only beyond `2σ`. Separations of `σ+1 … 2σ`
  are visible only through jitter-zone labels. Those labels share `η_j` within a window, so they
  are dependent.

### 2.3 Theorem L1 (tournament localisation under any predictable causal design; proved)

**Statistic.** For hypotheses `a` and `b`, let
`T_ab(t) = Σ_i log(p_a(Y_i)/p_b(Y_i))`. The sum runs over labels **released by time `t`** whose
residue lies in `D(a, b)`, using the deterministic-state likelihoods. Let `n_ab(t)` be the number
of such labels.

**Estimator.** `φ̂_t = argmin_a max_b T_ba(t)`.

**Claim.** For any causal design whose query decisions are predictable (any adaptivity, any delay,
any budget), at any decision time `t`,

    P_φ( |φ̂_t - φ|_L > 2σ ) ≤ Σ_{φ': |φ'-φ|_L > 2σ} P_φ(n_φφ'(t) < n0) + N_far · (1-Δ²)^{n0/2}.

**Proof.**
1. *A martingale per far hypothesis.* Fix a far `φ'`. By Lemma B1, each label counted in
   `T_φφ'` has a deterministic state under both hypotheses, and these states are opposite. So
   `E_φ[exp(-½ LLR_i) | past] = 2√(p(1-p)) = √(1-Δ²)`, with `p = (1+Δ)/2`. Inclusion is
   predictable, so `M_t = exp(-½ T_φφ'(t)) · (1-Δ²)^{-n_φφ'(t)/2}` is a nonnegative martingale
   with `M_0 = 1`.
2. *Markov's inequality.* On the event `{T_φφ'(t) ≤ 0, n_φφ'(t) ≥ n0}` we have
   `M_t ≥ (1-Δ²)^{-n0/2}`. Markov's inequality then bounds its probability by `(1-Δ²)^{n0/2}`.
3. *The good event.* On the event that `T_φφ' > 0` for every far `φ'`:
   - the truth has score `max_b T_bφ = 0` (near `b` give `T = 0`);
   - every far `a` has score `≥ T_φa > 0`.

   So the argmin is within `2σ`.
4. *Conclusion.* A union bound over far `φ'` completes the proof. ∎

**Corollary L2 (round-robin causal design; proved, numerically vacuous at development sizes).**
- *Design.* In absolute block `j`, query `m` consecutive residues starting at `jm mod L`. Every
  residue is then queried once every `⌈L/m⌉` blocks.
- *Coverage.* After `N_c` complete released cycles, `n_φφ'` is at least
  `2·min(δ-2σ, W-2σ)·N_c` deterministically.
- *Error bound.* Summing the geometric series, with `ρ = (1-Δ²)^{N_c}` and `L ≥ 2W`:

      P(|φ̂ - φ|_L > 2σ) ≤ 2ρ/(1-ρ) + L·ρ^{W-2σ}.

- *Cost.* Labels `= L·N_c`, plus up to `m·⌈d/L⌉` pending. Calendar `≤ ⌈L/m⌉·N_c + 1 + ⌈d/L⌉`
  periods.
- *At development constants.* For `δ = 0.05` the bound needs `N_c = 22`, that is **528 labels**,
  and at least 22 periods even at `m = L`. That exceeds every development budget. The bound is
  valid but uninformative there, because round-robin spends most labels on non-decisive residues.

**Refinement L1′ (proved; also vacuous).** Separations `σ < δ ≤ 2σ` can be handled with
jitter-zone labels.
- *Construction.* Use at most one such label per *even* absolute block. Each block of length `L`
  meets at most two consecutive governing windows, so even blocks share no `η`. The selected labels
  are then independent under the truth, with jitter-marginal law `Ber(p_φ(r))`. Step 2 of the proof
  holds with per-label factor `BC(p_φ(r), p_φ'(r)) < 1`.
- *Cost.* At `σ = 2` the best residue gives `BC ≈ 0.970`. Exact localisation then needs on the
  order of 400 periods.

**All-policy label floors (proved, Fano).**
- *Information per label.* Any adaptive design receives at most the binary-symmetric capacity
  `C = ln 2 - h(0.7) = 0.0823` nats per label.
- *σ = 0.* Exact localisation with success `0.95` needs
  `E[N] ≥ (0.95 ln 24 - ln 2)/C = 28.3` labels.
- *σ = 1, 2.* Packing `⌊L/(2σ+1)⌋` hypotheses gives floors of 15.6 and 7.6 labels for `±σ`
  localisation.

**Conjecture L3 (not proved).** The posterior-guided design localises to `±σ` with
`O((ln(L/(2σ+1)) + ln(1/δ))/C_σ)` labels and `O(labels/m + d/L)` periods, where `C_σ` is a
jitter-dependent capacity.
- *Design.* Exact jitter-marginalised posterior; query the current round iff its information gain
  plus pre-certification betting value ranks among the top `⌈(B - used)·L/(T - t)⌉` candidate
  times in `[t, t+L)`.
- *Status.* Its coverage, meaning that it keeps sampling decisive residues for every surviving far
  hypothesis, is not established. Section 7 measures it.

---

## 3. Promotion validity, power and the certification floor (deliverable c)

### Theorem C1 (validity of the phase-stratified e-process; proved; standard)

**Setup.**
- *Stakes.* Each queried round `s` gets a stake `λ_s ∈ [0, λ_max]`, with `λ_max < 1`, fixed at
  request time from released information. Stake `λ_s = 0` off the predicted-good stratum and on
  boundary probes.
- *Wealth.* Define `W_s = Π_{s' ≤ s} (1 + λ_{s'} Q_{s'} Z_{s'})`, indexed by **request time**.

**Proof.**
- *Supermartingale.* Under `H0`,
  `E[W_s | F_{s-1}] = W_{s-1}(1 + λ_s Q_s E[Z_s | F_{s-1}]) ≤ W_{s-1}`, because `λ_s Q_s ≥ 0` is
  `F_{s-1}`-measurable (with private coins).
- *What the learner sees.* With fixed in-order delay, at time `t` the learner sees exactly
  `W_{t-d}`.
- *Ville.* Promotion requires observed wealth `≥ 1/α`, so
  `P(any promotion) ≤ P(sup_s W_s ≥ 1/α) ≤ α`. ∎

**Remarks.**
- **Validity does not use the recurrence model.** A wrong period, window or jitter model affects
  power only.
- **Budget exhaustion is harmless.** It is equivalent to all later stakes being 0.
- **Out-of-order or informative delays are not covered** (the R3 correction).
- **The all-onset e-detector mixture is valid by the same argument.** This is the reactive arm,
  with start weights `1/((i+1)(i+2))` summing to at most 1.
- **The gate certifies only the absence of the null.** Value in the current regime comes from the
  declared periodic persistence model. That is the goals document's
  "post-change evidence **or** a persistence model" route, and the value claim is only as good as
  the model. Recurrence breaks are outside this narrowed family.

### Lemma C2 (power and budget exhaustion; proved, exact computation)

**Claim.** Suppose the stake is `λ = Δ` on labels that lie truly in core-good rounds. Then the
probability that the wealth crosses `1/α` within `n` such labels is the exact anytime value
`P_n`, computed by dynamic programming in `anytime_power`. With `Δ = 0.4` and `α = 0.05`:

| `n` good labels | 20 | 30 | 40 | 55 | 60 | 75 | 120 |
|---|---|---|---|---|---|---|---|
| `P_n` | 0.31 | 0.52 | 0.67 | 0.80 | 0.84 | 0.90 | 0.98 |

**Consequences.**
- *Budget exhaustion.* Even with free, perfect localisation, the chance of never certifying is at
  least `1 - P_B`: 0.48 at `B = 30` and 0.16 at `B = 60`.
- *Calendar time.* At most `W` good rounds occur per period. Certification therefore takes at
  least `⌈n/W⌉` periods from the moment localisation is good enough to aim stakes.

### Proposition C3 (all-policy certification floor; proved)

**Claim.** For any α-valid policy, `kl(P_alt(promote), α) ≤ KL_g · E_alt[N_good]`.
- `N_good` counts queried rounds inside realised windows.
- `KL_g = KL(Ber(0.7) ‖ Ber(0.5)) = 0.0823`.

**Proof.**
1. *A null with the same latent structure.* Take `Q ∈ H0` with the same `(φ, η)` law, mean 0
   inside windows and mean `-Δ` outside. Its full-history conditional mean is
   `-Δ·P(outside | past) ≤ 0`, so `Q` is in the null.
2. *Divergence of observations.* By the chain rule and data processing, after conditioning on the
   shared latent `(φ, η)`,
   `KL(P_obs ‖ Q_obs) ≤ E_alt[Σ_{queried s in window} KL_g]`. Labels outside the windows have the
   same law under both and contribute 0.
3. *Conclusion.* Data processing to the promotion event, with `Q(promote) ≤ α`, gives the
   claim. ∎

**Numbers.** Promotion with probability 0.8 needs `E[N_good] ≥ 23.2`; with probability 0.9 it
needs `≥ 28.9`.

**The floor is not attained.** The fixed-stake anytime test needs 55 and 75 labels. The factor of
about 2.4 is the price of anytime validity with a predictable stake, compared with a
known-horizon likelihood-ratio test. This gap concerns certification engines, which are Lane A's
risk-frontier topic, and is not specific to RLS.

---

## 4. Upper bound on excess cost over S recurrences (deliverable d)

**Variant analysed (RLS-R, the proved variant).** RLS-R has three phases:
1. **Localisation.** Round-robin localisation (Corollary L2).
2. **Certification.** Bet `λ = Δ` on the *deep core* `{φ̂+3σ, …, φ̂+W-3σ-1}`. This lies inside
   the true core whenever `|φ̂ - φ| ≤ 2σ`, which needs `W ≥ 6σ+1`.
3. **Deployment.** After certification, deploy the nominal window of `φ̂_j`. Here `φ̂_j` uses
   only labels released before period `j` starts.

**Definitions.**
- `N_c` is the period of first promotion (`∞` if it does not occur by `S`).
- `e_j = |φ̂_j - φ|_L`.

### Theorem D1 (decomposition; proved accounting inequality)

    E[J(RLS-R) - J(φ-oracle)] ≤ c·E[Q]                                   (labels; ≤ cB)
                               + G·E[min(N_c, S)]                          (localisation + certification calendar)
                               + (ΔW + 2k)·P(N_c ≤ S)                      (the partial certification period)
                               + Σ_{j=1}^{S} 2Δ·E[min(e_j, W)·1{N_c < j}]  (forecast error, released labels only)

**Proof.**
- *Before promotion.* RLS-R earns 0, while the oracle earns `G` per period, net of its own `2k`
  switches. This charges the oracle's switch costs in the term `G`.
- *Certification period.* The difference in that period is at most `ΔW + 2k`.
- *After promotion.* Both policies deploy one length-`W` window per period with exactly two
  switches, so the switch costs cancel. The realised `η` is common to both, so gains differ only
  on the symmetric difference of the two windows, which has at most `2·min(e_j, W)` rounds,
  each worth at most `Δ`.
- *Query cost.* At most `c` per label. ∎

**Plugging in the proved lemmas.**
- **Forecast error.** By Theorem L1, `E[min(e_j, W)] ≤ 2σ + W·δ_j`, where `δ_j` is the L2 bound
  at the labels released before period `j`.
- **Certification time.** `P(N_c > N_loc + ⌈n/(W - 6σ)⌉ + 1) ≤ δ_loc + 1 - P_{min(n, B - L·N_c)}`,
  using Lemma C2 with budget exhaustion included.
- **Two residual terms remain.**
  - A **linear residual** `4ΔσS` comes from localising only to `±2σ`. It is removed by exact
    localisation; L1′ proves this only for an impractically slow design, and Conjecture L3 claims
    it for the posterior design.
  - A **transient** `G·(N_loc + n/(W-6σ))` comes from localisation and certification calendar
    time.
- **Per-boundary terms, written as the task asked.**
  - The learner pays `Δ·E|η + e_j| + k` per boundary after certification.
  - The oracle pays `Δ·E|η| + k`.
  - The learner's excess per boundary is at most `Δ·|e_j|`.
  - The jitter term `Δ·E|η|` is common to both, so it cancels in the excess.

**At development sizes the proved bound is vacuous.** L2 needs about 528 labels, while
`B ≤ 240`. So the proved theorem says nothing about `S = 20`, `B ≤ 60`. The bound becomes
informative only for `B ≳ 600` and `S ≳ 40` at `Δ = 0.4`.

The practical RLS of section 7 uses the posterior design. Its upper bound is the same
decomposition with `δ_j` taken from the unproved Conjecture L3.

---

## 5. Lower bounds (deliverable e)

### 5.1 Proposition E1 (all-policy jitter floor against the clairvoyant reference; proved)

**Claim.** Fix any causal policy. Give it knowledge of `φ`, an unlimited budget and *noiseless*
labels; all of these only help it. At each up-edge, its expected number of mismatched rounds is at
least

    g(σ,d) = (1/(2σ+1)) Σ_{t=-σ}^{σ} min( #{η: t-d < η ≤ t}, #{η: η > t} )   (η ranging over {-σ..σ}).

**Properties of `g`.**
- `g(σ, d) = E|η|` whenever `d ≥ 2σ+1`.
- `g(σ, d) ≥ min(σ, d)/4` for all `σ, d ≥ 1` (proved). Numerically it is `≥ min(σ, d)/2` for
  `σ ≤ 24` and `d ≤ 59`.

**Proof.**
1. *Information about `η_j`.* `η_j` is independent of everything before the zone
   `[φ+jL-σ, φ+jL+σ]`. At time `t`, the most the learner can know about `η_j` is
   `1{η_j ≤ s}` for zone rounds `s ≤ t-d`; noisy labels are a garbling of this. So the learner
   knows `η_j` if `η_j ≤ t-d`, and otherwise only that `η_j > t-d`.
2. *Bayes error at time `t`.* The minimal mismatch probability at `t` is the count in the display
   divided by `2σ+1`. `jitter_floor_bruteforce` checks this by explicit enumeration.
3. *Scaling.* Take `m = ⌈min(σ, d)/2⌉ ≤ min(σ, d)`. For `t ∈ [-σ+m-1, σ-m]` both counts are at
   least `m`. This gives `g ≥ m(2σ-2m+2)/(2σ+1) ≥ m/2 ≥ min(σ, d)/4`. ∎

**Net form (sketched).** Every period, a policy either:
- deploys and withdraws, paying `2k` as the clairvoyant does plus `Δ·g`;
- skips the window, losing `ΔW - 2k`; or
- stays on the candidate through the bad stretch, losing `Δ(L-W-2σ) - 2k`.

Hence `Reg_clair ≥ S·min{Δ·g(σ,d), ΔW - 2k, Δ(L-W-2σ) - 2k} = Ω(SΔ·min(σ, d))` in the regular
regime. **This is the `Ω(SΔ min{σ,d})` target of the review, proved against the clairvoyant.**

**Matching.**
- *`d ≥ 2σ+1`:* RLS, and every forecaster, pays `2ΔE|η|` per period, against the floor
  `ΔE|η|`. The match is within a factor of 2.
- *Where the factor of 2 comes from.* The floor lets an unlimited-budget learner read `η_j` from
  the up-edge and use it at the down-edge.
- *Budget bound on the down edge (sketched).* By Pinsker, with `κ̄ = KL(0.7 ‖ 0.3) = 0.339`, the
  down-edge loss summed over periods is at least
  `Δ(S·E|η| - (2σ+1)·√(S·B·κ̄/2))`. This is vacuous at development sizes; at
  `σ = 2, S = 20, B = 60` the correction is 71, against `S·E|η| = 24`.
- *`d < 2σ+1`:* matching is **open**. The floor `Θ(Δd)` sits against forecasting's `Θ(Δσ)`.
  Closing it needs in-period edge detection, and the Pinsker bound above is the only
  budget-limited argument available.

### 5.2 What fails against the φ-oracle (the task's comparator)

No `Ω(S)` all-policy lower bound can hold against the φ-oracle when `σ ≥ 1`.
- The φ-oracle itself pays `2ΔE|η|` per period of jitter loss.
- A learner with a per-period label budget can use in-period evidence about `η_j` to pay as little
  as `Δ·g(σ, d) < 2ΔE|η|` per period, beating the oracle.
- So the excess against the φ-oracle can be negative per period.

**Transient lower bound (sketched).** What remains is a transient,

    Reg_φ ≥ G·E[min(N_c, S)] - (gain from in-period edge learning),   with E[N_good before promotion] ≥ kl(1-β, α)/KL_g by C3,

and the subtracted term is at most `Δ(2σ+1)·√(S·B·κ̄/2)` by the Pinsker argument above.

**Conclusion.** The linear-in-`S` jitter floor is jitter-irreducible. Every policy pays it,
including the φ-oracle and every forecaster, so it does not separate RLS from any competitor. The
learning content against the φ-oracle is entirely in the transient terms:
- localisation: the Fano floor, compared with RLS's empirical label counts;
- certification: the C3 floor, compared with the C2 anytime power.

These are standard information floors with standard constants.

---

## 6. Mandatory competitors (deliverable f)

### 6.1 Reactive e-detector plus rollback

**Composition.**
- Promotion uses Shin–Ramdas–Rinaldo all-onset mixtures, a Lane A baseline. Each component bets
  `λ = Δ`.
- Rollback and re-promotion use a two-sided CUSUM on released labels with threshold
  `h = 1.5 ≈ 1.8` labels of log-likelihood ratio.
- Queries follow a uniform random calendar at rate `B/T`.

**Per-boundary loss.** About `Δ(d + ℓ_det) + k`, where `ℓ_det ≈ n_det·T/B` rounds; Lane A's
fixed-calendar bound gives `n·⌈T/B⌉ + d`. At development sizes `T/B = 8`–`16` rounds per label,
so `ℓ_det ≫ W = 8`. The controller cannot follow 8-round windows.

**Pre-promotion behaviour.** With no phase model, the label mean averaged over the calendar is
`-Δ/3`, so the mixture rarely crosses.

**This separation is not a contribution.** RLS, and any forecaster, beats it by about
`S·G` (linear in `S`) after localisation. But that only says forecasting with a *correct* declared
periodic persistence model beats reacting. This is the standard explicit-duration argument. It
holds only while the persistence model holds, and recurrence breaks are excluded from this family.

### 6.2 Periodic EXP4 (Oh, Meetoo Appavoo and Gilbert, ICALP 2019), adapted to budget and delay

**Adaptation.** Under the paired common-label contract, a queried round reveals the gain of
**all** `L` schedule experts. So the right adaptation is the label-efficient exponentially
weighted forecaster (Cesa-Bianchi, Lugosi and Stoltz 2005; named from memory, not re-verified here)
over the `L` periodic experts:
- importance-weighted paired gains `Z_s·1{s ∈ nominal window}/q`;
- updates at release;
- the expert resampled once per block;
- the same gate, with weight-based stakes.

**Regret guarantee.** The worst-case bound against the best schedule is
`O(T·√(ln L/B) + d·…)`. At development sizes this is about 110, larger than
`S·G ≈ 35`–`54`, so it is vacuous. Its comparator, the best fixed schedule, is exactly the
φ-oracle's schedule, so it is directly comparable with D1.

**Structural fact (standard).** The Bayes mixture over the `L` schedule experts with log-loss and
learning rate 1 is the aggregating algorithm, which coincides with Bayesian model averaging (textbook identity, stated from memory). That
mixture **is** RLS's posterior. "Schedule experts with likelihood weights" is therefore RLS's
estimator. The only remaining differences are linear-loss adversarial weights against a
stochastic likelihood, and the query design. Neither is new.

### 6.3 Duration-aware forecasting controller: the decisive kill test

**The controller.** It knows `L`, `W` and the emission law, estimates `φ` by maximum likelihood
from released labels, and plans switches at predicted boundaries.

**Identity on this family.** RLS has the same parts:
- the likelihood is the exact jitter-marginalised one, so **the MLE equals RLS's MAP** under its
  uniform prior;
- RLS's planner (receding-horizon two-state DP with switch cost `k`) is the controller's planner;
- the gate is common and mandatory.

**What remains.** RLS is this controller plus:
- (i) the posterior predictive instead of a plug-in;
- (ii) a query design.

Ablation (i) is `mle_active` against `rls` in §7. Item (ii) is Bayesian sequential experimental
design: expected information gain (Lindley 1956; MacKay 1992; named from memory) plus a betting-value term, inside a
causal planning window. The textbook alternative, Thompson-sampling-targeted queries
(`ts_forecaster`), is simulated too.

**If the controller with a standard design matches RLS, RLS is a standard composition and dead.**
Section 7 shows that it does at the primary budgets. At larger budgets the fully Bayesian design
wins by 2–10 units, which is a tuning advantage within standard design.

---

## 7. Development sanity check (deliverable 2; not confirmatory)

**Protocol.** Constants were fixed in the script header before the first run.
- **Instance.** `L=24`, `W=8`, `S=20`, `Δ=0.4`, `α=0.05`, `c=0.01`, `k=0.25`.
- **Grid.** `σ ∈ {0, 1, 2}`, `d ∈ {1, 4}`, primary `B ∈ {30, 60}`. Exploratory
  `B ∈ {120, 240}` was added to see where arms separate; it is labelled exploratory.
- **Seeds and common random numbers.** 2,000 alternative worlds use seeds 100696000–100697999.
  2,000 null worlds use seeds 100698000–100699999, shared by the two nulls. Both ranges lie inside
  `lane_b_toy_development` and are disjoint from every range used by `separation_check.py` and from
  the overflow block; a test enforces this. No registry edit was needed. The same seeds are used
  in every cell and arm.
- **Nulls.** Mean 0 everywhere (the boundary null) for all cells, and mean `-Δ` everywhere for the
  primary cells.
- **Arms.**
  - learning arms: `rls`, `mle_uniform` (the duration-aware MLE forecaster on a uniform calendar),
    `mle_active` (plug-in with RLS's design), `ts_forecaster` (Thompson-targeted queries, plug-in
    MLE planning), `exp4`, `reactive`;
  - references: `never`, `always` (ungated), and `oracle` (the φ-oracle).
- **Metric definitions.**
  - *Net cost* is relative to never switching, and lower is better: `-Σ A_t μ_t` (conditional mean
    given the realised windows) `+ c·labels + k·switches`.
  - *Excess* is paired against the φ-oracle.
  - *Per-boundary loss* is `(Δ·mismatched rounds + k·switches)/(boundaries)` after the arm's
    promotion, averaged over seeds with at least 4 post-promotion boundaries.

**Command:**

    cd <worktree> && PYTHONIOENCODING=utf-8 PYTHONPATH="$PWD/src" \
      UV_PROJECT_ENVIRONMENT="C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv" \
      uv run --no-sync python scripts/lane_b/rls_exact_small.py 2000 --out <scratch>/rls_results.json

Tests: `tests/test_lane_b_rls.py` covers seeds, closed forms, posterior exactness against brute
force, no-lookahead, budget, a null smoke test, and the oracle.

### 7.1 Results (2,000 seeds per cell; runtime 1,243 s; `*` = exploratory budget)

**Net cost relative to never switching** (lower is better). Each cell shows the mean, with the
per-arm SE in parentheses, and `p = P(promoted by T)`. For every primary cell, `never` = 0 and
`always` = +64.3 (ungated, so its false-promotion rate is 1).

| B | σ | d | rls | mle_active | ts_forecaster | mle_uniform | exp4 | reactive | φ-oracle |
|---|---|---|---|---|---|---|---|---|---|
| 30 | 0 | 1 | -2.4 (0.2), p=0.13 | -3.9 (0.2), p=0.16 | -3.6 (0.3), p=0.10 | 0.2 (0.0), p=0.01 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | -53.9 |
| 30 | 0 | 4 | -1.5 (0.1), p=0.10 | -3.0 (0.2), p=0.13 | -3.1 (0.3), p=0.09 | 0.2 (0.0), p=0.01 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | -53.9 |
| 30 | 1 | 1 | -2.0 (0.1), p=0.20 | -3.0 (0.2), p=0.23 | -2.1 (0.2), p=0.07 | 0.2 (0.0), p=0.01 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | -43.3 |
| 30 | 1 | 4 | -1.4 (0.1), p=0.17 | -2.5 (0.2), p=0.18 | -1.9 (0.2), p=0.07 | 0.2 (0.0), p=0.01 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | -43.3 |
| 30 | 2 | 1 | -0.9 (0.1), p=0.13 | -2.0 (0.1), p=0.18 | -0.9 (0.1), p=0.05 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | -34.7 |
| 30 | 2 | 4 | -0.6 (0.1), p=0.11 | -1.6 (0.1), p=0.16 | -0.7 (0.1), p=0.04 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | 0.3 (0.0), p=0.00 | -34.7 |
| 60 | 0 | 1 | -11.4 (0.3), p=0.55 | -10.5 (0.3), p=0.45 | -13.5 (0.4), p=0.38 | -0.5 (0.1), p=0.09 | 0.6 (0.0), p=0.00 | 0.6 (0.0), p=0.00 | -53.9 |
| 60 | 0 | 4 | -10.7 (0.3), p=0.53 | -8.8 (0.3), p=0.38 | -12.6 (0.4), p=0.37 | -0.5 (0.1), p=0.09 | 0.6 (0.0), p=0.00 | 0.6 (0.0), p=0.00 | -53.9 |
| 60 | 1 | 1 | -8.5 (0.2), p=0.61 | -8.6 (0.2), p=0.53 | -9.3 (0.3), p=0.34 | 0.0 (0.1), p=0.05 | 0.6 (0.0), p=0.00 | 0.6 (0.0), p=0.00 | -43.3 |
| 60 | 1 | 4 | -8.3 (0.2), p=0.58 | -7.1 (0.2), p=0.45 | -8.4 (0.3), p=0.32 | 0.1 (0.1), p=0.05 | 0.6 (0.0), p=0.00 | 0.6 (0.0), p=0.00 | -43.3 |
| 60 | 2 | 1 | -5.2 (0.2), p=0.48 | -5.5 (0.2), p=0.44 | -5.6 (0.2), p=0.27 | 0.4 (0.0), p=0.03 | 0.6 (0.0), p=0.00 | 0.6 (0.0), p=0.00 | -34.7 |
| 60 | 2 | 4 | -4.8 (0.2), p=0.46 | -4.8 (0.2), p=0.40 | -4.8 (0.2), p=0.25 | 0.4 (0.0), p=0.03 | 0.6 (0.0), p=0.00 | 0.6 (0.0), p=0.00 | -34.7 |
| 120* | 0 | 1 | -24.5 (0.3), p=0.90 | -20.5 (0.4), p=0.77 | -22.2 (0.3), p=0.75 | -4.6 (0.2), p=0.32 | 1.1 (0.0), p=0.01 | 1.3 (0.0), p=0.01 | -53.9 |
| 120* | 0 | 4 | -24.4 (0.3), p=0.90 | -19.2 (0.4), p=0.73 | -20.8 (0.3), p=0.74 | -4.4 (0.2), p=0.32 | 1.1 (0.0), p=0.01 | 1.3 (0.1), p=0.01 | -53.9 |
| 120* | 1 | 1 | -18.2 (0.3), p=0.87 | -15.7 (0.3), p=0.75 | -15.8 (0.3), p=0.71 | -2.6 (0.2), p=0.27 | 1.1 (0.0), p=0.01 | 1.3 (0.0), p=0.01 | -43.3 |
| 120* | 1 | 4 | -17.6 (0.2), p=0.88 | -13.5 (0.3), p=0.70 | -14.5 (0.3), p=0.69 | -2.3 (0.2), p=0.26 | 1.2 (0.0), p=0.01 | 1.3 (0.1), p=0.01 | -43.3 |
| 120* | 2 | 1 | -12.6 (0.2), p=0.82 | -10.6 (0.2), p=0.69 | -10.3 (0.2), p=0.62 | -0.8 (0.1), p=0.20 | 1.2 (0.0), p=0.00 | 1.3 (0.0), p=0.01 | -34.7 |
| 120* | 2 | 4 | -11.8 (0.2), p=0.82 | -9.1 (0.2), p=0.66 | -9.1 (0.2), p=0.58 | -0.6 (0.1), p=0.19 | 1.2 (0.0), p=0.00 | 1.3 (0.1), p=0.01 | -34.7 |
| 240* | 0 | 1 | -32.5 (0.2), p=0.98 | -28.0 (0.3), p=0.93 | -22.8 (0.3), p=0.89 | -13.7 (0.3), p=0.69 | 0.6 (0.1), p=0.38 | 2.5 (0.0), p=0.01 | -53.9 |
| 240* | 0 | 4 | -31.8 (0.2), p=0.98 | -25.5 (0.3), p=0.91 | -21.4 (0.3), p=0.86 | -13.1 (0.3), p=0.68 | 0.9 (0.1), p=0.36 | 2.6 (0.1), p=0.01 | -53.9 |
| 240* | 1 | 1 | -23.2 (0.2), p=0.96 | -20.1 (0.3), p=0.89 | -16.2 (0.3), p=0.84 | -9.1 (0.3), p=0.64 | 1.3 (0.1), p=0.31 | 2.5 (0.0), p=0.01 | -43.3 |
| 240* | 1 | 4 | -22.4 (0.2), p=0.96 | -17.6 (0.3), p=0.86 | -14.9 (0.3), p=0.82 | -7.8 (0.2), p=0.60 | 1.5 (0.1), p=0.29 | 2.6 (0.1), p=0.01 | -43.3 |
| 240* | 2 | 1 | -16.4 (0.2), p=0.92 | -13.3 (0.2), p=0.84 | -10.6 (0.2), p=0.76 | -4.8 (0.2), p=0.55 | 1.9 (0.0), p=0.19 | 2.5 (0.0), p=0.01 | -34.7 |
| 240* | 2 | 4 | -15.2 (0.2), p=0.92 | -11.2 (0.2), p=0.79 | -9.3 (0.2), p=0.72 | -3.8 (0.2), p=0.51 | 2.0 (0.0), p=0.17 | 2.6 (0.1), p=0.01 | -34.7 |

**Per-boundary loss after promotion.** The oracle pays `ΔE|η| + k`: 0.25, 0.52 and 0.73 for
`σ = 0, 1, 2`. The posterior arms pay:

| Arm | σ = 0 | σ = 1 | σ = 2 |
|---|---|---|---|
| rls | 0.28–0.49 | 0.53–0.79 | 0.72–0.88 |
| mle_active, ts_forecaster | same range as rls (0.27–0.48) | same range (0.55–0.82) | same range (0.76–0.92) |
| reactive (few promotions) | 2.3–2.9 | 2.3–2.9 | 2.3–2.9 |

The posterior arms pay close to the oracle's per-boundary loss once they are promoted. The
reactive arm's loss is consistent with `Δ(d + ℓ_det) + k` when `ℓ_det ≫ W`.

**Localisation at the end of period 20** (`d = 1`; `d = 4` is within 0.03):

| B | σ | rls: ±σ / exact (labels) | ts_forecaster | mle_uniform |
|---|---|---|---|---|
| 30 | 0 | 0.43 / 0.43 (30) | 0.47 / 0.47 (30) | 0.37 / 0.37 (28) |
| 30 | 1 | 0.53 / 0.24 (30) | 0.68 / 0.30 (30) | 0.60 / 0.27 (28) |
| 30 | 2 | 0.72 / 0.19 (30) | 0.78 / 0.24 (30) | 0.74 / 0.21 (28) |
| 60 | 0 | 0.75 / 0.75 (58) | 0.69 / 0.69 (60) | 0.57 / 0.57 (57) |
| 60 | 1 | 0.80 / 0.43 (60) | 0.84 / 0.45 (60) | 0.79 / 0.40 (57) |
| 60 | 2 | 0.89 / 0.33 (60) | 0.92 / 0.35 (60) | 0.89 / 0.32 (57) |
| 120* | 0 | 0.95 / 0.95 (83) | 0.88 / 0.88 (120) | 0.80 / 0.80 (116) |
| 120* | 1 | 0.97 / 0.71 (114) | 0.96 / 0.62 (120) | 0.92 / 0.54 (116) |
| 120* | 2 | 0.99 / 0.55 (115) | 0.99 / 0.50 (120) | 0.97 / 0.44 (116) |
| 240* | 0 | 0.99 / 0.99 (94) | 0.94 / 0.94 (160) | 0.94 / 0.94 (236) |
| 240* | 1 | 1.00 / 0.84 (147) | 0.98 / 0.69 (160) | 0.98 / 0.70 (236) |
| 240* | 2 | 1.00 / 0.69 (166) | 1.00 / 0.59 (160) | 1.00 / 0.59 (236) |

**Null worlds.** All 36 mean-0 cells and all 12 mean-`-Δ` cells passed.
- *Maximum false-promotion rate over cells and learning arms under the mean-0 boundary null:*
  0.0485 (`mle_active`, `B = 240`, `σ = 1`, `d = 4`; Clopper–Pearson upper 0.057). The point
  estimate is below `α = 0.05`.
- *Approach to `α`.* Rates rise towards `α` as `B` grows, as expected for a nearly exhausted
  Ville bound at the boundary null.
- *Mean `-Δ` null:* at most 0.001.
- *`exp4`:* at most 0.0005, because its weight-based stakes stay near zero.

### 7.2 Reading of the development check

1. **Budget-starved certification dominates the primary cells.** At `B ∈ {30, 60}` every arm keeps
   at least 29 of the oracle's 35–54 units of excess. The best learning arm recovers only 1–13.5
   units.
   - *Certification is the binding constraint.* Promotion probabilities are 0.04–0.23 at `B = 30`
     and 0.25–0.61 at `B = 60`, consistent with Lemma C2 (`P_30 = 0.52` and `P_60 = 0.84` even
     with perfect aim).
   - *Localisation is also incomplete.* At period 20, exact `σ = 0` localisation is reached in only
     0.43 (`B = 30`) and 0.75 (`B = 60`) of runs.
   - *This is an instance property.* The Fano floor is 28 labels for localisation and the C3 floor
     is 23 labels for certification.
2. **Reactive and Periodic-EXP4 are not competitive here.** Both are at about the never-switch
   level, with slightly positive net cost from query fees.
   - *Reactive* rarely promotes (≤ 0.5%) and loses about 2.5 per boundary when it does.
   - *EXP4* has a theory-tuned learning rate of about 0.02 per importance-weighted label, so its
     weights, and hence its gate stakes, barely move. It promotes at most 38% of the time even at
     `B = 240`, and its net cost is positive.
   - *These separations are not a contribution.* They are the expected "correct persistence model
     beats reacting" and "stochastic likelihood beats adversarial linear weights" effects (§6.1,
     §6.2).
3. **Kill test against the duration-aware forecaster.**
   - *(a) Uniform calendar.* The forecaster with a uniform calendar (`mle_uniform`) is far behind
     RLS. It trails by 0.8–2.6 units at `B = 30`, 5.2–10.9 at `B = 60` and 11–20 at
     `B ≥ 120`. At `B ≤ 60`, `mle_active` (plug-in, RLS's design) is within about 1.9 units of
     RLS, so the design explains essentially all of that gap; the estimator and the planner do
     not.
   - *(b) Primary budgets, design comparison.* At `B ∈ {30, 60}` the textbook
     Thompson-sampling-targeted design (`ts_forecaster`) matches or beats RLS's
     information-gain design in all 12 primary cells. It is better by 0.7–2.0 units in 5 cells and
     within 0.5 units in the other 7.
     - *Example:* at `B = 60`, `σ = 0`, `d = 1`, TS gets −13.5 against RLS −11.4.
     - *Example:* at `B = 30`, plug-in `mle_active` is the best arm, or within 0.1 of the best,
       in every cell.

     No posterior-arm ordering is stable across the primary cells.
   - *(c) Exploratory budgets.* At `B ∈ {120, 240}` RLS's full Bayes design does pull ahead:
     - by 2.0–5.2 units over `mle_active` at `B = 120`, and by 3.1–6.3 at `B = 240`;
     - by 2.3–10.4 units over `ts_forecaster`, with the largest gap at `B = 240`, `σ = 0`.

     The gain comes from higher and earlier promotion (0.92–0.98 against 0.72–0.93 at `B = 240`).
     It does not come from cheaper labelling, because query-fee differences are below 0.9.
     It is a 4–20% share of the oracle gain.
   - *(d) What the remaining advantage is.* Its components are:
     - expected information gain over the next `L` rounds, plus Kelly betting value, under a
       budget pacer;
     - an exact jitter-marginalised posterior predictive, including the within-window `η`
       posterior.

     These are standard Bayesian sequential experimental design and standard Bayesian prediction,
     applied to the duration-aware forecaster. The advantage is **a better-tuned standard
     design, not a new mechanism**, and it does not appear at the primary budgets.

     Paired standard errors of arm differences were not computed. Per-arm SEs are 0.1–0.4 with
     common random numbers, so differences under about 1 unit should be read as ties.
4. **Validity holds empirically for every arm.** This is as Theorem C1 predicts. The development
   check gives no evidence of a validity advantage for any arm.

**Decisive answer.**
- *Against the duration-aware MLE forecaster on a uniform calendar:* RLS differs only through its
  query design, and that difference matters (0.8–20 units, growing with `B`).
- *Against the same forecaster with a standard targeted design (Thompson sampling):* there is no
  advantage for RLS at the primary budgets, where TS is equal or better. At 2–4× larger
  exploratory budgets the fully Bayesian information-gain design wins by 2–10 units.
- *Conclusion.* Both designs are textbook. RLS ≡ standard estimator + planner + standard Bayesian
  sequential design + standard gate. **The candidate is dead as a novel method.**


---

## 8. Ledger: proved, sketched, conjectured

| Statement | Status |
|---|---|
| A1: the φ-oracle deploys the nominal window, with net gain `G` per period | Proved |
| B1: core labels are conditionally independent with known law | Proved |
| L1: tournament localisation to `±2σ` under any predictable causal design (delay and budget included) | Proved |
| L2: round-robin coverage, explicit label and period counts | Proved (vacuous at development sizes: 528 labels) |
| L1′: `±σ` / exact localisation via one jitter-zone label per even block | Proved (vacuous: about 400 periods) |
| Fano label floors (28.3 / 15.6 / 7.6) | Proved (standard) |
| L3: the posterior-guided design localises with a near-Fano number of labels | **Conjectured**; measured in §7 |
| C1: phase-stratified (predictable-stake) e-process validity under fixed delay and a hard budget | Proved (standard Ville) |
| C2: exact anytime power and budget-exhaustion probability | Proved (exact computation) |
| C3: all-policy `kl(1-β, α)` certification floor | Proved |
| D1: excess decomposition with released-label-only error terms and both switch costs | Proved; numerical instantiation vacuous at development sizes |
| E1: `Ω(SΔ min(σ,d))` all-policy jitter floor against the clairvoyant, with `g ≥ min(σ,d)/4` | Proved (gross); net form sketched |
| E1 matching within a factor of 2 for `d ≥ 2σ+1` | Proved (upper bound from forecasting plus E1) |
| Matching for `d < 2σ+1` under a hard budget | **Open** (the Pinsker bound is vacuous) |
| No `Ω(S)` lower bound against the φ-oracle when `σ ≥ 1` | Sketched |
| RLS ≡ duration-aware MLE controller + Bayesian design + standard gate | Argued (identity of estimator and planner); design equivalence measured: holds at primary `B`, while fully Bayesian design is better by 2–10 units at exploratory `B` (§7) |

## 9. Assessment: STOP RLS as a method candidate

Kill criterion 4b of the review fires. Its two parts:

- **Same estimator and planner.** The duration-aware forecaster with the same likelihood has
  exactly RLS's estimator and planner.
- **Same design effect from a standard design.** At the primary budgets, the textbook
  Thompson-sampling query design on the same posterior reproduces RLS's design effect (§7).
  RLS's remaining advantage at larger budgets is better-tuned standard Bayesian design.

**What survives, as supporting results only.**
- Theorem L1, a localisation bound that holds for any predictable design with delay and a hard
  budget.
- Proposition C3, a certification floor against an explicit causal null.
- Proposition E1, a jitter floor `Ω(SΔ min(σ,d))` that every policy pays.

None of these is a method. E1 also shows that the review's target rate does not separate methods.

**Recommendation.** Record the negative result in `LANE_CONTROL.md` (lead's action; this memo does
not edit it). Then return to the C0 pivot memo for the user's choice. The options are:
- a delay-heterogeneous second channel;
- partially selective labels, which re-couple information and deployment;
- many-candidate selection.

Each of these breaks one of the decompositions K1–K3. Under the frozen single-stream contract,
this memo found no remaining room in the recurrent latent-phase family.

**Code and data version.** Worktree branch `research/claude-lane-burst-allocation` at `0c65e21`
plus the uncommitted new files `scripts/lane_b/rls_exact_small.py` and
`tests/test_lane_b_rls.py`. Synthetic data only, with no `data/` reads.
