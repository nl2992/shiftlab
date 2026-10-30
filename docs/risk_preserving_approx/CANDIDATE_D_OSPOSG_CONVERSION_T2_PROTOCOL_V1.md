# Candidate D OS-POSG conversion T=2 protocol

**Registered:** 2026-10-29, before running the converter or HSVI on this model.
This is a model/compiler equivalence check only, not a ShiftLab efficacy result.

## Frozen instance and comparison

Compile the existing two-law causal switching game with horizon `T=2`, query
budget `B=1`, delay `d=1`, `alpha=1/10`, query cost `1/100`, switch cost
`1/10`, and the repository's default exact HMM (`transition01=transition10=1/10`,
`emission0=1/4`, `emission1=3/4`, `prior1=1/2`). Use scalarization multiplier
`lambda=1` and OS-POSG discount `gamma=0.9`. The transformed root mode is
alternative/null with probabilities `1/2,1/2`; the alternative cumulative
cost and null first-promotion indicator are each multiplied by two and
negated as learner rewards. Rescale the round-t reward by `gamma^(-2(t-1))`
at its request microstage. Null endpoint responses are `0` and `1/2`.

Compare (a) HSVI's root value interval for the compiled OS-POSG and (b) an
independently assembled scalarized sequence-form LP over the original
`CausalSwitchingGame` learner and opponent flow constraints. The exact identity
is `OSPOSG_value = -min_pi(C(pi)+lambda*R(pi))`. Require the sequence-form LP
to be optimal, the OS-POSG interval to contain its value, and interval width
at most `1e-4` within a 30-second HSVI limit. Validate parser counts and the
input model hash. A parse/model mismatch, non-containing interval, timeout or
excess width is a recorded no-go; do not tune the model or threshold.

Preserve generated game, logs and JSON under ignored
`.aris/runs/candidate_d_osposg_conversion_t2/`. No T=6 run, risk/cost policy
claim, baseline comparison, real data, holdout or new seed is part of this
protocol.
