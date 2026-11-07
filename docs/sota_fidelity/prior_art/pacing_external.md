# External prior-art check: lever (a), label pacing under change-time uncertainty

2026-11-07. Retrieval-agent report. Scope: does published work already give a **predictable
label-acquisition intensity** that depends on remaining horizon, remaining budget and/or the current
evidence state, under a hard label budget, with a valid sequential (ideally anytime-valid) detector?
And what is the strongest published baseline? Sources already audited in the repo (212 arXiv ids,
including DE-CuSum 1211.3729, on-off control 1105.1361, Geng–Bayraktar–Lai 1309.5396,
Bayraktar–Kravitz 1212.4717, Hou et al. 2412.20207, Gopalan et al. 2107.10492, Xu et al. 2406.10490,
DISCERN 2609.17560, Huang–Veeravalli 2511.12803) are **not** re-audited. Where they matter they are
cited from the repo's own audits.

Reading-depth labels: **Full text** means the body text was extracted and searched for definitions,
theorems and algorithms. **Rendered full text** means the arXiv/ar5iv HTML rendering was read through a
summarising fetch tool and the key statements were cross-checked. **Abstract** means only the abstract
and/or bibliographic record.

## 1. Search log

Web search (Claude WebSearch; "extended" mode where marked *) and WebFetch, run 2026-11-07:

1. `bandit quickest changepoint detection Gopalan Saligrama Lakshminarayanan`. Hit 2107.10492 (already audited).
2. `quickest change detection sampling control limited observations Xu Mei multi-stream`. Hits 2601.22561, 2604.18008, 2603.28563 (audited).
3. `active label acquisition e-process model monitoring anytime-valid label budget`. Hits 2406.10490 (audited), 2411.12563, Capezza et al. ENBIS-25 abstract.
4. `quickest change detection finite horizon observation budget schedule unknown change time optimal allocation of samples`*. Hits 2511.12803 (audited), 2408.05817, 1105.1361 (audited).
5. `active sequential testing e-values adaptive label querying change detection deployed model 2025 2026 arXiv`*. Hits 2203.03532, 2301.12616 (both audited), 2603.20135, 2606.00878.
6. `Zliobaite active learning with drifting streaming data budget variable uncertainty 2014`.
7. `"sampling budget" quickest change detection censoring sensor energy constraint Bayesian optimal sampling policy`. Hits 1411.3107 and the Ren–Johansson–Shi TAC 2017 scheduling paper.
8. `label-efficient model performance monitoring delayed labels when to query labels drift detection budget sequential test`*. Hits 2204.06822, 2603.08578, 2604.15740 (all audited).
9. `Premkumar Kumar optimal sleep-wake scheduling quickest intrusion detection`.
10. `e-detector active sampling budget change detection anytime-valid optional sampling predictable sampling probability`*. Hits 2403.16297, 2504.06526, 2604.04755, 2103.14224 (audited).
11. `arXiv 2026 label budget pacing sequential monitoring champion challenger promotion e-process`*. Hits 2604.26169, 2501.03568.
12. `Bayesian change detection costly observations optimal observation times Dayanik discrete sampling schedule`. Hit 1212.4717 (audited).
13. `sequential change detection with limited number of observations total sample budget optimal when to sample stopping`. Hit 1710.00915 (change acceleration; judged off-target).
14. `Zhang Mei bandit change-point detection ... under sampling control Technometrics`. Hit 2009.11891.
15. `active risk monitoring deployed model label queries importance weighted e-process detect harmful shift`*. Hits 2110.06177, 2505.04608, 2602.02229 (all audited).
16. `"label-efficient" sequential change detection classifier performance active querying arXiv`*. Hits 2501.03568, 2009.08592.
17. `testing by betting active labeling budget deterministic vs adaptive query rate horizon remaining budget e-value power`*. Hits 2512.01423 (audited), 2502.05715.
18. `variable sampling interval CUSUM control chart Reynolds Amin ...` and `variable sampling interval control chart finite production horizon short runs ...`.
19. `Tagaras dynamic control charts finite production runs ...` and `Nenes Tagaras Bayesian control chart finite horizon adaptive sampling economic optimal policy`.
20. `budget manager stream-based active learning balanced incremental quantile filter ... Kottke`.
21. `sequential change detection missing observations intermittent sampling e-process e-detector ...`. Nothing new.
22. `quickest detection finite number of observations remaining horizon Bayesian dynamic programming ...`. Nothing newer than 2014.
23. `arXiv October 2026 anytime-valid monitoring active labeling label budget delayed labels ...`*. Hits 2606.14028, 2608.08174, 2502.04294 (all audited) and 2602.06379. **No Sept–Nov 2026 paper matching lever (a) found.**
24. `optimal deterministic sampling schedule unknown change point finite horizon minimax uniform spacing ...`*. Nothing new.

