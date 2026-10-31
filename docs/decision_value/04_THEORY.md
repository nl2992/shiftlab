# Theory: deployment value as a functional of the alarm process

**Status:** draft v1 (orchestrator, 2026-10-30). Proofs are elementary and are written to be
checked line by line. Novelty assessments are provisional until `02_PRIOR_ART_AND_NOVELTY.md` is
complete; the default assumption is that each statement is known in spirit (Bayesian quickest
change detection already treats risk as linear in the stopping-time law). Numerical checks are
tracked in `RESEARCH_LEDGER.md` and listed at the end of this file.

## Setting

Horizon `T`. Two actions: `0` incumbent, `1` challenger/fallback. An **environment** `e` fixes the
evaluator-side mean losses `μ_t(a)`, `t = 1..T`, possibly random (e.g. a latent regime path).
Realised losses `ℓ_t(a)` are drawn conditionally independently given `e`, with
`E[ℓ_t(a) | e] = μ_t(a)`. Benefit of the challenger: `Δ_t = μ_t(0) − μ_t(1)`.

The operational system sees only queried labels released after delay `d`. An **alarm process**
`A = (A_1, …, A_T)`, `A_s ∈ {0,1}`, is produced by an acquisition rule and a monitor; `A_s` is
measurable with respect to labels released by the end of step `s`. A controller is
**alarm-driven** if the deployed action `a_t` is a deterministic function of `A_1..A_{t-1}`. Net
cost (acquisition shared by all compared systems, so query cost cancels in paired differences):

`C_T(P) = Σ_t μ_t(a_t) + c_s N_s + c_q N_q`.

Using `μ_t(a_t)` instead of `ℓ_t(a_t)` leaves expectations unchanged because `a_t` is
`F_{t-1}`-measurable and `ℓ_t` is conditionally independent of `F_{t-1}` given `e` (Proposition 0).

Value relative to never switching: `V(P) = C_T(never) − C_T(P)` (positive is good).

## P0 (Rao–Blackwellised cost; known)
`E[Σ_t ℓ_t(a_t)] = E[Σ_t μ_t(a_t)]`.
*Proof.* `E[ℓ_t(a_t) | F_{t-1}, e] = Σ_a 1{a_t=a} E[ℓ_t(a) | F_{t-1}, e] = μ_t(a_t)`; take
expectations. ∎ Requires that actions do not affect future outcomes (prediction replay, Setting
A/C); fails when actions change the data stream.

## P1 (permanent-switch value identity)
Controller: switch to `1` at `t = S+1` where `S = min{s : A_s = 1}` (`S = ∞` if none), never
revert. Let `F(s) = P(S ≤ s | e)`. Then

`E[V | e] = Σ_{t=1}^{T} Δ_t F(t−1) − c_s F(T−1)`.

*Proof.* `V = Σ_{t=S+1}^{T} Δ_t − c_s 1{S ≤ T−1} = Σ_t Δ_t 1{S ≤ t−1} − c_s 1{S ≤ T−1}`. Take
conditional expectations. ∎

Value is a **linear functional of the alarm-time law** with weight density `Δ_{t}` and a point
mass `−c_s` at the horizon. Detection power is `F(T)`; expected delay is another functional. The
two coincide in ranking only when the weights align.

## P2 (switching-cost crossing; exact, testable)
Compare monitors A, B under the same environment, acquisition and permanent controller, and write
`g(s) = F_A(s) − F_B(s)`. Because `c_s` enters neither the monitor nor the alarm law,

`E[V_A − V_B | e] = D_0 − c_s · g(T−1)`, with `D_0 = Σ_t Δ_t g(t−1)`.

If `D_0 > 0` and `g(T−1) > 0` (A is better at zero switching cost **and** more powerful by the
horizon), the deployment ranking reverses exactly at `c_s* = D_0 / g(T−1)`; for `c_s > c_s*`
the more powerful monitor is worse. If A is earlier with equal power (`g(T−1)=0`) no switching
cost reverses the ranking.

