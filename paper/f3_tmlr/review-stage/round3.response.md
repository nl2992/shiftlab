**Overall score: 6/10 — weak accept. Verdict: Almost.**

The paper develops a useful, clearly motivated safety constraint for reversible model deployment and a shield whose accounting combines sampled feedback, pending exposure, and rollback fees. The central upper-bound argument appears sound within the intended exogenous-loss setting, and the experiments report meaningful unfavorable outcomes. The manuscript still needs writing revisions to align its strongest summaries with the formal results and make the calibration and exposure-ratio analyses self-contained.

Reviewed manuscript: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.pdf" purpose="source"}

Source locations below refer to: :codex-file-citation{path="/Users/nigelli/Desktop/ICML/shift-paper3-f3/paper/f3_tmlr/main.tex" purpose="source"}

**Ranked strengths**

1. **A precise and practically interpretable target.** The paper distinguishes cumulative intervention harm from model quality, prediction error, and future payback. Including both switching fees and the comparison against never switching makes the guarantee understandable.

2. **A coherent safety argument.** The decomposition into blind, released, pending, and sampling-error terms is transparent. The rollback reserve closes an important operational gap, and the ride-out branch correctly acknowledges the finite-horizon alternative. The first-spell lower bound complements the upper bound without pretending to establish regret optimality in the body.

3. **Unusually useful adverse evidence.** The manuscript reports the two paced-arm violations, higher shield cost relative to Wald, substantial utility loss on some real streams, failed calibrated comparators, and the v3 failures at small budgets and at scarce-family headroom 50. These results should remain prominent.

4. **Reasonable separation of evidence types.** The registered simulation, previously exposed real streams, later v3 development, and correlational regime analysis are distinguished. The limitations of cached losses and simulated release times are explicit.

5. **Good conceptual figures.** Figure 1 explains the mechanism effectively. Figures 2–4 communicate safety, utility cost, and the empirical exposure relationship without concealing the less favorable outcomes.

**Ranked weaknesses and required writing fixes**

**CRITICAL: None identified.** I did not find a demonstrated counterexample to the main shield theorem under the intended assumptions.

**MAJOR 1 — The abstract overstates the lower bound.**

- **Location:** Abstract, p. 1; `main.tex:36`. Compare Proposition 2, pp. 8–9, and Appendix A.3, p. 21.
- The assertion that “no valid controller” can hold a first promotion for more than \(R-2k\) disagreements omits two essential conditions: the first-promotion event must have probability greater than \(\delta\), and the rollback branch must bind rather than the finite-horizon \(k+n\) alternative.
- A controller can spend its allowed failure probability on a risky deployment, so an unconditional impossibility statement is false when \(\delta>0\). The abstract’s “exactly that many” also needs the integer floor and the stated all-harm/full-sampling conditions.
- **Fix:** Replace this with, for example: “For first-promotion events of probability greater than \(\delta\), a matching lower bound requires reserves for unseen exposure and rollback when enough horizon remains; on an all-harm tape, the full-sampling shield attains the resulting \(\lfloor R-2k\rfloor\) limit.”
- Keep the explicit finite-horizon qualification already present in the body.

**MAJOR 2 — The calibrated-comparator standard is not specified consistently.**

- **Locations:** Abstract, p. 1; `5.2, p. 14, `main.tex:308–314`; Table 9, p. 15; Appendix C, pp. 22–23, `main.tex:433`.
- `5.2 calls calibration “the shield’s own standard” and describes a per-regime violation rate of at most .05. Appendix C defines the shield’s registered C2 criterion as a **Wilson upper confidence bound** of at most .05. A point estimate and an upper confidence bound are different selection rules, especially with 200 calibration runs.
- The tested calibration grids, tie-breaking, fallback when no threshold passes, and precise headroom-transfer rule are absent. Consequently, “CUSUM rollback cannot meet the standard” is stronger than the reader can establish from the documented finite search.
- **Fix:** State exactly whether selection used the empirical rate or a confidence bound. If it used the empirical rate, replace “same standard” with “same nominal .05 threshold.” Give the tested margins and thresholds, selected values, fallback rule, and transfer formula in a compact appendix table. Change the impossibility-sounding sentence to “No tested CUSUM rollback threshold met the criterion at \(R=12\) or \(R=20\).”
- Preserve the fresh-seed failures and the clean-stream utility advantage of the calibrated CUSUM comparator.

**MAJOR 3 — The headline exposure-ratio analysis is not sufficiently self-contained.**

