# Candidate D T=2 extraction and exact verification results

**Protocol:** `CANDIDATE_D_T2_EXTRACTION_PROTOCOL_V1.md`

**Run date:** 2026-10-29

**Status:** PASS for the adapter; no efficacy or baseline win.

On the frozen `T=2, B=1, d=1, lambda=1` game, the independently assembled
scalarized sequence LP is optimal at `-1`. HSVI returned lower/upper bounds
`[-1.0000000555, -1.0000000000]`, width `5.56e-8`, in 16.852 seconds. Gadget
extraction took 0.285 seconds, created four controller nodes, and had maximum
local feasibility residual `4.45e-16`.

The extracted controller was rationalized and mapped into the original
`CausalSwitchingGame` policy histories. The independent exact-rational evaluator
found alternative decision cost `1`, query cost `0`, switch cost `0`, total
alternative cost `1`, and full causal-null first-promotion risk `0`. It uses no
queries and never promotes, so it respects the pathwise budget. Thus
`C_alt + R_null = 1`, matching the exact scalarized optimum at lambda one.
Controller action distributions normalized exactly after rationalization; the
largest rationalization L1 change was `1/4503599627370496`.

This demonstrates that the gadget adapter can produce and verify a policy on
this tiny compiled switching game. The returned policy is the no-query,
never-promote controller. There is no evidence it improves economic cost over
the exact constrained oracle or any calendar baseline, meets a useful
risk/value recovery bracket, or scales. The result therefore passes only the
plumbing gate. Do not describe it as a promising method or novelty result.

The ignored run bundle is under
`.aris/runs/candidate_d_t2_extraction_v1/`:

- OS-POSG model SHA-256: `0e8450ea81024d9adac0137c926cc9101bdd96df76f57d4e8bbc94f6a4ce92ee`
- metadata SHA-256: `53e8ff3bcffa227822464fd66a642fbf5581f891de7c385278cbeece08c113b5`
- structural validation SHA-256: `4336151d4d7abe50dc0d8691dbfdb66e77dddd6215bf2c5012a404ca7cbbac7`
- HSVI/extraction log SHA-256: `1d35f875e36d2bce6af8d5db246a14b568d6de7210a2f64888a97188d2aeafb4`
- controller SHA-256: `cc786df79c10392305691993f6a272ebc1cae85ab2be532e44502bf32d39ffab`
- exact policy verification SHA-256: `26407800d4ff91a1467f94c1ad1d785559da268c47f0ed9f20fa11a6cd4d8fca`

The adapter source files and protocol are branch-local and committed with this
result. Passing this adapter check does not establish a multiplier search or
risk-bracketing method. The next decision is whether a preregistered fixed
multiplier set can produce a genuinely informative, exactly verified policy
pair at a small instance, with an audited bound relative to the exact
constrained oracle. If not, stop Candidate D as a baseline and return to the
remaining structural research directions. Keep G1–G3 and the real-data gate
open.
