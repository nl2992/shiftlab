# WP3 prescreen: stop the adaptive observation-controller branch

The frozen 20-seed prescreen failed its advancement rule. Stop WP3 before any
development grid, null calibration, real-data run or confirmation block. This is
a development-screen result only; it does not establish validity or a confirmed
power difference.

The [protocol](data_efficient_edetector_prescreen_protocol.md) fixed the candidate,
cells, panel and margins before seed block 59000000–59000019 was used. The run
started at committed code HEAD `7536f1109468b9779deb4f03ced2c549dcfc18cf`, used
CUDA for path generation and two CPU replay workers, and finished 40 seed/onset
tasks in 1,708.82 seconds. Command:
`uv run --no-sync python scripts/run_data_efficient_prescreen.py --workers 2`.
The frozen analysis command was
`uv run --no-sync python scripts/analyze_data_efficient_prescreen.py`.

All 39,200 registered rows were retained: 20 seeds, onset fractions {.50,.75},
budgets {.02,.05,.10,.20}, every registered observation policy, source/composed
monitor, betting engine and detector. The primary cell compared the canonical
`optional_candidate/fixed1/sr` arm with 208 applicable same-null incumbent
configurations. The 20% cells contain 224 comparators because the historically
used common-96.9 uniform arm is defined only there. No arm was dropped after
outcomes.

## Primary result

At 75% onset and a 5% label-dollar budget, the candidate detected 11/20 streams:
55%, Wilson 95% interval 34.21%–74.18%. Its mean censored delay was 488.35 events,
using 48.05 labels and $71.50 against a mean $180.03 cap.

The strongest applicable registered configuration was the simple pre-specified
temporal policy with fixed-stake started evidence. It detected 20/20 streams:
100%, Wilson 95% interval 83.89%–100%, with mean censored delay 172.20, 110.40
labels and $165.59. Candidate minus incumbent detection was -45 points; the fixed
10,000-resample paired seed-bootstrap interval was [-65,-25] points. The
incumbent/candidate delay ratio was 0.353. The candidate used fewer resources,
but it met neither the required +10-point detection margin nor the required 1.5x
lower-delay margin. It therefore failed the primary gate.

The top primary configurations illustrate that the failure is not an isolated
engine comparison:

| Arm | Engine / detector | Detection (Wilson 95%) | Mean delay | Labels | Dollars |
|---|---|---:|---:|---:|---:|
| Temporal policy | fixed1 / started | 100% (83.9–100) | 172.20 | 110.40 | 165.59 |
| Temporal policy | plugin / started | 100% (83.9–100) | 185.55 | 110.40 | 165.59 |
| Temporal policy | fixed1 / SR | 100% (83.9–100) | 217.85 | 110.40 | 165.59 |
| Temporal policy | Timans GRAPA / started | 100% (83.9–100) | 254.10 | 110.40 | 165.59 |
| Candidate | fixed1 / SR | 55% (34.2–74.2) | 488.35 | 48.05 | 71.50 |

## Registered-cell candidate summary

| Onset | Budget | Detection (Wilson 95%) | Mean delay | Labels | Dollars |
|---:|---:|---:|---:|---:|---:|
| .50 | .02 | 60% (38.7–78.1) | 879.85 | 30.40 | 44.37 |
| .50 | .05 | 90% (69.9–97.2) | 509.25 | 89.40 | 133.52 |
| .50 | .10 | 95% (76.4–99.1) | 406.00 | 109.95 | 164.25 |
| .50 | .20 | 95% (76.4–99.1) | 405.25 | 110.30 | 164.96 |
| .75 | .02 | 20% (8.1–41.6) | 572.20 | 18.00 | 25.94 |
| .75 | .05 | 55% (34.2–74.2) | 488.35 | 48.05 | 71.50 |
| .75 | .10 | 75% (53.1–88.8) | 393.85 | 72.35 | 107.40 |
| .75 | .20 | 75% (53.1–88.8) | 391.40 | 72.80 | 108.25 |

Every secondary cell failed its registered all-incumbent non-inferiority and
resource rule. The candidate's qualitative mechanism behaved as predicted in the
protocol: it conserved pre-onset observations, but its evidence feedback stayed
too weak to raise intensity soon enough. The ranked fallback is the fixed temporal
schedule with started evidence for this synthetic late-onset setting. It is a
standard baseline finding, not a method claim.

Full feedback is an unmatched upper reference and feature ADWIN has a feature-shift
target, so neither is used as a same-null harm incumbent. Standard subgroup
composition has an intersection null and belongs to WP2. Comparecast weak-null,
PPRM predictive-risk and Q2 promotion methods remain excluded for target mismatch.
PPE/Xu source-factor aliases and gated/shared-betting compositions remain in the
complete tables; they are not silently treated as new published methods.

## Integrity and scope

An independent audit checked all 40 path files plus `streams.csv` against the run
manifest, all three analysis outputs against the analysis manifest, the exact
seed/cell panel, key executed-source hashes, and every finite spend cap. There were
zero hash, coverage or budget failures. The final repository suite passed 1,794
tests with one skip in 971.76 seconds.

The ignored artifact directory is `outputs/data_efficient_prescreen_20/`. Receipts:

| Artifact | SHA-256 |
|---|---|
| launch.json | 79aa44ffa0911f8a4d9284d76d5f1359182ae8cbfe77d80b0ab94b62edda2d18 |
| manifest.json | 282ddffba298953db2fe33c7165c7e1760507daada77223fecc0cb3404093f3c |
| streams.csv | 84f9f81554fb3dc22c7067c741812c3dd256556953c8332cdf438293e7fbd21c |
| analysis/summary.csv | 1da55ce007459de3cbb4632c42b1e1810a173db1a47c3703012cd1f2f8f2ca28 |
| analysis/paired.csv | d0678f4df216f8a13707fe241cf62351b569a7d23f2d11fe73272acd4f31c460 |
| analysis/decision.json | cb4248b2be6db78225fed918e84f65bbd95d5fdafba7e6b7f8329379ad273d50 |

PaperBanana is required for research figures, but no working PaperBanana/API
configuration exists in the pinned environment. No figure or substitute visual
was generated. The complete tables are the authoritative visualization for this
screen.
