# Sprint 2 novelty and prior-art audit (Agent H)

2026-11-04. This extends [the sprint-1 audit](../../sota_sprint/novelty_audit.md) and does not repeat
it. Citations verified there (Wasserman et al. 2020; Ramdas et al. 2102.00630; Shekhar 2512.20039;
Saha & Ramdas 2607.28322; Kalbfleisch & Lawless 1985; Henzi & Ziegel 2022; Choe & Ramdas 2024;
Howard et al. 2021; Waudby-Smith et al. 2024; Johari et al. 2022; Karampatziakis et al. 2021;
Shin-Ramdas-Rinaldo; Shekhar & Ramdas 2023; Banerjee & Veeravalli; Podkopaev & Ramdas 2022; Xu et
al. 2024; CAMS; Model Picker; Model Selector; DISCERN; SMCS; Lindon & Kallus 2026; Digalakis et al.)
are cited by short name only.

**How the new citations were checked.** Each entry below marked (v) was confirmed on 2026-11-04 from
the arXiv abstract page, the publisher or society record, RePEc/EconPapers, PMLR, JMLR or a
bibliographic search hit that gave the publisher record. Two text claims about Henzi & Ziegel and
Choe & Ramdas were checked against the full arXiv PDFs (text extracted locally). **UNVERIFIED**
marks anything not confirmed. This is a literature audit only. It contains no empirical result.
"No prior art found" means our searches (web, arXiv, publisher records) returned nothing. It does
not show that nothing exists.

---

## Headline finding: the conditional-versus-unconditional distinction behind P2 is already established

The framing that sprint 1 treated as P2's conceptual core ("the certificates control the
conditional, episode-level null; the violation is of the marginal null") is **already the central
distinction of the forecast-comparison literature**, and it has already been carried into the
anytime-valid setting.

1. **Giacomini & White (2006)** (v), *Tests of conditional predictive ability*, Econometrica
   74(6):1545-1578, DOI 10.1111/j.1468-0262.2006.00718.x. They separate *unconditional* predictive
   ability (Diebold-Mariano/West: which forecast was more accurate on average, `E[d_t]=0`) from
   *conditional* predictive ability (`E[d_{t+1} | F_t] = 0`, which forecast will be more accurate
   given current information). They argue that the conditional question is the relevant one for
   forecast *selection*, and they give a two-step decision rule that uses current information to
   choose the forecast.
2. **Henzi & Ziegel (2022)** (v, full text checked). The anytime-valid e-values test *conditional
   forecast dominance*, `E_Q[S(p_t,Y)-S(q_t,Y) | F_t] <= 0` at every t. The paper says explicitly
   that this notion "has been introduced by Giacomini and White (2006)". It also says that choosing
   the e-value alternative plays the role of GW's `F_t`-measurable test functions, and that the
   e-value, unlike GW, stays valid under any adapted choice.
3. **Choe & Ramdas (2024)** (v, full text checked). This paper tests the *weak* null, a time-average
   of conditional means. It compares itself directly with DM and GW (its Section H and its Table 1).
   Its footnote 3 notes that Ehm & Krüger (2018) separate tests of *average* from tests of
   *step-by-step* conditional predictive ability, "which mirrors that of weak and strong nulls".
4. **Zhu & Timmermann**, *Can two forecasts have the same conditional expected accuracy?*,
   arXiv:2006.03238 (v; journal version **UNVERIFIED**). The conditional loss differential is a
   martingale difference only when the outcome is the simple average of the two forecasts. The GW
   null of *equal* conditional accuracy therefore essentially never holds. This is a one-sided-null
   caveat that Henzi & Ziegel also cite.
5. **Ehm & Krüger**, *Forecast dominance testing via sign randomization*, Electron. J. Statist.
   12(2):3758-3793, 2018, DOI 10.1214/18-EJS1495 (v).

**Consequence for P2.** "Conditional vs marginal null" cannot be claimed as a new insight. A
reviewer from econometrics or from the Ramdas group will see P2's twin-null result as GW versus DM,
restated for deployment gates. The defensible novelty is narrower and is set out in §2.

