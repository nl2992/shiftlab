# Gap-Mix adversarial prior-art audit

Date 2026-11-08. Scope: is the Gap-Mix evidence process (`src/shiftlab/gaver/gapmix.py`, `ExactGapStart` + `RestartMixture`, label `exact0.8_s4`) novel? Search is bounded (about 12 searches, 6 primary documents). It is not exhaustive. Absence of a hit is not proof of novelty. No theorem was re-proved by the auditor except the short chain-rule argument in section 3.

## 1. Method as implemented (verified from code and docs)

| Item | What the code does | Source |
|---|---|---|
| Data | Binary Z = 1[D<0] at released label rounds ev_k. Declared null: stationary 2-state round chain, p <= q0 = 0.55, persistence rho in [0, rho_bar], rho_bar DECLARED (0.8) | gapmix.py docstring |
| Gap law | P(Z_k=1 given z) = p + (z-p) rho^g, with g = ev_k - ev_{k-1} (exact 2-state skeleton P^g) | `exact_loglik` |
| Numerator | Fixed equal-weight mixture of 16 alternatives (p_a, rho_a) in {.65,.75,.85,.95} x {0,.4,.7,.9}, each scored with exact P^g transitions | `ExactGapStart.update` |
| Denominator | Certified UPPER bound of the HINDSIGHT sup over the null (p<=q0, rho in cells of width .005 up to rho_bar) of the exact-gap conditional likelihood. Per-cell endpoint bound on rho^g, then bisection in p | `certified_null_sup_loglik` |
| Restart | Equal-weight average of 4 per-start e-processes, starts at event rounds {0, .25T, .5T, .75T}; each conditions on its first label | `RestartMixture` |
| Threshold | 1/alpha on the mixture (alpha spent once) | `RestartMixture.alarm` |
| Validity as stated in the repo | Proven only for deterministic calendar and constant delay, given the declared null. NOT proven: value-dependent (closed-loop) requests, informative delay, rho > rho_bar. | gapmix.py docstring, 10_GAPMIX_RESULTS.md |

Discrepancy with the task summary: the task says "predictable (adaptively chosen) times". The repo contract is a deterministic calendar; adaptive times are explicitly unproven. Under a gap g_k that is F_{k-1}-measurable and depends only on history up to the previous label's round, the chain rule (section 3) would carry over, but this is the auditor's reasoning, not a repo result. With label delay, a gap chosen using information correlated with unreleased intermediate states can bias the likelihood. Treat adaptive-time validity as open.

Empirical status (development only): `exact0.8_s4` beats the in-repo Markov LR (`mlr_default8`) by +36.7 points detection with null UCB <= 0.078 for rho <= 0.8, but fails (FP .71-1.0) at undeclared rho = .95 and .99. Every variant valid to rho .99 lost the advantage (WP1b: best valid `exact0.99_s4` is -5.9 points vs `mlr_default8`). The power gain is purchased entirely by the declared null restriction rho <= 0.8. Note `mlr_default8` ignores gaps and takes a sup over ALL 2-state chains with stationary <= q0, a superset of every gap-g skeleton, so it is valid but loose; Gap-Mix tightens the null class, it does not discover new structure.

## 2. Source ledger

Status: READ = text of the relevant method/definition sections read directly (pdftotext or HTML). READ-via-summary = page fetched, a summariser model returned the method; key claims then grep-checked where noted. ABSTRACT-ONLY / SNIPPET-ONLY as labelled.

