## 1. Overall score: **7/10 — Accept**

**Verdict: Almost.** The manuscript has a coherent contribution and substantial supporting analysis. I found no critical defect in the central accounting argument, but several statements should be aligned more precisely with the proof and the reported experiments before submission.

I reviewed all 34 pages of :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.pdf" purpose="source"}, together with :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.tex" purpose="source"} and its included table and figure sources. This review assesses the manuscript’s argument and presentation; it does not independently verify the experimental results.

## 2. Summary

The paper proposes a wrapper for reversible model promotion that bounds cumulative excess loss against never switching, including switching fees, under delayed, sampled, or missing feedback. Its main contribution is the combination of a design-based bound with explicit pending-feedback and rollback reserves; simulation and cached-loss experiments show budget control, while documenting the utility sacrificed relative to an unconstrained promotion rule.

## 3. Ranked strengths

1. **The target is useful and clearly distinguished from prediction accuracy or prospective payback.** Pages 1–4 explain why a live intervention budget differs from certifying future improvement. The paper identifies the reference policy, loss range, switching fees, paired-loss availability, and exogeneity assumptions.

2. **The main accounting argument is transparent.** The decomposition into blind exposure, resolved inverse-propensity estimates, pending reserves, and sampling error makes Theorem 1 understandable and auditable. Reserving the rollback fee connects the upper bound to an actionable controller rather than merely a monitoring statistic.

3. **The lower bound gives the reserve construction scientific substance.** Proposition 2 explicitly includes the first-promotion event probability and the competing terminal-horizon branch. The manuscript generally preserves these qualifications instead of presenting a universal optimality claim.

4. **The experiments have identifiable argumentative duties.** Ablations test the accounting terms; calibrated comparators ask whether a simpler resolved-harm threshold suffices; the regime map studies when the guarantee retains useful benefit. The harmful-stream table distinguishes improvement over Wald from improvement over never switching.

5. **Unfavorable results remain visible.** Table 5 reports the higher pooled cost than Wald, Table 10 reports positive cost relative to never switching on harmful streams, and the appendix retains the v3 failures. The paper also distinguishes controller seeds from independent stream evidence and documents simulated delays and incomplete provenance.

6. **The related-work discussion engages plausible neighboring formulations.** Conservative bandits, delayed baseline safety, off-policy confidence sequences, safe policy improvement, and label-efficient selection are distinguished by their targets and feedback assumptions.

## 4–5. Ranked weaknesses and actionable fixes

### CRITICAL

**None identified.**

### MAJOR 1 — The formal object being quantified over is inconsistent when delays adapt to past query coins

**Where:** Setting and observation model, pp. 2–3; Definition 1; Theorem 1; Appendix A.2, p. 22.

A “tape” is defined as the sequence of losses, flags, **and delays**, while O2 says the current query coin is independent of the tape given the past. O3 then permits delays to depend on past coins. These statements need a more precise joint interpretation: for example, a future delay depending on today’s query coin makes the complete realized delay sequence informative about that coin.

The proof uses the appropriate formulation: it fixes the loss/flag sequence and considers a nonanticipating delay rule. The definition and theorem should use that same object. This is an exposition/formalization issue, not a demonstrated failure of the martingale proof.

**Writing-only fix:** Define a fixed loss/flag sequence separately from an admissible delay rule. State the budget uniformly over those sequences and rules, with probability over the controller’s coins, without conditioning on the realized future delay sequence. Carry that wording through Definition 1, Theorem 1, and the abstract.

The abstract should also say that a delay cannot depend on **the current round’s query coin**. Its present “do not depend on its query coins” unnecessarily excludes dependence on past coins that O3 and the proof allow.

**Open evidence item:** None, if the intended result is the one proved in Appendix A.2.

### MAJOR 2 — The headline worst-regime comparison needs the high-fee condition stated explicitly

**Where:** Abstract, p. 1; scenario settings and simulation description, pp. 9–10; Table 5, p. 11; Figure 2, p. 12; Table 14, p. 26.

The main settings repeatedly give \(k=3\), and describe \(R=12,20,30\) as headrooms \(6,14,24\). However, the “High switch fee” regime uses \(k=30\). CUSUM’s headline worst-regime exceedance rate, 0.987 at \(R=20\), occurs in that regime. A first promotion already exceeds \(R=20\), even with the most favorable one-round loss.

The number is valid as a stress result, but it has a different interpretation from failure to account for pending harmful labels. The override is too far from the headline comparison, and the headroom correspondence is not uniform across the pooled regimes.

**Writing-only fix:** State the fee and label-budget overrides in the main experimental settings. Immediately after the worst-regime comparison, explain that CUSUM’s worst case is the \(k=30>R=20\) regime, while the other four worst cases are adverse dropout. Retain all numbers and retain the pooled rates. Describe \(h=6,14,24\) as the **default-regime** headrooms.

**Open evidence item:** None.

### MAJOR 3 — “Attainment in 12 of 12 cells” conflates two different checks

**Where:** Discussion after Proposition 2, p. 8; Appendix A.3, p. 22; Table 26, p. 33.

The manuscript says it checked “feedback-blind-window attainment in 12 of 12” cells. Table 26 reports first-spell lengths, the quantity \(\lfloor R-2k\rfloor\), and \(\min(d,\lfloor R-2k\rfloor)\), followed by an undifferentiated “attained” column.

For example, at \(d=1,R=20\), the first spell is 14 rounds but the feedback-blind window is one round. The first-spell identity is useful, and Appendix A.3 correctly says the lower bound does not govern longer holds when labels arrive during them. The main summary and table should preserve that distinction.

**Writing-only fix:** Report that the first-spell identity holds in all 12 cells. Separately identify which cells satisfy the stated delay condition for rollback-branch tightness. Rename or split the “attained” column so readers can tell whether it refers to the algebraic first-spell identity or the lower bound within a feedback-blind window.

