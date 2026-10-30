# Synthetic protocol C1: wealth-snapping approximation of the exact RPOQ oracle (frozen before any run)

**Date:** 2026-10-30. **Candidate C** (fallback in `CANDIDATE_RANKING.md`). Synthetic, exact, no data. Code: `src/shiftlab/dive/rpoq_next/approx_dp.py` (after this file is committed). **Claim level: none.** State aggregation and approximate dynamic programming are standard; this tests whether the *specific* exact RPOQ problem admits a cheap policy with certified loss.

## Question
The exact oracle (S3 instance, `T=10`, `d=2`, `α=0.2`, bet fraction 0.5, `q ∈ {0.25, 0.5, 0.75, 1}`) needs about 0.9M to 2.8M states and 40 to 200 s per budget. Does snapping the resolved-prefix wealth to a log-scale grid of width `δ` give a policy that keeps most of the gap between the best constant table and the exact optimum, at a fraction of the cost?

## Method
- Value recursion identical to `rpoq_exact.Evaluator`, except that the wealth entering `post_value` is snapped to `exp(round(log(w)/δ)·δ)` (alarm checks use the unsnapped wealth first). The policy is `act()` of this snapped solver.
- **Certified evaluation:** the snapped policy is then evaluated by the *exact* evaluator (true dynamics, true wealth, the policy reading snapped wealth), under both the alternative (power) and the null (false-alarm probability). No Monte Carlo and no approximation in the reported power.
- `δ ∈ {0.5, 0.25, 0.1}`; budgets `B ∈ {3, 4, 6}`. The exact optimum and best constant table are the S3 registered values (`outputs/rpoq_s3_structure_v1/results.json`, unchanged).

## Metrics and decision
- States visited and wall-clock seconds of the snapped solve (policy evaluation reported separately).
- **Recovery** `ρ = (power_snapped − power_best_constant) / (power_opt − power_best_constant)`, defined where the gap exceeds 0.01 (`B=4`: 0.0125, `B=6`: 0.0307; `B=3` has gap 0.027 but power below 0.04, reported only).
- **Pass (screen):** for at least one `δ`, at `B ∈ {4, 6}`: `ρ ≥ 0.8`, null false-alarm ≤ `α = 0.2`, and the snapped solve visits ≥ 5× fewer states and runs ≥ 3× faster than the exact solve for the same budget. Otherwise: not supported.
- A pass is an engineering result about a toy instance. It does not establish scaling, novelty, or any real-data effect.

---

# C2: threshold-adaptive snapping (revision 1; frozen before running; informed by the C1 failure)

**Disclosure.** C1 was run and seen first. It reduced states by 100 to 800× but the snapped policies lost most of the oracle's value (certified power at `B=4` about 0.11 to 0.16 vs 0.356 for the best constant table). The hypothesis for the revision comes from that outcome and from S3 (optimal decisions depend on the fine wealth lattice), so C2 is a development revision on the same instance, not an independent confirmation.

**Failure it targets:** coarse wealth bins blur the distance to the alarm threshold `1/α = 5`, which determines whether one more label can cross it.

**Change (only):** snap with width `δ_c` when `w < (1/α)·e^{−1}` (about 1.84) and with `δ_f = 0.02` otherwise (between 1.84 and the threshold). Alarm checks still use the unsnapped wealth. `δ_c ∈ {0.5, 0.25}`.

**Decision rule:** identical to C1 (recovery ≥ 0.8 of the gap to the best constant table, null false-alarm ≤ 0.2, ≥ 5× fewer states and ≥ 3× faster than the exact solve, at `B ∈ {4, 6}`). One revision only; if C2 fails, Candidate C is closed.

**Bookkeeping fix (no result change):** the certified quantities are renamed `policy_power` and `policy_null_alarm` (in C1 a key collision made the printed `exact_power` the snapped policy's certified power, not the optimum). The optimum is reported as `optimal_power`.
