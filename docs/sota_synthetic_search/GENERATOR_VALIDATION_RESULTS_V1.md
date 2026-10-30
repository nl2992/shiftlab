# Four-family generator validation — checkpoint 2

## Result

Continue to baseline adapters and controlled algorithm search. All 52 registered
development family/scenario pairs completed, and an independent verifier checked
all 52 raw-world snapshots. There is no SOTA improvement or novelty conclusion.

Code/protocol checkpoint: `2ead80b`. Batch:
`outputs/sota_search/generator_contract_v1/`. The manifest, 104 start/terminal
registry events, per-run logs/results, compressed evaluator arrays, source archive,
programme usage receipt and independent verification are preserved together.
The executed source hash is
`8d71225a66a1f7829dad104f9b7bbcda621ddd1fda7cb05103d2211661092b41`.

## Independent recomputation

`scripts/sota_search/verify_generators.py` reads archived covariates, outcomes,
hidden states and schedules. It separately reconstructs the fixed forecasts and
decisions, recomputes observed and expected losses (including exact finite-support
G4 integration), and checks the nominal counterfactual losses. It does not call
`make_world`, `binary_risk`, `bounded_position`, or the generator's loss helpers.
It also recomputes every manifest configuration hash and the archived source hash,
checks start/terminal provenance agreement, and reconciles purchased, delivered and
pending labels. Numeric comparisons passed with tolerance 1e-12.

```powershell
$env:PYTHONPATH = 'src'
python scripts/sota_search/validate_generators.py --output outputs/sota_search/generator_contract_reproduction_UNIQUE
python scripts/sota_search/verify_generators.py outputs/sota_search/generator_contract_reproduction_UNIQUE
```

Both output snapshot and verification filename are exclusive-create artifacts.
Use new names rather than overwrite an archived result.

## Verified distinction between prediction deterioration and cost deterioration

Changes below average the current-minus-nominal *conditional expected* incumbent
loss over one generated development world. They are generator diagnostics rather
than estimates of algorithm performance or population confidence intervals.

| Family | Nuisance shift: risk / cost change | Prediction-only: risk / cost change | Cost-only: risk / cost change |
|---|---|---|---|
| G1 | 0 / 0 | 0.1804 / 0 | 0 / 0.1409 |
| G2 | 0 / 0 | 0.2101 / 0 | 0 / 0.1302 |
| G3 | 0 / 0 | 0.1889 / 0 | 0 / 0.1445 |
| G4 | 0 / 0 | 0.0221 / 0 | 0 / 0.0636 |

Exact values for all four families and all thirteen scenarios are in
`independent_verification.json`; G4 uses a different normalized prediction/decision
loss contract and is not pooled with classification losses.

## Resources and limits

Across this batch and the previous 12-run smoke, the persisted programme ledger
reports 64 worker launches, 170.681969 wall seconds and 131.015625 sampled CPU
seconds. The four-hour wall/CPU and 2 GiB global storage caps remain in effect.
The ledger uses reservations to survive supervisor crashes and imports older
batch usage idempotently. No independent programme ledger is created per batch.

Before this batch, 83 focused tests passed. A broader synthetic-only run including
the source PPE/PPRM/Robust ASI, monitoring, and delayed-feedback modules passed
115 tests in 12.35 seconds. Ruff and formatting checks passed. The failed first
budget-policy-reopen unit test exposed a connection-close ordering bug; it was
fixed before committing or launching this batch. No experimental run failed or
was discarded in this checkpoint.

Two additional verifier tests passed after the batch: deliberately corrupting an
archived-style expected-loss value is detected for both classification and returns.

## Remaining substantive work

The coverage gaps listed in 02_SYNTHETIC_GENERATOR_CONTRACT.md remain open. These
52 diagnostic configurations do not replace the requested 500–1,500-configuration
algorithm screen. Remaining required work includes baseline reproduction/adaptation,
Q1/Q2/Q3 experiment adapters, staged candidate search, held-out validation,
full-archive failure synthesis, targeted repairs and cross-parent ablations,
independent final confirmation, theory/novelty analysis, and final leaderboards.
No final confirmation world has been opened.
