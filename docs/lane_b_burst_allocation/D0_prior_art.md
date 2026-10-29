# D0 prior-art audit: split-clock (fast biased surrogate + slow gold) switching

Date: 2026-10-29. Lane B, Phase D, gate D0. Status: audit only. No method, theorem, novelty claim or
efficacy result is established here.

## Question audited

Does published or in-repo work already give a rule that:

- **(a)** uses a fast biased surrogate channel to trigger rollback/reversal without alpha-certification;
- **(b)** keeps promotion validity on slow gold labels (anytime-valid under a causal null);
- **(c)** allocates a hard budget across the two channels and time, with delayed releases;
- **(d)** proves a per-reversal advantage of order `Delta*(d_gold - d_fast)` over single-channel methods?

Contract: `docs/switching_problem_v1.md`. Target: `LANE_CONTROL.md` Phase D and `C0_candidates.md` C2.

## Verification levels used

- **L1** = full or theorem-level primary read recorded by Lane A (cited, not redone).
- **L2** = primary page, ar5iv/HTML or abstract fetched in this pass. A fetch tool summarised the page;
  I did not read theorem statements verbatim. Treat statements as "reported", not proof-checked.
- **L3** = search snippet or repo-matrix entry only. Identity confirmed, content not read.
- **Repo** = I read the code docstring and protocol text in this worktree. Result tables were not re-run.

## 1. In-repo work

| Item | What it does | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|
| `controller.CertifiedPromotionRollback`, `closed_loop_intervention.py`, `docs/closed_loop_intervention_*` (Repo) | Single channel. Promotion e-process and an **alpha-certified** rollback e-process (alpha/2 each), rollback cost amortised over a fixed horizon. Caller enforces the budget. | No. Rollback is certified, on the same channel. | Yes, promotion only. | No (budget enforced by caller). | No. |
| `delayed_evidence_directed_ppi*.py`, `delayed_ppi_*.py`, their protocols/results (Repo) | Predictable-bound PPI e-process, history-directed query propensities, **delayed gold labels** with event-order buffering. Docstring: "an algorithm comparison, not a novelty claim". Hard realised label cap, matched delays. | No. | Yes, with the stated conditional-mean null and predictable bound. | Partly: one channel, hard cap, delays. | No. |
| `proxy.py`, `proxy_aggregation.py`, `proxy_hedge_benchmark.py`, `risk_proxy_*` (Repo) | The proxy is a **model prediction** `H_t = clip(a + b X_t)` fit on source data. It is available with no delay and is not a separately observed, separately delayed outcome channel. Used for variance reduction in the PPI increment `H_t + (Q_t/q_t)(Z_t - H_t)`. | No. | Yes (the proxy only changes variance). | No. | No. |
| `prediction_powered_evalues.py` (Csillag et al. transform; Repo) | Factor-level transform with a predictable proxy and recorded propensity. | No. | Yes, if the base factor is an e-value. | No. | No. |
| `active_inference.py` (Zrnic-Candes task adaptation; Repo) | Fixed-horizon, expected-budget baseline, "not an anytime-valid monitor", no pathwise cap. | No. | No (fixed horizon). | No. | No. |
| `delayed_feedback.py`, `delayed_adaptive_query.py`, `delayed_regime_information.py`, `delayed_switching_reference.py` (Repo) | Event-order buffering, Neyman-style query heuristic, an exact two-regime information reference, uniform-query delayed Hedge. | No. | Bookkeeping only. | Partly. | No. |

Repo finding. A repo-wide search for `surrogate`, `fast channel`, `second channel` and `rollback` finds
no code with two separately delayed label channels. The only rollback code is the single-channel
alpha-certified one. The PPI "proxy" is a feature-based predictor with no delay of its own, so the repo's
PPI work is a **variance-reduction** mechanism, not a **latency** mechanism. It is not an overlap with
(a), (c) or (d). It is a mandatory baseline for (b) and for the combined-channel comparison.

One structural fact about the repo's PPI monitor matters for the residual. Its event-order buffering
releases evidence only through the contiguous resolved prefix (protocol text of
`delayed_evidence_directed_ppi_grid_protocol.md`). The PPI e-process therefore cannot cross before the
gold labels it depends on arrive. A fast channel cannot speed up PPI-certified promotion unless it enters
as a *bias-controlled factor with its own validity argument*.

