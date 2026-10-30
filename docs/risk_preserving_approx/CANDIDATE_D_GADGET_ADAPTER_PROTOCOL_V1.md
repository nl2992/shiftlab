# Candidate D gadget-adapter toy verification protocol

**Registration date:** 2026-10-29. **Purpose:** test the published learner
strategy-extraction gadget implementation only. This is not a ShiftLab efficacy
experiment, does not allocate seeds, and cannot pass G1–G3.

## Frozen toy game

Use a two-hidden-state, two-decision OS-POSG with initial belief `(1/2,1/2)`,
discount `gamma=0.9`, no opponent choice (one dummy action), and four reachable
hidden states plus one absorbing terminal state. At stage 1, Player 1 chooses
`probe` or `skip`. `probe` gives reward `-1/10` and reveals a binary signal with
accuracy `4/5`; `skip` gives reward zero and observation `none`. At stage 2,
Player 1 chooses a state guess; a correct guess earns `+1`, an incorrect guess
`-1`. The hidden state is unchanged and the game then absorbs with zero reward.
The exact optimal value is `-1/10 + (9/10)(3/5) = 11/25 = 0.44`, attained by
probing and guessing the more likely state after the signal.

## Method and limits

Use the pinned `HSVIforOSPOSGs.jl` source commit
`05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`. Run its value-bound solver with
target gap `1e-4`, per-run limit 30 seconds, and the smallest neighborhood
parameter satisfying the source's `check_neighborhood` condition. Then implement
the paper's Algorithm 5 gadget step as a JuMP LP over the existing lower-bound
alpha vectors. Starting from the maximizing initial alpha vector, recursively
extract the learner's action distributions and child gadgets for all reachable
action-observation pairs. Keep the opponent's single dummy action fixed.

Independently enumerate the extracted controller on the toy transition model.
Record initial HSVI lower and upper bounds, achieved value, controller node
count, extraction wall time, maximum gadget-constraint residual, and exact
benchmark value. Pass only if the controller payoff is at least `0.44 -
2e-3`, the HSVI reported lower/upper gap is at most `1e-4`, the maximum gadget
constraint residual is below `1e-7`, and the controller contains the
probe-then-signal-conditioned-guess behavior. A timeout, numerical failure,
incorrect history update, or failed threshold is a recorded no-go; do not tune
the game or thresholds after seeing output. No real-data, holdout, or broader
synthetic comparison is included.

## Artifacts

Use a new script under `scripts/risk_preserving_approx/` and write the toy model,
raw log, and JSON result under ignored `.aris/runs/candidate_d_gadget_toy/`.
Record source, protocol, and output hashes in a follow-up result note before any
ShiftLab pilot is registered.