| # | Source | URL | Status | Relevance |
|---|---|---|---|---|
| S1 | Shin, Ramdas, Rinaldo, "E-detectors: a nonparametric framework for sequential change detection" (NEJSDS 2023) | https://arxiv.org/abs/2203.03532 | READ (pdftotext: Def 2.2, 2.5, 2.6, Example 1, setup of 2.1) | SR/CUSUM e-detectors = sums/maxes of e_j-processes started at each time; non-iid, composite pre-change class, fixed-mixture or predictable-mixture composite alternatives, null-MLE denominators "as in universal inference" |
| S2 | Sethi, Sagar, Agrawal, Basu, Karthik, "Asymptotically Optimal Sequential Testing with Markovian Data" (arXiv v3 12 Jun 2026; ICML 2026 poster) | https://arxiv.org/abs/2602.17587 (html v3) | READ-via-summary for Sec 4-5 (Algorithm 1, Remark 4.2, Thm 4.1); full-text grep for restart/change terms found no change-detection mechanism | The "Sethi et al." of 40_PRIOR_ART_CHECK.md. See section 4 |
| S3 | Wasserman, Ramdas, Balakrishnan, "Universal inference" (PNAS 2020) | https://arxiv.org/abs/1912.11436 (ar5iv) | READ-via-summary (Sec 2, 6, 8) | Split LRT; Sec 6 allows non-iid if likelihood computable conditionally; Sec 8 running-MLE sequential LRT, validity via oracle-likelihood martingale. Proof as presented is iid; says non-iid gives supermartingale. Does NOT treat Markov chains |
| S4 | Ramdas, Ruf, Larsson, Koolen, "Testing exchangeability: fork-convexity, supermartingales and e-processes" | https://arxiv.org/abs/2102.00630 | READ (pdftotext: abstract, Sec 2.1 excerpts) | Universal-inference-style e-process: Jeffreys Markov mixture over alternative divided by null MLE; Markov alternatives; consecutive observations only |
| S5 | "Sequential One-Sided Hypothesis Testing of Markov Chains" | https://arxiv.org/abs/2501.13187 | READ-via-summary | Simple null P known; composite alternative handled by causal (KT/Jeffreys) estimator; test martingale + Ville; consecutive observations |
| S6 | Hypothesis testing for Markovian models with random time observations | https://arxiv.org/abs/1505.06101 | READ-via-summary (model + statistic) | Markov chain seen at iid random times with UNOBSERVED gaps; fixed-sample, asymptotic; observed chain Q = sum_l mu(l) P^l; not sequential, not P^g likelihood |
| S7 | Ramdas, Grünwald, Vovk, Shafer, "Game-theoretic statistics and safe anytime-valid inference" (Stat. Sci. 2023) | https://arxiv.org/abs/2210.01948 | SNIPPET-ONLY | Background: test martingales, e-processes, composite nulls |
| S8 | Ramdas and Wang, "Hypothesis testing with e-values" | https://arxiv.org/abs/2410.23614 | SNIPPET-ONLY (TOC, ICML checklist) | UI e-variable with inf over null; sequence of UI e-variables is an e-process |
| S9 | Shekhar, "Optimal Anytime-Valid Tests for Composite Nulls" | https://arxiv.org/abs/2512.20039 | SNIPPET-ONLY (PDF unreadable; abstract-level description from search only) | Mixture-over-alt / sup-over-null for finite alphabet. Markov extension unconfirmed |
| S10 | Phatarfod (SPRT for Markov chains); Su (Purdue thesis, sequential LRT for Markov dependence) | https://docs.lib.purdue.edu/dissertations/AAI9104711 | SNIPPET-ONLY | Classical Markov SPRT exists |
| S11 | Lai (1988 composite sequential tests; 1998 information bounds for dependent data); Tartakovsky arXiv 2405.00928 (non-iid extension of Lai) | https://arxiv.org/abs/2405.00928 | SNIPPET-ONLY | GLR/mixture sequential tests and CUSUM optimality for general dependent models |
| S12 | Fuh, "SPRT and CUSUM in hidden Markov models" (AoS 2003); "Asymptotic operating characteristics ... HMM" (AoS 2004) | https://arxiv.org/abs/math/0503682 | SNIPPET-ONLY | CUSUM/SR for Markov-dependent data; asymptotic optimality |
| S13 | Lau and Tay, QCD with observation-switching cost (arXiv 1912.11693); Ren, Johansson, Shi (TAC 2017) | https://arxiv.org/abs/1912.11693 | SNIPPET-ONLY (carried from 40_PRIOR_ART_CHECK.md) | Sampling/scheduling for CUSUM; not Markov gap likelihood |
| S14 | Gafni, Iyengar, Zeevi (arXiv 2602.11406) | https://arxiv.org/abs/2602.11406 | SNIPPET-ONLY (carried) | Restart-style CUSUM, regret objective |

Not found in any search: a paper that scores irregularly spaced, KNOWN-gap observations of a Markov chain with the exact P^g likelihood inside an e-process / test martingale. S6 is the nearest "random time observation" paper and it targets the opposite case (unobserved gaps, fixed sample).

## 3. Component-by-component audit

