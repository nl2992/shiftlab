# Candidate D T=2 strategy extraction and exact verification protocol

**Registered:** 2026-10-29, before implementing the model-specific extraction
runner. This is an adapter and policy-verification check, not an efficacy,
novelty, or baseline-superiority experiment.

## Frozen instance

Use `T=2`, `B=1`, delay `1`, `alpha=1/10`, query cost `1/100`, switch cost
`1/10`, the default HMM, `lambda=1`, and `gamma=0.9`. The scalarized LP must be
optimal at `-1.0`. Use HSVI `neighborhood=1e-8`, `presolve_epsilon=1e-8`,
`presolve_time_limit=10s`, value tolerance `1e-4`, and solver limit `30s`.
Reuse the validated v2 explicit-zero-reward serializer, but write a fresh bundle
to `.aris/runs/candidate_d_t2_extraction_v1/` and record hashes.

## Required procedure

1. Solve once and require the HSVI root interval to contain the independent
   scalarized sequence-LP value with width at most `1e-4`.
2. Extract a learner controller from a valid root HSVI lower-bound vector using
   the registered gadget LP. Construct every positive-probability action and
   observation branch; do not prune small positive probabilities by an arbitrary
   cutoff. Record gadget feasibility residuals and controller nodes.
3. Export the controller against the compiled learner information histories.
   Map it into the original `CausalSwitchingGame` policy class without exposing
   hidden mode, pending labels or opponent actions to the learner.
4. Independently evaluate exact-rational alternative decision/query/switch
   costs and the full causal-null first-promotion risk using the repository
   policy evaluator. Verify distributions normalize, all actions are legal for
   the remaining pathwise budget, and evaluation uses delayed label release.
5. Require `1 <= C_alt + R_null <= 1 + 5e-3` for this lambda-one instance,
   consistent with exact scalarized optimum `1`. Also require maximum gadget
   residual at most `1e-7`. Treat any mismatch, missing information history,
   timeout, or unsupported risk evaluation as a no-go; preserve artifacts.

Report solve, extraction and exact-verification time separately and together,
controller nodes, HSVI search counts, exact `C_alt`, exact `R_null`, scalarized
gap and maximum budget. Do not compare against calendars as a performance claim,
run T=6, search additional multipliers, open real data/holdouts, or allocate new
seeds under this protocol. Passing only qualifies the adapter for a separately
registered exact-oracle pilot; it does not establish feasibility at alpha or a
risk-bracketing/cost guarantee.