## 2. External and Lane-A-audited sources

"Reuse" rows come from Lane A's records (`docs/switching_*audit*.md`,
`docs/budgeted_switching_research_goals.md`, `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md`).
I did not redo them.

| Source | Level | Model; channels / delays / costs | Guarantee type | Rollback vs promotion asymmetry | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|---|---|
| Prabhu, Bhashyam, Gopalan, Sundaresan, IEEE TIT 2022 (reuse: `switching_sequential_safety_prior_v1.md`) | L1 | Sequential multi-hypothesis testing with controlled sensing and sensing-switch cost. Stationary exp-family, immediate observations, terminal false-detection constraint. | Asymptotic optimality of a modified GLR policy for stopping time plus switch cost. | None: one terminal decision. | No | Terminal error constraint only | Channel choice with costs, immediate | No delays, so no delay-gap term |
| Huang et al., UCB-CuSum (arXiv:2603.28563) (reuse: `switching_ucb_controlled_sensing_audit_v1.md`) | L1 | Multi-stream QCD, immediate observations, one stream per step. | First-order optimal Lorden delay under a false-alarm constraint. | None | No | ARL, not a causal null | Channel selection, no budget cap | No |
| Lau-Tay, IEEE TSP 2021; Li et al. finite-horizon multichannel; Ferrari et al. (reuse) | L1 | QCD with observation-switching cost; finite-horizon sensing; no delay queue. | Asymptotic ARL-WADD; Bellman thresholds. | None | No | No | Sampling-mode / resource selection | No |
| Gong-Zhang ICML 2026 paid observation; Schur et al. UAI 2026 two-phase costed bandits; Kapoor-Nair AISTATS 2026 Markov state sensing (reuse) | L1 | Paid observation and cost-adjusted acquisition, mostly immediate. | Regret bounds including observation spend. | None | No | No | Costly acquisition, hard allowance (Gong-Zhang) | No |
| Lindon-Kallus ICML 2026 (arXiv:2603.25971) (reuse; matrix marks "lead-fetched / abstract read") | L2/L1 per Lane A | Design-based confidence sequences with **treatment-dependent delayed outcomes** and staggered entry. Single outcome channel. | Anytime-valid CS for realised cumulative reward by calendar time. | None | No | Yes, for realised past | No | No |
| Lu et al. JMLR 2026 delayed online multiple testing (reuse) | L1 | Delayed truth labels recycle alpha. | mFDR/FDR. | None | No | Partly | No | No |
| Waudby-Smith et al. arXiv:2210.10768 (reuse) | L1 | Paired policy-value-difference e-process under adaptive logging. | Anytime-valid. | None | No | Yes | No | No |
| Zhang et al. PPRM, ICML 2026; Csillag et al. PPE, ICML 2025 (reuse; repo code) | L3/Repo | Proxy-corrected e-values / risk bounds with a few labels. Proxy is a prediction. | Anytime-valid with a proxy and predictable propensity. | None | No | **Yes** | Label selection, no channel delay | No |
| Zrnic-Candes, Active Statistical Inference, ICML 2024 (arXiv:2403.03208) | L2, first 100k characters of the HTML | Model-uncertainty-driven label sampling with an **expected** label budget; sequential variant with a budget schedule. No delays, no multiple labelers or fidelities. | Asymptotic CLT / martingale-CLT confidence intervals. Not anytime-valid. | None | No | No (asymptotic) | Expected budget over time, one channel | No |
| Kilian, Cortinovis, Caron, anytime-valid Bayes-assisted PPI (arXiv:2505.18000) | L2 abstract | Sequential PPI, growing labelled and unlabelled sets. | Time-uniform, but "asymptotically valid uniformly over time". | None | No | Asymptotic | No | No |
| Angelopoulos et al., Prediction-powered inference (Science 2023) | L3, background only; venue unverified here | Small labelled set plus large predicted set. | Fixed-sample CIs. | None | No | No | No | No |
| Kandasamy et al., The Multi-fidelity Multi-armed Bandit (NeurIPS 2016, arXiv:1610.09726) | L2 (ar5iv, reported) | K arms, M fidelities; cheaper fidelity m has **known** bias bound `zeta_m`, cost `lambda_m`; **no delays**. MF-UCB picks the lowest fidelity whose width is below `gamma_m`. | Cost-weighted regret upper bound and an asymptotic lower bound; open gap on one arm class. | None | Partly: cheap biased fidelity used to eliminate arms | No | **Yes** for cost allocation across fidelities (immediate, known bias) | No |
| Wang et al. MF-MAB revisited (arXiv:2306.07761); Poiani-Degenne multi-fidelity BAI (arXiv:2406.03033) | L3 | Fixed-confidence multi-fidelity BAI with costs. | Cost-complexity lower bound and matching algorithm. | None | No | Fixed-confidence | Yes, costs only | No |
| Ao et al., BAI with LLM judges and limited human audits (arXiv:2601.21471) | L3 | Cheap biased judge scores every sample; costly human audit selectively, with IPW correction. | Anytime-valid CS and a no-judge-only impossibility result. | None | No | **Yes (anytime-valid CS with a biased cheap channel)** | Yes, audit allocation (Neyman), no delay | No |
| Grover et al., BAI with delayed feedback (AISTATS 2018, arXiv:1803.10937) | L2 abstract | Delayed final feedback plus earlier partial feedback that may be a **biased or unbiased estimator**; parallel extension. | Sample-complexity improvement from using partial feedback (abstract: no explicit bounds). | None | Partly: early biased signal replaces waiting | No | No costs | Qualitative only |
| Mann et al., Learning from delayed outcomes via proxies (ICML 2019, arXiv:1807.09387) | L2 (ar5iv, reported) | Adversarial online prediction, fixed outcome delay `D`, proxy revealed with **no delay** (theory). Factored Forecaster regret `O((D+1)|Y||Z| ln(T/|Z|) + |Z| N ln(T/N))`, additive in delay and instance terms. | Expected regret versus the best fixed predictor. | No actions or rollback. | No (prediction only) | No (no validity) | No costs | Delay-additivity, in prediction regret, not decision regret |
| Zhang et al., Impatient Bandits (JMLR 2026, arXiv:2501.07761; KDD 2023 precursor) | L2 abstract | Delayed-reward bandit; Bayesian filter fuses short-term surrogates and delayed reward. Regret depends on a "Value of Progressive Feedback". | Regret bound. | Traffic reallocation, not promotion/rollback. | Partly: surrogate-driven allocation | No | No budget | Information-theoretic, not delay-gap |
| Vernade-Cappe-Perchet, delayed conversions (UAI 2017) | L3 | Bandit with delayed conversions, known delay law, censoring. | Lower bounds and UCB/KL-UCB regret. | None | No | No | No | Delay appears in regret, no surrogate |
| Athey-Chetty-Imbens-Kang, Surrogate Index (NBER w26463) | L3 (search summary) | Short-term outcomes combined into a surrogate index; Prentice surrogacy; bias characterised when surrogacy fails. | Identification and efficiency, fixed sample. | None | Surrogate substitution for a long-term outcome | No (no sequential validity) | No | No |
| Gopalan et al., Bandit QCD (NeurIPS 2021, arXiv:2107.10492) | L3 | Sensor/arm selection with cost-delay trade-off; sensors differ in which parameters they inform. | Delay lower bound and matching scheme. | None | No | No | Partial | No |
| Solozobov, "Evidence Sufficiency Under Delayed Ground Truth" (arXiv:2604.15740) (matrix: abstract-only) | L3 | Governance gate with a label-latency blind period and proxy indicators. | None formal. | Qualitative | Informal | Informal | No | No |

