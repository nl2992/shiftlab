# Experiment audit, milestone 3 (ARIS `experiment-audit`, cross-model)

**Auditor:** Codex CLI `gpt-reserve` at medium effort, read-only. Reported model: gpt-5.
**Executor:** claude-opus-5-5. **Skill:** ARIS SKILL.md at f76ec8d.

| run | state audited | verdict | cause | action |
|---|---|---|---|---|
| 1 ([raw](m3_experiment_audit_codex_run1.md)) | while Amendment 5 was still executing | **FAIL** (check C) | Amendment 5 had a partial records file (575 lines) and no result or report entry | Amendment 5 finished (HC PASS); report and register synced; re-audit run |
| 2 ([raw](m3_experiment_audit_codex_run2.md)) | all experiments complete | **WARN** | No fabrication or mismatch was found. Headline values reconcile with artifacts, and the reviewer recomputed the fresh-data checksums. Four auditability weaknesses were flagged: (1) stale tracker; (2) `analyze_validation` skipped missing files silently; (3) `analyze_real` built the comparator class from whatever columns existed; (4) manifests hashed only `scripts/sota_sprint` and git-dirty checks covered `scripts` only | All four fixed, in the commit after this file: (1) `validation/leaderboard_inputs.json` sets the validated status, main-track potential and SOTA fields per candidate, merged by `leaderboard.py`; (2) and (3) both scripts now fail closed and re-ran clean on the existing records; (4) manifests now hash every imported dependency directory plus the replayed loss caches, and the dirty check covers `scripts`, `data` and `src`. Manifests written earlier keep the narrower hashes. |

Evaluation types:
- **simulation_only:** synthetic validation, nulls, out-of-class nulls, and the RMM and gate transfer tests.
- **Loss-stream replay of dataset-derived model losses:** the fresh and exposed real-data runs. The auditor classes this as `synthetic_proxy` for the policy replay. The losses come from real labels, but the online label channel is reconstructed.
- **Proxy-labelled:** the real-data oracle diagnostics.
