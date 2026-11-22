**Score: 6/10 — weak accept. Verdict: Almost.**

I read the full manuscript source, every included LaTeX file and bibliography, and visually inspected all 32 PDF pages, including every appendix table and all four figures. This review uses the manuscript alone; I did not inspect research code, data, registries, or sealed material.

The paper presents a useful and clearly motivated target: controlling cumulative realised intervention harm, including switching fees, under delayed and incomplete feedback. Its strongest contribution is the combination of a design-based upper bound with explicit pending-feedback and rollback reserves; the manuscript needs tighter definitions and more consistent qualification of its lower-bound and empirical claims before submission.

Sources: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.pdf" purpose="source"} and :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.tex" purpose="source"}.

**Ranked strengths**

1. **A meaningful target with intelligible accounting.** The distinction between future payback, model quality and realised cumulative harm is useful. The reference policy, exogenous-outcome assumption, shadow predictions and separate treatment of label purchases are substantially clearer than in many deployment papers.
2. **The main safety argument is inspectable.** Theorem 1’s decomposition and rollback argument are short enough to audit. I found no clear counterexample to the full-sampling argument under the stated observation model. Appendix B explains why deterministic settlement preserves the design-based bound.
3. **The paper preserves unfavorable evidence.** The original/stress split, higher costs than Wald on the original regimes, worse performance than never switching on harmful streams, calibrated CUSUM’s cheaper beneficial-stream performance, and the paced violations are all retained.
4. **Useful experimental breadth and transparency.** The manuscript identifies simulated latency, previously exposed streams, limited baseline fidelity, and repeated real-stream looks. Figures 1 and 4 connect the mechanism and empirical pattern effectively.

**Ranked weaknesses and actionable fixes**

1. **Major — the resource and objective definitions are incomplete or inconsistent.** Locations: `main.tex:124–130, 198–201, 304, 430, 531–532`.

   At line 126, labels cost $c_q$ “out of a budget $B$,” suggesting a monetary budget. Subsequent acquisition rules treat $B$ as a number of labels. The primary empirical objective $J$ is described only as deployed loss plus label, switching and compute fees; the charged compute quantity and its coefficient are never defined. This also sits awkwardly beside the explicit exclusion of shadow-model compute.

   **Fix:** State whether $B$ caps query count or expenditure, then give one complete equation for $J$, defining every charged component and every fixed coefficient used in the reported experiments. Distinguish the compute included in $J$ from shadow compute excluded from $H$. Do not infer missing settings from the numerical results.

2. **Major — the blind branch is not mathematically defined in the main check.** Locations: `main.tex:183–189, 228–229`.

   Blind rounds have $\pi=0$, and $\kappa(\pi)$ receives an explicit blind convention. However, the width still contains $g_t(1/\pi-1)$. Thus the displayed $W_t$ and Algorithm 1 are undefined when labels run out, despite that being an intended operating condition.

   **Fix:** Define the variance increment separately: zero for blind rounds and $g_t(1/\pi-1)$ for monitored rounds. Give the blind check explicitly or use this piecewise increment throughout. This is a specification repair; it does not require changing the experiments or weakening Theorem 1.

3. **Major — the e-process comparator’s asserted guarantee lacks its necessary null and filtration.** Location: `main.tex:540–541`, PDF p. 27.

   The update $W\leftarrow W(1+\lambda_g Z)$ is said to have type-I error at most $\alpha$ under “the global null of no benefit.” A marginal no-benefit condition does not establish this under dependence or outcome-dependent release. The necessary condition concerns the conditional mean of the next included observation given the filtration in which the product is updated. A fair latent sign shared by all observations already illustrates why marginal mean zero is insufficient.

   **Fix:** Specify the conditional null and observation ordering under which the product is an e-process. Explicitly state that the experimental tapes need not satisfy that comparator-specific null. Preserve all comparator results; the problem is the unqualified validity statement.

