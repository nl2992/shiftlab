# WP2 status (sim agent), 2026-11-07

- DONE: docs/d2a_rar/BENCHMARK_CONTRACT.md (Suite A rules, Suite B contract).
- DONE: src/shiftlab/bench/contract/ (types, guards, streams, simulator, audit, paired, policies, adapters, costs).
- DONE: configs/d2a_rar/cost_vectors.yaml (4 frozen vectors, sha256-checked), stream_families.yaml (9 dev families).
- DONE: tests/d2a_rar/test_contract.py: 33 passed (`pytest tests/d2a_rar/test_contract.py`, ~2 s). Fault-injection tests prove guards fire (leaky truth/stream/pending/swallowing policies, overspend, over/phantom/double charging, early release, unpaired seeds, tampered payer).
- DONE: smoke pair (scripts/d2a_rar/run_contract_smoke.py): ~0.7 s for 20 paired seeds, T=1000. Integrity check only, not evidence.
- STUB: adapters.py Drift2ActAdapter / RARAdapter (STUB_NOT_PORTED) for COMMON_CONTRACT_PORT by the d2a/rar agents.
- TODO (coordinator): register seed blocks (smoke 110900000-110900999, dev 110000000-110099999, confirmation 120000000-120099999) in configs/seed_registry.yaml; create confirmation_families.yaml at WP7 preregistration; not committed.

## WP2b (2026-11-07)
- DONE: seed blocks registered in configs/seed_registry.yaml (d2a_rar_contract_smoke / d2a_rar_dev / d2a_rar_confirmation_reserved); tests/test_seed_registry.py 7 passed.
- DONE: retrospective query(round=s) with max_lookback; release t+delay_s; cost at request; served-model obs; budget + no-leak tests.
- DONE: first-class canary route(target, fraction) with logged propensity, per-model routed-label counts, audit verification.
- DONE: retrain quality model q(e) keyed by clean labelled fraction in W_train (BENCHMARK_CONTRACT 4a); early-vs-late retrain test.
- DONE: propensity verification (state.u) in verify_run; independent loss / serving-model recomputation.
- tests/d2a_rar/test_contract.py: 48 passed; with tests/test_seed_registry.py: 55 passed.
- Open: retrain-quality form is an assumption (sensitivity analysis required); propensity check verifies honoured randomisation, not the true marginal.