Searches in this pass returned **no** paper on: (i) anytime-valid sequential testing with an early
surrogate and a late primary outcome; (ii) quickest change detection with cheap noisy and expensive
accurate sensors that differ in delay. These are negative search results (bounded; not exhaustive), not
evidence of absence.

## 3. What each of (a)-(d) reduces to

**(a) Fast-surrogate rollback without alpha.** Rollback to the incumbent has an economic loss (lost gain
plus switch cost), not a null-based error rate, so any detector on the surrogate may drive it. Candidate
mechanisms exist off the shelf: a CUSUM or e-detector on the surrogate; MF-UCB-style cheap-fidelity
elimination; Grover/Impatient-Bandit use of partial feedback. Nothing found is specific to rollback
after promotion, but nothing about it is hard either. **Open as a named result, trivial as a mechanism.**

**(b) Promotion validity on gold.** Covered by the repo's delayed PPI monitor and PPE, and by Lindon-Kallus
and Waudby-Smith et al. for the delay and adaptive-logging plumbing. Ao et al. show an anytime-valid CS
over a biased cheap channel with selective gold audits (no delay). **Established.** A surrogate can
only enter promotion evidence as a PPI/PPE factor whose correction term needs gold labels, which
arrive at `d_gold`. So **promotion cannot be accelerated by the fast channel without a bias assumption**,
and that is exactly the asymmetry the target is built on.

