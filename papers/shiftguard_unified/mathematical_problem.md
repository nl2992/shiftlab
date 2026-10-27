# Common problem formulation and streaming information contract

**Version:** 0.1, 2026-10-25. This document defines the common comparison language for Q1–Q3. It does not assert that all existing runners already satisfy this contract. Each experiment protocol must map its implementation to these fields and identify any deviation.

## 1. Separate the three estimands

Let (P_t) be the deployment distribution at event time (t), (f_t) a predictive model, (pi_t) a decision policy, (pi_{\mathrm{ref}}) a declared reference policy, and (c(a,y;x)) the declared downstream cost for action (a), outcome (y), and, where relevant, features (x). The study keeps these quantities separate:

\[
\begin{aligned}
\Delta_D(t) &= D(P_t,P_0) &&\text{distributional discrepancy},\\
\Delta_R(t) &= R_t(f_t)-R_0(f_0) &&\text{predictive-risk change},\\
\Delta_C(t) &= \mathbb E_t[c(\pi_t(X_t),Y_t)-c(\pi_{\rm ref}(X_t),Y_t)] &&\text{decision-cost change}.
\end{aligned}
\]

The first is not evidence that risk or decision cost changed. The second is not evidence that downstream utility changed. A feature-shift monitor, predictive-risk monitor, and paired decision-cost monitor therefore have separate endpoints and alarms in every result table.

## 2. Event clock, availability clock, and learner filtration

Every record has separate fields for:

1. event occurrence time (t_e);
2. feature availability time (t_x);
3. prediction time (t_p);
4. action execution time (t_a);
5. label-request time (t_q), if queried;
6. outcome availability time (t_y);
7. model update time (t_u);
8. candidate promotion or fallback time (t_s).

An event-time timestamp does not establish that its features or outcome were historically available then. A protocol must source each clock, identify unknown clocks, and state whether the analysis is prospective, delayed-feedback replay, or retrospective. If labels arrive out of event order, the implementation must state whether inferential updates follow arrival order, event order with maturity constraints, or a martingale construction designed for the actual feedback filtration.

Let \(\mathcal F_t\) be the information actually available to the learner just before acting on event (t). It includes the prior observable event history, model and policy versions, predictions, available features, past query decisions and propensities, and labels whose availability time has passed. It excludes unavailable labels, future events, latent generator state, oracle expected costs, future regime indicators, and confirmation-only evaluator metrics. Any action, query probability, cost estimate, context assignment, policy update, or candidate choice used in a validity argument must be measurable with respect to the stated pre-outcome filtration.

## 3. Data contract: learner versus evaluator

| Field | Learner may see | Evaluator may see | Required rule |
|---|---|---|---|
| Event id, event time, feature availability | Yes, when available by decision time | Yes | Stable unique event key; clocks are not silently collapsed. |
| Feature vector (X_t) | Only if available by (t_p) | Yes | A missing or late feature cannot be backfilled into the learner replay. |
| Model/policy version, prediction and action | Learner-created; version must be logged | Yes | Log before the outcome is revealed. |
| Reference action and candidate shadow action | Only if actually computed before outcome and permitted by task contract | Yes | In full-feedback classification, multiple fixed policies can be scored from one label. Do not assume this where actions change outcomes. |
| Label request indicator (I_t), propensity (q_t), label cost (k_t) | Yes, if generated at request time | Yes | (q_t) must be the actual conditional request probability and be strictly positive wherever inverse weighting is used. |
| Outcome (Y_t), label arrival time, maturity status | Only after actual availability | Yes | Delayed negative labels are censored until the outcome window matures; an unobserved label is never treated as a negative. |
| True DGP parameters, counterfactual outcomes, oracle actions, expected losses, latent regimes | No | Yes | Evaluator-only columns cannot enter the policy, query model, tuning, or threshold selection. |
| Split assignment, domain/source version, data hash | Preassigned split/domain metadata as allowed | Yes | Development, calibration, confirmation and final holdout roles are frozen before use. |

Synthetic generators must return learner data and evaluator metadata as separate objects. Tests must assert that learner-facing structures do not contain oracle fields and that perturbing oracle metadata cannot alter learner outputs. Real-data adapters must mark assumed availability times as assumptions rather than verified timestamps.

## 4. Costs, policy comparison, and potential-outcome scope

For a frozen policy pair on a common outcome, define the paired incremental cost

\[
Z_t=c(\pi_t(X_t),Y_t;X_t)-c(\pi_{\rm ref}(X_t),Y_t;X_t).
\]

