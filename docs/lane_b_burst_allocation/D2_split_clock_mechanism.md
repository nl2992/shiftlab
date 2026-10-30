# D2: split-clock mechanism and theorem against the composition C*

**Date:** 2026-10-29. **Gate:** D2 (`LANE_CONTROL.md`, Phase D). **Status:** theory memo plus a
development-only Monte Carlo. Not reviewed by Codex. No novelty, theorem-validity or confirmatory
claim beyond the ledger in section 7.

## Verdict: EXIT (D2 reduces to a composition)

- **Step 1 (targeted search) did not find the target.** No source gives an adaptive two-channel
  allocation with surrogate rollback and gold-certified promotion. The search therefore did not
  trigger an exit (section 1).
- **Step 2 (theory) splits the bias-shift range into two regimes.** Neither leaves room for a
  non-composition mechanism.
  - **Identifiable regime** (the fast mean visibly moves at the reversal). A standard Page CUSUM on
    the surrogate, run against a lagged reference mean, needs no bias calibration at all. This
    already removes C\*'s stale-calibration failure (Prop. 3).
  - **Hidden regime** (`b >= 2βΔ`). No rule can roll back before `d_g`, because the fast-channel law
    can be made identical before and after the reversal (Prop. 2). The only lever left is the gold
    monitoring rate, which is a static allocation choice.
  - **The "adaptive" ingredients are standard.**
    - *State-dependent allocation* is a two-phase schedule (certify on gold, then monitor on fast).
      It is a per-phase static index, with a gain that is a constant factor in the certification
      term (Prop. 4).
    - *Triggered gold re-calibration* cannot reduce rollback delay below a continuous gold
      backstop, and can only save budget (Prop. 5). That is scout/confirm, or group-sequential
      futility; both were already closed by Lane A.
- **Step 3 (Monte Carlo, 1,000 seeds per cell) agrees with the theory.**
  - **The win is not the candidate's.** The best valid arm in 8/9 reversal cells is the
    *standard* two-phase composition. It beats the best stationary arm by 3.1–22.5 net units, and
    that gain comes from earlier certification, as Prop. 4 predicts.
  - **The candidate's own ingredient hurts.** The triggered gold burst is worse than the two-phase
    composition in 8/9 cells, by 3.9–7.5 units (best member against best member). It is better in
    one cell only: −1.8 at q=0.8 with no bias shift.
  - **The bias shift blinds the fast channel.** It sends every arm's rollback back to gold-backstop
    delays.
  - **Validity holds where it should.** Every gold-gated arm keeps false promotion at or below
    0.055. Surrogate-only reaches 0.49.

This is the RLS failure pattern from `C2_rls_narrowed_theory.md`, repeated: estimator, planner,
detector and e-process, each standard. By the D2 exit rule ("reduces to a composition → stop"),
Phase D should stop. The one adjacent open direction (section 8) is a contract change, not a D2
pass.

---

## 1. Step 1: targeted search (required by D0 before freezing D2)

Verification levels follow D0. **L2+** means the full HTML was read through a fetch tool that
reported the theorem statements and conditions; the proofs were not checked. **L2** means the
abstract or primary page was read. **L3** means a search snippet only.

