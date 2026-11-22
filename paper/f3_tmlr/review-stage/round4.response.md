**Overall score: 7/10 — accept. Verdict: Almost.**

This is a substantive and generally well-calibrated paper. The remaining issues are writing and presentation problems that can be corrected without changing results or running experiments. I found no critical flaw in the presented argument during this manuscript-only review.

I read the full manuscript, all 29 included table/figure TeX files, the bibliography, and visually inspected all 33 PDF pages. No underlying data, protected confirmation runs, or sealed group were accessed. All anchors below refer to the current submission.

Source: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.tex" purpose="source"}

Rendered manuscript: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.pdf" purpose="source"}

**Summary**

The paper studies a useful operational target: cumulative realized harm relative to retaining an incumbent, including switching fees, when paired losses are revealed through delayed, missing, or purchased labels. Its shield combines an anytime sampling bound with reserves for pending exposure and rollback. The deterministic full-sampling result, probabilistic sampled-feedback result, conditional reserve lower bound, and first-spell ruin bound form a coherent contribution. Experiments demonstrate the safety–utility tradeoff and report several unfavorable outcomes honestly.

The manuscript is close to submission quality. Its most important remaining corrections are reconciling the stream-provenance table with its accompanying text, removing an obsolete limitation that understates the documentation now present, and giving the calibrated comparator variants an unambiguous operational definition.

**Ranked strengths**

1. **A precise, meaningful target.** The distinction between realized intervention harm, challenger quality, and future payback is clear. Fees, the reference policy, shadow prediction assumptions, and the separation of query cost from harm are explicitly explained (§2, pp. 2–4).

2. **The theoretical claims have useful scope qualifications.** The lower bound is restricted to first-promotion events with probability greater than \(\delta\), and the rollback versus remaining-horizon branches are distinguished. The ruin result has its own positive conditional-gain assumptions. These qualifications should be retained.

3. **The empirical narrative preserves the cost of safety.** The paper reports the shield’s higher cost than Wald in the original regimes, its residual harm on harmful streams, the calibrated CUSUM’s utility advantage on beneficial streams, and v3’s unfavorable outcomes at some budgets. This supports credibility.

4. **The observation and evaluation semantics are unusually explicit.** Exogenous outcomes, logged paired predictions, simulated release times, policy-seed dependence, cached-stream reuse, and the v3 second look are all discussed.

5. **The pedagogical material is helpful.** The running example and Figure 1 explain the two reserves effectively. Figure 4 makes the correlational exposure-ratio result interpretable without presenting it as a law.

**Ranked weaknesses and writing-only fixes**

**Critical: none identified.**

**Major 1 — The stream-provenance table contradicts the accompanying provenance account.**

- **Anchors:** Appendix D.3, pp. 26–27; `main.tex:476–485`; Table 15.
- The prose identifies documented model pairs for seven atlas streams and describes Criteo’s task/source. Table 15 nevertheless labels all nine atlas model pairs “not documented,” and labels Criteo’s task and source “not in the inventory.”
- The table caption also defines “not documented” using the cache documentation or inventory, while the preceding paragraph adds evidence from linked historical scripts. The reader cannot tell whether the table is deliberately restricted to an older inventory or is intended to summarize current provenance knowledge.
- **Fix:** Reconcile the table with the evidence already stated in Appendix D.3. Either populate the seven model-pair entries from that text, with an explicit provenance note about the linked script, or clearly distinguish “cache inventory field” from “model pair documented by linked source.” Preserve the genuinely unknown entries for `openml_ldpa` and `uci_occupancy`.
- Describe the SHA-256 result precisely as identity between cached loss files and the earlier run’s files; present the associated script as construction documentation. This avoids making file identity sound like an independently rerun reconstruction.

Relevant table source: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/tables/app_streams_desc.tex" purpose="source"}

**Major 2 — The conclusion understates documentation that is already present.**

