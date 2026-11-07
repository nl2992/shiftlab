# E-SR 90/10 promotion-risk split calibration

**Gate: FAIL.** The fixed `alpha_split=0.90` configuration did not pass the prospectively
registered any-false-promotion criterion. The independent late-improvement and reversal seed sets
remain unopened under this protocol.

On 1,000 `F0_null` streams (seed base `7110601201`), the candidate promoted 49 times: rate 4.9%.
The one-sided 95% Wilson upper bound is **6.15%**, above the registered 5% ceiling. The candidate
therefore fails calibration and the protocol requires stopping this operating-point screen. No
alternative-regime cost results were generated from the candidate.

The prior default 50/50 split at alpha `0.0005` had a separate 1,000-stream result of 20
promotions and one-sided 95% Wilson upper bound 2.87%, in
`research/scoped_method/pilots/srr_any_false_calibration_20261106/EVALUATION_RESULTS.md`. These
streams are not pooled. The calibration difference is consistent with the larger restart-detector
share increasing the chance of any promotion; it does not show that the alternative gate failed
because of runtime or label-budget handling.

## Reproduction and provenance

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:split90:gated_deployment \
  --seeds 1000 --seed-base 7110601201 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_risk_split_20261106/calibration
```

The source and protocol were frozen at commit `1631e7cfe75cb22c41584e1aaa6391b2d03645d8`.
The runner manifest records the full command, environment contract and source hashes.

| Artifact | SHA-256 |
|---|---|
| `calibration/records.jsonl` | `12673d36cae0ea66bf1ebd21cd37a7d2a9d8beb90673791023aeae19c4f29cdd` |
| `calibration/manifest.json` | `0625f237d6b7de4c2e48a56f8f3d0e5e923d42ccd6253eba0098668b02401216` |

The adjustment was also checked on one separate development smoke stream in `F1_late_800` (one
paired seed). It cost 349 versus 350 for the default split and promoted 7 events earlier; this
single-stream plumbing check is not evidence and is not pooled with the null calibration.
