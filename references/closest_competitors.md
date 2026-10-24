# Closest competitors and scope boundary

This is an initial primary-source comparison, not a complete literature review. It is a warning against presenting the individual ingredients as new.

| Work | Established result relevant to DIVE | Implication for our contribution |
|---|---|---|
| [WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales, ICML 2025](https://proceedings.mlr.press/v267/prinster25a.html) | Weighted conformal test martingales for sequential deployment monitoring; online adaptation under mild covariate shift; detection and diagnosis of harmful shifts. | Sequential monitoring, covariate shift, and adaptation as separate ingredients are already covered. Compare decision-cost estimands and explicit label acquisition, rather than claim these ingredients. |
| [Prediction-Powered E-Values, ICML 2025](https://proceedings.mlr.press/v267/csillag25a.html) | Prediction-powered inference is combined with e-values for continuous risk monitoring, including efficiency from a predictive proxy and anytime-valid evidence. | The combination of a prediction-powered residual correction with e-process evidence is already established for predictive risk. DIVE must identify a precise distinction in paired policy cost, acquisition design, or intervention evaluation. |
| [Prediction-Powered Risk Monitoring of Deployed Models for Detecting Harmful Distribution Shifts, 2026](https://arxiv.org/abs/2602.02229) | PPRM combines per-round labeled and unlabeled samples into unbiased prediction-powered risk estimates, forms an anytime lower confidence sequence for running test risk, and compares it with an upper bound on the source risk. A predictable reliance coefficient may be optimized from prior rounds. The paper assumes bounded loss, i.i.d. source calibration, and positive labeled and unlabeled samples per round; its stated type-I guarantee is for its running-risk null. | This is a close monitor baseline, but its estimand is single-policy predictive risk relative to source risk, not the current paired deployed-minus-reference decision cost. Our scalar-reliance analogue is not PPRM. A paired-cost PPI/CM-EB adaptation is specified in `docs/pprm_paired_decision_benchmark.md`; it must be called an adaptation and its running-mean null must be distinguished from our stronger eventwise conditional null. |
| [Active Statistical Inference, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html) | Uses a label budget and model-assisted adaptive sampling to form valid confidence intervals and tests, with uncertainty-focused allocation and black-box prediction models. | Valid inference under active label allocation is established. Our experiment needs direct comparisons at matched budgets and must show a decision-harm-specific benefit beyond generic uncertainty sampling. |
| [Monitoring Risks in Test-Time Adaptation, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/746960ad49ddb47248970a0e1404230c-Abstract-Conference.html) | Sequential confidence-sequence monitoring of predictive risk for continuously adapting test-time models, including no-label estimation procedures. | Monitoring adapted models is established. A DIVE claim would need an independent candidate-promotion and cost-sensitive decision rule with valid repeated testing. |
| [When to retrain a machine learning model, ICML 2025](https://proceedings.mlr.press/v267/regol25a.html) | Formulates retraining as a cost/performance trade-off and forecasts future bounded model performance under limited information to decide when updating is worthwhile. | Cost-sensitive retraining is already an explicit contribution. DIVE must distinguish itself through valid evidence acquisition, paired decision-cost targets, and certification of alternative interventions, and compare against its forecasting policy. |
| [Robust Decision-Focused Learning via Worst-Case Regret Minimization, UAI 2026](https://proceedings.mlr.press/v337/yamao26a.html) | Trains prediction-and-optimization systems against worst-case regret under measurement error and deployment distribution shift. | Decision-focused robustness addresses training under uncertainty, not sequential monitoring or intervention. It is a relevant training comparator where optimization-based actions fit, but does not replace the sequential deployment comparison. |
| [High Confidence Policy Improvement, ICML 2015](https://proceedings.mlr.press/v37/thomas15.html) and [Safe Policy Improvement by Minimizing Robust Baseline Regret, NeurIPS 2016](https://papers.neurips.cc/paper_files/paper/2016/hash/9a3d458322d70046f63dfd8b0153ece4-Abstract.html) | Certifies or optimizes policy improvement relative to a baseline using offline/trajectory data and explicit safety criteria. | Candidate promotion and safe policy improvement are established in sequential decision settings. Our paired pointwise cost setup is simpler and must not be presented as a general solution to off-policy policy evaluation. |
| [Online multiple testing, ICML 2024](https://proceedings.mlr.press/v238/xu24a.html) | Online allocation and control of false discovery across a sequence of tests. | Repeated candidate or regime tests require an explicit multiplicity strategy; a single e-process does not solve repeated promotion testing. |
| [Ignatiadis et al., Data-driven hypothesis weighting, Nature Methods 2016](https://www.nature.com/articles/nmeth.3885) | Uses independent covariate information to allocate testing weight and improve power while controlling multiplicity. | Validation-informed alpha weights are an established idea. Our validation-power allocation is included as a baseline; novelty would require a stronger decision-harm-specific guarantee or demonstrable utility under matched information and error control. |
| [Maurer and Pontil, Empirical Bernstein Bounds and Sample Variance Penalization, COLT 2009](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf) | Theorem 11 gives a finite-sample empirical-Bernstein bound for independent bounded observations, including non-identically distributed variables. | Our fixed-horizon variance-adaptive promotion gate is a standard construction assembled from this result and Bernstein concentration; it is not a novelty claim. Its independence assumption is stronger than the sequential martingale gate. |
| [Waudby-Smith and Ramdas, Estimating means of bounded random variables by betting, JRSSB 2024](https://academic.oup.com/jrsssb/article/86/1/1/7043257) ([preprint](https://arxiv.org/abs/2010.09686)) | Develops nonnegative betting processes, predictable plug-in empirical-Bernstein confidence sequences, and a hedged capital confidence sequence for bounded means. | Matched CUDA grids compare PM-EB, the one-sided positive betting branch, and the canonical half-weighted positive branch of the hedged-capital method against fixed-stake and plug-in Kelly betting on globally bounded inverse-propensity decision contrasts. PM-EB had lower crossing rates and lower power in this sparse-label setup. The full-alpha one-sided positive branch modestly increased crossing on the high-cost-only alternative, while the half-weighted hedge was statistically indistinguishable from its fixed-mixture comparator at alpha/2. The complete two-sided hedge is not valid for our one-sided upper-mean no-harm null. These are existing methods and baselines, not novelty claims. |
| [Prediction-powered inference](https://www.science.org/doi/10.1126/science.adi6000) | General prediction-powered estimation combines model predictions with residual corrections from labeled examples. | The residual-correction estimator itself is established. Our estimator tests whether decision-aware acquisition can improve evidence per label under declared conditions. |
| [Sample-Efficient Multiple Testing with Adaptive Data Collection (e-PS, 2026)](https://arxiv.org/abs/2609.26651) | Uses empirical average log e-value growth to allocate samples among unresolved hypotheses, with e-BH and arbitrary-stopping FDR control under conditionally valid increments. | Adaptive acquisition guided by e-process growth is already established in a multiple-testing/bandit setting. Our exact-mixture-growth rule instead optimizes a myopic, covariate-conditional query probability for one paired decision-harm monitor under prediction-powered corrections and label costs. This difference is a candidate problem specialization, not a novelty claim; direct comparison or a precise theorem beyond e-PS remains necessary. |
| [R-IDeA: Robust Instance-Dependent Active Learning under Model Misspecification (AISTATS 2026)](https://proceedings.mlr.press/v300/tang26d.html) | Studies active learning when the assumed predictive model is misspecified and develops robust instance-dependent query selection. | Robust active acquisition under misspecification is already a studied direction. Our interval worst-case mixture-growth score is a task-specific baseline for label allocation to a paired sequential monitor, not a general robust active-learning contribution. A direct comparison against robust active-learning methods remains necessary. |
| [Active Sequential Two-Sample Testing (2023)](https://arxiv.org/abs/2301.12616) | Uses an anytime-valid sequential likelihood-ratio test and actively queries costly labels based on a classifier's estimated feature-label dependence. | Active label acquisition for sequential valid tests is established. Its estimand is distributional dependence, not a paired downstream cost contrast. A fair comparison should isolate estimand and acquisition objective while matching labels and error control. |
| [Active Testing: Sample-Efficient Model Evaluation (ICML 2021)](https://proceedings.mlr.press/v139/kossen21a.html) | Derives label-acquisition schemes for lower-variance risk estimation and corrects selection bias through importance weighting. | Cost-sensitive test-label acquisition and unbiased risk correction are established. Decision-harm monitoring must demonstrate a gain beyond variance reduction for fixed-horizon risk estimation, under matched sequential error control. |
| [AnyRank: Reliable Anytime Policy Ranking via Sequential Testing (arXiv:2610.14603, v2)](https://arxiv.org/abs/2610.14603) | For a fixed set of policies evaluated on i.i.d. tasks with a shared bounded score, combines N-SCORE anytime pairwise tests with a prespecified graphical multiple-testing procedure; it adaptively allocates evaluations and claims FWER control for the final ranking. Its paper reports up to 50% fewer evaluations than statistically rigorous alternatives on robotics benchmarks. | This substantially overlaps sequential candidate comparison, adaptive evaluation allocation, and error-controlled policy promotion. It allocates policy/task evaluations for ranking; it does not study selectively querying labels for a paired incumbent-versus-reference harm stream with known propensities and a query budget. Any candidate-certification comparison must include it or explain the interface mismatch. The source is an arXiv v2 preprint (dated 2026-10-16); do not describe it as a settled published result without checking its venue status. |
| [PACE: Anytime-Valid Acceptance Tests for Self-Evolving Agents (arXiv:2606.08106)](https://arxiv.org/abs/2606.08106) | Applies a paired testing-by-betting e-process to accept or reject each proposed agent modification using paired outcomes on shared instances; claims an anytime false-commit bound per candidate under its conditional paired-outcome assumption. The paper explicitly distinguishes this per-candidate claim from run-level family-wise control. | The basic anytime paired candidate gate is already proposed, so a single-candidate e-process promotion rule is not new. Its setting is prompt-level self-evolution and its stated guarantee is per decision, not a run-level guarantee across an adaptively generated sequence. A ShiftLab method must specify fresh evaluation data or a valid cross-candidate error budget, and show a distinct decision-cost/resource contribution. The source is an arXiv preprint; reproduce neither the result nor its assumptions by citation alone. |
| [Comparing Sequential Forecasters (Operations Research 72(4), 2024)](https://pubsonline.informs.org/doi/10.1287/opre.2021.0792) ([full paper](https://arxiv.org/abs/2110.00115); [author code](https://github.com/yjchoe/ComparingForecasters)) | Gives distribution-free, anytime-valid confidence sequences and e-/p-processes for differences in bounded sequential scores. It distinguishes a weak running-average null from stronger per-time conditional comparisons and includes predictable subsequence/bound extensions. | Full-feedback paired decision costs are bounded score differences after a sign convention, so a sequential cost monitor is a close direct application of existing theory, subject to matching the precise null and filtration. Its headline weak null is a running-average expected score differential; our per-step conditional harm null is stronger. That difference does not make a basic direct-loss betting monitor new. Evaluate or use the authors' `comparecast` implementation to validate a faithful score adaptation. |

## Working distinction to test

The plausible experimental gap is **query allocation for evidence about a paired downstream decision-cost contrast**, compared at matched label expenditure with uniform prediction-powered monitoring and established predictive-risk monitoring. This is a candidate distinction, not a novelty claim. Decision-boundary sampling, residual-variance allocation, and decision value of information have substantial existing literatures; the exact allocation rule and baselines need another targeted review before any claim.

AnyRank narrows the policy-evaluation contribution: sequential ranking with active allocation and global error control is already addressed when the evaluator can run selected policies on i.i.d. evaluation tasks. PACE narrows candidate promotion: a paired anytime-valid accept gate is already proposed, although its stated control is per candidate and the paper does not claim run-level FWER. *Comparing Sequential Forecasters* makes full-feedback anytime inference on bounded paired scores an established baseline that maps closely to direct paired decision costs. A defensible distinction would therefore need a precise advantage under the harder information constraint (which labels to acquire on a common deployment stream), a valid predictable-propensity correction, and a demonstrated improvement in harm evidence or net intervention utility. Those remain hypotheses until a matched implementation and theorem establish them.

This first implementation is a benchmark scaffold and not a reproduction of the cited methods. Its bounded betting process is a transparent baseline; it does not implement the conformal constructions, confidence-sequence details, adaptive model handling, or guarantees of the cited papers. In particular, the PPRM-style reliance analogue is not the PPRM baseline itself.

## Allocation-level comparator audit: Active Statistical Inference

The query-allocation baseline needs a more precise match than the broad label
“uncertainty sampling.” [Active Statistical Inference (ASI)](https://proceedings.mlr.press/v235/zrnic24a.html)
derives model-assisted sampling for a fixed-horizon estimator. In the equal-cost mean-estimation
case, its oracle allocation is proportional to the conditional residual standard deviation,
`q(x) ∝ sqrt(E[e² | X=x])`, subject to budget and propensity constraints. ShiftLab's
`variance_proxy` uses residual-second-moment power `0.5`, so it already implements this allocation
shape when that conditional second moment is correctly estimated. The `allocation_grid` power
sweep is a sensitivity analysis around this established rule, not a new allocation family. With
unequal query costs, `cost_variance_proxy` instead uses the familiar `sqrt(E[e²|X]/k(x))` score;
that too is an established cost-adjusted Neyman allocation. These are allocation correspondences,
not a claim that the online hard-budget runner reproduces ASI's estimator or fixed-horizon theory.

[Robust Sampling for Active Statistical Inference (NeurIPS 2025)](https://papers.nips.cc/paper_files/paper/2025/file/6389470564214983604d1ac81631c2c5-Paper-Conference.pdf)
is a closer missing comparator for residual-model misspecification. It studies the variance term
`E[e²(X)/q(X)]`, constructs budget-preserving paths between active and uniform sampling, and
selects a path point using a minimax objective over an L2 uncertainty set for estimated residual
second moments. The [authors' implementation](https://github.com/lphLeo/Robust-Active-Statistical-Inference)
uses the objective `mean(v_hat/q) + c/n * ||1/q||_2` and searches a geometric active-to-uniform path.
The current `robust_mixture_growth_proxy` is **not** this method: it robustifies the outcome
probability in a one-step log-growth objective. ShiftLab now includes a separately named
`robust_active_inference_proxy` adaptation: it selects a point on a 21-point geometric path from
cost-adjusted square-root residual-variance scores to uniform querying, using only pre-monitor
validation predictions. The validation criterion is the paper's L2 robust variance objective;
its radius is the prespecified `robust_active_inference_radius_fraction` times the validation
residual-second-moment norm (default 0.5). The chosen path point and multiplier are frozen before
monitoring; current covariate-specific propensities can still respond to past-fitted residual
models, and actual spend is capped by the runner's hard-dollar stop. This is an adaptation for
comparison, not a reproduction of the paper's batch estimator. In particular, the batch
asymptotic variance result is not a sequential e-process guarantee and is not transferred here.
The radius default is a development setting, not a calibrated or universally justified value; it
should be included in a prespecified sensitivity study before confirmatory claims.

WATCH is likewise not a drop-in paired-cost comparator. Its weighted conformal test martingales
test conformal validity under stated calibration and shift assumptions; the current DIVE target is
a paired deployed-minus-reference decision-cost contrast with selective label acquisition. A fair
WATCH comparison requires specifying a cost-linked conformity score and an explicit mapping from
its validity null to the harm null before interpreting detections as decision-harm evidence.
Until that mapping exists, WATCH should remain a scope reference rather than be scored in the same
table as the paired-cost e-process.

## Decision record: intervention-framework scope audit (2026-10-24)

The proposed action set—continue, query, recalibrate, adapt, retrain, or fall back—and a costed
sequential objective do not by themselves distinguish the project. The component methods already
have close precedents:

- [WATCH](https://proceedings.mlr.press/v267/prinster25a.html) develops weighted conformal
  martingales for deployment monitoring, online handling of mild covariate shift, and diagnosis of
  harmful shifts. It substantially overlaps generic monitoring and monitor-triggered adaptation.
- [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html) studies
  model-assisted label acquisition under a label budget and valid confidence intervals/tests. It
  overlaps active-query plus inference; a different downstream cost estimand alone is not yet a
  methodological contribution.
- [Active Sequential Two-Sample Testing](https://arxiv.org/abs/2301.12616) treats feature-label
  dependence as two-sample discrepancy, actively queries costly group labels, and derives an
  anytime-valid test. It overlaps active, sequential distribution-shift detection, but its null is
  independence/distributional equality rather than paired policy-cost harm.
- [Off-Policy Confidence Sequences](https://proceedings.mlr.press/v139/karampatziakis21a.html)
  provide time-uniform contextual-bandit policy evaluation and demonstrate gated upgrades.
  [High Confidence Policy Improvement](https://proceedings.mlr.press/v37/thomas15.html) separately
  makes candidate search/test multiplicity explicit by splitting policy selection from safety
  evaluation. Generic candidate promotion is therefore not an open gap.
- [Podkopaev and Ramdas, Tracking the Risk of a Deployed Model (ICLR 2022)](https://arxiv.org/abs/2110.06177)
  explicitly supports labels revealed after predictions and labels arriving in delayed batches.
  Delayed feedback by itself is therefore not a gap. Any benchmark here must compare against this
  risk-monitoring framework and explain the distinct paired decision-cost estimand and feedback
  protocol; an event-order buffer is only infrastructure, not a method contribution.

In the current synthetic benchmark, both deployed and reference action costs are observed on the
same outcome, labels are immediate when queried, policy actions do not alter the outcome process,
and the monitor has a known global increment bound. Under those assumptions, inverse-propensity or
prediction-powered estimation followed by a bounded-mean e-process is a transparent composition of
established ideas. It is a useful estimand-specific benchmark; this source audit does not support
calling it a new general algorithm. If policy actions change outcomes, paired losses are not both
identified and the problem must move to randomized/off-policy evaluation. If feedback is delayed,
the event-time null, arrival-time filtration, query propensities, pending labels at stopping, and
latency costs must all be specified before any validity claim.

The next implementation question is consequently a **delayed-feedback comparability benchmark**,
not a new monitor claim: compare event-order buffering, a no-query/hold policy, and an implementation
of the Podkopaev–Ramdas delayed-risk baseline under outcome-independent variable delays, with matched
label budgets and evaluator-known costs. Outcome-dependent delays are a separate stress case and
must not inherit the independent-delay guarantee. Preserve every predeclared e-process assumption
and measure both event-time detection and wall-clock/arrival-time delay. The new
`shiftlab.dive.delayed_feedback.EventOrderBuffer` is an ordering primitive only; its tests establish
release order and latency accounting, not statistical validity. Only after this baseline comparison
shows a concrete failure mode should a new delay-aware evidence or intervention rule be designed.
