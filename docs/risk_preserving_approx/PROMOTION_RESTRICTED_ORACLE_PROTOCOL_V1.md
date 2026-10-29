# Promotion dominance restricted-oracle verification v1

Registered before execution on 2026-10-29 after the exact bound diagnostic.
Use the original T=6, B=3, d=1 HMM and costs of
`PROMOTION_DOMINANCE_PROTOCOL_V1.md` with alpha=1/10. Build the untouched
first-promotion game and its same sequence-form LP. For each pre-promotion
information set, mark every immediate-promotion action when its fully-revealed-
future-state economic lower bound L is at least the incumbent-only continuation
cost S (epsilon 0), or at least S-1/100 (epsilon 1/100). Force those realization
variables to zero in a separate LP solve. Keep all pre-promotion action, query,
null information and risk constraints otherwise identical. Run the unrestricted
solver as comparator. Record objective, exact-rational recovered cost and causal
null risk, solver residuals, marked information sets and columns, and all failures.

For epsilon zero require a returned feasible value matching the reference within
1e-7; for epsilon 1/100 require the returned feasible value within 1/100 + 1e-7.
Compare exact recovered-policy null risk to alpha. If floating recovery exceeds
alpha, record the gap rather than calling it safe. Use a unique result file, and
record runner/protocol/reference hashes. Solver time and builder-node limits remain
unchanged. This is a deterministic single-cell structural test, not a claim of
statistical efficacy, speedup, source-level novelty, or real-data benefit.
