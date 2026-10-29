# Exact certificate for a restricted causal-null master: protocol v1

Registered 2026-10-29 at starting revision `8fd735a`, before this diagnostic.
This is an independent certificate-development check, not an efficacy or
confirmation study and not a new claim about the prior unrecorded policies.

Re-run standard causal-null constraint generation for the frozen T=6 and T=7
cells of `CAUSAL_CUTS_PROTOCOL_V1.md`, with the same 64-cut and 60-second LP
limits. Retain the best recovered root-repaired feasible policy and every
selected endpoint null strategy. Rebuild the decomposed alternative objective as
exact fractions, including exact post-promotion continuation values; check it
agrees with the numerical coefficients to 1e-10.

For the final restricted master, take candidate numerical dual multipliers,
rationalize them, require nonpositive upper-constraint multipliers, and compute
all dual residuals with exact fractions. Every learner realization weight lies in
[0,1]. Subtract the sum of all positive column violations from the rationalized
dual objective. The result is a valid lower bound on the restricted master and
therefore the full robust optimum, provided every cut is an admissible null
strategy and the exact cost/flow/payoff coefficients are verified. Store the
rational dual, sparse null responses, claimed residual correction, best feasible
behavior policy, root activation, and source hashes in a new certificate artifact.
Re-evaluate the policy's exact alternative cost and worst-case causal-null risk.
Do not use a numerical master objective as a certificate.

Write a separate verifier that reconstructs all coefficients and each opponent
flow, checks all cut strategies and every dual residual in exact arithmetic,
rebuilds the saved policy, and verifies its risk and cost without invoking an
optimizer. Report rigorous L<=V*<=U and U-L, plus the reference numerical result
for context. Stop on missing/invalid information or a resource limit; preserve
failures. T=6/T=7 may have different stopping points. No real data, new seeds,
holdouts, or historical output modifications are permitted. A successful
certificate does not itself establish computational advantage or novelty.