- **Locations:** “What the bound predicts,” p. 9; `5.4, pp. 15–17; Appendix C, p. 23; Tables 23–24, p. 30; `main.tex:243`, `340–348`, `441–445`, `534`.
- The paper describes the original 30 regimes thoroughly, but not the construction of the **47-regime scarce family** used for v3 selection and the central regime-map analysis. Naming the family and giving \(T,B,k\) does not specify its loss paths, disagreement rates, delays, or other variations.
- The empirical definitions of \(r\), \(d\), and “labels per exposed round” are unclear. In `4, \(r\) is the disagreement rate **while deployed**; Table 15 describes a whole-stream disagreement fraction. Those quantities need not coincide under adaptive deployment.
- Table 24 provides coefficients without defining the exact regressor, weighting, or fitted model beyond its shorthand title.
- **Fix:** Add the scarce-family construction or a compact parameter table, and define the analysis quantities explicitly—including their aggregation across episodes/seeds and whether \(r\) depends on the evaluated arm. State the OLS formula and weighting. Give the numbers of analysis units in each exposure bin. Document the v3 selection objective and exact frozen mixture grid.
- This is a reporting requirement using existing records, not a request to run the analysis again.

**MAJOR 4 — Clarify the analytical filtration and the scope of adaptive delays.**

- **Locations:** Observation model and Definition 1, p. 3; Lemma 1, p. 4; Proposition 3, p. 9; Appendix A.2 and A.4, pp. 21–22.
- O3 permits delays to depend on past query coins, but a “tape” is also defined as including delays, and the guarantee is phrased as conditioning on every tape while randomizing only those same coins. The proof more appropriately fixes the loss/flag sequence and a nonanticipating **delay rule**.
- The proof calls \(\chi_s\) predictable after fixing the loss sequence, whereas the earlier \(\mathcal F_{s-}\) is the controller’s observed information. The distinction between observed and analytical information should be explicit.
- Proposition 3’s “past” must include the previously realized gains needed for its supermartingale argument; a conditional mean assumption only given released controller feedback would not automatically provide that argument.
- **Fix:** Define an analytical filtration separately, fixing the exogenous loss/flag sequence and any external delay randomness, with the delay rule adapted to past coins. State the theorem uniformly over these objects. Define the filtration in Proposition 3 explicitly. This would make the intended proof precise without changing its construction.

**MINOR 1 — Correct misleading appendix table captions.**

- **Locations:** Tables 20–21, pp. 29–30; `main.tex:529–530`.
- Both captions say “per stream,” but the rows are pooled controller summaries. They also describe only \(R=24\) comparator exceedances although the tables contain \(R=60\) counts.
- **Fix:** Say “pooled over 14 streams,” specify the weighting for cost averages, and describe both comparator thresholds. Distinguish equal-stream cost averages from raw run counts.

**MINOR 2 — Make Table 4’s supported verdicts interpretable on their own.**

- **Location:** Table 4, p. 11.
- C4 reports higher cost than Wald, \(+0.96\), followed by “supported,” without stating the registered 3% tolerance in the table.
- **Fix:** Include the actual C4 acceptance criterion and identify the shield variant. The numerical adverse result should remain unchanged.

**MINOR 3 — Avoid calling the heuristic Wald score a valid confidence bound.**

- **Locations:** `3, p. 4; Appendix E, p. 27.
- The manuscript calls the discounted Wald quantity a “lower confidence bound” and the resulting gain “lower-bounded,” although its validity is not established under dependence and informative release.
- **Fix:** Use “nominal Wald lower score” or explicitly say the interval is heuristic here. The careful qualification already supplied for the e-process gate is a good model.

**MINOR 4 — Tighten two statements that understate or confuse the guarantee.**

- **Locations:** `2, p. 2, `main.tex:83`; broader impact statement, p. 19, `main.tex:387`.
- “The guarantee never relies on [gains]” is misleading: banked observed gains do free budget. It does not rely on an assumption of **future** gains.
- “Systematically biased labels” could be read as excluding outcome-dependent selection or missingness, which the paper explicitly allows. “Average-loss budget” is also inaccurate for a cumulative pathwise budget.
- **Fix:** Say “requires no assumption that future gains will occur”; distinguish incorrect or biased recorded label values from informative missingness; use “cumulative population-level loss budget.”

**MINOR 5 — State elementary mathematical domains.**

- **Locations:** Lemma 1, p. 4; Theorem 1, p. 8; Appendix B, p. 22.
- Specify \(\Lambda\subset(0,\infty)\), positive mixture weights, \(\pi_{\min}\in(0,1]\), and the level domain, treating \(\delta=0\) separately for deterministic monitoring. Include Assumption (L) when interpreting the theorem as actual model excess loss.
- In the settlement description, distinguish a round assigned a sampling propensity below one from a round actually queried.

**MINOR 6 — Correct Figure 3’s caption and preserve its diagnostic status.**

- **Location:** Figure 3, p. 13.
- The list of open markers omits the no-rollback ablation, which also has \(q_{99}>R\).
- **Fix:** Include all three ablations. Add that the 99th percentile is a utility/tail diagnostic, not a substitute for the time-uniform violation guarantee.

**MINOR 7 — Several broad phrases need local qualification.**

