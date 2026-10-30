# 01 Repository and evidence audit
Code commit at start: `8552911` (branch `research/shiftlab-mandate-gap-closure-2026-10-30`); sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: `docs/sota_gap_closure/*`, `outputs/gap_closure/*`, `configs/gap_closure/frozen_confirmation_v{1,2}*.json`, `tests/gap`, `tests/sota_search`. Theorem status: n/a. 
Re-verification performed in this sprint: 30 tests pass (18 gap, 12 sota_search) in a fresh environment; stored confirmation comparisons re-read from `outputs/gap_closure/e15_confirm/comparisons.csv`.

| starting claim | verdict | evidence |
|---|---|---|
| 1. HG > local PPRM-style parent (+0.029 / +0.052) | **VERIFIED** (Holm p .004 / .0025; CIs [.012,.046], [.020,.090]) | `comparisons.csv` |
| 2. no HG superiority over PH / CUSUM | **VERIFIED** (HG-PH -0.066 [-0.240,+0.079], -0.110 [-0.247,+0.005]) | same |
| 3. false-alarm inflation of e-process monitors under clusters / GARCH | **VERIFIED as an empirical fact**; its *interpretation* is audited in Gate A | `e6_stress_main`, Gate A script |
| 4. LRV heuristic: fewer false alarms, less power, no proof | **VERIFIED** (e14, round 1 informational arm) | `SECOND_ROUND_FIX_RESULTS.md` |
| 5. disagreement querying matches CAMS-style | **VERIFIED within this repo**; "CAMS-style" is a local source-inspired baseline, never the published CAMS | `Q2_BASELINE_REPRODUCTION.md` |
| 6. growth / pacing / balancing failed confirmation | **VERIFIED** (round 2 label-matched -0.023..+0.016) | `FINAL_CONFIRMATION_ROUND2_RESULTS.md` |
| 7. H2c / HG-branch obligations | **NOT AUDITED**: the H2c and original-HG research branches named in the mandate are not present in this repository's remote branch list (`rpoq-s1-fatal-flaw-audit`, `risk-preserving-switching-approx`, the two sota branches only). Marked UNRESOLVED; no claim here depends on them | `git branch -r` |
| 8. no broad novelty / no verified SOTA superiority | **VERIFIED, and strengthened by Gate C**: baselines are local source-inspired implementations | docs 01, Q2 |

Caveats that carry into this sprint: "HG" in the stored results is the **decision-cost-gated discounted Kelly e-process on a Brier channel**; the sprint's earlier-phase results are synthetic only; no real-data evidence exists on this branch.