| Component | Verdict | Closest prior | Comment |
|---|---|---|---|
| Likelihood of an embedded/skeleton chain at known gaps = P^g | KNOWN (textbook) | Standard Markov-chain / CTMC discrete-skeleton theory; S6 context | For a 2-state chain P^g has the closed form p+(z-p)rho^g. Using it for a sparse label calendar is an application, not a method. No primary source for a sequential e-process version found (search-limited) |
| Composite null via a supremum denominator | KNOWN | S3 Sec 2/8, S1 Example 1, S4 Sec 2.1, S8, S9; S2 uses inf over P in the Markov null | Gap-Mix denominator is the hindsight null MLE (not split, not predictable). Validity: M/D <= M/L(theta*), and M/L(theta*) is a test martingale for ANY sequentially-defined alternative mixture because the conditional likelihoods factorise by the chain rule. This is the universal-inference argument and needs no iid |
| "Certified" sup (cell endpoint bound + concavity in p) | IMPLEMENTATION DETAIL | none needed | Numerical upper bound of a sup over a 2-parameter compact set; conservatism measured 0 to 0.72 nats. Not a statistical contribution |
| Fixed mixture over alternative grid | KNOWN | S1 (fixed mixture e-detector), S4 (Jeffreys mixture), S5 (Jeffreys/KT) | Grid of 16 is a coarse choice, not a principled mixture |
| Restart mixture over onsets | KNOWN in principle, restricted in form | S1 SR e-detector: sum over e_j-processes started at every time; "average of e-detectors is an e-detector" | Gap-Mix uses 4 FIXED starts at {0,.25,.5,.75}T on event rounds with equal weights. This is a sparse, hand-set SR/CUSUM e-detector, plausibly weaker than a full or geometric-grid SR e-detector. Dilution measured: start-0-only variants lose most late/transient power |
| Predictable/adaptive gap in the evidence | NOT ESTABLISHED | none | Repo proves deterministic calendar only |
| Declared rho_bar as null-class restriction | A modelling assumption, not a method | Restricted null classes standard in UI and S2 (null set P) | WP1b shows the whole advantage disappears when the null is widened to rho <= .99 |