Indices and venues touched: arXiv abs/HTML/PDF, ar5iv, IISc ePrints / author PDF (Premkumar–Kumar),
IFORS IAOR abstracts (Tagaras), RePEc/EconPapers (Nenes et al.), Scilit/Bohrium (Reynolds et al.),
scikit-activeml docs (Žliobaitė strategies). The INFORMS page for Tagaras–Nikolaidis returned HTTP 403.
Downloaded PDFs were text-extracted with `pdftotext` (no code executed) under
`/private/tmp/claude-501/.../scratchpad/prior_art_pacing/{premkumar,zhangmei,ren15}/`.

## 2. New sources (closest first)

### 2.1 Ren, Johansson, Shi, Shi, "Quickest Change Detection in Adaptive Censoring Sensor Networks"

- arXiv:1503.04999 **v2** (5 Aug 2016). Listed as to appear in *IEEE Trans. Control of Network Systems*.
  **Full text** (PDF extracted).
- **Native problem.** Minimax (Lorden) QCD. Sensors censor (do not send) observations to a fusion
  centre, subject to a communication-rate constraint. Densities f0 and f1 are known and observations are iid.
- **Rule.** CuSum-AC, Eq. (9) and Fig. 3. The fusion centre feeds back a censoring policy that
  **depends on the previous CuSum statistic** s_{k-1}. It uses the maximum-post-censoring-KL policy
  ψ*(ε1) (a low rate) while s_{k-1} < a1, and full transmission ψ*(1) once s_{k-1} ≥ a1. The paper also
  gives an N-level extension. The statistic is reset to a1 when it crosses a1 from below. Parameters
  (ε1, a1, a) are set by simulation.
- **Budget.** Eq. (2): limsup of the *average* pre-change communication rate under P∞, conditioned on
  T ≥ n, must be ≤ ε. This is an average budget, not a pathwise cap.
- **Guarantee.** Theorem 1: Tc(a) is an equalizer rule. Theorem 2: CuSum-AC is asymptotically optimal
  for Problem 1 as the ARL to false alarm ζ → ∞, for any ε > 0. The horizon is infinite, observations
  are immediate, the change time is deterministic and unknown, and the false-alarm criterion is ARL.
- **Verdict: PARTIALLY OVERLAPS.** This is a published, provably optimal (asymptotically)
  **evidence-state-dependent sampling intensity**: sample sparsely when the detection statistic is low
  and densely when it is high. That is the "evidence-state" arm of the candidate rule. It does not have
  remaining-horizon or remaining-budget dependence, a hard cap, label delay, a composite nonparametric
  null or anytime-valid PFA.
- **Repo note.** `docs/lane_b_burst_allocation/B0_prior_art.md` groups 1411.3107 with 1503.04999 as
  "censoring depends on the statistic". That is true only for 1503.04999 (see 2.2).

### 2.2 Ren, Chen, Johansson, Shi, "Quickest Change Detection with a Censoring Sensor in the Minimax Setting"

- arXiv:1411.3107 **v1** (12 Nov 2014). **Rendered full text** (ar5iv).
- **Native problem.** Minimax QCD with one energy-limited censoring sensor and known densities.
- **Rule.** A stationary censoring rule θ_k = μ(X_k) that depends **only on the current observation**.
  It has no memory and gets no feedback from the detector. μ* maximises the post-censoring KL divergence
  (Eq. 20).
- **Budget.** Eq. (5): E∞[μ(X_1)] ≤ ε, an average pre-change energy budget.
- **Guarantee.** Theorem III.1 (CuSum, Lorden) and Theorem III.2 (SRP, Pollak) give asymptotic
  optimality as γ → ∞. Theorem III.3: the optimum uses the full budget. Theorem III.4: the no-send
  region is a single likelihood-ratio interval. The conclusion lists **time-varying, statistic-dependent
  censoring as future work**.
- **Verdict: ADJACENT.** It is useful as evidence that "spend the whole budget" is optimal in the
  stationary infinite-horizon case. It gives no temporal pacing.

