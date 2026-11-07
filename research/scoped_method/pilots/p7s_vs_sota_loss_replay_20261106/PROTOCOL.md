# P7s versus published deployment baselines: exposed loss replay

**Status:** exploratory, previously exposed-data comparator screen. This is not confirmation,
not a new-method claim, and not a fully authentic prediction-stream replay. It answers one narrow
unsettled question: does the frozen P7s settled-acquisition rule reduce net cost against the
published baseline suite on the two adequately powered chronological loss cases already used in
the B3+ work?

## Why this comparison is being run

The B3+ cases compared P7s to P3b and P6, while the SOTA lane compared `EconomicStop` to
certificate baselines. P7s itself has not been compared to the published SOTA suite. The research
claim can only proceed if this gap is addressed. The two powered cases are `rialto` (16 episodes)
and `openml_ldpa` (32 episodes); both are previously exposed and selected, so any result is a
development diagnostic. The three low-power P7s cases are omitted to keep this a decisive,
powered-case screen rather than a broader sweep.

## Frozen settings

- Candidate: unchanged `CertPlus(variant="P7s", acq_shape="settled")`,
  `r_max=1.0`, `r_floor=0.25`, `settled_floor=0.0`, `p_min=0.05`.
- Contract: horizon 2,000, pathwise query budget 200, label price 0.05, switch cost 5,
  alpha 0.05, epsilon 0, and each loss cache's registered delay (100 for Rialto; cache value
  for LDPA).
- Episodes: Rialto K=16, LDPA K=32. Query randomization uses 100 shared seed values per episode,
  base `20261101`; each policy has a private deterministic RNG.
- Primary endpoint: paired episode-average net cost,
  `loss + 0.05 * requested_labels + 5 * deployment_switches`.
- Primary published comparator: `GatedDeploymentStop` (Karampatziakis et al., ICML 2021),
  the strongest applicable certified stop identified in the earlier comparator audit. Also report
  DISCERN-style, SMCS, Model Picker, Model Selector causal adapter, Online LLM Picker, and
  Xu acquisition-only with exact adapter labels. Never-switch is a control, not an SOTA competitor.
- Robustness to lost class marginals: run both `zeros` and balanced `xor` loss-preserving replay
  encodings. These are two encodings of the same fixed loss streams, not independent data and not
  authentic labels/predictions. If the result depends on encoding, it is not a valid data-transfer
  finding.

## Decision rule

This screen can nominate a target for a **new** prospective study only if, in both label encodings:

1. P7s saves at least five net-cost units against Gated on at least one powered case and the
   paired 95% episode-bootstrap interval is entirely below zero; and
2. on the other powered case, P7s is not more costly than Gated by five or more units (paired
   interval must not be entirely above +5); and
3. P7s is cheaper than every other applicable published baseline on the nominated target, with
   paired 95% episode-bootstrap intervals below zero, and passes budget and information-flow
   assertions.

Otherwise, this P7s lane does not justify a fresh confirmation run. Passing would still establish
only a promising exposed-data target: P7s is a conventional settled-decision acquisition rule and
its novelty is not established. A separate prior-art gate and a genuinely fresh source protocol
would be required before any confirmation outcomes are opened.

## Data and implementation provenance

- `data/atlas_v2_losses/rialto.npz`, SHA-256
  `92f4cc16aa2168aea1e34952bc9f5ed208bd7dabc32728dcb28f2eb1ca69ba11`.
- `data/atlas_v2_losses/openml_ldpa.npz`, SHA-256
  `016bf919209d8081ff1608eadc28ee470609d8c6b56a3bf24c767e5f057dd1e2`.
- Runner `scripts/promising_directions/sota/run_vs_sota.py`, SHA-256
  `2d140860daffcc6fce6ac9a7e30c687333c1483e522502916e330fb3b046b819`.
- P7s adapter `scripts/promising_directions/sota/competitors/b3_plus_policy_adapter.py`, SHA-256
  `57084802b15a72a2c41e531f18a19fc65b190d2bd38cdcfe974259e17f476e4d`.
- Certificate adapters `scripts/promising_directions/sota/competitors/certificate_stops.py`,
  SHA-256 `bc313c11681b15a3a2b1feb45dd3fa6a14f5db08d5af327c26be5ef6d5dc79d8`.
- Existing B3+ method freeze: `docs/promising_directions/B3_PLUS_SCREENING_PROTOCOL.md`, SHA-256
  `3a3807c9976f322a90e45c5cd8e313de3c3ee291d4309cfd6764b26ff113561e`.

The runner reconstructs predictions from binary losses (`pred = label XOR loss`) and does not
retrain models or access feature rows. This preserves the recorded paired loss sequences exactly,
but randomized labels do not recreate authentic model-pair predictions or class-feature
relationships. Context-dependent baselines that need features/nuisance models are correctly marked
not run. Raw data and locked holdouts are not accessed by this experiment.

## Exact command

```sh
uv run python scripts/promising_directions/sota/run_vs_sota.py \
  --datasets rialto,openml_ldpa \
  --loss-roots data/atlas_v2_losses \
  --controls \
  --n-seeds 100 \
  --label-mode zeros \
  --out research/scoped_method/pilots/p7s_vs_sota_loss_replay_20261106/zeros

uv run python scripts/promising_directions/sota/run_vs_sota.py \
  --datasets rialto,openml_ldpa \
  --loss-roots data/atlas_v2_losses \
  --controls \
  --n-seeds 100 \
  --label-mode xor \
  --out research/scoped_method/pilots/p7s_vs_sota_loss_replay_20261106/xor
```

**Frozen at commit `d4da0831` plus this protocol commit; run only after committing this file.**
