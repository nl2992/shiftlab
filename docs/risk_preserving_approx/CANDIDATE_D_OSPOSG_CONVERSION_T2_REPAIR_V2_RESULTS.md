# Candidate D OS-POSG conversion T=2 repair v2 results

**Protocol:** `CANDIDATE_D_OSPOSG_CONVERSION_T2_REPAIR_V2_PROTOCOL.md`

**Run date:** 2026-10-29

**Status:** PASS for scalarized value/compiler equivalence at this T=2 instance.

The separate v2 compiler writes explicit zero rewards while leaving the v1
compiler and failed model untouched. The independent structural validator
passed all 101 legal state/action triples: none lacked a reward or transition,
all outgoing transition masses were one within `1e-12`, every
partition/action/observation had a unique target partition, and the initial
belief had mass one. The pinned parser read 65 states, 28 partitions, 118
transitions and 101 rewards.

The original scalarized sequence-form LP remained optimal at `-1.0`. HSVI
completed its solve successfully: the captured upstream log ended with lower
bound `-1.00000`, upper bound `-1.00000`, gap `0.00000`, status `OK`, and
reported elapsed time 18.16 seconds. The interval contains the LP value and
meets the registered `1e-4` width and 30-second HSVI limits.

The Julia command then exited with code 1 because the post-solve reporting
expression called `LB_value` unqualified, although that helper is not exported
by the pinned package. This happened after the solver's `OK` result; it is a
harness reporting error, not a solver failure. The v2 protocol's value result
is therefore established by the solver's own final log row plus the previously
written independent LP value. Do not rerun HSVI just to restate this result.
Future Julia harnesses should call the helper as
`HSVIforOSPOSGs.LB_value(...)` and `HSVIforOSPOSGs.UB_value(...)`.

The output bundle is under ignored
`.aris/runs/candidate_d_osposg_conversion_t2_repair_v2/`:

- model SHA-256: `0e8450ea81024d9adac0137c926cc9101bdd96df76f57d4e8bbc94f6a4ce92ee`
- structural validation SHA-256: `4336151d4d7abe50dc0d8691dbfdb66e77dddd6215bf2c5012a404ca7cbbac7`
- HSVI log SHA-256: `e82066ef01eb7c84bcdd2380c33472c364efba630f3de00b1ddd15b9bac3536e`
- v2 compiler SHA-256: `9ecd4bd743d6b91974b5821e6e8b4060c7ef0b2b8f209102891812f135313567`
- independent validator SHA-256: `f1fce8995ab6d0425068988b04ac308b8c14951108b7722e9bd5b9ff0d5755a6`

This is one scalarized game-value equivalence check, not a risk/cost policy
recovery result, a baseline win, a novelty result, or a ShiftLab efficacy test.
It does not prove that state/reward conversion plus approximation preserves
the constrained optimum, nor that HSVI has an end-to-end resource advantage.
Proceed only to a source-level audit of approximation error and multiplier
recovery, then preregister a small exact-oracle pilot only if strategy
extraction and exact causal-null risk verification are implementable.
