# 06 H2c and HG Reproduction Status (2026-10-30)

Status vocabulary: VERIFIED (re-derived from raw artifact this session), DOC-ONLY, MISMATCH, NOT FOUND.

## 1. Classification

| Item | Analysis level (stored artifact to statistic) | Simulation level (generator to artifact) | Overall |
|---|---|---|---|
| H2c G5 confirmation | VERIFIED: rerun of `scripts/sota_search/g5_confirmation_analysis.py` on the stored per-seed parquet reproduces the reported numbers | PARTIAL: full simulation not re-run; one cell (subgroup_failure/concept2, N=600, different seeds) re-run and MC-consistent | Analysis VERIFIED; simulation partial |
| HG e15 confirmation | VERIFIED: recomputed estimates and Holm p-values from `perseed.parquet` match | Not re-run in this audit | Analysis VERIFIED; simulation DOC-ONLY |
| HG "~21/24 harm reduction" | MISMATCH (section 3) | n/a | Restate as relative harm-world figures |
| H2c cost-null validity | n/a | n/a | DOC-ONLY (`docs/h2c_next/COST_NULL_VALIDITY.md`; no unit test) |
| HG cap repair | VERIFIED by `tests/gap/test_engine.py::test_exact_finite_support_cap` (18 tests pass) | n/a | VERIFIED |

## 2. H2c

Source: branch `research/h2c-strong-baselines-and-generalization-2026-10-30`, HEAD `60930a4`; results commit `44119c6`; preregistration `e164d63`.

Inputs (sha256):
- `outputs/h2c_next/g5_confirmation_per_seed.parquet`: `ed5923e9486c6bc9c8a0d1497f68c74563a4221f5644721f508dfd7fbbf66ba7`
- `outputs/h2c_next/g5_confirmation_cells.csv`: `81c8e39d6afc29ce88a62a28d42395d11cc3661af2ff538e0978c0e04c1877b6`
- No manifest exists in the repository (NOT FOUND).

Reproduction command (analysis level):

```
cd <h2c worktree>   # C:/Users/nigel/OneDrive/桌面/ICML/branch-research-h2c-strong-baselines-and-generalization-2026-10-30
PYTHONPATH=src python scripts/sota_search/g5_confirmation_analysis.py
```

Re-derived values (VERIFIED):

| Quantity | Value |
|---|---|
| Cells | 14 harm, 10 benign, 8 null; 600 seeds |
| Advantage vs better comparator @10% | +0.086 [0.059, 0.113] |
| Advantage vs better comparator @20% | +0.094 [0.063, 0.125] |
| Power (H2c) | 0.382 / 0.640 |
| Benign FAR @20% | 0.067 |
| Null FAR max | <= 0.027 |
| Harm cells won | 13/14 and 14/14 |

CI method: cluster bootstrap, 4000 resamples over cells then seeds; the better comparator in each cell is chosen from realised means.

Simulation-level partial check: single cell subgroup_failure/concept2, N=600, different seeds: H2c 0.330 / 0.617 vs frozen 0.342 / 0.627, consistent within Monte Carlo error; runtime 3.1 s. Generator script: `scripts/sota_search/g5_confirmation.py`. Full re-run not performed.

Statistic: `src/shiftlab/sota_search/detectors.py`, `pp_cost_guided(mode="guided_disc", gamma=0.995)`, lines ~570-610; threshold ln(1/alpha). Comparators: C1 fix_cost (discounted Kelly), C2 cost_ons, C7a sr_cost_tight (empirically calibrated; more powerful by 0.19 / 0.13; no guarantee).

Limits bounding the reading: G5 nominal cost effectively known; fixed delay 5; static proxy defects; one generator family; no comparator is a verified published reproduction; outcome-dependent delay not covered; dependence not re-run for cost-null; under AR rho=.98 Brier-null e-processes exceed alpha (up to .36). Companion evidence: restart branch `d4673d9` (valid restart mixtures +.003/.009/.023, noise; unknown nominal gives power ~ 0 for n_cal <= 1000; EB n_cal = 50,000 gives .535/.850 vs .603/.902 known); sweet-lovelace `d1b173b` X1 (H2c reduces exactly to discounted Kelly with a substituted moment ratio, max abs dlogW 8.9e-16; guidance helps +.03 to +.14 only when Brier co-shifts, loses up to .59 when flat/opposed) and D2 Gas (H2c 242-824 events later than cost-only Kelly/ONS; 2-4x excess cost before alarm). All DOC-ONLY.

## 3. HG

Source: branch `research/shiftlab-mandate-gap-closure-2026-10-30`, HEAD `8552911`; data `outputs/gap_closure/e15_confirm/perseed.parquet` (21 worlds; 400 seeds harm, 1000 null); script `scripts/gap/e15_confirm.py`. A hash of the parquet was not recorded in this audit.

| Quantity | Reported | Recomputed (VERIFIED) |
|---|---|---|
| Effect 1 | +0.029 [0.012, 0.046] | 0.0288; Holm p 0.004; raw p 0.0005 |
| Effect 2 | +0.052 [0.020, 0.090] | 0.0518; Holm p 0.003 |
| Holm family size | 10 | 10 |

MISMATCH: "harm reduction ~21/24" are raw cumulative-harm units (-20.6 / -24.2) averaged over all 21 worlds, including null worlds. In harm worlds only they are -28.9 / -33.9, about 15% / 25% relative. Use the relative harm-world figures.

Other HG facts: predictable uniform cap repair VERIFIED by `tests/gap/test_engine.py::test_exact_finite_support_cap` (18 tests pass). HG vs Page-Hinkley/CUSUM power -0.066 / -0.110, not significant, so not a win (DOC-ONLY). HG is invalid under dependent outcomes (FAR up to .23; DOC-ONLY). hg-validation G3 (`1299c1c`, `docs/hg_validation/05_G3_RESULTS.md`): beat the parent by +.050 / +.131 but not ONS or plain discounting (DOC-ONLY).

The HG simulation was not re-run in this audit; do not describe it as reproduced beyond the analysis-level recomputation above.

## 4. Assessment

No new confirmatory evidence was produced. The verified analysis supports only the descriptive statements above. All data are synthetic or exposed holdouts, so no confirmatory real-data claim is supported.
