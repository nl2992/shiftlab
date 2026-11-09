# P2-NAD validity audit: what is proved, under which assumptions

Status 2026-11-09: proofs written by the lead (Opus) and checked against `scripts/p2/nad.py`. They
have not had an external review. Results are elementary, built from testing by betting and Ville's
inequality. The claimed contribution is the combination, not new probability theory.

## Setting and filtration

- Events t = 1..T. A disagreement indicator D_t is independent of the sign process s_t
  (s_t = 1 when the challenger is right). Queries are issued only on disagreements.
- Query k is issued at t_k, with gap g_k = t_k − t_{k−1}. The query decision uses released labels,
  disagreement indicators and private randomness only. It never reads an unreleased label, so t_k
  is predictable.
- Outcome z_k = s_{t_k}. With constant delay, outcomes are released and processed in issue order.
- F_{k−1} = σ(z_1..z_{k−1}, t_1..t_k, private randomness). The sign is not read before it is
  released.

## Declared classes (nested in ρ̄)

- **M(ρ̄, b):** s is a stationary two-state Markov chain with marginal P(s=1) = p ≤ b and
  persistence ρ ≤ ρ̄.
- **M̃(ρ̄, b), the per-step relaxation:** any process with P(z_k=1 | F_{k−1}) ≤ u_k, where
  u_k = b + (1−b) ρ̄^{g_k} z_{k−1} and u_1 = b. It contains M(ρ̄, b), since
  P(z_k=1 | F_{k−1}) = p + ρ^g (z_{k−1} − p), which is at most b + ρ̄^g (1−b) z_{k−1}.
  It also contains non-stationary processes whose persistence varies over time up to ρ̄.
- **Φ(β, b):** any stationary process with P(s=1) ≤ b and φ-mixing coefficient φ(g) ≤ β(g).
  Then P(z_k=1 | F_{k−1}) ≤ b + β(g_k). Heavy-tailed run lengths (the semi-Markov nulls) are
  **not** in Φ for any geometric β. The hidden-state null is in Φ only for β(g) at least its
  latent mixing rate. Order-2 chains are in Φ(β) for suitable geometric β, but not in M̃(ρ̄)
  in general.

The plain promotion null is b = 1/2. The payback null at release time τ is b(τ) = 1/2 + h(τ).

## P1. Validity of the envelope certificate

