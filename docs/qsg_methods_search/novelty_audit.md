# Novelty audit: EQSDp (Beta-quantile payback hurdle with symmetric switch-back)

Date: 2026-11-07. Branch `research/qsg-methods-search-2026-11-07`. Read-only audit; this is the only file written.
Method under audit: `scripts/qsg_methods_search/eqs_d.py` (class `EQSD`; `margin` argument is the D4 additive-hurdle ablation).
Retrieval only: web search + page fetches through a summarising fetch tool; no code downloaded or run.
Status labels: **VERIFIED** = the primary page (arXiv/PMLR/HTML) was opened this session and the cited statement read;
**VERIFIED-REPO** = verified by the repo's own earlier audit (`ECON_CHECK.md`, opened PDFs) and not re-opened here;
**SNIPPET-ONLY** = only a search snippet/listing/abstract seen; nothing is claimed beyond it.
Note: the fetch tool summarises pages, so "quotes" are short and checked against the summary, not against raw PDF bytes.

## 1. Verdict

**NOVEL-INTEGRATION, with a weak NOVEL-COMPONENT claim at most.** No source found states "switch when a conservative
posterior quantile of remaining-horizon payback exceeds the switching cost, with symmetric switch-back, on discounted
disagreement-only evidence under a hard delayed-label budget". But every ingredient is published, and two sources come
uncomfortably close to the *quantile-hurdle* idea: Regol et al. (ICML 2025) decide retrain-vs-keep by comparing
delta-quantiles of horizon-summed cost including a retrain cost (a quantile payback rule, without hysteresis band,
discounting, paired evidence or labels budget), and the horizon-pays rule of Wan et al. / Chick-Forster-Pertile is the
point-estimate version. The honest novelty is therefore "a particular, ablation-supported way of putting uncertainty
into the horizon-pays rule for a budgeted paired-label model-replacement contract", not a new decision principle. A search
of this breadth cannot prove absence (see section 6). One more fact lowers the headline: the repo's "Gong-Zhang" and
"Qiu" comparators are **adapters, not the papers' rules** (section 2, note A), so "beats tuned Gong-Zhang" really means
"beats a discounted importance-weighted point-estimate payback rule"; the additive-margin ablation is the more
informative comparison and it only *ties* that tuned point-estimate rule.

## 2. Closest-prior table

Columns: P = payback rule (remaining horizon x gain > switch cost); Q = uncertainty-scaled (quantile/LCB) hurdle;
D = discounting/nonstationarity; E = disagreement/paired-outcome evidence; B = hard delayed-label budget; S = switch-back/hysteresis.
Y = present, p = partial, - = absent, ? = not determinable from what was read.

