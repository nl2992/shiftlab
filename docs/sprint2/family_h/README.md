# Family H: A5b x D2 hybrids (sprint 2, development only)

Code is in `scripts/sota_sprint/fam_h.py` (`HGate`, `UniformStartSUI`, plus the `diagnose` and
`summarize` CLIs). Tests: `uv run pytest -q tests/sprint2/test_fam_h.py` (50 passed). The ledger is
`ledger.json` and the diagnosis is `diagnosis.md`.

| file | contents |
|---|---|
| `screen_synthetic.json` | synthetic summaries |
| `screen_real_fresh.json` | real fresh-stream summaries |
| `track_R.json` / `track_R.md` | Track R curves |

Raw runs are in `outputs/sprint2/H/` (gitignored); run commands are in `run_chain1.sh` and
`run_trackR.sh`. The original screens use development seed base 2026110701, and Track R evaluation
uses 2026110711. A post-development H2 follow-up uses the separate Round-5 seed bases specified in
[`ROUND5_H2_AMENDMENT_20261104.md`](ROUND5_H2_AMENDMENT_20261104.md); it is not independent
confirmation. Empirical risk levels are not guarantees.

## Corrected comparator analysis (2026-11-04)

The `best_cert` cells in the original `screen_synthetic.json` and `screen_real_fresh.json` were
generated with a stale local comparator list: it included Xu's acquisition adapter and the
non-native Choe–Ramdas port, while omitting other ports in `bench.CERTIFIED_PUBLISHED`. Treat those
historical `best_cert` contrasts as non-authoritative for published-certificate comparisons. The
raw screens and JSON files are preserved. `fam_h.summarize` now uses the current registered pool by
default; `--legacy-comparator-pool` is reserved for exact reproduction of the old summaries.

A matched 20-seed fresh-real replay is complete at
`outputs/sprint2/round5/H_corrected_real_20/` on the five existing streams. It includes H1–H5/H6-r10,
the six registered certificate ports, and internal controls. Xu and Choe–Ramdas are separately
labeled supplemental adapters. The 1,240-job run wrote 21,080 unique policy/episode/seed records;
the manifest records seed base `2026110701`, four workers, the source and cache hashes, and runtime
of 1,145.3 seconds. The corrected analysis is in [`corrected_real_20.md`](corrected_real_20.md) and
[`corrected_real_20.json`](corrected_real_20.json).

On the equal-weight mean over the five fixed datasets, every H candidate is more costly than
`gated_adaptive_range` (+34.2 to +56.4 J) and `gated_adaptive_range+front` (+85.7 to +107.8 J),
with the episode-bootstrap intervals above zero. H1–H6-r10 are cheaper than `discern_style`
(-76.3 to -98.4 J), but this adapter's native fidelity limitations are described in the SOTA audit.
Relative to D2, H candidates cost +100.9 to +123.0 J; relative to A5b, H1 is -11.6 J (CI includes
zero), H2–H4 are -24.1 to -21.8 J (displayed intervals exclude zero), and H5/H6 are -4.2/-1.9 J
(intervals include zero). These are descriptive results on previously exposed streams. The
per-dataset lowest-cost port is selected
on the same data and shown only as a descriptive ranking. The episode bootstrap treats episodes as
exchangeable within each dataset; temporal dependence may make its intervals optimistic. No causal
shift labels are available.

## Answer to the central question
On synthetic data, yes, partly. H1/H2 match D2 on iid alternatives (+2 to +10 J) while keeping
V2 validity. They hold 0/20 on the F5 r8/r95 nulls, where D2 promotes .15/.70.
- H1 has two parts:
  - A5b `_B` evidence.
  - A single-cycle threshold 1/alpha, because promotion is absorbing and no second cycle exists.
- Against D5, H1/H2 recover F9 (-22), the delay alternatives (-6 to -13) and F1_late (-4).
The original 3-seed replay showed every H candidate losing to D2 by +62 to +240 J per episode; the
20-seed matched replay above refines that descriptive estimate to +100.9 to +123.0 J. The old +60
to +239 “best certified” range is withdrawn because its selected pool was misclassified and
incomplete (see above). The
14-source follow-up shows the same economic direction for H2: equal-source cost is +81.2
[38.1,136.1] vs D2 and +71.7 [30.1,126.4] vs `gated_adaptive_range+front`. H2's 1,000-seed Markov-null
rates remain below .05 on the four tested cells, while D2's are .192, .660 and .815 on persistent
nulls. These are post-development checks; see
[`round5_h2.md`](round5_h2.md) for per-regime results and limits.

D2's dependent-alternative and real "power" comes from the same iid reading of winning runs that
gives D2 .206 pooled promotion on the twin nulls. H1/H2/H4 have .04 there. Diagnosis C4 shows that
the tested SUI variants do not match D2's promotion rate on the specified strongly persistent
alternative; it does not establish an impossibility for all V2-valid methods.

## Track-R completion follow-up

H1 and H3 were screened post hoc over the full eight-alpha grid, with 20 development seeds per regime
for calibration and 20 separate evaluation seeds per regime. Their curves are merged with H2/H4 and
the shared D2/A5b controls in [`track_R_all.json`](track_R_all.json). H1/H3 add no Pareto point:
H2 is cheaper at R5, and H4 is cheaper at R10-R30 at the same observed risk. H5/H6 have now been
screened on Track R after a dedicated timing recheck; their costs remain higher than H2/H4 at the
tested points. These empirical rates are not guarantees.

## Unit-test fix recorded
The H5 reversal test was first built with fam_a start weights 1/(m(m+1)), and it never rolled back
on F3. It was replaced by `UniformStartSUI`, which uses ceil(B/10) equal-weight starts (still a
valid mixture). `H5-decay` keeps the old weights as an ablation. The screen1 rows for H5/H6 used
the old weights and are superseded by screen1b. screen1 was killed after F0_better/F7 finished
because of CPU load, so it has no manifest; screen1c and screen1b complete it.
