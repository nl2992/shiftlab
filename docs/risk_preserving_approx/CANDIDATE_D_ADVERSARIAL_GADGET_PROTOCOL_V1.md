# Candidate D adversarial gadget toy protocol

**Registered before the corrected execution, 2026-10-29.** This is adapter verification only,
not a ShiftLab efficacy test and not a method or novelty claim. The initial execution failed before
solver initialization because the fixture declared ten transitions but contained nine; preserve
that parser failure and do not count it as a solver result.

## Frozen toy

Use the two-state, one-step zero-sum matching-pennies game in
`scripts/risk_preserving_approx/fixtures/candidate_d_adversarial_toy.osposg`. The initial belief
is `(1/2,1/2)`. The learner chooses `row0` or `row1`; the opponent chooses `column0` or
`column1`; matching indices yield reward `+1`, mismatches `-1`. The transition immediately enters
an absorbing zero-reward state, independent of actions. The exact maximin security value is zero,
attained by the uniform root action distribution. No controller observations affect the policy.

## Pass criteria

Using the same pinned HSVI implementation and gadget extractor as the registered probe/guess toy,
solve with `epsilon=1e-4`, 30-second solve limit and neighborhood `1e-8`. Independently evaluate
the extracted root distribution against both pure opponent actions. Pass only if the reported HSVI
gap is at most `1e-4`, the extracted distribution sums to one within `1e-8`, its maximin value is
within `1e-3` of zero, and the maximum gadget residual is below `1e-7`. Record value bounds,
strategy, both pure-action payoffs, solve time, exploration count and hashes. Do not tune the game
or thresholds after execution. This probes opponent/action randomization only; it does not test
sequential adversarial strategy extraction, pending-label information, or the switching model.
