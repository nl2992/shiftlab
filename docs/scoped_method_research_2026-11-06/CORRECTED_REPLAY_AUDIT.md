# Corrected Sprint 2 replay audit (2026-11-06)

## Scope and provenance

The primary checkout at `/Users/nigelli/Desktop/ICML/Shift-lab` completed adaptive-range correction replays, with the null suite produced from `c13f232...+dirty` and the other corrected suites from `c66185c0a1f3338e7422cfceeeedd0694867fb74`. These are same-seed correction replays, not independent validation. Raw records remain in the primary checkout's ignored `outputs/sota_sprint/validation/*_wmaxfix_20261105/` directories; this worktree contains only compact analyzed summaries. The unchanged user-owned replay audit is `docs/sprint2/adaptive_gate_replay_differences.md` in the primary checkout (99 regime-policy cells, 130 run-level changes across its comparisons).

Contract for the five suites: `T=2000`, pathwise `B=200`, `c_q=.05`, `c_s=5`, `alpha=.05`. Corrected real-exposed used 10 policy seeds and 9 previously exposed data sources; corrected real-fresh used 20 policy seeds and 5 previously exposed sources. “Fresh” denotes newly generated policy RNG streams, not new or untouched datasets. The synthetic suite used 100 seeds for each of 21 regimes. Source manifests and raw-record SHA-256 values are listed below.

## Null and out-of-class outcomes

In the corrected 1,000-seed `V_null` suite, promotion counts were 0/1000 for ordinary adaptive-range Gated, 1/1000 for Gated+front, and 1/1000 for Gated+pace-tuned. These are empirical rates under the simulator's specified null, not proof of anytime validity. Under dependent null stresses, the ordinary host and acquisition variants diverge materially: for example, at `V_null_dep_r8`, counts were 9/1000, 106/1000, and 105/1000 respectively; at `W_null_dep_r95`, they were 115/1000, 386/1000, and 385/1000. These dependent cases are robustness stresses and must not be called violations unless they lie in the method's stated null class. The null suite does not establish the validity of C2/C6 under their required target null.

The two out-of-class suites also show why a general risk claim is not supported. In `O_null_order2`, C2/C6 promoted 216/1000 and 208/1000, versus 31/1000 for ordinary Gated and 239/1000 for Gated+front. In `O_null_semimarkov`, counts were 140, 126, 62, and 171 respectively. These are not a common theorem target; report them as stress outcomes, alongside costs.

## Corrected synthetic comparison

The 100-seed, 21-regime summary is `corrected_synthetic_replay.json` and its full table is `corrected_synthetic_replay.md`. It reinforces a regime-specific trade-off, not a general winner. In the late alternatives, C2 and C6 have lower average net cost than Gated+front: `V_late_600` differences are −7.7 (95% paired interval [−9.3,−6.1]) and −7.5 ([−8.4,−6.6]); `W_late_1000` differences are −7.4 ([−7.8,−7.1]) and −7.8 ([−8.1,−7.6]). In these same cells promotion remains rare (C2 1% / 0%, C6 0% / 0%) and query counts fall sharply. The benefit is largely an economic decision to stop spending labels when evidence does not arrive; this does not establish increased timely promotion of a late-improving model.

Outside those cells C2/C6 lose to the front-loaded host in several improving, dependent, and reversal regimes. Example: on `W_reversal_700`, net costs are 407.9 / 406.7 for C2/C6 versus 369.1 for ordinary Gated, a roughly 38-unit disadvantage. Their existing code and prior exposure make these outcomes discovery/falsification evidence, not a novel repair confirmation.

## Corrected retrospective real replays

Source-level uncertainty uses sources as units; episode-level intervals are not used to claim independent transfer.

