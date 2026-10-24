# Regime-warning reliability grid: exploratory results

## Finding

With 500 paired streams per scenario, a warning feature whose mean shifts at the same time as
harm reduces candidate exposure as signal strength grows. At signal shift `delta=2`, a 5%
conditional-per-read warning threshold, and sensor cost 0.0005 per attempted event, mean realized
utility in harmful adaptation was **−51.15** with no missing reads, **−46.08** with 10% missingness,
and **−36.13** with 30% missingness. Those missing reads trigger incumbent fallback, so more
missingness reduces harm by acting like additional abstention. Each policy remained below `continue`
by those amounts; none has positive net utility in the harmful-reversal scenario.

At the same settings, the warning rule improved over promotion/rollback by **18.93** units at 0%
missingness (paired 95% seed-bootstrap interval **[16.25, 21.85]**), **23.99** at 10%
(**[21.33, 26.63]**), and **33.94** at 30% (**[31.42, 36.57]**). Against fixed 25% candidate
coverage, the differences were **−15.26** (**[−16.46, −14.03]**), **−10.19**
(**[−11.40, −8.95]**), and **−0.24** (**[−1.41, 0.95]**), respectively. The last cell has
approximately matched coverage; the two policies are statistically indistinguishable there.

The most diagnostic result is the oracle-matched-coverage comparison. For each warning configuration,
an evaluator-only randomized policy uses the candidate at exactly the warning rule's theoretical
rate. Because warning values and missingness are independent of paired decision gains in this DGP,
the two have the same expected decision gain. The warning rule's expected utility is therefore
exactly lower by `H * sensor_cost`; the runner checks this identity in every grid cell. This
reference uses evaluator-known coverage and cannot be deployed by the learner. It shows that the
current warning feature adds no expected decision value beyond reducing candidate exposure. A
useful contextual warning must predict heterogeneous gains among events, a condition absent here.

In no-warning controls, the observed false-warning rates conditional on an available read ranged
from **0.98% to 1.03%** for a 1% target, **4.99% to 5.03%** for 5%, and **9.94% to 10.03%** for
10%, across stationary, benign-nuisance, and persistent-benefit profiles and missingness rates
0%, 10%, and 30%. These are marginal per-read rates, not run-level familywise alarm guarantees.

## Design and evidence

The CUDA RTX 4060 grid covers six scenarios, 400 shadow and deployment events, four warning shifts
`{0, 0.5, 1, 2}`, three conditional false-warning targets `{1%, 5%, 10%}`, three MCAR missingness
rates `{0%, 10%, 30%}`, three sensor event costs `{0, 0.0005, 0.002}`, fixed coverage `{25%, 50%,
75%}`, and four sequential promotion/rollback baselines. It produced **264,000 stream-policy rows**
and **2,187 paired contrasts**. All sequential-baseline streams respected the 40% hard label cap.
Metrics include realized and evaluator-expected utility, candidate events, warning and missing-read
counts, label use, and costs. The warning rule uses only prediction-time features; scenario labels
and future gains stay evaluator-side.

At a fixed conditional false-warning rate, the one-sided Gaussian threshold is the
Neyman-Pearson most-powerful test for the stipulated normal location shift. This optimality is only
for detecting that known feature shift; it is not optimal decision utility, robustness to unknown
signals, or a novel method. The current signal appears at the same time as harm and is not a
forecast.

All paired intervals are unadjusted across the development grid. Every warning configuration had
negative expected net utility against `continue` in harmful adaptation, so no candidate is
nominated for confirmation from this block. The next study should test warning features that
predict event-level heterogeneous gains, together with measurement reliability, acquisition cost,
and a no-signal control. Predeclare a quantitative utility-retention threshold before that study;
if no candidate passes it against `continue`, retain this negative result.

Reproduce with the command in the [protocol](regime_warning_grid_protocol.md). The metrics, paired
contrasts, generated report, and manifest are in
[`outputs/regime_warning_grid_500/`](../outputs/regime_warning_grid_500/). Metrics SHA-256:
`c74fdcc8aa993a8086345661d4a603ec6bc373be73019db047fd6d212ac074a3`.

No figure was generated. ShiftLab research visuals must use PaperBanana; it was unavailable for
this run, and no alternate visual generator was used.
