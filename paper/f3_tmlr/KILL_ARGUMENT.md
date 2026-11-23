# Kill Argument Report: A Pathwise Harm Budget for Reversible Model Promotion under Delayed, Missing and Scarce Feedback

**Date**: 2026-11-22
**Reviewer model**: claude-sonnet-5-5, single-context sequential run (attack written first, then adjudicated against the text). This is not two fresh spawned threads, so review_independence is `same-context` and acceptance_status is `provisional`.
**Attack agent / Adjudicator agent**: none (no spawn_agent used)
**Scope read**: main.tex, tables/*.tex, figures/*.tex (via compiled main.pdf text), main.pdf. Nothing else.
**Verdict**: WARN (`reason_code: partial_critical_or_repeated_major`). Zero still_unresolved points; three partially answered points are major.

## Net assessment

Theorem 1 and its proof hold up on a manuscript-level read, the assumptions (Assumption L, O1-O4) are stated precisely, and the text repeatedly marks its own limits (first-promotion-only lower bound, correlational regime map, cached losses with simulated feedback, development-only screen). The paper would probably survive a TMLR read on correctness. What a hostile reviewer can still exploit is the gap between body-text caveats and abstract/headline phrasing: "matching lower bound", worst-regime exceedance of comparators, the 100-stream result and the "registered"/"pre-stated" labels each read stronger in the abstract than in Sections 4-5 and Appendix C. All fixes are sentence-level and use existing material.

## Attack memo (verbatim)

> The guarantee is real but much thinner than advertised. Under full sampling the "shield" is a deterministic worst-case stop-loss that books every unlabelled exposed round at one unit and reserves a second fee; that sup H_t <= R follows by construction, so the zero-violation tables (Tables 4, 9, 100-stream screen) test arithmetic, not a finding. The abstract's "matching lower bound" is Proposition 2, which covers only the first promotion, needs a feedback-blind window m <= d (so it says nothing when d < R-2k, the running example's own d=5, h=14), and is attained only by the full-sampling variant on an all-harm tape; nothing shows the sampling width or later spells are necessary. The empirical case then compares against heuristics that were tuned for cost, mostly not told R, and quotes their worst regime (64-99%) from author-built stress regimes that withhold unfavourable labels; pooled over the 24 original regimes they exceed R in 1-6% of runs. Where feedback is truly scarce and slow (x >= 1, the motivating setting) the shield costs more than never switching. Real-data support is 12 cached streams from the authors' earlier studies with simulated delay and dropout (two of 14 streams were dropped after the run, disclosed only in Appendix C), plus a 100-stream screen that the text itself calls development evidence yet the abstract reports as "beat never switching on 57". The regime-map prediction was fixed after its outputs already existed. Correct, but overclaimed and under-evidenced for the stated scope.

## Adjudication (per-point)

### P_1: Scope of the guarantee (assumptions, reference policy, what H_t omits)
**Attack claim**: Guarantee needs Assumption L (logged paired predictions, shared outcome), O1 exogeneity, and excludes label and shadow costs; it is relative to never switching only.
**Verdict**: answered_by_current_text
**Evidence**: Section 2 states Assumption L, O1-O4, "Why harm against never switching", label cost "accounted separately", shadow cost "not charged"; Section 7 and the Broader impact statement restate exogeneity and that the guarantee does not show the challenger is good.
**Severity if unresolved**: minor
**Residual fix (optional)**: none required.

### P_2: Lower bound and triviality of the full-sampling guarantee ("matching" overstated)
**Attack claim**: Abstract's "matching lower bound" is first-promotion only, requires m <= d, and is attained only by full sampling on the all-harm tape; full-sampling validity is accounting by construction.
**Verdict**: partially_answered
**Evidence**: Table 1 scope column, the text after Proposition 2 ("concerns the first promotion and its stated event only"), Appendix A.3 and Table 12 (rollback branch binds only when d >= h) answer it in the body. The abstract says "when enough horizon remains" but omits the d >= R-2k condition and the first-promotion restriction. The running example (d=5, h=14) is outside the binding case. Nothing in the text argues that the paced width or later spells are necessary, and the "attained" column of Table 12 is an identity check on spell length, not tightness for d < h.
**Severity if unresolved**: major
**Recommended fix**: In the abstract, change to "a matching lower bound holds for the first promotion when the label delay is at least R - 2k and enough horizon remains" and add one sentence in Section 4 stating that tightness of the sampling width and of later spells is not claimed.

### P_3: Comparison design (comparators not budget-aware; worst-regime framing)
**Attack claim**: Comparators are cost-tuned heuristics, only the stop-loss is told R, and 64-99% is a worst-regime figure from authors' stress regimes built to hide unfavourable labels.
**Verdict**: partially_answered
**Evidence**: Section 5 intro says exceedance for non-told comparators "measures the absence of a guarantee rather than a design flaw"; Tables 5-6 give pooled rates (stress 0.13-0.23, original 0.011-0.056); Section 5.2 calibrates the stop-loss and CUSUM rollback and shows they pass only by blocking promotion or fail on fresh seeds; Table 7 ablations isolate each reserve. Not answered: the abstract and introduction quote only the worst-regime range, the worst regime is adverse dropout (constructed by the authors) for four of five, and no budget-aware baseline with a pending reserve but weaker accounting is compared on cost (only on violations, as ablations).
**Severity if unresolved**: major
**Recommended fix**: In the abstract and Introduction, add that the figures are for author-built stress regimes and give the pooled original-regime range (1-6%); in Section 5.2 add one sentence that the comparison shows the reserves are necessary for the guarantee, not that no other budget-aware design could match the shield's cost.

### P_4: Utility claims against the motivating setting
**Attack claim**: In the slow, scarce-label setting the shield gives up all gain or costs more than never switching; "beats never switching" is overstated.
**Verdict**: answered_by_current_text
**Evidence**: Abstract and Section 5.4 state the x < .5 versus x >= 1 split and that it is "an empirical association, not a theorem"; Section 5.3 reports being within 10.0 units of never switching at h=6 and 13-59 units above it on harmful streams; Appendix Table 15 shows v3 worse than never at R=12; Section 1 reports 46% retention at h=14. The caveats are present and quantified.
**Severity if unresolved**: minor
**Residual fix (optional)**: add "at h >= 14" after "beats never switching" in the abstract.

### P_5: Scope of the real-data evidence
**Attack claim**: 12 cached streams from the authors' earlier work, simulated delay and adversarial corruption, a post-hoc exclusion of two streams, and a 100-stream screen with author-defined success.
**Verdict**: partially_answered
**Evidence**: Section 5 ("simulated feedback conditions", "not end-to-end model comparisons"), Section 5.3 ("consistency check rather than independent evidence"; screen is "development evidence ... not repeated on fresh streams"), Section 7 answer most of it. Not answered in the main text: Appendix C says the protocol was run on 14 streams and two were removed afterwards for unrecorded provenance; Section 5 and Section 7 do not say so. The abstract reports the screen result ("beat never switching on 57") without the development-evidence label, and the support criterion is author-chosen.
**Severity if unresolved**: major
**Recommended fix**: Move the 14-to-12 stream exclusion sentence into Section 5 (Real streams) and Section 7; add "development screen" to the abstract's mention of the 100 streams.

### P_6: "Registered" and "pre-stated" language
**Attack claim**: Registration is an in-repository dated commit, not an external registry, and the regime-map test used existing outputs, so "fixed before the test run" does not mean the prediction preceded the data.
**Verdict**: partially_answered
**Evidence**: Appendix C states the registration date, frozen arms and that the exposure-ratio test "was fixed before its first run, using existing outputs only". Section 4 says "fixed before the test run" and Section 5.4 calls the tests "pre-stated" without noting the outputs already existed; thresholds .5 and 1 were therefore stated after authors had seen the runs. The text does call the test correlational and clusters are only 8 real streams.
**Severity if unresolved**: minor
**Recommended fix**: In Section 5.4 add "computed on outputs that already existed; the thresholds were fixed before the analysis script ran, not before the runs"; in the abstract say "a protocol registered in a dated commit".

## Summary
Total rejection points: 6
- answered_by_current_text: 2
- partially_answered: 4
- still_unresolved: 0

## Top action items
1. Qualify the abstract's lower-bound sentence (first promotion, delay at least R - 2k) and state that tightness of the width and later spells is not claimed (P_2).
2. Qualify the comparator headline (author-built stress regimes; pooled original-regime 1-6%) and add the "necessity of reserves, not optimality of cost" sentence (P_3).
3. Disclose the 14-to-12 stream exclusion in Section 5/7 and label the 100-stream screen as development evidence in the abstract (P_5); soften "pre-stated" in Section 5.4 (P_6).

## Recommendation
All remaining items are writing-level (no new experiments). Apply in the next improvement round; none requires changing Theorem 1.
