# Branchwise verification of the T=10 IID-relaxation policy

Registered 2026-10-29 before execution. Input is the saved policy from
`iid_relaxation_t10_stress_v1.json`; no optimization is repeated and no data,
seeds or holdouts are accessed.

Rebuild the T=10/B=4/d=2 learner information tree and reconstruct the saved
behavioral policy from exact action probabilities. Require that it has exactly
one randomized information state and that every other information state is
deterministic. Split that state into its two deterministic actions, yielding the
two candidate root branches. For each branch, exhaustively enumerate all 1,024
potential-label tapes indexed by event time, simulate the branch using only
released labels, verify the hard query cap, and check coordinatewise monotonicity
of the first-promotion event on every cover edge.

Independently compute each branch's exact IID fair-tape risk, full adaptive
causal-null risk and alternative expected cost. Verify that monotonicity implies
each branch's robust risk equals its IID risk under the registered null family
(each queried label has conditional success probability in `{0,1/2}`), and that
the public-history root mixture's weighted branch risks and costs reproduce the
saved candidate's exact values. Save every violation, branch metric, input hash,
runner hash and verifier state count. Any extra randomization, nonmonotonicity,
hard-cap violation or metric mismatch falsifies this branchwise certificate.

The coupling statement is a sufficient structural certificate, not a novelty
claim. This check cannot establish an approximation theorem or general runtime
advantage.