| Source | Level | What it gives | D2 target? |
|---|---|---|---|
| **Ao, Chen, Gao, Li, Simchi-Levi, BAI with LLM judges and limited human audits (arXiv 2601.21471, Jan 2026)** | **L2+** (upgrades D0's L3) | K arms with contexts. A cheap judge score `F` is observed on every pull. Bias `b_k(x)` is unknown but **fixed** (Eq. 1). A human audit `Y` is drawn with probability `π_t(history, k, X, F)` and observed **in the same round**. The audit rate is an average constraint `E[π]=ρ`, not a hard cap. Estimator: `θ̂ = mean F + mean (A/π)(Y−F)` (Eqs. 6–8). Thm 3.3: a judge-only rule mis-selects with probability ≥ 1/2 on some instance. Props 4.3–4.4 and Thm 4.5: anytime-valid CS (Howard-type boundary, range `2/π_min`). Thm 5.1: LUCB stopping is δ-correct. Thm 5.2: Neyman audit `π* ∝ sqrt(E[(Y−F)^2 | k,x,f])` (pointwise Lagrangian). | **No.** No delay of any kind, no nonstationarity, bias shift, change point, rollback or switching state. Judge drift is mentioned only as motivation (App. A). It does give the established answer to *audit-on-surrogate with IPW correction* (section 8). |
| Chaythanya KV et al., QCD with measurements over a lossy link (arXiv 2510.25604) | L2 abstract | CUSUM / Lorden under queueing and retransmission delay. Heterogeneous sensors are scheduled by trading **age of observation against information content**. | No bias, no budget, no promotion/rollback asymmetry. It is the closest "multi-rate sensor" source: an information-versus-freshness index, which is a delay-shifted controlled-sensing index. |
| Gundersen et al., active multi-fidelity Bayesian online changepoint detection (UAI 2021, arXiv 2103.14224) | L3 | Chooses a fidelity per step by expected information gain. Low fidelity is **noisier, not biased**. | No bias, no hard budget, no validity guarantee. |
| Gopalan, Lakshminarayanan, Saligrama, Bandit QCD (NeurIPS 2021, arXiv 2107.10492) | L3 (as in D0) | Costly sensor selection with a delay lower bound and a matching scheme. | No bias or calibration, no delay heterogeneity. |
| Parast & Bartroff, group sequential testing with a surrogate marker (arXiv 2409.09440) | L3 | Group-sequential efficacy/futility boundaries for a surrogate-based test. | One decision, no gold-certified promotion, no rollback, no budget. |
| Lindon & Kallus (arXiv 2603.25971) | reuse (Lane A) | Calendar-time anytime CS under treatment-dependent delayed outcomes. | Plumbing for gold delay only. |
| Drift2Act, Lamaakal et al. (arXiv 2603.08578) | L2 abstract | Unlabeled monitoring signals give a drift belief. A small delayed-label set gives an "anytime-valid" risk bound. Escalation to rollback, with cooldowns. | Closest systems analogue, but no bias-shift analysis, no allocation theorem, no rollback-delay theorem (abstract level). |
| Li, Lin, Chen, Tu, surrogate-assisted stepped-wedge (arXiv 2603.10405) | L2 abstract | Surrogate bridge for a delayed, censored primary outcome; efficiency bound used for wave allocation. | Fixed sample, not sequential. |
| arXiv 2605.12947 (verifier scores calibrated on a reference pool, then an e-process); arXiv 2606.14028 (anytime-valid label-shift confirmation); arXiv 2408.02667 (imperfect surrogates in adaptive experiments) | L3 | Proxy-plus-calibration e-processes; surrogate trade-offs. | No delay heterogeneity or rollback. |
| Guardrail-metric practice (Spotify Confidence docs; Johari, Pekelis, Walsh, always-valid inference, arXiv 1512.04922) | L3 | Guardrails are pre-declared harm metrics. Automatic pause or rollback uses mSPRT or fixed-horizon tests **on the guardrail metric itself**. | No source found that rolls back on a fast proxy while certifying on a delayed gold label, or that calibrates the proxy's bias. |

**Search conclusion.** This is a bounded search, not an exhaustive one. It found no published
mechanism that hits the D2 target, so no exit at Step 1. Two findings matter for Step 2.
- Ao et al. close the static "cheap biased channel + selective gold audit + anytime CS + Neyman
  allocation" problem.
- The multi-rate QCD literature already uses an information-versus-age scheduling index.

Together these are exactly the two pieces into which the D2 candidate decomposes below.

## 2. Model

Two fixed policies. Paired loss difference `Z_t = l_t(0) − l_t(1)`, with mean `μ_t`:

- **Reversal at an unknown time.** `μ_t = +Δ` for `t < ν`, and `μ_t = −Δ` for `t ≥ ν`.
- **Null worlds.** `μ_t ≤ 0` for all t.

**Gold channel.** Querying round t returns `Z_t` at `t + d_g` for price `c_g`. It is unbiased, with
independent noise across rounds.

**Fast channel.** Querying round t returns `S_t = βZ_t + b_t + σ_f η_t` at `t + d_f`
(`d_f < d_g`) for price `c_f`.
- **Bias.** `b_t = b0` for `t < ν` and `b0 + δb` for `t ≥ ν`. The shift is unknown, with
  `|δb| ≤ b`, and happens **only at the reversal** (the task's model).
- **Delays and pairing.** Delays are constant and known. The query decision for round t is made at
  round t (contract of `switching_problem_v1.md`), so `S_t` is never available when round t's gold
  query is decided.

**Budget and costs.** A hard budget `B` is charged at request. Switch cost is `k`, and `A_0 = 0`.

**Promotion and rollback.** The first 0→1 switch must be gated by a gold-label test of the causal
null at level α. Rollback (1→0) carries no α; it is scored by its economic cost.

Write:
- `v_f = Var(S_t | μ_t)` (equal to `β²(1−Δ²) + σ_f²` for Rademacher Z);
- `I_g` = per-label KL between the gold laws at `+Δ` and `−Δ`;
- `I_f(δb) = (2βΔ − δb)² / (2 v_f)` = the per-label fast KL across the reversal (Gaussian-linear
  model; section 7 notes how the Rademacher simulator departs from it).

**C\* (from D0).**
- Stationary split: gold at rate `r`, with fast paired on gold rounds, plus extra fast labels.
- Gold e-process promotion.
- Fast rollback by a CUSUM on bias-corrected increments `(S_t − b̂⁺)/β`, where `b̂⁺` is a pooled
  paired-calibration UCB.
- Gold CUSUM backstop.

## 3. Candidate mechanism (as the task suggested)

**ACR (adaptive calibration-and-rollback).**
1. **Pre-promotion.** Gold at a high rate for certification, and fast at a low rate to build a
   reference sample. Pre-promotion spend is capped at `B/2`.
2. **Promotion.** Gold betting e-process, with stakes fixed at query time and multiplied in release
   order. Fast labels never enter it.
3. **Post-promotion.**
   - Fast labels at rate `f`. The remaining budget is paced evenly on a gold backstop CUSUM.
   - A Page CUSUM runs on `S` against a **lagged reference mean**: fast labels at least 50 rounds
     old, so no calibration is needed.
   - Roll back when either CUSUM reaches `h`.
4. **Trigger.** When the fast CUSUM reaches `h/2`, buy a 40-round gold burst. This is the
   "re-calibration / verification triggered by fast evidence". Its budget is reserved in the
   pacing.

The ablation without step 4 is called **two-phase** below.

## 4. Theory

### Prop. 1 (promotion validity under any fast-driven allocation; proved, standard)

**Assumptions.**
- The null path `μ_t ≤ 0` is deterministic (oblivious).
- Noise is independent across rounds.
- Delay is constant.
- Every gold stake `λ_t ∈ [0,1)` is fixed at query time t.

**Claim.** Then `M_k = Π_{j≤k} (1 + λ_{t_j} Z_{t_j})`, taken over gold queries in query order, is a
nonnegative supermartingale for **any** predictable query rule, including rules driven by fast
labels. Hence `P(promotion) ≤ α`.

**Proof.**
- Let `G_{k−1} = σ(H_{t_k}, Z_{t_1}, …, Z_{t_{k−1}})`. `H_{t_k}` contains only rounds `< t_k`: the
  fast label `S_{t_k}` is released at `t_k + d_f > t_k`.
- So `Z_{t_k}` is independent of `G_{k−1}` given the mean path, and `E[Z_{t_k} | G_{k−1}] = μ_{t_k} ≤ 0`.
- With constant delay, the labels released by any time form a query-order prefix. Promotion is
  therefore a stopping time of `M`, and Ville's inequality applies. QED.

**Caveats.**
- Validity breaks if a contract allows gold to be bought for a past round *after* seeing its fast
  label. Auditing selected on S then biases the product unless an IPW correction is used (Ao et
  al.'s construction, section 8).
- Adaptive nulls and informative delays are outside this proof. This inherits the qualified
  fixed-delay note `R3_delayed_update_validity_note.md`.

### Prop. 2 (hidden-shift impossibility; proved, coupling)

**Assumption.** The fast observation is Gaussian-linear in the mean: `S_t = βμ_t + b_t + ξ_t`, with
`ξ_t` iid `N(0, v_f)`, independent of the gold noise given the mean path.

**Claim.** Suppose `b ≥ 2βΔ`, and fix any rule (any adaptive allocation over channels and time,
any detectors). Let `p` be its probability of rolling back during `[ν, ν+d_g)` in the
never-reversing world `P^good` (same `b0`). Let `π_ν` be its probability of being promoted at `ν`.
Then in the instance with `δb = 2βΔ`, its expected regret is at least `(π_ν − p)·Δ·d_g`.

**Proof.**
- With `δb = 2βΔ`, the post-ν fast mean is `−βΔ + b0 + 2βΔ = βΔ + b0`, the same as before ν, so
  the fast-label law is unchanged.
- Gold labels from rounds `≥ ν` are released no earlier than `ν + d_g`.
- Couple the private coins with `P^good`. Through round `ν + d_g − 1`, the transcripts have the
  same law, so the rule rolls back during the window with probability at most `p`.
- On the complement, a rule that was promoted at ν stays deployed and loses Δ per round for `d_g`
  rounds. QED.

**Consequences.**
- When `b ≥ 2βΔ`, no allocation, re-calibration or detector beats gold-only rollback timing by more
  than its false-rollback budget. The feasibility proposition of `switching_problem_v1.md` carries
  over with `d = d_g`, even though a faster channel exists.
- **Smooth version (sketched; standard Lai 1998 / Lorden argument, asymptotic in `p → 0`).**
  Detection by `ν + D` with false-alarm `≤ p` requires approximately
  `I_f(δb)·N_f[ν, ν+D−d_f] + I_g·N_g[ν, ν+D−d_g] ≥ log(1/p)`, where `N_j` counts channel-j labels
  from those rounds.
- **Practical hiddenness.** As `δb → 2βΔ`, `I_f → 0`. When `I_f r_f d_g ≪ log(1/p)`, the shift is
  practically hidden even though `δb < 2βΔ`. The simulator's "moderate" shift (`δb = 1.25βΔ`) is
  in this regime (section 6).
- **Rademacher simulator.** There, `δb = 2βΔ` matches the fast mean and variance exactly but not
  the third moment. The residual KL is `O(β^6 Δ² / v_f^3)`, negligible at the simulated `σ_f`.

### Prop. 3 (static calibration fails, but a standard change detector does not need it; proved, drift sign)

**Setup.** C\*'s fast leg uses `x_t = (S_t − b̂⁺)/β`, where `b̂` pools `n0` pre-change pairs and
`n1` post-change pairs, and `m = b̂⁺ − b̂`. In S units:
- the post-change mean of `S − b̂⁺` is `−βΔ + δb − m − δb·n1/(n0+n1)`;
- post-change pairs arrive only from `ν + d_g`, at the paired rate `r_p`.

**(i) C\* is silent when `δb > βΔ + m`.** With `n1 = 0`, the mean is positive, the CUSUM drift is
negative, and the leg stays silent. It stays silent until `n1 > n0 (δb − βΔ − m)/(βΔ + m)`, that is,
until `ν + d_g + n1/r_p`. C\*'s rollback is then gold-driven, and its regret is at least `Δ·d_g`
(with high probability).

**(ii) A Page CUSUM on S does detect when `δb < 2βΔ − s/2`.** It runs against a reference mean
(designed shift `s`) with no calibration. Its post-change drift is `(s/v_f)(2βΔ − δb − s/2) > 0`.
By the standard Lorden bound its expected delay is about `d_f + h / (r_f (s/v_f)(2βΔ − δb − s/2))`.

**What this shows.** In the window `βΔ + m < δb < 2βΔ − s/2`, C\* as specified in D0 loses
`≈ Δ·(d_g − d_f − O(h/(r_f I_f)))` to a *standard* change-based composition. That composition uses
no gold and no calibration for rollback.

**Why this is not a D2 pass.** The separation is between two compositions. The level
parameterisation of C\* (rollback when the calibrated level crosses 0) is the defect, and Page's
1954 CUSUM against an estimated pre-change mean repairs it. Under the task's model (the bias moves
only at the reversal), the bias level is a nuisance parameter that change detection never needs.
Adaptive re-calibration therefore has nothing to fix in this regime.

### Prop. 4 (state-dependent allocation = two-phase static index; proved accounting, standard)

**Accounting.** Let `N_cert` be the gold labels needed for the e-process to cross; by Wald,
`E N_cert ≈ log(1/α) / E log(1+λZ)`.
- A gold rate `r` before promotion gives promotion at `≈ d_g + E N_cert / r`.
- The pre-promotion regret is therefore `Δ·(d_g + E N_cert / r)`, when `ν` comes later.
- A stationary split must use one `r_stat`, and must keep budget for post-promotion monitoring.
- A phase-dependent schedule may use `r_pre > r_stat`.

**Gain.** `Δ·E N_cert·(1/r_stat − 1/r_pre)`, minus any monitoring loss from the smaller remaining
budget. This is a constant factor in the certification term, not a rate change.

**Optimum.** The optimal rule in the two-phase class allocates per phase:
- before promotion, only gold carries certification information;
- after promotion, it is the delay-shifted index `argmin_j d_j + h / (r_j I_j)`, with the leftover
  budget paced.

This is the static controlled-sensing / multi-fidelity index of D0 §3(c), applied twice. It is
also the information-versus-age scheduling of the multi-rate QCD source, and "certify, then
monitor" as in the repo's `CertifiedPromotionRollback` with a per-phase budget. Schur et al.'s
two-phase reduction (Lane A audit) is the stationary analogue.

### Prop. 5 (triggered gold cannot reduce rollback delay; proved)

**Argument.** A gold query triggered at `τ ≥ ν` is released at `τ + d_g ≥ ν + d_g`.
- A continuous backstop at rate `r` already has labels from rounds in `[ν, τ)` in flight. So, for
  the same number of post-ν gold labels, a triggered burst gives a gold-driven detection time no
  earlier than a backstop that bought those labels at ν.
- In the identifiable regime with fast detection time `< d_g`, the fast alarm fires before any
  triggered label arrives.
- In the hidden regime, nothing triggers (Prop. 2).

**What is left.** The trigger only *saves budget* in worlds without a reversal. That is a
budget-reallocation (futility) gain. It is the scout/confirm structure of Chandar–Tchamkerten
(audited by Lane A, Lemma 1), and the group-sequential futility that Lane A already closed
(positive-prefix no-go).

**The one window where it helps.** A narrow intermediate window: the fast statistic crosses `h/2`
early, but crosses `h` later than `τ_{h/2} + d_g + n_burst`. There the gain is bounded by
`Δ·(τ_h − τ_{h/2} − d_g − n_burst)`, a constant-order term.

### Equivalence test (run honestly)

| ACR component | Standard object it equals |
|---|---|
| Pre/post allocation | Per-phase static index (Prop. 4; MF-UCB / controlled-sensing index / info-vs-age scheduling) |
| Fast rollback | Page CUSUM against an estimated pre-change mean |
| Gold rollback | CUSUM backstop at a paced rate |
| Trigger | Scout/confirm, or futility (Prop. 5) |
| Promotion | Predictable-stake betting e-process (Prop. 1) |
| Bias handling | Unnecessary under the task's model (Prop. 3); impossible beyond `b ≥ 2βΔ` (Prop. 2) |

Every component is standard, and the composition is the obvious one. **The C0/C2 kill criterion
("a contract-matched … controller attains the same rate by standard composition") fires.** The
only regime-dependent separation that is proved (Prop. 3) is against a weak parameterisation of
C\*, not against the class of compositions.

## 5. What no rule can do (lower-bound side, summary)

- **Hidden shift (`b ≥ 2βΔ`).** No rule rolls back before `ν + d_g` except by spending
  false-rollback probability (Prop. 2). Regret is at least `(π_ν − p)Δ d_g`, plus the gold
  detection term from the budget-limited gold rate (Lane A's noisy lower bound with `d = d_g`).
- **Practically hidden (`I_f r_f d_g ≪ log(1/p)`).** The same floor holds approximately (smooth
  version, sketched).
- **Promotion.** Promotion cannot be accelerated by the fast channel under any bias bound `b > 0`
  that is unknown to within `βΔ`. This is a judge-only impossibility in the style of Ao et al.
  Thm 3.3, carried over to the causal null. It is stated, not re-proved here.

## 6. Step 3: development Monte Carlo

**Command** (worktree `C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane`, base commit
`9e33b1d`, uncommitted files):

```
PYTHONIOENCODING=utf-8 PYTHONPATH="$PWD/src" UV_PROJECT_ENVIRONMENT="C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv" \
  uv run --no-sync python scripts/lane_b/split_clock_small.py <out.json>
```

Runtime was 41 s. The JSON output was kept outside the repository (SHA-256 `a8b38ad0…5737ba7f`); the
tables below are its summary. Tests: `tests/test_lane_b_split_clock.py`, 19 tests. With
`tests/test_seed_registry.py`, 31 pass, and ruff is clean.

**Constants.**

| Group | Values |
|---|---|
| Horizon and reversal | `T=600`; `ν ~ U{250..400}`; `Δ=0.4`; `β=1`; `b0=0.2` |
| Delays and prices | `d_f=1`, `d_g=48`; `c_g=1`, `c_f=1/8`; `B=240` |
| Costs and promotion | `k=2`; query cost weight 0.02 per unit in net; `α=0.05`; gold stake 0.36 |
| Surrogate quality | `σ_f = β/Φ⁻¹(q)` for sign agreement `q ∈ {0.55, 0.65, 0.80}` |
| Bias shift `δb` | none = 0; moderate = 0.5 (`1.25βΔ`); large = 0.8 (`2βΔ`, hidden) |
| Null worlds | `μ ≡ 0`, `b ≡ 0.2` |

**Seeds.** New registry block `lane_b_d2_split_clock_development` (100900000–100919999), allocated
with `shiftlab.seed_registry.allocate` and added to `configs/seed_registry.yaml`.
- Evaluation: seed `100900000 + cell·1000 + i`, 12 cells × 1,000.
- Threshold calibration: `100915000 + q_index·1000 + i`, 500 per q, in a separate always-good world.
- Common random numbers across arms.

**Matching across arms.**
- Every arm gets the same `B`, delays, prices and knowledge of `(Δ, β, σ_f)`.
- Each arm's CUSUM threshold `h` is calibrated to a false-rollback probability ≤ 0.05 in the
  always-good world.
- The tuned families each report their best member per cell by mean net cost on the evaluation
  seeds. This oracle selection is equally generous to all of them:
  - C\* and C\*-chg: gold rate `r ∈ {0.15, 0.25, 0.35}`;
  - two-phase and ACR: post-promotion fast rate `f ∈ {0.25, 0.5, 1}`.
- Arms that are not tuned: gold-only (rate 0.4) and surrogate-only.

**Disclosed forking path.**
- Two smoke runs used the first 100 and 200 seeds of each evaluation cell. After them I changed:
  - `n_ref` and `n_cal_min`;
  - frozen → lagged reference mean;
  - fixed thresholds → calibrated `h`;
  - fixed post-promotion gold rate → paced.
- The reason: the first versions produced false-rollback rates of 0.07–0.40 and budget exhaustion
  in the two-phase arms.
- The model constants did not change. Those seeds are therefore not untouched. This is
  development evidence only.

### Results (reversal worlds; net = regret + k·switches + 0.02·spend; SE about 0.6–0.9)

| q | shift | gold-only | surrogate-only (invalid) | C\* best | C\*-chg best | two-phase best | ACR best | Best valid arm |
|---|---|---|---|---|---|---|---|---|
| 0.55 | none | 98.5 | 132.5 | 107.9 | 104.9 | **94.6** | 98.5 | two-phase |
| 0.55 | moderate | 97.2 | 134.8 | 108.0 | 105.1 | **94.0** | 98.2 | two-phase |
| 0.55 | large | 97.2 | 134.7 | 108.3 | 105.4 | **93.4** | 97.6 | two-phase |
| 0.65 | none | 98.5 | 108.3 | 115.5 | 106.3 | **92.0** | 97.6 | two-phase |
| 0.65 | moderate | 98.9 | 146.5 | 115.9 | 105.5 | **90.6** | 98.1 | two-phase |
| 0.65 | large | 98.8 | 158.7 | 116.3 | 104.6 | **90.8** | 98.3 | two-phase |
| 0.80 | none | 100.5 | 50.1 | 104.3 | 104.3 | 78.0 | **76.3** | ACR (by 1.8) |
| 0.80 | moderate | 101.3 | 112.7 | 116.6 | 109.3 | **91.7** | 96.8 | two-phase |
| 0.80 | large | 102.2 | 132.1 | 116.0 | 108.1 | **92.5** | 98.5 | two-phase |

**Rollback delay after ν** (promoted before ν and caught), in rounds:
- **Gold-only:** 87–96.
- **q=0.8, no shift:** the fast channel cuts this to 58–63 (C\*, C\*-chg, two-phase, ACR).
- **Moderate or large shift at q=0.8:** every valid arm is back at 100–121. The fast channel is
  practically or exactly hidden (Prop. 2). The two-phase arm's gold backstop is slower than
  gold-only's, because its certification spend leaves less post-promotion gold budget.
- **q=0.55 and 0.65:** the fast channel never helps rollback. C\*-chg delays are about 93, close to
  gold-only.

**Promotion time:**
- two-phase and ACR: 106–109;
- gold-only: 137–141;
- C\*: 150–182.

**Unsafe rollback** (before ν) is 0.000–0.037 for every valid arm.

**Null worlds (false promotion; Ville bound 0.05; MC SE about 0.007).**

| q | gold-only | C\* best | C\*-chg best | two-phase | ACR | surrogate-only |
|---|---|---|---|---|---|---|
| 0.55 | 0.054 | 0.037 | 0.037 | 0.040 | 0.038 | 0.060 |
| 0.65 | 0.048 | 0.055 | 0.033 | 0.048 | 0.048 | 0.168 |
| 0.80 | 0.037 | 0.040 | 0.040 | 0.035 | 0.035 | **0.493** |

### Reading

1. **Where the gain comes from.** The best valid arm beats the best stationary arm by 3.1–22.5
   units. The best stationary arm is gold-only in 8/9 cells; C\*'s grid optimum sits at its edge
   `r=0.35`. The gain is promotion about 30 rounds earlier. Prop. 4's accounting predicts it:
   `E N_cert ≈ 36` labels gives promotion at about 108 / 138 / 151 for gold rates 0.6 / 0.4 / 0.35,
   as observed. That is a standard two-phase composition, not the candidate.
2. **The candidate's own ingredient hurts.** ACR minus two-phase (best member against best member)
   is +3.9, +4.2, +4.2, +5.6, +7.5, +7.5, −1.8, +5.1 and +6.0. The triggered burst's budget
   reserve slows the paced gold backstop, and the burst rarely arrives before the fast alarm. This
   matches Prop. 5's direction.
   - The comparison is confounded by the reserve.
   - A variant without the reserve was **not run**.
   - Prop. 5 bounds what any variant could gain in delay.
3. **Calibration.** C\*-chg beats C\* in 8/9 cells (by 2.9 to 11.7) and ties in the ninth (q=0.8, no
   shift: 104.34 against 104.32). Calibration-free change detection
   dominates the level-based, UCB-calibrated leg, as Prop. 3 predicts.
4. **Surrogate quality.** Only q=0.8 makes the fast channel useful, and only without a bias shift.
   The Binance task's 0.563 lies in the regime where the fast channel has no rollback value in this
   model.
5. **Invalid control.** Surrogate-only shows the invalid-promotion hazard: 0.49 false promotion at
   q=0.8. Its apparently best net (50.1) in that cell comes entirely from uncertified promotion.

## 7. Ledger

| Item | Status |
|---|---|
| Prop. 1, gold e-process validity under any fast-driven predictable allocation (oblivious null, independent rounds, constant delay, stake fixed at query time) | **Proved** (standard Ville argument) |
| Prop. 2, hidden-shift floor `(π_ν − p)Δ d_g` for every rule when `b ≥ 2βΔ` (Gaussian-linear surrogate) | **Proved** (coupling). The Rademacher simulator matches it to second moments only |
| Prop. 2, smooth information version | **Sketched** (standard Lai/Lorden, asymptotic) |
| Prop. 3(i), C\* level leg silent until `ν + d_g + n1/r_p` when `δb > βΔ + m` | **Proved** (drift sign; with-high-probability statement not quantified) |
| Prop. 3(ii), change-CUSUM delay | **Standard** (Lorden bound), not re-derived |
| Prop. 4, two-phase gain `Δ E N_cert (1/r_stat − 1/r_pre)` and per-phase index optimality | **Accounting proved**; per-phase optimality **sketched** (Lagrangian) |
| Prop. 5, triggered gold cannot beat a continuous backstop in delay | **Proved** (release-time argument); budget-saving value = futility (prior art) |
| Non-composition separation against C\* | **Not found**. The only proved separation is against C\*'s level parameterisation and is closed by a standard detector |
| Novelty of any component | **None claimed** |

**Limitations.**
- The simulator, constants, single reversal, β and known noise, and no re-promotion are all
  idealised.
- C\*'s grid optimum sits at its edge.
- Oracle best-member selection is on the evaluation seeds.
- The smoke-run forking path (section 6).
- `h` is calibrated per q, so gold-only gets h6 or h7 from calibration noise.
- The JSON output is not in the repository.
- Codex has not reviewed this memo.

## 8. Recommendation

**EXIT D2 → stop Phase D,** per the gate. The candidate reduces to a per-phase static index, a
Page CUSUM, a gold backstop, scout/confirm and an e-process. Its one distinctive ingredient (the
triggered re-calibration) loses in 8/9 development cells.

**The one adjacent direction that is not obviously closed requires a contract change, not a D2
pass.** Allow *retrospective* gold audits of past rounds selected on their fast labels: Ao et al.'s
audit-on-surrogate, but with delayed audits and a reversible deployment. Prop. 1's validity then
needs IPW correction, and allocation becomes Neyman auditing under delay and change.
- **Risks.** Ao et al. (static) plus Zrnic–Candès / delayed PPI already cover most of it, so the
  same composition risk applies.
- **Action.** This should go into the lead's pivot memo as an option. It should not be started
  inside Phase D.