- **Anchors:** §7, p. 18, `main.tex:382`; Appendix C, pp. 23–24, `main.tex:444–449`.
- The limitation stating that the manuscript does not fully specify the 47-regime family, v3 candidate grid and selection rule, or regression aggregation conflicts with the detailed construction, grid, score, tie preference, unit definitions, and OLS specification in Appendix C.
- **Fix:** Replace this blanket reproducibility criticism with a direct Appendix C pointer. Retain the actual limitations: stream reuse, unknown provenance for two streams, simulated feedback, restricted comparator families, exogenous outcomes, v3’s second look, and correlational analysis.
- This is an important correction in the direction of **avoiding understatement**. The existing documentation deserves to be represented accurately; any remaining unknown detail should be recorded specifically as an open item.

**Major 3 — The calibrated comparator variants need a compact, explicit operational definition.**

- **Anchors:** §5.2, p. 14, `main.tex:308–314`; Appendix E, p. 28, `main.tex:503–510`.
- The search grids, sample sizes, qualification criterion, selection directions, fallback, and headroom transfer are clearly reported. The less clear part is the relationship between the original CUSUM rollback and the calibrated version, which additionally receives a stop based on resolved harm.
- **Fix:** Add a short paragraph or small methods table defining each calibrated variant: its inherited promotion/acquisition rule, stopping statistic, exact threshold inequality, whether fees enter that statistic, and what happens after the cumulative stop. Link this definition from §5.2.
- State that matching the numerical level `.05` by calibration is an **empirical per-regime selection criterion**, while the shield’s theorem controls probability for each admissible loss sequence. The paper already says the calibration uses point estimates; one further sentence would make the distinction complete.
- Qualify “Only the stop-loss is told \(R\)” at `main.tex:248` as referring to the original comparator set, since the calibrated CUSUM subsequently receives an \(R\)-dependent safeguard.
- The exact semantics to put in this paragraph are an **open reporting item**, not grounds to infer an implementation error.

**Major 4 — A few explanatory sentences extend beyond the carefully qualified formal statements.**

- **Anchors:** §5.3, p. 15, `main.tex:331`; §5.4, p. 16, `main.tex:345`; §3, p. 5, `main.tex:146`.
- At \(h=6\), “a promotion holds for … 6 exposed rounds” reads as a universal duration limit. Arriving evidence of gains can replenish the budget.
- “A valid controller cannot stay deployed through [the window] without banked gains” loses the first-promotion/event-probability and remaining-horizon qualifications of Proposition 2.
- “The reserve cannot be dropped” is stronger shorthand than the proposition’s stated conditional necessity.
- **Fix:** Use “initial uncredited exposure allowance” for the six-round example. Tie the regime-map interpretation explicitly to the first-promotion rollback branch, and describe the reserve as necessary under the proposition’s conditions. Preserve the stronger general guarantee of Theorem 1; it does not need weakening.

**Major 5 — Several important tables and the regime heatmap are harder to read than necessary.**

- **Anchors:** Figure 2, p. 12; Table 9, p. 15; Table 15, p. 27; `main.tex:319–338, 483–485`.
- Table 9 is compressed into very small text, while Table 10 on the same page is enlarged substantially. Table 15 combines long provenance text with six numeric/status columns and becomes particularly small. Figure 2(a)’s thirty row labels and abbreviated method labels require close zoom.
- **Fix:** Avoid expanding compact tables to full width, and avoid shrinking wide mixed-content tables wholesale. Split Table 15 into a provenance panel and a numeric-summary panel, retaining every value. Give the calibration table more vertical space or split its settings and outcomes. Allocate more width to Figure 2(a), for example by stacking its panels.
- These are layout changes, not requests for new evidence or new plots.

**Minor revisions, ranked**

1. **Float order:** Table 8, the real-stream summary, appears inside §5.2 on p. 14; Table 9, the calibration result, appears at the start of §5.3 on p. 15. Move the calibration table into the calibration subsection and the real table after the opening real-stream paragraph (`main.tex:316–329`). Let labels renumber automatically.

2. **Signed comparison wording:** “Cheaper … by −50.2” on p. 14 is awkward. Write “the cost difference relative to the shield is −50.2 [−91.9, −19.8]” (`main.tex:312`). Preserve all numbers and their signs.

