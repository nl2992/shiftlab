# Errata (Stage 0, T0.4)

**Recorded 2026-10-28.** Historical documents are not edited. Each entry gives the location, the
wrong text, the correction and how it was checked. Any manuscript or later document must use the
corrected value.

| ID | Location | Says | Correct | Evidence |
|---|---|---|---|---|
| E-1 | `docs/gated_monitor_null_calibration_results.md:8` (S2 null calibration) | "seeds 58300000–58301999" | **Seeds 58500000–58501999.** The 2,000-stream-per-cell count and all results are unchanged. | Seed column in the S2 output parquet (`outputs/gated_monitor_null/`), lead-verified during the evidence inventory; registered by T0.1 in the seed registry |
| E-2 | `docs/methods_and_assumptions.md:126` | "Model-version persistence and operational rollback are not implemented." | **Stale.** Simulated rollback is implemented in `controller.py::CertifiedPromotionRollback`, `closed_loop_intervention.py` and `integrated_pipeline.py` (`rollback_log_e_value`, `rollback_triggered_here`). No *operational* (deployed-system) rollback exists. | `RESEARCH_EVIDENCE_INVENTORY.md:387`; `src/shiftlab/dive/integrated_pipeline.py:87–90, 159–165` |
| E-3 | `docs/closest_prior_work.md` | Jang et al. (ICML 2022) titled "Sequential Predictive Two-Sample and Independence Testing" | *Sequential Covariate Shift Detection Using Classifier Two-Sample Tests* (Jang, Park, Lee, Bastani; PMLR 162, pp. 9845–9880) | PMLR record; `PRIOR_ART_AND_NOVELTY_MATRIX.md` §2 |
| E-4 | `docs/closest_prior_work.md` | Amoukou et al. "2024 preprint" | Accepted at NeurIPS 2024 (arXiv 2412.12910) | arXiv record; matrix §2 |
| E-5 | Intervention and monitoring audits (G0 list) | DE-CuSum is arXiv 1105.1361 | DE-CuSum is **arXiv 1211.3729**. 1105.1361 is the Shiryaev-based on-off observation-control paper. | arXiv records; matrix B1 §1 item 3 |
| E-6 | `docs/closest_prior_work.md` (RCCDA row) | RCCDA has update-frequency and cost guarantees | The guarantee (Theorem 5.3) **requires a zero-error gain estimator** | Primary source; matrix §2 |
| E-7 | `docs/algorithm_search_exit_ledger.md` §1 (M8) | DE-CuSum "already address[es]" burst allocation | **Too strong.** DE-CuSum assumes known likelihoods and a rate constraint, not a hard finite budget with unknown bursts. M8's exclusion rests on Paper 3 scope, not on prior coverage. | Matrix §2 |
| E-8 | `docs/research_refinement_v1/BRIEF.md:75` | "RADAR", with no reference | Zheng, Wiberg and Zhu, "Deciding When to Decide: Testing Operational Suboptimality Under Distributional Shift", arXiv 2608.29465 v1. Its guarantees are asymptotic, not anytime-valid. | Confirmed by the user 2026-10-28; matrix §2 |
| E-9 | `docs/research_refinement_v1/REFINEMENT_ROUND_2.md:46` (Claim B) | "A naive monitor-then-revert rule beats a certification pipeline by 4–6× on three profiles" | **5.63× (boundary harm) and 4.26× (monitor-aligned adaptation), on two profiles.** On recurring regimes it is +447.96 against 0, so no ratio exists. After a reversal, revert is 8.0× worse (−1,148.46 against −143.76). The arms also differ in response latency, coverage and rollback, so the comparison is descriptive. | `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv`; Codex round 2; independently recomputed by T0.2 |
| E-10 | `docs/research_refinement_v1/COMPETING_RESEARCH_DIRECTIONS.md` (tick-5 derivation) | A strong signal makes a low `q` costly | **Wrong.** Per-label growth does not depend on `q` in either regime (Lemma L at ε = 0; bounded remainder for ε > 0). Already annotated in that file at §0; listed here for completeness. | Tick-6 numerical check; `tests/test_lemma_l_propensity_invariance.py` |

## Not errata, but disclosure items found by Stage 0

The seed overlaps disclosed by T0.1 and the Target-Scout hash drift verdict (T0.5) are recorded in
their own Stage 0 files. They are listed in `STAGE0_SUMMARY.md` once all tasks finish.
