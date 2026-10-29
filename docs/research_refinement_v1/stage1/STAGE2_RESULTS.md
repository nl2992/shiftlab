# Stage 2 confirmatory results: E2, E3, E4 (2026-10-28)

All three ran on CPU from frozen records (`P1_E2_freeze.json`, `P2_E3_freeze.json`,
`P3_E4_freeze.json`, commit `8aa5676`), on fresh registry seeds. The freeze checks passed at start.
Outputs are in `outputs/e2_confirmation/`, `outputs/e3/confirmation/` and
`outputs/e4_heldout/locked/` (gitignored). The commands are as in the protocols.

**Disclosures:**
- The E2 manifest records `git_dirty = true`. The tree had uncommitted changes to files *outside*
  the frozen list (P4 contract work); every frozen file matched.
- The E2 and E4 manifests record HEAD `7ea6923`. That commit landed during the chain and changed no
  frozen file.

## E2: acquisition and pacing (20,000 streams, 3,389 s)

| Hypothesis | Result | Status |
|---|---|---|
| H-B1a: gated beats uniform HT (gating ablation; DISCERN replication) | r=0.02: 734/0 discordant pairs, p≈1e-221; r=0.05: 914/2, p≈8e-271. Detection gated 0.70–0.97 vs uniform 0.00–0.05 | **Supported** (replication, credited to DISCERN) |
| H-B1b: acquisition expenditure ratio < 0.5 at r=0.20, joint detection condition | ratio 0.304 (upper 97.5% 0.308); detection difference lower bound +0.247 | **Supported** |
| H-B2 (i) fixed non-inferior to paced, post-onset burst | fixed − paced = +0.078 and +0.222 (lower bounds +0.060 and +0.203) | **Supported, and stronger than registered:** paced is clearly *worse*. The pacer throttles during a post-onset burst. |
| H-B2 (iii) fixed non-inferior to paced, recurrent | +0.042 and +0.128 | **Supported**; paced again worse |
| H-B2 (ii) paced beats fixed, harmless pre-onset burst | paced 0.996–0.999 vs fixed 0.546 / 0.055 / 0.000 | **Supported** (bands A and C are reserve exhaustion by construction; band B is informative) |
| Horizon-aware reserve baseline (descriptive) | (ii): 0.93 / 0.61 / 0.54; (i): best or tied best | Descriptive |
| Validity stop rule | no arm-engine withdrawn; worst pre-onset alarm rate 0.2% | Pass |
| Mechanism predictor (descriptive) | held-out RMSE 0.535 vs design-parameter baseline 0.556 | A retrospective association only. It narrowly beats the baseline here, where it lost on development data. |

**Reading:**
- **No fixed rule wins both burst regimes.** Paced loses when bursts are harmful, and fixed loses
  when bursts are harmless.
- **The horizon cap is a compromise** that loses in both regimes.
- **This is the concrete algorithmic gap:** an allocation rule that does not know in advance whether
  a burst is harmful.

## E3: intervention dose-response (1,000 seeds, 1,610 s)

| Estimand | Result |
|---|---|
| D(dose) = U(revert) − U(certify-promote), simultaneous 95% bands | Revert side at doses 0–0.45; promote side at 0.6–1.0; no unresolved doses |
| Crossover | **Located in (0.45, 0.6]**, adjacent bracket; trend slope −1,011 per unit dose (p < 1e-10) |
| Promotion component (promote vs continue) | Positive at doses 0–0.6, shrinking from about 314 to about 20; not detected at 0.8 or 1.0 |

**Reading:**
- The ranking reverses as the post-alarm reference deteriorates, which is H-B3's prediction on fresh
  seeds.
- Beyond the crossover the advantage is mostly the incumbent staying in place (abstention).
- The certification delay costs utility at every dose below 0.6.

## E4: locked held-out EIA authorities (21 authorities, 42 paths, 3,105 s; opened once)

| Hypothesis | Result |
|---|---|
| H-B4(a): orientation nulls | 714-cell Bonferroni family; **all cells validated**; 89 informative. Gated HT fixed/paced, gated EB and full feedback are **SUPPORTED** (6 informative paths, 4 authorities). Ungated HT is **INCONCLUSIVE**. |
| H-B4(b): fixed gating matches full-feedback delay (q < 1 cells only) | **INCONCLUSIVE.** All 201 detectable cells had q = 1 (structural; 97.5% exact match, which does not count). There are no q < 1 cells, so the transfer statement is **not established**. |
| R20 rule | All 21 authorities pass |

## What these results are for now

The user changed the goal on 2026-10-28: an ICML methodological contribution, not a benchmark paper.
These results are kept as **platform evidence**: verified baselines and failure modes. They are not
the manuscript. They motivate two algorithm-design problems:
1. **Allocation:** budget allocation under bursts whose harmfulness is unknown (E2).
2. **Switching:** certification delay and the switch-back decision as the reference deteriorates
   (E3).

E4 shows that the current real-data task has too little disagreement information for q < 1
evidence. A real dataset with denser disagreement and defensible timing is needed.

The P4 external-adapter gate is frozen. The implementer agent was stopped by a usage limit before it
finished.
