# Synthetic protocol A2: does Candidate A survive estimation? (frozen before any run)

**Date:** 2026-10-30. **Follows:** A1 ([`SYNTHETIC_RESULTS.md`](SYNTHETIC_RESULTS.md)), which showed an oracle-knowledge effect. New protocol; A1 is not edited. Exploratory, synthetic, no claim. Code: `src/shiftlab/dive/rpoq_next/screen_a2.py` (after this file is committed).

## What changes from A1
The allocator no longer receives `μ_k, r_k`. Everything is learned from labels drawn from the **same hard budget**. Proxy `H_k = ρ·μ_k` is a fixed pretrained model, known to every arm (as in A1), not estimated.

## Generator and stream
As A1 (`K=8`, `N=4000`, `B=400`, `d=20`, `α=0.05`, `q_min=0.02`, `M=1`), plus a new **const** setting: `μ_k = 0.05` and `σ_k = 0.5` for all `k` (constant SNR, the correct tie control), and the **null** setting as in A1. Settings: null, const, hom, het, anti; `ρ ∈ {0, 0.6}`. 1,000 seeds, common random numbers across arms.

## Learning (identical for every arm)
- **Burn-in:** events `0..399` are queried at the uniform propensity `q = 0.25` (100 labels, 25% of the budget, counted against the cap).
- **Estimators** (unbiased given known propensities, per context, from resolved active events): `μ̂_k = mean of X`; `r̂_k = mean of Q(Y−H_k)²/q`. Floors: `r̂_k ≥ 10⁻³`, `μ̂_k` clipped to `[0, 1]`.
- Remaining budget per event is `(B − spent)/(events left)`.

## Arms (all with per-context Kelly bets, as A1)
1. **uniform**: remaining budget spread uniformly after burn-in.
2. **neyman-est**: `q ∝ sqrt(r̂_k)`, set once after burn-in.
3. **rasi-est**: a Robust-ASI-style path from `neyman-est` to uniform, `q(s) ∝ q_neyman^(1−s)·q_unif^s`, `s` chosen on a 21-point grid to minimize `Σ p_k r̂_k/q_k + c·sqrt(Σ p_k q_k^(−2))` with `c = 0.5·sqrt(Σ p_k r̂_k²)`. This is an *adaptation* of the published objective (authors' code read), not a reproduction.
4. **growth-fixed**: `allocate(μ̂, H, r̂)` once after burn-in.
5. **growth-online**: as 4, recomputed every 400 events from all resolved data (e-PS-style sequential learner, adapted; not a reproduction).

## Metrics and decision
- Power (cross `1/α` through the resolved prefix), null crossing rate (must be ≤ 0.07), mean spend (must respect the cap), mean log-wealth.
- **Primary contrast:** `max(growth-fixed, growth-online) − max(uniform, neyman-est, rasi-est)` power in **het** at `ρ ∈ {0, 0.6}`, paired bootstrap over seeds (2,000 resamples).
- **Pass:** primary ≥ **+0.05** with 95% lower bound > 0 in het at both `ρ` values **and** `|growth-online − neyman-est| ≤ 0.02` in **const**.
- **Fail:** otherwise. A fail closes Candidate A (the effect does not survive estimation) and moves work to Candidate C.
- Report hom and anti as descriptive. Choosing the best of two growth arms is a disclosed upward bias, so a pass here is a screen and not a result.