Positive (Z_t) means the deployed policy is worse. If one outcome (Y_t) determines the costs of all fixed policies, the benchmark is full-information paired evaluation after the label is observed. If an action changes the outcome distribution, only the chosen action's outcome may be observed; the experiment must instead use a causal/off-policy design with positivity, consistency, and any needed ignorability assumptions. It must not score unobserved potential outcomes as if observed.

Application costs must be observed or elicited from a defensible application contract. In synthetic studies, imposed cost ratios are experimental controls and must be named that way. Label cost, compute/update cost, switching cost and action loss should remain separate if their units cannot be credibly converted. If a single scalar objective is used, state the conversion (lambda) and sensitivity range before outcomes are examined. Otherwise report a Pareto frontier over decision loss, labels, compute and interventions.

## 5. Q1: sequential decision-harm monitoring

For a declared materiality threshold (epsilon\ge0), the population-average running harm null is

\[
H_0^{\rm run}:\quad \mathbb E[Z_t\mid\mathcal F_{t-1}]\le\epsilon
\quad\text{for every monitored }t.
\]

This conditional null is stronger than a single unconditional average-risk comparison. A separate weak running-average null may be studied but must be named and not conflated with the eventwise conditional null. A direct bounded-mean e-process can monitor (Z_t-epsilon) only if its bounded support and conditional-mean condition hold for the policy and filtration actually used. Repeated alarms, multiple policies, selected subgroups or policy changes require an explicit joint error allocation or a method with a matching guarantee.

With selectively queried labels and a learner-known predictor (g_t(X_t)), a possible prediction-powered increment is

\[
\widehat Z_t=g_t(X_t)+\frac{I_t}{q_t}\{Z_t-g_t(X_t)\},
\qquad q_t=\Pr(I_t=1\mid\mathcal F_{t-1},X_t),
\]

subject to the actual sampling design, support bounds and timing. This identity alone does not make a sequential test valid. In particular, adaptive policy selection, covariate-dependent nulls, informative delays, positivity failures and unbounded inverse weights require separate handling. When labels are delayed, evidence may only update when the label is available; the process must be justified for that arrival-time filtration.

## 6. Q2: candidate selection and certification

For candidate (k), define expected improvement relative to the incumbent on a declared target distribution:

\[
G_k=\mathbb E[c(\pi_0(X),Y)-c(\pi_k(X),Y)].
\]

If switching cost (K_{\rm switch}) is charged over a fixed deployment horizon (H), the benchmark may test (G_k>K_{\rm switch}/H), provided the horizon, cost unit and target population are fixed in advance. Candidate selection must use a scout/development sample, and certification must use fresh data or an inferential procedure valid under the adaptive selection scheme. Testing many candidates or contexts requires FWER/FDR or another explicitly stated error target. A passed shadow certificate supports a claim about the evaluation distribution and assumptions; it does not guarantee future utility after arbitrary distribution change.

## 7. Q3: budgeted action selection

Let the available intervention (u_t\) belong to a declared finite set such as continue, query, recalibrate, update, retrain, promote or fallback. The intended objective is

\[
\min_{u_{1:T}}\mathbb E\left[\sum_{t=1}^T c(\pi_t(X_t),Y_t)+C_{\rm label}(u_t)+C_{\rm update}(u_t)+C_{\rm switch}(u_t)\right]
\]

subject to the observed information constraint, hard resource budgets, and specified monitoring/certification error controls. Use a scalarization only when the cost conversion is justified; otherwise report a vector objective and Pareto comparison. Distinguish a heuristic controller that optimizes supplied forecasts from a certified action rule. A hard label or retraining budget is an empirical constraint to verify on every run, not an expected budget statement.

If intervention actions are selected adaptively from current feedback, all comparator policies must receive a comparable information stream and budget. Bandit methods are evaluated under action-dependent feedback, while full-feedback classification methods can score several fixed policies from one observed (Y_t); results must not mix these observation models in one nominally matched table.

## 8. Minimum trial-level log and report fields

Each event/run records dataset or generator version, source hash, event id, all available timestamps, policy/model version, learner features/prediction/action, reference and candidate definitions, query probability and realized request, label maturity/arrival, observed cost and missingness, resource expenditures, evidence value/threshold, intervention action, and split/domain. The evaluator additionally records oracle parameters, potential costs where identified, true expected loss, change time, and regime. Export aggregate per-seed outcomes, uncertainty at the independent unit (seed, entity or temporal block as appropriate), configuration, source hashes, data hashes, runtime, stopping rule, exclusions and all registered metrics.

No real dataset currently supports all fields without assumptions. A task contract must identify exactly which are observed, derived, evaluator-only, imposed, or unavailable before that dataset enters a matched benchmark.