---

## 1. P1 / RMM: restart monitoring as a transferable add-on for certified deployment gates

### Closest prior art (new beyond sprint 1)

- **Detector-triggered restarts of a learner.** This is the structural analogue of "monitor, alarm,
  restart the host".
  - Cao, Wen, Kveton, Xie, *Nearly optimal adaptive procedure with change detection for
    piecewise-stationary bandit* (M-UCB), AISTATS 2019, PMLR 89:418-427; arXiv:1802.03692 (v).
  - Besson, Kaufmann, Maillard, Seznec, *Efficient change-point detection for tackling
    piecewise-stationary bandits* (GLR-klUCB), JMLR 23(77):1-40, 2022; arXiv:1902.01575 (v).
  - These restart a regret-minimising policy, not a certificate. They give no false-promotion
    control, but they set the template the reviewers will cite.
- **Monitoring after an initial decision (econometrics).**
  - Chu, Stinchcombe, White, *Monitoring structural change*, Econometrica 64(5):1045-1065, 1996
    (v). Real-time monitoring with asymptotic size control, after a historical training sample.
  - Giacomini & Rossi, *Forecast comparisons in unstable environments*, J. Appl. Econometrics
    25(4):595-620, 2010, DOI 10.1002/jae.1177 (v). Its Fluctuation and One-Time Reversal tests
    target the time-varying *relative* performance of two models, which is exactly "late
    improvement / reversal". It is a fixed-sample (historical) test, not sequential.
  - Golosnoy & Okhrin, *Nonparametric monitoring of equal predictive ability*, J. Statist. Plann.
    Inference 141(9), 2011 (v; pages **UNVERIFIED**). Sequential online monitoring of EPA, designed
    to signal that an initially assumed EPA no longer holds.
  - Inoue & Rossi, *Recursive predictability tests for real-time data*, JBES 23:336-345, 2005 (v).
- **Industry staged rollout with monitoring.**
  - Zhao, Liu, Deb, *Safely and quickly deploying new features with a staged rollout framework using
    sequential test and adaptive experimental design*, arXiv:1905.10493 (v; the Uber blog lists
    ICCIA 2018, venue **UNVERIFIED**). SPRT monitoring during ramp-up.
  - Lindon & Kallus 2026 (canary/delayed outcomes).
  - Johari et al. 2022.
- **MLOps / drift-to-action, with budgeted labels and anytime-valid certificates.**
  - Lamaakal, Yahyati, El Makkaoui, Ouahbi, Maleh, *Drift-to-Action Controllers: budgeted
    interventions with online risk certificates* (Drift2Act), arXiv:2603.08578, ICLR 2026 CAO
    workshop (v). Delayed labels from a recent window give an anytime-valid upper bound on current
    risk. That bound gates an escalation to adapt, abstain, roll back or retrain, under intervention
    costs.
  - **This is the closest MLOps competitor found.** It certifies the incumbent's *absolute* risk,
    not a paired challenger advantage, and it has no restart mixture or cross-host transfer.
- **Negative corroboration.**
  - Han & Qu, *When the martingale never stops firing: anytime-valid gating on real forecast
    streams*, arXiv:2608.30502, Aug 2026 (v). A conformal test martingale gate fired in 135/135 clean
    real-stream runs, against ≤1/60 on synthetic exchangeable streams. The authors blame dependence
    in the deployed score stream and ask for null-calibration controls.
  - Li, *Who drifted: the system or the judge?*, arXiv:2606.15474, Jun 2026 (v). A betting-e-process
    monitor for LLM evaluation pipelines. A rolling z-test false-alarms on 75% of drift-free streams.
  - Together these mean "anytime-valid monitors break on real dependent streams" is **already in
    the 2026 literature**. RMM's twin-null failure (.14-.62) is consistent with them, not a
    discovery.
- **Tooling.** The CRAN package `edetect` 0.1.0 implements Shin-Ramdas-Rinaldo e-detectors (v,
  CRAN r-universe page). An off-the-shelf e-detector is therefore a trivial competitor to wire in.

