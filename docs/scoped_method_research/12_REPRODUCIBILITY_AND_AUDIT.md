# Reproducibility and audit trail

## Code and worktree

- Worktree: `.claude/worktrees/scoped-method-research-current`
- Branch: `codex/scoped-method-research-current`
- Research code base before this package: `c66185c0a1f3338e7422cfceeeedd0694867fb74`
- Primary checkout contains user-owned dirty files; this worktree was used to preserve them.
- Raw large replay records remain outside Git in ignored primary-checkout output directories. The
  copied JSON/Markdown summaries and checksums are retained under
  `docs/scoped_method_research_2026-11-06/`.

## Reproduction inventory

| Evidence | Command / record | Reproduction status |
|---|---|---|
| Graphify map | `.codex/skills/graphify/SKILL.md`, `graphify-out/`, queries for simulator, baseline, acquisition, guarantee, deployment, audits, datasets and tests | Graph build completed; source checks are described in `01_GRAPHIFY_MAP.md`. Graph outputs are local, not committed as a large binary corpus. |
| Corrected null/OOC/synthetic/real suites | Five raw suites and hashes listed in `../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md` | Raw files remain in ignored `outputs/sota_sprint/validation/*_wmaxfix_20261105/`. The report notes original command-line gaps; do not invent them. |
| Source-cluster recomputation | `python3 research/scoped_method/analyze_real_source_clusters.py <real_exposed_records.jsonl> <real_fresh_records.jsonl>` | Requires the ignored raw record files from the primary checkout; outputs saved as `corrected_real_14_source_clusters.json`. |
| Development pilot | Exact command is in `06_DEVELOPMENT_PROTOCOL.md` | Results, generated file hashes and runtime to be appended to `07_DEVELOPMENT_RESULTS.md`; not confirmatory. |
| Tests | The earlier execution log retained suite paths/counts but not the exact isolated shell invocations | Three isolated groups passed 43, 22 and 106 tests, respectively (171 total). A combined invocation has a top-level `regimes` import collision; see `00_STATE_AUDIT.md`. Do not treat an inferred command as an exact reproduction command. These are regression checks, not statistical validation. |

## Data and claim controls

The null, out-of-class, synthetic, and real suites have distinct seed/source scopes. “Fresh” in an
existing cohort means new policy RNG seeds on exposed sources, not fresh source data. Source-level
uncertainty uses dataset-source clusters, not episodes, and the combined 14-source estimate is
retrospective and exposed. No held-out real result is in this package. No theorem follows from
empirical false-promotion counts.

Graphify, run manifests, code commit, and outputs are navigation/reproducibility aids; preserve the
historical registered reports unchanged. Before a manuscript release, regenerate SHA-256 values for
all included artifacts from the final tree and replace any provisional hashes with exact values.
