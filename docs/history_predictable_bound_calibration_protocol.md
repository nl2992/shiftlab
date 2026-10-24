# History-predictable PPI bound calibration and harm study

**Status:** locked development benchmark, 2026-10-24. The seed block is disjoint from the prior trace replay. Do not tune the protocol from these results; use a new seed block for any confirmation after selection.

## Question and hypothesis

Does replacing the global PPI support bound by a bound computed from a propensity chosen only from past monitor wealth and remaining label budget retain false-escalation control under a nondegenerate marginal null, and does it improve detection of a subsequent localized increase in expected decision cost?

The contribution under test is the established predictable-bound betting construction, not a new e-process theorem. The scientific target is the paired excess decision cost

\[
Z_t=c(\pi_{\mathrm{current}}(X_t),Y_t)-c(\pi_{\mathrm{reference}}(X_t),Y_t),
\]

with null `E[Z_t | F_(t-1)] <= 0`, a frozen action pair throughout monitoring, immediate queried feedback, and an independent randomized label query. Here the current action is 1, the reference action is 0, and both false-positive and false-negative costs equal 1 in the low-cost stratum and 5 in the high-cost stratum. Thus `Z_t = cost(X_t) * (1 - 2 Y_t)` and `|Z_t| <= M=5`.

## Data-generating process

Each event independently draws a low/high cost context with probability one half. In the stationary null, the outcome probabilities are `P(Y=1 | low)=0.56` and `P(Y=1 | high)=0.488`. The conditional expected cost contrasts are `-0.12` and `+0.12`, so the population mean is exactly zero while the observation variance is nonzero. This is a mixed-sign, nondegenerate marginal null.

The harm dose-response grid changes only the high-cost outcome probability at event 1,200. For aggregate post-onset expected-cost effects `delta in {0.04, 0.20, 0.40, 0.60}`, set `P(Y=1 | high)=0.488-delta/5`; low-stratum behavior is unchanged. The resulting aggregate expected cost contrasts are exactly the registered `delta` values. Outcomes, contexts, training samples, and query uniforms use common random numbers across methods and across the paired null/alternative stream IDs.

The learner receives 512 independent pre-monitor training examples per stream and fits a two-cell empirical conditional-mean proxy. The oracle probabilities are used only to generate outcomes and compute evaluator-known expected harm; they are not inputs to querying or monitoring.

## Locked algorithms and grid

Use `alpha=0.05`, a 2,400-event monitoring horizon, onset at event 1,200, and a hard cap of 480 observed labels per stream. Queries are Bernoulli with the recorded propensity and labels arrive immediately. Stop monitoring at the first threshold crossing or when the label budget is exhausted.

Compare:

- uniform querying at `q=0.20` with the fixed support bound `M(2/0.20-1)`;
- evidence-directed querying with `(q_min, q_max)=(0.05,0.80)`, `(0.10,0.80)`, and `(0.15,0.80)`, activation fraction `0.05`, urgency power `0.5`, and budget-taper power `1`;
- for each evidence-directed floor, a fixed-bound mixture with `B=M(2/q_min-1)` and a predictable-bound mixture with `B_t=M(2/q_t-1)`.

The evidence-directed propensity is calculated before the current outcome from that arm's own prior monitor log-e value and remaining label fraction. It does not use the current covariate, label, evaluator truth, or future data. Under the fixed-bound arm it is driven by the fixed-bound process; under the predictable-bound arm it is driven by that process's own prior wealth. This is a closed-loop comparison, and query paths can therefore differ between the two monitors. The uniform arm has a fixed propensity, so a predictable bound equals its fixed support bound and is included once.

Use 2,000 paired streams per condition with Torch RNG root seed `27102027`. The stream IDs are the 2,000 columns of each independently generated tensor batch; each ID is reused across null/effect conditions and all arms. This gives paired method contrasts without making the stream arms statistically independent. Generate on CUDA when available; CPU is permitted only to reproduce or smoke-test the deterministic protocol.

## Primary outcomes and analysis

Primary calibration outcome: any false escalation by the hard-budget stopping time under the exact-zero, nondegenerate null, separately for each arm. Report counts, Wilson 95% intervals, and the nominal 5% line. This finite Monte Carlo study checks implementation and generator calibration; the proof remains the conditional supermartingale argument.

Primary power outcome: post-onset detection by the end of the monitor window across the four high-cost harm magnitudes, both over all streams and among streams that processed the onset. Compare fixed and predictable bounds within each propensity floor and effect size by stream-paired differences and bootstrap intervals. Also report pre-onset escalations, delay conditional on detection, evaluator-known excess cost accumulated until alarm or censoring, labels consumed, and processed events.

Do not select a winner from these grid cells. Intervals are descriptive and unadjusted across floors and methods. The query-policy arm may trade off detection, label use, and exposure; do not report its detections without those resource metrics. A method chosen from this block requires a separately locked confirmation with fresh seeds and an explicit multiplicity plan.

## Validity argument and limitations

At event `t`, `q_t` and `B_t=M(2/q_t-1)` are functions only of prior process wealth and prior realized label spend. Thus the bound is predictable under the filtration for the marginal null. Given the independent query coin and observed queried outcomes, the PPI increment has conditional expectation equal to the paired-cost contrast. Its absolute value is bounded by `B_t`; for every fixed stake `eta in (0,1]`, `1+eta H_t/B_t` is nonnegative with conditional expectation at most one. A fixed mixture of these stakes and its first threshold crossing therefore have the usual Ville bound, assuming the stated eventwise conditional-mean null holds throughout the null scenario.

This benchmark uses independent synthetic streams, a known binary cost contrast, immediate feedback, and a finite predictable query policy. It does not establish validity under serial dependence, delayed or outcome-dependent labels, adaptive policy changes, repeated candidate selection, or interventions that change outcomes. The history-predictable bound is a standard construction and is not claimed as novel.

## Reproduction

```powershell
uv run python scripts/calibrate_history_predictable_query_bounds.py --streams 2000 --horizon 2400 --seed 27102027 --device cuda --output outputs/history_predictable_bound_calibration_2000
uv run pytest tests/test_history_predictable_query_bounds.py -q
```

No image is generated by the analysis script. The project requires PaperBanana for any research figure; if it is not callable in the active environment, report that dependency rather than creating a substitute.
