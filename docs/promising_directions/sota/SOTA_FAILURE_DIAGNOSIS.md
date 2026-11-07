# Failure diagnosis

## What was claimed

That stopping acquisition when the *economic* deployment decision can no longer change beats
stopping when a *statistical certificate* fires, under a hard budget, delayed release and a
switching cost.

## What happened

It lost on both powered datasets, with the paired interval entirely above zero, and it was better
in 0 of 16 rialto episodes and 6 of 32 ldpa episodes.

## The mechanism, stated as an asymmetry

The two triggers differ by a threshold: `0` versus `c_s/(T-t)`.

- **What the economic trigger buys**: avoiding switches that do not repay `c_s`. The saving is
  **bounded by `c_s` per avoided switch**, and at most one switch per episode here.
- **What it pays**: every event spent waiting for the lower bound to clear a higher bar is an
  event deployed on the worse model. That cost is **per-event and unbounded by `c_s`**.

A bounded saving against an unbounded cost loses whenever the advantage is large enough that the
wait is long. Here `c_s = 5` buys at most 5 of saving; on `openml_ldpa` the wait cost 9.73.

This is not a tuning failure. It is the wrong trade for this regime, and no threshold calibration
fixes it, because the two quantities scale differently.

## Why our earlier result did not predict this

Against **P3b**, settled-decision acquisition won by saving labels with *identical deployment
behaviour* — deployment loss was bitwise identical, and the gain was purely `c_q N_q`. That is
why its scaling law held so exactly.

Against **gated deployment**, the comparison is completely different: a confidence sequence that
stops as soon as the sign is determined is already label-efficient, so there is little label waste
left to recover. Gated used 30.8 labels on rialto where P3b used 159. The waste our method was
built to remove had already been removed by a better stopping rule, and all our threshold did was
add delay.

**The lesson is about the baseline, not the method.** We measured against P3b for the whole
programme and a 67% label saving looked substantial. Against the right baseline the same mechanism
has almost nothing to recover, and its side effect dominates.

## Honest statement of what remains true

- Settled-decision acquisition does beat P3b, reproducibly, on five datasets.
- P3b is not the strongest available method for this task. Gated deployment is cheaper on both
  powered datasets by a wide margin (94.7 vs 103.7 on rialto under our accounting).
- Therefore the B3+ result, while correct, is a comparison against a weak baseline, and should
  not be published as though P3b were the state of the art.

That last sentence is the most important thing this programme produced.

## CORRECTION 2026-11-03

This diagnosis analyses `EconomicStop`, not `P7s`. The claim that "the B3+ result is a win over a
weak baseline" rests on gated deployment beating **P3b**, which the decisive run does show
(94.695 vs 103.728 on rialto). It does **not** rest on any measured comparison between gated
deployment and **P7s**, because none exists. P7s versus the published suite is untested, and the
conclusions above must not be extended to it.

## CORRECTION 2026-11-06: P7s comparator screen

The previous paragraph records the historical state and is superseded on the narrow point that
P7s had never been compared. The exposed loss-replay screen now compares P7s directly with Gated,
DISCERN-style, SMCS, Model Picker, Model Selector, Online LLM Picker, and Xu acquisition-only on
Rialto and OpenML-LDPA. P7s loses to Gated on Rialto; on LDPA it beats Gated but loses to Model
Picker and Model Selector with paired intervals entirely above zero. The exact values, label
encoding invariance, and input limitations are documented in
`research/scoped_method/pilots/p7s_vs_sota_loss_replay_20261106/RESULTS.md`.

This closes only the *loss-replay screen*, not the authentic real-prediction comparison or the
five-case completion gate. It supports a narrow positive versus Gated on LDPA, but not an SOTA
advantage: stronger applicable selectors are cheaper. No fresh confirmation source is justified
for unchanged P7s.
