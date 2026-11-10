# Prior-art audit for Paper 1 scale-25 (Workstream E1)

Written 2026-11-09. Scope: the combined problem and the three ingredients of the frozen v1 package — **E48** (next-information-arrival value veto), **F60** (multi-label short-rollout value of information with a change hazard) and the **hard label cutoff** — plus the surrounding literature the brief lists. Companion files: `NOVELTY_MATRIX.md`, `THEORETICAL_ANALYSIS.md`, `11_NOVELTY_AND_THEORY.md`. It extends, and does not repeat, `docs/qsg_methods_search/sota_expansion/01_PRIOR_ART_AUDIT.md` (comparator-side), `docs/lane_b_burst_allocation/{B0,D0,E0}_prior_art.md` (burst allocation and detection) and `docs/qsg_methods_search/novelty_audit.md`.

## 0. Contract of this audit

Contract (the problem the package solves): two frozen predictors, one deployed at a time; each paid label of a chosen event costs c_q and is released after a delay; a hard cap B on labels; a charge c_s per change of the deployed model, reversible; finite horizon T; mean net cost objective; possible regime change; evaluated on real event streams.

Verification labels (stricter than the earlier audits, because the fetch tool summarises pages):
- **TEXT** — I read extracted text of the paper itself this session (PDF through `pdftotext` or HTML) for the claim made.
- **PAGE** — the arXiv/PMLR/publisher abstract page was opened this session; claims are limited to the abstract.
- **LISTING** — a search-result record (title, authors, venue, abstract snippet) matched; the paper was not opened. Venue and bibliographic data are reliable; content claims are limited to the abstract snippet.
- **INHERITED** — stated by an earlier repo audit that opened it; not re-opened here.
- **BACKGROUND** — classical reference known from memory, nothing opened. Included only to name the established theory; no claim here depends on its text.

A negative ("no paper does X") is evidence of absence from about 25 searches and about 25 page fetches (plus the earlier repo audits), not proof. The list of searches is in section 9.

## 1. Active model selection under limited labels

| work | what it does | what it lacks against the contract | level |
|---|---|---|---|
| Karimi, Gürel, Karlaš, Rausch, Zhang, Krause, AISTATS 2021 (PMLR 130:307-315, arXiv:2010.09818) | Stream of unlabeled points, k classifiers; sample the prediction from exponential weights, recommend argmax; adaptive query probability; regret and query bounds | immediate labels; query *count* is the cost; no hard budget in the paper; no switching cost; no horizon-aware stopping | TEXT (Algorithm 1, Eq. 1, Thm 1-2) |
| Liu, Xia, Stevens, Chen, CAMS (arXiv:2207.06030) | Contextual extension: policies over contexts, hard query budget b, regret and query complexity | immediate labels; no switching cost; contextual machinery unused when streams carry no features | TEXT (Figure 1, Eq. 4, Thm 1-4) |
| Okanovic et al., Model Selector (arXiv:2410.13609) | Pool-based: pick informative points to label, then the best model | pool, not stream; selection once; no deployment cost | PAGE |
| Turrin et al., Online LLM Picker (arXiv:2610.01592) | Stream of prompts, 130+ LLMs, annotation budget | model identification objective; switching and delay not in the abstract | PAGE |
| Hara, Matsuura, Honda, Ito, *Machine Learning* 113 (2024) | Query distribution minimising the variance of the loss-difference estimator | pool; estimation objective; no deployment decision | LISTING |
| Madani, Lizotte, Greiner, UAI 2004, pp. 357-365 | Budgeted active model selection: probes to find the best of several models | offline probe budget; no stream, no horizon, no switching | LISTING (NP-hardness / Biased-Robin statements are a third-party summary and are unverified) |
| Kossen et al., active testing; Sawade et al., active risk estimation | Choose which points to label to estimate a test loss | estimation only | BACKGROUND (repo docs cite them; not opened here) |
| Kuboyama, arXiv:2609.18622 (Sep 2026) | Label budget needed to certify the winner on a selective-prediction metric | certification of a fixed pool; no deployment, no switching, no delay | PAGE |
| Cui, Mignacco, Mori, arXiv:2610.23477 (Oct 2026) | Optimal selection schedules for online linear classification with query cost Δ | learning, not model replacement; delay not in the abstract | PAGE |