* **Five-source previously exposed cohort (`real_fresh_wmaxfix_20261105`):** mean per-source paired `J(Gated) − J(Gated+front)` is +46.12 (positive favors front-loading), but its equal-source 95% t interval is [−7.86, 100.11], n=5 independent source clusters. Source effects are metro +47.13, Beijing PM2.5 +1.98, bike +45.40, appliances +116.29, household power +19.82. Front vs tuned-pace is +0.28 [−0.17, +0.73]. Front vs C2 is +0.02 [−1.76, +1.79]; front vs C6 is −0.16 [−2.91, +2.59]. Thus the simple pacing variants are not distinguishable at source level, while the front-versus-unmodified gap has a large but uncertain mean driven by five clustered sources.
* **Nine-source previously exposed cohort (`real_exposed_wmaxfix_20261105`):** the earlier paired cluster report gives mean per-source `J(Gated) − J(Gated+front)` +12.56, 95% source-t interval [+0.96, +24.16] (sign convention positive favors front). Front versus tuned pace is +0.63 [−0.55, +1.80]; C2 versus front is −0.93 [−3.76, +1.91]; C6 versus front is −0.14 [−4.99, +5.27]. Episode counts are not independent-source counts.
* **Combined equal-source cohort (14 dataset-source clusters):** recomputed from paired records by averaging episode-seed contrasts within source and weighting each source equally, `J(front)−J(Gated)` is −24.55, 95% t interval [−42.81, −6.29]; `J(front)−J(pace_tuned)` is −0.30 [−1.05, +0.45]; `J(front)−J(C2)` is +0.60 [−1.15, +2.35]; and `J(front)−J(C6)` is +0.03 [−3.07, +3.14]. The 14 source-level effects are in `corrected_real_14_source_clusters.json`. Recompute with `python3 research/scoped_method/analyze_real_source_clusters.py /Users/nigelli/Desktop/ICML/Shift-lab/outputs/sota_sprint/validation/real_exposed_wmaxfix_20261105/records.jsonl /Users/nigelli/Desktop/ICML/Shift-lab/outputs/sota_sprint/validation/real_fresh_wmaxfix_20261105/records.jsonl`. This combined interval is still retrospective and exposed; several sources are related temporal/predictive domains, so it must not be interpreted as independent domain confirmation.

Both cohorts use previously exposed underlying datasets and generated model-pair/loss streams; their imposed label delays are not authentic label-release logs. The five-source cohort further overlaps Beijing-derived task families. Neither cohort meets the brief's independent real confirmation gate. The strong episode-level differences on appliances, bike, metro, spam, occupancy, weather and OpenML must be disclosed as source-specific descriptive replay results.

## Frozen decision consequence

The corrected outputs do not supply a new confirmed method. C2/C6 already existed and were selected using prior exposed experiments; their late-regime cost advantage is interpretable but not new confirmation and not improved promotion. Simple front-loading often accounts for the early-promotion effect. E_rb's separate reversal advantage remains confounded by rollback alpha/start-grid choices and lacks the matched restart-grid/two-sided-control falsification described in `BASELINE_FIDELITY.md`. No further candidate search is authorized by this report. Keep the paper decision at `BENCHMARK_OR_CASE_STUDY_ONLY` unless a separately frozen, non-overlapping method and source protocol is approved prospectively.

## Reproduction manifest

Paths are relative to the primary checkout unless marked otherwise. Summaries were produced with repository analysis code, including `scripts/sota_sprint/analyze.py`. The original analyzer command lines were not persisted in the replay manifests, so this report does not invent them; the exact raw paths, run manifests, source hashes and record hashes are provided for recomputation. The analysis JSON/Markdown are copied beside this report.

| Suite | Manifest git | Manifest SHA-256 | Raw records SHA-256 | Size bytes |
|---|---|---|---|---:|
| `null1000_wmaxfix_20261105` | `c13f232...+dirty` | `645e0028e829d6af8e3c61bd6e4089537f506214dccf381629525cdae287c63a` | `0008f8fc8a755bf8471fb0bcaf6cfcd383c62ac6d55357fee711e5a6655398b5` | 11,844,622 |
| `ooc1000_wmaxfix_20261105` | `c66185c0a1f3338e7422cfceeeedd0694867fb74` | `eb307e7c41d08b35c2436a208bcb9fdb14aa46569550f90c7c87d93b38457511` | `5a731dd659343acdc0cea9616a40a1d0463f7adb0d3a36e6436de48304a374fa` | 4,496,485 |
| `synth_wmaxfix_20261105` | `c66185c0a1f3338e7422cfceeeedd0694867fb74` | `074ee2ae4952e3ebdc077406b8632a1aa6b222f1065d290ba1330fab97191d48` | `d57a084e02217f7ff3ec4dfbf6f0b0ac4932721d49fa4dbebadf07f7277e3de1` | 5,971,017 |
| `real_exposed_wmaxfix_20261105` | `c66185c0a1f3338e7422cfceeeedd0694867fb74` | `896982b87ee7c8e672b687f01eaed65792942de8f3a28dc49017dfbae60917d5` | `5d857b7ad65127e8106bab265344b4aa5ac7316ebd98a0ad8fb89b5043da1b99` | 4,720,504 |
| `real_fresh_wmaxfix_20261105` | `c66185c0a1f3338e7422cfceeeedd0694867fb74` | `22e3cdf253d366ea1b75371d9b4f1f632a77b708f0b46fa28cfb2d18b5762400` | `301149c3b42e0853349eb8da3c1119c70ec1b90f6c917f025cddf13601f819a4` | 3,534,403 |

The primary-run manifests record exact arguments, code hashes and git commit. Raw ignored outputs are not copied into this worktree or Git.