**Searches that returned nothing.**
- A paper attaching a restart e-detector to an *anytime-valid A/B or deployment certificate* after
  its verdict, under a shared hard label budget.
- A paper evaluating any monitoring add-on *across multiple certificate families*.

The sprint-1 claim "no paper evaluates restart detectors as a deployment add-on across certificate
families" survives this round.

### Exact delta

RMM is a composition: an SR-type mixture of label-clock e-processes (Shin-Ramdas-Rinaldo) plus
continued post-verdict acquisition, plus a host restart and an alpha split. What is new is the
operating point:
- it works on query-conditional, unweighted outcomes on the label clock;
- it shares the host's hard budget;
- it attaches to any certificate.

The measured transfer across four certificate families is also new. Sprint-1 ablations attribute
more of the gain to *continued acquisition* (−8 to −11) than to the *restart mixture* (−2.4 to
−5.5). The most novel-looking component is therefore the least important one.

### Substantive or incremental?

**Incremental as a method.** The design is composition. Its failures (ρ=.8 at .12-.18, twins
.14-.62, reversal) are the failure mode Han & Qu document. It becomes substantive only with one of
two additions:
- a proved joint error statement for promote → monitor → restart cycles, combining false promotion
  with the detector's ARL or PFA under the alpha split. No such statement was found in the
  literature, and none exists in the repo;
- a demonstration that the post-verdict acquisition schedule is *the* fix for the M1 latency
  diagnosis, across hosts, on a real late-improvement stream.

### Hardest competitor to include

The host plus an off-the-shelf **Shin-Ramdas-Rinaldo e-CUSUM/e-SR detector** (e.g. `edetect`'s
Bernoulli/bounded detector), with:
- the same alpha split;
- the same post-verdict acquisition rate;
- the same restart rule.

This isolates RMM's specific mixture. Also include a **GLR-klUCB-style Bernoulli GLR restart**
(Besson et al.) as the uncertified restart reference, and Giacomini-Rossi's One-Time Reversal test
as an offline oracle diagnostic of whether a late reversal exists in a real stream.

### Ablation needed

On the same certificate hosts and budget, run a 2×3 grid:
- {continued acquisition on/off} × {no detector, off-the-shelf e-detector, RMM mixture};
- plus label-clock vs wall-clock indexing.

Report:
- late-improvement J;
- reversal J;
- iid, ρ=.8 and twin-null promotion.

If "off-the-shelf detector + continued acquisition" is within noise of RMM, the contribution is
"keep sampling after the verdict", and it should be written that way.

### Follow-up status (2026-11-04)

The Giacomini–Rossi One-time Reversal diagnostic was implemented post hoc on all 348 non-twin WP1
episodes (`docs/sprint2/wp1/gr_one_time_reversal.json`). A post hoc label-clock vs elapsed-timestamp
start-grid replay covers 62 episodes across five timestamped fresh UCI streams
(`clock_ablation_posthoc3.md/json`); equal-dataset mean ΔJ is −0.61 (five-dataset cluster-bootstrap
95% CI [−5.85, +2.41]). This is exploratory, uses the known episode endpoint to lay out starts, and
does not model publication-time delay. Nine cached streams lack elapsed-time fields, so the real-data
comparison remains incomplete. The GR diagnostic also reuses outcomes that defined WP1 classes and
does not establish the paper's asymptotic assumptions.

---

## 2. P2: conditional vs marginal nulls in sequential model comparison under dependence

### Closest prior art

- **Conditional/unconditional framing:** Giacomini & White 2006; Henzi & Ziegel 2022; Choe & Ramdas
  2024; Ehm & Krüger 2018; Zhu & Timmermann (see the headline finding).
