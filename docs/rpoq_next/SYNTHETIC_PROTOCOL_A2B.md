# Synthetic protocol A2b: placebo and fair-bet diagnostic (frozen before any run)

**Date:** 2026-10-30. **Follows:** A2 (registered verdict NOT PASSED: tie control violated; see `SYNTHETIC_RESULTS.md`). Diagnostic, synthetic, no claim. Code: `screen_a2.py` extended (default behavior unchanged).

## Why
In A2, `growth_fixed` beat Neyman by +0.12 in the **const** setting, where every context is identical and no allocation can be informative. Two untested explanations: (H-conc) concentrating labels in one context speeds up per-context bet learning regardless of *which* context; (H-bet) the A1/A2 comparators were handicapped by per-context bets, so the strongest equally equipped baseline was not used.

## Arms added (same stream, burn-in, learning, cap, seeds as A2)
- **random_conc:** after burn-in, all spare labels go to one context chosen uniformly at random per seed (independent of data): `q = 0.02` elsewhere, the remainder on the chosen context, capped at 1. A placebo with growth-fixed's concentration but no information.
- Each of `uniform`, `neyman`, `growth_fixed`, `random_conc` is run with **both** bet types (ctx, common). The strongest equally equipped baseline for any comparison is the better bet type for that arm in that setting (a disclosed upward bias for the baseline).

Settings: null, const, het; `ρ ∈ {0, 0.6}`; 1,000 seeds.

## Decision (applied to het and const)
- **Concentration explains the effect** if `growth_fixed − random_conc < 0.05` (or its 95% lower bound ≤ 0) in het at both `ρ`, **or** `random_conc ≥ growth_fixed − 0.03` in const. Candidate A is then falsified as a *growth-awareness* mechanism (the gain is a concentration/bet-learning artifact).
- **Growth-aware selection adds value** only if `growth_fixed(best bet) − max(random_conc(best bet), uniform(best bet), neyman(best bet)) ≥ +0.05` with a positive 95% lower bound in het at both `ρ`, and the const gap to `random_conc` is within ±0.03.
- Anything else: inconclusive; report as such.
- Null calibration (≤ 0.07) and the cap must hold for every arm.
