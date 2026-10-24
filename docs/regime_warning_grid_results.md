# Regime-warning grid: exploratory results

## Finding

A visible Gaussian warning feature reduced losses in the harmful-reversal simulator as its mean
shift strengthened. It did not make the policy net-beneficial against retaining the incumbent at
any tested strength. At the strongest registered cue (`delta=2`), a 10% per-event warning target
reduced candidate coverage to 23.6% and mean realized net utility to **−33.29** (95% seed-bootstrap
interval for the paired contrast against `continue`: **[−34.12, −32.44]**). The same rule exceeded
the promotion/rollback baseline by **36.79** units (**[34.09, 39.30]**) and the fixed 25%-coverage
policy by **2.60** (**[1.52, 3.65]**). Thus the feature helps choose a less harmful policy than
those comparators in this strong-signal cell, but `continue` remains better.

At `delta=2` and a 5% per-event warning target, the warning policy's mean realized utility was
**−51.15**; it improved on promotion/rollback by **18.93** (**[16.32, 21.67]**) but was
**−15.26** below fixed 25% coverage (**[−16.45, −14.03]**) and **−51.15** below continuing with
the incumbent (**[−52.16, −50.13]**). At zero warning strength, the 5% threshold produced
candidate coverage 95.0% and mean utility **−133.80** in harmful adaptation. The signal is what
makes abstention informative; a threshold alone cannot anticipate an unseen reversal.

The no-warning controls closely matched their nominal *per-event* warning rates. Across stationary,
benign-nuisance, and persistent-benefit streams, observed rates were 1.02–1.03% for a 1% target,
4.99–5.02% for 5%, and 9.95–10.01% for 10%. These rates are not run-level false-alarm probabilities.
In persistent-benefit streams, the 5% warning rule had expected utility **379.75**, compared with
**399.95** for unconditional candidate deployment, reflecting foregone gains on false-warning
events plus feature-processing cost.

## Design and evidence

The CUDA development screen used 500 paired seeds per each of six scenarios, 400 events per shadow
and deployment phase, four warning strengths, three per-event false-warning targets, and fixed
coverage levels 25%, 50%, and 75%. It produced 66,000 stream-policy rows and 756 seed-paired
contrasts. The warning rule sees only a prediction-time feature. Its distribution shifts only
during harmful-adaptation deployment; scenario labels, true gains, and future costs are used only
by the evaluator. All 80%-query / 40%-hard-cap sequential-baseline streams respected their label
caps. The warning and static-coverage policies query no labels and pay a feature-processing cost;
they therefore use a different information resource from the sequential gate.

The tested threshold is the Neyman-Pearson most-powerful one-sided test for the stipulated normal
location-shift alternative at each fixed marginal per-event false-warning rate. That classical
optimality only concerns detecting this registered Gaussian feature shift. It does not establish
optimal intervention utility, generality to unknown warning mechanisms, or a novel method.

All paired intervals are unadjusted across the development grid. No policy was selected for
confirmation. The positive comparison against promotion/rollback at `delta=2` does not overcome
the persistent advantage of the incumbent under harmful reversal, so the next study should first
charge for warning acquisition and model the warning signal's deployment reliability. Confirmation
is not warranted until a frozen policy passes an explicit net-utility rule against `continue` on
independent streams.

Reproduce with the command in the [protocol](regime_warning_grid_protocol.md). The full synthetic
metrics, paired contrasts, report, and manifest are in
[`outputs/regime_warning_grid_500/`](../outputs/regime_warning_grid_500/). Metrics SHA-256:
`ec55038700cc2b4d78b4bcda70a61456edd89b5963da246b8809b4e5c601b200`.

No figure was generated. All ShiftLab research visuals must use PaperBanana; it was unavailable in
this run, and no alternate generator was used.
