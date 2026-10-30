# Candidate D gadget-extraction toy: result and decision

**Date:** 2026-10-29. **Status:** frozen adapter toy passed; no ShiftLab pilot or efficacy result.

## Result

Ran `scripts/risk_preserving_approx/test_hsvi_gadget_extraction.jl` against the pinned
`HSVIforOSPOSGs.jl` checkout at `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`, using the registered
game and thresholds in `CANDIDATE_D_GADGET_ADAPTER_PROTOCOL_V1.md`. The exact optimal value is
`11/25 = 0.44`. HSVI returned lower/upper bounds `0.4399999283581686` and
`0.44000007402989255`, a gap of `1.4567172396118266e-7`. The extracted controller evaluates to
`0.44000000000000017`, probes with probability one, and guesses each hidden state after its
corresponding signal with probability one. Maximum gadget residual is `8.381903504606214e-10`;
the extracted controller has three nodes. Solve and extraction took 12.282s and 0.100s in this
run. All registered acceptance thresholds passed.

The adapter's controller evaluator recursively integrates the OS-POSG transition and reward maps
over each hidden state and controller node. This is a finite toy verification of the extraction
path, not an independent implementation of ShiftLab's two-law risk and alternative-cost evaluator.

## Reproduction and provenance

From the repository root, run:

```powershell
& 'C:\Users\nigel\AppData\Local\Programs\Julia-1.13.3\bin\julia.exe' `
  --project=.aris/runs/hsvi-osposg-upstream `
  scripts/risk_preserving_approx/test_hsvi_gadget_extraction.jl
```

The ignored raw log and JSON output are under `.aris/runs/candidate_d_gadget_toy/`. SHA-256:

- Adapter source: `1eca6c388fb35997268614d38660d1fcbaa238497f9eb17838eb672b398dd715`
- Frozen protocol: `26dbe2528f6aa04c5539bb0d3c71cab8da7603ec910079d21c2583817903c562`
- JSON result: `9a15924d53afd7618308cdc8f4ef8078a675d4e5d53b95f60a52a321247abe94`
- Upstream implementation commit: `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`

## Decision

The toy closes the adapter-existence question for this simple finite OS-POSG: the gadget LP can
produce a controller whose value is independently evaluated to the exact toy optimum. It does
not satisfy Candidate D's ShiftLab pilot gate. The OS-POSG reduction, scalarization, strategy
gadget, exact evaluation and multiplier recovery remain an established-method composition; no
new theorem, complexity result, risk guarantee for the switching model, or end-to-end resource
advantage has been shown. Keep this as comparator plumbing only. Do not launch the ShiftLab pilot
without a separate registered costed-resource and exact two-law risk comparison, and do not treat
this result as passing G1 or G2.
