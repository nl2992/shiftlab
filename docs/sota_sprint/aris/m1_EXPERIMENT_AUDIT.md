# Experiment audit, milestone 1 (ARIS `experiment-audit`, cross-model)

**Date:** 2026-11-03

**Auditor:** Codex CLI 0.163, model `gpt-reserve` at medium effort. It reported itself as
`Reviewer-Model: gpt-5`. The user approved this cheaper tier. The audit was read-only.

**Executor:** claude-opus-5-5. The reviewer is from a different model family, as ARIS requires.

The skill is the ARIS `experiment-audit` SKILL.md from wanshuiyin/auto-claude-code-research-in-sleep at
commit f76ec8d, with the exact prompt. The executor passed file paths only. The prompt, route and raw
response are in `.aris/traces/sota-sprint/2026-11-03_m1/`, which is gitignored. The raw response is also
copied to [m1_experiment_audit_codex.md](m1_experiment_audit_codex.md).

## Overall verdict: FAIL (one critical item), all items acted on

| check | status | action taken |
|---|---|---|
| A. Ground truth | WARN | Real-data `gain` is the realised mean advantage, a proxy. `screen.py` now labels it (`gain_is_proxy`) and documents which diagnostics use it. The primary metric `net` does not use it. |
| B. Normalisation | PASS | none needed |
| C. Results exist/match | PASS | none needed. The reviewer recomputed C2 B100 +24.4, D1 53/300 and C2 nulls 2/300 and 18/300. |
| D. Dead code | WARN | `suite.run_metrics` is the FLQ runner's metric. The sprint uses `screen.metrics` only. Recorded here; FLQ is left untouched for continuity. |
| E. Scope | WARN | Development evidence is 20 seeds and synthetic only. The reports already call it screening; no broader claim is made from it. |
| F. Type | simulation_only (dev); real_gt intended for the fresh streams | none needed |
| **Critical** | **FAIL** | **`gate_audit.py` pooled records by policy name across families, so A1 was credited with Family D runs. Fixed: records are now keyed by (family, policy). The gate is re-evaluated on a family-isolated re-screen at the committed revision (`outputs/sota_sprint/gate/`).** |
