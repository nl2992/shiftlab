# WP1 S3: gated-versus-ungated comparison results

**Decision: both co-primary endpoints PASS. Gating is material, and G1's growth prediction is
confirmed.**

This is a fresh development comparison on the registered block `58400000–58400099`, with 100
streams per scenario × budget. It ran under the [frozen protocol](gated_vs_ungated_monitor_comparison_protocol.md)
with the [numerical amendment](gated_monitor_s3_numerical_amendment.md). Gating is DISCERN's
mechanism. **No new-method claim follows.**

## Co-primary endpoints (`boundary_local_harm`)

| Endpoint | Registered rule | Result |
|---|---|---|
| P1: growth ratio, paced gated HT / correctly bounded uniform, `r = 0.20` | One-sided 97.5% lower bound ≥ 2 | **7.20** (95% interval 6.88–7.55): pass |
| P2: paired detection difference, `r = 0.05` | Lower bound > 0 | 100 discordant wins, 0 losses; McNemar one-sided `p = 7.9e-31`: pass |

**G1's analytic prediction against the measured growth ratio** (each within the registered
factor of two):

| Budget `r` | Predicted | Measured |
|---|---:|---:|
| 0.02 | 18 | 17.5 |
| 0.05 | 18 | 20.6 |
| 0.10 | 15 | 14.7 |
| 0.20 | 7.5 | 7.2 |

**At `r = 0.05`, at about equal labels and dollars:**

| Arm | Detection | Censored delay | Labels |
|---|---:|---:|---:|
| `gated_ht_paced` | 1.00 | 496 | 118 |
| `gated_ht_paced` + Timans GRAPA | 1.00 | 469 | 118 |
| `ppe_gated` (source-factor alias) | 0.99 | 451 | 118 |
| `uniform_ppi` (bound 45.9) | 0.00 | 1,616 | 114 |
| `uniform_ppi` + Timans GRAPA | 0.01 | 1,611 | 114 |
| `xu_active` | 0.00 | 1,616 | 115 |

The full-feedback reference detects 1.00 with delay 407; it is unmatched.

## Validity in S3's own null cells

The largest false-alarm rate is 2/100 in both `stationary` and `benign_nuisance`, across every
arm, engine and budget. S2 remains the registered calibration.

## Panel findings

1. **Every gated arm dominates every ungated arm at scarce budgets.** In `boundary_local_harm` at
   `r ≤ 0.05`, gated arms detect 0.82–1.00 and ungated arms 0.00–0.01.
2. **The best selective-label arms are published compositions.** These are gated HT or gated PPI
   with Timans GRAPA (mean detection 0.99) and the PPE gated alias (0.99). The engine adds a few
   points at `r = 0.02`.
3. **The PPI proxy adds nothing over gated HT** in `boundary_local_harm`. Under
   `harmful_adaptation` it hurts: mean detection 0.36–0.39 against 0.50–0.59 for gated HT.
4. **R7 prediction falsified.** The regime map predicted that past-paced gating would hold
   coverage better than a fixed rate when disagreement rises. Under `harmful_adaptation`, fixed
   gating is equal or better at every budget: 0.86 against 0.76 detection at `r = 0.10`, with
   censored delay 370 against 1,028 under GRAPA. This replicates, on synthetic paths, the
   burst-pacing failure seen on EIA injected harm ([WP4](eia_real_data_validity_results.md)).
5. **Low budgets under harmful adaptation fail for every selective arm** (at most 0.33 detection at
   `r ≤ 0.05`). Disagreement rises from about 9% to 42%, and the reserve is exhausted.

## Regime outcomes (development stage)

- **R2 and R3: tie, no method claim.** The gain is from gating (DISCERN) plus published engines.
- **R7: paced incumbent beaten by fixed gating.** Both are DISCERN-style compositions, so this is
  a benchmark finding, not a method.

## Reproduction

```powershell
$env:OMP_NUM_THREADS=1; uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage compare --workers 6
uv run --no-sync python scripts/analyze_gated_monitor_comparison.py --stage compare
```

- **Run.** 1,521 s on 6 workers with CUDA, from HEAD `d0d49f6`. The amendment and this session's
  WP4 files were uncommitted at launch; they are listed in `launch.json` and `manifest.json`,
  together with their source hashes. The amendment is committed in `a4c3800`.
- **Artifacts:** `outputs/gated_monitor_compare/` (`streams.parquet`, `manifest.json`,
  `analysis/summary.csv`, `analysis/decision.json`). The two earlier crashed launches are kept
  beside it.

## Continue / pivot / stop

WP1 has reached its exit. Its findings go into the benchmark manuscript:
- the repository's earlier ungated "sparse labels lose power" conclusions are mostly label waste;
- the G1 growth calculation predicts realised growth within about 15%;
- under bursty disagreement, fixed gating should be preferred to past-paced gating.

No method claim follows.