- **Unconditional EPA under serial dependence (HAC):**
  - Diebold & Mariano, *Comparing predictive accuracy*, JBES 13(3):253-263, 1995 (v). Serially
    correlated loss differentials are allowed via the long-run variance.
  - West, *Asymptotic inference about predictive ability*, Econometrica 64(5):1067-1084, 1996 (v).
  - Coroneo & Iacone, *Comparing predictive accuracy in small samples using fixed-smoothing
    asymptotics*, J. Appl. Econometrics 35(4):391-409, 2020, DOI 10.1002/jae.2756 (v). Size control
    of DM with few observations.
  - Newey-West HAC itself was not re-verified (**UNVERIFIED** citation details).
- **Sequential / monitoring versions:** Chu-Stinchcombe-White 1996; Inoue & Rossi 2005; Golosnoy &
  Okhrin 2011; Giacomini & Rossi 2010 (all v, §1). None is anytime-valid in the Ville sense. Their
  validity is asymptotic and mixing-based.
- **Anytime-valid inference under dependence:**
  - Martingale (conditional) constructions need no mixing: Henzi-Ziegel, Choe-Ramdas.
  - Choe & Ramdas, *Combining evidence across filtrations*, arXiv:2402.09698, accepted JRSSB (v).
    Its adjusters move e-processes from a coarsened to the original filtration at a logarithmic
    cost. This is the formal tool for "thinned or coarsened evidence".
  - Han & Qu 2026 (v) give real-stream failure evidence.
  - A time-uniform CS for the *marginal* mean of a mixing or Markov process: none found again.
- **Impossibility background for the marginal null:**
  - Bahadur & Savage, *The nonexistence of certain statistical procedures in nonparametric
    problems*, Ann. Math. Statist. 27(4):1115-1122, 1956, DOI 10.1214/aoms/1177728077 (v). Even for
    i.i.d. data, no non-trivial test of a mean exists over an unrestricted nonparametric class.
  - Ryabko, *A criterion for hypothesis testing for stationary processes*, arXiv:0905.4937, and
    *Uniform hypothesis testing for ergodic time series distributions*, arXiv:1107.4165 (v as arXiv
    records; journal versions **UNVERIFIED**). These characterise when consistent and uniformly
    consistent tests exist for stationary ergodic classes.
- **Known-null / placebo designs in ML evaluation:**
  - Dietterich, *Approximate statistical tests for comparing supervised classification learning
    algorithms*, Neural Computation 10(7):1895-1923, 1998 (v). Type-I error is measured with
    known-null simulations.
  - Bouthillier et al., *Accounting for variance in machine learning benchmarks*, MLSys 2021;
    arXiv:2103.03098 (v). Retraining randomness is a variance source.
  - A/A tests in online experimentation: Kohavi & Longbotham 2010 (title and venue **UNVERIFIED**;
    only secondary sources were seen).

### What is already known (the delta has to be cut against this)

- **The two nulls are distinct, and the conditional one is the decision-relevant one for
  selection.** GW 2006 says so explicitly.
- **Anytime-valid tests of the conditional null exist and are assumption-free.** Henzi-Ziegel,
  Choe-Ramdas.
- **Tests of the unconditional null under dependence are asymptotic and mixing-based.** DM, West
  and Coroneo-Iacone are fixed-sample. Chu-Stinchcombe-White and Golosnoy-Okhrin are sequential
  but asymptotic.
- **Equal conditional accuracy almost never holds.** Zhu & Timmermann.
- **Nonparametric mean tests can be impossible.** Bahadur-Savage; Ryabko.

### Exact delta (what survives)

1. **The twin construction is a known-unconditional-null under which the conditional null provably
   fails.** Two identically specified models are trained on random disjoint halves, and a coin
   assigns the incumbent. Unconditional equality then holds exactly by symmetry over the
   randomisation. In any realised episode, though, one twin is conditionally better (the Zhu &
   Timmermann phenomenon, made concrete).
   - Against the conditional null, a certificate that promotes in a twin episode is therefore
     *not* making an error.
   - This is the cleanest reframing of the K1 result, and a reviewer will push it. The K1 "failure"
     of nine powered ports is largely those ports correctly detecting GW-conditional advantage.
   - Sprint-1's harm numbers support this: promotions go toward the twin with lower realised loss,
     and the harmful-promotion rate is ≤ .018 (Xu) and ≤ .072 (SMCS).
   - **New:** a real-stream construction that separates the two nulls exactly, used to calibrate
     *which* null each deployment certificate controls. Dietterich and A/A tests use known nulls
     only under i.i.d. resampling or randomisation. We found no use of independently retrained
     twins on persistent temporal streams.
