# Paper improvement log — F3 TMLR

Run: `2026-11-17_run01`  
Scope: writing and presentation changes under `paper/f3_tmlr/` only. No experiments, data, numerical results, or citations were added or changed.

## Round summary

| Round | Score and verdict | Review scope | Independence / acceptance status |
|---|---|---|---|
| 1 | **6/10 — weak accept; Almost** | Sanitized source and PDF pages 1–21; appendix omitted. | `review_independence: unknown`; `acceptance_status: provisional` (reviewer model identity unavailable). |
| 2 | **6/10 — weak accept; Almost** | Fresh-context review of the full manuscript source and all 32 pages of the then-current PDF, including appendices, tables, figures, and bibliography. No research code, data, registries, or sealed material was opened. | Bias guard used; `review_independence: unknown`; `acceptance_status: provisional` (reviewer model identity unavailable). |
| 3 | **6/10 — weak accept; Almost** | Fresh zero-context review of full source, included tables/figures, bibliography, and all 31 pages of the pre-fix PDF. No code, results, data, prohibited table, or protected resource was opened. | Bias guard used; `review_independence: unknown`; `acceptance_status: provisional` (runtime reviewer identity unavailable). |
| 4 | **7/10 — accept; Almost** | Fresh zero-context review of full manuscript, all included table/figure sources, bibliography, and all 33 pages of the pre-fix PDF. No research code, data, protected confirmation block, sealed group, or excluded table was opened. | Bias guard used; `review_independence: same-family`; `acceptance_status: provisional` (reviewer model identity unavailable). |
| 5 | **7/10 — accept; Almost** | Fresh zero-context review of the full manuscript, included sources, and all 34 pages of the pre-fix PDF, including appendices. No code, data, protected confirmation block, sealed group, or excluded table was opened. | Bias guard used; `review_independence: same-family`; `acceptance_status: provisional`. |
| 6 | **7/10 — weak accept; Almost** | Fresh bias-guarded review of the full manuscript source, 30 direct TeX inputs, bibliography, and all 36 pre-fix PDF pages, including appendices and references. No prior-round material or research artifacts were opened. | `review_independence: same-family`; `acceptance_status: provisional` (runtime reviewer identity not independently verified; not an external acceptance review). |

Round 3 was run as an explicitly requested extension beyond the original two-round loop. The reviewer saw no prior-round context. Its complete response and metadata are in `review-stage/round3.response.md` and `review-stage/round3.meta.json`. The reviewer returned 6/10, Almost; identity was unavailable, so independence and acceptance remain unknown/provisional.

Round 4 was run as the requested continuation. The fresh reviewer had no earlier-round context and reviewed the entire manuscript and PDF. Its full response and request/metadata are in `review-stage/round4.response.md`, `review-stage/round4.request.json`, and `review-stage/round4.meta.json`. The reviewer returned 7/10, Almost, with no critical flaw identified. Reviewer identity was unavailable; the review is classified same-family and acceptance remains provisional.

Round 5 was run with the bias guard enabled and no earlier-round context in the reviewer prompt. The reviewer read the full manuscript, included source files, and all 34 pre-fix PDF pages. The full report and request/metadata are in `review-stage/round5.response.md`, `review-stage/round5.request.json`, and `review-stage/round5.meta.json`. The reviewer returned 7/10 — accept; Almost, with no critical flaw. The requested reviewer was GPT-6-Astra at xhigh; runtime identity is not independently verifiable. Independence is classified same-family and acceptance remains provisional.

Round 6 used a fresh reviewer prompt with bias guard enabled and no earlier-round context. The reviewer read the entire pre-fix source and PDF. The report and request/metadata are in `review-stage/round6.response.md`, `review-stage/round6.request.json`, and `review-stage/round6.meta.json`. The reviewer returned 7/10 — weak accept; Almost. The requested model and effort were GPT-6-Astra and xhigh; runtime identity is not independently verifiable. The review is same-family and acceptance remains provisional, not an external acceptance judgment.

## Fixes applied

### Round 1 fixes retained

