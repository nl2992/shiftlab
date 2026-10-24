# Prequential proxy-Hedge development protocol

## Research question and status

This is a development benchmark for whether a predictable ensemble of bounded loss proxies can
improve prediction-powered evidence about paired decision harm under a fixed query schedule. It is
not a confirmatory study or novelty claim.

For a bounded paired excess cost `Z_t` and a pre-outcome proxy `h_t`, the queried estimator is

    Zhat_t = h_t(X_t) + Q_t / q_t * (Z_t - h_t(X_t)).

If `Q_t | X_t, past` is Bernoulli with known predictable probability `q_t`, independent of the
current outcome conditional on the query information, then
`E[Zhat_t | X_t, Z_t, past] = Z_t`. Thus the history-conditional mean and the one-sided e-process
null are unchanged by the proxy. A convex mixture of proxies bounded by `M` remains in `[-M, M]`,
so the same correction has support bound `M * (2 / q_min - 1)`.

The candidate `prequential_hedge` starts with equal weights on four frozen predictors: zero,
training-set ridge regression, training-set random forest regression, and a probability-derived
paired-cost prediction from a training-set logistic model. After a queried monitor label arrives,
it updates expert weights by exponentiated, inverse-propensity weighted squared loss:

    ell[j,t] = ((Z_t - h[j,t]) / (2M))^2,
    w[j,t+1] proportional to w[j,t] * exp(-eta * Q_t * ell[j,t] / q_t).

The weights used to form `h_t` are therefore determined only by prior queried outcomes. Since
`ell` lies in `[0,1]`, the IPW loss is at most `1/q_min`; the default `eta=q_min/2` keeps each
log-weight update bounded. This is an online aggregation/control-variate candidate, adjacent to
established adaptive reliance and prediction-powered inference. The validity argument for the
monitor comes from predictability and boundedness, not from Hedge. It is not a new e-process theorem.

## Matched development grid

Use 100 shared seeds per registered scenario: stationary, benign nuisance shift, boundary-local
harm, residual-variance shift, recurring regimes, and harmful adaptation. Generate 3,200 events on
CUDA when available. Fit the four predictors only on the historical training slice. Select the
`validation_best` comparator on a disjoint, pre-monitor labeled validation slice. Keep these models
fixed during monitoring; only the Hedge weights update online.

All methods use the same fixed Bernoulli query probability 0.20, the same query uniforms, and the
same realized hard label-dollar budget. This isolates proxy adaptation from query-allocation
effects. The primary comparison is `prequential_hedge` versus fixed ridge, averaged over
evaluator-confirmed material-harm scenario/seed cells, with a percentile bootstrap clustered by
seed. Secondary comparisons include fixed experts and validation-best proxy, paired cellwise
detection, false escalation on the two population-null controls, label count/spend, detection delay,
and stream-level estimator RMSE. Report the null counts as development diagnostics only; 100 seeds
cannot certify 5% calibration.

Advance to an independent confirmation only if the seed-clustered primary interval is above zero,
the online ensemble does not lose more than five percentage points in any registered harmful
scenario, and its estimator RMSE does not materially worsen. A confirmation must use fresh seeds and
independent null calibration before making any error-control claim. If it fails, preserve the negative
result and stop this candidate.

## Assumptions and limits

The learner sees current features, historical labels, query randomization, the four proxy forecasts,
and only queried current outcomes. Evaluator probabilities and change schedules are used only to
compute expected loss, material-harm onset, and outcome metrics. Both actions' costs are observed on
the same simulated outcome. This does not identify counterfactual policy value when deployed
actions change outcomes. Labels are immediate in this development experiment; delayed-label updates
would need to occur only upon arrival and require a separate filtration analysis.

## Reproduction

```powershell
uv run shiftlab-dive-proxy-hedge --device cuda --seeds 100 --seed-offset 20401024 --n 3200 --query-rate 0.20 --output-dir outputs/prequential_proxy_hedge_development
```

No figure is prespecified. If empirical visuals are later added, use PaperBanana and verify every
plotted value against the validated metrics.
