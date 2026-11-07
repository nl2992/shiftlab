# Phase 2 — economic headroom results and decision

**Branch:** `codex/scoped-method-research-results-2026-11-06`  
**Runs:** frozen economic matrix (`seed_base=2026110626`), fixed-alpha E-SR panel (`7110601401–1402`), supplemental cost-aware and reserve/rollback panels (`7110601403–1404`). All are synthetic development evidence, not confirmation.

## Verified target and controls

Primary target is `F3_reversal_1200`: the challenger has an event-level expected advantage of +0.08 for 1,200 events, then −0.08 for 800. The paired horizon, delay, pathwise label cap, label price and switch cost are identical within each panel. The unfavorable boundary is `F3_reversal_800`; `F0_null` and `F0_better` are controls. Oracle truth is evaluator-only.

The original matrix used alpha .05 and found nominal E-SR at cost 360.00 versus never-switch 378.83 (difference −18.83 [−30.96,−6.71]) on the target, but it promoted on all 30 null streams. This is not an acceptable operating point.

At the preselected E-SR setting alpha=.0005, the independent 1,000-stream null calibration passed the empirical gate (18/1000, one-sided Wilson 95% upper 2.63%). At that fixed setting, the fresh 30-stream panel had:

| Cell | E-SR net cost | Never-switch | Paired difference E-SR−never [95% CI] | E-SR promotions / rollbacks |
|---|---:|---:|---:|---:|
| `F3_reversal_1200` | 389.60 | 366.43 | +23.17 [+16.41,+29.93] | 29/30; 0.50 mean rollback |
| `F3_reversal_800` | 383.30 | 341.47 | +41.83 [+34.14,+49.53] | 27/30; 0.77 mean rollback |
| `F0_better` | 365.83 | 419.80 | −53.97 [−64.74,−43.20] | 30/30; 0 |
| `F0_null` | 373.70 | 363.97 | +9.73 [+9.19,+10.28] | 1/30; 0 |

On the target, E-SR spent 10.00 on labels and 7.33 on switches; predictive loss was 372.27. It did not reach an economic advantage over never-switch or E_swcert. The `F0_better` result is a favorable registered control cell, but it does not reverse the target-cell failure or establish a method contribution.

## Supplemental baseline completion

The repository's `R:economic_stop` was missing from the original matrix. A fresh exploratory panel at global alpha .0005 showed on `F3_reversal_1200`: cost 387.70 vs never 377.83, paired +9.87 [9.84,9.89]. It made no promotions and spent 197.3 labels (9.87 label cost). On `F3_reversal_800`, it likewise made no promotions, spent 196.4 labels, and cost +9.85 [9.83,9.87] over never. Its value threshold alone therefore did not conserve the pathwise label budget or close the gap.

The known `B5` reserve+rollback+deadline composition was also screened on fresh paired streams at the same alpha. On `F3_reversal_1200`, B5 cost 408.08 vs never 375.33, paired +32.74 [24.14,41.35]; it spent 185.6 labels and had 1.03 switches on average. On the unfavorable `F3_reversal_800`, B5 cost 373.86 vs never 346.83, paired +27.03 [16.99,37.07]. The simpler B2 rollback-only policy also did not close the gap. B5 is not a new method.

In the same supplemental target panel, E_swcert was +12.59 [8.69,16.49] vs never; E_rb was +28.73 [19.92,37.54]; RMM +33.70 [24.62,42.78]; PFA-SR +40.73 [30.58,50.89]; and E-SR +18.87 [9.16,28.58]. The uncertified `economic_replacement` was +0.82 [−5.78,7.43] vs never but promoted on 26/30 `F0_null` streams; it is not a safe feasible resolution. The original matrix's expected-oracle cost was 294.70 on average, about 84.13 below never-switch; this remains an evaluator-only upper bound.

## Headroom decision

The tested environment has material economic headroom in principle: the evaluator-only upper bound is substantially below never-switch. No evaluated feasible risk-qualified policy captures it while meeting the target, and the apparent low-cost alternatives either lose on fresh target streams or fail the registered null-risk conditions. The evidence does not support `NO_ECONOMIC_HEADROOM`; it supports a specific interaction failure across evidence speed, promotion timing, post-promotion rollback, label expenditure and switching cost.

One bounded risk-separated rollback hypothesis is justified for a falsification pilot: keep the promotion alpha fixed at the empirically qualified 0.0005, but give the post-promotion rollback test its separate cost-only threshold of 0.05, as used in existing rollback monitors. The candidate must be compared with the exact low-alpha E-SR ablation, B2/E_rb, never-switch, E_swcert and the simplest economic stop at identical acquisition, horizon, delay, budget and costs. This is a setting-level adaptation of established restart/rollback ingredients; it is **not presumed novel**. If E_rb or another conventional two-sided monitor explains the gain, record `EXISTING_METHOD_ALREADY_SOLVES_IT` and stop the novelty claim. If no material gain remains, stop the repair lane and report `BENCHMARK_ONLY`.

## Prior-art boundary

- Cost-aware deployment is an optimal stopping/switching problem with switching costs; the repository already has `R:economic_stop` and finite-horizon Bellman comparators. A threshold `c_s/(T-t)` alone is not a new method.
- Budget allocation under drift and delayed labels is established in online active learning, including PRopagate/drift-dependent allocation and DBAL's dynamic post-drift labeling budget.
- Active change-point detection and controlled sensing are established; sequential sensing policies have been studied jointly with detection delay and false-alarm constraints, including observation-switch costs.
- Two-sided SR/CUSUM and rollback state machines are established. The 2026 RAR preprint also studies explicit rollback actions and cost-triggered production responses. These references make a generic joint reserve/acquisition/rollback novelty claim unsupported.

Primary prior-art sources reviewed: [Castellani et al., stream-based active learning with verification latency](https://arxiv.org/abs/2204.06822); [Aguiar & Cano, dynamic budget allocation for sparsely labeled drifting streams](https://doi.org/10.1016/j.ins.2023.119821); [Hayashi et al., Active Change-Point Detection](https://proceedings.mlr.press/v101/hayashi19a.html); [Lau & Tay, quickest change detection with observation-switching cost](https://doi.org/10.1109/TSP.2021.3057258); [Veeravalli et al., Quickest Change Detection with Controlled Sensing](https://doi.org/10.1109/JSAIT.2024.3362324); [Sadeghian et al., Retrain, Alert, or Rollback? (2026 preprint)](https://arxiv.org/abs/2611.02251).

## Provenance

- Fixed-alpha E-SR protocol: `research/scoped_method/pilots/srr_reversal_20261106_protocol.md`.
- Fixed-alpha E-SR results: `research/scoped_method/pilots/srr_reversal_20261106/EVALUATION_RESULTS.md`.
- Cost-aware comparator raw rows SHA-256: `b9e83a0f297527341df4f59f06c68436fd805b2c57f8f494e35bc118ca17cc69`.
- Reserve/rollback panel raw rows SHA-256: `6d8d0ac6d435dbac9b6d54dcbbb85c7da40cecca2e8ec8f0383bd172dbc8e1b1`.
- Source manifests are adjacent to each `records.jsonl`; the full paired records and cost components are preserved.