- Qualified the first-promotion lower-bound claim by its probability threshold, feedback-blind window, sufficient-horizon condition, and rollback-versus-terminal branch; revised the running example to distinguish affordable rollback from immediate realised harm.
- Reconciled the abstract, claims, figure captions, and conclusion with the existing simulation and real-stream violation counts; retained the paced-arm violations and adverse comparisons.
- Scoped the abstract’s retention result to the evaluated favorable units and clarified that the exposure-ratio result is an observed association, not a causal exclusion.
- Corrected the stop-loss explanation to focus on pending exposure and its stopping rule; preserved the separate rollback-reserve ablation and calibrated-comparator qualifications.
- Tightened observation-model and filtration language, including the dependence restriction on the current query coin; clarified that unobserved losses are bounded rather than exactly observed in hindsight.
- Defined the blind-round variance increment piecewise and clarified the count-budget meaning of `B`; renamed the payback horizon to avoid the headroom notation collision.
- Reworked the simulation comparison table and reader-facing arm labels; moved floats to paragraph boundaries and clarified figure captions and table aggregation descriptions.

### Round 2 fixes

- Replaced the repetitive/defensive introduction structure (challenge map, contribution list, and overlapping claims table) with a concise problem-and-contribution narrative and one consolidated scope/claims table. Removed process narration and repeated assurances.
- Revised the abstract and running example to retain the first-promotion event condition, rollback branch, blind-window limit, and sufficient-horizon qualification.
- Defined the blind branch of the variance update without `1/0`; specified the e-process comparator’s conditional null and release-time filtration, and stated that experimental tapes are not assumed to satisfy it.
- Clarified that `B` is a query-count cap and `c_q` accounts for monetary query cost. The complete empirical objective `J` is still not fully documented; see open items.
- Surfaced the missing model/training-window provenance for nine legacy streams, and missing task/source information for three, in the main real-stream description.
- Stated the negative v3 comparisons in the main text, including v3 at `R=12` on original regimes; preserved unfavorable real-stream results, including the appliances comparison where the shield loses to never switching.
- Removed the unsupported low-misuse-risk claim; clarified exposure-ratio criteria, adverse-delay scope, and captions for the mechanism, regime-map, and cost-tail figures.
- Grouped appendix floats with their protocol/results discussion and revised generated regime labels and table captions for readability. The three duplicate appendix tables intentionally removed by the author between rounds remain removed.

### Round 3 fixes

- Qualified the abstract's reserve lower bound by the first-promotion probability event, rollback-branch condition, sufficient horizon, feedback-blind window, and all-harm/full-sampling attainment; retained the plain-language abstract rewrite.
- Preserved the author's edits defining the empirical objective `J`, its label and switching charges, optional compute fee, and exclusion of shadow-model serving cost. The existing writing gap in `J` is resolved in the manuscript.
- Recast calibration claims as results for the tested settings against a nominal per-regime target; replaced class-wide CUSUM impossibility language with a statement about tested thresholds. The unspecified selection rule and search details remain explicit limitations.
- Clarified that the real-stream disagreement rate in the exposure map is the stream-wide fraction used as a proxy for deployed exposure. Stated that the 47-regime family, v3 grid/selection rule, and exposure-regression aggregation are not fully specified in the paper.
- Added the registered C4 cost tolerance to the confirmation-table caption; corrected pooled real-stream captions to identify equal-stream cost summaries and raw run counts at both comparator thresholds.
- Reframed the discounted Wald statistic as a nominal heuristic score, clarified that observed gains can free budget while no future gain is assumed, and narrowed the small-headroom statement to evaluated settings.

### Round 4 fixes

