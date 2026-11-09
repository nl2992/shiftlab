# 00 — Paper 1 scale-25 master plan

Mandate: the user brief of 2026-11-09 ("MASTER AGENT PROMPT — ShiftLab Paper 1: 25+ Dataset Discovery, 2.5% Certified Improvement…"). Initial state and feasibility are in `01_REPOSITORY_AUDIT.md`.

**Hard rules**
- No CVaR, tail or worst-case gates anywhere.
- Mean net cost is the objective.
- The selected cohort is disclosed as selected, and the full ledger is kept.
- Frozen v1 and the Nov-9 evidence are never revised.
- Confirmation windows stay unopened until a protocol is registered with hashes.
- New method versions get new confirmation data.

## Workstreams (run in parallel; each owns disjoint files)

| WS | scope | outputs | milestone |
|---|---|---|---|
| A — datasets | inventory of all 45 existing C4 recipes plus discovery of ≥50 new candidates (311, transport, energy, weather, finance, temporal NLP, OpenML/WILDS streams, other); D0 metadata eligibility; dev/confirm window definitions; D1 dev-window builds and headroom | `DATASET_DISCOVERY_LEDGER.csv`, `DATASET_SOURCE_REGISTRY.json`, `DATASET_ELIGIBILITY_PROTOCOL.md`, `02_*`, `03_*`, `scripts/paper1_scale25/data/` | P1, P4 |
| B — algorithm | brief §10 ablation table on dev data (interaction, label-matched uniform and uncertainty); headroom by component for v1; v2 candidates aimed at late adoption, searched on dev data only | `04_*`, `06_*`, `scripts/paper1_scale25/algo/` | P3 |
| C+E — fidelity and novelty | faithful-comparator audit and upgrades; prior-art audit; novelty matrix; reduced exact DP | `05_*`, `PRIOR_ART_AUDIT.md`, `NOVELTY_MATRIX.md`, `THEORETICAL_ANALYSIS.md`, `11_*` | P2, P7 (part) |
| D — statistics | per-dataset one-sided lower bounds for relative reduction (block or cluster resampling over chronological episode blocks); α_i = .05/(i(i+1)) attempt ledger; cohort certificate; power analysis; tests | `07_*`, `09_*`, `scripts/paper1_scale25/stats/`, `tests/paper1_scale25/` | P5 machinery |

## Sequence

1. P0 audit (done).
2. WS A–D in parallel.
3. D2 cheap screen of v1 plus controls on new dev windows.
4. D3 full dev evaluation; freeze v1 (or v2) and the reference per dataset rule.
5. Register cohort confirmation (07) with hashes.
6. Open once.
7. Certify (09).
8. Results (10).
9. Manuscript readiness (12), then decision (13).

Continue discovery while the target is unmet and sources remain.

## Counters (kept separately, never merged)

- discovered;
- downloaded;
- eligible;
- dev-screened;
- dev-positive;
- confirmation-opened;
- confirmation-positive;
- statistically supported;
- selected cohort.