3. **Broken table range in prose:** Appendix C prints “Tables 23–13” on p. 24 (`main.tex:449`). Cite the three relevant tables individually rather than using a descending range.

4. **Table 5 caption:** “The last two columns give … pooled and … worst regime” no longer matches the two-panel table. Name the pooled-rate, worst-regime-rate, and worst-regime columns explicitly (`main.tex:274`, p. 11).

5. **Rounded zero in Table 6:** The paced row displays `0.000` for both subsets, although the manuscript reports a nonzero exceedance. Add a rounding note or retain a count alongside the rate; do not let a rounded zero imply zero violations (p. 13).

6. **Regression covariate terminology:** Appendix C defines the covariate as \(B/(rT)\), available labels per expected disagreement, rather than realized label use. Use that phrase in the main text and Table 24 caption instead of the potentially ambiguous “label-use variable” (`main.tex:348, 446, 540`).

7. **Terminology in tables:** Replace raw identifiers such as `wald_cut`, `f3v2d_R20`, and `never` with the existing readable method names in reader-facing main tables, retaining a mapping to configuration IDs in the appendix.

8. **Tone of §5.1:** “The budget holds and the comparators break it” is stronger than the careful explanation that most original comparators were not designed to enforce \(R\). A descriptive heading such as “Budget exceedance and utility” would fit the actual evaluation.

9. **Repetition:** The same fidelity disclaimer appears in §§5, 7, Appendix C, and Appendix E. The simulation settings recur in adjacent paragraphs. The running example is revisited four times. Keep the precise methods definition and one limitations statement; shorten repeated explanations, particularly `main.tex:219, 232, 254–256, 438–439`.

10. **Formatting:** Remove visible red/green link boxes if compatible with the submission style. Keep short proposition statements together where practical: Proposition 1 splits across pp. 3–4, and Proposition 3 across pp. 8–9. Table 17 interrupts the reproducibility paragraph across pp. 28–29.

**Visual review**

| Element | Assessment |
|---|---|
| Figure 1, p. 6 | Strong explanatory figure. The 35/40 rollback times and 20/25 peak harms match its caption. Existing legend text is somewhat small but usable. |
| Figure 2, p. 12 | Caption is clear about the single paced exceedance and real-stream zeros. Heatmap labels are the principal readability problem; enlarge their available space. |
| Figure 3, p. 13 | Readable and correctly described as a quantile diagnostic. Keep the explicit warning that \(q_{99}\le R\) is not the guarantee. |
| Figure 4, p. 16 | Clear axes, reference levels, and median markers. Caption correctly distinguishes connected medians from a fitted relationship. |
| Main tables | Booktabs styling is consistent. Font scale is not: Tables 9 and 10 are the clearest contrast; Table 11 is also enlarged relative to surrounding text. |
| Appendix tables | Complete and unclipped. Table 15 is too compressed; Tables 19–22 are small but structured. Table 14 continues with repeated headers appropriately. |
| Overall layout | No clipped text, overlapping elements, missing glyphs, or unresolved references observed. Float spacing on pp. 29–33 could be tightened, but it is secondary to main-text readability. |

**Open reporting/evidence items**

These are items to resolve from existing documentation if available, not proposed experiments:

- Exact calibrated CUSUM cumulative-stop semantics and whether it permanently prevents later promotion.
- The calibration/evaluation seed-block identifiers and their relationship to the registry, if a precise supplement pointer is available.
- Any remaining v3 tie rule after candidates tie on the stated score tolerance and pacing floor.
- The exact linked provenance-script/manifest identifiers supporting the seven recovered atlas model descriptions.
- The machine identity remains explicitly unknown in the ledger. Retain that limitation unless recorded evidence exists.

**References**

The bibliography covers the main neighboring areas, including conservative bandits, delayed baseline safety, confidence sequences, safe policy improvement, active model selection, and deployment monitoring. I have no specific additional citation to recommend from this manuscript-only review. Adding speculative references would not address the current problems.

Bibliography reviewed: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/refs.bib" purpose="source"}
