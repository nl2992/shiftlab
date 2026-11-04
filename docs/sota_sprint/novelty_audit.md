# SOTA sprint novelty audit (Agent F)

2026-11-03. Scope: the mechanisms behind the 24 candidates in `candidates.json` (families A to D),
for the contract T=2000, B=200 paid delayed labels, switching cost, anytime false-promotion
control (see `docs/failure_atlas_v2_flq/results/REPORT.md`, M1 to M4).

How the citations were checked: each one was looked up on 2026-11-03 through arXiv abstract pages,
publisher or PMLR pages, or a web search that returned the publisher record. Entries marked
**UNVERIFIED** were not confirmed. This is a literature audit only. Nothing here is an empirical
result. "No prior art found" means our searches returned nothing. It does not show that nothing
exists.

**Update 2026-11-04:** targeted search for Markovian sequential testing and robust model monitors
found two direct 2026 works not included in the original search. The audit below supersedes any
unqualified "no prior use" wording for Markov e-processes. See the paper record for
[Sethi et al. (ICML 2026)](https://arxiv.org/abs/2602.17587) and
[Kurečka et al. (arXiv:2610.26193, Oct. 2026)](https://arxiv.org/abs/2610.26193).

**Continuation update 2026-11-04:** the post-sprint search checked [Sargent et al., *Prediction-Powered
Adaptive Inference with Pretrained AI Models for Contextual Bandits* (ICML 2026)](https://proceedings.mlr.press/v306/sargent26a.html).
It integrates pretrained predictions and adaptively collected labels and proves asymptotic
inference for broad Z-functionals. This strengthens the adjacent-work bar for prediction-aware
acquisition, while its stated result does not itself supply the project's finite-sample,
time-uniform replacement-safety guarantee. The active inference, active testing and delayed-feedback
sources were also rechecked against publisher pages. The A5b+C6 deadline-value screen has since
failed its registered cost gate; the budget/deadline scheduler subsection below is therefore closed
as a method lead, not an open development recommendation.

## Cross-cutting finding (read first)

There is already a strong, assumption-light answer to "is the challenger better, valid under
arbitrary dependence". It is the weak-null, time-averaged conditional mean of paired score
differences, from Choe & Ramdas (*Comparing sequential forecasters*) and Henzi & Ziegel (*Valid
sequential inference on probability forecast performance*). These confidence sequences and
e-processes are martingale-based. They need no i.i.d. or Markov assumption because they test
`sum_t E[delta_t | F_{t-1}] <= 0`, not a marginal mean.

The M4 failure ("strong serial dependence inflates promotion") is therefore partly a question of
**which null is being controlled**. Any family-A mechanism that adds a Markov model must say why
the conditional-mean null is the wrong target for false promotion. If it is the right target,
family A is solving a problem those papers have already removed. Under a Markov null, validity
becomes model-dependent, which is a regression in assumptions. Both papers should be required
comparators, ported to IPW-observed paired losses.

---

## (a) Gap-indexed Markov likelihood / running-MLE universal-inference e-processes (A1, A4, A5, D5)

**Nearest prior art (verified)**
- Wasserman, Ramdas, Balakrishnan, *Universal inference*, PNAS 117(29):16880-16890, 2020.
  DOI 10.1073/pnas.1922664117; arXiv:1912.11436. Introduces the split LRT and running-MLE e-values
  for composite nulls, which only need the null MLE to be computable.
- Ramdas, Ruf, Larsson, Koolen, *Testing exchangeability: fork-convexity, supermartingales, and
  e-processes*, Int. J. Approximate Reasoning (accepted); arXiv:2102.00630. A binary-sequence
  e-process built from universal inference and mixtures against **Markovian alternatives** of any
  order. It is an e-process but not a supermartingale.
- Shekhar, *Optimal Anytime-Valid Tests for Composite Nulls*, arXiv:2512.20039, Dec 2025. Shows that
  a universal predictor divided by the running null MLE is an optimal e-process (finite alphabet,
  i.i.d.).
- Saha & Ramdas, *Non-partitioned e-detectors for nonparametric sequential change detection*,
  arXiv:2607.28322, Jul 2026. Takes an infimum over null distributions of point-null e-processes,
  with changes in Markov transition matrices as an explicit example. The repo's prior read notes a
  Markov(p,q) likelihood e-process valid on the full chain without thinning (Prop A.1; partial read).
- Sethi, Sagar, Agrawal, Basu & Karthik, *Asymptotically Optimal Sequential Testing with Markovian
  Data*, ICML 2026, arXiv:2602.17587. Gives an anytime alpha-correct test for a compact composite
  set of finite-state Markov transition matrices, with an asymptotically optimal stopping-time
  result. Its algorithm uses transition counts and a least-favorable KL projection onto the null
  set. It observes a homogeneous Markov trajectory; the paper does not study hard label budgets,
  delayed paired-loss feedback, or predictable outcome-dependent sampling. A fixed, label-independent
  query-gap schedule may make its binary-chain test directly portable and must be checked.
- Kurečka, Andriushchenko, Češka, Paoletti & Novotný, *Anytime-Valid Monitoring of Robust Stochastic
  Models*, arXiv:2610.26193, Oct. 2026. Formalizes betting monitors for rectangular robust models
  and proposes mixtures of linear monitors. It studies runtime model-conformance alarms, not paired
  challenger promotion under paid labels; nevertheless, its anytime-valid monitor construction is
  close prior art for robust Markov-state monitors.
- Kalbfleisch & Lawless, *The analysis of panel data under a Markov assumption*, JASA
  80(392):863-871, 1985. DOI 10.1080/01621459.1985.10478195. This is the classical gap-indexed
  likelihood: a chain observed only at irregular panel times, with the transition probability over
  each gap.

**What is known.** Running-MLE likelihood-ratio e-processes for composite nulls are standard. They
have been instantiated for Markov alternatives (Ramdas et al.) and Markov change detection (Saha &
Ramdas). Likelihoods for Markov chains observed at irregular times (`P^gap`, or `exp(Q*gap)`) are
40 years old.

**What would be new.** After the 2026 update, the narrow open question is whether there is a
substantive contribution beyond the existing composite Markov tests and robust monitors. The
potential difference is combining (i) a composite **null** of first-order binary
Markov loss chains with unknown persistence, (ii) **observation times chosen by the tester's own
predictable query policy**, scored with gap-indexed transition likelihoods, and (iii) a paired
incumbent/challenger promotion decision under a hard query budget and delay. The defensible new
element remains narrow. It is a lemma that the
gap-indexed running-MLE ratio stays an e-process when gaps are predictable, so the missingness is
ignorable for the likelihood because query decisions depend only on observed history. It also
needs a measured or derived advantage over the Sethi et al. composite-Markov test under an acquisition
schedule where that baseline's assumptions hold, and a statement of what this buys over thinning.

**Substantive or renaming?** It is borderline. The validity argument is close to a plug-in of
universal inference into an ignorable-missingness observed-data likelihood. It is substantive only
if one of two things holds. Either (1) the gap-aware e-process has a provable or measured power or
latency gain over thinned and conditional-mean alternatives at matched budget, or (2) the Markov
null is argued to be the correct false-promotion target (see the cross-cutting finding).
Otherwise it is a modelling choice that adds a validity assumption: first-order, stationary,
correctly specified.

**Ablation that would show it matters.** Use the same query schedule (predictable, irregular gaps)
and compare four variants: (i) gap-aware Markov e-process, (ii) gap-ignorant Markov (treats
observed labels as consecutive), (iii) i.i.d. betting e-process, and (iv) Choe-Ramdas
conditional-mean e-process. Report false-promotion rate on rho in {0, .5, .8, .95} nulls,
including misspecified dependence (order-2 AR, regime switching), and promotion latency on
F0_better. Variant (ii) shows that the *gap* part matters. Misspecification shows the cost of the
model.

**Hardest competitor.** Choe & Ramdas (and Henzi & Ziegel) on the conditional-mean null: valid
under arbitrary dependence with no model. On the model-based side, the Saha-Ramdas Markov
likelihood e-process.

## (b) Dependence-robust sequential tests: block/thinned e-values, batch martingales, mixing-based CS (A1, A4 alternatives)

**Nearest prior art (verified)**
- Henzi & Ziegel, *Valid sequential inference on probability forecast performance*, Biometrika
  109(3):647-663, 2022; arXiv:2103.08402. Erratum in Biometrika 109(4):1181-1182: the original
  anytime-valid construction holds only for lag h=1, and a corrected stopping-time construction is
  given for h>1. Lag-h dependence is handled by restructuring the sequence, which is the closest
  verified "thinning" precedent.
- Choe & Ramdas, *Comparing sequential forecasters*, Operations Research 72(4):1368-1387, 2024. DOI
  10.1287/opre.2021.0792; arXiv:2110.00115. Distribution-free CS and e-processes for a time-varying
  forecaster difference.
- Waudby-Smith, Arbour, Sinha, Kennedy, Ramdas, *Time-uniform central limit theory and asymptotic
  confidence sequences*, Ann. Statist. 52(6):2613-2640, 2024. DOI 10.1214/24-AOS2408;
  arXiv:2103.06476. Asymptotic CS via strong approximation.
- Howard, Ramdas, McAuliffe, Sekhon, *Time-uniform, nonparametric, nonasymptotic confidence
  sequences*, Ann. Statist. 49(2):1055-1080, 2021. DOI 10.1214/20-AOS1991; arXiv:1810.08240.
- A blocking-based CS under mixing noise appears in *Linear Bandits with Non-i.i.d. Noise*,
  arXiv:2505.20017. **UNVERIFIED:** authors and venue were not confirmed; only the title and
  blocking idea were seen in search snippets.
- No time-uniform (anytime-valid) CS for Markov-chain means indexed by mixing time was found.
  Fixed-n Markov concentration exists but was not audited here.

**What is known.** Thinning or lag-splitting to restore martingale structure, and martingale CS
that need no independence, are both established.

**What would be new.** Little. A mixing-time-calibrated block or thinning e-value for paired
IPW-observed losses under a label budget could be a lemma, but the conditional-mean route already
gives validity without mixing assumptions.

**Substantive or renaming?** It is mostly tuning (block length, thinning stride). It counts as a
baseline arm, not a contribution.

**Ablation.** Compare block length or stride in {1, 5, 20, 1/(1-rho)} against conditional-mean
e-processes, measuring the validity/latency frontier.

**Hardest competitor.** Choe & Ramdas.

## (c) Active / adaptive query density under autocorrelation (A2, C3, C4)

**Nearest prior art (verified)**
- Chernoff, *Sequential design of experiments*, Ann. Math. Statist., 1959. DOI
  10.1214/aoms/1177706205. **UNVERIFIED:** page range.
- Naghshvar & Javidi, *Active sequential hypothesis testing*, Ann. Statist. 41(6):2703-2738, 2013.
  DOI 10.1214/13-AOS1144; arXiv:1203.4626.
- Reynolds, Amin, Arnold, Nachlas, *X-bar charts with variable sampling intervals*, Technometrics
  30(2):181-192, 1988. DOI 10.1080/00401706.1988.10488366. Adapts the sampling interval to the last
  observation, a direct precedent for adaptive evidence density in monitoring.
- Banerjee & Veeravalli, *Data-efficient quickest change detection in minimax settings*,
  arXiv:1211.3729 (submitted to IEEE TIT; journal reference not shown on the arXiv page). Bayesian
  precursor: arXiv:1105.1361. Uses on/off observation control under an observation-cost
  constraint.
- Xu, Karampatziakis, Mineiro, *Active, anytime-valid risk controlling prediction sets*, NeurIPS
  2024; arXiv:2406.10490. Budgeted optimal labelling policy `q* ∝ sqrt(E[(R-rhat)^2|x])`.
- Zrnic & Candès, *Active statistical inference*, ICML 2024, PMLR 235:62993-63010;
  arXiv:2403.03208.
- Efroni, Merlis, Saha & Mannor, [*Confidence-Budget Matching for Sequential Budgeted Learning*](https://proceedings.mlr.press/v139/efroni21a.html),
  ICML 2021, PMLR 139:2937-2947. Explicit hard query-budget constraints are established in
  sequential bandit and reinforcement-learning settings.
- Verma, Dai & Low, [*Bayesian Optimization under Stochastic Delayed Feedback*](https://proceedings.mlr.press/v162/verma22a.html), ICML 2022,
  PMLR 162:22145-22167. Delayed-feedback acquisition and pending queries are established in
  Bayesian optimization.
- Kossen, Farquhar, Gal, Rainforth, *Active testing: sample-efficient model evaluation*, ICML 2021,
  PMLR 139:5753-5763; arXiv:2103.05331.
- Li, Kadambi, Saidi, Ramamurthy, Dasarathy, Berisha, *Active sequential two-sample testing*, TMLR
  2024; arXiv:2301.12616.

**What is known.** Variance-optimal label allocation (i.i.d.), active inference with a label
budget, hard query budgets in sequential learning, delayed-feedback acquisition, on/off sampling
for change detection, and adaptive sampling intervals in SPC are all established. The checked
primary sources do not by themselves settle the joint contract here: serially dependent paired
loss signs, hard label cap, delayed outcomes, and a time-uniform replacement-safety decision.

**What would be new.** In this scoped primary-source search, we found no paper choosing the label
**spacing** for an anytime-valid test to maximise information per label when consecutive outcomes
are positively autocorrelated. Under
persistence rho, a label taken right after another carries roughly `(1-rho^2)`-discounted
information. The defensible element is a value-of-information rule per label that is a function of
the estimated persistence and the time since the last query, and that stays predictable.

**Substantive or renaming?** It is substantive if it comes with a closed-form or measured
information-per-label gain over uniform pacing and over Xu's q*. If the rule is a tuned schedule
("query less often after a query"), it is a VSI-chart heuristic.

**Ablation.** At matched B=200, compare uniform pacing, Xu q*, a front-loaded schedule, and the
autocorrelation-aware spacing, across rho. Report labels-to-promotion and false promotion. Add a
spacing-oracle row to bound the attainable gain.

**Hardest competitor.** Xu et al. q* (combined with a conditional-mean e-process). On change
detection, DE-CuSum.

**Current disposition (2026-11-04).** This remains a literature-level gap, not a surviving method
lead. Family A's adaptive-spacing A5b and the separate A5b+C6 deadline-value coupling have both
been evaluated; the latter fails its registered cost gate, while A5b does not beat the strongest
same-contract panel. Do not revive a scheduler screen without a distinct policy and a source-level
reason to expect a gain beyond those tested controllers.

The broader adaptive-inference landscape includes Sargent et al. (ICML 2026), which uses pretrained
predictions to improve asymptotic inference under adaptive data collection. It is adjacent rather
than a same-contract comparator: its stated result is not a finite-sample, time-uniform promotion
guarantee with hard label and deployment costs. This remaining contract difference is a research
question, not by itself a novelty claim.

## (d) Restarts, e-detectors, monitoring reserve, certified rollback, multi-timescale (B1-B3, B5, B6, D3, D4)

**Nearest prior art (verified)**
- Shin, Ramdas, Rinaldo, *E-detectors: a nonparametric framework for sequential change detection*,
  arXiv:2203.03532 (reported published in New England J. Statist. Data Sci., 2023). Covers
  e-SR/e-CUSUM and mixtures for statistical and computational efficiency.
- Saha & Ramdas, arXiv:2607.28322 (see (a)), and Saha & Ramdas, *Huber-robust likelihood ratio
  tests for composite nulls and alternatives*, arXiv:2408.14015 (listed as accepted, IEEE TIT).
- Shekhar & Ramdas, *Sequential changepoint detection via backward confidence sequences*, ICML
  2023, PMLR 202:30908-30930; arXiv:2302.02544.
- Banerjee & Veeravalli, data-efficient QCD (see (c)): sampling control with change detection.
- Podkopaev & Ramdas, *Tracking the risk of a deployed model and detecting harmful distribution
  shifts*, ICLR 2022; arXiv:2110.06177.

**What is known.** Restartable SR/CUSUM-type e-detectors, mixtures over start times and scales,
harmful-shift monitoring, and observation-cost-constrained change detection are all known.

**What would be new.** The candidate is a joint budget split between pre-promotion certification
and post-promotion detection (reserve), with a rollback gate that has its own error accounting. No
paper we found couples a hard label budget with both a promotion e-process and a post-promotion
e-detector. Critically, the guarantees differ: ARL or false-alarm probability for detection versus
P(ever falsely promote) for the gate. The claim must state which error each component controls and
how they combine (union bound or alpha-splitting).

**Substantive or renaming?** It is mostly composition and budget tuning. The reserve fraction
{10, 15, 25}% is a hyperparameter. Multi-timescale restarts are an e-detector mixture. The one
substantive piece is a correct joint error statement for promote-then-rollback cycles with
switching cost, if it is proved and not only simulated.

**Ablation.** On reversal and recurrence regimes, compare reserve 0% vs 10/15/25%, rollback on vs
off, single-scale vs multi-scale. Report regret vs oracle, number of switches, and empirical
P(any false promotion or false rollback). Also run on the null to show that the reserve costs
latency there.

**Hardest competitor.** A gated host plus a Shin-Ramdas-Rinaldo e-detector restart, with a fixed
budget split. This is a two-line composition of published parts that the candidate must beat.

## (e) Budget shadow pricing, pending-label credit, deadline-aware acquisition (C1, C2, C5, C6, B4)

**Nearest prior art (verified)**
- Badanidiyuru, Kleinberg, Slivkins, *Bandits with knapsacks*, FOCS 2013. DOI 10.1109/FOCS.2013.30;
  arXiv:1305.2545. Lagrangian/primal-dual resource pricing. **UNVERIFIED:** journal version.
- Xu et al. 2024 and Zrnic & Candès 2024 (see (c)): budget-constrained labelling policies with an
  expected-rate (not hard) budget.
- Joulani, György, Szepesvári, *Online learning under delayed feedback*, ICML 2013, PMLR
  28:1453-1461; arXiv:1306.0686.
- Vernade, Cappé, Perchet, *Stochastic bandit models for delayed conversions*, UAI 2017, PMLR
  R15:730-739; arXiv:1706.09186.
- Desautels, Krause, Burdick, *Parallelizing exploration-exploitation tradeoffs in Gaussian process
  bandit optimization*, JMLR 15:4053-4103, 2014; arXiv:1206.6402. "Hallucinated" observations for
  pending queries, the closest precedent for pending-label credit.
- Lindon & Kallus, *Design-based anytime-valid inference for randomized experiments with delayed
  outcomes and staggered entry*, ICML 2026, PMLR 306:75193-75210. An event-time filtration for
  delayed outcomes.
- Deadline-aware label acquisition for sequential tests: no specific prior art found.

**What is known.** Dual pricing of a budget constraint, delay-robust bandits, crediting pending
feedback when choosing new queries, and filtrations for delayed outcomes are all known.

**What would be new.** A **hard**-budget acquisition rule for an anytime-valid test whose query
probability is a predictable function of (i) a shadow price from remaining budget and horizon,
(ii) information already in flight, and (iii) whether a label can arrive before the decision
deadline. It must keep the e-process valid: q_t is F_{t-1}-measurable and the IPW range is
declared. The REPORT identifies the hard-budget acquisition layer as unspecified in every
certified method (M1), and that is the real gap.

**Substantive or renaming?** Each piece alone is a rename (BwK dual, GP-BUCB hallucination). The
substantive claim is the M1 latency result: certificates arrive about 1/q late under uniform
pacing. A scheduler that provably or measurably closes part of that gap, at matched budget and with
validity intact, would be a contribution to the *acquisition layer*, not to testing.

**Ablation.** Starting from the gated host with uniform pacing, add C2 shadow price alone, C1
pending credit alone, B4 deadline alone, and then all three, at B in {100, 200, 400}. Measure
promotion latency on F0_better, labels wasted (pending duplicates, post-deadline arrivals), and
null false promotion. The REPORT's convergence at B=1000 is a built-in negative control.

**Hardest competitor.** Xu et al. q* with a hard-budget cap, plus a front-loaded schedule
("spend early"), which is trivial to implement.

## (f) Certification gates on fast online model selectors (D1, D2, D4, D6)

**Nearest prior art (verified)**
- Karimi, Gürel, Karlaš, Rausch, Zhang, Krause, *Online active model selection for pre-trained
  classifiers* (Model Picker), AISTATS 2021, PMLR 130:307-315; arXiv:2010.09818.
- Liu, Xia, Stevens, Chen, *Contextual active model selection* (CAMS), NeurIPS 2024; arXiv:2207.06030.
- Okanovic, Kirsch, Kasper, Hoefler, Krause, Gürel, *All models are wrong, some are useful: model
  selection with limited labels* (Model Selector), AISTATS 2025, PMLR 258:2035-2043;
  arXiv:2410.13609.
- Turrin, Okanovic, Hoefler, Gürel, [*Which LLM to pick? Online Active Model Selection for Large
  Language Models*](https://arxiv.org/abs/2610.01592), arXiv preprint submitted 1 Oct 2026. It
  combines stream-wise active model selection with a finite annotation budget and adaptive query
  probabilities based on model-posterior uncertainty. It is a new mandatory acquisition baseline;
  its model-identification/regret objective is not automatically a time-uniform replacement-safety
  certificate.
- Karampatziakis, Mineiro, Ramdas, *Off-policy confidence sequences*, ICML 2021, PMLR
  139:5301-5310; arXiv:2102.09540. Includes a **gated deployment** application.
- Johari, Koomen, Pekelis, Walsh, *Always valid inference: continuous monitoring of A/B tests*,
  Operations Research 70(3):1806-1821, 2022. DOI 10.1287/opre.2021.2135; arXiv:1512.04922.
- Howard et al. 2021 (see (b)); Lindon & Malek, *Anytime-valid inference for multinomial count
  data*, NeurIPS 2022; arXiv:2011.03567 (includes canary testing); Lindon & Kallus 2026 (see (e)).
- Digalakis, Pérignon, Saurin, Sentenac, *The Challenger: when do new data sources justify
  switching machine learning models?*, arXiv:2512.18390.

**What is known.** Active selectors give regret or PAC identification, not anytime false-promotion
control. Model Selector (2025) and Online LLM Picker (Oct 2026) also strengthen the label-budgeted
selection baseline. Anytime-valid gating of a candidate policy (Karampatziakis et al.) and
always-valid A/B or canary testing are standard.

**What would be new.** "The selector proposes, an anytime certificate disposes": the gate reuses
the selector's own (predictable) query probabilities as IPW weights, so certification costs no
extra labels. The defensible element is the measured M2 finding: all eight uncertified families
falsely promote on 64-100% of null streams. The other part is a host-agnostic wrapper (D6) whose
validity follows from predictability of the host's query rule.

**Substantive or renaming?** The method is composition. Validity comes from the gate, and the
gate is published. It is substantive as a **benchmark/negative finding** and as a transfer result
(D6) only if the wrapper keeps most of the selector's speed. Otherwise it is "gated deployment with
a different proposal".

**Ablation.** For each host, compare host alone, host plus gate (shared labels), host plus gate
(separate gate labels), and the gate alone with uniform proposal. Report false-promotion rate,
switches, and latency. If gate-alone matches host-plus-gate, the selector contributes nothing.

**Hardest competitor.** Karampatziakis et al. gated deployment with the stronger `wmax_t = 1/q_t`
re-port (already in the REPORT).

## (g) Anytime-valid deployment across retrained challenger versions (new research lead)

**Nearest prior art (verified 2026-11-04)**
- Digalakis et al., [*The Challenger: When Do New Data Sources Justify Switching Machine Learning
  Models?*](https://arxiv.org/abs/2512.18390), v2 dated July 2026. Repeated challenger training,
  switching economics, a sequential evaluation algorithm and chronological credit-scoring results.
- Karimi et al., [*Online Active Model Selection for Pre-trained Classifiers*](https://proceedings.mlr.press/v130/reza-karimi21a.html),
  AISTATS 2021. Active label requests and high-probability identification among a fixed model set.
- Turrin et al., [*Which LLM to pick? Online Active Model Selection for Large Language Models*](https://arxiv.org/abs/2610.01592),
  arXiv 2026. Online streaming selection with a finite annotation budget and uncertainty-driven
  query probabilities; include it or a faithful classifier-domain adaptation as a strong active
  baseline.
- Lindon & Kallus, [*Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed
  Outcomes and Staggered Entry*](https://proceedings.mlr.press/v306/lindon26a.html), ICML 2026. Delayed
  outcome anytime-valid confidence sequences under treatment assignment and arm-specific
  event-time filtrations.
- Sethi et al. and Kurečka et al. as listed in (a); relevant to dependence-robust testing and
  monitoring, respectively.

**Potential gap.** Sequentially retrained versions may be selected using past history, then
certified on fresh future paired losses under a shared selective-label budget and delayed feedback.
One possible construction assigns a summable alpha share to each predictably activated version,
tags queried outcomes to the version at issue time, and runs a version-specific started e-process.
The theorem would require conditional validity after the model-selection history and strict
separation between training outcomes and that version's certification outcomes. A union bound over
versions alone does not solve evaluation-data reuse or serial dependence.

**Substantive or renaming?** Unknown. The ingredients are individually established, and composition
alone is insufficient. Retain only if a proof for adaptive versions under delayed selective feedback
and a measured gain over *The Challenger*, RMM and fixed-model active selection are both delivered.
The candidate specification is in
[`versioned_challenger_candidate.md`](versioned_challenger_candidate.md). No implementation or
performance result supports this claim yet.

## (h) Closest certified competitors overall

Verified:
- Karampatziakis et al. 2021 (above).
- Waudby-Smith, Wu, Ramdas, Karampatziakis, Mineiro, *Anytime-valid off-policy inference for
  contextual bandits*, arXiv:2210.10768. No known bound on importance weights is needed. This is
  directly relevant to the declared-HT-range cap the REPORT blames for part of M1.
- Balachandran, *Pay only for disagreement: certified no-regression verdicts for model updates*
  (DISCERN), arXiv:2609.17560, Jul 2026 (v1, single author, not peer-reviewed as far as seen). The
  REPORT records a `/4` omission in our port's `psi_E`, which is now fixed.
- Xu, Karampatziakis, Mineiro 2024 (above).
- Arnold, Gavrilopoulos, Schulz, Ziegel, *Sequential model confidence sets*, arXiv:2404.18678;
  reported in JRSSB 2026, DOI 10.1093/jrsssb/qkag066. Author list and version varied across
  records, so cite the arXiv record.
- Choe & Ramdas 2024; Henzi & Ziegel 2022; Podkopaev & Ramdas 2022; Chugg, Cortes-Gomez, Wilder,
  Ramdas, *Auditing fairness by betting*, NeurIPS 2023, arXiv:2305.17570 (betting audit with a
  probabilistic data-collection policy). Waudby-Smith & Ramdas, *Estimating means of bounded random
  variables by betting*, JRSSB 2024, DOI 10.1093/jrsssb/qkad009; arXiv:2010.09686.
- Prabhu, Bhashyam, Gopalan, Sundaresan, *Sequential multi-hypothesis testing in multi-armed bandit
  problems: an approach for asymptotic optimality*, IEEE TIT 68(7):4790-4817, 2022; DOI
  10.1109/TIT.2022.3159600; arXiv:2007.12961. Covers switching cost plus a false-detection
  constraint, a close formal analogue of "switching cost + false promotion".

**Recommendation.** Add Choe-Ramdas (conditional-mean paired e-process, IPW-adapted) and
Waudby-Smith et al. 2022 (no weight-bound requirement) as required certified comparators. They
target M4 and the HT-range part of M1 respectively, and neither appears in the REPORT's competitor
list.

---

## Summary table

| mechanism | nearest prior art | smallest defensible novel element | substantive? | hardest competitor | required ablation |
|---|---|---|---|---|---|
| (a) gap-indexed Markov running-MLE e-process | Wasserman+ 2020; Ramdas+ 2102.00630; Saha-Ramdas 2607.28322; Sethi+ ICML 2026; Kurečka+ 2026; Kalbfleisch-Lawless 1985 | validity lemma for running-MLE e-process under a Markov composite null with **predictable, policy-chosen gaps** in a paired promotion test | borderline; it adds a model assumption, and is substantive only with a gain over conditional-mean and composite-Markov baselines | Choe-Ramdas conditional-mean e-process; Sethi et al. composite-Markov test | gap-aware vs gap-ignorant vs i.i.d. vs Choe-Ramdas vs Sethi et al., matched acquisition, rho grid plus misspecified dependence |
| (b) block/thinned/mixing CS | Henzi-Ziegel 2022 (+erratum); Choe-Ramdas 2024; Waudby-Smith+ 2024 | none beyond a stride lemma | no (tuning) | Choe-Ramdas | stride/block grid vs conditional-mean e-process |
| (c) autocorrelation-aware query density | Chernoff 1959; Naghshvar-Javidi 2013; VSI charts 1988; DE-CuSum; Xu+ 2024 | info-per-label spacing rule as a function of persistence and time since last query, predictable | yes if gain is shown or derived; otherwise VSI heuristic | Xu+ q* | uniform / Xu q* / front-load / spacing / oracle at B=200 across rho |
| (d) reserve, rollback, multi-timescale restarts | Shin-Ramdas-Rinaldo; Saha-Ramdas; Shekhar-Ramdas 2023; Banerjee-Veeravalli | joint error statement for promote-then-rollback under a hard shared budget | mostly composition; the error statement is the only substantive part | gated host + e-detector with fixed split | reserve 0/10/15/25%, rollback on/off, single vs multi-scale, plus null cost |
| (e) shadow price, pending credit, deadline | BwK 2013; Joulani+ 2013; Vernade+ 2017; Desautels+ 2014; Lindon-Kallus 2026 | hard-budget, predictable acquisition layer that reduces the 1/q certification lag (M1) with validity kept | pieces are renames; the M1-closing scheduler is substantive | Xu q* with hard cap; naive front-load | one-at-a-time add C2/C1/B4 at B in {100, 200, 400}; B=1000 negative control |
| (f) certify fast selectors | Model Picker 2021; CAMS 2024; Model Selector 2025; Karampatziakis+ 2021; Johari+ 2022 | shared-label gate wrapper (D6) plus M2 benchmark finding | as a method, composition; as a finding, yes | gated deployment (`wmax=1/q`) | host / host+gate shared / host+gate separate / gate alone |
| (g) certified competitors | Karampatziakis+; Waudby-Smith+ 2210.10768; DISCERN; Xu+; SMCS | n/a | n/a | add Choe-Ramdas and Waudby-Smith+ 2022 to the comparator set | n/a |

UNVERIFIED items: authors and venue of arXiv:2505.20017; JACM version of BwK; Chernoff 1959 page
range; IEEE TIT journal reference of Banerjee-Veeravalli minimax (the arXiv page shows submission
only); Saha-Ramdas 2607.28322 Prop A.1 content (repo partial read, not re-read here).
