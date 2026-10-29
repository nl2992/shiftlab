# T=8 exact certificate for the first-promotion decomposed oracle

Registered 2026-10-29 before implementation and execution. This is a
deterministic certificate attempt for the already exposed `T=8`, `B=3`, `d=1`
cell with alpha `1/10`, query fee `1/100`, switch fee `1/10`, symmetric
transitions `1/4`, emissions `(1/20,19/20)`, and prior `1/2`.

Construct the exact objective coefficients of the full first-promotion
decomposition, solve its registered sequence-form LP once with the existing
60-second limit, rationalize a candidate dual, and verify an exact feasible
lower bound with the optimizer-free residual correction used by the T=7
certificate procedure. Separately solve the `m=2` pre-promotion cap and
independently reconstruct exact expected cost and full-history causal-null risk.
Write a new certificate and verifier without modifying the T=7 certificate or
any historical outputs. If both LP lower and cap-policy upper coincide, the
restricted cap policy is certified globally optimal for this cell under the
proved first-promotion decomposition; otherwise report the exact bracket and do
not infer optimality.

Record every failed step. This certificate uses the decomposed formulation and
its exact reduction theorem; it is not a completed generic full-sequence-form
builder run. It establishes neither a general cap guarantee nor novelty, and it
does not open real data, seeds or holdouts.
