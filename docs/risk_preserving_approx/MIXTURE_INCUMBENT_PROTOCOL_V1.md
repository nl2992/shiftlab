# Risk-certified mixture of cut-master incumbents: protocol v1

Registered 2026-10-29 at starting revision `e61d63e`, before implementation or
execution. This is a deterministic candidate-B upper-bound diagnostic for the
existing T=7 two-law problem, not a novelty or efficacy claim.

Re-run the frozen T=7, B=3, d=1, alpha=1/10 HMM cut-generation cell from
`CAUSAL_CUT_CERT_PROTOCOL_V1.md`, with at most 64 cuts and identical LP tolerances.
Collect every recovered pre-promotion policy, its exact causal-null risk R_i and
exact alternative cost C_i. Include the deterministic no-query/never-promote
policy as (R,C)=(0,C0). For a root mixture with weights w_i, use the conservative
risk certificate sum_i w_i R_i, which bounds the causal-null risk even if the
adversary learns which component was selected. Require nonnegative weights summing
to one and weighted risk <=alpha; minimize weighted cost. In this two-constraint
LP it suffices to enumerate singleton feasible components and all pairs that
straddle alpha. Use exact fractions for the final weights, risk bound and cost.

For each master iteration, compare the best feasible mixture over candidates seen
so far with the old repair rule's best candidate-plus-never-promote mixture.
Use the same generated candidates and no future iterations. Save the best selected
components' complete behavior records, exact costs and risks, exact mixture
weights, a canonical checksum, total per-stage solver times, and the per-iteration
best upper bounds. Preserve failures and stop reasons; do not overwrite prior
certificates or outputs.

Construct the actual mixture's realization flow exactly from component behavioral
probabilities. Derive conditional behavior from its mixed realization flows without
revealing the root coin to the null; retain the same post-promotion HMM
continuation. Independently compute its exact worst-case causal-null risk and
expected alternative cost, and require risk <= the conservative certificate and
<=alpha. Verify its known pathwise query cap. Also independently recheck the
existing T=7 rational lower certificate with the optimizer-free verifier, then
report the rigorous new upper minus that existing lower; do not treat the fresh
master objective as a certified lower bound.

Compare with the previous best upper `59747/17500` only as a development result;
selecting from the same known-model cell is not confirmation. Record whether the
method is better, equal or worse, the achieved exact gap and all resource limits.
Mixture optimization is standard convexification and is not a new method claim.
Do not infer end-to-end speed or scaling from this single diagnostic; no seeds,
real-data rows or reserved holdouts are opened. Save a unique artifact and verifier.