For a relative edge c ∈ (0,1) and an outcome h in the tested direction, the bet is
p'_k = u_k + c(1−u_k), with LR_k = (p'_k/u_k)^h ((1−p'_k)/(1−u_k))^{1−h}. If the conditional
success probability is v ≤ u_k, then

E[LR_k | F_{k−1}] = 1 + (v − u_k)(p'_k − u_k)/(u_k(1−u_k)) ≤ 1.

The started mixture E_k = Σ_c π_c Σ_{j≤k} w_j Π_{i=j..k} LR_i, with w_j = 1/(j(j+1)), satisfies
"E_k + 1/(k+1) is a test supermartingale" (QSG's argument). Ville's inequality then gives
P(sup_k E_k ≥ 1/α) ≤ α under every member of M̃(ρ̄, b). Cycle j of promotion uses threshold
2^j/α. Each cycle's test starts at a stopping time and is conditional on its past, so total false
promotion is at most Σ_j α/2^j ≤ α.

**Implementation requirement:** z_{k−1} must be the immediately preceding *queried* outcome over
the whole stream, including outcomes a test restart discards (those with e < seg).

- `NAD.observe` sets `self.prev` for every non-agreement outcome before checking `seg`.
- `QSG-env8` sets `prev = None` at each restart. Its first post-restart factor then uses u = 1/2,
  although the class allows up to 1/2 + ρ̄^g/2. This is a (small) validity gap in the precursor.
- Side −1 (discard and rollback) uses the mirrored coding, with hit = 1 − z and
  prev_hit = 1 − z_{k−1}.

## P2. Payback-certified promotion (PB variants)

- **Monotonicity.** For fixed data, each factor is non-increasing in u_k: on h=1 it is
  1 + c(1−u)/u, and on h=0 it is 1 − c. u_k is increasing in b and in ρ̄. Therefore
  E^{(ρ̄,b)}_k is pathwise non-increasing in both b and ρ̄.
- **Rule.** Promote at τ if E^{(ρ̄, b_j)}_τ ≥ 2^{cycle}/α, where b_j is the smallest grid
  value ≥ b(τ). b(τ) may depend on any data, including the estimated disagreement rate.
- **Guarantee.** P(promotion at some τ with p ≤ b(τ)) ≤ α under M(ρ̄, ·). On that event,
  E^{(ρ̄, p)}_τ ≥ E^{(ρ̄, b_j)}_τ ≥ threshold, and E^{(ρ̄, p)} is a valid e-process.
  Equivalently, it is a confidence-sequence statement: the lower confidence sequence of p
  exceeded the hurdle.
- **Economic reading (approximate, not part of the guarantee).**
  - Under M(ρ̄), switching at τ has expected forward net benefit
    ≈ dis·(2p−1)(T−τ) + transient − c_s.
  - The transient is at most ≈ dis·ρ̄/(1−ρ̄) per unit of current excursion.
  - With h(τ) = (c_s + κ)/(2·dis·(T−τ)) and κ = dis·ρ̄/(1−ρ̄), "forward benefit ≤ 0" implies
    p ≤ b(τ), up to the error in the plug-in dis.
  - So PB bounds the probability of a promotion that does not pay back over the remaining
    horizon. That is the Tier B notion, made sequential.

## P3. Growth optimality and the price of robustness

Fix a predictable gap policy. Let the alternative have conditional success probabilities q_k.

- The member of M̃(ρ̄, b) with conditional probability min(q_k, u_k) at every step belongs to the
  class. For any e-process valid under M̃,
  E_Q[log(E_k/E_{k−1}) | F_{k−1}] ≤ KL(q_k ‖ u_k)·1[q_k > u_k].
  This is the standard bound: the expected log of an e-variable under Q is at most
  KL(Q ‖ P) for any null P.
- Summing over labels and applying Wald's identity, the expected number of events to cross
  1/α is at least ≈ log(1/α) / R*(ρ̄), up to overshoot and the usual (1−β) factor. Here
  R*(ρ̄) = max_g I(g) / max(g + 1/dis, T/B) is the best achievable per-event information rate
  under the gap design, and I(g) is the per-label KL.
- The envelope bet with c near the optimum attains I(g) per label. The mixture over c costs
  O(log k) regret. NAD with gap g* = argmax R is therefore rate-optimal for M̃(ρ̄).
- **Price of robustness:** PoR(ρ̄) = R*_iid / R*(ρ̄). Values from `scripts/p2/info_rates.py`
  (dis=.2, T/B=10):

| p_alt | true ρ | R* iid-valid (×1e3) | R* M̃(.8) | R* M̃(.9) | R* M̃(.95) |
|---|---|---|---|---|---|
| .65 | 0 | 4.57 | 2.00 (g*=13) | 1.60 | 1.60 |
| .65 | .8 | — (V1 invalid) | 2.00 (g*=13) | 1.11 (g*=26) | 0.59 (g*=49) |
| .65 | .95 | — | (out of class) | (out of class) | 0.60 (g*=47) |

- The bound is for the **relaxed** class M̃. A procedure that exploits a fixed ρ across time,
  such as universal inference over M(ρ̄), can beat it on stationary data, because the stationary
  class is smaller.
- That is why bounded-ρ UI (UI80/UI90) and the envelope+UI mixture (MIX) are screened.
- **Consequence for F5:** on persistent alternatives with p=.65 and ρ=.8, any M̃(.8)-valid
  certificate needs on the order of 1,500 events in expectation. Much of the A5b−QSG gap is
  intrinsic, not an artefact of A5b.

## P4. Anytime dependence-robustness value

Let ρ̄*(t) = sup{ρ̄ in grid : max_{s≤t} E^{(ρ̄)}_s ≥ 1/α}. By pathwise monotonicity in ρ̄,
for every ρ_0 and every null in M̃(ρ_0, 1/2): P(∃t : ρ̄*(t) ≥ ρ_0) ≤ α. Simultaneously over
time, the reported value is a valid lower bound on the persistence a null would need to explain
the evidence. This is the dependence analogue of a Rosenbaum sensitivity value. It needs the
acquisition to be fixed independently of which ρ̄ is reported; NAD's gap policy satisfies this
because it is predictable.

## What is not guaranteed

- Validity outside the declared class (semi-Markov heavy tails, slow hidden states, real streams).
  These are reported as empirical stress tests only.
- Real data: twin nulls have an exact marginal null, but their dependence class is unknown.
  Empirical promotion rates on twins are evidence, not a guarantee.
- Delay that varies or reorders releases: P1 assumes processing in issue order. With variable
  delay, outcomes must be buffered and processed in issue order. `NAD.observe` sorts each batch,
  not across batches; constant delay makes this exact.
- The economic reading of PB uses a plug-in dis and an approximate transient bound.
