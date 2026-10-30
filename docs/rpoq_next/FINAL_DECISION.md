# Decision record (2026-10-30)

**Scope of this record:** Candidate A (growth-aware, signal-aware label allocation with per-context bets). Candidates B and C were not developed. Historical RPOQ results are unchanged.

## What the evidence says

| Gate | Result |
|---|---|
| Source audit | **Incomplete.** The mandatory primary papers could not be fetched; two (Pro-Active Inference, Active MPPI) are unread by anyone on this project. Novelty is unassessed |
| Synthetic A1 | Not passed (oracle subgroup effect; my tie prediction was wrong: SNR, not signal, must be constant) |
| Synthetic A2 | Not passed (tie control). The online-learning variant was worse than uniform |
| Synthetic A2b | Inconclusive (placebo gap in const +0.083; against the best fair baseline +0.02) |
| Synthetic A3 (fresh seeds, fair baselines) | **Supported with restriction:** `het` Δ ≈ +0.215 [0.18, 0.25], calibrated, cap respected, tie control met; **fails** when the favourite loses signal (`het_flip` Δ = −0.120) |
| Real-data R0 (development splits only) | Heterogeneity and stability present for size contexts |
| Real-data R1 (exploratory; exposed test split) | **Negative:** Δ = −1.15 [−1.56, −0.76] at 5% and −3.21 [−5.16, −0.87] at 20% against the best baseline. The post-hoc diagnostic shows the predicted failure: the pre-test favourite bin lost most of its benefit |
| Theory | Moment identity proved; allocation equivalences conditional; no new guarantee |

## Classification
Candidate A is, at best, a **restricted special-case mechanism**: active concentration on estimated high-SNR contexts, beneficial when the alternative is heterogeneous across observable contexts and stays put. It is not a method that improves a strong existing algorithm in general, it is not shown to be new, and it was harmful on the one real stream tested. **It does not meet the bar for a methodological claim.**

## Adversarial self-review (no independent reviewer model was available)
- *Is the claimed novelty already published?* Unknown for two sources; plausible overlap with e-PS and active-subgroup ideas. Treated as not novel.
- *Is the comparison to SOTA fair?* Improved over time (best bet type per arm, placebo, SNR-constant control), but Robust ASI and online learning are adaptations; the repo's evidence-directed rule, PPRM, Podkopaev–Ramdas and `comparecast` were not run.
- *Does the result depend on an invalid information advantage?* A1 did (exact moments). A2/A3 learn them from the same budget. The oracle allocation was never treated as a ceiling.
- *Is the gain statistically meaningful?* Synthetic yes (A3). Real data: the effect is negative; intervals are anti-conservative.
- *Does it generalize?* No: the flip case and R1 show a specific failure.
- *Are the assumptions defensible?* The stratified intersection null and stationarity after burn-in are strong.
- *Best description?* A restricted hybrid/heuristic, not a new algorithm.

## Decision: **STOP Candidate A as a method claim; keep it as a documented, restricted finding.**

## What I would do next, and what blocks it
1. **Close the source gate** (needs `arxiv.org`, `proceedings.mlr.press`, `proceedings.neurips.cc`, `people.bath.ac.uk`, `doi.org`, `openreview.net` reachable, or the papers pasted in). Without it, no novelty statement is possible for any candidate.
2. **Candidate C (approximate the exact RPOQ oracle)** is the registered fallback. Its ceiling is small by the repo's own exact results (best constant table to optimum: +0.002 to +0.03 absolute power), so it is a computational/engineering contribution at best. It has not been started.
3. **A nonstationarity-robust allocator** would have to be tested on a genuinely untouched period. CRSP 2020–2025 is exposed; data after 2025, or another point-in-time dataset with release clocks, is required for any confirmation.
4. Run the missing benchmarks (evidence-directed rule, PPRM, Podkopaev–Ramdas, `comparecast`) before any comparison claim.
