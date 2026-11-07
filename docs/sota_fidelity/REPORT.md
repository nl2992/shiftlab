# SOTA fidelity pass — status report (2026-11-06)

Scope: the comparators named in the methods-paper strategy brief (tracks A/B priority) that were
missing, partial or unaudited in ShiftLab. Workflow in [README.md](README.md); every decision with
its evidence is in [LEDGER.md](LEDGER.md). Specs are retrieval-agent reads of the primary source
and official code; checks are independent re-reads that confirm or correct every claim.

This is a fidelity and implementation pass. **No comparative results are claimed.** All smoke runs
are 5-seed descriptive checks.

## Status by method

| Method | Source read | Official code | Check verdict | Honest tier now | Decision |
|---|---|---|---|---|---|
| Shekhar & Ramdas, ICML 2024 | PMLR + arXiv, full | `sshekhar17/SCDtoCS@c3a7ece` (deviates from paper) | accept w/ corrections | **new**: T2 core, T3 adapter | Implemented: `shekhar_ramdas_rcs_t3` (paper rule), `_anyexcl` (composite-null-safe) |
| Han, Huang & Wang, ICML 2024 (ARW) | PMLR + arXiv, full | `eliselyhan/ARW@c48f830` (no licence) | accept w/ corrections | **new**: T2 core, T3 adapter | Implemented: `han_arw_label_clock` |
| Regol et al., ICML 2025 (When to Retrain) | PMLR + arXiv, full | none found | accept w/ corrections | T2 native (existing); **new** T3 | Implemented: `upf_style_switch_timing_T3` (not UPF) |
| Shin, Ramdas & Rinaldo, NEJSDS 2024 | NEJSDS + arXiv v4 | 3 repos pinned | accept w/ corrections | **new**: T2 core (NBA e-SR alarm reproduced), T3 adapter | Implemented: `two_sided_esr_label_clock` (matched competitor for RMM/E_rb) |
| Page–Hinkley (river) | river / skmultiflow code | river 0.26.1 | accept w/ corrections | existing = CUSUM with slack; **new** river detector T1, wrapper T3 | Relabelled; implemented `river_page_hinkley_t3` |
| Saha & Ramdas, 2026 preprint | arXiv v1 | pinned | accept w/ corrections | numerical pilot only | Novelty constraint only |
| WATCH, ICML 2025 | PMLR + arXiv v4 | pinned + paper-era commit | accept w/ corrections | existing = inspired-by | Next: unweighted CTM sentinel (no covariates in sprint streams) |
| Timans et al., UAI 2025 | PMLR + arXiv | pinned (post-paper) | accept w/ corrections | T1 claim unsupported (vacuous replay) | Downgraded to T1-pending; needs non-vacuous replay test |
| IUPM, AISTATS 2025 | PMLR = arXiv | MIT, pinned | accept w/ corrections | none | Excluded: needs covariates, not a decision rule |
| Model Selector, AISTATS 2025 | PMLR + arXiv | pinned | accept w/ corrections | native T1-pending-parity; causal adapter T3 | Kept; record-gate rounding bug fixed |
| Tenzer et al., ICML 2026 | PMLR = arXiv | pinned | accept w/ corrections | existing `tenzer_*` = inspired-by | Relabelled; T1 port deferred to track C |
| CAMS / CAMS-MAX, NeurIPS 2024 | (existing audit) | pinned = HEAD | accept w/ corrections | native T1-pending-parity; adapters T3 | Kept; argmax follows paper; eta/u_t gaps noted |

## Findings that change how earlier work should be read

1. **RMM/E_rb vs e-detectors (track A).** RMM's statistic is Shin et al.'s e-SR (Def 2.6 with
   Remark 2.7 weights) on the label clock; E_rb's additions are system-level. The matched simple
   competitor (two-sided e-SR, start at every label, restart at switch) had never been run. It is
   now implemented (`two_sided_esr_label_clock`) and must be beaten on development seeds before any
   track-A novelty claim. A 5-seed smoke shows no resolvable difference yet.
2. **Composite nulls break the paper's RCS stopping rule.** Shekhar–Ramdas's joint-emptiness rule
   false-alarmed in 100% of constructed drifting-within-null streams; the `any_excludes` variant
   (instantaneous CS disjoint from Theta0) gave 0%. Relevant to any CS-intersection rule in
   ShiftLab.
3. **Regol et al. Proposition 3.1 is misprinted** (Eq. 40 reverses an implication). Corrected bound
   r* <= max(0, floor(T - sqrt(alpha/L)) + 1); exhaustive check over 29,099 instances: printed
   form fails 5,225 times, corrected form 0. Two wrong statements about Regol in
   `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` were corrected.
4. **Author-parity tests are silently skipped.** `vendor_sota/` is empty in both checkouts, so the
   T1 claims for CAMS, Model Selector, Model Picker, SMCS and variance-min are not currently
   re-verified. Restoring the pinned clones needs your go-ahead (it downloads and runs third-party
   research code).
5. **The sprint comparator streams carry no covariates.** WATCH's weights and IUPM cannot run there;
   claims involving covariate-shift methods need a real stream with features.
6. **Behaviour of the new uncertified adapters at B=200** (descriptive): label-clock ARW flips on
   noise (no margin in the paper); the Regol-style T3 switches on 8/20 null seeds. Neither can serve
   as a safety comparator; both can enter cost comparisons with parameters locked on development
   seeds.

## Registration

New comparators are opt-in through `scripts/failure_atlas_v2_flq/fidelity_extras.py` (`EXTRA`,
`FIDELITY_INFO`) and listed in `bench.FIDELITY_ADAPTERS_20261106`. They are not in
`bench.ALL_COMPARATORS` or any registered pool, so historical protocols and outputs are unchanged.

## Reproduce

```bash
uv run pytest tests/sota_fidelity tests/promising_directions/test_sota_model_selector.py tests/sota_sprint -q
```

## Still open

- ~~Development-seed comparison of E_rb/RMM against `two_sided_esr_label_clock`~~ **done 2026-11-07**:
  E_rb − e-SR on reversal +1.90 [−1.01, +4.80], not favourable to E_rb; all valid methods lose to
  never-switch on reversal. See [esr_vs_erb_dev_results.md](esr_vs_erb_dev_results.md).
- **Track B diagnosis done 2026-11-07** ([late_change_diagnosis_results.md](late_change_diagnosis_results.md)):
  stale evidence and budget exhaustion drive late-change failure; post-verdict stopping does not.
- **Track B prior-art check done 2026-11-07** ([prior_art/README.md](prior_art/README.md)): levers (a) pacing, (b) delay and (c) alpha allocation are each closed as contributions; track B stops as a method contribution.
- **Track A economic gating done 2026-11-07** ([econ_gate_bound_results.md](econ_gate_bound_results.md)): even the hindsight-optimal veto gate over a valid detector does not beat never-switch on the reversal regimes (headroom about −10, the label spend); stopped.
- **Paper 3 pacing minimax screen done 2026-11-07** ([pacing_minimax_results.md](pacing_minimax_results.md)): no pacer beats uniform's worst case by >6%; stopped as a method (independent check pending).
- WATCH unweighted CTM sentinel; non-vacuous Timans replay test.
- Restore `vendor_sota/` and re-run author-parity tests (needs approval).
- Not yet audited in this pass: e-SR/e-CUSUM is done, but the DISCERN-style, SMCS and gated
  certificate ports were covered by the 2026-11-04 audit, not re-checked here.