**(c) Hard budget across channels, time and delayed releases.** Cost allocation across fidelities is
MF-UCB / Poiani-Degenne (known bias, no delay). Selective gold audit allocation is Ao et al. Delay-shifted
channel choice is Prabhu-type controlled sensing with delay added to the cost, which is the index
`j* = argmin_j [d_j + n_j c_j T / B_j]` already written in C0 and flagged there as probably a one-line
Lagrangian argument. **Covered in its static form; the open piece is state dependence** (post-promotion
rollback needs versus pre-promotion certification needs, pending pipelines counted at request time).

**(d) Advantage `Delta*(d_gold - d_fast)` per reversal.** Against **gold-only** this advantage is
essentially definitional: the feasibility proposition in `switching_problem_v1.md` gives an unavoidable
loss of order `Delta*d` per channel. Any rule that rolls back through a channel with a shorter delay
beats a gold-only rule by that gap, minus the extra detection samples the noisier channel needs
(`n_f` versus `n_g`). So (d) as stated is **not a distinguishing result**. It becomes one only if stated
against the composition baseline below.

## 4. Composition baseline and why it does or does not reach the target

**Composition C\*.**
1. Promotion: the repo's delayed PPI/PPE e-process on gold labels (gold-certified, hard realised cap).
2. Rollback: a CUSUM or e-detector on the fast surrogate, with threshold set by economic cost (no alpha).
3. Budget: a fixed split of `B` between gold and surrogate, plus a fixed paired-calibration rate for the
   surrogate bias `b` (with `b_hat_+` an upper confidence bound).
4. Optional: MF-UCB-style or stationary controlled-sensing channel index.

**What C\* already attains.**
- (a) and (b) by construction.
- A per-reversal rollback delay of about `d_f + n_f/r_f` instead of `d_g + n_g/r_g`. So the
  `Delta*(d_g - d_f)` gain over gold-only is reached by the composition (up to `n_f` versus `n_g`).
- (c) in a static sense: a fixed split, with a Lagrangian index for the split.

**What C\* does not obviously attain (the residual, none of it proved).**
- **State-dependent allocation.** The best split between gold, surrogate and paired calibration differs
  between pre-promotion (the fast channel is nearly useless for certification) and post-promotion (gold
  is nearly useless for latency). Pending queries are charged at request time, so the post-promotion
  rollback pipeline competes with in-flight gold calibration. A stationary split pays a constant factor.
  Whether the optimal state-dependent rule beats the best stationary split by more than a constant is the
  open question. Per C0 it may be a one-line index argument (the C2 falsifier), so this is the main
  EXIT risk at D2.
- **Bias robustness under shift.** A rollback threshold needs `b`, and `b` is estimated from gold labels
  that arrive `d_g` late. If the surrogate bias changes at the same moment as the reversal (the natural
  failure mode), `b_hat` is stale for exactly the `d_g` window that the fast channel was supposed to
  close. MF-UCB assumes known `zeta_m`; Grover and Mann et al. assume a stable proxy-outcome relation; Ao et al.
  have no delay. A guarantee that survives time-varying bias with a delayed calibration stream was not
  found. This is the most plausible non-composition content, but it may also be only a robust-bias
  margin added to the CUSUM.
- **Spurious rollback cost.** Surrogate rollback has no alpha but has a price `k` per false rollback and
  a re-promotion cost. Re-promotion needs fresh gold evidence (summable alpha or online fallback). The
  joint risk/regret frontier of "cheap rollback, expensive promotion" under recurrent reversals is not
  covered by any source above, but the repo's `CertifiedPromotionRollback` plus a surrogate swapped into
  the rollback leg is an obvious extension.

## 5. Verdict

