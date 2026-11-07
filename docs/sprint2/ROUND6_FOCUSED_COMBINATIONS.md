# Round 6 focused-combination audit

## Existing combinations and evidence

The focused combinations in the current worktree were screened during development; they precede the
separate Round-5 evaluation and are not represented as fresh post-Round-5 runs.

- **T6 evidence × acquisition 2×2:** A5b × C2 interaction estimate +0.8 net cost
  (95% interval [-1.5,+3.0]); acquisition effect at best evidence -0.6 ([-1.9,+0.7]). The
  combination had 0/20 promotions on the four development null screens, mean alternative J 391.1,
  and a selected R20 point with risk .087 [.043,.170] and cost 374.2 [368.7,379.8]. The interaction
  is small/uncertain and does not support an added mechanism. See `family_t/results.md` and
  `outputs/sprint2/T/contrasts.json`.
- **P6_RRD reserve + restart detector:** reserve ablation did not produce a useful late gain;
  P6_RRD is near A5b economically and does not recover P6_LRMD_U's synthetic late effect. Its Track-R
  point is on the empirical frontier but ties A5b, without a demonstrated joint improvement. See
  `family_p/P6_late_reversal.md` and `family_p/trackR.md`.
- **D2 + A5b (D5/H2 line):** completed in the committed-code screen and H family work. Dependence
  control is an explicit design trade-off; the tested variants do not preserve D2's fresh-real cost
  advantage while establishing broader class reliability. See `family_h/` and the gate log.
- **RMM + SUI (prior Amendment 6):** documented negative interaction: it recovered only 13–22% of
  RMM's late gain and failed twin-null reliability. No repeat was run.

## Decision

No existing combination demonstrates a transferable cost-risk improvement. E_rb's fresh-seed
reversal result is a scoped single-mechanism extension and does not justify stacking another
mechanism. Do not advance a complex hybrid from these results. Round 6 is therefore complete as a
focused-combination decision using existing runs, but there is no new post-Round-5 combination
experiment. If a paper claim depends on new hybrid evidence, that remains outstanding rather than
being inferred from these earlier development runs.