*Prediction checked numerically:* the crossing point computed from empirical alarm-time CDFs
must match the simulated cost crossing (ledger item TH-1).

## P3 (incumbent-target monitors: invariance and exact reversal)
Suppose the monitor's inputs are functions of the incumbent's labelled losses only (including any
reference risk estimated from incumbent labels). Then the alarm law does not depend on
`μ(1)`, and by P1 `E[V | e]` is affine in the challenger path:

`E[V | e] = Σ_t (μ_t(0) − μ_t(1)) F(t−1) − c_s F(T−1)`.

(a) If the fallback is never better (`μ_t(1) ≥ μ_t(0)` for all `t`), `E[V|e] ≤ −c_s F(T−1) ≤ 0`,
and for two incumbent monitors with `F_A ≥ F_B` pointwise (A earlier and at least as powerful),
`E[V_A | e] ≤ E[V_B | e]`: **a better harm detector is a worse deployment system**, even if every
alarm is a correct detection of incumbent harm.

(b) (No universal proxy.) For any two incumbent monitors with distinct alarm laws, there exist
admissible challenger paths `μ(1) ∈ [0,1]^T` under which A has strictly higher value and others
under which B does. *Proof.* Pick `s_0` with `g(s_0) ≠ 0` (exists since the laws differ; if
`g ≡ 0` on `s < T` the laws agree). Let `μ_t(1) = μ_t(0)` for `t ≠ s_0+1` and
`μ_{s_0+1}(1) = μ_{s_0+1}(0) ∓ η` with small `η > 0` keeping `μ ∈ [0,1]` (possible unless
`μ_{s_0+1}(0) ∈ {0,1}`, in which case one sign is available and the second ranking is produced by
`c_s > 0` when `g(T−1) ≠ 0`, or by a different `s_0` otherwise), with `c_s = 0`. Then
`E[V_A − V_B | e] = ±η g(s_0)`, taking both signs. ∎

Hence no functional of the alarm law alone (power, delay, ARL) ranks incumbent monitors
consistently with deployment value across environments that differ only in fallback quality.
This formalises H4 for this monitor class. For **paired-target** monitors the alarm law depends on
`Δ`, so the decoupling argument does not apply; P2 still holds.

## P4 (hold controllers: linear in the alarm intensity)
Controller Hold(H): at an alarm at `s` switch at `s+1`, stay on `1` for `H` steps, revert at
`s+H+1` (if `≤ T`); the monitor is paused during the hold and restarted fresh. With
`ν(s) = P(alarm at s | e)`,

`E[V | e] = Σ_s ν(s) w_H(s)`, `w_H(s) = Σ_{t=s+1}^{min(s+H,T)} Δ_t − c_s (1 + 1{s+H+1 ≤ T})`.

*Proof.* Each alarm contributes its own hold block; blocks do not overlap because the monitor is
paused. Sum and take expectations. ∎ When `Δ` is random (regime environments) the identity holds
conditionally on the regime path, and the value is driven by the **covariance between alarm
intensity and future benefit**, not by alarm frequency alone.

## P5 (Markov regimes: precision at action time is sufficient; delay–persistence ceiling)
Environment: a two-state Markov chain `Z_t ∈ {good, bad}` with stay probabilities `ρ_g, ρ_b`,
`λ = ρ_g + ρ_b − 1 ∈ [0,1)`, stationary `π_b = (1−ρ_g)/(2−ρ_g−ρ_b)`. Benefit of the challenger:
`Δ_bad > 0` in bad, `−δ ≤ 0` in good. Hold(H) controller as in P4, labels only, delay `d`.

Let `θ_S = P(Z_S = bad | alarm at S, past data)`. Because the alarm uses data up to `S` and the
chain is Markov, future states depend on the alarm only through `Z_S`, so
`P(Z_{S+h} = bad | alarm) = π_b + (θ_S − π_b) λ^h`. The expected net gain of one alarm is