**PASS (narrow, conditional). No source found gives all four of (a)-(d), so the EXIT rule
("fast-surrogate rollback plus gold-certified promotion with a delay-gap advantage already exists") does
not fire on this audit.** But the pass is thin, and the target as written in `LANE_CONTROL.md` is
mis-specified.

1. **Parts that are prior art or composition.** (a), (b), static (c), and the `Delta*(d_g - d_f)`
   gain over **gold-only**. The last is nearly definitional (unavoidable-delay proposition plus a
   shorter-delay detector), so a proof of it is not a contribution.
2. **Mandatory re-statement of (d) at D2.** The advantage must be proved against C\* (gold-certified
   PPI promotion + surrogate-CUSUM rollback + fixed split + calibration), not against single-channel
   methods. A gap of order `Delta*(d_g - d_f)` over C\* is implausible, because C\* already captures it.
   A defensible target is a constant or log-factor, or a regime-dependent separation, from
   state-dependent allocation and from stale-calibration bias.
3. **Precise residual.** A hard-budget, delayed-release allocation between the two channels that is
   provably better than the best stationary split, with a rollback rule that remains safe when the
   surrogate bias is estimated only from `d_g`-late gold labels and may shift with the reversal. This is
   plausible but unproved and is one Lagrangian argument away from a delay-shifted controlled-sensing
   index.
4. **Risks to carry into D1/D2.** (i) D2 reduces to the stationary index plus a bias margin: EXIT per
   the gate. (ii) The surrogate (e.g. OPSD) is informative enough that C\* is near-optimal, leaving only
   a constant-factor gain. (iii) No quantitative claim is available until D1 measures the development
   surrogate-gold correlation and the delay gap relative to noise (`d_g - d_f` versus `n_f - n_g`
   detection samples). If the noisier channel needs more samples than the delay it saves, there is no
   gain even for C\*.

## 6. Three closest sources

1. **Kandasamy et al., Multi-fidelity MAB (L2).** The cheap-biased-fidelity cost allocation with an
   explicit bias bound and a regret/lower-bound pair. Missing: delays, sequential validity, rollback.
2. **Ao et al., BAI with LLM judges and limited human audits (L3).** An anytime-valid CS over a cheap
   biased channel with selective, IPW-corrected gold audits and optimal audit allocation. Missing:
   delays, a reversible deployment state, rollback asymmetry. The closest match to (b)+(c).
3. **Repo `CertifiedPromotionRollback` plus delayed evidence-directed PPI (Repo).** The single-channel
   certified promotion/rollback and delayed PPI that C\* is built from. Grover et al. and Mann et al. are
   the next nearest on the delayed-proxy axis but give no decision or validity guarantee.

Controlled sensing (Prabhu; Huang; Lau-Tay) remains the structural threat for (c) via Lane A's audit,
and Lindon-Kallus remains the delayed-validity plumbing for (b).

## 7. Obvious composition baseline to beat (D3 baseline list)

`C*` = gold-certified delayed PPI/PPE promotion + surrogate CUSUM/e-detector rollback with an
economic threshold + fixed budget split with a paired calibration rate and bias UCB, run with and
without an MF-UCB-style/stationary controlled-sensing channel index. Report separately: gold-only,
surrogate-only (false promotions as the invalid-promotion control), and `CertifiedPromotionRollback`
with the surrogate swapped into the rollback leg. A D2 pass requires a stated separation from `C*`,
not from gold-only.

## Limits of this audit

- Level L2/L3 sources were not proof-read. MF-UCB, Mann et al. and Zrnic-Candes details are as reported
  by a fetch tool. Grover, Impatient Bandits and Kilian et al. rest on abstracts. Athey et al., Vernade
  et al., Ao et al., Poiani-Degenne, Wang et al. and Gopalan et al. rest on search snippets.
- Angelopoulos et al. (Science 2023) was not fetched. Csillag et al. (PPE) and Zhang et al. (PPRM) were
  taken from the repo matrix and code, not re-read.
- The search was bounded and not exhaustive. A covering result may exist under different terminology
  (multi-source/multi-rate change detection, A/B guardrail rollback with surrogate metrics, "early
  stopping on proxies"). Before D2 is frozen, a targeted search on those three phrases is worth doing.
- Nothing here was run; no code, data or tests were touched.