Finding. Every method here optimises *identification* or *estimation* of the best model; none charges a deployment change, and none models label delay. Our task is a decision under cost: the value of a label is the expected saving of a later switch minus its price, which is not what these acquisition rules maximise. At two models and two classes they all collapse to disagreement-gated sampling (repo audit), so they test the deployment layer, not the acquisition idea.

## 2. Online active learning with delayed or latent feedback

| work | what it does | gap | level |
|---|---|---|---|
| Castellani, Schmitt, Hammer, ICANN 2022 (arXiv:2204.06822) | Stream-based active learning with *verification latency* under concept drift. PRopagate: a utility estimator that "also predicts the requested, but not yet known, labels"; a drift-dependent dynamic budget | learning objective (accuracy), not a deployment-cost decision; no switching cost; budget is redistributed after detected drift, not optimised | PAGE |
| Cesa-Bianchi, Lugosi, Stoltz, *IEEE TIT* 51(6), 2005 | Label-efficient prediction: forecaster must request labels under a hard query budget; matching bounds | immediate labels; regret objective; no switching | LISTING |
| Joulani, György, Szepesvári, ICML 2013 (PMLR 28) | Online learning under delayed feedback; black-box reductions; delay adds regret additively (stochastic) or multiplicatively (adversarial) | feedback is free (no purchase); no budget | LISTING |
| Vernade, Cappé, Perchet, UAI 2017 | Bandits with delayed conversions | free, censored feedback; no switching cost | LISTING |
| Desautels, Krause, Burdick, *JMLR* 15 (2014) | GP-BUCB: batch/delayed BO; the same bounds hold when there is a delay between starting an experiment and observing the result | no cost per observation; no switching | LISTING |
| Kandasamy et al., AISTATS 2018 (PMLR 84) | Asynchronous parallel BO via Thompson sampling | same | LISTING |
| "Forgetting and Simulating", *Machine Learning*, doi 10.1007/s10994-021-06099-z | Active learning with delayed labels by simulating the missing ones (search snippet) | not opened (publisher redirect) | LISTING only |

Finding. Treating pending labels as uncertain futures inside the *acquisition* utility is **not new**: Castellani et al. (PRopagate) do it for stream active learning, and the batch/asynchronous BO literature does it for pending evaluations (hallucinated or Thompson-sampled outcomes). What none of them has is the economic objective (payback against a switch cost on a finite horizon) or a hard price-and-budget structure on the pending labels. E48/F60's use of pending labels (they average the pending outcomes with their beta-binomial predictive before valuing extra labels) is therefore an application of an existing idea to a new objective.

## 3. Budgeted information acquisition and value of information