- Reconciled the real-stream provenance table with the seven model pairs and Criteo task/source already documented in the appendix. Kept `openml_ldpa` and `uci_occupancy` provenance unknown, and described the SHA-256 match as file identity with the linked script serving as construction documentation.
- Replaced the obsolete conclusion sentence that understated Appendix C documentation with a pointer to its 47-regime family, v3 candidate grid and selection rule, exposure-analysis quantities, and OLS specification. Preserved the actual stream reuse, feedback, comparator, outcome, second-look, and correlational limitations.
- Added operational definitions for calibrated stop-loss and CUSUM variants, including inherited acquisition/promotion, stopping statistics and inequalities, fee treatment, permanent cumulative-harm safeguard, and repromotion behavior. Distinguished empirical per-regime point-estimate calibration from the shield theorem.
- Tightened the h=6 allowance, Proposition 2 regime-map interpretation, and reserve-necessity wording to retain their formal conditions. Clarified signed cost differences, the simulation-table aggregation columns, displayed rounded zeros, regression covariate, and table references; shortened repeated prose and softened the subsection heading.
- Improved float order by moving the calibration table into its subsection and the real-stream summary after its opening paragraph. Split provenance from numeric stream summaries, enlarged the calibration table by removing wholesale scaling, and kept proposition statements together. At that round, the final appendix comparison table remained alone on the last page; Round 5 grouped the comparison tables, though sparse appendix float pages remained.
- Retained the author’s post-round-3 edits to the abstract, Section 3 labels, objective `J`, compute fee, and conservative-bandit analogy. No experimental values or citations were added or changed.

### Round 5 fixes

- Aligned the abstract, formal definition, theorem and proof setup: quantify over fixed loss/disagreement sequences and admissible nonanticipating delay rules, without conditioning on future realized delays; specify that a delay cannot depend on the current query coin.
- Clarified the high-fee override (`k=30`) and the interpretation of the CUSUM worst-regime rate at `R=20`; identified the other worst cases as adverse dropout and scoped headrooms to the default regime.
- Split the Proposition 2 table checks into first-spell identity and the delay condition for feedback-blind rollback tightness. Kept the horizon qualification and all displayed values.
- Consolidated comparator calibration documentation, including the per-regime empirical threshold, tested grids, selection directions, fallback and headroom transfer. Kept the 47-regime scarce family, v3 grid/selection rule, exposure quantities/OLS specification, lemma domains and Proposition 3 filtration documentation.
- Recorded in this log that the seven atlas model descriptions are documented by `scripts/promising_directions/b3_real_data.py` (committed in `475bf474`); this script path was not added to the paper.
- Added the existing simulation comparison to the introduction; clarified label-exhaustion behavior for full sampling, the meaning of above-never regime-map values, and that the v3 real-stream evaluation is a second look. Removed progress-report/repetitive wording and retained all adverse comparisons and limitations.
- Moved the two proposition tables next to their proofs, clarified their captions, improved float order, and replaced “original 30 regimes” with “registered 30 regimes.” The final-page comparison tables now share a page. Some appendix float pages and dense/small tables remain; Figure 2 label polish still depends on PaperBanana, unavailable in this environment.
- No citations, numerical results, or experiments were added or changed. The author’s uncommitted edits to the abstract, Section 3 labels, `J`, compute fee and stop-loss analogy were preserved.

### Round 6 fixes

- Shortened the abstract’s lower-bound explanation while retaining the first-promotion probability condition, rollback-branch condition, sufficient horizon, and feedback-blind all-harm scope.
- Clarified query ownership on promotion rounds, distinguished the common deployment acceptance inequality from the settlement-specific construction of its accounting check, and pointed the algorithm caption to the settlement appendix.
- Clarified that the lower-bound count includes disagreements from promotion through the horizon; aligned the Proposition 2 table caption and column labels with the identity and feedback-blind rollback conditions.
- Replaced repeated registered-run values with `tables/numbers.tex` macros, including pooled simulation costs and seed/regime counts. The prose now states that the `R=20` costs are pooled over the simulated regimes.
- Replaced code-like arm identifiers with reader-facing labels in included appendix result tables; retained identifiers in the frozen-arm specification table. Moved the exposure-regression and v3 scarce-family tables beside their protocol descriptions. The compiled PDF is 35 pages, one page shorter than the prior 36-page draft.
- No citations, experiments, or numerical results were added. Negative results, data limitations, and the author’s uncommitted edits remain.

## Round 4 review and build record

The full fresh review scored **7/10 — accept; Almost**. It found no critical flaw. Its complete report is retained in `review-stage/round4.response.md`. The pre-fix review covered 33 PDF pages; the post-fix PDF has 34 pages. The reviewer did not inspect code, data, protected confirmation runs, the sealed group, or the excluded `table_real48.tex`.

