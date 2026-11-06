# Heavy-tail PFA-SR late-label screen

**Status:** frozen development pilot. This is a bounded test of a conventional start-prior adjustment; it is not a novelty claim or confirmation run.

## Hypothesis

The canonical PFA-SR start weights `0.5/[s log(e s)^2]` allocate relatively little wealth to late label-clock starts. A finite-budget prior proportional to `1/[s log(e s)^1.2]`, normalized to the same total mass as canonical PFA-SR at that budget, may reduce detection delay when an improvement begins late and feedback is delayed. The conditional-null e-process argument remains valid because the nonnegative mixture weights sum to the canonical total (at most one). This does not imply validity under arbitrary dependence.

The exponent 1.2 is fixed before this run; it will not be tuned on these outcomes. The candidate is `PFA-SR:q1.2:gated_adaptive_range`. The canonical comparator is `PFA-SR:gated_adaptive_range`; same-host RMM is `rmm:gated_adaptive_range+RMM`.

## Development cells and decision rule

Run 30 paired seeds, seed base `2026110631`, horizon 2,000, switch cost 5, query cost 0.05, alpha 0.05. The late/scarce primary cell uses budget 100 and fixed 400-step label delay. Its model advantage is zero until event 600, then 0.0748 per event in expectation (`0.22 × (2×0.67−1)`). Additional cells are a strong persistent alternative, a correctly specified iid null, and the pre-existing adverse `F3_reversal_800` diagnostic. All outcomes are reported.

Policy panel: candidate; canonical PFA-SR on the same host; same-host RMM; `xu_acquisition_only`; `E_rb:gated_adaptive_range`; `E_swcert`; `CONTROL_never_switch`. The ARL-only E-SR is excluded from safety-qualified ranking; it may be reported only as a diagnostic in any later confirmation.

Development signal requires in the late/scarce cell: (a) ≥5 net-cost savings with paired 95% t interval below zero against canonical PFA-SR, same-host RMM and Xu adapter; (b) no more than 5 units mean extra net cost versus never-switch in the null and reversal cells; and (c) no null promotions in 30 streams (screen only, not alpha validation). Failure of any condition ends this candidate. Passing permits one independently seeded confirmatory synthetic screen; it does not establish novelty or real-world transfer.

## Cost and information contract

Net cost = predictive loss + 0.05 × requested labels + 5 × deployment switches. All policies receive the same stream, horizon, pathwise hard label budget, delay and predictable query/disagreement information. Synthetic oracle truth remains evaluator-side. Paired 95% t intervals are over shared seeds. No multiplicity adjustment is used; this is a screening experiment.

## Reproduction

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes PFA_tail_late_scarce@B100,PFA_confirm_persistent,PFA_confirm_null,F3_reversal_800 \
  --policies 'CONTROL_never_switch,xu_acquisition_only,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,E_swcert,PFA-SR:gated_adaptive_range,PFA-SR:q1.2:gated_adaptive_range' \
  --seeds 30 --seed-base 2026110631 --workers 4 \
  --out research/scoped_method/pilots/heavy_tail_pfa_screen_20261106/run
```

## Prior-art boundary

Changing a summable change-point prior is a standard e-detector design choice. The candidate is being tested as a targeted parameterization/application, not presumed original. See Shin, Ramdas & Rinaldo, [*E-detectors*](https://nejsds.nestat.org/journal/NEJSDS/article/59/text), and Shin et al., [*Non-partitioned e-detectors*](https://arxiv.org/abs/2607.28322). Any positive development finding must be audited against mixture/weighted e-SR priors before a paper claim or real-data confirmation.
