# NM-C4: real-data validation for the next method

**Status: BLOCKED for a new method (no C3 finalist).** Infrastructure and exposed-stream evidence
are recorded here so C4 can start immediately once a claim is frozen.

## Data audit

- **Exposed (development only):** 9 Atlas streams (`data/atlas_v2_losses`) and 5 Sprint streams
  (`data/sprint_fresh_losses`). Checksums verified on 2026-11-07 for both next-method runs.
- **Fresh candidates:** the C4 builder (`c4_build.py`, `c4_sources/`, binding brief
  `c4_source_brief.md`) seals test windows without computing any policy outcome. Built so far:
  - chicago_crimes: INELIGIBLE, disagreement 2.1% < 3%;
  - austin_animal and la_crime: build records in `c4_builds/`.
  Sealed windows were never opened, so they remain valid for **any** later frozen claim,
  including a changed algorithm.
- Remaining candidate list (c4_plan.md): nyc_311, nyc_collisions, nyc_restaurant_inspections,
  sf_311, nyc_tlc_taxi, citibike, chicago_taxi, uk_police, eia_ba.

## Exposed-stream development evidence relevant to choosing the C4 claim

| contrast (stream-equal pooled, 14 streams) | Δ | streams negative |
|---|---|---|
| EQSDp-B (frozen C4 arm) − tuned Gong–Zhang-style | **−5.7** | 13 / 14 |
| EQSDp-B − best real fixed Wald (λ=.97, γ=.2) | +6.0 [+2.3, +10.6] | 0 / 10 (≥5 episodes) |
| ESS-Wald (λ=.9) − its r≡0 ablation | −2.2 | 7 / 14 (5 ties) |
| ESS-Wald − best real fixed Wald | +2.3 | 1 / 14 |

**Implication.** The registered C4 claim (arm B beats tuned Gong–Zhang-style) is well supported
on exposed data. But arm B's λ=.9 is the wrong memory for real streams (M5). If C4 is re-frozen,
it is legitimate to change the arm *before* any sealed window is opened, since exposed data are
development. The cross-domain minimax choices are ESS-Wald (λ=.9, γ=.15) or Wald (λ=.95,
γ=.2). That change needs an amendment committed before the opening.

## Blocker

C4 for a *new* algorithm requires a C3 finalist. None exists, so no dataset was evaluated and
none is counted. Eight-dataset support is not claimed.
