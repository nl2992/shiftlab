# PPE paired decision-cost confirmation results v1

**Status:** frozen synthetic null calibration and independent alternative
confirmation passed; project-specific endpoint adaptation. Protocol:
[`ppe_paired_cost_confirmation_protocol_v1.md`](ppe_paired_cost_confirmation_protocol_v1.md).
Full run:
[`ppe_paired_cost_confirmation_v1`](../../outputs/shiftguard_unified/sota_reproductions/ppe_paired_cost_confirmation_v1/).
Independent analysis and deterministic PPE replay:
[`ppe_paired_cost_confirmation_analysis_v2`](../../outputs/shiftguard_unified/sota_reproductions/ppe_paired_cost_confirmation_analysis_v2/verification.json).

## Design and verification

The CUDA run produced **25,600 method-stream rows**: 1,000 seeds in each of
two null controls, 300 seeds in each of four alternatives, two query rates
(0.20, 0.40), and four monitors. The alternatives were boundary-local harm,
residual variance, recurring regimes, and harmful adaptation. The runs used
the NVIDIA GeForce RTX 4060 Laptop GPU for synthetic generation with PyTorch
2.9.1+cu130. All methods shared each stream's query path, processed events,
label count, and spend. The largest realized spend was 996.46 against a
maximum registered hard budget of 997.59; there were no budget violations.

The independent null family contains 16 scenario/rate/method cells. It
recorded **0 false alarms in all cells**. The largest one-sided exact
Clopper-Pearson upper bound after the registered Bonferroni adjustment was
**0.5752%**, below the 5% per-cell target. This is Monte Carlo evidence at the
registered operating point, alongside—not a replacement for—the conditional
e-process argument.

The independent verifier re-executed all **6,400 PPE** scenario/seed/query
streams. It found no differences in alarm time, false alarm, detection status,
detection delay, labels, spend, processed event counts, RMSE, expected excess
cost, or budget status. The saved metrics contain all 25,600 rows; stream
paths match across the four methods, all hard caps pass, and the metric hash
matches the run manifest.

## Confirmatory comparison

The primary endpoint averages each stream seed equally across the four
alternative profiles and both query rates, including non-harm outcomes where
the generator did not cross the declared material-harm threshold. PPE's
detection rate was **67.71%**; fixed-mixture's was **55.21%**. The paired gain
was **+12.50 percentage points**
with a 95% seed-cluster bootstrap interval of **[+11.17, +13.83] points**
(300 resampled seeds, 10,000 replicates). PPE also exceeded predictable Kelly
by **+17.63 points** (simultaneous Bonferroni-adjusted interval
[+16.00, +19.38]) and plug-in empirical Bernstein by **+44.46 points**
([+42.92, +46.03]).

The improvement is concentrated at query rate 0.20, where PPE averaged
64.17% detection across alternatives versus 37.25% for fixed mixture. At
query rate 0.40, PPE averaged 71.25% versus 73.17% for fixed mixture. Thus the
result supports a narrower statement: in these registered synthetic streams,
the PPE correction improved detection over the fixed mixture under the
lower-label-rate condition, while matching or slightly trailing it at the
higher rate. Residual-variance-profile alarms were rare for all methods; that
profile is included to expose endpoint behavior rather than to manufacture a
uniform power claim.

## Interpretation and limits

The factor correction follows the published PPE transformation and its
nonnegativity propensity condition. The paired-cost application remains a
ShiftLab adaptation, not a full reproduction of the paper's benchmark suite
or a novelty claim. Its validity requires the eventwise conditional-mean null,
bounded base factors, a predictable outcome-free proxy, predictable known
propensities, query randomization independent of the current outcome, and an
identified paired cost from the observed outcome. The synthetic generator
reveals both policies' potential costs from the same outcome. These findings
do not establish validity under informative queries, arbitrary serial
dependence, delayed feedback, performative actions, misspecified costs, or
real data. No real-data PPE transfer or integrated end-to-end improvement is
established.

The confirmation supports keeping PPE as a Q1 comparator in the finite
baseline set. It does not justify starting a new RIVE/ASC branch. The next
project decision remains the comparative gap/go-no-go gate across Q1–Q3 and
the real-data feasibility audit.
