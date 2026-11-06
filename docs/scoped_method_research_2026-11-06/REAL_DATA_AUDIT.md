# Real-data evidence and construction audit

## Existing evidence

Current WP1 evidence uses 348 chronological paired-loss episodes across 14 dataset sources, but those streams and classes have been exposed during development. The registered late-improvement stratum is 10 episodes from five source clusters. RMM versus the selected best certified comparator has four host intervals, all crossing zero (NOT_SUPPORTED). RMM also does not significantly beat matched E_srr on that stratum. The reversal stratum has 16 episodes from seven clusters; E_rb has mixed host intervals and is not independent confirmation. See `docs/sprint2/wp1/RESULTS.md`.

## Authenticity and chronology limitations

- Nine cached real streams were used in earlier development; five UCI streams and derived windows were used in Sprint 2. Re-splitting or changing windows does not make them untouched sources.
- `scripts/failure_atlas_v2_flq/suite.py` constructs balanced labels and predictions from labels XOR loss values. This supports paired-loss replay but does not recreate model training and prediction chronology.
- Delays in the replay runner are imposed experimental delays, not observed dataset label-release timestamps.
- Current policy comparisons use paired loss traces. They do not establish an application-level causal intervention effect unless both policy outcomes are identified under the observation design.
- Episode bootstrap intervals are not independent-source confirmation. Report source-cluster counts and source-level uncertainty; the late stratum has only five source clusters.

## Fresh source registry status

No newly sourced independent chronological dataset was run in this execution. Wild-Time includes HuffPost and arXiv chronological tasks ([official benchmark site](https://wild-time.github.io/), [NeurIPS Datasets & Benchmarks paper](https://papers.nips.cc/paper_files/paper/2022/file/43119db5d59f07cc08fca7ba6820179a-Paper-Datasets_and_Benchmarks.pdf)); it is a candidate, not confirmation evidence. Task timestamps do not alone prove point-in-time label release. Before use, freeze source version/checksum, model training cutoffs, prediction timestamps, label availability/release clocks, missingness, policy pairing, source clusters and windows. Keep the candidate developer from seeing any held-back confirmation outcomes.

UCI Online Retail II and Beijing Multi-Site Air Quality are also possible time-series/task sources, but a predictive target, training schedule and realistic label-release process must be defined prospectively. A convenient change episode must not be selected after outcomes are inspected.

The repository also contains a distinct OPSD load-reserve task and Binance momentum task spec under `docs/lane_b_burst_allocation/R1_task_specs.md`, with frozen development task code in `src/shiftlab/real_tasks/`. OPSD uses an externally verified ENTSO-E publication rule as its nominal feedback clock; Binance uses hourly market bars and an imposed one-bar label release. Both task specs mark their 2020 and 2026 holdouts unexposed, respectively, and the handoff prohibits access until a separate method-specific freeze and one-opening runner exist. Their development costs are imposed, OPSD snapshot revisions remain a threat, the OPSD holdout choice was not blind, and Binance fees are proxies. The active worktree has no raw OPSD/Binance files available; no holdout was read or fetched here. These are follow-up testbeds, not evidence for the present candidate.

## Smallest next action

First freeze a distinct repair and baseline/test protocol using development-only records. Then verify the raw OPSD/Binance checksums, implement and test the required one-opening runner, and use at least two distinct source domains if the prespecified target supports both. Do not open either locked holdout before those conditions are satisfied. If no method survives bounded synthetic falsification, close C4 for this method claim instead of opening data to search for a positive result.
