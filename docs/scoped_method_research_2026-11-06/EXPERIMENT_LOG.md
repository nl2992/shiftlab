# Append-only execution log

Entries are ordered by execution; earlier experiment records in other research folders were not edited or replaced.

## 2026-11-06 — scoped repository graph and source audit

- Worktree branch `codex/scoped-method-research-2026-11-06`, HEAD `c13f232edd72f7d56c286aba5c3cd68e0315b68b`; charter reference `origin/main=7bfe1e6388a546b08786db1a037749c1201fb6b0`.
- Graphify 0.9.103; 388 curated files; 5,819 nodes / 15,743 edges. Query outputs and source verification: `GRAPH_MAP.md`.
- No source results were changed as part of graph extraction. The graph is navigational and includes inferred edges.

## 2026-11-06 — fresh-seed, post-development synthetic rollback sensitivity

- Hypothesis: E_rb has lower net deployment cost than matched RMM on the existing three reversal regimes. This is an exposed-method replication, not a novel candidate test or independent confirmation.
- Frozen before the run: regimes `F3_reversal_800,W_reversal_700,S_reversal_400`; E_rb and RMM on gated, DISCERN-style, SMCS and adaptive-range hosts; never-switch control; 20 seeds; seed base `2026110699`; alpha .05; 4 workers; primary estimand is equal-weighted across 3 regimes × 4 hosts per seed; two-sided t interval.
- Command: `uv run python scripts/sota_sprint/screen.py --regimes F3_reversal_800,W_reversal_700,S_reversal_400 --policies E_rb:gated_deployment,E_rb:discern_style,E_rb:SMCS+retain-incumbent,E_rb:gated_adaptive_range,rmm:gated_deployment+RMM,rmm:discern_style+RMM,rmm:SMCS+retain-incumbent+RMM,rmm:gated_adaptive_range+RMM,CONTROL_never_switch --seeds 20 --seed-base 2026110699 --workers 4 --alpha 0.05 --out outputs/scoped_method_research_20261106/erb_reversal_seed20`.
- Result: E_rb−RMM ΔJ −6.86, 95% t CI [−8.69,−5.03], n=20 seed blocks. Never-switch mean net cost 333.75, lower than all switching policies in the pooled suite. Costs and analysis artifacts are in `synthetic_reversal_seed20.json`, `synthetic_cost_decomposition.json`, and ignored raw outputs under `outputs/scoped_method_research_20261106/erb_reversal_seed20/`.
- Interpretation: supports only a narrow E_rb-vs-RMM relative sensitivity. It does not beat the no-switch control, does not test matched-alpha/two-sided SR/CUSUM variants, and is not confirmatory because method selection and earlier comparisons were exposed. No new method claim.

## 2026-11-06 — targeted tests

- `uv run pytest -q tests/test_atlas_v2_qce.py tests/sota_sprint/test_fam_c.py` — 43 passed in 35.70s.
- `uv run pytest -q tests/sota_sprint/test_fam_b.py` — 22 passed in 69.63s.
- `uv run pytest -q tests/test_failure_atlas.py tests/failure_atlas_v2/test_restart_monitor.py tests/failure_atlas_v2/test_regimes.py tests/promising_directions/test_sota_simulator.py tests/sota_sprint/test_fam_a.py` — 106 passed in 152.90s.
- An initial combined collection including `test_fam_b.py` failed because top-level `regimes` resolved to `scripts/failure_atlas_v2/regimes.py` without `ALL_REGIMES` after the other tests imported a same-named module. Isolating the Family-B test file passed; this import-order collision remains a test-suite limitation.

## 2026-11-06 — current-head corrected replay consolidation

- The primary checkout advanced to `c66185c0a1f3338e7422cfceeeedd0694867fb74`; a fresh worktree based on that head was used. User-owned dirty docs in the primary checkout were not modified. One corrected null replay was generated from `c13f232...+dirty`; OOC, synthetic, exposed-real and fresh-seed real corrections use c66185. This provenance split is recorded in `CORRECTED_REPLAY_AUDIT.md`.
- Consolidated correction suites: null 1,000 seeds/regime; OOC 1,000 seeds/regime; 100 seeds × 21 synthetic regimes; 10 policy seeds × 9 exposed real sources; 20 policy seeds × 5 exposed real sources. All use `T=2000, B=200, c_q=.05, c_s=5, alpha=.05`. These are correction/sensitivity replays over previously exposed sources and methods, not confirmation.
- Main observations: iid `V_null` rates are 0/1000 for Gated and 1/1000 for front/pace; dependence rates are evaluated against marginal robustness, not conditional theorem validity. C2/C6 reduce cost by ~7.4–7.8 versus Gated+front on two existing late regimes but retain <=1% promotion there and show elevated promotion under the out-of-class OOC fair-sign nulls. On five-source real data, equal-source front−Gated = −46.12 J, t95 [−100.12,+7.87]; front−pace = +.28 [−.17,+.73]; no C2/C6 addition is supported. Exact results/hashes: `CORRECTED_REPLAY_AUDIT.md`.
- OPSD/Binance R3 task code and freeze were reviewed read-only. They provide future testbeds, not evidence: raw data are absent in the active worktree; no holdout was opened. The task contract requires a separate committed method freeze and one-opening runner first.
- **Tests rerun on c66185 worktree:** `uv run pytest -q tests/test_atlas_v2_qce.py tests/sota_sprint/test_fam_c.py` — 43 passed in 25.88s; `uv run pytest -q tests/sota_sprint/test_fam_b.py` — 22 passed in 56.63s; `uv run pytest -q tests/test_failure_atlas.py tests/failure_atlas_v2/test_restart_monitor.py tests/failure_atlas_v2/test_regimes.py tests/promising_directions/test_sota_simulator.py tests/sota_sprint/test_fam_a.py` — 106 passed in 139.40s. Total 171 passed in isolated groups. No research source code was changed in this execution; tests confirm the graph-audited current code still passes these groups.