4. **Major — several summaries overstate the reserve lower bound.** Locations: `main.tex:41, 87, 149, 289–293`; compare the correctly qualified discussion at `main.tex:274–276`.

   Proposition 2 concerns a **first-promotion event with probability greater than $\delta$**, a window of length at most $d$, and the minimum of a rollback and terminal-horizon branch. The abstract’s “exactly as long as any valid controller can” omits these conditions. The running example’s “15th would break the budget” also conflates the pre-action check including an exit reserve with immediately realised harm: the issue is retaining an affordable rollback.

   **Fix:** Carry the already stated qualifications into the abstract and running example. A suitable formulation is: “With sufficient remaining horizon, the shield attains the first-promotion lower bound on the all-disagreement, all-harm tape during the feedback-blind window.” Explain that the next exposure would make the guaranteed rollback unaffordable. Keep the strong attainment claim within its proved scope.

5. **Major — the exposure-ratio and calibration studies are not self-contained.** Locations: `main.tex:357–363, 391–399, 489–493`; Table 12, PDF p. 18.

   The 47-regime label-scarce family supporting a headline contribution is not specified comparably to the original 30 regimes. The manuscript does not enumerate the six exposure-ratio decision criteria. Table 12 labels its count column “units,” but reports 32 or 10 per fit, while the text defines units as regime/stream × arm × headroom and reports 502 overall. These appear to be cluster counts, but the manuscript does not resolve this. Calibration also lacks the tested parameter grids, the precise empirical acceptance rule, the fallback when no CUSUM threshold passes, and the headroom-transfer formula.

   **Fix:** Add the existing design specifications, clarify cluster counts versus analysis-unit counts, list the six decision rules, and state calibration selection/fallback and transfer rules. These are reporting fixes. If the necessary information is unavailable from the existing record, leave it as an explicit open item rather than reconstructing it from outcomes.

6. **Major evidence limitation — nine cached streams lack essential provenance.** Locations: `main.tex:513–518`; Table 14, PDF p. 26.

   The admission is appropriately candid, but missing model identities and training windows prevents assessment of chronology, leakage and the meaning of the challenger comparison for nine streams. Missing task/source records for three streams further restrict the empirical interpretation.

   **Fix now:** Surface this limitation in the main real-stream setup, not only Appendix D and a general limitation paragraph. Describe these results consistently as evaluation on cached paired losses with simulated feedback. **Open evidence item:** recover the missing existing provenance if possible. Do not invent metadata, silently omit these streams, or treat them as independently reproducible end-to-end model studies.

**Minor writing and calibration issues**

- `main.tex:286`: “all lie within Monte Carlo error of the bound” suggests closeness, which the loose $d=5$ cells do not show. Say that no observed frequency exceeds the bound by more than the reported 0.7 binomial standard errors, retaining the five point estimates above it.
- `main.tex:62`: “any delay or missing-label mechanism” should retain O3’s restriction on dependence on the current query coin.
- `main.tex:293`: the prediction is stated, paraphrased and qualified repeatedly. One precise prediction plus its non-theorem status is enough.
- `main.tex:98–118`, Tables 1–2: challenge mapping, contributions, claim mapping and subsequent introductory restatement substantially overlap. Compress these without removing scope information.
- `main.tex:143, 264`: “no model of the world has to be believed” repeats a stronger rhetorical version of the precise design-based statement. Keep the formal claim and one plain-language explanation.
- `main.tex:260`: “No monotone invariant is needed” reads like development history; it contributes nothing to the proof.
- `main.tex:432`: the conclusion underplays the proved contribution by summarizing almost exclusively observed violations. State Theorem 1’s guarantee directly under its assumptions, then report the empirical findings.
- `main.tex:493, 399`: explicitly mention the v3 negative results already in Tables 25–26: it is worse than the earlier paced arm at $h=50$ in the scarce family and worse than never switching at $R=12$ on the original family. “Narrows the gap at large headroom” should not become the entire summary.
- `main.tex:435`: “we see a low risk of misuse” is not established by conservative promotion or existing logs. The preceding concrete limitations are more useful.
- Notation: $h$ denotes both headroom and the payback horizon; $W$ denotes both the shield check and comparator wealth. Renaming the payback horizon and comparator wealth would reduce avoidable collisions.

