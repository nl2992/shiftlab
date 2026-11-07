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

## 2026-11-06 — restarted slower-pacing E-SR screen

- **Question:** Does the existing `k=0.5` horizon-weighted pacing configuration improve late-improvement deployment economics after passing an independent iid-null screen?
- **Protocol:** `research/scoped_method/pilots/srr_tail_pacing_20261106/RESTART_PROTOCOL_20261106.md` and `EVALUATION_AMENDMENT_RESTART1.md`, frozen in commits `9535e1d2` and `3fd8443c`. The earlier interrupted 378-record attempt was excluded. Fresh calibration seed base `7110601701`, independent null seed base `7110601702`, and alternative seed base `7110601703`; `T=2000`, `B=200`, delay 100, label cost .05, switch cost 5, alpha .0005.
- **Calibration:** 20/1,000 iid `F0_null` promotions; one-sided 95% Wilson upper 2.8682%. Independent evaluation null also 20/1,000, upper 2.8682%. Both pass the registered empirical <=.05 screen; this is not a theorem or serial-dependence guarantee.
- **Primary result:** On 100 paired `F1_late_800` streams, candidate net cost was 366.05 versus 362.66 for default E-SR; candidate-minus-default was +1.69/1,000 events, 95% paired t CI [−0.51,+3.90]. It therefore failed the required >=5-unit saving.
- **Adverse and control results:** On `F0_better`, candidate-minus-default was +10.92/1,000 [7.92,13.92]. On `F3_reversal_800`, candidate cost versus never-switch was +20.04/1,000 [17.26,22.82]; on `F3_reversal_1200`, +15.02 [12.90,17.14]. It also lost to the Qiu and Gong common-contract ports on `F1_late_800`, which do not share the certified methods' safety claims. Full matched cost decomposition and baseline intervals are in `research/scoped_method/pilots/srr_tail_pacing_20261106/RESTART1_RESULTS.md`.
- **Decision:** Stop this fixed pacing candidate without retuning. It is a conventional prior-art setting, not a new method. Do not open a real confirmation dataset based on this failed development gate.


## Direct front-loading plus E_rb screen — 2026-11-06

- **Question:** Does the existing front-loaded Gated acquisition schedule composed with E_rb create useful economic headroom over its components, RMM, and never-switch?
- **Protocol:** `research/scoped_method/pilots/direct_frontload_erb_20261106/protocol.md`; four reused regimes, 20 paired seeds per regime, seed base 2026110618, horizon 2000, delay 100, budget 200, label cost 0.05, switch cost 5. The protocol's pre-run timing is not independently verifiable because it was not committed/checksummed before execution.
- **Command:** `PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F0_better,V_late_600,F3_reversal_800,F0_null --policies E_rb:gated_adaptive_range+front,E_rb:gated_adaptive_range,gated_adaptive_range+front,rmm:gated_adaptive_range+RMM,CONTROL_never_switch --seeds 20 --seed-base 2026110618 --workers 1 --out research/scoped_method/pilots/direct_frontload_erb_20261106/run`
- **Result:** The candidate's incremental effect over the front-loaded host was unresolved on F0_better (−3.86, 95% interval [−12.35, 4.64]); its contrast to paced E_rb on V_late_600 was unresolved (−9.65 [−19.89, 0.59]); and it was more costly than never-switch on F3_reversal_800 (+60.65 [42.52, 78.78]). Null promotion was 1/20, with Wilson interval [0.009, 0.236]. No method or confirmation claim.
- **Audit:** Independent recomputation matched all paired contrasts and verified zero cost-identity discrepancy across 400 rows. The run is a dirty-snapshot development result (`469ee3c0+dirty`), with 16-character source hashes; it is not an auditable preregistered or confirmatory run.
- **Artifacts:** `research/scoped_method/pilots/direct_frontload_erb_20261106/run/{records.jsonl,summary.json,manifest.json}`; `docs/scoped_method_research_2026-11-06/DIRECT_FRONTLOAD_ERB_CRITICAL_REVIEW.md`; `research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md`.

## Frozen Wild-Time HuffPost transfer — 2026-11-06

- **Question:** Does canonical published PFA-SR on the `gated_adaptive_range` host reduce deployment cost against matched-host RMM and Xu acquisition-only on a fresh chronological source selected by the frozen validation gate?
- **Protocol and opening:** `research/scoped_method/pilots/chronological_news_transfer_20261106/protocol.md` plus `PROTOCOL_AMENDMENT_20261106.md`. The code snapshot was `9e8fffca` and the frozen-manifest commit is `07a014797c8e04bb785a30175363e98b10e0e959`; the code freeze records source, lockfile, model-pair, eligibility and runtime hashes. The opening was independently reviewed. `TEST_OPENING_STARTED.json` records candidate IDs; `TEST_OPENED.json` records the final 3,877 eligible IDs before any prediction/loss calculation. Label release is simulated at publication date + 24 hours; one source cluster only.
- **Command:** `.venv/bin/python scripts/sota_sprint/run_huffpost_transfer.py`.
- **Frozen operating point:** chronological test `2018-01-01` through `2018-05-25`; 3,877 events; budget 200; label cost 0.05; switch cost 5; alpha .05; 2,000 paired moving-block resamples with 7-calendar-day blocks and seed `2026110641`.
- **Pretest gate:** corrected stable source-line ordering, 8,786 validation rows, 6,953 disagreements, overall error advantage 0.404621, conditional disagreement advantage 0.511290, three block advantages `[0.419939, 0.374872, 0.419057]`; source eligible. UCI and MN-DS did not pass the same frozen validation eligibility rule and were not opened.
- **Result:** PFA-SR net cost 3,163 (3,153 prediction loss + 10 label expense; zero switches), with no promotion after 200 labels. Same-host RMM cost 2,039 (2,024 loss + 10 labels + 5 switch; promote at event 1,498). Xu acquisition-only cost 1,454 (1,439 loss + 10 labels + 5 switch; promote at event 254). E_rb matched RMM (no rollback); E_swcert cost 1,627.95; never-switch cost 3,153. PFA-SR minus RMM = +289.91/1,000 events, 95% interval `[+193.64,+391.18]`; minus Xu = +440.80/1,000, `[+394.19,+486.84]`. Both frozen transfer gates fail.
- **Interpretation:** adverse single-source chronological case study for PFA-SR under a simulated label clock. No cross-source, causal, or iid-null guarantee claim; this is a negative transfer result for published prior art, not a novel method result.
- **Artifacts:** `run/wildtime_huffpost/{TEST_OPENING_STARTED.json,TEST_OPENED.json,code_freeze.json,transfer_results.json,prediction_stream_sha256.json}`. Raw labels and row-level traces remain local. The result and source-level limitation were added to `REAL_DATA_AUDIT.md`, `FAILURE_ATLAS_UPDATE.md`, and `FINAL_ASSESSMENT.md`.