| work | content | relevance | level |
|---|---|---|---|
| Gupta and Miescke 1996 (origin of the knowledge gradient) | one-step Bayesian look-ahead for selection | named in the FPD abstract record | LISTING (via Frazier-Powell-Dayanik) |
| Frazier, Powell, Dayanik, *SIAM J. Control Optim.* 47(5):2410-2439 (2008) | the knowledge-gradient policy: myopic expected increment in terminal value; optimal for one period and as the horizon → ∞; bounded suboptimality otherwise | E48 is a KG-type one-step look-ahead with an arrival delay | LISTING |
| Ryzhov, Powell, Frazier, *Oper. Res.* 60(1):180-195 (2012) | KG for **online** learning (finite or infinite horizon): rewards earned while learning | the online variant is the closest KG relative of "labels pay back over the remaining horizon" | LISTING |
| Frazier and Powell, *Decision Analysis* 7(4):378-403 (2010) | the marginal value of information is **not concave** (nonconcavity from Radner-Stiglitz 1984); "eventually concave"; a policy that handles it | the reason a one-label VOI can be 0 while a two-label VOI is positive — F60's bundle | LISTING |
| Radner and Stiglitz 1984; Chade and Schlee, *J. Econ. Theory* 107:421-452 (2002) | nonconcavity in the value of information; sufficient conditions | theory behind the previous row | LISTING (Chade-Schlee); Radner-Stiglitz cited through listings, original not opened |
| Chick, Branke, Schmidt, *INFORMS J. Comput.* 22(1):71-80 (2010) | sequential sampling that myopically maximises expected value of information; finds the gain from fewer approximations is outweighed by myopia once more than a few dozen samples are allocated | warns that one-step VOI is myopic; supports bundles | LISTING |
| Chick, Forster, Pertile, *JRSS-B* 79(5):1439-1462 (2017) | Bayesian fully sequential experiment with **delayed response**; sampling cost c; population P (finite horizon); one-time switching cost I; pipeline observations; optimal "no experiment / fixed / sequential" regions and stopping boundaries; for unknown variance a **KG continuation set that evaluates multi-sample allocations** (a set of batch sizes) | the closest published *controller*: DP + pipeline + finite horizon + switching cost + multi-sample look-ahead | TEXT (model section, stage definitions, KG continuation set) |
| Wan, Liu, McQueen, Hains, Song, KDD 2023 (arXiv:2304.00420) | Bayesian sequential decision for online A/B early stopping, solved by RL | finite horizon and opportunity cost; no label budget, no reversibility | PAGE (title/abstract only; the repo's "Sec. 5.2.4 Eq. 1" hurdle citation is INHERITED) |
| Howard 1966; Raiffa and Schlaifer; Berry and Fristedt 1985; Gittins index | classical decision-theoretic value of information and bandit theory | context | BACKGROUND |

Finding. E48 = knowledge gradient with a delayed arrival, F60 = multi-sample KG (batch look-ahead), both with a finite-horizon payback terminal value, i.e. exactly the structure of Chick-Forster-Pertile's KG continuation set. The hazard survival factor `surv(H,h)` and the stale-posterior reset component are the only parts I can not place in these papers; they correspond to hazard-discounted horizons used in change-point models (section 6). The arrival discount 0.5 is a heuristic constant with no counterpart.

## 4. Reversible switching and switching-cost online learning

| work | content | gap | level |
|---|---|---|---|
| Cesa-Bianchi, Dekel, Shamir (arXiv:1302.4387); Dekel, Ding, Koren, Peres (STOC 2014, arXiv:1310.2997) | switching costs: Θ̃(T^{2/3}) bandit vs Θ̃(√T) full information | adversarial regret; no label price, no delay | INHERITED (abstract) |
| Altschuler and Talwar, *Math. OR* 46(1):179-203 (2021) | prediction from experts with limited switching; phase transition in the switching budget | switching *budget* not price; no labels | LISTING |
| Banks and Sundaram, *Econometrica* 62(3):687-694 (1994) | with switching costs there is **no optimal index policy** for the multi-armed bandit | explains why the exact controller is a DP, not an index; our DP is the right object | LISTING |
| Asawa and Teneketzis 1996 | partial index characterisation | | LISTING (via Banks-Sundaram records) |
| Qiu et al. (arXiv:2602.06902) | OCO with movement costs and delay | continuous action | PAGE |
| Gong and Zhang, ICML 2026 | paid observations; switching-cost analogy | no deployment | TEXT (structure) |

## 5. Sequential experimentation with acquisition costs; optimal stopping; SPRT

- Wald-Wolfowitz 1948 (*Ann. Math. Statist.* 19(3):326-339): the SPRT minimises expected sample size among tests with the same error probabilities — **LISTING**. The Wald controller in our panel is a normal lower-bound payback rule, *not* an SPRT, and should not be named after Wald in a paper (the repo uses "Wald LCB"). The SPRT has no horizon or cost; the Bayes version with sampling cost and a finite horizon (Arrow-Blackwell-Girshick 1949; DeGroot 1970) is the right ancestor: **BACKGROUND**.
- Chow, Robbins, Siegmund 1971 (*Great Expectations*): in the "monotone case" the one-step look-ahead stopping rule is optimal — **LISTING** (second-hand through two journal records). This is the theoretical home of E48: one-step look-ahead is optimal when the value of continuing is monotone. Our reduced DP (THEORETICAL_ANALYSIS.md) exhibits exactly the nonconcavity that *violates* the monotone case when labels are pending (single-label VOI 0, two-label VOI > 0), which is why F60's bundle exists.
- Chick-Forster-Pertile 2017 (section 3, TEXT): stopping boundaries with delay, and the statement that sequential sampling benefits from pipeline arrivals.
- Challenger (Digalakis et al., arXiv:2512.18390): finite-horizon stopping with payback and confidence bound, no delay or budget — PAGE + INHERITED.

## 6. Change-point-aware model selection and cost-aware retraining

| work | content | gap | level |
|---|---|---|---|
| Adams and MacKay 2007 (arXiv:0710.3742) | Bayesian online changepoint detection: run-length posterior with a hazard H(τ); constant hazard for geometric gaps | detection, no decision cost; the `Post` class of search60 is a moment-matched two-component hazard mixture in the BOCPD spirit (the E-module docstring says "BOCPD-style weights") | LISTING |
| Regol et al., ICML 2025 (PMLR 267:51369-51404) | retrain-or-keep via forecast quantiles; 7 datasets; robustness to mis-specified cost | no labels budget, no delay | PAGE |
| Mahadevan and Mathioudakis, arXiv:2310.04216 (published *Knowledge-Based Systems* 2024 per a listing) | cost-aware retraining algorithm balancing retraining cost against a staleness cost estimated from offline data | no label purchase | LISTING |
| Podkopaev and Ramdas, ICLR 2022 (arXiv:2110.06177) | sequential test for harmful shift of a deployed model's risk, confidence sequences | alarm, not a switching policy | LISTING |
| Han, Huang, Wang, ICML 2024 | adaptive window for assessment under temporal shift | no cost | PAGE |
| Shin-Ramdas-Rinaldo e-detectors; Shekhar-Ramdas | detection with ARL control | detectors | INHERITED |

## 7. Rollout approximations to dynamic programming

Bertsekas, Tsitsiklis, Wu, *J. Heuristics* 3:245-262 (1997; LISTING) define rollout: improve a base heuristic by one-step look-ahead with the heuristic as the continuation; Bertsekas's later survey and book (BACKGROUND/LISTING) show rollout improves on its base policy (policy-improvement property) under mild conditions. F60 is called a "short-rollout" in the repo but is not a rollout in this sense: it evaluates the value of b *additional labels* followed by the optimal *terminal* decision (max(0, payback − c_s)), a one-step multi-sample look-ahead (KG with batch b), and does not roll out a base policy for the remainder. It therefore carries neither a policy-improvement guarantee nor a Bellman-residual bound. The reduced DP in THEORETICAL_ANALYSIS.md measures its gap to the exact optimum numerically.

## 8. Is the combined problem new, and does the package approximate an established controller?

**Question 1: is the combination "paid labels + delay (pending observations) + hard budget + reversible deployment + switch cost + change hazard + finite horizon + real-stream evaluation" published?** I did not find it. Closest, in order:
1. Chick-Forster-Pertile 2017: paid sampling, delay with pipeline observations, finite population/horizon, one-time switching cost, Bayesian DP and KG look-ahead. Lacks: hard budget (only a maximum sample size), reversibility, change hazard, stream evaluation, paired-disagreement structure.
2. The Challenger (2025-26): payback with a confidence bound, finite-horizon stopping. Lacks delay, budget, reversibility, disagreement evidence.
3. Castellani et al. 2022: delayed labels with budgets under drift, utility of pending labels. Lacks switching costs and deployment decisions.
4. Regol et al. 2025 / Mahadevan-Mathioudakis: cost-aware retraining; no labels at all.
5. CAMS / Model Picker / Model Selector: label-efficient selection with budgets; no switching cost, no delay.
The absence of a hit is not proof. In particular I did not search the real-options and sequential-clinical-trial literatures beyond Chick et al., the quickest detection with sampling constraints beyond B0/D0/E0, or restless-bandit/Whittle-index treatments of switching with observations.

**Question 2: what is new in E48?** Known: one-step knowledge-gradient VOI of the next observation (Gupta-Miescke; Frazier et al.), its online/finite-horizon form (Ryzhov et al.), the delay-adjusted horizon (Chick et al.), the veto/threshold use against a price. New or unverified: the specific *arrival discount* constant and the hazard-survival factor in this form; applying it as a veto on a randomised pacing draw. It is not a new principle.

**Question 3: what is new in F60?** Known: multi-sample look-ahead against nonconcave VOI (Frazier-Powell 2010; Chick et al. 2017 KG continuation set; Chick-Branke-Schmidt on myopia), pending labels averaged with their predictive (PRopagate, GP-BUCB-style pending handling), hazard-discounted horizons (BOCPD-style). New or unverified: committing to a packet of b disagreement events after a positive bundle test. Not a rollout in Bertsekas's sense.

**Question 4: what is new in the hard label cutoff?** Known: finite-horizon value of information vanishes near the end (every finite-horizon DP; Chick et al. "do not experiment" region). The exact reduced DP shows the **Bayes-optimal stop is far later than the heuristic cutoff** (THEORETICAL_ANALYSIS.md section 6): the cutoff at H=0.55T is therefore not a feature of the optimal controller but a repair for a payback controller that keeps buying labels it does not use well. As a design lever for a heuristic switcher it is an empirical finding, not a theoretical result.

**Question 5: does the package approximate an established controller?** Yes: the exact Bayes-adaptive DP of the reduced model is the established benchmark (Bellman; Chick et al. for the delayed finite-horizon case), and EQSDp + E48 + F60 is a hand-built approximation of the KG-with-pipeline family to it. No guarantee ties them; the measured gap is in THEORETICAL_ANALYSIS.md.

## 9. Search log (all 2026-11-09, standard web search unless noted)

Frazier-Powell-Dayanik KG; Ryzhov-Powell-Frazier online KG; Frazier-Powell paradoxes; Radner-Stiglitz / Chade-Schlee; Desautels-Krause-Burdick; Joulani-György-Szepesvári; Chick-Branke-Schmidt; Bertsekas-Tsitsiklis-Wu rollout; Altschuler-Talwar; Banks-Sundaram; Madani-Lizotte-Greiner; Cesa-Bianchi-Lugosi-Stoltz; Mahadevan-Mathioudakis; Podkopaev-Ramdas; an extended search "online model selection limited labels switching cost delayed labels stream deploy challenger"; Chick-Forster-Pertile; Kandasamy et al.; Vernade et al.; Adams-MacKay; Chow-Robbins-Siegmund; Wald-Wolfowitz; "active learning with delayed labels"; Wan et al.; Hara et al. Fetches: Karimi (PMLR, arXiv, PDF), CAMS (arXiv abs, HTML), Okanovic, Turrin, Digalakis, Regol (arXiv, PMLR), Gong-Zhang (PMLR, PDF), Qiu, Han, Castellani, Kuboyama, Cui et al., Chick-Forster-Pertile (accepted manuscript), GitHub pages for DS3Lab, xuefeng-cs, RobustML-Lab, sato9hara, eliselyhan. An attempt to read the Springer record for the delayed-label AL paper hit a redirect and was not completed.

## 10. Not done

Full text of Hara et al., Madani et al., Castellani et al., Frazier-Powell-Dayanik and Ryzhov et al. (listing level only). Any claim in this file labelled LISTING is limited to its abstract snippet. Searches for restless-bandit or Whittle-index treatments of switching with observations, for sequential change detection with *paid, delayed* observations beyond the burst-allocation audits, and for real-options learning (Keller-Rady, Moscarini-Smith) were not run. A Google-Scholar-style forward-citation search of the Challenger and CAMS papers was not run.