The requested `build.sh` was not run: it invokes `make_tables.py`, which reads cached loss/result inputs, including protected confirmation artifacts. To respect the no-opening/no-running constraint, the existing generated tables were left intact and the manuscript was rebuilt with `latexmk -pdf -file-line-error -interaction=nonstopmode -halt-on-error main.tex`. The compile succeeded; the final log has no undefined or multiply-defined references/citations and no overfull boxes. No experiment, result regeneration, or tests were run. The final rendered file is `main_round4.pdf`.

### Round 5 review and build record

The fresh review scored **7/10 — accept; Almost**, with no critical weakness. It reviewed the full manuscript and all 34 pre-fix PDF pages; its response and metadata are retained under `review-stage/round5.*`. It did not inspect research code or data, the protected confirmation block, the sealed group, or `table_real48.tex`.

`build.sh` was not run because it invokes `make_tables.py`, which reads cached result inputs including the protected confirmation summary. To honor the explicit no-open/no-run restriction, the existing generated table sources were preserved. The PDF was rebuilt with `latexmk -pdf -file-line-error -interaction=nonstopmode -halt-on-error main.tex`; compilation succeeded and the resulting PDF has 36 pages. The log has no undefined references/citations or multiply defined labels, and no overfull boxes were reported. A visual spot-check confirmed that the final comparison tables no longer sit alone on the last page; some sparse appendix float pages and dense tables remain. No experiments or tests were run.

## Round 5 open items

- Figure 2’s regime heatmap labels and method abbreviations remain dense. The repository requires PaperBanana for research visual edits; it was unavailable in this active environment, so the figure was not altered or replaced.
- The calibration/evaluation seed-block registry mapping remains to be verified from permissible public supplement/registry records. The seven atlas model descriptions are documented in the script path recorded above. No protected confirmation block was opened.
- Provenance for `openml_ldpa` and `uci_occupancy`, and machine identity absent from the run ledger, remain unknown.
- The Proposition 3 and Proposition 4 tables are now placed beside their proof discussions. Some appendix tables still occupy sparse float pages; the Proposition 3 table remains on a relatively sparse page after its proof.
- Full regeneration through `build.sh` remains pending a workflow that does not open or reprocess protected confirmation data. The PDF compile verifies the current generated table sources only.

## Round 6 review and build record

The fresh review scored **7/10 — weak accept; Almost**, with seven focused writing and layout recommendations and no request for new evidence. It read `main.tex`, all 30 directly included TeX files, `refs.bib`, and all 36 pages of the pre-fix PDF. The bias guard was enabled; no prior-round reports, logs, state, code, configuration, results, registries, or datasets were opened. It did not access the protected confirmation block, `civic_records_sealed`, or `table_real48.tex`, and made no edits. The complete review is in `review-stage/round6.response.md`; request and metadata are in `review-stage/round6.request.json` and `review-stage/round6.meta.json`. The reviewer is same-family; the recommendation is provisional and is not an external acceptance review.

The specified external skill path `/Users/nigelli/Desktop/shift-codex-paper4/.agents/skills/auto-paper-improvement-loop/SKILL.md` was unavailable in this environment, and its shared-references directory was also absent. Round conventions were recorded from this run's existing review artifacts. The current log had no separate `Round 4 open items` heading or Round 3 bullets beneath one; the Round 3 history remains under `Round 3 fixes`.

The requested `./build.sh` was not run because it invokes `make_tables.py`, which reads `confirm_summary.json` from the protected confirmation results. Instead, the manuscript was rebuilt from the existing generated table sources with `cd paper/f3_tmlr && latexmk -pdf -file-line-error -interaction=nonstopmode -halt-on-error main.tex`. Compilation succeeded; `main.pdf` has 35 pages (down from 36), and `main.log` contains no undefined references or citations, duplicate labels, or overfull boxes. The final PDF is saved as `main_round6.pdf`. A visual check of affected theory and appendix pages found no clipped text; the crowded appendix result tables remain readable at page scale with zoom.

## Round 6 open items