### 2.3 Premkumar & Kumar, "Optimal Sleep-Wake Scheduling for Quickest Intrusion Detection Using Wireless Sensor Networks"

- IEEE INFOCOM 2008, pp. 1400–1408, DOI 10.1109/INFOCOM.2008.198. Read from the author-hosted PDF at
  ece.iisc.ac.in. **Full text** (extracted).
- **Native problem.** Bayesian (Shiryaev) QCD. The change time is T ~ geometric(ρ), with ρ = 0.01 in
  the examples. Known f0 and f1, with n sensors. The cost is Eq. (5): λf·P(false alarm) + E[delay] +
  λs·Σ(sensors awake). Sensing is priced through a Lagrange multiplier λs. There is no hard cap.
- **Rule.** Three controllers solved as MDPs on the posterior Π_k. (i) Closed-loop control of the number
  of awake sensors M_{k+1} = M*(Π_k), Eq. (6). Theorem 5 gives the structure M*(π) = max{m : d(m;π) ≥ λs}.
  (ii) Closed-loop control of the wake probability q_{k+1}(Π_k), Eq. (7). (iii) An open-loop constant
  wake probability q, Eq. (8). Stopping is a posterior threshold (Theorems 3, 8, 11). The horizon is
  infinite and the policy stationary.
- **Evidence.** One numerical setting (n = 10, λf = 100, λs = 0.5, N(0,1) to N(1,1)). Total cost J*(0)
  is 38 for closed-loop M, 50 for closed-loop q, and 55 for the best open-loop q = 0.15 (Section V).
- **Verdict: PARTIALLY OVERLAPS.** This is a published demonstration that **posterior-dependent
  (closed-loop) sampling intensity beats the best constant-rate (open-loop) schedule** in Bayesian QCD.
  It is the Bayesian analogue of "adaptive pacer beats fixed pacer". It has no horizon or budget
  dependence, no hard cap, no delay and no frequentist or anytime guarantee.

### 2.4 Tagaras, "Dynamic control charts for finite production runs"; Tagaras & Nikolaidis, "Comparing the effectiveness of various Bayesian X̄ control charts"

- Tagaras, *EJOR* 91(1):38–55, 1996. Tagaras & Nikolaidis, *Operations Research* 50(5):878–888, 2002,
  DOI 10.1287/opre.50.5.878.361. **Abstract only** (IFORS IAOR records; INFORMS returned 403).
- **Native problem.** Economic design of Bayesian control charts over a **finite production run**.
  The process state is updated by Bayes. Dynamic programming chooses the sampling interval (and sample
  size and limits) at each stage to minimise expected cost (sampling, false alarm, out-of-control
  operation).
- **Rule.** A DP-optimal sampling interval that is a function of the posterior and the stage, so it
  depends implicitly on the remaining run. Per the abstract, the 2002 paper concludes that making the
  **sampling interval** adaptive gives most of the economic gain.
- **Guarantee.** Optimal for the stated Bayesian cost model. There is no false-alarm probability
  guarantee beyond the cost trade-off and no hard sample cap. Exact theorem statements are UNVERIFIED.
- **Verdict: PARTIALLY OVERLAPS (structurally closest classical precedent).** A finite-horizon,
  posterior-and-time-dependent sampling schedule optimised for a net economic cost already exists. It is
  model-based (known shift sizes, Bayesian prior), has no hard budget, no delay and no anytime-valid null.

### 2.5 Nenes, Castagliola, Celano, Panagiotidou, "The variable sampling interval control chart for finite-horizon processes"

- *IIE Transactions* 46(10):1050–1065, 2014, DOI 10.1080/0740817X.2013.876128. **Abstract only**
  (RePEc/EconPapers).
- **Native problem.** A VSI Shewhart chart in short (finite) runs. Because intervals are statistic
  dependent, the number of inspections is random. A Markov chain gives exact finite-horizon performance.
- **Verdict: ADJACENT.** It shows that statistic-dependent sampling over a finite horizon is analysed
  in SPC. It has no budget optimisation and no anytime guarantee.

### 2.6 Reynolds, Amin, Arnold, "CUSUM charts with variable sampling intervals"

- *Technometrics* 32(4):371–384, 1990, with discussion by Lucas & Saccucci and a response.
  **Abstract only** (Scilit/Bohrium). The repo already cites the 1988 X̄ VSI paper in
  `docs/sota_sprint/novelty_audit.md`.
