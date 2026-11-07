# Active-RCPS learned-query contract audit

2026-10-30. This continues the explicit baseline inventory. Native author code is a separate comparison from an adapted paired-cost monitor. No assertion of exhaustive SOTA coverage or validated new method.

## Primary source versus our target

[Xu, Karampatziakis and Mineiro](https://arxiv.org/html/2406.10490v2) study sequential calibration of a monotone risk/utility family, active queries under an expected sampling constraint, prediction-assisted increments and learned sampling. Their Section2 risk calibration and AppendixA labeling-policy construction are the relevant mapping targets. A fixed candidate question removes grid inversion; it does not reproduce the original calibration problem. The existing fixed-target parity test therefore covers a component only.

| Contract field | Native author simulation | Required paired-switching comparison |
|---|---|---|
| Object | False-positive risk of threshold beta | Benefit of one frozen challenger versus incumbent |
| Model family | Monotone threshold grid; safe endpoint beta1 | Single question; optionally a separately justified candidate-selection procedure |
| Labels | Immediate queried common outcome | Fixed delayed release; pending reservations count |
| Budget | Learned expected-rate normalization; stop each arm at label count | Hard pathwise cap, stop at promotion or exhaustion |
| Objective | Certified threshold at a label budget | Decision losses + queries + deployment switches |
| Guarantees | Native monotone risk-calibration target | Explicit conditional gain null; no automatic promise of future benefit |
| Comparator truth | Uniform score with Bernoulli conditional outcome | Same synthetic/real stream and frozen models for all arms |

Native-task results cannot be ranked directly against our net-cost figures. Conversely, changing this contract and labeling the result an unmodified author reproduction is incorrect.

## Exact fixed-question reduction

Write Z=L_inc−L_candidate in[−1,1], benefit hurdle m, bounded risk R=(1−Z)/2 in[0,1], theta=(1−m)/2. For query indicator Q with known propensity q, a predictor c in[0,1] gives the author's PartialIw increment:

    xi = theta − c + (Q/q)(c − R).

Conditional independence of Q and the current outcome given query-time information gives E[xi | full event past]=theta−E[R | full event past]. Under E[Z | full event past]<=m this is nonpositive. Query/c may depend on observed covariates, but the bet must be measurable before those covariates unless the null is strengthened accordingly. This is supporting reduction algebra, not a new theorem.

For a fixed positive q floor, xi>=theta−1/q_floor is a conservative bound; half its inverse magnitude is the original code's maximum stake. Its FTL update is clipped sum(xi)/(sum(xi)+sum(xi²)). The existing formula adapter has component parity; learned sampling and predictor estimation are additional obligations.

For delayed adaptation, freeze the bet, propensity and predictor **when the query decision is made**, store them with the event and update predictors only after the label is released. Recomputing c for a pending event using a model trained on subsequently released data does not reproduce the predictable event-time factor. Using a current stake selected from later information for an old event is likewise not justified by this reduction. Fixed-delay, in-order publication exposes event-prefix products; arbitrary arrival reordering needs separate proof and cannot be asserted here.

At hard-cap exhaustion, cease issuing requests and freeze further event factors after existing pending events. Do not substitute q=0 in an importance ratio. Charge requests at issue, including those unreleased at promotion/horizon. The original expected-rate guarantee is not a guarantee for this wrapper; the hard cap must be checked directly.

## Native source audit, pinned commit a67f85d

Author source is in ignored outputs/exhaustive_evaluation/active-rcps. Its Predictor.py has an inactive-branch dangling-dot syntax error. A separate compatibility copy removes the dot and converts ximin's return for modern NumPy/Torch interoperability. Original source remains untouched; compatibility copy was checked against every original Python file. No broader source edits are concealed.

Important source-level distinctions:

1. RiskPredictorPolicyPrimalPlayer.predict takes the square root of its supplied predictor and divides by an adaptive positive normalization, clipped to[q_min,1]. The dual update and COCOB normalization are implemented in the native code. The learned-query arms therefore execute real adaptive query decisions, unlike our earlier fixed-target component.
2. In LinearRiskPredictor.update, the squared-error target is **raw risk**, even for the object passed as var_predictor. For Bernoulli risk with conditional mean u, minimizing E[(R−a)²] gives a=u, whereas the conditional variance is u(1−u). Thus that source path is not an exact conditional-variance regression. It may still be a useful nonnegative sampling heuristic, and this observation does not invalidate the risk martingale. Preserve it in the native pilot; any corrected residual-variance estimator is a separate adaptation/ablation.
3. The learned predictors use features built from model-derived risk/variance guesses. In the native simulator these guesses use the true calibrated score law. The optimal and cv-only arms have exact conditional information; they are privileged references, not deployable default baselines on arbitrary shifted data.
4. simulation.test_once records the current **bet-against** beta in its curve, while the martingale's curbeta[0] is the certified beta. Pilot results must retain both. Likewise its data counter is zero-based; len(agent._hist) gives processed observations. Do not use a last recorded beta as the certified safety parameter without checking this distinction.

5. The native normalization loss is exp(−c)−dual×(target−q), minimized by COCOB. At an unclipped q its derivative is −exp(−c)−dual×q, always negative for nonnegative dual. Direct execution at c=0,q=.5 verifies gradients−1 and−1.153426 for dual0 and1−log2. Thus this loss pushes c upward and q downward even with no budget violation. The [PDF AppendixA.2, printed page22](https://arxiv.org/pdf/2406.10490v2) instead states maximization of −c−dual×(q−B); its negative-payoff derivative is1−dual×q. The PDF confirms both this expression and squared-residual variance fitting; this is not merely an HTML extraction discrepancy. It does not establish which implementation the authors intended or refute their inference theorem. Keep source-as-written and paper-formula variants distinct. Evidence: author_rcps_normalizer_audit.json and audit_rcps_normalizer.py.

## Bounded native pilot and completion rules

author_rcps_pilot_registration.json freezes3 seeds,200 labels per arm,6 original arms,theta.05,q_min.1,target rate.3 and3×3 feature knots. This is a multi-seed native-task pilot, far smaller than the default author experiment (100 trials,2500 labels,10×10 knots); it is not a paper-scale statistical reproduction. For native p uniform[0,1],Y|p Bernoulli(p), risk(beta)=(1−beta)²/2, so the exact feasible boundary is1−sqrt(2theta). Record actual certified risk, original reported beta, observations, mean query probability and realized query fraction. Three seeds cannot validate a5% guarantee or expected-rate convergence.

Pilot terminal status/results are authoritative, not this plan text. A failure must be retained; do not retune parameters after it. Full learned-policy cost adaptation, predictable delayed factors, hard-cap testing, parameter parity and independent same-target comparison remain required after the pilot.

Next implementation: reuse the native learned-query normalization and explicitly distinguish source-as-written risk prediction from residual-variance correction. First verify delay1 factor/query parity on a fixed native trace, then add a queue with frozen issue-time quantities and hard caps. Only after that run development and fresh synthetic/real comparisons with the same information and costs as tuned FTL/CUSUM. This constitutes an adaptation; it does not finish the original full-paper reproduction or establish novelty.

## Optimizer transport check

The vectorized NumPy COCOB primitive in active_rcps_learning.py matches the author's Torch optimizer exactly (maximum absolute error0) on200 updates,7 independent learner rows and13 coordinates. The parity replay includes signed gradients spanning seven orders of magnitude, zero-gradient rounds and masked rows. Original MIT attribution/license is retained in COCOB_LICENSE.txt. This removes one implementation cost for later matched simulation; it is optimizer parity only, not learned-query/predictor parity or scientific efficacy. Evidence: cocob_component_parity.json and check_cocob_parity.py.