- Figure 2's heatmap labels and annotations remain dense. PaperBanana was not available in the active tool set, so the research visual was not edited or replaced with another generator.
- The seed-block registry mapping still needs verification against permissible registry records; the protected confirmation block was not opened or run.
- Provenance for `openml_ldpa` and `uci_occupancy` and the missing machine identity in the run ledger remain unknown.
- Several appendix tables remain dense, and some float pages retain excess whitespace. The final PDF is one page shorter, and the last comparison table no longer sits alone on the final page.
- Full `build.sh` regeneration remains pending a workflow that does not read or regenerate from protected confirmation results.

The objective-definition item from Round 2 was resolved by the author's intervening edits: `J` now has an explicit deployed-loss, label-fee and switching-fee equation, with optional compute and shadow serving cost addressed in prose. No new evidence was requested or generated through experiments. Existing unfavorable results and limitations remain in the manuscript.

## Build record

- Command: `cd paper/f3_tmlr && ./build.sh`
- Result: successful; final `main.pdf` is 31 pages.
- Reference check: no undefined citations/references or multiply-defined labels in `main.log` after the final build.
- LaTeX reports some underfull boxes in dense tables and page layouts; no build-stopping errors were reported.
- Final PDF snapshot: `main_round2.pdf`.

### Round 3 build record

- Command: `cd paper/f3_tmlr && ./build.sh`
- Result: successful; `main.pdf` is 31 pages and was saved as `main_round3.pdf`.
- Reference check: no undefined citations/references or multiply-defined labels in `main.log`; no overfull boxes were reported. Dense tables and page layouts still produce underfull-box warnings.
- Visual check: rendered and inspected a contact sheet of all 31 rebuilt pages. No clipping, broken glyphs, or missing figures were visible; appendix table density and small figure labels remain open.

## Full reviewer reports

<details>
<summary>Round 3 — 6/10, Almost (full manuscript and PDF)</summary>

Full raw response: [`review-stage/round3.response.md`](review-stage/round3.response.md). The report identifies no critical issue; its main writing concerns are lower-bound scope, calibration selection details, the 47-regime/exposure analysis specification, analytical-filtration clarity, pooled-table captions, and appendix-table/figure legibility. Its page-by-page assessment and all actionable findings are preserved in the linked response.

</details>

<details>
<summary>Round 1 — 6/10, Almost (partial manuscript scope)</summary>

**Overall score: 6/10 — weak accept. Submission readiness: Almost.**

The paper proposes a controller that limits cumulative excess loss against never switching, including switching fees, under exogenous paired losses and delayed, missing, selectively queried feedback. Its strongest contribution is the combination of a design-based harm bound with explicit pending-feedback and rollback reserves; the supplied results show useful gains over never switching while documenting the cost of this protection.

I reviewed the supplied source, its included tables, and the corrected PDF’s pages 1–21. I did not inspect the excluded protocol material. Runtime model and reasoning-effort metadata: **unknown**.

### Ranked strengths

1. **A precise, operational safety target.** The distinction between a future payback certificate and a bound on realised intervention harm is useful. Including switching fees and comparing against a frozen incumbent makes the target interpretable.
2. **A transparent accounting argument.** Theorem 1’s decomposition into observed, pending, blind, and sampling-error terms is understandable. Full sampling gives a particularly strong and clean deterministic guarantee.
3. **Evidence includes meaningful benefits and costs.** At $R=20$, full sampling reduces mean simulation cost from 71.53 to 69.43, while costing 0.96 more than tuned Wald. The paper also reports the deterioration on harmful streams relative to never switching. These unfavorable comparisons should remain.
4. **The experiments isolate relevant failure modes.** Original/stress splits, reserve ablations, calibrated comparators, and real-loss streams with controlled feedback corruption each have an identifiable argumentative purpose.
5. **Useful explanation and scope disclosure.** The running example, explicit shared-outcome assumption, discussion of policy-seed dependence, and separation of simulated latency from authentic label-release times materially improve interpretability.

### Critical weaknesses

**No demonstrated failure of the basic full-sampling guarantee under a fixed exogenous tape.** However, the following major issues should be corrected before submission. Several affect headline claims rather than optional wording.

### Major weaknesses — definite required fixes

