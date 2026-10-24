# History-predictable propensity-bound replay

## Status and question

This is a post hoc development replay of `outputs/monitor_signal_diagnostic_20_60_v2`, not a new independent experiment. It asks whether an event-specific PPI support bound can improve monitoring when the query propensity is predictable from prior evidence and remaining budget.

The original trace was generated with 60 seeds per scenario, the 20% hard dollar cap, `q_min=0.10`, `q_max=0.80`, `alpha=0.05`, and common random numbers. It contains stationary, benign-nuisance, and boundary-local-harm streams for uniform querying and `evidence_curve_a0.05_p0.5`.

## Registered replay

Use each saved sequence of PPI increments without changing queries, labels, proxies, event order, stopping times, or synthetic outcomes. First replay the fixed common bound

\[
B_{\mathrm{fixed}}=M(2/q_{\min}-1),\qquad M=\max(c_{FN},c_{FP})+\epsilon,
\]

and require agreement with every stored learner log-e value to absolute error at most `1e-9`. Then replay the same mixture and stakes using

\[
B_t=M(2/q_t-1).
\]

For the evidence-directed policy, `q_t` is computed before the current query from the prior fixed-bound log-e value and remaining spend only. For uniform querying it is constant. This makes `B_t` predictable under the registered filtration and keeps the marginal conditional-mean null unchanged. Reject any trace with noncontiguous event offsets, propensity outside the registered range, a checksum mismatch, a failed fixed replay, or an increment outside `B_t`.

Classify a crossing before the evaluator-known harm onset as an early escalation; classify a crossing at or after onset as a post-onset detection. Report all streams and reached onsets. Use seed-level pairs for descriptive contrasts. Do not interpret these reused traces as independent calibration, confirmation, or algorithm selection.

## Results and interpretation

The completed replay and output hashes are in `outputs/predictable_query_bound_replay_60/`. The replay changes only the betting scale, so gains in detections are monitor sensitivity on the fixed acquisition path. They do not show that evidence-directed allocation is better than uniform, and they do not establish nominal false-alarm control empirically.

The mathematical validity claim is the standard bounded-mean supermartingale argument, conditional on the stated marginal null, history-predictable query probability, bounded PPI increment, correct pre-outcome randomization, immediate labels, and stopping at event boundaries. A current-context propensity or bound depending on `X_t` does not satisfy this argument without a stronger context-conditional null or another proof.

## Reproduction

```powershell
uv run python scripts/analyze_predictable_query_bound_replay.py --input outputs/monitor_signal_diagnostic_20_60_v2 --output outputs/predictable_query_bound_replay_60
uv run pytest tests/test_predictable_bound_replay.py -q
```

No visual is needed for this table-based replay. Any research figure produced from a follow-up must be created with PaperBanana.
