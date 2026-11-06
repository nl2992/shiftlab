# PFA-SR published-baseline screen

**Status:** prospective development screen of an existing published detector; not a novel method
and not confirmatory evaluation. This protocol is frozen before the screen.

## Research question

Does the canonical summable-start-prior e-Shiryaev–Roberts detector retain the fast economic
benefit of the ARL-only e-SR port in the Failure Atlas favorable-reversal regime while controlling
the probability of any false promotion? This is a baseline-fidelity and headroom screen. The method
is taken from Shin, Ramdas, and Rinaldo's e-detector framework and the PFA-weighted extension in
*Non-partitioned e-detectors for nonparametric sequential change detection* (2026 preprint).

The detector uses signed queried disagreement outcomes `X_n` and a grid of bets
`lambda ∈ {0.15, 0.3, 0.5}`. For candidate start `s`, its start-specific e-process is
`E_{s,n} = product_{j=s}^n (1 + lambda X_j)`. The mixture is
`M_n = mean_lambda sum_{s≤n} pi_s E_{s,n}`, with
`pi_s = 1 / (2 s log(e s)^2)`. The decreasing-series integral bound gives
`sum_s pi_s ≤ 1`. Under the iid conditional null `E[X_n | F_{n-1}] ≤ 0`, the active wealth plus
unopened prior mass is a nonnegative supermartingale; threshold `1/alpha` therefore controls
`P(any alarm)` by `alpha` per detector run. The existing wrapper splits first-promotion alpha
between the host certificate and detector, spends promotion alpha geometrically on re-promotion,
and resets the detector after each switch. This guarantee does not cover serial dependence or a
false rollback cost. All labels, delays, costs, and switch rules come from the shared simulator.

## Cells, run, and comparators

Run 30 fresh paired streams per cell with seed base `2026110627`, horizon 2,000, delay 100, budget
200, label price 0.05, switch cost 5, alpha 0.05. Cells are `F3_reversal_1200` (economically
worthwhile temporary gain), `F3_reversal_800` (unfavorable reversal), `F0_null` (promotion error
diagnostic), and `F0_better` (persistent control). Compare `PFA-SR:gated_deployment` with
`E_srrSR:gated_deployment` (ARL-only diagnostic), `rmm:gated_adaptive_range+RMM`,
`E_rb:gated_adaptive_range`, `E_swcert`, `xu_acquisition_only`, and never-switch.

Primary contrast is net cost versus never-switch on the worthwhile reversal. A potentially useful
PFA-SR signal requires ≥5 units savings with the paired 95% interval below zero, promotion in no
more than the Atlas screening tolerance of 9.36% on the independent null cell (30 seeds are still
too few to validate alpha 0.05), and no more than 5 units mean harm in the unfavorable reversal.
Report all cells and metrics, whether or not the signal passes. No real data will be opened in this
screen. If this established method closes the gap, the next step is a prior-art transfer benchmark,
not a novelty claim.

## Reproduction

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes F3_reversal_1200,F3_reversal_800,F0_null,F0_better \
  --policies 'CONTROL_never_switch,xu_acquisition_only,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,E_swcert,E_srrSR:gated_deployment,PFA-SR:gated_deployment' \
  --seeds 30 --seed-base 2026110627 --workers 4 \
  --out research/scoped_method/pilots/pfa_srr_reversal_20261106/run
```

Primary reference: [Shin, Ramdas & Rinaldo, *E-detectors: A Nonparametric Framework for Sequential
Change Detection*](https://nejsds.nestat.org/journal/NEJSDS/article/59/text); and [Shin et al.,
*Non-partitioned e-detectors for nonparametric sequential change detection*](https://arxiv.org/abs/2607.28322),
Section 2.2, Theorem 2.3. The second paper is a preprint; use it as prior art and do not claim the
weighted prior construction as original.
