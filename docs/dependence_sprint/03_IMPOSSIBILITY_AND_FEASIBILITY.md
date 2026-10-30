# 03 Impossibility and feasibility (GATE B)
Code commit at start: `8552911` (branch `research/shiftlab-mandate-gap-closure-2026-10-30`); sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: `scripts/dep_sprint/gate_ab.py` (exact enumeration, n=16), `scripts/dep_sprint/gate_b_oracle.py` (T=2000, 6000 paths per cell) → `outputs/dep_sprint/gate_ab.json`, `gate_b_oracle.json`.

## Theorem B1 (persistence obstruction) — status: PROVED (elementary); not independently reviewed
Let L_t in {0,1} follow the lazy-resample chain C(delta, pi): x_1 ~ Bern(pi); at each step with probability delta draw x_{t+1} ~ Bern(pi) afresh, else x_{t+1} = x_t. It is stationary with marginal Bern(pi) and encodes a hidden regime of mean duration 1/delta. Let P_pi denote the law of the first T steps. For every (possibly randomized, adaptive-query, delayed, budget-limited) test phi with P_{r0}(reject) <= alpha,
  P_{r0+eps}(reject) <= alpha + eps (1 + (T-1) delta).
*Proof.* Couple the two chains with the same uniforms for the switch events and the Bernoulli draws, using the maximal coupling of Bern(r0) and Bern(r0+eps) at each draw. The paths differ only if one of the 1 + Bin(T-1, delta) draws differs, which has probability <= eps each. So TV <= eps(1+(T-1)delta), and any observation scheme (queries, delays, budgets) is a randomized function of the path, so data processing gives the same bound. QED.
**Consequence:** to reach power beta >= 0.8 against eps = 0.1 at alpha = 0.05 one needs (T-1)delta >= 6.5, i.e. at least ~7.5 independent regime draws in the horizon; this is necessary, not sufficient.

## Numerical checks
* Exact Neyman-Pearson power (full enumeration, n=16, eps=0.1, alpha=0.05): 0.067 (delta=5e-4), 0.068, 0.071, 0.080, 0.107, 0.213 (delta=1). All below the bound (0.151..); exact TV 0.1002 <= coupling bound 0.1008 at delta=5e-4.
* **Oracle ceiling at the real horizon** (T=2000; the test knows delta, pi0, pi1 exactly, Monte-Carlo NP threshold at alpha=.05):

| expected regime draws T*delta | regime length | oracle power, eps=0.05 | oracle power, eps=0.10 |
|---|---|---|---|
| 0.2 | 10,000 | 0.000 | 0.002 |
| 1 | 2,000 | 0.022 | 0.024 |
| 5 | 400 | 0.069 | 0.099 |
| 20 | 100 | 0.092 | 0.184 |
| 100 | 20 | 0.193 | 0.476 |
| 500 | 4 | 0.606 | 0.976 |

## Decision branch
* The desired guarantee (level-alpha *and* useful power for the stationary-average null) is **impossible without structure** (B1) and, for the persistence range that matters for financial / model-risk clusters (regimes of 20-400 steps in a 2000-step horizon), **has no useful power even for an all-knowing oracle** (power 0.07-0.48 at eps = 0.05-0.1).
* Minimal structure that avoids the obstruction: a lower bound on the regime-switching rate (known mixing envelope / minimum effective sample size) of order T*delta >= ~100-500, i.e. near-iid. Within that class the problem is *feasible but practically uninteresting here*.
* One reformulation attempted (as required): replace H0-marg by H0-cond (the forward conditional excess). That null **is** testable with the existing monitors (Gate A, rows 1-2) and needs no mixing assumption; its price is that a persistent high-loss stretch is *correctly* an alarm.
**GATE B: FAIL for the original goal** (marginal guarantee with useful power under persistent dependence); **PASS only for** (i) the near-iid class and (ii) the reformulated conditional null. No non-vacuous operating regime remains for a *new* dependence-robust marginal-null monitor.
