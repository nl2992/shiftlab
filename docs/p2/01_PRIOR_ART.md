# P2 prior art and novelty position for NAD (2026-11-09)

Status: working document. Not a survey. Nothing here is a claim of novelty until the checks in
section 5 are done.

## 1. Scope and search method

NAD (null-aware deployment) is an incumbent/challenger promotion rule. It buys delayed labels only
on events where the two models disagree, under a hard label budget, and it charges a switching cost.
Its certificate is a started mixture of betting factors tested against a per-step envelope u_k, the
worst-case conditional success probability under a declared dependence class:

- Markov persistence <= rho_bar: u_k = 1/2 + rho_bar^{g_k}/2 after a favourable previous queried
  outcome, 1/2 otherwise;
- phi-mixing envelope: u_k = 1/2 + beta(g_k), with beta(g) = rho_bar^g in the implementation.

Here g_k is the event gap between consecutive queries. The acquisition rule chooses the gap that
maximises the planned information rate KL(q||u(g)) / (g + 1/dis_rate) under a predictable plug-in
alternative and the budget ("dependence-priced spacing"). Because certificates are pathwise
monotone in rho_bar, one can also report an anytime-valid "dependence robustness value", the largest
rho_bar whose certificate has crossed, analogous to Rosenbaum sensitivity values.

Search method. The external literature comes from model-assisted web search (WebSearch and
WebFetch) on 2026-11-09 (`docs/p2/_lit_raw.md`), from the 2026-11-06 pass
(`docs/p2_benchmark/RELATED_WORK.md`), and from the SOTA-sprint audit
(`docs/sota_sprint/novelty_audit.md`). The search was not exhaustive. A missing hit is not evidence
that a work does not exist. Most items were checked at title, author, venue and abstract level only.
Items marked UNVERIFIED were seen second-hand or as search hits. Official code links were not found
for most items. Several arXiv identifiers carry 2026 dates; I report them as the input files give
them and did not re-check them.

## 2. Closest prior work

"Lacks" means lacks relative to NAD, as far as the input files show (mostly abstract-level).

### (a) Anytime-valid forecast comparison

| Work | What it does | Lacks relative to NAD |
|---|---|---|
| Choe and Ramdas, "Comparing sequential forecasters", Oper. Res. 72(4), 2024, arXiv 2110.00115 | Confidence sequences and e-processes for the time-averaged mean score difference, no assumptions on forecasts or outcomes. Valid because the null is a conditional mean of increments given the past. | Targets the average of conditional means, not the marginal quantity. No label purchase, budget, switching cost or dependence class. The model-free baseline any Markov or mixing assumption must beat on power. |
| Henzi and Ziegel, Biometrika 109(3), 2022 (erratum 109(4)), arXiv 2103.08402 | E-values for proper-score comparison, valid under optional stopping. Erratum: the original construction holds only for lag h=1; a corrected construction is given for h>1. | Lag-h dependence is handled by restructuring the sequence, the closest verified thinning precedent. No dependence envelope, no label cost. Authors note a power cost. |
| Arnold, Gavrilopoulos, Schulz, Ziegel, Sequential model confidence sets (SMCS), arXiv 2404.18678 | Time-uniform nonasymptotic model confidence sets from e-processes. | Multi-model selection; no labels, costs or dependence robustness per abstract. Author order and venue vary across sources (one aggregator says JRSSB; unverified). |
| Giacomini and White, Econometrica 74(6), 2006 | Fixed-sample tests of conditional predictive ability; origin of the conditional vs unconditional distinction. | Not sequential. Conceptual ancestor only. |

### (b) Gated or safe deployment, active labelling, active model selection