**Open evidence item:** None; the displayed \(d,R\), and spell lengths suffice.

### MINOR 1 — Some reporting language still sounds like an internal progress report

**Where:** Table 1, p. 2; Table 4, p. 11; variants table, p. 7; appendix comparator description, p. 29.

Examples include “Proposition … (proved),” the repeated “supported” verdicts, “designed after the real-stream run,” and “none is called state of the art.” The last phrase describes what the authors chose to call something rather than explaining the comparator.

Keep the registration information and provenance, but place development chronology in the protocol appendix. Remove “none is called state of the art.” Present the main findings as results with their numerical criteria, rather than repeatedly announcing that a criterion was supported.

### MINOR 2 — Qualification is sometimes repeated after the relevant scope is already explicit

**Where:** pp. 3, 8, 10, 16, 19, 24, and 29.

The distinction between adapters and native reproductions is repeated many times. The first-promotion restriction is restated immediately after a paragraph that already gives it precisely. Correlational status appears repeatedly, including as the conclusion’s final clause.

These are mostly correct qualifications, not reasons to weaken the results further. Consolidate repeated provenance and generic caveats. Keep necessary conditions beside the relevant claims. End the conclusion with the supported guarantee or observed benefit, after retaining the correlational qualification with the association result.

### MINOR 3 — The introduction does not finish the problem → gap → idea → strongest-result sequence

**Where:** p. 1 and Table 1, p. 2.

The opening successfully starts with the decision problem. It then reaches the proposed target, but the introduction ends without a compact empirical result paragraph.

Add the central quantitative comparison already supported by the paper: budget control, cost 69.43 versus 71.53 for never switching and 68.47 for Wald, and the stress-regime improvement. This would convey both the benefit and its cost before the formal setting.

### MINOR 4 — The regime-map prose softens the above-never results

**Where:** p. 16; Table 11, p. 17.

For \(x\ge1\), the prose says the shield is “about as costly as never switching.” Several paced-arm bin medians exceed one, reaching 1.17. The caption defines this correctly, but the prose should also state that some bins cost more than never switching.

Use the displayed range and explain \(L>1\) directly. This is an observed weakness in those bins, not an additional benefit to be relabeled as a tradeoff.

### MINOR 5 — Small terminology and precision issues

- “Original 30 regimes” in Table 12 conflicts with the established distinction between 24 original and six stress regimes. Use “registered 30 regimes.”
- “Lower cost … by −5.19” on p. 13 is awkward. Write “a cost difference of −5.19” or “5.19 lower,” preserving the interval.
- “Full sampling” is described as querying every exposed round, although label exhaustion produces blind rounds. State the exhaustion behavior beside the variant definition.
- Appendix A.3’s exact \(\lfloor R-2k\rfloor\) spell statement should specify the nontrivial promotion range, avoiding a negative “spell length” when \(R<2k\).
- Table 27 rounds some positive theoretical bounds to 0.0000. Scientific notation would distinguish tiny bounds from exact zero.

## 6. Missing references

I do not identify a specific essential missing reference from the manuscript alone. The principal neighboring literatures are covered. I did not use external search or independently verify the recent references or their attributed claims.

The two streams with missing task/model/source records remain an **open provenance item**. The current restriction to cached paired-loss evaluation is appropriately explicit; stronger end-to-end empirical claims would require those records.

## 7. Visual review

**Figures and labels**

- **Figure 1, p. 6:** Clear and effective. The two deployment traces, pending-label panel, rollback band, and budget line communicate the mechanism. No visible clipping.
- **Figure 2, p. 12:** The heatmap is informative but its regime names and cell labels are very small. The 0.001 paced exceedance is difficult to see at ordinary page scale. Allocate more width to panel (a), or separate the panels.
- **Figure 3, p. 13:** The mean-cost/tail-harm comparison is useful, and the caption correctly distinguishes the quantile diagnostic from the theorem. The faint comparator points are difficult to identify individually.
- **Figure 4, p. 17:** Axes, reference lines, and the meaning of \(L=0,1\) are clear. The source-specific panels are well chosen. Some markers overlap, but the plot remains interpretable.

**Captions and alignment**

Captions consistently sit beneath figures and above tables. Figure captions are unusually long; much of the repeated implementation/provenance language could move into the surrounding text. Table 14’s caption has a noticeably narrower measure than its table and neighboring captions.

**Layout and float placement**

The PDF has no obvious broken equations, overlapping text, or missing objects. Several pages interrupt sentences with full float pages. Page 15 has substantial unused vertical space around two small tables; pages 28, 33, and 34 also have sparse float arrangements. The “6 stress regimes” separator is stranded at the bottom of p. 26 before its rows begin on p. 27.

**Tables and readability**

Table 5’s repeated controller column wraps some method names over several lines. Tables 8–9 on p. 15 are small despite substantial free page space. Tables 17–18 and the detailed appendix result tables also require zooming.

Table scaling is inconsistent: Table 10 on p. 16 is enlarged substantially, while more important comparison tables remain compressed. Use consistent font sizes and column widths, avoiding automatic upscaling of short tables and excessive shrinking of wide ones.

**Visual consistency**

Typography, color roles, mathematical notation, and section hierarchy are generally consistent. The largest remaining inconsistency is table scale rather than figure style.

## 8. Verdict: **Almost**

The paper’s principal claim is credible on the manuscript’s own argument, and the empirical narrative generally respects the distinction between safety and utility. Align the delay-rule quantifiers with the proof, contextualize the high-fee worst case, distinguish the attainment checks, and improve the main-table presentation. These are targeted revisions; they do not require replacing the central story or concealing unfavorable results.
