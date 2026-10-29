# Exact joint-risk mixtures of cut-master incumbents: protocol v1

Registered 2026-10-29 after the conservative-mixture result, before execution.
Use the same T=7 64-cut sequence, data-free known HMM cell and solver limits from
`MIXTURE_INCUMBENT_PROTOCOL_V1.md`. Reconstruct each saved candidate's exact
learner realization plan and the never-promote plan. The initial candidate set and
sequence-generation rule are unchanged; do not choose new HMM cells.

Instead of summing each policy's individual worst risk, optimize their root weights
using the joint null-response sequence form. Let X_i be the exact learner
realization vector of candidate i, A the original promotion payoff matrix, and
F y=f the opponent's causal-null sequence form. Define B_ij=X_i' A[:,j]. Solve
numerically for weights w and free opponent dual z:

    min sum_i w_i C_i
    s.t. w>=0, sum(w)=1, B' w - F' z<=0, f' z<=alpha.

This uses one common null response for observationally indistinguishable mixture
branches and preserves the hidden root lottery. It is the standard sequence-form
robust mixture LP, not a new optimization theorem. Solve once after the registered
64-cut sequence. Rationalize and normalize weights; assemble the mixture's exact
realization flow and recover behavioral probabilities with no null access to the
private component. Evaluate the mixture's exact full-history causal-null risk and
its exact alternative cost independently. If risk exceeds alpha, use an exactly
calculated root activation against never-promote. Retain the prior verified safe
incumbent if cheaper. Record rationalized weights, complete behaviors of nonzero
components, raw and activated risk/cost, numerical LP status and residuals, and
the previously verified lower bound. Save a unique signed certificate and verify
it without an optimizer, including the lower-bound certificate.

Compare exact achieved upper with 59747/17500 and report the independently checked
gap. A strictly smaller upper is an improved development incumbent; it is not an
independent confirmatory result, a speedup or proof of novelty. Preserve a negative
or failed result. No real-data rows, holdouts, new seeds or historical files are
opened or overwritten.