- **Rule.** Short sampling interval when the CUSUM statistic signals a possible shift, long otherwise.
  Evaluated by Markov chain (average time to signal, average number of samples to signal). It is
  compared with fixed-interval CUSUM at matched in-control performance (matching convention UNVERIFIED).
- **Verdict: PARTIALLY OVERLAPS (evidence-state arm).** This is the classical name for
  "evidence-dependent sampling intensity". A reviewer will cite it.

### 2.7 Zhang & Mei, "Bandit Change-Point Detection for Real-Time Monitoring High-Dimensional Data Under Sampling Control" (TSSRP)

- arXiv:2009.11891 **v2** (10 Apr 2022). *Technometrics* 65(1):33–43, 2023. **Full text** (extracted).
- **Rule.** Algorithm 1. Thompson sampling chooses which q of K streams to observe, under a hard
  **per-time** constraint Σ_k δ_{k,t} = q. Local SRP statistics are combined by sum-shrinkage.
- **Guarantee.** Theorem 1 links the method to Bayesian procedures under a Geometric(p) change prior.
  Theorem 2 gives ARL E∞(T) ≥ A/K. Theorems 3 and 4 cover sensor-layout properties.
- **Verdict: ADJACENT.** It allocates over space (streams), not time. There is no total budget.

### 2.8 Kartzman, Hawkins, Hale, "Approximately Optimal Multi-Stream Quickest Change Detection"; Halme & Koivunen, "Multi-stream Quickest Change Detection: Foundations and Recent Advances"

- Kartzman et al.: arXiv:2601.22561, latest **v9** (8 Sep 2026). **Abstract only.** One stream sampled
  per time, a decaying-ε-greedy switch plus GLR, approximate asymptotic first-order optimality.
  **ADJACENT** (per-time constraint, no temporal budget).
- Halme & Koivunen: arXiv:2604.18008 **v1** (20 Apr 2026). **Rendered full text** (first ~100k of
  113k characters). The survey's sampling constraint is per-time only (|A_n| ≤ L, Section 3.2).
  Statistic-dependent sampling rules are surveyed in Section 3.2 (Dragalin; Lai et al.; Xu, Mei & Shi
  exploration increment Δ; Thompson-type rules). It finds **no rule that depends on remaining budget or
  time**. The conclusion calls for adaptive sampling rules with guarantees under resource constraints.
  **ADJACENT, but useful as a negative-search witness** for the remaining-budget/horizon arm as of
  April 2026.

### 2.9 Žliobaitė, Bifet, Pfahringer, Holmes, "Active Learning With Drifting Streaming Data"

- *IEEE TNNLS* 25(1):27–39, 2014, DOI 10.1109/TNNLS.2012.2236570. **Abstract plus implementation docs**
  (scikit-activeml module page). Full text not obtained.
- **Rule.** Stream active learning under a label-budget *ratio*. The variants are fixed uncertainty,
  variable uncertainty (a time-dependent threshold driven by the budget and by counts of observed vs
  acquired samples, i.e. a spend-rate controller), randomised variable uncertainty, and split
  (variable uncertainty plus a random fraction to catch drift away from the boundary).
- **Verdict: ADJACENT.** It is a budget-pacing controller for *learning*, with no detector, no
  false-alarm control and no change-time robustness. The 2011 workshop precursor is already in
  `docs/closest_prior_work.md`.

## 3. Strongest published baselines for lever (a)

No single published method has the full contract. The baselines a new pacer must beat, ranked by how
directly a reviewer would demand them:

1. **Uniform pacing and front-loaded / greedy "sample while rights remain".** These are the repo's
   existing fixed pacers. Geng–Bayraktar–Lai (1309.5396, already audited) supply the theoretical
   justification: per the repo audit, uniform/greedy sampling is first-order asymptotically optimal in
   their Bayesian model. Already implemented; no new tier needed.
2. **Evidence-dependent two-level intensity (CuSum-AC / DE-CuSum / VSI-CUSUM family).** Ren et al.
   2015 (Eq. 9), Banerjee–Veeravalli DE-CuSum (audited), Reynolds et al. 1990. **Tier T3**: replace
   CuSum with the repo's SR-type e-detector and censoring with a predictable label probability, map
   (ε1, a1) to label probabilities chosen so the expected spend meets B, and enforce the hard cap by
   truncation. No author code was found or searched for. A T2 port is not meaningful because the native
   model (known densities, average rate, immediate observations) differs from the contract.
