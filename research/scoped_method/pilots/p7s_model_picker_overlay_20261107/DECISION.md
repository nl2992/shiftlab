# Decision: P7s / Model Picker overlay

**Exit: `BENCHMARK_ONLY`. Candidate status: terminate.** The overlay does not establish a distinct
economic improvement. This is a decision about the frozen tested candidate and operating regions,
not evidence that the wider research question has been exhausted.

## Evidence

Frozen protocol: [`PROTOCOL.md`](PROTOCOL.md), source commit `99a3046c813226ccd1fcaf9fc47d8adb82d5e3e5`.
Results: [`RESULTS.md`](RESULTS.md); independent recomputation and chronology review:
[`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md). The run covers 50 paired seeds in each of four
synthetic cells and seven methods (1,400 episode rows; 2,800,000 event rows).

On the primary late-improvement cell, candidate minus Model Picker net cost was `−1.00`
(`95% CI [−10.53, 8.54]`), and candidate minus P7s was `+0.73`
(`95% CI [−2.78, 4.24]`). Neither meets the frozen minimum saving of five units with an interval
wholly below zero. Under reversal the candidate exceeded never-switch by `56.43`
(`[47.69, 65.17]`); under null it exceeded never-switch by `9.96` (`[9.89, 10.04]`), above the
five-unit adverse-cost cap. Null promotions were 1/50, below the count cap, but that small screen is
not a false-alarm guarantee. The settled-throttle ablation did not show a distinct primary benefit.

No real or locked data was opened because the synthetic gate failed. There is no independent real
transfer evidence for this candidate, and no novelty or statistical-validity claim is made.

## Contribution status

| Contribution | Status | Evidence and limitation |
|---|---|---|
| Diagnosis | PARTIAL | Reproducible synthetic late, reversal, and null trade-offs appear in `RESULTS.md`; this does not establish a newly identified failure of a published method in independent real data. |
| Explanation | PARTIAL | Paired cells and the settled-throttle ablation show that the proposed acquisition/deployment interaction did not produce the expected cost reduction. They do not isolate a general causal mechanism. |
| Repair | FAIL | The proposed overlay misses both frozen primary comparator gates and fails the reversal and null cost caps. No repair claim survives. |
| Validation | FAIL | This is a synthetic development screen, not independent confirmation. No real/locked dataset was opened. |

## Reproduction and checkpoint

From repository root, reproduce with:

```bash
PYTHONPATH=scripts/promising_directions/sota uv run python research/scoped_method/pilots/p7s_model_picker_overlay_20261107/run_pilot.py
uv run python research/scoped_method/pilots/p7s_model_picker_overlay_20261107/analyze.py
uv run pytest -q tests/promising_directions/test_sota_b3_plus_adapter.py tests/promising_directions/test_p7s_model_picker_overlay.py
```

Recorded focused tests: 15 passed; `git diff --check` passed. Exact environment, seeds, source and
output hashes are in `MANIFEST.json`. The pilot itself should not be rerun merely to reproduce the
committed result; use the committed rows and analysis for audit.

**Smallest next action:** stop this candidate lane and add its negative result to the Failure Atlas.
Only start another bounded development pilot if a source-audited, pre-existing Failure Atlas
scenario identifies an untested mechanism with measurable headroom over the corrected strongest
baseline; do not open real confirmation data before its synthetic and novelty gates pass.
