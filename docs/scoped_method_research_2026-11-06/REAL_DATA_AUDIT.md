# Real-data evidence and construction audit

## Existing evidence

Current WP1 evidence uses 348 chronological paired-loss episodes across 14 dataset sources, but those streams and classes have been exposed during development. The registered late-improvement stratum is 10 episodes from five source clusters. RMM versus the selected best certified comparator has four host intervals, all crossing zero (NOT_SUPPORTED). RMM also does not significantly beat matched E_srr on that stratum. The reversal stratum has 16 episodes from seven clusters; E_rb has mixed host intervals and is not independent confirmation. See `docs/sprint2/wp1/RESULTS.md`.

## Fresh chronological HuffPost replay (2026-11-06)

The only source passing the frozen pretest regime gate was Wild-Time HuffPost. The untouched test window was opened once after the evaluator, data, models, eligibility, protocol, code and dependencies were hashed and independently reviewed. Raw data stayed local. The protocol, source receipt, pretest record, opening markers, result and checksums are under `research/scoped_method/pilots/chronological_news_transfer_20261106/`.

The corrected stable-row-ID validation gate has 8,786 rows, 6,953 disagreements, overall incumbent-minus-challenger error advantage `0.4046`, conditional disagreement advantage `0.5113`, and positive signed advantage in all three chronological blocks. On the 3,877-row 2018 test window, with 200 labels maximum, 0.05 label cost, 5 switch cost and a simulated midnight +24-hour release, canonical `PFA-SR:gated_adaptive_range` bought 200 labels but never promoted; its net cost was 3,163 (815.84/1,000 events), equal to never-switch prediction loss plus labels. Matched-host RMM promoted at event 1,498 and cost 2,039 (525.92/1,000); Xu acquisition-only promoted at event 254 and cost 1,454 (375.03/1,000). E_rb matched RMM because no post-promotion rollback occurred. E_swcert cost 1,627.95 (419.90/1,000).

The paired PFA-SR net-cost contrast was **+289.91/1,000** versus same-host RMM (95% 7-calendar-day moving-block interval `[+193.64,+391.18]`) and **+440.80/1,000** versus Xu (`[+394.19,+486.84]`). Both frozen transfer gates fail by a wide margin. This is an adverse, single-source time-blocked case study; it does not support a generalization claim, a real label-release claim, or PFA-SR's iid conditional-null guarantee under serial dependence. Date-only timestamps require the registered simulated feedback clock. The policy constructors use the median validation articles/day as their integer event-delay pacing parameter; actual feedback availability is still timestamped. UCI News Aggregator and MN-DS failed the validation eligibility gate and remained locked.

Exact artifacts: `run/wildtime_huffpost/TEST_OPENED.json`, `transfer_results.json`, `prediction_stream_sha256.json`, `source_eligibility.json`, `pretest_manifest.json`, and `code_freeze.json`. Row-level traces and target values were not written to Git. This reproduces a scoped PFA-SR late-improvement failure, not a repair or positive method transfer.

## Authenticity and chronology limitations

- Nine cached real streams were used in earlier development; five UCI streams and derived windows were used in Sprint 2. Re-splitting or changing windows does not make them untouched sources.
- `scripts/failure_atlas_v2_flq/suite.py` constructs balanced labels and predictions from labels XOR loss values. This supports paired-loss replay but does not recreate model training and prediction chronology.
- Delays in the replay runner are imposed experimental delays, not observed dataset label-release timestamps.
- Current policy comparisons use paired loss traces. They do not establish an application-level causal intervention effect unless both policy outcomes are identified under the observation design.
- Episode bootstrap intervals are not independent-source confirmation. Report source-cluster counts and source-level uncertainty; the late stratum has only five source clusters.

## Other fresh source registry status

No additional newly sourced independent chronological dataset was run. Wild-Time arXiv, OPSD and Elexon remain follow-up candidates, not evidence for this result. Task timestamps do not alone prove point-in-time label release. Before use, freeze source version/checksum, model training cutoffs, prediction timestamps, label availability/release clocks, missingness, policy pairing, source clusters and windows. Keep the candidate developer from seeing any held-back confirmation outcomes.

UCI Online Retail II and Beijing Multi-Site Air Quality are also possible time-series/task sources, but a predictive target, training schedule and realistic label-release process must be defined prospectively. A convenient change episode must not be selected after outcomes are inspected.

The repository also contains a distinct OPSD load-reserve task and Binance momentum task spec under `docs/lane_b_burst_allocation/R1_task_specs.md`, with frozen development task code in `src/shiftlab/real_tasks/`. OPSD uses an externally verified ENTSO-E publication rule as its nominal feedback clock; Binance uses hourly market bars and an imposed one-bar label release. Both task specs mark their 2020 and 2026 holdouts unexposed, respectively, and the handoff prohibits access until a separate method-specific freeze and one-opening runner exist. Their development costs are imposed, OPSD snapshot revisions remain a threat, the OPSD holdout choice was not blind, and Binance fees are proxies. The active worktree has no raw OPSD/Binance files available; no holdout was read or fetched here. These are follow-up testbeds, not evidence for the present candidate.

## Smallest next action

First freeze a distinct repair and baseline/test protocol using development-only records. Then verify the raw OPSD/Binance checksums, implement and test the required one-opening runner, and use at least two distinct source domains if the prespecified target supports both. Do not open either locked holdout before those conditions are satisfied. If no method survives bounded synthetic falsification, close C4 for this method claim instead of opening data to search for a positive result.
