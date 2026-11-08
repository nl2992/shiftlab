# PAVE-EF comparator panel (registered before the C3 result is inspected)

Registered 2026-11-08. This panel is **separate** from the frozen C3 protocol (`70_PAVE_C3_PROTOCOL.md`),
which stays unchanged. It answers two questions:
1. Does PAVE-EF beat every available state-of-the-art and in-repo comparator in this harness, not
   only `episode_front`?
2. Does the combination beat each of its original parts?

## Arms (all in the same harness, contract and cells)

| group | arms |
|---|---|
| candidate | `pave_ef` (frozen, as in C3) |
| original parts | `pave` (original PAVE on the DSS shell), `episode_front` (original engine, uniform calendar) |
| safety-gated e-process comparators | `episode_geo`, `episode_equal`, `allonset_edetector` (all-onset e-detector), `c2_rho0.75`, `c1_hmm_cs` (HMM confidence sequence), `markov_lr_gate`, `thinned_hedged_gate`, `dss` |
| ungated comparators (no false-promotion control; reported, not used in the claim) | `periodic_mean`, `dal_restart`, `pacing_bernoulli`, `uniform` |
| floor | `no_switch` |

Every arm is built exactly as the harness builds it (`fa.make_method(..., bernoulli_grid_spec())`,
cycle-7 variants and dependence gates, `GaverMethod("dss","pave")`).

## Cells and seeds

- **Cells:** the same 54 long-delay cells as C3 (9 specifications × d ∈ {50, 75, 100, 150, 200, 300}).
- **Seeds:** fresh block `pave_panel_eval`, 102500000–102599999, 30 seeds per cell
  (102500000 + 1000·i + k).

## Analysis

Pooled equal-weight cell-mean J/T. Each contrast `pave_ef − X` is a relative % of X, with a paired
bootstrap over seeds within cells (10,000 resamples) and Holm adjustment across the 10
claim-bearing comparators (original parts + safety-gated).

- **SOTA claim:** PAVE-EF *beats the panel* if every claim-bearing contrast is negative with
  Holm p < .05.
- **PARTIAL:** list which comparators it beats, ties and loses to.
- **Contraption claim:** "beats its original parts" requires `pave_ef − pave` < 0 and
  `pave_ef − episode_front` < 0, both Holm p < .05.

Ungated comparators are reported with an explicit "no false-promotion control" label.

## Not allowed

No change to `pave_ef`. No arm added or dropped after results.
