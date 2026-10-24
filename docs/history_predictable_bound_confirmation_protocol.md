# Independent confirmation protocol for history-predictable query bounds

**Status:** frozen before confirmation, 2026-10-24. The development study used Torch root seed `27102027` and stream IDs 0–1,999. This confirmation uses root seed `27104027` and 4,000 new stream IDs (27104027–27108026). Do not tune the rule after opening these results.

## Question and candidate

Does replacing the fixed PPI support bound with the predictable eventwise bound improve the average detection-versus-label tradeoff under the registered independent synthetic decision-cost stream?

The candidate is evidence-directed querying with `q_min=0.05`, `q_max=0.80`, activation fraction 0.05, urgency power 0.5, and budget-taper power 1, using `B_t=M(2/q_t-1)`. The primary comparator uses the same evidence-directed rule and floor but the fixed bound `B=M(2/q_min-1)`. A uniform `q=0.20` fixed-bound arm is an established reference. Each arm updates its own evidence and therefore may have a different adaptive query path; this is a comparison of complete monitor-query systems, not an isolated bound substitution on identical paths.

This is an application of the standard bounded-factor supermartingale construction. It is not a new betting algorithm or theorem. At every event, `q_t` is chosen from past monitor evidence and past label spend. The current context and outcome do not enter q. For the marginal estimand `E[Z_t | F_(t-1)] <= 0`, the independent query coin gives the PPI increment the paired-cost contrast as its conditional expectation, and its absolute value is at most `M(2/q_t-1)`. The proof additionally requires a frozen current/reference action pair, complete observed labels when queried, the stated filtration, and the conditional-mean null.

## Frozen design

- 4,000 paired independent streams per scenario; 2,400 monitor events; alpha 0.05; 480-label hard cap; onset at zero-based event index 1,200 (the 1,201st event) for controls and alternatives.
- The exact-zero nondegenerate marginal null has `E[Z]=0` and `Var(Z)=13`, with equally likely low/high cost strata, costs 1 and 5, and outcome probabilities 0.56 and 0.488.
- The strict negative control changes the high-stratum outcome probability to 0.528 at event index 1,200, giving `E[Z]=-0.20` thereafter. Any escalation over the entire stream counts as false.
- Harm alternatives use registered aggregate post-onset effects `delta in {0.04, 0.20, 0.40, 0.60}`, beginning at event index 1,200. All four are included equally in the single primary detection estimand. Dose-specific estimates are secondary.
- Each stream uses 512 independent pre-monitor training events. Oracle probabilities are confined to outcome generation and evaluator expected-cost calculations.
- Common random numbers pair the three arms and dose conditions by stream ID. Null and harm metrics are separate outcomes; all streams use immediate feedback and independent query randomization.
- Generate and analyze on the NVIDIA CUDA device if available. The manifest must record requested and resolved devices, runtime versions, exact seed range, code hashes, result hashes, and row count.

## Primary decision rule

The primary estimand is the equal-weight average over the four registered harm doses of the per-stream post-onset detection indicator difference (predictable minus fixed), averaging within stream first and then across streams. Pre-onset escalations remain in the denominator as competing outcomes; they are not counted as detections. Bootstrap whole stream IDs 10,000 times. Retain the candidate only if all three gates pass:

1. The two-sided 95% paired-bootstrap lower confidence limit for the primary detection difference exceeds +0.02.
2. The two-sided 95% paired-bootstrap upper confidence limit for the mean label-count difference is at most zero, so the candidate does not consume more labels on average.
3. Every simultaneous one-sided calibration upper limit is at most 0.05.

For calibration, the family is the two nonpositive-mean controls (exact-zero and strict-negative) crossed with the three arms. Use exact one-sided Clopper–Pearson limits with Bonferroni per-cell alpha `0.05/6`. This yields at least 95% simultaneous coverage for the six false-escalation rates. A finite simulation pass is evidence about this DGP and code path only; validity follows from assumptions and proof, not empirical non-rejection.

Report dose-specific detection, false escalations before onset, onset reach, delay conditional on post-onset detection, query labels, processed events, evaluator-known cumulative expected harm exposure, and paired differences. Include paired bootstrap intervals for dose-level detection, labels, and evaluator exposure as descriptive secondary results. Evaluator exposure assumes mitigation at the first alarm and is not realized or empirically prevented harm. Report the uniform arm as a baseline, but the primary retention contrast remains predictable versus fixed at q-min 0.05.

## Scope and interpretation

This protocol is not a selection step across the earlier q-min grid; it confirms one development candidate and one comparator. If the complete retention rule fails, do not continue tuning this family on the confirmation seeds. If it passes, the next paper-level work is a separate replication under a declared dependence model, followed separately by a delayed-but-noninformative feedback model, each with a valid filtration and proof. No general superiority claim follows from a synthetic confirmation.

Research figures must use PaperBanana. If PaperBanana is unavailable in the active environment, report that limitation and do not substitute another figure generator.

## Reproduction

```powershell
uv run python scripts/confirm_history_predictable_query_bounds.py --streams 4000 --seed 27104027 --device cuda --output outputs/history_predictable_bound_confirmation
uv run pytest tests/test_history_predictable_query_bounds.py tests/test_history_predictable_bound_confirmation.py -q
```