| Work | What it does | Lacks relative to NAD |
|---|---|---|
| Karampatziakis, Mineiro, Ramdas, "Off-policy confidence sequences", ICML 2021 (arXiv 2102.09540) | Betting confidence sequences for off-policy evaluation, with a gated-deployment application: stage a candidate, track the CS, upgrade when safe. The acronym "MOPE" was not confirmed on a primary page. | No label cost or budget, no switching cost, no serial dependence. Nearest ancestor of the certificate gate. |
| Xu, Karampatziakis, Mineiro, "Active, anytime-valid risk controlling prediction sets", NeurIPS 2024 (arXiv 2406.10490) | Label policy decides per covariate whether to query; budget is an expected proportion; optimal policy characterised; anytime-valid under adaptive collection. | Acquisition is i.i.d.-style variance allocation. No dependence, no spacing, no promotion economics. Disagreement-only labelling is a special case. Its acquisition is used here as `xu_acquisition_only`. |
| Balachandran, "Pay only for disagreement" (DISCERN), arXiv 2609.17560 (single-author preprint) | Zero-label tier plus an audited tier that labels sampled disagreements, with an anytime-valid CS. Label complexity rho^2/eps^2; one error budget over unbounded promotions; 785 update pairs. | Highest threat to "label only on disagreement plus sequential certificate". Per abstract: no switching cost, delay or payback, no dependence robustness. Full text NOT read (section 5). |
| Karimi et al., Model Picker, AISTATS 2021 (arXiv 2010.09818); title and venue from memory, authors not re-verified | Online active model selection for pre-trained classifiers. | No level-alpha promotion certificate, no deployment economics. |
| Liu, Xia, Stevens, Chen, CAMS, NeurIPS 2024 (arXiv 2207.06030) | Context-aware active model selection. | Uncertified; no promotion certificate, no dependence. Used here as `cams_adapter`. |
| Zrnic and Candes, "Active statistical inference", ICML 2024 (arXiv 2403.03208) | Model-guided labelling under a budget with valid confidence intervals. | Estimation rather than a promotion decision; i.i.d.; no switching. |
| Chugg et al., "Auditing fairness by betting", NeurIPS 2023 (arXiv 2305.17570) | Betting tests with adaptive collection under a known policy. | No serial dependence. |
| Podkopaev and Ramdas, ICLR 2022; Amoukou et al., NeurIPS 2024 | Harmful-shift monitoring by sequential risk tracking; label-free extension. | Monitoring, not paired promotion with purchased labels. |

### (c) Dependence-robust sequential inference

| Work | What it does | Lacks relative to NAD |
|---|---|---|
| Yuan, "Self-normalized concentration inequalities of marginal mean with sample variance only", arXiv 2512.01817 (single-author, unreviewed) | Martingale-difference case uses sample variance; phi and phi-tilde mixing case uses an empirical block long-run variance. A marginal-mean, dependence-robust bound. | Time-uniformity not established from the abstract (must check). No betting, acquisition or budget. If time-uniform, it is a competing certificate class, not an economic layer. |
| Wasserman, Ramdas, Balakrishnan, "Universal inference", PNAS 117(29), 2020 (arXiv 1912.11436) | Split LRT and running-MLE e-values for composite nulls. Basis of A1 in this repo. | Model-based (needs a likelihood family), not an envelope on the conditional mean. No acquisition or economics. |
| Ramdas, Ruf, Larsson, Koolen, "Testing exchangeability", arXiv 2102.00630 (from the audit file) | Binary-sequence e-process by universal inference with Markov alternatives of any order. | An e-process, not a supermartingale. Tests exchangeability, not promotion. |
| Saha and Ramdas, e-detectors, arXiv 2607.28322 (audit file; partial read) | Infimum over null distributions of point-null e-processes; Markov transition-matrix changes as an example. | Change detection, not promotion; no budget or spacing. |
| Choe and Ramdas, "Combining evidence across filtrations", arXiv 2402.09698 | E-values combine under arbitrary dependence; e-processes on different filtrations need care. | Justification source for predictable thinning on a coarser filtration, not a competitor. Conditions for thinned streams not yet checked. |
| Waudby-Smith et al., time-uniform CLT, Ann. Stat. 52(6), 2024 (arXiv 2103.06476) | Asymptotic confidence sequences via strong approximation. | Serial correlation not seen in the abstract. Building block for a HAC-style alternative. |
| Ramdas, Grunwald, Vovk, Shafer, Stat. Sci. 2023 (arXiv 2210.01948); Howard et al., Ann. Stat. 49(2), 2021 (arXiv 1810.08240) | Background on e-processes and confidence sequences. | Not threats. |
| Shekhar, arXiv 2512.20039; Whitehouse, Wu, Ramdas, COLT 2025 (arXiv 2310.09100) | Composite-null e-processes (i.i.d. only); martingale-based CS. | No dependence treatment. |
| "Confidence estimation via sequential likelihood mixing", arXiv 2502.14689 | Anytime CS for non-i.i.d. but well-specified likelihood families. | Authors and venue NOT verified. A competing route if a parametric Markov loss model is used. |
| "Linear Bandits with Non-i.i.d. Noise", arXiv 2505.20017 | Blocking-based CS under mixing noise. | UNVERIFIED (title and idea from snippets only). |

