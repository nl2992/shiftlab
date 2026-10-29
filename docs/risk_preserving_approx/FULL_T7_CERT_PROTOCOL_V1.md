# T=7 full decomposed-LP rational certificate: protocol v1

Registered 2026-10-29 after the pre-promotion-cap development screen and before
this certificate run. The goal is a tighter, independently checkable lower bound
for the original full B=3 oracle; this does not constitute a new seed, efficacy
study or real-data evaluation.

Use the T=7, B=3, d=1 registered HMM from
`PREPROMOTION_CAP_PROTOCOL_V1.md` and the unchanged full first-promotion LP.
Reconstruct objective coefficients as exact fractions. Solve the original LP once
with its existing 60-second limit to obtain candidate dual multipliers. Rebuild
its free-variable dual equality exactly by converting the null-related inequality
multipliers into an exact feasible opponent sequence flow: rationalize the scalar
risk multiplier, recursively normalize endpoint-action weights at each opponent
information set, and multiply the flow by the scalar. Rationalize the learner-flow
duals. Verify the inequality-dual signs and every free-column equality exactly;
subtract the sum of positive learner-column dual residuals using x_j<=1. If an
exact flow cannot be constructed or checks fail, save the failure and do not
claim a bound. Record the exact-risk recovered full-policy upper and complete
rational certificate in a new non-overwriting artifact.

Create a separate optimizer-free verifier that rebuilds the matrices, exact
objective and null flow, checks signs, free-column equations, residual correction,
checksum, and recovered policy risk and expected cost. Compare the resulting
certified lower bound with the saved pre-cap m=2 safe policy cost, independently
re-evaluating that policy if its full behavior is available. A numerical LP value
alone is not a lower certificate. Do not modify prior T=6/T=7 cut certificates,
historical outputs, or open real data or seeds.
