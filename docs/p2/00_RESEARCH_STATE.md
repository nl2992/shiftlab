# P2 null-aware deployment: research state

Branch `research/p2-null-aware-deployment-2026-11-09`, worktree
`ICML/shiftlab-p2-nad-2026-11-09`, created 2026-11-09 from `origin/main@8af33afe`.

## 1. Recovery

| Step | Result |
|---|---|
| Source | `origin/claude/shiftlab-progress-review-c30588@350bc596` (28 commits ahead of its merge base with main) |
| Method | `git merge --no-ff`. 23 conflicts, all between main's ruff-format commit `8af33afe` and P2 logic changes. P2 side taken (`--theirs`), then `ruff format`. Commit `3292e3e7` |
| Tests | `tests/sota_sprint tests/sprint2` 384 passed; `tests/p2_benchmark` 4 passed |
| Not merged | Paper 1 branches (EQSDp, search60, QSG methods search). Their findings are cited here as prior development evidence only |

Recovered material: `docs/p2_benchmark/` (scope, H1–H8 registrations and results, comparator
fidelity, related work, W5 scope), `scripts/p2_benchmark/`, `scripts/sota_sprint/` (P2 runner and
families), `scripts/failure_atlas_v2_flq/`, `docs/scoped_method_research*/`.

Raw P2 run directories (`outputs/p2_benchmark/`) are **not on this machine**; the results docs carry
their SHA-256 hashes. Loss arrays needed to regenerate them are present: `data/sprint_fresh_losses`
(5 UCI sources), `data/sprint_twin_losses`, and in the main checkout `data/c4_sealed` (27 municipal
and transport streams built for Paper 1; exposed in Paper 1 development, never used in P2).

## 2. What P2 establishes (evidence class in brackets)

| # | Finding | Evidence |
|---|---|---|
| F1 | V1 (conditional-null) certificate ports promote at ~2α on exact real-data marginal-null twins | Confirmatory, twin v3: .098 [.091,.106] |
| F2 | Those promotions are conditionally informed | Confirmatory: mean remaining advantage .0152 [.0114,.0198] |
| F4 | Uncertified selectors (CAMS, Model Picker) promote on most nulls | Confirmatory |
| F5 | Dependence robustness is expensive: J(A5b) − J(QSG) on synthetic dependent alternatives | Confirmatory: +50.3 [+47.0,+53.5] per episode |
| F7 | A5b (V2) exceeds α on bike_hour | Confirmatory: .089, 99% LB .067 |
| F8 | Two-tier gate (claimed-null + dependent-null decision harm ≤ 5) admits gated_adaptive_range, 37.5 cheaper than the all-null gate's only admittee | Registered H8c, supported. Offline admission rule, **not a sequential algorithm** |
| — | Real twins never bind Tier B (decision harm UB ≤ 1.46); every Tier B rejection comes from synthetic ρ=.95 | H8 post-hoc |
| — | never-switch (419.9) is cheaper than discern_style (429.8) on the alternatives | H8 |

Comparator fidelity open issues: MOPE port endpoints ~1.2–1.6× wider than author code (valid,
less powerful); Choe–Ramdas stand-in more aggressive than `comparecast`; no DISCERN code exists.

## 3. Prior development evidence elsewhere in the programme (not P2 claims)

- Paper 1 / QSG search: on uncertified economic switching, a dozen mechanisms tie tuned Wald
  within 1–1.6 units; an evaluator-side oracle restart gains 11.7, so that problem is
  information-limited. +100% free labels are worth ~5 units. Late-label cutoff and the E48+F60
  acquisition add-on give 0.4–0.9% (small, confirmed).
- Lane A: under tight risk a fixed calendar is exactly optimal for joint acquisition+switching.
- Failure Atlas cycle 6: gate validity under dependence tracks label spacing relative to
  correlation time.

Implication: the remaining large, unexplained gap in P2 is the **price of dependence robustness**
(F5, ~50 units ≈ 12% of J), not acquisition or switching heuristics, which earlier searches found
near their ceiling.

## 4. Real-stream dependence (descriptive, this session)

Autocorrelation of the disagreement subsequence `l0−l1 ≠ 0`, mean over episodes:
UCI sources lag-1 .29–.70, lag-5 −.01–.42, lag-20 ≤ .06; municipal sources lag-1 ≤ .23,
lag-5 ≤ .12. Dependence is short-range, and strongest on the UCI sources that break V1
certificates (appliances, household, beijing). Script: session scratch `dep.py` (to be moved into
`scripts/p2/`).

## 5. Status log

- 2026-11-09: branch created, P2 recovered, harness map and prior-art search running.
