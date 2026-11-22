# Round 6 — 7/10, weak accept; Almost

This was a fresh, bias-guarded TMLR-style writing and presentation review. It is not an external acceptance judgment or a certification of scientific results.

I reviewed the complete `main.tex`, all 30 directly included TeX files, `refs.bib`, and every page of the pre-fix 36-page PDF: main text pp. 1–20, references pp. 21–23, and appendices pp. 23–36. The four included figures were inspected in their rendered manuscript context. I did not read prior-round materials, research code, configurations, data, results, registries, the protected confirmation block, `civic_records_sealed`, or `table_real48.tex`. I made no edits. Bibliographic accuracy and cited-work characterizations were not externally verified; mathematical validity, numerical correctness, reproducibility, and novelty were outside this writing-only review.

The manuscript has a clear central idea: budget the harm of reversible deployment, including pending exposure and rollback fees. The running example and Figure 1 explain that idea effectively. The distinction between the mathematical guarantee, empirical exceedance counts, and the correlational exposure-ratio analysis is explicit. The paper also acknowledges cached-loss provenance gaps, simulated latency, repeated use of real streams, and comparator limitations.

The principal weakness is presentation efficiency. The paper repeats its guarantee and caveats, while readers must reconcile several method names and two accounting constructions. The PDF alternates between dense prose and spacious float pages. The following fixes require no new evidence, experiments, results, or citations.

## Ranked recommendations

1. **Clarify query ownership at promotion rounds (p. 5, “Queries”).** The paragraph begins with incumbent-deployed rounds, then describes queries as occurring on rounds with `a=0`. A promotion round has `a_{t-1}=0` but `a_t=1`. State the three cases directly: remaining on the incumbent uses the inner rule’s query, accepted challenger deployment uses the shield’s query, and rollback makes no query.

2. **Distinguish the common safety condition from the accounting formulas (pp. 4–8 and Appendix B, p. 26).** The main construction charges a sampled current round `1/pi`; settlement initially books it at one. Table 3 says all variants use “the same check,” and Algorithm 1 appears to describe them all. Clarify that variants share the acceptance condition `W_t <= R`, while settlement changes how `W_t` is constructed. Point the algorithm caption to Appendix B.

3. **Remove two lower-bound ambiguities (pp. 9 and 24).** On p. 9, `n` is described as disagreements remaining “thereafter,” though it counts from promotion `j` through `T`, including the blind window. Say “from promotion through the horizon.” Table 12 should say the first spell can be longer than the feedback-blind portion when labels return before rollback. Align its identity and rollback-condition labels with the table header.

4. **Use consistent reader-facing method names, especially in the main simulation table and appendix tables.** Readers encounter “Shield, paced,” “paced with settlement,” `f3v2d`, “v2,” and “v3.” Use “Full,” “Paced,” “Blind,” and “Label-scarce” consistently in results tables; retain implementation identifiers in the frozen-arm specification table.

5. **Repair table sizing and float placement (pp. 7, 12, 16, 25, 28, 31, 34 and 36).** Several pages have large vertical gaps and Table 13 occupies a mostly empty page. Table 5 wraps `R=20` and `delta=.05` awkwardly, Table 10 is enlarged beyond surrounding text, and Tables 15 and 25 are unnecessarily small. Use a consistent table size, avoid enlarging narrow tables to the full line width, shorten repeated method labels, and rebalance floats without increasing the 36-page draft.

6. **Improve Figure 2’s heatmap readability within its existing footprint (p. 13).** The pattern is visible, but regime labels and small shield-column values need zooming. Allocate more width to the heatmap or shorten existing labels while retaining their mapping. The data and conclusions need not change.

7. **Shorten repetition and simplify the abstract (pp. 1–5, 8–10, 19–20).** The abstract introduces first-promotion events, the rollback branch, horizon conditions, and an attainment formula before readers know those objects. Preserve the scope but defer detail to the contribution table and proposition. Compress repeated restatements of O1–O4, the deterministic full-sampling guarantee, and comparator provenance; keep one plain-language explanation beside each formal statement.

References render cleanly. I saw no unresolved references, missing glyphs, overlapping equations, or clipped manuscript text.

**Recommendation: 7/10 — weak accept; Almost.** Continue with a bounded editorial pass focused on consistency, compression, and layout. The recommendation is provisional and is not an independent external acceptance review.
