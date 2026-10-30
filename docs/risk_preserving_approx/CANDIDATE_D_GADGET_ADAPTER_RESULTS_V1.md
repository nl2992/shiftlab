# Candidate D gadget adapter toy result

**Date:** 2026-10-29. **Status:** PASS for the frozen toy adapter protocol only.

The pinned HSVI solver and branch-local Algorithm 5 gadget adapter produced a
controller on the preregistered two-hidden-state toy game. Its independently
enumerated payoff was `0.44000000000000017` against exact optimum `0.44`;
the solver's reported gap was `1.4567e-7`, maximum gadget residual was
`8.3819e-10`, and the three-node controller probed with probability one and
guessed according to both signals. The run took 12.043 seconds for HSVI and
0.102 seconds for extraction.

This verifies only the basic gadget algebra, history update, and toy controller
enumerator on a one-action-opponent game. It does not verify extraction against
an active adversarial strategy, finite-horizon switching semantics, causal-null
risk, or any ShiftLab economic or compute result. It does not pass G1–G3.

## Provenance

- Protocol: `CANDIDATE_D_GADGET_ADAPTER_PROTOCOL_V1.md`
- HSVI upstream: `brozjak2/HSVIforOSPOSGs.jl`, commit
  `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`
- Runtime: Julia 1.13.3; Julia project instantiated from the pinned checkout.
- Command: `julia --project=.aris/runs/hsvi-osposg-upstream scripts/risk_preserving_approx/test_hsvi_gadget_extraction.jl`
- Preserved output: `.aris/runs/candidate_d_gadget_toy/result.json` and `run.log`
- SHA256 adapter script: `1ECA6C388FB35997268614D38660D1FCBAA238497F9EB17838EB672B398DD715`
- SHA256 toy fixture: `1EC3E77CBDE142ED8CA02E86C44976C669CA2F7C118621E6EDDDA70F6A96C94D`
- SHA256 protocol: `26DBE2528F6AA04C5539BB0D3C71CAB8DA7603EC910079D21C2583817903C562`
- SHA256 result JSON: `640FFBD0573DE5314E77BA03A9F6BA728A71ED99D507F4F51D4AA28A0647508C`

## Decision

Do not start a ShiftLab efficacy pilot yet. The exact reference LP can expose a
numerical risk-constraint dual for post-hoc comparison, but using that exact
dual to select multiplier endpoints would make the proposed scalable recovery
procedure depend on solving the benchmark LP. More importantly, the toy has no
strategic opponent, so this result does not establish that the adapter's
controller is a security strategy in the full game. The next bounded technical
step is an adversarial toy with at least two opponent actions and an independent
maximin controller evaluator. Only after that passes should the D3 pilot be
reconsidered, with a genuine, checkable multiplier-bracketing rule and an
end-to-end cost comparison preregistered in advance.
