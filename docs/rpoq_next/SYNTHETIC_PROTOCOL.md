# Synthetic protocol A1: necessary-condition screen for Candidate A (frozen before any run)

**Date:** 2026-10-30. **Status:** exploratory development screen, synthetic only. **Claim level:** none.
**Code:** `src/shiftlab/dive/rpoq_next/screen_a.py` (written after this file is committed). **Method:** [`METHOD_DESIGN.md`](METHOD_DESIGN.md).

## Question
Under *exact* knowledge of per-context signal `μ_k`, proxy `H_k` and residual second moment `r_k`, does growth-aware allocation with per-context bets beat equally equipped variance-based and uniform allocation? (Predictions P1, P2 in the method design.) This is a necessary condition. Misspecified estimates (P3) are a separate protocol that runs only if this passes.

## Generator (frozen)
- `K = 8` contexts, equal probability. `Y = clip(μ_k + σ_k ε, −1, 1)`, `ε ~ N(0,1)`. Proxy `H_k = ρ·μ_k`, with `ρ = 0` (no proxy) and `ρ = 0.6`, both run. Bound `M = 1`.
- `σ_k = linspace(0.2, 0.8, 8)` in the orders below.
- **hom:** `μ_k = 0.05` for all `k`; `σ_k` increasing in `k`. Variance allocation should be at its best here.
- **het:** `μ = (0, 0, 0, 0.02, 0.04, 0.06, 0.10, 0.14)`; `σ_k` assigned by the fixed permutation `(3, 0, 6, 1, 7, 2, 5, 4)` of the linspace indices (noise independent of signal).
- **anti:** same `μ` as het; `σ_k` increasing with `μ_k` (high-signal contexts are the noisiest).
- **null:** `μ_k = 0` for all contexts, `σ` as in het (calibration).
- `r_k` and `μ_k` used by the allocator are the exact values of the clipped law, computed once by Monte Carlo (10⁶ draws per context, seed 1).

## Stream and monitor (frozen)
`N = 4000` events, hard budget `B = 400` (10%), fixed label delay `d = 20` events, `α = 0.05`, `q_min = 0.02`. Evidence is updated through the contiguous resolved prefix; the bet for event `t` uses only increments of events `≤ t − d`. Increment `X = H + Q(Y−H)/q`; when the budget is exhausted `X = 0` and the event is excluded from statistics. Bet `λ_t = min(μ̂₊/m̂₂, 0.5/(M(2/q_t − 1)))` with running moments from resolved increments and one zero pseudo-observation.

## Arms (every arm gets both bet types)
Allocation: **uniform** `q = B/N`; **neyman** `q ∝ sqrt(r_k)`; **growth** (`allocate()` with exact `μ_k, H_k, r_k`). Bet: **ctx** (per-context moments) and **common** (pooled moments). Six arms. Common random numbers across arms (shared `Y`, contexts, query uniforms).

## Metrics and decision
- Power: fraction of 2,000 seeds that cross `1/α` at some resolved time under each non-null setting. Secondary: mean final log-wealth, spend.
- Calibration: crossing fraction under **null** for every arm. Must be ≤ 0.07 (a 95% upper bound near α for 2,000 seeds); a breach is a bug, not a finding.
- **Primary contrast:** `growth+ctx − max(neyman+ctx, uniform+ctx)` power, paired bootstrap over seeds (2,000 resamples), in **het** at `ρ ∈ {0, 0.6}`.
- **Pass (A survives this screen):** primary contrast ≥ **+0.05** with 95% lower bound > 0 in het at least one `ρ`, **and** `|growth+ctx − neyman+ctx| ≤ 0.02` in hom (P1: ties when signal is constant).
- **Fail:** otherwise. Report anti as descriptive. A fail falsifies Candidate A in the exact-estimate setting, and work moves to the fallback (Candidate C) without a misspecification run.

## Not covered
Misspecified estimates, nonstationary alternatives, real data, correlation. No claim beyond this screen.