Searches that found nothing: a Markov-chain-specific e-process indexed by a declared persistence
bound with predictable gaps; a time-uniform CS for Markov means indexed by mixing time; sensitivity
analysis for dependence in sequential testing. Abeles et al. 2025 (mixing online-to-PAC) was seen
second-hand only and is UNVERIFIED.

### (d) Economic switching and retraining

| Work | What it does | Lacks relative to NAD |
|---|---|---|
| Digalakis Jr et al., "The Challenger", arXiv 2512.18390 | Learning-curve model; optimal evaluation time scales as horizon^(1/(1+alpha)); regret O(T^(2/3) sqrt(log T)). | No statistical certificate, no label purchase. Threat only to a remaining-horizon payback claim. |
| Regol et al., "When to retrain a machine learning model", ICML 2025 (arXiv 2505.14903) | Forecasts performance; retrains when a delta-quantile of retrain cost beats no-retrain. | Economic hurdle without certificates or label acquisition. Baseline. |
| Mahadevan and Mathioudakis, CARA, arXiv 2310.04216 | Staleness cost versus retrain cost. | Same. Venue taken from a search snippet. |
| Katz, arXiv 2604.06438 | Retrain when expected regret exceeds cost; synthetic. | Minor. |
| Fernandez-Barrios et al., arXiv 2609.04388 | Common-harness comparison of nine promotion policies for intrusion detection, conditional null, e-process commit rule, delayed labels, fixed random probes. | Labels counted not priced; no active queries; no dependence analysis; synthetic known nulls only. A benchmark neighbour; must be cited and differentiated. |
| Switching-cost online learning: Kalai and Vempala 2005; Geulen et al. COLT 2010 (snippet only); Dekel et al. STOC 2014 (arXiv 1310.2997); Sherman and Koren (arXiv 2102.03803) | Adversarial-regret view of switching costs. | No alpha-level gating. |

### (e) Internal precursors in this repository

| Item | What it does | Lacks relative to NAD |
|---|---|---|
| QSG (`scripts/failure_atlas_v2_flq/qsg.py`) | Front-loaded disagreement queries; started mixture of betting factors (weights 1/(j(j+1))) against a constant 1/2 null; promote, discard and rollback tests. Valid under a conditional null with no dependence assumption; its i.i.d.-style evidence is not certified for the marginal null under persistence. | No envelope, no spacing, no robustness value. |
| A1 (`scripts/sota_sprint/fam_a.py`, MarkovSUI) | Sequential universal inference: mixture of Markov alternatives divided by a rigorous upper bound on the null likelihood over cells of (p, rho); gap-indexed. Declares the whole Markov family, with NO bound on rho. | Model-based and heavier. Because no rho bound is declared, it is more conservative than a class with a declared bound. No priced spacing. |
| A4 | Bets only on outcomes following an unfavourable previous outcome (and the first), where P(z=1 given previous 0) = (1-a)p <= 1/2 for any rho. Valid with no rho bound. | Discards post-favourable information; no rho_bar tradeoff; no spacing. |
| A5b | A1 evidence plus adaptive density: query only if the gap since the last issued query is at least g* = ceil(ln 0.25 / ln rho_hat), rho_hat a gap-indexed Markov MLE from released outcomes (the fam_a docstring writes g* = min{g : rho_hat^g <= c}). | Already does adaptive spacing, but with a heuristic target (residual correlation <= c), not an information-per-event optimum co-designed with the certificate and budget. Evidence is not envelope-based. |
| QSG-env8 (`EnvelopeMixture`, rho_bar = 0.8) | Envelope bet u = 1/2 + rho_bar^g/2 after a favourable previous outcome, 1/2 otherwise; each grid component bets only where p' > u. | No spacing (ordinary QSG acquisition). It resets the previous outcome at test restarts, so the first post-restart factor is not bounded by u under the class (per the `nad.py` docstring); NAD tracks the previous outcome over the whole stream. M1 therefore exists internally in an earlier form. |

