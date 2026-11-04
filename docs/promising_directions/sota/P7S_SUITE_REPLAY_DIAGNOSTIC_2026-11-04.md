# P7s published-suite replay diagnostic — 2026-11-04

**Status:** exploratory replay only; not confirmation and not an SOTA claim.

## Question

Does P7s's label-saving mechanism survive a paired replay against the implemented published
certificate and acquisition comparators on the two episode-level powered streams, Rialto and
OpenML LDPA? The decisive comparator is Gated Deployment. This diagnostic uses the existing
runner and does not modify the method or select parameters.

## Frozen run

- Runner: `scripts/promising_directions/sota/run_vs_sota.py`.
- Methods: the runner's complete default suite, including Gated Deployment, DISCERN-style stop,
  SMCS, Model Picker, Model Selector, Online LLM Picker, Xu acquisition-only, and P7s.
- Data: `data/atlas_v2_losses/{rialto,openml_ldpa}.npz`; 16 and 32 episodes, respectively, each
  with 2,000 paired 0/1-loss events. The arrays are exposed derived-loss caches, not raw labels,
  feature rows, or an untouched evaluation set.
- Fixed settings: `T=2000`, `B=200`, `c_q=0.05`, `c_s=5`, `alpha=0.05`, `eps=0`,
  `p_min=0.05`, `n_seeds=100`, seed base `20261101`, delay 100.
- Label replay: `xor`, where balanced synthetic binary labels are XORed with each model's cached
  loss so the two loss sequences remain exact. This is a sensitivity construction, not the
  dataset's actual label/prediction stream. Methods requiring development features or a fitted
  nuisance model remain not-run.
- Primary comparison: episode-level paired net cost `P7s - Gated`; negative favors P7s. The
  script also reports all other suite contrasts, label counts, switches, prediction losses, and
  its run-time budget/future-access checks.

## Reading rule

Treat the result as an implementation/replay diagnostic only. No inference about real label
semantics, causal deployment value, or an untouched population follows. A P7s win would nominate a
new protocol on authentic prediction/label streams; it would not pass the completion gate. A loss
to Gated on both powered streams closes this P7s parameterization as an SOTA lead unless a distinct
structural mechanism is proposed and compared on new data.

## Reproducibility

Run from the repository root:

```powershell
uv run python scripts/promising_directions/sota/run_vs_sota.py `
  --datasets rialto,openml_ldpa `
  --loss-roots data/atlas_v2_losses `
  --n-seeds 100 `
  --label-mode xor `
  --out outputs/p7s_sota_suite_replay_diagnostic
```

Record the input and source hashes with the output. Do not pool this replay with B3 or call the
100 query-randomization seeds independent real episodes.