Chain-rule check (auditor's argument): if each Z_k given F_{k-1} (including a predictable g_k) has the Bernoulli law P^{g_k}(z_{k-1}, .) under every null member theta*, then L_t(theta) = prod_k P^{g_k}_theta(z_k | z_{k-1}), the numerator mixture over a FIXED set of alternatives divided by L_t(theta*) is a nonnegative martingale, and sup_Theta0 L_t >= L_t(theta*) gives M_t/D_t <= M_t/L_t(theta*). Ville then gives alpha. Nothing here uses iid, and it covers any F_{k-1}-measurable gap choice provided the Markov-with-known-gap law holds conditional on the filtration actually used (the delay caveat above).

## 4. The "Sethi et al." overlap (resolved)

Identification: Sethi, Sagar, Agrawal, Basu, Karthik, arXiv 2602.17587 (v3, 12 Jun 2026), ICML 2026.

| Aspect | Sethi et al. (READ, Alg 1, Rem 4.2, Thm 4.1) | Gap-Mix |
|---|---|---|
| Null / alt | Composite null set P of transition matrices vs disjoint set Q, ergodic finite-state chain | 2-state, structured null class {p<=q0, rho<=rho_bar} |
| Statistic | L_t = inf over P in 𝒫 of sum_x N_x KL(Q̂_t(x,.) || P(x,.)): hindsight empirical-kernel vs least-favourable null, with threshold beta_t = log(1/alpha) + (m-1) psi_t paying a mixture-regret term. Remark 4.2: exp(L_t - (m-1)psi_t) is bounded by a nonnegative supermartingale (e-process). Not a plug-in or fixed-mixture numerator | Fixed 16-point mixture numerator over certified hindsight null sup, threshold 1/alpha |
| Observations | Consecutive X_{t-1}, X_t | Unequal known gaps, exact P^g |
| Restart / change | None found (full-text grep of v3) | 4-start mixture |
| Goal | alpha-correct and asymptotically optimal expected stopping time (lower bound + matching test) | Finite-budget promotion evidence, empirical |
| Theory | Optimality as alpha -> 0 | Validity under declared null; no optimality |

Conclusion: Sethi et al. supply the closest complete composite-null Markov sequential test and its optimality theory; the 'Markov sequential test with composite null via inf over transition matrices' component is KNOWN. They do not cover irregular known gaps or change/restart structure. Their abstract-level omission of e-process language (noted in 40_PRIOR_ART_CHECK.md) is superseded: Remark 4.2 calls the process an e-process.

## 5. Answers

1. Closest complete prior method: a universal-inference e-detector for Markov data. Concretely S1 (SR/CUSUM e-detector with null-MLE denominators, non-iid allowed) combined with S2/S4/S5 (Markov composite-null / Jeffreys-mixture e-processes). No single paper does the full Gap-Mix combination, but each piece is documented, and S1 explicitly licenses assembling it.
2. Known: exact skeleton likelihood (textbook); sup-over-null denominator (UI, S1, S2, S4); fixed-mixture alternative (S1, S4, S5); restart/onset mixture (S1 SR, S13-style CUSUM restarts). Classical SPRT/CUSUM theory for Markov data (S10-S12) is the older ancestor (SNIPPET-ONLY).
3. Possibly new: only the INTEGRATION, namely exact gap-g Markov likelihood for known irregular gaps inside an e-detector with a declared dependence bound rho_bar, applied to label-budgeted promotion. Not new: each ingredient. Not established: adaptive-time validity, any optimality, or any advantage once rho_bar must cover the real dependence range (WP1b). Search was bounded; a targeted check for "irregularly sampled Markov e-process" in the sensor / bandit literature is still advisable.
4. Yes. "Universal inference with a predictable plug-in Markov MLE alternative plus e-detector restarts" is a standard valid alternative under the same assumptions (declared null class; chain-rule factorisation; deterministic or predictable gaps). Indeed Gap-Mix IS that family: it differs only in (a) fixed 16-point mixture instead of a running plug-in MLE, (b) 4 sparse starts instead of an all-starts SR e-detector, (c) a certified-bound denominator. So the mandatory comparator is UI-plugin-gap: numerator = predictable (running MLE or KT-style) mixture over (p, rho) with exact P^g, denominator = same exact null sup, SR e-detector over all label indices (or a geometric grid of starts, plus a CUSUM variant). Not yet run in this repo. Gap-Mix must beat it at equal null validity; otherwise its numerator/restart choices are tuning details. The in-repo `mlr_default8` is a weaker comparator (gap-blind, 8 starts).
5. Verdict: NOVEL-INTEGRATION at best (weak). Not NOVEL-COMPONENT: no component is new. Not claimable as a new statistical method; claimable as a documented application of known e-detector and universal-inference machinery to gap-aware, delayed, budgeted label feedback.

Positioning sentence (non-overclaiming): "We instantiate a universal-inference e-detector (Shin et al. 2023; Wasserman et al. 2020) for a two-state Markov null with known unequal observation gaps by using the exact P^g skeleton likelihood and a declared persistence bound; the sup-null and restart-mixture machinery is standard, and the gain over gap-blind Markov likelihood ratios comes from the declared bound rho <= 0.8, not from a new inferential principle."

## 6. Required next actions (not done here)

- Implement and run the UI-plugin-gap + all-starts SR/CUSUM e-detector comparator (4 above) on the same null and power seeds before any novelty or superiority claim.
- Prove or drop adaptive-gap validity, including the delay case.
- Re-read S5 and S9 full text (S9 was unreadable, S5 summary only) for Markov mixture / finite-alphabet overlap.
- Cite S1, S2, S3, S4 in any write-up.

## Summary (10 lines)

1. Gap-Mix = exact P^g Markov LR, fixed 16-alternative mixture over a certified hindsight null sup (rho <= 0.8 declared), 4 fixed restart starts, threshold 1/alpha.
2. Repo proves validity only for deterministic calendars; adaptive gaps and delay are unproven.
3. Closest complete prior: e-detector framework (Shin-Ramdas-Rinaldo, READ) plus UI-style Markov e-processes (Ramdas et al., READ; Sethi et al. arXiv 2602.17587, READ-via-summary).
4. Sethi et al. = composite-null Markov sequential test, inf over transition matrices, e-process (Remark 4.2), consecutive data, no restarts, optimality theory.
5. Known: skeleton likelihood, sup-null denominator, fixed mixture alternative, restart mixture. Certified sup is an implementation detail.
6. Only possible novelty: integration (known irregular gaps + exact P^g + e-detector + declared rho_bar for label-budgeted promotion).
7. The empirical gain over mlr_default8 comes from the declared rho_bar = 0.8 null restriction; WP1b shows it vanishes at rho_bar = .99.
8. Standard valid alternative (UI with predictable plug-in Markov MLE + all-starts e-detector) exists and is the comparator Gap-Mix must beat; not yet run.
9. Verdict: NOVEL-INTEGRATION (weak); not a new statistical method; not NOVEL-COMPONENT.
10. Sources: 2 READ, 4 READ-via-summary, 8 SNIPPET-ONLY; file at docs/methods_recovery/50_GAPMIX_NOVELTY.md (uncommitted).