**1. The lower-bound and attainment language exceeds Proposition 2.** Proposition 2 includes three qualifications that repeatedly disappear in the surrounding text: the first promotion, an event with probability greater than $\delta$, and the alternative $R\ge \min(2k+e,k+n)$. Consequently, “no valid controller” can hold more than $R-2k$ exposed rounds and the claim of exactly $\lfloor R-2k\rfloor$ rounds on every all-harm tape are too broad. A short horizon can let the ride-out branch remain deployed beyond this threshold.

**Fix:** State exact attainment for an initially proposed first promotion, sufficient remaining horizon, available full sampling, and the setting where the rollback branch of the lower bound applies. Retain the ride-out alternative. Replace claims of general optimality with tightness in the stated feedback-blind setting. The assertion that a valid controller “must cycle” when $x>1$ should describe the proposed mechanism or empirical prediction, rather than all valid controllers.

**2. Several summaries incorrectly erase the paced arms’ violations.** Table 5 reports one violation in each of two paced arms, and Table 6 shows paced maximum harm 22 at $R=20$. Nevertheless, the claims table says “empirical zero violations in the registered simulation”; the conclusion says “The budget held in every registered and real run”; and Figure 2’s opening caption says the shield does not break the budget, before its later exception. A probabilistic guarantee permits these outcomes.

**Fix:** Consistently state zero observed violations for deterministic arms, one per 30,000 runs for each paced simulation arm, and zero observed real-stream violations. Separate “satisfies the probabilistic guarantee” from “never exceeded $R$ in the experiment.”

**3. The abstract turns a conditional median result into a universal retention claim.** The 88–96% figure comes from medians for paced variants in selected units where Wald gains at least 10% over never switching. It does not hold for all shield variants or every unit with $x<0.5$. Table 12’s full-sampling median losses of improvement are 0.40 and 0.33, corresponding to 60% and 67% retention.

**Fix:** Say directly that **paced variants retain a median 88–96% of Wald’s gain in the evaluated favorable units with $x<0.5$**. Apply the same qualification to Figure 4. Describe the exposure ratio as a prediction motivated by the lower bound and supported by the observed association. Replace “the effect is not explained by label use” with “the positive association remains after controlling for the stated label-use variable”; the regression does not establish the stronger causal exclusion.

**4. The stop-loss failure explanation contradicts its own definition.** The stop-loss threshold is $R-k$, explicitly reserving the rollback fee. Section 5.1 and Figure 1 nevertheless say the rollback fee is invisible to it. The plotted overshoot demonstrates the consequence of omitted pending harm; it does not demonstrate that this comparator lacks a rollback reserve. The calibrated-comparator conclusions also sometimes sound universal.

**Fix:** Attribute the stop-loss failure to unresolved exposure and its stopping rule. Keep the separate no-rollback-reserve ablation as evidence for that component. Scope calibration conclusions to the evaluated families and parameter choices, preserving all reported violations, deployment rates, and costs.

**5. The observation-model and filtration statements need tighter mathematical wording.** The abstract promises validity for “every delay or missing-label mechanism,” while O3 excludes dependence on the current query coin. Appendix A.2 conditions on a tape while also allowing its delay mechanism to react to past coins. Conditioning on the entire realised tape can reveal coin information; fixing a nonanticipating mechanism is different from conditioning on its future realised outputs. This is a presentation gap in the supplied argument, not a demonstrated counterexample to the intended result.

**Fix:** Define the analysis filtration explicitly. Distinguish a fixed exogenous loss/flag sequence and fixed nonanticipating delay rule from a realised delay sequence. State predictability of the action and propensity and the conditional Bernoulli law in that filtration. Use “arbitrary delays satisfying O3” or equivalent in the abstract and introductory claims. Also replace the introduction’s statement that realised harm is “observable in hindsight from sampled labels.” With missing or unqueried labels, its exact realised value generally remains unobserved; the method bounds it.

**6. Several definitions prevent fully self-contained reading.** The shield formula permits a blind choice $\pi=0$, but its width argument still contains $1/\pi-1$. Table 12 labels 32 and 10 as “units,” while the text defines 502 units and Figure 4 gives hundreds of plotted observations. The main text does not clearly specify uncertainty calculations for principal cost differences. “Budget $B$” is introduced alongside a label price, then used as a number of labels; its units should be explicit.