3. **Xu–Karampatziakis–Mineiro active labeling** (2406.10490). An audited port already exists
   (`docs/xu_active_betting_paper_to_code_audit.md`). Its budget is an *expected* label fraction, and
   q_t is bounded below and not horizon-aware. Pairing it with a hard-cap pacer is a **T3** adaptation.
   It supplies the validity mechanism (inverse-propensity e-factor with predictable q_t).
4. **Bayes-optimal DP pacer** (Tagaras 1996 / Premkumar–Kumar 2008 / Geng–Bayraktar–Lai Thm 1 style).
   A posterior- and time-dependent sampling DP under a change-time prior. Implementable only as a
   **T3** oracle-informed reference with known pre/post loss rates and prior, and only as a diagnostic
   upper reference, since it uses information the contract's monitor does not have.

## 4. Residual

Every mechanism in the candidate rule is published separately:

- **Validity of predictable optional sampling** for e-processes: Xu et al. 2406.10490; DISCERN
  2609.17560 (both audited).
- **Evidence-state-dependent intensity**: Ren et al. 2015 Theorem 2 (asymptotically optimal); VSI
  CUSUM 1990; DE-CuSum.
- **Closed-loop beats best open-loop** sampling: Premkumar–Kumar 2008, one numerical setting.
- **Remaining-horizon/remaining-budget-dependent schedules via DP** under a change prior:
  Tagaras 1996 / Tagaras–Nikolaidis 2002 (finite run, economic cost); Geng–Bayraktar–Lai and
  Bayraktar–Kravitz (finite rights, audited).

No source found combines all of the following:

- a hard pathwise cap counting pending labels
- fixed label delay
- a finite horizon
- a nonparametric composite conditional null with anytime/finite-horizon false-promotion control via
  an e-detector
- a net-cost objective (loss + c_q + c_s)
- a pacing rule that depends on remaining horizon, remaining budget and e-detector state, analysed
  for robustness **across change times** (minimax regret against the best fixed pacer per change time)

The 2026 survey (2604.18008) also lists no remaining-budget/time-dependent rule. Plainly stated, the
residual is **a combination of existing pieces**: predictable-sampling validity, a horizon/budget-
weighted schedule, an evidence-gated rate and an e-detector. A predictable pacer is valid by
construction, so validity is not a contribution. A defensible contribution would have to be one of:

- (i) a theorem on change-time-robust pacing under a hard cap with delay, for example a minimax-regret
  or competitive-ratio bound against the per-change-time best fixed pacer, which no source above
  provides
- (ii) strong empirical dominance over the T3 baselines in Section 3 across the change-time grid

Without one of these, lever (a) is an engineering combination.

## 5. UNVERIFIED items

- Tagaras 1996 and Tagaras–Nikolaidis 2002: abstract only. The exact DP state, theorem statements and
  whether the sampling interval depends explicitly on remaining run length are not read.
- Nenes et al. 2014 and Reynolds–Amin–Arnold 1990: abstract only. The matched-comparison convention
  (ARL- vs sampling-rate-matched) is not confirmed.
- Žliobaitė et al. 2014: the full text was not obtained. The variable-uncertainty threshold update is
  described from the scikit-activeml documentation, not the paper.
- Kartzman et al. 2601.22561: abstract only.
- Halme–Koivunen 2604.18008: the last ~13k characters of the HTML were not read.
- 1411.3107: read via a summarising fetch of the ar5iv rendering. The "future work" statement on
  statistic-dependent censoring was relayed by that tool, not checked against the PDF.
- Not read at all (seen only in search results, judged lower priority): Huang–Veeravalli 2408.05817
  (unknown finite horizon, no sampling control); Ren–Johansson–Shi TAC 2017 observation scheduling;
  Kottke et al. BIQF budget manager (IDA 2015); 2411.12563 (stream active learning for process
  monitoring); 2502.05715 (active multiple testing); 2504.06526 (e-values from intermittently active
  sensors); 2403.16297 (round-robin active QCD).


---
**Checker qualifications (see [CHECK.md](CHECK.md)):** Premkumar–Kumar Theorem 5 holds only if d(m;π) decreases in m, which the authors hypothesise from numerics. The Halme–Koivunen survey credits the Δ exploration rule to Liu, Mei & Shi, not Xu, Mei & Shi. The lead verdict is in [README.md](README.md).
