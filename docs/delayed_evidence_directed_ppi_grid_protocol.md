# Delayed feedback with evidence-directed PPI: development grid protocol

**Status:** frozen development grid; not a null calibration or confirmatory study. It combines the already-established evidence-directed propensity rule, prediction-powered estimation, predictable support bounds, and event-prefix handling for delayed labels. The combination is being benchmarked; no algorithmic novelty is presumed.

## Question

Under a common realized label cap, how do the registered evidence-urgency curves compare with uniform querying and the fixed global PPI support bound when queried outcomes arrive after random delays? The primary development endpoint is post-onset detection of boundary-local decision harm. Also report false alarms on stationary and benign-variance controls, queried labels, events completed, and alarm event/wall time. This screen selects at most a candidate for separate calibration; it does not establish error control or superiority.

## Synthetic data and information boundary

Each independent stream has 1,200 source examples and up to 2,400 target events. A learner-visible context `X_t` is independently sampled from `{-1,+1}` with equal probability. Source outcomes `Z` lie in `{-1,+1}` with conditional mean `0.35 X`. A source-only least-squares fit produces a frozen proxy `H_t=clip(a+b X_t,-1,1)`; target outcomes are never used to fit or update it. Under the stationary control, the target conditional mean remains `0.35 X`. The benign control reduces the outcome magnitude from 1 to 0.55 halfway through the target period while preserving the conditional mean. Under boundary-local harm, the outcome conditional mean changes from `0.35 X` to `0.35 X+0.20` at event 1,200. Thus the marginal paired-cost null is zero in both controls; the harm alternative has a post-onset marginal mean of 0.20 against materiality margin `epsilon=0.05`. Outcomes remain in the registered `[-1,1]` support.

Each queried label has an independent discrete-uniform delay in `{0,...,12}` events. The learner sees current context, its frozen source-trained proxy, prior committed e-process evidence, remaining budget, query randomization, and only labels that have arrived. Evaluator outcomes are used only to resolve a requested label and compute simulator truth; they do not enter the proxy, propensity, or an unqueried increment.

## Methods and mathematical basis

All methods share the stream seed, target contexts/outcomes, query-uniform stream, feedback delays, propensity range `[0.05,0.80]`, and pathwise cap of 480 requested labels. Uniform PPI queries at propensity 0.20. The evidence-directed family crosses activations `{0,0.025,0.05}` with urgency powers `{0.5,1,2}` and uses the established `EvidenceDirectedQueryPolicy`; its query probability depends on the previous committed log e-value and remaining budget. The fixed-bound comparator uses activation 0.05 and power 0.5 with the global bound based on `q_min`.

The monitored null is `E[Z_t | G_(t-1)] <= epsilon`, where `G_(t-1)` includes all prior event history used by query adaptation. For an outcome-free proxy `H_t` and a query coin conditionally independent of `Z_t`, the PPI increment is

`X_t = H_t - epsilon + Q_t (Z_t - H_t) / q_t`.

Its conditional mean is `E[Z_t-epsilon | G_(t-1)]`, and its absolute value is bounded by `B_t=(M+epsilon)(2/q_t-1)` for `|Z_t|,|H_t|<=M`. Since `q_t` is chosen only from prior committed evidence and past spend, this bound is predictable under the stated event-history filtration. Each event is registered in order; queried increments remain pending until the indexed label arrives; unqueried proxy increments are immediate; and the monitor updates only when the contiguous prefix resolves. An arrival-time crossing of that prefix is a crossing of the event-time e-process. This preserves the standard bounded-mean betting guarantee under the stated conditional null, predictable query/bound, correct randomized feedback, and eventual label resolution. It does not make the event-time process a supermartingale in the arrival-time filtration, and it does not guarantee detection power or bounded latency.

The cap is enforced by stopping before registering another event once all 480 request slots have been used. Pending labels are resolved before the run ends. This is a pathwise request cap; it is not a fixed number of events or a fixed feedback delay.

## Registered grid and reporting

Run 30 independent stream seeds per scenario, with root seed offset `20272000`, across all 11 methods (990 method-stream rows). Report per-cell alarm and post-onset detection proportions, mean labels and events processed, paired seed-level differences versus uniform in detection, labels, and alarm delay, and the full source proxy fit and final e-value in the raw metrics. The development sample is too small for a calibration claim; do not interpret observed null rates as type-I error guarantees. A candidate can proceed only to a fresh, multiplicity-adjusted null calibration under the two registered controls, and only if its detection/label trade-off is scientifically meaningful. A disjoint alternative confirmation follows calibration; any method or generator change requires a new protocol. No figures are planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-grid --seeds 30 --seed-offset 20272000 --device cuda --output-dir outputs/delayed_evidence_directed_ppi_grid_30`

The command automatically supports CPU when CUDA is unavailable. It refuses to overwrite a nonempty output directory and writes CSV/Parquet metrics, a grouped summary, and a runtime/config/source-hash manifest.