Sprint-audit verdicts (`novelty_audit.md`): a gap-aware Markov e-process with predictable gaps was
rated borderline, substantive only with a power gain over the conditional-mean null. Thinning and
block e-values were rated "little new" and a baseline arm. Autocorrelation-aware spacing was judged
defensible only with a closed form or a measured information-per-label gain over uniform pacing and
Xu's q*.

## 3. Novelty matrix

Mechanisms:

- M1: envelope certificate under a declared dependence class (started mixture against a per-step
  worst-case conditional mean).
- M2: information-rate-optimal spacing co-designed with the envelope and the hard budget.
- M3: anytime dependence robustness value (largest rho_bar whose certificate has crossed).
- M4: economic layer (switching cost, payback, hard budget, delayed labels) joined to the certificate.

Entries (same / partial / absent) are judged from the inputs, mostly at abstract level.

| Work | M1 envelope | M2 co-designed spacing | M3 robustness value | M4 economic layer |
|---|---|---|---|---|
| Choe-Ramdas 2110.00115, Henzi-Ziegel | partial (conditional-mean null, no declared class) | absent | absent | absent |
| SMCS 2404.18678 | absent | absent | absent | absent |
| Karampatziakis et al. 2021 | partial (betting CS, no dependence) | absent | absent | partial (deploy gate, no costs) |
| Xu et al. 2024 | absent | partial (optimal i.i.d. label policy) | absent | absent |
| DISCERN 2609.17560 (abstract only) | absent | absent | absent | absent per abstract (shares disagreement-only labelling) |
| CAMS, Model Picker, Zrnic-Candes | absent | partial (active querying, i.i.d.) | absent | absent |
| Yuan 2512.01817 | partial (different construction; time-uniformity unknown) | absent | absent | absent |
| Universal inference, Ramdas et al. 2102.00630 | partial (composite null by likelihood) | absent | absent | absent |
| Combining evidence across filtrations | absent (supports validity of predictable thinning) | absent | absent | absent |
| Challenger, Regol, CARA | absent | absent | absent | partial (switching economics, no certificate or labels) |
| Fernandez-Barrios 2609.04388 | absent | absent | absent | partial (promotion harness; labels not priced) |
| QSG | absent | absent | absent | partial (budget and rollback; no switching price) |
| A1 | partial (model-based class, no rho bound) | absent | absent | partial (QSG skeleton) |
| A4 | partial (valid for any rho, uses post-unfavourable outcomes only) | absent | absent | partial |
| A5b | partial | partial (heuristic adaptive gap) | absent | partial |
| QSG-env8 | same, modulo the restart reset | absent | absent | partial |

Honest reading.

- M1 alone is an elementary construction: bounded-conditional-mean testing by betting. If the
  conditional success probability is at most u_k, the likelihood ratio against u_k has conditional
  mean at most 1. QSG-env8 already implements it internally. M1 is the certificate component, not a
  contribution. Refinements over env8 are the whole-stream previous-outcome tracking (a validity
  fix) and the phi-mixing envelope (a one-line change).
- Whether the Markov envelope has more power than A1/A4/A5b, or than Choe-Ramdas on the marginal
  null, is an empirical question this document does not answer.
- M2: A5b already spaces queries adaptively. NAD differs in objective (planned KL against the
  envelope per unit of expected event time, with a budget-sustainable floor on the gap) and in the
  fact that the envelope depends on g, so spacing buys certificate strength directly. The claim is
  "a different rule evaluated head to head with A5b", not "first spacing rule". Per the sprint
  audit it counts as substantive only with a measured gain over A5b and Xu's q* at matched budget.
- M3: nothing found resembles a dependence sensitivity value for sequential tests. Monotonicity in
  rho_bar follows directly from the construction, so this is a reporting device with a clean
  interpretation, not a deep result. The Rosenbaum analogy is an analogy only.