2. **The budgeted, actively queried, delayed-label deployment context.** Here IPW or
   query-conditional outcomes and gap-indexed observation interact with persistence. In
   econometrics the loss differential is observed at every t, with no label budget and no
   predictable missingness. This context is new but incremental.
3. **An economic-cost and predictive-loss accounting.** The twin results separately report paired
   prediction-loss changes and all-in excess economic cost versus never-switch; the latter includes
   label and switching expenditure. Neither quantity identifies application-level decision harm,
   because the records contain no causal application utility.
   - This supports a measured tradeoff between predictive performance and monitoring/deployment
     expenditure under the twin construction. It does not convert marginal-size violations into a
     claim of small application-level harm.
   - The paper should describe which null a certificate controls and report predictive and
     accounting outcomes separately, while leaving decision utility unclaimed.
4. **The lower-bound item (register item 1).** "Any test valid for all ρ ≤ 1 needs evidence growing
   with run changes" is close in spirit to Bahadur-Savage/Ryabko non-existence, and to the
   transition-structure dependence of the stopping-time lower bound in Sethi et al. 2026 (§3).
   - A clean version for a binary first-order Markov composite null with predictable query gaps
     would be a lemma-level contribution.
   - It should be proved by reduction to Sethi et al.'s lower bound or to a two-point argument, and
     framed as an instance of known non-existence, not as a new impossibility theorem.

### Substantive or incremental?

The conceptual distinction is **not new** (GW 2006). The substantive possibility is a **benchmark
and methodology paper**, built from three parts:
- the twin construction as an exact known-null on real persistent streams;
- a "null-tested" ledger (V1/V2/V3) that scores every published certificate against the null it
  actually controls;
- predictive-loss and all-in excess economic-cost accounting (not application-level decision harm).

This is a credible datasets-and-benchmarks or empirical contribution. As a main-track methods paper
it is weak unless the lower bound is proved.

### Hardest competitor to include

- **Conditional side:** Henzi-Ziegel strong-null e-values and Choe-Ramdas weak-null e-process,
  IPW-ported (already partly in the repo as `choe_ramdas_eb`; sprint 1 noted the port is
  query-conditional, not the all-events IPW version, so a faithful all-events IPW port is still
  owed).
- **Marginal side:** a **sequential DM/GW monitor** (Chu-Stinchcombe-White boundary or
  Golosnoy-Okhrin control chart on HAC- or fixed-b-studentised loss differentials). It has
  asymptotic size, but it is the econometrician's default, and reviewers will ask why A5b beats it.
- **End-of-horizon diagnostic:** a fixed-sample DM with Coroneo-Iacone fixed-b, run on the observed
  differentials.

### Ablation needed

- Run every certificate on the same streams under three nulls:
  - V1 conditional: a synthetic stream with `E[d_t|F_{t-1}]≤0` for all t and persistent noise;
  - V2 marginal: twins and a stationary Markov null;
  - V3 economic.
- Report a 3×K violation matrix. The claim is that the pattern is block-diagonal: each method holds
  only its own null.
- Add a *conditional oracle* that knows the episode-level advantage, to measure how much of the twin
  "violation" is correct conditional detection.
- Add HAC-DM sequential monitoring as the marginal baseline.

---

## 3. A5b: gap-indexed Markov sequential universal inference and recovering its power

### Closest prior art (new beyond sprint 1)

