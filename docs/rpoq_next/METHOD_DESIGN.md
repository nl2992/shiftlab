# Method design: growth-aware, signal-aware label allocation (Candidate A)

Proof status key: PROVED / CONDITIONAL / SKETCHED / CONJECTURED / FALSIFIED. Code: `src/shiftlab/dive/rpoq_next/growth_alloc.py`; tests: `tests/rpoq_next/test_growth_alloc.py`.

## Setting (unchanged from RPOQ)
Context `x`, bounded outcome `Y`, predictable proxy `H`, predictable propensity `q`, `Q ~ Bernoulli(q)` independent of `Y` given the past, `X = H + Q(Y−H)/q`, hard label cap, delayed release with evidence updated through the contiguous resolved prefix, wealth `E_t = ∏(1+λ_s X_s)` with `λ_s ≥ 0` predictable and `|λ_s X_s| ≤ 1/2`.

## Validity (CONDITIONAL, inherited, not new)
If `E[Y | G_t] ≤ 0` (the stated conditional null), `E[X_s | G_{s−1}] ≤ 0`, so for any predictable `q_s, λ_s` the product is a nonnegative supermartingale and Ville's inequality bounds crossing by `α`. This holds for *any* allocation rule that is predictable and respects the cap, including everything below. Allocation choices cannot create or destroy null validity; they change only power. The condition is unchanged from `docs/delayed_event_prefix_validity.md`: the current event's delay must not be used to pick `q` or `λ`.

## Moments (PROVED algebra, numerically checked by test)
With `μ = E[Y|x]`, `D = Y−H`, `r = E[D²|x]`:
- `E[X | x] = μ`
- `E[X² | x] = H² + 2H(μ−H) + r/q = c + r/q`, with `c = 2Hμ − H²`.

## Why growth allocation differs from variance allocation (DERIVED; CONDITIONAL on the quadratic approximation)
Quadratic log-growth of one bet `λ`: `μλ − ½(c + r/q)λ²`.
1. **Common bet.** If one `λ` is shared across events, `q` enters only through `Σ r_i/q_i`. Minimizing it under `Σq = B` gives Neyman `q ∝ √r`. So **with a common bet, growth-optimal and variance-optimal allocation coincide** (to second order). This explains why a growth objective alone is not expected to beat ASI when bets are common.
2. **Per-context Kelly bet.** With `λ_i = μ_i/(c_i + r_i/q_i)`, event growth is `g_i(q) = μ_i² / (2(c_i + r_i/q))`. This depends on `μ_i`, not only on `r_i`:
   - `c_i > 0`: `g_i` is concave; KKT gives `q_i = (|μ_i|√(r_i/(2ν)) − r_i)/c_i`.
   - `c_i = 0` (no proxy, `H=0`): `g_i = μ_i² q / (2 r_i)` is linear, so the optimum is **bang-bang on the signal-to-noise ratio `μ_i²/r_i`**: spend labels on the highest-SNR contexts first. (Seen in the test: the Neyman rule gives equal `q` to equal-`r` contexts; the growth rule favours the high-signal one.)
   - `c_i < 0` (proxy of the wrong sign): `g_i` is convex, optimum at a corner.
3. **Bet-bound penalty.** With `B_t = M(2/q − 1)`, the cap `λ ≤ 0.5/B_t` shrinks as `q` falls. `growth()` includes this cap, so very small propensities are penalised in a way variance allocation ignores. This is a candidate explanation for the CRSP linear-Neyman shortfall; it is **not** isolated yet.

## Falsifiable predictions (to be tested before any claim)
- P1 (necessary condition): with exact `μ, r, c` and per-context bets, growth allocation beats Neyman and uniform in power/log-wealth when `μ_k` varies across contexts, and ties them when `μ_k` is constant.
- P2: with a common bet, growth allocation and Neyman perform alike.
- P3: with noisy `μ̂`, the advantage shrinks and can reverse; a fallback toward uniform is needed.

If P1 fails, Candidate A is falsified for this setting.

## Known precedent and delta
The repo's `exact_mixture_growth_proxy` is a myopic model-based growth rule with a common stake (negative result: 0/60 vs 4/60 uniform on boundary harm). The delta here is the **per-context bet and SNR dependence** and the explicit bet-cap term. Whether similar covariate-dependent Kelly designs are published is **unresolved** (Pro-Active Inference and Active MPPI are unread). No novelty is claimed.

## Limits
Second-order approximation; requires estimates of `μ_k, r_k` (predictable); grid search per event (`shortcut:` comment in code); bang-bang optimum is fragile to `μ̂` error.