- M4: individually present in the literature (Challenger, Regol, CARA); not found jointly with
  certificates and label purchase.

Combinations that look new as far as the search found (weak evidence of absence):

1. M1 with M2: spacing chosen to maximise the information rate of an envelope certificate under a
   declared dependence class and a hard label budget. Nearest: A5b (different rule and evidence),
   Xu et al. (i.i.d. allocation).
2. M3 on top of M1: an anytime robustness value for an e-process certificate. No close match found.
3. M1, M2 and M4 in one promotion rule with delayed labels. Pairwise overlaps exist (DISCERN and Xu
   for acquisition plus certificate; Karampatziakis for certificate plus deployment; Challenger and
   Regol for economics); none of the found works has all of them.

Not novel, cite and do not claim: disagreement-only labelling with an anytime CS (DISCERN, Xu);
CS-gated deployment (Karampatziakis); paired-forecaster CS (Choe-Ramdas); horizon-based switching
(Challenger); cost-ratio retraining (Regol, CARA); thinning to restore structure (Henzi-Ziegel).

Validity of spacing. Under the envelope, validity holds for any predictable gap because u_k uses the
realised gap; spacing affects power only. This sidesteps the "thinning leaves residual dependence
rho^g" concern in `_lit_raw.md`, but makes the guarantee conditional on the declared class: it fails
if true persistence exceeds rho_bar, and the phi envelope as implemented does not cover heavy-tailed
run lengths.

## 4. Positioning against the strongest competitors

- Versus Choe-Ramdas: they control the conditional-mean null with no assumption. NAD controls a
  marginal-style null (sign process with mean <= 1/2) under a declared class, at the price of an
  assumption. The case for NAD rests on over-promotion of the conditional-mean certificate on
  persistent streams, an empirical finding of this repository, not a theorem.
- Versus A1/A4/A5b: same skeleton, different evidence and spacing. Needs a head-to-head on the
  sprint benchmark including misspecified dependence.
- Versus DISCERN: shared acquisition idea. Differences to show are the dependence class, the
  spacing and the economic layer.

## 5. Threats and what must be checked before submission

1. Read DISCERN (arXiv 2609.17560) in full: i.i.d. assumption, handling of delay, any dependence
   correction or switching cost, and what "one error budget over promotions" means relative to NAD's
   alpha / 2^j cycle schedule. Do a manual pass on its related work.
2. Check whether Yuan (2512.01817) is time-uniform, whether it applies to adaptively spaced samples,
   and whether a block long-run-variance certificate beats the envelope on power. If time-uniform,
   add it as a comparator.
3. Search specifically for sensitivity analysis for dependence in sequential testing and for
   Rosenbaum-style sensitivity values for e-processes. Only one search pass has been done.
4. Search for phi-mixing and beta-mixing e-processes and confidence sequences, including the
   unverified 2505.20017, 2502.14689 and Abeles et al.
5. Verify the conditions in Choe-Ramdas 2402.09698 for predictable thinned streams and
   delayed-label filtrations (delay about 100 events makes the filtration lag).
6. Prove the phi envelope: P(z_k=1 | F_{k-1}) <= 1/2 + beta(g_k) must hold conditional on the whole
   past, including the intervening query times. The mixing coefficient bounds dependence for a
   sigma-field at lag g; check this against the history actually conditioned on.
7. Write the proof that tracking the previous outcome across test restarts and across
   promote/rollback cycles preserves the supermartingale property with the alpha / 2^j schedule and
   the rollback test. The docstring asserts it; no written proof is in the inputs.
8. Check the envelope for side -1 and for the first outcome of the stream (u = 1/2 requires the
   stationary p <= 1/2 in the declared class).
9. Rerun the gap search for anything dated after 2026-11-09 and check the 2026 arXiv identifiers
   against primary pages.
10. Verify the loose bibliographic details noted above: MOPE acronym, Model Picker authors, SMCS
    venue and author order, CARA venue, depth of the Saha-Ramdas read.
11. Empirical evidence still needed for the novelty claim: a measured gain of the co-designed
    spacing over A5b, Xu's q*, uniform and fixed gaps at matched budget; a rho_bar misspecification
    study (true rho above and below the declared bound); and a comparison with A1 and A4.
