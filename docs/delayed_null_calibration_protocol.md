# Delayed decision-harm null calibration

**Status:** completed null calibration and disjoint primary alternative confirmation; not evidence outside the stated simulator.

## Registered question and procedure

Estimate the probability that the complete event-order monitor ever escalates under two
nondegenerate paired-cost null controls: a stationary symmetric contrast and a benign variance
shift with unchanged zero mean. The three procedures are the fixed-mixture Hoeffding process, the
fixed-mixture bounded-mean betting process, and an equal-weight mixture of eight fixed-start copies
of that betting process. Each tests the eventwise conditional-mean null
`E[C_t | F_(t-1)] <= 0.02` on queried paired contrasts, with outcome-independent Bernoulli label
querying and independent delays. The restart starts are fixed from the expected query horizon before
outcomes; all processes use the same query stream within each seed and cell.

The frozen run uses 3,000 prediction events, alpha 0.05, query probabilities 0.10, 0.25 and 0.50,
uniform integer feedback delay from zero through six, and 2,000 independent seed streams per
scenario and query-rate cell. Seeds are `20264000`–`20265999`, disjoint from the development pilot
and grid. Query-rate cells reuse each seed's underlying generated outcomes and random query scores;
each rate is analyzed separately and the rates are never pooled. Exact two-sided 95%
Clopper–Pearson intervals are reported for every method, scenario and rate.

Run it from the repository root with:

```powershell
uv run shiftlab-dive-delayed-calibration --device cuda --streams-per-cell 2000 --seed-offset 20264000 --output-dir outputs/delayed_null_calibration_2000
```

The runner uses CUDA for reproducible stream generation and vectorized CPU calculations for the
sequential monitor paths. It records the requested and resolved device, seed interval, versions,
code hashes and Parquet checksum. A unit test compares the vectorized path against the online
monitor classes, including the event-order buffer's wall-time convention.

## Results

Each cell contains 2,000 streams. False escalations and exact 95% intervals are:

| Null scenario | Query rate | Hoeffding | Full-stream betting | Eight-start mixture |
| --- | ---: | ---: | ---: | ---: |
| Stationary | 0.10 | 0 (0–0.184%) | 30 (1.50%; 1.014–2.134%) | 21 (1.05%; 0.651–1.601%) |
| Stationary | 0.25 | 0 (0–0.184%) | 27 (1.35%; 0.891–1.958%) | 27 (1.35%; 0.891–1.958%) |
| Stationary | 0.50 | 0 (0–0.184%) | 27 (1.35%; 0.891–1.958%) | 14 (0.70%; 0.383–1.172%) |
| Benign variance shift | 0.10 | 0 (0–0.184%) | 29 (1.45%; 0.973–2.076%) | 13 (0.65%; 0.347–1.109%) |
| Benign variance shift | 0.25 | 0 (0–0.184%) | 27 (1.35%; 0.891–1.958%) | 13 (0.65%; 0.347–1.109%) |
| Benign variance shift | 0.50 | 0 (0–0.184%) | 27 (1.35%; 0.891–1.958%) | 4 (0.20%; 0.055–0.511%) |

The calibration found no cell above a 2.14% upper two-sided interval limit. This is consistent with
the nominal 5% Ville bound and shows that the earlier 2/30 betting false escalations at low query
rate were a noisy small-sample estimate. The lower observed rates are expected to depend on the
registered effect margin, horizon, query mechanism and e-process stake mixtures; they do not support
changing alpha or claiming power from null behavior.

## Disjoint alternative confirmation

The frozen primary alternative was run on seeds `20266000`–`20267999`, with the same late onset
(0.60), weaker expected paired-cost increase (0.12), 25% query rate, 3,000-event horizon and
independent uniform delays 0–6. Query and delay realizations were shared across the three calibrated
paired-cost monitors for each seed. The eight-start mixture detected 933/2,000 streams (46.65%,
exact 95% interval 44.44%–48.86%); full-stream betting detected 100/2,000 (5.00%, 4.09%–6.05%);
the Hoeffding process detected 1/2,000 (0.05%, 0.001%–0.278%).

For the registered primary paired test, the restart mixture detected harm when full-stream betting
did not on 836 streams; full-stream betting alone detected 3. The exact two-sided McNemar p-value is
`5.37e-245` (839 discordant pairs). Conditional on detection, mean event delays were 778.2 events
for the restart mixture and 909.7 for full-stream betting; corresponding wall delays were 781.5 and
913.2. Those delay means condition on detection; nondetections are censored. This is strong evidence
that the fixed-start mixture improves detection in this particular registered design. It does not
establish universal superiority or novelty; the method is a standard convex mixture of e-processes.

Reproduce the confirmation with:

```powershell
uv run shiftlab-dive-delayed-confirmation --device cuda --output-dir outputs/delayed_feedback_confirmation_2000
```

