# Synthetic protocol A3: confirmatory screen with fair baselines and nonstationary alternatives (frozen before any run)

**Date:** 2026-10-30. **Follows:** A1, A2, A2b (`SYNTHETIC_RESULTS.md`). Fresh seed offset; A1–A2b are not edited. Synthetic, exploratory, no claim. Code: `screen_a2.py` extended (`confirm` mode); the nonstationary settings are added without changing existing defaults.

## Changes that address earlier defects
- **Fair baselines:** every arm is run with both bet types and each arm is scored with its better bet type per setting (a disclosed upward bias for the baselines).
- **Placebo:** `random_conc` included.
- **Tie control:** constant-SNR `const` with the criterion defined against the *best equally equipped baseline*, not a single arm.
- **Nonstationary alternatives (new):** the realistic failure mode of concentrating on a burn-in favourite.

## Settings (`N=4000`, `B=400`, `d=20`, burn-in 400 events / 100 labels, `α=0.05`, `ρ ∈ {0, 0.6}` unless stated)
- **null** (`ρ=0.6` only), **const**, **het**: as A2.
- **het_onset** (`ρ=0.6` only): all `μ_k = 0` before event 2000 and `μ_k = MU_HET[k]` after. The burn-in sees only the null.
- **het_flip** (`ρ=0.6` only): `μ_k = MU_HET[k]` during burn-in; from event 400 on the signals are reversed (`μ_k = MU_HET[7−k]`), so the burn-in favourite becomes the weakest context. The proxy `H_k` uses the initial `μ_k` (a stale proxy).

Seeds: 1,000 per setting, seed base 2026, common random numbers.

## Arms
`uniform`, `neyman`, `rasi`, `growth_fixed`, `growth_online`, `random_conc` (as in A2/A2b), each with `ctx` and `common` bets.

## Decision (all applied with 95% paired-bootstrap intervals, `Δ = growth_fixed(best bet) − max over {uniform, neyman, rasi, random_conc}(best bet)`)
1. **Validity:** null crossing ≤ 0.07 for every arm; spend ≤ 400. A breach is a bug.
2. **Tie:** const `Δ` within `[−0.04, +0.04]`.
3. **Primary:** het `Δ ≥ +0.05` with lower bound > 0 at both `ρ`.
4. **Robustness:** het_onset and het_flip `Δ ≥ −0.03`. If `Δ` is materially negative there, the claim is restricted to stationary heterogeneous-SNR settings, and this is reported as a failure condition.
- **Candidate A is supported (as a screen only) if 1–4 all hold; supported-with-restriction if 1–3 hold and 4 fails; falsified if 1 or 3 fails.**