- Sethi, Sagar, Agrawal, Basu, Karthik, *Asymptotically optimal sequential testing with Markovian
  data*, arXiv:2602.17587, ICML 2026 (v).
  - α-correct sequential tests for an ergodic finite-state chain with a **composite null set of
    transition matrices**.
  - Gives an instance-dependent lower bound on expected stopping time that depends on both the
    stationary distribution and the transition structure, with a matching test.
  - **This is the most important new citation for A5b.** It is both the strongest competitor and
    the tool for a lower bound.
- Larsson, Ramdas, Ruf, *The numeraire e-variable and reverse information projection*, Ann.
  Statist. 53(3):1015-1043, 2025; arXiv:2402.18810 (v). The log-optimal e-variable for composite
  nulls dominates universal inference's running-MLE denominator.
- Ramdas & Wang, *Hypothesis testing with e-values*, arXiv:2410.23614 (v). Covers UI e-processes
  and the dominance of UI by the numeraire.
- Choe & Ramdas 2402.09698 (v). The adjuster cost of coarsening or thinning.
- No paper found on an anytime-valid test of the *mean* of a Markov chain with unknown persistence,
  apart from Sethi et al.'s transition-matrix formulation.

### Exact delta

A5b's validity follows from running-MLE UI under ignorable, predictable missingness. Sprint 1
called this a borderline plug-in. Sethi et al. now cover composite Markov nulls with an optimal
test, so the delta shrinks to two things:
- **gap-indexed observation** chosen by the tester's own query policy, which Sethi et al. do not
  have (they observe every step);
- **the paired deployment setting.**

### Can power be recovered?

The free-ρ composite null *is* the source of the power loss. A long run of challenger wins is
explained by ρ→1. Any valid test of that null must pay, and the Sethi et al. bound should quantify
the payment. The options:

1. **Replace the running MLE with the numeraire/RIPr or a mixture denominator.** This is a strict
   improvement in growth rate, but bounded by the same lower bound. It is incremental.
2. **Restrict the null to ρ ≤ ρ_max (declared).** This buys power by adding an assumption, and the
   real streams have ρ̂ up to .98, so it is not credible as a fix.
3. **Use Sethi et al.'s optimal test as the evidence process,** adapted to gaps. This is the best
   power-recovery route and the strongest competitor. If A5b already sits near their bound, the
   power loss becomes a *theorem-backed* finding for P2, which is more valuable than any recovery
   heuristic.
4. **Change the null to V1 (conditional).** Not a recovery: it is a different hypothesis.

### Substantive or incremental?

**Incremental as a method.** It is substantive only as "A5b is near the Sethi et al. lower bound
under gaps, so dependence-robust marginal certification is provably slow". That result belongs
inside P2.

### Hardest competitor to include

Sethi et al.'s optimal Markov-composite sequential test (gap-aware port), and the numeraire variant
of A5b.

### Ablation needed

- Compare A5b-UI, A5b-numeraire/mixture and the Sethi-style test, all on the same predictable query
  schedule.
- Plot each against the Sethi lower bound, computed on the fitted chain, across ρ ∈ {0, .5, .8, .95}
  on F0_better and on real replays.
- Include the gap-ignorant variant, which sprint 1 asked for and is still needed.

---

## 4. D2: CAMS plus an anytime certification gate, and risk-calibrated cost-risk frontiers

### Closest prior art

- Composition parts (sprint 1): CAMS; Karampatziakis et al. gated deployment; Xu et al. active
  anytime-valid RCPS.
- Drift2Act (arXiv:2603.08578, v). A budgeted-label anytime-valid gate in front of interventions.
- **Risk calibration and frontiers:**
  - Angelopoulos, Bates, Candès, Jordan, Lei, *Learn then Test*, arXiv:2110.01052; Ann. Appl.
    Statist. 2025, DOI 10.1214/24-AOAS1998 (v from listing; volume/pages **UNVERIFIED**).
  - Laufer-Goldshtein, Fisch, Barzilay, Jaakkola, *Efficiently controlling multiple risks with
    Pareto testing*, ICLR 2023; arXiv:2210.07913 (v). Candidates on a cost-risk Pareto front, then
    tested.
  - Bates, Angelopoulos, Lei, Malik, Jordan, *Distribution-free, risk-controlling prediction sets*,
    J. ACM 68(6):43, 2021, DOI 10.1145/3478535 (v).

