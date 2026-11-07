# Restarted E-SR slower-pacing screen — 2026-11-06

**Status:** prospectively frozen null-calibration restart. This preserves the earlier interrupted
attempt and does not reuse its partial records. It is an existing-method configuration screen, not
a new detector or novelty claim.

## Frozen candidate and question

Candidate: `E_srrSR:pace_k0.5:gated_deployment`, implemented in
`scripts/sota_sprint/fam_e.py`. It changes only the existing horizon-weighted acquisition factor
from `k=1.0` to `k=0.5` for both host and detector sampling. The e-SR rule, global alpha `0.0005`,
50/50 alpha split, restart rule, horizon, delay, costs, and pathwise label budget remain fixed.

Question: does this fixed acquisition schedule pass an empirical iid conditional-null screening
gate, allowing the previously specified late-improvement development comparison to be run? The
earlier partial run at seed base `7110601301` remains incomplete and is excluded.

## Calibration gate

Run 1,000 fresh `F0_null` streams at seed base `7110601701`. Count any first promotion per stream.
Pass only if the one-sided 95% Wilson upper bound is at most `0.05`. If it fails, stop this
candidate without opening any alternative-regime outcomes. This is an empirical screening result
for the registered iid null generator, not a theorem or evidence under serial dependence.

Frozen command:

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:pace_k0.5:gated_deployment \
  --seeds 1000 --seed-base 7110601701 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_tail_pacing_20261106/calibration_restart1
```

If the gate passes, a separate evaluation amendment must be committed before any alternative
outcomes are opened. It will use fresh seeds, the existing frozen comparison cells and gates from
`protocol.md`; no pacing parameter or target window may be changed. Even a positive result would
remain an application/configuration result unless a matched novelty audit establishes otherwise.

## Provenance

The candidate implementation existed before this restart. This protocol is committed before the
new calibration command is run. The incomplete `calibration/records.jsonl` is explicitly excluded.