`G_H(θ) = Σ_{h=1}^{H} [ (π_b + (θ − π_b) λ^h)(Δ_bad + δ) − δ ] − 2c_s`  (one switch + one revert;
use `c_s` for the last block if it reaches `T`),

which is **affine and increasing in θ**. Two monitors with the same alarm rate are ranked by the
mean precision at action time, not by power or delay.

*Ceiling.* Labels of events after `S−d−1` are unreleased at `S`, so
`θ_S ≤ P(Z_S = bad | Z_{S−d−1} = bad) = π_b + (1−π_b) λ^{d+1}` (when `λ ≥ 0`). Therefore every
label-only monitor satisfies

`E[gain per alarm] ≤ G_H(π_b + (1−π_b) λ^{d+1})`.

If `max_H G_H(π_b + (1−π_b)λ^{d+1}) ≤ 0`, no label-only monitor yields positive value with any
hold length: the obstacle is persistence and delay, not detection power. The ceiling decays
geometrically in delay with rate `λ`.

*Proof of the bound.* `θ_S = E[P(Z_S = bad | Z_{S−d−1}, data) | alarm]` and, by the Markov
property, `P(Z_S = bad | Z_{S−d−1}=z, data ≤ S−d−1) = π_b + (1{z=bad} − π_b) λ^{d+1}`, which is
maximised at `z = bad`. ∎ (If deployable proxies observe `Z` without delay, the bound is replaced
by the proxy-informed precision.)

## P6 (transient opportunity: an information ceiling; direct corollary of known results)
Single window `[τ, τ+L)` of benefit `Δ > 0`, `Δ_t = −δ ≤ 0` elsewhere, `τ` unknown. Any monitor
whose mean time to false alarm is at least `γ`, observing a paired stream with per-event
Kullback–Leibler information `I` thinned by query rate `q`, has worst-case conditional detection
delay at least `(log γ)/(qI)` (1+o(1)) as `γ → ∞` (Lai, 1998, Thm 1; Lorden, 1971). With label delay
`d`, informed time on the challenger inside the window is at most `(L − d − log γ/(qI))^+`
asymptotically, giving the dimensionless **conversion number**

`κ = (L − d) q I / log γ`.

For `κ < 1` no false-alarm-controlled monitor captures the opportunity asymptotically; for
`κ ≫ 1` delay differences between reasonable monitors are second order relative to `ΔL`.
This is a corollary of classical quickest-detection lower bounds, not a new theorem; its use is as
a predictor of where monitor improvements can matter (tested in ledger item TH-4).

## Novelty summary (provisional)

| Item | Status |
|---|---|
| P0, P1, P4 accounting identities | Known (Bayesian QCD risk is linear in the stopping-time law; Shiryaev, Pollak). Useful framing only. |
| P2 crossing point | Elementary corollary; possibly not stated in this form. Value is as an exact, testable prediction. |
| P3 invariance / no-universal-proxy | Elementary; potentially useful formalisation of H4. Literature check pending. |
| P5 precision sufficiency + delay–persistence ceiling | Elementary Markov-chain algebra; potentially useful. Literature check pending. |
| P6 | Direct corollary of Lai (1998) / Lorden (1971). Not novel. |

None of these is claimed as an ICML-level theoretical contribution on its own. A possible
contribution is the combination: an exact accounting framework that predicts monitor-to-value
conversion, verified quantitatively against simulation and real-data replay.

## Numerical checks to run

- TH-1: P2 crossing point from empirical CDFs vs simulated crossing (S1/S3, permanent controller).
- TH-2: P3(a) reversal for incumbent monitors under no-useful / common-shock fallbacks.
- TH-3: P5 predicted gain per alarm from estimated `θ` vs simulated value; ceiling vs best monitor.
- TH-4: P6 conversion number `κ` vs realised fraction of headroom captured across S1 cells.
