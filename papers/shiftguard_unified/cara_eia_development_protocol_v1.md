# CARA on EIA: matched retraining-frontier protocol

**Version:** 1.0  
**Status:** frozen for exploratory development, not preregistered or confirmation.  
**Primary source:** Cost-Effective Retraining of Machine Learning Models (CARA), official code snapshot `ac2a600a3bbc5729087318087c9def96104c9023`.  
**Question:** Do CARA's threshold, cumulative-threshold, and periodic retraining rules add useful operating points to the existing matched EIA EBA retraining frontier?

## Scope

This is a task-specific adaptation of CARA to next-hour EIA demand regression. CARA's paper and reference implementation use query-data-model overlap with classification error and discrete batches. This experiment replaces the 0/1 loss with bounded normalized absolute error, and replaces the future query batch with an observed current-period prefix proxy. It is not a reproduction of the paper's classification experiments or proof of CARA's theory under this EIA adaptation.

The outcome is the same normalized bounded absolute error and update-cost frontier used in the corrected UPF v2 and RCCDA v2 studies. Costs are imposed normalized scenarios, not electricity-system utility. CISO and ERCO remain separate historical case studies; neither provides independent replications. Feature release at event time is assumed, and additional label delays of 0 and 168 hours are sensitivity conventions.

## Data and decision-time information

Use EIA EBA release `e47bdef8b208f8e7d788`, the existing 15 contiguous periods, the first 80% prefix and last 20% evaluation tail in each period, offline periods 0–6, and online periods 7–14. Ridge candidates, loss scale, held-out rows, assumed delays, and the ten-point `alpha` frontier match the frozen UPF v2 artifact.

At the decision at the beginning of period `t`'s evaluation tail:

- `D_t` consists only of current-period prefix rows whose labels are finite and mature by the tail start under the registered delay.
- `D_i` is the exact mature training set used to fit candidate model `i` at its own evaluation-tail start.
- `Q_t` is a deterministic, at-most-256-row sample of the current period prefix covariates. No evaluation-tail feature or target is used.
- Each row sample uses evenly spaced positions in its chronologically ordered array. The same sample rule is used at every decision.
- Feature distances use the imputation, center, and scale from the period-0 training model, fixed before evaluation. Similarity is a Gaussian RBF with `gamma=1/4`, equivalent to scikit-learn's default `1/n_features` for this four-feature task.

For active model `M_i`, the task-specific staleness score is

`QDM_t(i) = mean_{q in Q_t} [ mean_{x in D_t} K(q,x) * ell(M_i(x), y) - mean_{x in D_i} K(q,x) * ell(M_i(x), y) ]`,

where `ell=min(abs(y-prediction)/S, 1)` and `S` is the frozen UPF v2 robust target scale. This query-average normalization keeps the score invariant to the fixed query sample count; it is an explicit scaling adaptation of the paper's sum over query points. A negative score is retained as observed. If fewer than 20 current-prefix labels are mature, the method does not trigger at that decision and cumulative threshold state is preserved.

## Parameter fitting and online rules

Threshold, cumulative-threshold, and periodic parameters are selected separately for each domain, assumed delay, and `alpha` using only offline transitions in periods 1–5. Period 6 is excluded from tuning because its evaluation tail is too close to the online boundary for its labels to be guaranteed mature under the zero-delay convention. The chosen parameters minimize offline realized bounded evaluation loss plus `alpha` per update; ties prefer fewer updates and then deterministic parameter order. This is offline historical tuning, not a validity guarantee.

- CARA-T retrains to the current period's prefix-trained candidate if the current QDM staleness score exceeds its tuned threshold.
- CARA-CT accumulates the active model's QDM scores since its last update and retrains when the cumulative score exceeds its tuned threshold; the accumulator resets on retraining.
- CARA-P retrains on a calendar-period/offset schedule selected on the same offline transitions.

At online period `t`, the candidate model is the Ridge model trained from labels mature at that period's decision. Decisions are scored only on the held-out tail with identical evaluation rows. The evaluator-only full-information oracle is retained from the matched baseline artifact and never enters parameter selection or learner decisions.

## Comparators, outcomes, and stopping rule

Join the three CARA policies to the already verified matched frontier containing never, always, periodic-2/4, error-threshold, UPF, RCCDA, and the evaluator-only oracle. The primary display is the existing `sum(bounded loss) + alpha * update count` frontier. Also report per-period bounded loss, MAE, RMSE, update count, and chosen parameters. This experiment does not add a new conversion between forecast loss and deployment utility.

Run exactly 2 domains × 2 delays × 10 cost points × 8 online periods. Stop when every scheduled cell is complete and its row keys, source/data hashes, label-maturity rules, alpha grid, matching evaluation-row counts, and oracle lower-bound relation to every feasible policy pass verification. Do not generate figures as part of this protocol; any later paper figure must use PaperBanana from validated output data.

## Interpretation limits

The current-prefix proxy is observable at the declared event-time decision but does not guarantee that it represents the forthcoming evaluation-tail query distribution. Labels have assumed release delays, not verified publisher release timestamps. Periods share one historical series, and prior analyses have exposed the data. Report the result as exploratory EIA forecasting/resource evidence, not live deployment, causal intervention value, statistical certification, independent real-data confirmation, or general CARA superiority.