### Exact delta

Track R calibrates each method's alpha on simulated development nulls and reports empirical
cost-risk curves. LTT and Pareto testing do the same operation *with* a finite-sample guarantee on
exchangeable calibration data. Ours has no guarantee: the SPEC says so, and the calibration nulls
are simulator nulls, not draws from the deployment distribution. It amounts to a parametric
bootstrap calibration of a sequential threshold.

The D2 method itself (selector proposes, gate disposes, labels shared) is composition. Sprint-1
evidence:
- the 4/5 real-data advantage did not replicate on new seeds;
- ρ=.8 null promotion is .20-.23.

### Substantive or incremental?

**Incremental.** The cost-risk frontier is an evaluation device, not a contribution. Do not
describe it as "risk-calibrated certification".

### Hardest competitor to include

- Gated deployment with Xu q* acquisition, calibrated on the same development nulls.
- An LTT/Pareto-testing calibration of the gate threshold on *held-out real twin streams*. That
  would give the honest, guaranteed version of Track R wherever exchangeability across streams is
  defensible.

### Ablation needed

- Host alone, host+gate with shared labels, host+gate with separate labels, and gate alone with a
  uniform proposal (sprint 1 already asked for these).
- The same four at matched empirical risk (Track R), to see whether CAMS adds anything once alpha
  is recalibrated.

---

## 5. Risk-aware economic deployment (expected value of switching, risk penalty, optimal stopping)

### Closest prior art

- Feit & Berman, *Test & Roll: profit-maximizing A/B tests*, Marketing Science 38(6):1038-1058,
  2019; arXiv:1811.00457 (v). The test is a trade-off between the opportunity cost of testing and
  the loss from deploying the worse arm. It gives a closed-form profit-maximising sample size,
  smaller than hypothesis-testing sizes, with near-Thompson regret.
- Chick, Forster, Pertile, *A Bayesian decision-theoretic model of sequential experimentation with
  delayed response*, JRSSB 79(5):1439-1462, 2017, DOI 10.1111/rssb.12225 (v).
  - Fully sequential, delayed outcomes, an adoption decision net of sampling cost, and stopping
    boundaries that depend on the delay.
  - **This is the closest formal match to our contract (delay + sampling cost + one adoption
    decision).**
- Azevedo, Deng, Montiel Olea, Rao, Weyl, *A/B testing with fat tails*, J. Political Economy
  128(12):4614-4672, 2020, DOI 10.1086/710607 (v).
- Rust, *Optimal replacement of GMC bus engines*, Econometrica 55(5):999-1033, 1987 (v). The
  canonical optimal-stopping replacement model.
- Mahadevan & Mathioudakis, *Cost-effective retraining of machine learning models*,
  arXiv:2310.04216 (v; no venue listed). Online retrain-or-keep under staleness and retraining
  costs.
- Malekipirbazari, risk-averse bandits with switching penalties (Risk-Averse Switching Index),
  EJOR 321(1):160-176, 2025 (v from RePEc; author list beyond the first **UNVERIFIED**).
- Digalakis et al., *The Challenger* (sprint 1).

### Exact delta

J = loss + c_q·labels + c_s·switches with a risk penalty is standard decision theory. Chick et al.
already solve the delay-plus-sampling-cost adoption problem in Bayesian form. Test & Roll already
argues that profit, not size, should set the test. What remains possibly new is the
**combination**: an economic objective that keeps an *anytime-valid* false-promotion constraint
under a *hard* label budget and *switching* costs, with the constraint priced explicitly as
"cost of certification". The Track E vs Track R gap is exactly that price.

### Substantive or incremental?

**Incremental** as a method. As a measurement it is useful in P2/P3: the J-cost of insisting on
anytime validity, against a Chick-style Bayes-optimal or Test-&-Roll policy.

### Hardest competitor to include

