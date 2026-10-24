# Late start-time prior confirmation results

## Registered comparison

This independent confirmation compares the frozen nominal-horizon Beta(2,1) start-time mixture
with the uniform eight-start mixture. Each of 18 alternative cells has 2,000 paired streams; the
12 method-by-null cells each have 2,000 streams. The CUDA generator used disjoint seed ranges
20286000–20287999 for alternatives and 20288000–20289999 for nulls. Full design and the frozen
analysis are in [`late_prior_confirmation_protocol.md`](late_prior_confirmation_protocol.md).

## Findings

The primary seed-clustered macro detection difference was **+1.68 percentage points** for Beta(2,1)
over uniform (95% percentile interval **[+1.48, +1.88] pp**, 20,000 resamples). Beta(2,1) detected
69.09% of alternative streams versus 67.41% for uniform. Its detection rate was higher in 16 of 18
cells and lower in two. The largest loss was **4.30 pp** (query rate 0.10, onset 0.20, harm increase
0.12); the other loss was 2.90 pp (query rate 0.25 in the same onset/effect cell). Eleven cellwise
advantages and both losses were significant after the registered Holm adjustment. The candidate
also produced 76 pre-onset escalations across its alternative streams, versus 170 for uniform.

On the registered null controls, the largest false-escalation rate was **1.40%** and the largest
one-sided exact Clopper–Pearson bound with simultaneous 95% coverage was **2.25%**, below the 5%
criterion. All null cells passed. The generator resolved to CUDA throughout.

The candidate passes the protocol's three retention criteria: its clustered interval is above zero,
all simultaneous null bounds are below 5%, and no cell loses more than five percentage points.
Therefore retain Beta(2,1) as a validated option for this registered nominal-horizon design. The
two early-onset, low-harm losses show that the benefit is not uniform across conditions; keep the
uniform mixture as a useful reference and do not generalize this result to other horizons, delay
laws, dependence structures, query policies, or real data.

This confirms a finite-sample synthetic comparison under the specified bounded conditional-mean
assumptions. It does not establish a new algorithm, external validity, or a guarantee under adaptive
policy/candidate selection. The result supports only the fixed mixture, fixed query mechanism,
independent uniform delays, and simulated contrast distributions used here.

## Reproduction and artifacts

From the repository root:

```powershell
uv run shiftlab-dive-late-prior-confirmation --device cuda --streams-per-cell 2000 --null-streams 2000 --alternative-seed-offset 20286000 --null-seed-offset 20288000 --output-dir outputs/late_prior_confirmation
```

The output directory contains the per-stream Parquet/CSV metrics, cell summaries, overall summary,
manifest, and rendered text report. The manifest records configuration, resolved hardware, source
hashes, row counts, and metric checksums. No figure is required for this result; if a figure is added,
use PaperBanana as requested.