Metrics, paired test and manifest are in
[`outputs/delayed_feedback_confirmation_2000/`](../outputs/delayed_feedback_confirmation_2000/).

## Interpretation limits and next experiment

This checks finite-sample behavior only for these generated independent streams, known bounded
contrasts, outcome-independent query selection, outcome-independent delays, and the implemented
event-order processing. It is not a proof of the e-process assumptions for observed finance data,
adaptive policies, serially dependent outcomes, informative missingness/delays, or selective model
updates. It does not calibrate the source/target risk-CS comparator, whose null is different.

The first confirmation addresses only one registered alternative. Before running the second block,
the replication seeds and unchanged configuration below were frozen. Any expanded grid uses distinct
seeds and Holm-adjusted paired tests. Do not tune start locations or weights on a confirmation block.

### Frozen replication block

Before examining a second alternative block, repeat the exact same 2,000-stream configuration and
primary two-sided McNemar contrast on seeds `20268000`–`20269999`. Keep the three methods, query
rate (0.25), onset (0.60), expected harm increase (0.12), horizon (3,000), delay law (uniform 0–6),
alpha (0.05), start positions, and all analysis code fixed. The replication is assessed as a separate
block; report its marginal exact intervals and paired discordance counts, then show the combined
paired estimate descriptively. Do not alter the primary method or tune based on the replication.

```powershell
uv run shiftlab-dive-delayed-confirmation --device cuda --seeds 2000 --seed-offset 20268000 --output-dir outputs/delayed_feedback_replication_2000
```

The second block reproduced the effect: restart mixture detected 895/2,000 (44.75%, exact 95%
interval 42.55%–46.96%), full-stream betting 100/2,000 (5.00%, 4.09%–6.05%), and Hoeffding 1/2,000
(0.05%, 0.001%–0.278%). There were 801 restart-only and 6 betting-only detections (exact two-sided
McNemar `p=8.89e-229`). Conditional mean event delays were 774.0 for restart and 932.5 for full
stream. Across both independent blocks, the descriptive combined detection rates were 45.70% for
restart (1,828/4,000) and 5.00% for betting (200/4,000), a 40.70 percentage-point difference.

### Frozen factorial extension

The completed analysis is a 12-cell alternative-only factorial on seeds `20270000`–`20271999` reused as
common random numbers in each cell: query rates `{0.10, 0.25, 0.50}` × onset fractions `{0.20, 0.60}`
× expected paired-cost increases `{0.12, 0.24}`. Each cell has 2,000 paired seeds, 3,000 events,
alpha 0.05 and uniform independent label delay 0–6. It compares the same three frozen e-processes.
The primary restart-versus-full-stream paired comparison is reported per cell with exact two-sided
McNemar p-values and Holm adjustment across all 12 cells. Marginal detection rates receive exact
Clopper–Pearson intervals; delay means are conditional on detection and nondetections remain
censored. Null calibration stays separate and unchanged.

```powershell
uv run shiftlab-dive-delayed-grid-confirmation --device cuda --seeds-per-cell 2000 --seed-offset 20270000 --output-dir outputs/delayed_feedback_grid_confirmation_2000
```

The completed factorial found a positive restart-mixture detection difference in all 12 cells.
Detection gains over full-stream betting ranged from 1.2 percentage points in the early, strong-harm
ceiling cell (q=0.25) to 68.4 points for late, weaker harm at q=0.50 (82.8% versus 14.4%). At the
registered late, weak primary condition, gains were 12.5, 40.1 and 68.4 points at query rates 0.10,
0.25 and 0.50. The early strong-harm cells were near ceiling for both methods (restart 99.45%–99.80%,
betting 97.70%–98.60%), so absolute gains were smaller there. All 12 exact paired McNemar contrasts
remained significant after Holm correction; the largest adjusted p-value was 3.03e-6. Extremely
small p-values are computed and retained on the log scale; displays below 1e-300 include their
log10(p) values to avoid reporting floating-point zero as an exact zero.

This broadens the power evidence for the fixed-start mixture across the registered synthetic grid.
It does not establish that every start mixture will help, that the effect transfers to dependent or
real streams, or that the procedure is novel. The 2,000-seed null calibration remains the separate
false-escalation evidence. Alternative-stream pre-onset escalations were 0/24,000 for Hoeffding,
80/24,000 (0.33%) for the restart mixture, and 344/24,000 (1.43%) for full-stream betting; these
alternative-prefix counts are descriptive and do not replace null calibration.

Metrics, cell summaries, paired tests, report and manifest are in
[`outputs/delayed_feedback_grid_confirmation_2000/`](../outputs/delayed_feedback_grid_confirmation_2000/).
The calibration metrics remain in
[`outputs/delayed_null_calibration_2000/`](../outputs/delayed_null_calibration_2000/). No figure is
included because project guidance requests PaperBanana for visuals and that tool is unavailable in
this session.