**Fix:** Define the variance increment piecewise, with zero increment for blind rounds. Rename Table 12’s count column to identify the grouping unit and distinguish it from the number of observations. State the existing aggregation and interval method briefly. Define $B$ unambiguously. These requests require clarification of existing analysis, not new experiments.

**7. The narrative is too repetitive and defensive for the strength of the supported result.** The opening has a useful problem–idea connection, but the abstract carries too many comparator statistics and qualifications. The introduction then repeats the contribution through four challenges, a challenge table, contributions, and a claims table. Later passages narrate the research process rather than advancing the argument. Examples include “A natural objection is…”, “The settings are not chosen for this study,” repeated assurances that no settings were tuned, “They are favourable to the shield by construction,” “All six … tests are supported,” “We found no prior work … in our search,” and repeated statements that no model of the world must be believed.

**Fix:** Lead with the supported guarantee and empirical benefit. Consolidate introductory maps. Describe stress regimes as isolating the missing-feedback mechanism, then give the original/stress split. Introduce calibration through its scientific question. Put procedural chronology and implementation provenance in their dedicated location. Preserve limitations and unfavorable numbers. The conclusion should state deterministic and probabilistic findings accurately and end with the contribution.

### Minor weaknesses

- Reuse of $h$ for both payback horizon and budget headroom is avoidable.
- Calling $1/\pi$ a “cost” is confusing alongside monetary label cost $c_q$; it is an accounting reserve.
- Specify positive grid values and weights in Lemma 1.
- Replace machine identifiers such as `wald_cut`, `f3_pi1_R20`, and `dropout_adverse` with readable labels in main-text tables.
- “Right more often than not” should retain Proposition 3’s conditional positive-drift assumption.
- The broader-impact conclusion that misuse risk is low does not follow merely from conservative promotion and use of logged losses; remove or justify that inference.

### Visual review

**Required: Table 6 is too small to read comfortably.** This is the simulation comparison at $R=20$, sourced from `tables/tab_sim.tex` and inserted at source lines 323–325. Its nine unwrapped columns include long controller names, a worst-regime rate with Wilson interval, and a worst-regime name. The enclosing `\scriptsize` followed by `\resizebox{\linewidth}{!}{...}` scales already small type down further. Split cost and harm results into two aligned panels or restructure at readable fixed font size, preserving every value. Table 10 has a milder version.

**Required: repair float interruptions.** On pages 6–7, Figure 1 and Table 3 interrupt the running-example sentence. The discussion beginning on page 16 is also interrupted by Figure 4 and Table 12 on page 17. Move floats to paragraph boundaries.

**Required: correct figure captions.** Figures 1, 2, and 4 need the scope corrections above. Figure 3’s “Only the shield arms” opening is inconsistent with the plotted never-switch point; distinguish active controllers or describe the plotted result without that exclusivity claim.

**Optional polish:** Enlarge Figure 2’s regime labels and simplify dense annotations; use consistent table typography; remove red/green hyperlink boxes if compatible with style; shorten captions by moving implementation provenance into a reproducibility note.

The corrected PDF is in numeric order. I observed no major clipping, missing figures, or overlapping mathematical content in pages 1–21.

### References and remaining evidence limits

I verified the relevant entries exist in the supplied `refs.bib`; I do not identify an additional missing citation on these restricted inputs. Conservative bandits, off-policy confidence sequences, delayed-outcome design-based inference, and Prudent-Banker are already represented; the more useful improvement is to bring the closest comparison into the introduction and articulate the precise distinction earlier.

The breadth of comparator coverage and generalisation to authentic deployment latency remain limitations of the existing evidence. The supplied material supports the evaluated comparator families and real-loss replays, not a universal superiority claim. These are open evidence questions; I am not proposing new experiments for this writing revision.

**Verdict: Almost.** The core result and empirical benefit are worth presenting. Submission readiness mainly requires precise scope, reconciliation of summaries with the existing numbers, explicit definitions, and readable tables—not stronger promotional language or additional experiments.


</details>

<details>
<summary>Round 2 — 6/10, Almost (full manuscript and PDF)</summary>

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


</details>