- **Locations:** Table 3, p. 7; `5.3, p. 14; `5.4, p. 15.
- “No help at small \(h\)” and “a promotion holds for … 6 exposed rounds” sound universal. Beneficial returned labels can extend a hold, and the small-headroom empirical statements concern evaluated settings.
- **Fix:** Use “did not help at the evaluated small headrooms” and “permits six exposed rounds before feedback or banked gains provide relief.”

**References**

The bibliography covers the main neighboring areas: conservative bandits, safe policy improvement, confidence sequences, delayed feedback, switching costs, and active model selection. I do not identify a clearly indispensable missing methodological reference from this manuscript-only review.

The documented datasets would benefit from proper dataset/repository citations and version identifiers instead of only UCI/OpenML identifiers or mirror names. I did not browse or independently verify bibliographic metadata or the descriptions of recent cited work.

**Evidence that remains open, not a prerequisite for writing revision**

- Comparative utility against native implementations of stronger safety-oriented methods remains unestablished; the present comparator claims should remain confined to the tested adapters and heuristics.
- Nine cached streams do not establish identifiable end-to-end model comparisons, and simulated delays do not establish performance under authentic label-release processes.
- The exposure-ratio result remains a selected-unit association, not a causal explanation or an optimality law.
- No result establishes validity for interventions that change outcomes or for biased recorded outcomes.
- The theorem supplies safety; the empirical studies supply utility evidence in their stated settings. Neither establishes generally favorable utility.

**Page-specific visual review**

| Page | Visual assessment |
|---|---|
| 1 | Clear title and readable abstract. Abstract is long but not crowded. |
| 2 | Table 1 is readable; narrow cells produce somewhat awkward wrapping. |
| 3 | Readable, but Proposition 1 begins at the foot of the page and is split immediately. Move the proposition together if possible. |
| 4 | Equations are legible. The shield definition continues onto the next page before its central check; keeping those together would help. |
| 5 | Dense prose remains readable. The running example is useful, though long. |
| 6 | Figure 1 is clear and visually explanatory; no clipping. Table 2 is legible. |
| 7 | Algorithm 1 and Table 3 are readable. Large intervening whitespace and awkward guarantee-column spacing can be reduced. |
| 8 | Proofs are well separated and legible. Proposition 2’s interpretation continues on the next page. |
| 9 | Readable mathematics and explanatory text; no visual defects. |
| 10 | Readable experimental setup. Large paragraph gaps make the page longer than necessary. |
| 11 | Table 4 is readable. Table 5’s repeated controller column wraps shield labels awkwardly across lines. |
| 12 | Figure 2 is sharp, but heatmap row labels and cell annotations are very small at normal page scale. Enlarge panel (a) or give it more space. |
| 13 | Figure 3 is clear. Table 6 is readable; replace raw arm identifiers with reader-facing names where practical. |
| 14 | Table 7 and body text are clear. The harmful-stream paragraph breaks across pages. |
| 15 | Table 8 is readable; Table 9 is substantially smaller and would benefit from more vertical space or fewer columns. |
| 16 | Table 10 is unusually enlarged relative to nearby tables. Figure 4 is clear, with readable axes and an effective \(L=0/1\) interpretation. |
| 17 | Major whitespace: a single short table occupies an otherwise nearly empty page. Move Table 11 beside its discussion and avoid a float-only page. |
| 18 | Related work is readable. Citation-link boxes are visually noisy but not obstructive. |
| 19 | Clear limitations and broader impact sections; bibliography transition is acceptable. |
| 20 | References are readable, with no visible clipping or malformed entries. |
| 21 | Appendix proofs are readable; A.4 starts very near the bottom and immediately splits. |
| 22 | Settlement equation is readable. The exact-coin lemma is dense but fits. |
| 23 | Long protocol identifier creates visibly stretched spacing in the real-stream paragraph. Table 12 is readable but compact. |
| 24 | Table 13 is small despite ample available width. Simulator explanation is clear. |
| 25 | Table 14 is too small for comfortable normal-scale reading. Split it across pages at a larger font; repeated headers are already available through `longtable`. |
| 26 | Table 15 is particularly small. Separate provenance/model descriptions from numeric summaries to improve legibility. |
| 27 | Comparator descriptions are readable and well organized. Reproducibility begins with only a few lines before a page break. |
| 28 | Tables 16–17 have small text and awkward identifier wrapping. Their content merits a larger font. |
| 29 | Table 18 is readable. Tables 19–20 are much smaller; expand or split columns. Correct Table 20’s pooled/per-stream caption. |
| 30 | Tables 21–23 are compact but sharp. Correct Table 21’s caption. Table 24 is readable but lacks methodological detail in its caption. |
| 31 | Tables 25–26 are readable. Substantial whitespace could be reallocated to the more crowded preceding tables. |

**Scope completed:** Yes. I read the complete LaTeX manuscript, bibliography, math-command file, every table source included by the manuscript, all four included figure wrappers and exported figures, and visually inspected all **31 PDF pages**, including the appendices. I did not inspect prior reviews, logs, Git history, implementation code, experiment outputs, data, the prohibited table, or either protected resource, and I ran no research code or experiments.
