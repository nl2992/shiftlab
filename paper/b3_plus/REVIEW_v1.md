# Pre-submission review: `main.tex` draft v1 (2026-11-02)

Paradigm: STEM / technical. Venue: ICML main track; topic and contribution type fit.
Reviewed against `B3_PLUS_RESULTS.md` and `B3_PLUS_FIVE_CASE_STUDIES.md`.

## Summary
- **CRITICAL: 3**
- **MAJOR: 5**
- **MINOR: 3**

Top three fixes first: (1) add citations and a bibliography, (2) include the two figures that
exist, (3) add the ablation table that attributes the effect to the proposed mechanism.

## Dimension 1: Macro logic

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | Related Work names its two closest works only in prose: "Contextual active model selection (CAMS) queries on a disagreement score..." and "Active, anytime-valid risk-controlling prediction sets...". **There is not one `\cite` in the paper and no bibliography.** | CRITICAL | Add a `.bib` with arXiv:2207.06030 and arXiv:2406.10490 and cite at first mention, with `~\cite{}`. |
| 2 | **Attribution is unverified inside the paper.** Section 7 asserts the gain comes from settled-decision acquisition, but no ablation appears. The records contain P7a (promotion only), P7b (acquisition only) and P4ref, and they are what isolate the mechanism; none reaches the manuscript. | CRITICAL | Add an ablation table: P3b, P7a, P7b, P7s, P4ref on rialto and ldpa. The data exists. |
| 3 | "We also compare against a cost-aware promotion rule already present in **our own codebase**" breaks anonymity in a double-blind submission and never names or reports the comparator. | MAJOR | Rename to P4ref, describe it as a cost-aware persistence baseline, report its numbers, and drop the self-reference. |
| 4 | The Abstract says "five real-world case studies" with no hint of selection; the 36-considered disclosure sits in Section 5. A reviewer who meets it late will read it as buried. | MAJOR | Put one clause in the Abstract: "five case studies selected from 36 screened datasets". |
| 5 | Contributions list three items; the third bundles evaluation, the scaling law and the failure case. Mapping to sections is therefore 3 contributions to 4 sections. | MINOR | Split the third contribution, or name the sections explicitly in each bullet. |
| 6 | The claim chain and the evidence agree everywhere I checked: "promotes the challenger at event~244 and then purchases labels for the remaining 1756 events" matches the records; "20--67\% fewer labels" matches 66.5/66.7/36.0/19.8\%; "on one of our five cases a fixed-sample binomial test remains the cheaper policy" matches weather (465.56 against 472.57). No overclaiming found. | - | No action. |

## Dimension 2: Writing details

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | Section 4's "Where the budget goes" paragraph is three lines and carries the paper's central empirical motivation. | MINOR | Expand with the per-case post-promotion label counts. |
| 2 | Abstract follows what/why/how/results but never states the challenge explicitly. | MINOR | One clause on why post-decision spend is not trivially removable (rollback must stay detectable). |

## Dimension 3: English grammar
No findings. Tense is consistent (Related Work present for standing facts, past for what was run),
articles and agreement are correct, and no Chinglish patterns are present.

## Dimension 4: LaTeX format

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | **Document class is `article`, not the ICML style file.** No page-limit compliance can be assessed. | CRITICAL | Switch to the official ICML style for the target year and re-check length. |
| 2 | Neither table has a `\label`, and the body never writes `Table~\ref{...}`. Both tables float unanchored. | MAJOR | Add `\label{tab:main}` / `\label{tab:sens}` and reference them from the text. |
| 3 | No algorithm box, although the method is a per-event loop with three stages and two gates. | MAJOR | Add an `algorithm` environment for the issue/release/decide loop. |
| 4 | Table 2's caption says "Em-dashes mark configurations not run"; the project style bans em-dashes as connectors, and using one as a data marker invites confusion with a minus sign. | MINOR | Use `n/a` in the cells and say so in the caption. |

## Dimension 5: Figure quality

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | **`fig1_method.png` and `fig2_netcost.png` exist and are verified, but the manuscript contains no `\includegraphics` and no figure environment at all.** | CRITICAL | Include both with captions whose first sentence states the finding. |
| 2 | Both available figures are raster PNG. ICML camera-ready wants vector. | MAJOR | Regenerate as PDF/SVG, or accept raster at high DPI and state the limitation. |
| 3 | Figure 1 carries a known defect: the SETTLED state uses a green upward arrow although acquisition falls. | MINOR | Regenerate when the billing block clears. |

## Banned-vocabulary and em-dash scan
Full scan of all 191 lines, not sampled.

- Em-dashes used as sentence connectors: **none**.
- Banned AI-tone vocabulary: **none**. ("yet" appears once, line 94, in "not yet promoted", which
  is ordinary usage and not the banned discourse marker.)

## Final score
**4 / 10** as a submission artifact; the research content behind it is considerably stronger than
the document. Three CRITICAL items are all mechanical completeness rather than defects of
substance: no citations, no figures included, wrong document class. None of them requires new
experiments.

## Recommendation
**Needs major revision before submission.** But the revision is assembly, not science: every
number verified, no overclaiming found, and the three limitations (power, reversal risk, ldpa's
inferred chronology) are already stated in the body rather than hidden.
