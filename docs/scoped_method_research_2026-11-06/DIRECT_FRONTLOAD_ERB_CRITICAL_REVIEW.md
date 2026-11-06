# Independent critical review: direct front-loading plus E_rb screen

**Scope:** Read-only adversarial audit of the direct composition screen in `research/scoped_method/pilots/direct_frontload_erb_20261106/run/`. This is an internal LLM-assisted review, not external peer review or an independent theorem verification.

## Recalculation

The screen contains 400 rows: 20 matched seeds × 4 regimes × 5 policies. Every row uses horizon 2,000, label budget 200, delay 100, label price 0.05, and switch cost 5. I recomputed paired net-cost contrasts from the raw rows with two-sided paired t intervals. The values agree with `summary.json` and `ECONOMIC_HEADROOM_DECISION_20261106.md` to rounding. The maximum absolute discrepancy in `net − (loss + 0.05 × labels + 5 × switches)` is 0.

Candidate-minus-comparator mean contrasts (95% paired t intervals) are:

| Regime | Paced E_rb | Front-loaded host | RMM composition | Never-switch |
|---|---:|---:|---:|---:|
| F0_better | −21.45 [−31.70, −11.20] | −3.86 [−12.35, 4.64] | −21.45 [−31.70, −11.20] | −61.35 [−75.67, −47.03] |
| V_late_600 | −9.65 [−19.89, 0.59] | −61.20 [−77.30, −45.10] | −9.65 [−19.89, 0.59] | −51.20 [−67.30, −35.10] |
| F3_reversal_800 | 18.20 [−3.88, 40.28] | −22.85 [−40.73, −4.97] | 4.80 [−16.60, 26.20] | 60.65 [42.52, 78.78] |
| F0_null | 1.20 [−1.31, 3.71] | 0.33 [−0.36, 1.01] | 1.20 [−1.31, 3.71] | 11.20 [8.69, 13.71] |

Negative differences favor the candidate. The candidate requests all 200 labels in every regime. Its mean null promotion frequency is 1/20; the Wilson 95% interval is [0.009, 0.236], too wide to validate a nominal 0.05 rate.

## Assessment

The described development gate is not met. In `F0_better`, the candidate's incremental saving over the front-loaded host is below the stated 5-unit practical threshold and unresolved. In `V_late_600`, its difference from paced E_rb is unresolved. Under reversal, it costs 60.65 more than never-switch, with the interval entirely above zero. The table does not support a distinct method claim or opening a real-data confirmation set. Existing acquisition and rollback components explain the observed trade-offs; the evidence supports `BENCHMARK_OR_CASE_STUDY_ONLY`.

## Limitations

- The experiment has 20 seeds per cell, reuses known simulator regimes, and is exploratory. The t intervals are not adjusted for multiple comparisons or prior candidate selection.
- The protocol file was not committed or checksummed before execution. Its claimed pre-run timing is therefore not independently verifiable.
- The run manifest records `469ee3c0+dirty` and 16-character source-hash prefixes. This is a dirty-snapshot development run, not an immutable registered evaluation.
- The null interval is uninformative about a 0.05 nominal error rate.
- This screen is not fresh-seed confirmation or real-world validation.

## Artifact hashes

- `records.jsonl`: `a1a83a1de7d101ce6e89d58461715529cb243aea0474618a31dc36a7225a09f1`
- `summary.json`: `08ffb4ec158640df1a7fb8d3c8a640fff3fa852d0233a204bec4e8b12a50d56d`
- `manifest.json`: `dc70ee343843432f7130c5019df065b04cbd7d093fee14cbcc15101251dea74b`
- Runner `scripts/sota_sprint/fam_e.py` SHA-256: `44b82db2a6db65f86fd17bca8866e4ed4039bf5277293a46358bc0c62bd34ce1`
