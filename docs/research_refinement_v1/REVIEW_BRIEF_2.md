# Adversarial review brief, round 2 (for the independent cross-model reviewer)

You are an independent reviewer, from a different model family than the author. **Do not modify
any file.** Review `docs/research_refinement_v1/REFINEMENT_ROUND_2.md` (including its two addenda), which responds to your own round-1 review in `docs/research_refinement_v1/ADVERSARIAL_REVIEW_1.md` in this repository. You may
read anything in the repository to check claims, in particular:
- `docs/gated_monitor_comparison_results.md`
- `docs/eia_real_data_validity_results.md`
- `outputs/gated_monitor_compare/analysis/`
- `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/`
- `papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md`
- `papers/shiftguard_unified/claim_evidence_map_v1.md`
- `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` and `COMPETING_RESEARCH_DIRECTIONS.md`
- `src/shiftlab/dive/gated_monitor_comparison.py`
- `src/shiftlab/dive/integrated_pipeline.py`

Write as four separate reviewers. Each must be adversarial, specific and evidence-seeking:

1. **Statistical theorist.** Hunt for invalid assumptions, hidden optional-stopping or
   composition errors, misuse of conditional versus marginal nulls, and predictability failures.
   Check whether Proposition S (label invariance) is correct as stated: try to break it for the
   PPI anchor, the mixture over stakes, the hard reserve stop and the `ε` term. Say whether "fixed
   fraction of the cap" matches what the engines actually do in code.
2. **Prior-literature specialist.** Does Claim A or Proposition S already exist? Consider DISCERN
   Thm 9 (Θ(1/ρ)), Ahmed et al. 2026, Timans et al. UAI 2025, Waudby-Smith et al. and any
   benchmark of sequential risk monitors you know. Is the "revert versus certify" finding (H4)
   already folklore or published, for example in conformal policy control, safe policy improvement
   or rollback literature?
3. **Empirical ML reviewer.** Challenge baselines, fairness, matched information, the
   synthetic-heavy evidence, the evaluator-oracle utilities in H4, the onset-informed baselines,
   seed reuse, exposed real-data windows, the statistical comparisons, and whether E1–E3 can
   actually falsify anything. Check that H1–H4's numbers match the cited artifacts.
4. **Sceptical programme-committee member.** Is this important enough for ICML or NeurIPS (main
   or Datasets & Benchmarks)? What is the one-sentence takeaway, and would a practitioner change
   behaviour? Is Claim A a contribution or a restatement of the obvious?

For each reviewer, give:
- FATAL weaknesses, if any; a fatal weakness means the claim cannot stand as written;
- MAJOR weaknesses;
- possible remedies;
- the exact evidence (proof, citation, experiment, artifact check) that would resolve each item.

Then give a joint summary:
- a score from 1 to 10 for main-track ICML and another for NeurIPS D&B;
- whether the decision should be BENCHMARK_PAPER, NEW_METHOD, PIVOT or NO_GO, and why;
- the three changes that would most strengthen the proposal.

Be calibrated. Do not manufacture objections, and do not wave through unsupported claims. An
attractive score is not the goal; resolving validity and novelty is.

## Round-2 specific instructions

This is a **second full adversarial review**, not a wording check. In addition to the four
perspectives above:

- For **each round-1 FATAL and MAJOR item**, state whether round 2 resolved it (RESOLVED /
  PARTIALLY / NOT RESOLVED / NEWLY BROKEN), with reasons. Check Lemma L's proof sketch, the
  applicability table, the arm-by-arm validity table (§4), the matching levels and multiplicity
  table (§5), and the restated H1–H4 against the artifacts.
- Attack the **new** material:
  - Claim B as a contribution;
  - the benchmark-contract deliverable;
  - E2 and E3 designs (power, falsifiability, confounds);
  - the revised E4, which uses held-out EIA balancing authorities from the local snapshot.
    Consider selection leakage, cross-authority correlation, the overlap with examined calendar
    windows, and whether a coverage gate is truly outcome-free.
  - the abandonment criteria.
- Say explicitly whether **another refinement round would resolve significant objections**, or
  whether remaining objections can only be settled by running E1–E4. The author will stop
  refinement if no new evidence or resolution is possible without experiments.
- Give updated scores (ICML main; NeurIPS D&B) and a final decision recommendation
  (BENCHMARK_PAPER / NEW_METHOD / PIVOT / NO_GO).
