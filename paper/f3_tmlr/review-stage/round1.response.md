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