A Chick-Forster-Pertile Bayesian sequential adoption policy (normal or Beta approximation, with the
delay) and a Test & Roll fixed-size test followed by rollout. The repo's `economic_replacement`
control should be checked against both.

### Ablation needed

Track E J for: Chick-style Bayes policy, Test & Roll, `economic_replacement` and each certified
method. The difference is reported as the "price of anytime validity" at each ρ.

---

## Final ranked table: main-track novelty potential

| rank | contribution | closest prior art (verified) | exact delta | substantive? | hardest competitor | ablation needed |
|---|---|---|---|---|---|---|
| 1 | **P2 as benchmark/method paper**: exact known-null (exchangeable twins) on real persistent streams, plus null-tested ledger, plus predictive-loss/economic-cost accounting, plus a Markov lower-bound lemma | Giacomini-White 2006; Henzi-Ziegel 2022; Choe-Ramdas 2024; Diebold-Mariano 1995; Zhu-Timmermann; Ehm-Krüger 2018; Bahadur-Savage 1956; Sethi et al. 2026; Han-Qu 2026; Dietterich 1998 | Twins separate unconditional from conditional nulls exactly on real data. The budgeted/gap-observed setting. Predictive-loss and all-in economic-cost outcomes; application-level decision harm is not identified. The conditional-vs-marginal distinction itself is **not** new. | Moderate. Strong for a D&B track; main track needs the lower bound | HZ/CR conditional e-processes (all-events IPW); sequential HAC-DM (Chu-Stinchcombe-White / Golosnoy-Okhrin) | 3-null × K-method violation matrix; conditional oracle on twins; HAC-DM baseline |
| 2 | **P1 RMM** transferable post-verdict monitoring | Shin-Ramdas-Rinaldo; M-UCB 2019; GLR-klUCB 2022; Chu-Stinchcombe-White 1996; Giacomini-Rossi 2010; Drift2Act 2026; Zhao et al. 2019 | Label-clock restart plus continued acquisition under a shared hard budget, transferred across 4 certificate families. No cross-family evaluation found. | Incremental unless a joint promote/restart error theorem is proved; the gain is mostly continued acquisition | Host + off-the-shelf e-detector (`edetect`) with the same split and acquisition; GLR restart | {acq on/off} × {none, e-detector, RMM}; label vs wall clock; twin and ρ=.8 nulls |
| 3 | **A5b** gap-indexed Markov SUI | Wasserman et al. 2020; Sethi et al. 2026; Larsson-Ramdas-Ruf 2025; Kalbfleisch-Lawless 1985 | Predictable query-chosen gaps in a composite-Markov e-process for paired promotion | Incremental as a method; substantive only as "near the lower bound", inside P2 | Sethi et al. optimal test (gap port); numeraire A5b | UI vs numeraire vs Sethi vs gap-ignorant, against the computed lower bound across ρ |
| 4 | **Economic risk-aware deployment** | Feit-Berman 2019; Chick-Forster-Pertile 2017; Azevedo et al. 2020; Rust 1987; Mahadevan-Mathioudakis 2023 | "Price of anytime validity" under hard budget and switching cost | Incremental; useful as a measurement | Chick-style Bayes adoption; Test & Roll | Track E of Bayes/T&R/economic_replacement vs certified, per ρ |
| 5 | **D2** CAMS + gate, with risk-calibrated frontiers | CAMS; Karampatziakis et al. 2021; LTT; Pareto testing 2023; RCPS 2021; Drift2Act | Shared-label gate on a fast selector; empirical (not guaranteed) alpha calibration | Incremental (composition; the frontier is an evaluation device) | Gated + Xu q* at matched empirical risk; LTT on held-out twin streams | host / host+gate shared / separate / gate-alone, at matched Track-R risk |

**UNVERIFIED in this round:**
- journal versions of Zhu-Timmermann and Ryabko;
- the pages of Golosnoy-Okhrin 2011;
- the venue of Zhao et al. 1905.10493;
- Kohavi-Longbotham 2010 details;
- Newey-West details;
- LTT volume and pages;
- the Malekipirbazari author list.
