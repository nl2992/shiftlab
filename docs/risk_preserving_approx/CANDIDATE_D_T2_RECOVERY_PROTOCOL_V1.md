# Candidate D T=2 multiplier-recovery diagnostic

**Registered:** 2026-10-29. Development diagnostic only; no seed allocation,
efficacy claim or novelty test.

## Frozen setting

Use the same `T=2`, `B=1`, `d=1`, `alpha=1/10`, default HMM, query cost
`1/100`, switch cost `1/10`, `gamma=0.9` instance. Evaluate the fixed
multiplier pair `{lambda=1/100, lambda=1}`. Reuse the already produced lambda-one
controller and exact verification from
`CANDIDATE_D_T2_EXTRACTION_RESULTS_V1.md`; do not rerun it. Compile, solve once,
and extract a controller at lambda `1/100` in a new ignored run directory. Use
the same HSVI settings and 30-second limit as the extraction protocol.

## Audits

1. Independently evaluate exact-rational `C_alt` and full causal-null `R_null`
   for both controllers. Record maximum pathwise queries and controller sizes.
2. Independently solve the original constrained sequence-form LP at
   `alpha=1/10` and recover its optimal risk-constraint dual multiplier
   `lambda_star` from the LP marginal. This exact oracle is an audit only and
   must not be used to choose or tune the Candidate D multipliers.
3. A bracket is certified only if the lambda-`1/100` policy has risk at least
   `alpha`, the lambda-one policy has risk at most `alpha`, and the exact LP dual
   satisfies `lambda_star in [1/100,1]`. Otherwise record no bracket.
4. If bracketed, calculate the root-mixture weight and exact rational mixture
   cost/risk. Report the conditional theorem bound `epsilon + delta` using the
   actual multiplier interval width; do not call it useful if it exceeds the
   observed exact-oracle cost gap by orders of magnitude.
5. Compare the mixture cost/risk to the exact constrained oracle and the
   no-query/never-promote baseline. Include total end-to-end time for the new
   lambda run, extraction, exact verification and oracle audit. A performance
   win is not expected from this two-point diagnostic and must not be claimed
   from scalarized value matching alone.

Stop after this pair. Do not insert extra multipliers, tune a grid, run T=6,
compare to calendars, open real data/holdouts, or use confirmation seeds. A
failure to certify a useful bracket closes this Candidate D recovery route as
currently specified; it does not end the broader ShiftLab research objective.
