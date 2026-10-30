# Candidate D sequential adversarial gadget development result

**Date:** 2026-10-29. **Status:** exploratory development check passed.

This two-stage, five-state zero-sum toy has a hidden state in `{0,1}`. At each
stage the learner chooses a row and the fully informed opponent simultaneously
chooses a column; matching earns `+1` and mismatching earns `-1`. The opponent's
first column determines the learner's next observation. The exact security
value is zero at each stage and under the full two-stage game. This was a
development check, not a preregistered ShiftLab efficacy pilot or a novelty
test. The initial OS-POSG parser checks caught and corrected fixture count and
transition-index errors before HSVI ran; those do not count as method failures.

Using the pinned HSVI source and the branch-local gadget extractor, the
independently checked root policy was `(0.50000002, 0.49999998)`. After either
opponent-generated observation, the continuation row-0 probability was `0.5`.
The statewise minimum payoff against either pure opponent action was zero in
both continuation branches and `-3.98e-8` at the root; the largest absolute
state/action payoff residual was `3.98e-8`. The final evaluator also checks the
full discounted game against state-dependent first-stage and
history-dependent second-stage opponent actions. The HSVI interval width was
`1.7689e-7`, all-constraint gadget residual `7.9602e-8`, controller size five
nodes, and solve time 6.280 seconds on the final recorded rerun.

During development, the first recursive version used the lower-bound solver's
single opponent response to decide which observation branches to recurse into.
That can omit branches another legal opponent strategy reaches. The extractor
now uses a full-support reference response only to select a child belief for
gadget tie-breaking and recursively includes every reachable observation.
This toy supports that implementation choice for this game; it does not prove
that the resulting procedure has the required two-law recovery guarantee.

## Reproduction and provenance

- Command: `& 'C:\Users\nigel\AppData\Local\Programs\Julia-1.13.3\bin\julia.exe' --project=.aris/runs/hsvi-osposg-upstream scripts/risk_preserving_approx/test_hsvi_sequential_adversarial_gadget.jl`
- Upstream: `HSVIforOSPOSGs.jl` commit `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`
- SHA256 sequential test script: `C1B5737A981601A0DE7719EE53F07D7C41CCDD625205256CA092B8CF31014083`
- SHA256 fixture: `1F078F193F197A3AD6961470755D23626263BF7A28C9C16DC1C5C0661969527C`
- SHA256 shared gadget extractor: `C8CA987F4831CA44AC6CA54333BB032268609E805F3646846AC45CDE30B4F513`
- SHA256 JSON result: `32482012EDB43D1EDF3F67FB829A41071F45D4B3426820EC4E4C117AB8565566`
- Ignored run files: `.aris/runs/candidate_d_sequential_adversarial_toy/result.json` and `run.log`

The test does not cover nonmatching-pennies payoffs, ShiftLab's delayed-query
chronology, hard query-budget constraints, null-pending-label access,
first-promotion risk, post-promotion continuation, multiplier bracketing,
baseline runtime/memory, synthetic superiority, or real-data performance.
Candidate D therefore remains unqualified for a ShiftLab efficacy pilot; G1–G3
and the user's full research objective remain open.
