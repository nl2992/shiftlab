# Contribution statement (honest scope)

**What could be written up.** These are accurate claims, not main-track novelty.

1. An exact, certified solver for ShiftLab's two-law budgeted switching problem under the full-history causal
   null. It returns a policy with exact rational robust risk `<= alpha` and a certified gap to the unrestricted
   optimum `V*` of at most 4e-14 on every tested cell.
2. An IID-first lazy constraint-generation implementation (FCG-fast). It is 1.3–1.85× faster end to end than
   the exact decomposed sequence-form reference at T=10, B=4, d=2. These are single fresh-process runs, and the
   reference timing varies by 20–38% between runs. The gain is **unattributed**: it mixes skipping the null tree,
   a belief cache the reference lacks, and a float build.
3. An empirical regularity. On every tested T=10 cell the IID-relaxed optimum is already causal-safe, and the
   adversarial cuts are needed only in small-horizon reversal regimes, where they recover 0.3–0.5% of cost.

**What must not be claimed.**
- A new optimisation principle. FCG is sequence-form oracle / constraint generation (Bošanský et al. 2014).
- A new risk theorem. The identity reduces to Krale et al. 2025.
- That cut generation causes the T=10 speed-up. It used zero cuts there.
- Any result outside synthetic development cells.
- Superiority over external solvers, which were not run.