**References**

The supplied bibliography covers the evident conceptual families: conservative learning, safe policy improvement, confidence sequences, delayed feedback, switching costs and active model selection. I would not demand an additional conceptual citation solely from the manuscript. Dataset references are the clear omission: Table 14’s repository identifiers and informal source labels should have precise public citations where records exist. I have not externally verified the bibliographic entries or their characterizations.

Bibliography reviewed: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/refs.bib" purpose="source"}.

**Complete visual assessment**

- **Figure 1, p. 7:** Strongest explanatory visual. Distinct solid/dashed traces, reserve band and deployment bars make the mechanism understandable. Caption and numerical annotations agree. The long embedded legend occupies substantial plot area; move its explanatory prose into the caption. The dotted check’s “evaluated after round $t$” convention deserves a short explicit distinction from the pre-action $W_t$.
- **Figure 2, p. 14:** The stress/original separation is clear and the zero/rare shield outcomes are visible. At final page size, heatmap row labels and numerical annotations are small. Very pale cells make small nonzero rates difficult to distinguish. Increase panel (a)’s width or give it a separate row. Keep the original-regime failures visible.
- **Figure 3, p. 15:** Readable and consistent across budgets; direct labels and open/filled markers work. Other comparators are faint and unidentified individually, reducing the usefulness of the displayed comparison. Label them directly or provide a compact key. “Pay little” is less precise than reporting the stated mean-cost differences. The graphic correctly concerns $q_{99}$, not satisfaction of the full pathwise guarantee.
- **Figure 4, p. 17:** Clear thresholds, shared vertical scale and visible dispersion. The open median markers and faded raw points work well. Caption alignment is good. Explain values $L>1$ and $L<0$, and clarify that the connecting lines join bin summaries rather than a fitted predictive law. This figure appropriately retains unfavorable $L>1$ outcomes.
- **Tables 1–4, pp. 2–9:** Generally readable but prose-heavy. Table 2 duplicates much of the surrounding material. Table 4’s long cells increase the interruption between theorem and proof.
- **Tables 5–12, pp. 12–18:** Values and headings are legible. Table 6’s two-part layout repeats controller names and makes cost/harm comparisons slower. Table 12 needs the count-label correction above. Table 11 is useful and preserves the shield’s unfavorable clean-feedback comparisons.
- **Table 13, pp. 24–25:** The continuation header is good. Dense descriptions and long identifiers make this table small; compact human-readable regime labels with identifiers in a separate column would help.
- **Tables 14–16, pp. 26–28:** Table 14 is especially small after scaling and contains long provenance cells. Split provenance/model information from numerical stream statistics. Tables 15–16 are readable with zoom but cramped at ordinary page scale.
- **Tables 17–27, pp. 29–32:** Numeric alignment is sound. Captions for Tables 19–20 should repeat the critical budget/aggregation definitions rather than relying on Table 18. Internal arm identifiers dominate these tables; a consistent mapping to readable names would help. Table 27 is stranded alone on p. 32 with extensive white space.
- **Layout:** No obvious clipping, overlapping text, broken figures or missing cross-references. Several floats separate connected prose: Theorem 1 starts at the bottom of p. 7, its proof begins after two floats on p. 8, and Table 4 interrupts its conclusion on p. 9. Move that table before the theorem or after its proof. The same issue affects the calibration discussion across pp. 13–15.
- **Consistency:** The manuscript alternates among “Wald with cutoff,” “Wald+cutoff,” `wald_cut`, “full,” `pi1,” “paced” and “v2d.” Standardize reader-facing names. The conspicuous red and green hyperlink rectangles add visual noise throughout; unobtrusive link styling would improve readability.

**Final judgment:** The core contribution warrants serious consideration and the main safety argument appears credible. The paper is close, but the specification gaps, comparator validity statement and lower-bound summaries should be corrected before treating the current version as submission-ready; provenance recovery remains an explicitly open evidence issue.