| # | Source | What it does | P | Q | D | E | B | S | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Regol, Schwinn, Sprague, Coates, Markovich, "When to retrain a machine learning model", ICML 2025, [arXiv 2505.14903](https://arxiv.org/abs/2505.14903) / [PMLR v267](https://proceedings.mlr.press/v267/regol25a.html) | UPF: each step retrain iff delta-quantile of total cost under "retrain" (cost alpha + new-model performance + future decisions, summed to horizon T) is lower than delta-quantile under "keep"; delta=0.95; Beta-modelled performance from a regression forecaster | Y | Y (quantile comparison of horizon cost) | - (undiscounted sum) | - | - (no label budget/delay discussed) | - ("not discussed") | VERIFIED (HTML Sec. 4.2 Eq. 16, Sec. 5; first 100k of 151k chars read). Quote: "we set the confidence threshold of our UPF algorithm to δ=95%" |
| 2 | Wan, Liu, McQueen, Hains, Song, [arXiv 2304.00420](https://arxiv.org/abs/2304.00420) (KDD 2023) | Launch iff posterior-mean effect x horizon x N exceeds hurdle cost c_h (Sec. 5.2.4 Eq. 1, 5.3) | Y (point estimate) | - | - | - | - | - (one-shot launch) | VERIFIED-REPO (ECON_CHECK #1) |
| 3 | Chick, Forster, Pertile, JRSS-B 2017 (DOI 10.1111/rssb.12225) | Bayesian sequential trial with delayed ("pipeline") responses; adopt iff P*Z > I (switch cost) | Y (point/posterior mean) | p (continuation region around I/P) | - | - | p (hard max sample size) | - | VERIFIED-REPO against DP v2 only |
| 4 | Schultzberg & Frånberg, [arXiv 2608.12949](https://arxiv.org/abs/2608.12949) | Finite-horizon continue/accept/reject: optimal rule is a time-varying Bayes-factor threshold (two-point model); per-launch shipping cost s | Y | p (evidence threshold that varies with n) | - | - | - | - | VERIFIED-REPO (ECON_CHECK #3: exact only for two-point prior, affine costs) |
| 5 | Bayraktar & Ludkovski, [arXiv 0712.0413](https://arxiv.org/abs/0712.0413) | Finite-horizon optimal switching on a hidden Markov regime with switching cost; "inertia and hysteresis" | p | p (posterior-state dependent bands, via DP) | - | - | - | Y | VERIFIED-REPO (ECON_CHECK #6) |
| 6 | Dixit 1989 JPE; Dusonchet & Hongler, Automatica 39(11), 2003 "Optimal hysteresis for a class of deterministic deteriorating two-armed bandit problem with switching costs" | Entry/exit band from sunk switching costs; optimal hysteresis for deterministic 2-armed bandit with switching costs | p | - (deterministic) | - | - | - | Y | SNIPPET-ONLY (Dusonchet-Hongler: bibliographic record and keywords only, abstract not read; Dixit abstract only) |
| 7 | Lansdell, Triantafillou, Kording, "Rarely-switching linear bandits", [arXiv 1905.13121](https://arxiv.org/abs/1905.13121) | Switch policy only if the current policy lies outside a confidence ellipsoid and the new one is sufficiently different; "only change policy when given good evidence" (no explicit switching cost) | - (horizon not in trigger) | Y (confidence-set trigger) | - | - | - | - (no switch-back rule) | VERIFIED (ar5iv Sec. 2.2 Alg. 1, App. A) |
| 8 | Gong & Zhang, "The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations", ICML 2026, [PMLR v306](https://proceedings.mlr.press/v306/gong26i.html) | Regret with paid observations; free-observation budget phase transition; meta-controller over strategies | - | - | - | - | p (observation cost / free budget) | - | VERIFIED for abstract only; full text not read, no arXiv id found. **Abstract defines no payback or switching rule** |
| 9 | Qiu, Jacobsen, Esposito, Zhang, "Parameter-free dynamic regret: time-varying movement costs, delayed feedback, and memory", ICML 2026, [arXiv 2602.06902](https://arxiv.org/abs/2602.06902) | OCO with movement costs; delay treated as movement cost; comparator-adaptive dynamic regret | - | - | p (dynamic comparator) | - | p (delay) | - | VERIFIED for abstract; mechanism not read |
| 10 | Mahadevan & Mathioudakis, "Cost-effective retraining of ML models", [arXiv 2310.04216](https://arxiv.org/abs/2310.04216) (CARA) | Retrain/keep trade-off between staleness cost and retraining cost; staleness estimated from offline data | p | - (point estimate; exact rule not read) | - | - | - | - | SNIPPET-ONLY (rule not read) |
| 11 | Shi, Tan, Li, "A Bayesian approach for bandit online optimization with switching cost", UAI 2023, [PMLR v216](https://proceedings.mlr.press/v216/shi23b.html) | Continuous-action Bayesian bandit with switching cost; Greedy/Alternating Search with competitive ratios | - | - | - | - | - | - | VERIFIED for abstract only; no quantile/hysteresis stated there |
| 12 | Chick & Gans, Mgmt Sci 55(3):421-437, 2009 | Stoppable Bayesian bandit with sampling cost and discounting; free-boundary approximation | p | - | Y (economic discount rate, not nonstationarity) | - | - | - | SNIPPET-ONLY |
| 13 | Stucchio 2014 "Bayesian A/B decision rule" (blog); Schultzberg & Frånberg Sec. 5 | "Threshold of caring" expected-loss stop rule (posterior-based) | - | p (posterior loss threshold, no horizon/switch cost) | - | - | - | - | SNIPPET-ONLY (as summarised in search results) |
| 14 | MLDAS, [arXiv 2604.14957](https://arxiv.org/abs/2604.14957) | Model switching with minimum dwell time and minimum relative improvement (fixed 5%) threshold | - | - (fixed relative margin) | - | - | - | Y (fixed-margin hysteresis) | SNIPPET-ONLY |
| 15 | Asawa & Teneketzis 1996; Banks & Sundaram 1994; Jun 2004 survey (De Economist) | Switching-cost bandit indices; no Gittins index policy optimal with switching costs | - | - | - | - | - | p | SNIPPET-ONLY |

### Answers to the three questions

**Q1. Is "switch when a lower credible/confidence bound on remaining-horizon gain exceeds switching cost, symmetric switch-back" published?**
Not found in that form. Pieces: horizon x gain vs cost (rows 2, 3: published, mean-based, one-shot); quantile comparison of horizon-summed costs including a
retrain cost (row 1: published, no switch-back/hysteresis, no label budget); confidence-set-triggered conservative switching (row 7: no horizon, no cost);
hysteresis from switching costs (rows 5, 6: published, via DP/deterministic or fixed band). Bayesian optimal-switching theory (row 5, row 15) implies
the *optimal* rule has an uncertainty-dependent band; EQSDp's quantile hurdle is a closed-form heuristic of that, not derived from it.

**Q2. Any source with disagreement/paired evidence + hard delayed-label budget + discounting + quantile hurdle?**
No source covers more than two of E, B, D, Q together. Closest single source is **Regol et al. 2025 (row 1)**. It differs by: (i) the uncertainty comes from a
regression forecaster over training/eval indices and a shift summary, not from paired outcome counts; (ii) no label-acquisition budget, delay or paired disagreement evidence;
(iii) no discounting of evidence on a label clock; (iv) the comparison is of cost quantiles under two futures with recursive future decisions, not a Beta lower bound on a per-event advantage times r(T-t);
(v) no explicit switch-back asymmetry. Second closest: Wan et al. 2023 (point-estimate payback). Third: Chick-Forster-Pertile 2017 (delayed responses, adoption cost, finite horizon, no rollback, no discounting).
Disagreement-only evidence is, from the repo's own contract discussion, common practice for paired comparisons; no external source found stating it as a rule.

**Q3. Is an uncertainty-scaled hurdle vs a fixed margin argued or compared explicitly?**
Only weakly. Regol et al. argue for risk-averse quantile decisions ("lower delta favors lower-variance costs", Sec. 4.2) against drift detectors and CARA, not against a fixed additive margin.
The AAAI-2026 "dynamic threshold" drift paper ([arXiv 2511.09953](https://arxiv.org/abs/2511.09953), SNIPPET-ONLY) argues a dynamic threshold beats any static one, in drift detection not switching.
MLDAS (row 14) uses a fixed margin. I found no paper that compares "confidence-based hysteresis" with "fixed-threshold hysteresis" on model replacement. That gap is exactly where the D4 ablation sits, so the ablation result is the strongest piece of the claim, but it is one synthetic family (see objection).

### Notes on the repo's comparators (important for the headline numbers)
A. `gong_zhang_paid_obs` (`scripts/failure_atlas_v2_flq/r6_policies.py`) is a discounted importance-weighted point-estimate gain `(T-t)*s_hat/den > c_s` with symmetric switch-back; its docstring states "adaptations, not reproductions: the source guarantees do not transfer". The Gong-Zhang abstract (row 8) contains no such rule. `qiu_delayed_movement` is a blocked fixed-share Hedge on IW differences; Qiu et al.'s abstract (row 9) is a parameter-free OCO dynamic-regret method. Neither name should be written as "Gong-Zhang's rule"; call them "Gong-Zhang-style paid-observation adapter" and "Qiu-style delayed-movement Hedge adapter", or cite them only as inspiration.
B. Consequently the decisive baseline is the tuned point-estimate economic switcher, and the D4 result says the quantile hurdle beats "point estimate + fixed margin" by 6-13 units while the margin version only ties it.

## 3. Internal precedents (other branches)

Searched `git grep` over all local heads/remotes for hysteresis, posterior quantile, `beta.ppf`, credible/lower bounds. Beta quantiles elsewhere are Clopper-Pearson style certification bounds, not switching hurdles.

- `heads/audit/shiftlab-retrospective-rectification-2026-11-01` and `heads/main`: `src/shiftlab/dive/atlas_components.py` (`certificate_econ`, `hysteresis` k-streak, `rollback_monitor`; "certificate_econ never rolls back", lines ~10-60, 189, 226, 657-671) and `docs/failure_atlas_v1_protocol.md:145/151` ("certificate plus economic check, hysteresis, rollback monitor"). Precedent for point-estimate economic gating and count-based hysteresis, **not** for a quantile hurdle; hysteresis there is a streak length k=2.
- `heads/main`: `docs/gaver/00_PLAN_AND_TODO.md:92,137,142` and `docs/gaver/01_HARNESS_MAP.md:61` (GAVE-R compared against "simple hysteresis" and E_rb; promotion rule `(T-t+1)*ben > econ_mult*s` with `ben` a sample mean of last 10 labels): again point-estimate horizon-pays.
- `scripts/promising_directions/sota/competitors/controls.py` (`EconomicReplacement`): point estimate, `min_obs`, additive `margin`. This is the in-repo ancestor of the D4 ablation.
- `heads/audit/retrospective-publishable-checkpoint-2026-11-02`: `docs/lane_b_burst_allocation/C0_candidates.md:128` mentions re-probing "a posterior quantile" in a burst-allocation context (not read in depth; different object: boundary-time quantile for probing). `docs/promising_directions/protocols/B1-certified-switching.md` and `scripts/promising_directions/b1_certified_switching.py` appear in the hysteresis/LCB grep; B1 is a *certified* (valid-test) switching design, different guarantee class. Not opened in depth.
- Internal prior-art audits already covering the economic side: `origin/claude/shiftlab-methods-strategy-dba13e:docs/sota_fidelity/prior_art/{econ_gate_external,ECON_CHECK}.md`; `docs/gaver/40_PRIOR_ART_CHECK.md` (Gong-Zhang at SNIPPET level).
Conclusion: no earlier ShiftLab method used a Beta/posterior-quantile payback hurdle; the quantile is new to the repo but not to the literature (Regol).

## 4. Positioning and strongest objection

Positioning sentence (paper): "We study budgeted, delayed-label model replacement as a finite-horizon switching problem and show that making the classical horizon-pays rule uncertainty-aware, by requiring a posterior quantile of the remaining-horizon payback on discounted disagreement evidence (rather than its mean, or its mean plus a fixed margin) to exceed the switching cost, reduces expected cost relative to tuned point-estimate and delayed-movement adapters on synthetic reversal episodes; we claim no false-promotion guarantee." Do not claim a new switching principle, a theorem, or superiority over Gong-Zhang or Qiu as published methods.

Strongest reviewer objection: "This is the Wan/Chick horizon-pays rule with a lower-confidence bound, which is standard practice (and in Regol et al. 2025 literally a quantile comparison with a retrain cost); your gain over the point-estimate rule is shown only against hand-adapted baselines and against fixed additive margins on one synthetic family, where a margin scaled like r(T-t)/sqrt(n) or a Wald/Hoeffding LCB would probably do as well." Secondary: the margin ablation uses additive constants (5-40) that do not scale with n, r or T-t, so it may be a weak control for "uncertainty-scaled".

## 5. Baselines the audit says must be run

1. **Regol-style UPF comparator (required).** Delta-quantile retrain-vs-keep comparison of horizon cost with switch cost, adapted to the paired-count evidence (Beta quantiles of the two futures, switch-back allowed). If it matches EQSDp, the quantile claim collapses to "Regol on paired budgeted labels".
2. **Matched-width non-Bayesian LCB (required).** Point estimate minus z*sqrt(p(1-p)/n_eff) (Wald) and a Hoeffding LCB, same gamma, same discounting. Tests whether the Beta form matters or any uncertainty-scaled hurdle works.
3. **Scaled-margin hysteresis (required for the Q3 claim).** Margin proportional to r(T-t) (relative) and a fixed-streak/dwell-time rule (`atlas_components` k=2 hysteresis; MLDAS-style minimum improvement + dwell), tuned on development data like the others.
4. **Finite-horizon Bayes-optimal benchmark (recommended).** Dynamic programming over the discounted-Beta state for the two-model switching problem, as an upper reference showing how much of the achievable gain the closed-form quantile rule captures (Bayraktar-Ludkovski spirit). Optional but it answers "why a quantile".
5. **Rename the existing adapters** in all tables (see Notes A) and, if feasible, open Gong-Zhang's full text and Qiu et al.'s algorithms to say exactly what was and was not ported.

## 6. Limits of this audit

- Fetch tool summarised pages; PDFs returned as binary were not parsed (Regol was read through arXiv HTML, 100k of 151k chars; the remaining 51k were not read, including appendix experiments that might compare fixed thresholds).
- Rows 6, 10-15 are SNIPPET-ONLY or abstract-only; CARA's exact rule, Dusonchet-Hongler's hysteresis result, Chick-Gans horizon and the EJOR 2025 "UCB fixes for switching costs" paper (not opened, not tabulated) could contain closer rules.
- Not searched: Thompson-sampling-with-switching-cost, Keller-Rady/Moscarini-Smith real-options learning, champion-challenger MLOps grey literature, Deng's Bayesian A/B papers. Absence of a hit is not proof of novelty.
- Venue-year facts (ICML 2026 titles) were taken from PMLR/ICML pages seen in search; not independently cross-checked.

## 7. Coordinator verification (2026-11-07)

A second, independent fetch of arXiv 2505.14903 (HTML v1, Secs. 1–7 and App. A.1–A.3, read verbatim) confirms row 1 and **strengthens** it:

- UPF's rule (Sec. 4.2, Eq. 16) compares δ-quantiles of total remaining-horizon cost, including a fixed retraining cost (Eq. 3, 15), at δ=0.95.
- App. A.1 reports that the conservative quantile beats the point-estimate rule (PF = δ=0.5). The AUC difference is significant on 5 of 6 datasets; the exception is electricity.

So the qualitative D4 finding, "an uncertainty-scaled hurdle beats a point estimate", is **already published** for one-directional retraining. Our D4 extension is narrower: the quantile also beats a point estimate **plus a tuned additive margin**, and does so with symmetric switch-back, discounting, and budgeted, delayed, disagreement-only labels. UPF has none of these. It assumes each period's full data is available, and it does not describe rollback to an older model.

**Revised verdict: NOVEL-INTEGRATION.** Drop the NOVEL-COMPONENT claim. Position EQSDp as "a UPF/horizon-pays-style quantile payback rule made reversible and label-budget-aware for paired model replacement". The empirical content is the D3/D4/C3 comparison, not the principle.

**Required comparator, already implemented.** `upf_style_switch_timing_T3` (Regol-style T3 adapter with reversible switching, IPW disagreement cells and periodised Monte Carlo recursion) is on `origin/claude/shiftlab-methods-strategy-dba13e` at `scripts/promising_directions/sota/competitors/upf_style_switch_timing.py`. Port it and run it with the other required baselines from section 5: Wald/Hoeffding LCB hurdles, margins scaled with r(T−t), and a k-streak dwell rule. Use new seeds, and label the run explicitly as **post-confirmation comparator additions**. The locked C3 result stands as recorded, but the C2/C3 claim must not go to a paper until EQSDp also beats these baselines.
