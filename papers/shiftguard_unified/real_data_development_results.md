# Real-data development results

**Status:** exploratory development summary, 2026-10-26. Existing inspected
test partitions are not treated as fresh confirmation. The sources below
answer different questions and their metrics must not be pooled.

## UCI Gas Sensor Drift: batch-held-out candidate selection

The frozen v4 CUDA protocol trains an incumbent on batches 1–3, trains three
retraining candidates on batches 1–5, chooses between the incumbent and
candidates using batch 6, and evaluates the locked choice on batches 7–10.
The row-random split field is ignored because it mixes batches. All choices
are made before the runner computes test metrics. Selection uses three
imposed loss matrices: symmetric, class-6 error cost 2, and class-6 error
cost 5.

Validation chose the no-adaptation incumbent under symmetric and 2× class-6
costs. Under 5× class-6 cost it chose the batch-1–5 retrained model with
weight decay 0.0001. That choice reduced validation cost from 0.93522 to
0.92565, but on batches 7–10 the incumbent's row-weighted cost was 0.79729
versus 0.82149 for the selected retrained model (incumbent-minus-candidate
gain **−0.02419**). The equal-batch-average costs were 0.87017 and 0.89434
(gain **−0.02417**). Batch-specific gains were +0.20482, −0.03401, −0.01277
and −0.25472 for batches 7, 8, 9 and 10. Batches 10 and 7 dominate the row
count, so the equal-batch summary is also reported. Feature-centroid
distances are provided as a separate distribution diagnostic; they do not
imply decision harm.

This is evidence that validation-selected adaptation can transfer poorly
across later domains under an imposed cost, and that the decision changes
with the cost matrix. It is descriptive: only four evaluation batches are
available, within-batch dependence is unknown, and later batches were already
examined by previous repository diagnostics. There is no within-batch event
order, sequential guarantee, or source-grounded application utility. The
complete protocol, runner, five targeted tests, checksummed output manifest,
and aggregate metrics are in [`gas_sensor_candidate_protocol.md`](gas_sensor_candidate_protocol.md),
[`evaluate_gas_sensor_candidates.py`](../../scripts/evaluate_gas_sensor_candidates.py),
[`tests/test_gas_sensor_candidates.py`](../../tests/test_gas_sensor_candidates.py),
and [`outputs/shiftguard_unified/real_data_development/gas_sensor_candidates_v4/`](../../outputs/shiftguard_unified/real_data_development/gas_sensor_candidates_v4/).

## WILDS CivilComments: sample-split candidate-policy selection

The protocol-compliant CUDA run fits three hashed-text logistic models on the
official 269,038-row training split, selects model/threshold pairs on the
45,180-row validation split, and evaluates the frozen choices on the
133,782-row official test split. The train, validation, and test splits have
zero overlapping `article_id` clusters. Text is the only learner input;
identity annotations are evaluator-only. No timestamp is used, so this is an
offline candidate-selection evaluation, not live monitoring.

The fixed incumbent is the `1e-4` penalty model at threshold 0.5. Validation
selected the `1e-5` model under all three imposed cost settings, with
thresholds 0.35 (symmetric costs), 0.25 (false-negative cost 2), and 0.50
(false-positive cost 2). On the test partition, the incumbent-minus-candidate
cost gains were respectively **+0.01250** (article-cluster 95% interval
[+0.01146, +0.01366]), **+0.05038** ([+0.04732, +0.05342]), and **+0.00467**
([+0.00402, +0.00536]); the three one-sided cluster-bootstrap p-values were
Holm-adjusted. These are imposed classification-cost units, not application
utility, and the bootstrap is not an anytime-valid certificate.

The incumbent test accuracy/Brier/log-loss were 0.88661/0.09044/0.31086.
The validation-selected candidates achieved accuracies 0.89910, 0.89496, and
0.89296 respectively; all three used the same fitted model, so Brier and log
loss were 0.07983 and 0.27159. The incumbent's worst identity-by-label-group
accuracy among groups with at least 20 examples was 0.00000 (30 positive
`other_race_or_ethnicity` examples); candidate worst-group accuracy was
0.15476 under symmetric cost, 0.29683 under the false-negative-sensitive
setting, and 0.04524 under the false-positive-sensitive setting. These group
figures are descriptive and come from one dataset.

The official test set has appeared in earlier repository diagnostics, and
its prior-use audit is incomplete. Accordingly, this is useful real-data
development evidence for the simple sample-split Q2 baseline, not independent
confirmation. It does not exercise DIVE, Target-Scout, delayed feedback,
resource allocation, or causal policy value. Costs are research-imposed.

The first implementation output is preserved but marked superseded because
it interleaved test scoring with later validation-only cost-setting selection.
No test metric fed a later choice, but that execution order violated the
frozen protocol. The corrected run freezes all three policies before opening
test outcomes. Its metrics, group aggregates, hashes, and environment are in
[`outputs/shiftguard_unified/real_data_development/wilds_civilcomments_candidate_selection_v2/`](../../outputs/shiftguard_unified/real_data_development/wilds_civilcomments_candidate_selection_v2/);
the pinned source data and zero-overlap audit are recorded in its manifest.
The [protocol](wilds_candidate_selection_protocol.md),
[runner](../../scripts/evaluate_wilds_candidate_selection.py), and
[targeted tests](../../tests/test_wilds_candidate_selection.py) make the
selection and scoring contract explicit.

## CRSP CIZ: retrospective decision-harm monitor comparison

The existing CRSP run evaluated a frozen train-only Ridge long/flat policy on
7,621,543 test events from 7,350 PERMNOs over 1,507 dates (2020–2025), against
a same-date market-direction reference under an imposed 5-basis-point capped
paired cost. Candidate cost was lower by 0.0003357 per event; a two-way
PERMNO × circular 20-date-block bootstrap gave a descriptive 95% interval
[-0.0006550, -0.0000415].

On the one historical path, paired-cost CUSUM and the bounded excess-cost
e-process did not cross their thresholds. Predictive-loss CUSUM crossed on
2020-03-20 and was above its empirical threshold on 96.4% of test dates;
sampled feature MMD crossed on 2020-03-27, with AUROC 0.551 for hindsight
labels of a positive mean cost over the next 20 dates. Four synthetic-screened
e-process variants replayed on the same aggregate path also had no crossings.
Their AUROC/average-precision values did not rise meaningfully above the
42.2% positive-window prevalence.

This is genuine panel data and executes actual monitor logic, but it is one
dependent retrospective path with an already examined 2020–2025 test period,
unknown historical feature-release times, and imposed returns/costs. It does
not establish sequential type-I control, causal harm, deployment utility, or
trading profitability. Details and checksummed outputs are in
[`docs/crsp_monitor_comparison_results.md`](../../docs/crsp_monitor_comparison_results.md),
[`docs/crsp_eprocess_candidate_replay_results.md`](../../docs/crsp_eprocess_candidate_replay_results.md),
and their linked protocols/manifests.

### CRSP CIZ: frozen train-selected decision-policy pilot

A separate CUDA pilot sampled 100 PERMNOs from the 11,472-identifier training
universe without conditioning on test presence; 30 sampled securities appeared
in the test period and contributed 40,557 next-observed returns. A train-only
Ridge long/flat candidate had worse RMSE (0.039943) than the training-mean
forecast (0.039786), but its imposed ±10%-capped long-only cost was lower than
the same-date market-direction rule by 0.0005581 per event at the 5-bps
turnover setting (20-date block 95% descriptive interval
[−0.0009119, −0.0002021]). This difference remained negative for 0, 10 and
25 bps. The example separates predictive RMSE from a particular downstream
decision cost; it is not a general model advantage.

An artifact verifier matched the dataset manifest, observation, protocol,
runner and output hashes, and confirmed that the year-level cost means
recombine to the reported totals. This is a sampled retrospective diagnostic,
not independent confirmation or a test of sequential monitoring assumptions.
Only 30 PERMNOs contributed test outcomes; date-block uncertainty omits
security-sampling and model-selection uncertainty. The imposed utility and
transaction costs are not trading economics. Full limitations and checksummed
outputs are in [`the pilot result report`](crsp_decision_policy_pilot_results.md)
and [`the run artifacts`](../../outputs/shiftguard_unified/real_data_development/crsp_decision_policy_pilot_100_v1/).

## EIA EBA electricity: event-time retraining resource frontier

The frozen CUDA replay uses the 2023–2025 hourly CISO and ERCO one-step-ahead
demand panels. It fits an initial Ridge model on the training split, reserves
calibration rows for a 95th-percentile 24-hour squared-error trigger, and
compares frozen, weekly, monthly, and error-triggered retraining at imposed
label delays of 0, 24 and 168 hours. The two balancing authorities share a
calendar period and are reported separately. Publisher feature/label release
times remain unknown; event-time feature availability is assumed.

At zero assumed delay, weekly retraining reduced CISO RMSE from 1,404.4 to
1,274.4, with 31 updates; the error trigger reached 1,274.5 with 29 updates
and 466,078 cumulative fit rows versus 504,064 for weekly retraining. For
ERCO, weekly retraining reduced RMSE from 2,109.4 to 2,079.6 with 31 updates;
the error trigger reached 2,077.7 with 20 updates and 312,787 fit rows versus
504,128 for weekly retraining. At 168-hour imposed delay, the trigger RMSEs
were 1,284.3 (CISO) and 2,081.8 (ERCO); weekly retraining gave 1,283.9 and
2,081.9. Monthly retraining had fewer updates (7) but higher RMSE than weekly
in both authorities. Every update policy improved over the frozen predictor
on this one historical period, but the trigger gave only a small error gain
over weekly retraining and still triggered 20–29 times.

These comparisons describe predictive error versus retraining work; the
study has no downstream action or grounded utility, and it does not implement
the published *When to Retrain* or RCCDA algorithms. Trigger thresholds are
heuristics with repeated looks and provide no false-alarm guarantee. Delay
values are sensitivity assumptions; the source test period was already used
in earlier repository diagnostics. No confidence interval is treated as an
independent deployment replication. Protocol, runner, tests, monthly
aggregates and output hashes are in
[`eia_retraining_protocol.md`](eia_retraining_protocol.md),
[`evaluate_eia_retraining_frontier.py`](../../scripts/evaluate_eia_retraining_frontier.py),
[`test_eia_retraining_frontier.py`](../../tests/test_eia_retraining_frontier.py),
and [`outputs/shiftguard_unified/real_data_development/eia_retraining_v1/`](../../outputs/shiftguard_unified/real_data_development/eia_retraining_v1/).

### Independent UPF adaptation on the same EIA source

An additional frozen exploratory protocol implements the finite-horizon UPF
decision rule on the same series using bounded clipped normalized absolute
error, with a fixed per-retrain relative cost. For each of CISO and ERCO it
uses 15 contiguous periods (seven offline and eight online), two assumed
extra label delays (0 and 168 hours), and ten cost values from zero through
the evaluator's break-even frontier. It compares UPF with never, always,
periodic-2, periodic-4, a fixed error-threshold rule, and an oracle schedule.
All methods use the same held-out period tails. The learner's UPF forecaster
receives only performance observations from mature prior periods and the
current prefix's feature shift; the oracle alone sees the full evaluation
matrix.

The v2 run completed with 2,240 period-level rows and 280 method/domain/delay/
cost summaries on the NVIDIA RTX 4060. The outcome is mixed: the corrected
oracle is a lower bound by construction; simple fixed policies and UPF trade
loss against retraining cost differently across the two balancing authorities,
and UPF does not consistently beat never or the heuristic trigger. At the
midpoint of each cost range, UPF made no retrains in all four domain-delay
settings and matched the never-retrain cost; at zero cost its choices varied
with domain and delay. These are descriptive frontier observations, not independent
replications. The normalized loss and alpha are imposed research units, not
electricity operating utility. Historical feature publication and label
release times remain unknown, and this retrospective data was previously
exposed. The experiment is an EIA regression adaptation of the published
classification setting, not author-code reproduction or confirmation.

The v1 run remains preserved but is superseded for oracle comparisons: its
exact schedule included offline period 6 and shifted one decision when applied
to online periods 7–14. The v2 protocol, runner, metrics, and manifest record
the corrected eight-period oracle alignment.

The protocol, execution-time snapshot, manifest with matching protocol
hashes, source/data/output hashes, Parquet metrics, and report are in
[`upf_eia_development_protocol_v2.md`](upf_eia_development_protocol_v2.md) and
[`outputs/shiftguard_unified/real_data_development/upf_eia_frontier_v2/`](../../outputs/shiftguard_unified/real_data_development/upf_eia_frontier_v2/).
The later CARA and ADWIN/DDM adaptations below complete those specific EIA
baseline gaps, but do not close the wider Q3 fidelity requirement.

### RCCDA paper-rule adaptation on the matched EIA frontier

A separate frozen runner implements RCCDA's published virtual-queue action
threshold and proportional/derivative history estimator with `Kp=1`,
`Kd=0.3`, `V=10`, target update rate 0.1, and unit update cost. Feedback is
restricted to held-out losses whose assumed label-maturity times precede each
decision. The adaptation uses the prior available loss for the derivative
term; the inspected official PACS evaluator instead reads the just-appended
current loss as `loss_prev`, which nulls that term. This is a paper-rule
adaptation on EIA, not an author-code reproduction, and its estimated-gain
error does not inherit RCCDA's ideal-estimator resource theorem.

The corrected CUDA run produced 320 RCCDA period rows and a 2,560-row matched
table across CISO/ERCO, 0/168-hour assumed delays, ten cost points, eight
online periods, and eight methods including an evaluator-only exact oracle.
RCCDA made three updates in CISO and four in ERCO under both delays. It attained
the lowest non-oracle objective at 6 of the 40 authority-delay-cost points;
no-update or error-threshold policies were better over much of the higher-cost
frontier. At zero update cost, cumulative bounded losses were 2.3322 (CISO,
0h), 2.3694 (CISO, 168h), 2.7535 (ERCO, 0h), and 2.7417 (ERCO, 168h). The exact
oracle was no worse than any feasible policy at all 40 points after correcting
the schedule alignment. These are descriptive outcomes from two dependent
historical series, not statistical replications or real-time utility.

An independent integrity pass recomputed all 32 feedback-row maturity counts,
checked duplicate-free method-period keys and all five artifact hashes, and
verified the oracle's lower-bound property at every cost point. The frozen
protocol, runner, tests, metrics, and report are in
[`rccda_eia_development_protocol_v2.md`](rccda_eia_development_protocol_v2.md),
[`evaluate_rccda_eia_frontier.py`](../../scripts/evaluate_rccda_eia_frontier.py),
and
[`outputs/shiftguard_unified/real_data_development/rccda_eia_frontier_v2/`](../../outputs/shiftguard_unified/real_data_development/rccda_eia_frontier_v2/).

### CARA on the matched EIA frontier

The official CARA threshold, cumulative-threshold, and periodic decision rules
were adapted to EIA using bounded normalized absolute regression loss and an
observed current-period prefix as the query-distribution proxy. Parameters
were tuned only on offline periods 1–5; period 6 was excluded so its evaluation
labels did not need to be assumed mature at the online boundary. QDM scores
used mature current-prefix labels, period-0 feature scaling, and at most 256
deterministically selected rows per loss/query set. Evaluation-tail covariates
and outcomes were excluded from policy decisions.

The CUDA run added 960 CARA rows to an 11-method, 3,520-row matched frontier
on the NVIDIA RTX 4060. Across the 40 domain-delay-cost cells, the best of the
three CARA policies improved on the best existing non-oracle method in 16,
tied in 5, and was worse in 19; its average objective gap was +0.010 normalized
units. Mean updates were 3.30 for cumulative threshold, 2.05 for periodic, and
2.30 for threshold. CARA is a useful Q3 comparator, but this mixed result does
not support a CARA superiority claim. This is a task-specific regression
adaptation, not a reproduction of the paper's classification experiments.

### ADWIN and DDM on the matched EIA frontier

The official CARA repository also includes ADWIN and DDM error-stream
retraining baselines. A separate CUDA replay used River 0.26.1: ADWIN monitored
bounded normalized absolute loss (`delta=0.002`); DDM monitored whether that
loss exceeded the 95th percentile of period-0 training residuals. DDM's
continuous-regression-to-binary mapping and River implementation are explicit
adaptations of the official scikit-multiflow baselines, not author-code
reproductions. Both consumed only mature current-prefix feedback and chose
period-specific models before the held-out tail.

The detector run added 640 policy-period rows over the unchanged 40-point
frontier. Across 32 online domain-delay-period decisions, ADWIN alarmed and
updated 22 times; DDM alarmed and updated 8 times. Average objectives were
2.7502 for ADWIN and 2.6367 for DDM. The best detector arm improved on the best
other non-oracle policy in only 3/40 cost cells, tied in 6, and lost in 31; its
mean gap was +0.0185 normalized units. These detectors add reference points
but do not improve the current frontier consistently. This is descriptive
evidence from two previously inspected historical series, not sequential
false-alarm calibration or independent real-data confirmation.

An independent verifier checked 4,160 matched rows, maturity counts, candidate
chronology, row alignment, source/artifact hashes, and the evaluator-oracle
lower bound across all 40 cells. Frozen protocols, runners, tests, manifests,
reports, and Parquet outputs are in
[`cara_eia_development_protocol_v1.md`](cara_eia_development_protocol_v1.md),
[`eia_adwin_ddm_development_protocol_v1.md`](eia_adwin_ddm_development_protocol_v1.md),
[`evaluate_cara_eia_frontier.py`](../../scripts/evaluate_cara_eia_frontier.py),
[`evaluate_eia_drift_detectors.py`](../../scripts/evaluate_eia_drift_detectors.py),
and their versioned output folders under
[`outputs/shiftguard_unified/real_data_development/`](../../outputs/shiftguard_unified/real_data_development/).

## Status against the real-data workstream

### WILDS PACE fixed-candidate gate comparison (exploratory)

The frozen CUDA run compared the paper's paired binary-correctness PACE gate
with a fixed-sample exact McNemar gate on disjoint article-level scout and
certification samples. The scout selected penalty `1e-5`, threshold `0.25`.
On 3,491 certification articles there were 108 candidate-only correct and 79
incumbent-only correct cases. PACE (`lambda=0.5`, `alpha=0.05`) ended at
`log(E)=-10.9684`, well below `log(20)=2.9957`, and retained the incumbent;
the fixed-N gate promoted (`p=0.02016`). Both had the same held-out test
accuracy for their resulting decisions: 0.88661 for PACE and 0.89496 for the
fixed-N gate, a paired gain of 0.00836 (article-cluster bootstrap 95% interval
[0.00671, 0.00996]) for the latter. This test comparison is exploratory
because the official test partition had prior diagnostic exposure. The
article-level exchangeability assumption, randomized rather than historical
certification order, single-candidate scope, common offline labels, and
symmetric correctness target limit interpretation; this is not a real-time
utility, active-label, or run-level familywise guarantee. The source snapshot,
protocol, aggregate outputs, and integrity verifier are under
`outputs/shiftguard_unified/real_data_development/wilds_pace_gate_v1/`.

Multiple acquired data families now have method-level evaluation. In
addition, two distinct task families have protocol-frozen final-period/split
evaluations: the EIA 2026 out-of-time retraining/resource replay and the
Upworthy project-relative randomized package-choice holdout. EIA tests
forecasting risk against refit-resource use under assumed delays; Upworthy
tests actual headline-package choice using observed CTR. Their information
contracts and outcome units differ, and neither tests the full real-data
monitor–certify–intervene pipeline. EIA is a new-to-ShiftLab event-time period,
not verified prospective feedback; Upworthy's public holdout was not globally
secret and supports CTR only. The EIA rerun reproduces all predictive metrics,
monthly aggregates, and block intervals exactly; see the [`real-data
confirmation gate audit`](real_data_confirmation_gate_audit.md) for the
requirement-by-requirement limits. An aggregate-only Criteo audit found that
only 3.31% of labels mature by the last impression under the assumed 30-day
delay, so it is not suitable for an informative within-stream monitor
comparison; it remains available for retrospective prediction or
extended-follow-up stress testing. The full Q1–Q3 published-baseline/integrated
comparison remains open; neither final-period result is prospective or an
independent deployment replication.

## CriteoPrivateAds: cost-sensitive click prediction with assumed feedback delays

A full single-seed CUDA run completed on the 30-day CriteoPrivateAds snapshot.
The frozen hashed-logistic incumbent used days 1–13; incremental candidates
used feedback through days 18, 19, or 20 under assumed two-day, one-day, or
immediate maturity. Days 21–25 formed the internal evaluation, and publisher
validation days 26–30 were excluded. The run used 72,004,608 training labels,
scored 15,917,641 rows per model, and took 403.6 seconds on the final
reproducibility run.

At the imposed 0.5% target CTR, updated candidates reduced weighted log loss
from 0.028087 to 0.027441–0.027467. Under imposed false-negative/false-positive
cost ratios 1, 5, and 20, their weighted costs decreased by 0.000017–0.000018,
0.000282–0.000312, and 0.002227–0.002290 per weighted example. Intercept-only
recalibration changed costs much less; unweighted Brier score worsened slightly.
These are descriptive aggregates over five adjacent days and one model seed,
without reliable cluster uncertainty. The assumed delay, target prevalence,
and costs are not verified operational quantities; the result neither
identifies campaign utility nor tests a sequential monitor. This is the
CriteoPrivateAds click-log task, distinct from Criteo Attribution's delayed
conversion task. The Attribution maturity audit still classifies that source
as uninformative for within-stream monitoring under its 30-day convention.

The aggregate report, protocol and timing limits are in
[`CriteoPrivateAds development report`](criteo_privateads_cost_development_v1.md).
Reproduction output and artifact hashes are in
`outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026/`.

## Hillstrom randomized email allocation

**Status:** single-source exploratory development; not independent confirmation. The official MineThatData challenge CSV contains 64,000 customers randomized to men's email, women's email, or no email, with two-week spend, conversion, and visit outcomes. The task compares a Women's-email-vs-no-email policy at a 10,000/64,000 capacity. Training uses pre-campaign fields only. Compared policies are no email, email all, stochastic random allocation at capacity, historical-spend targeting, neural T-learner, and Ridge T-learner. The latter's regularization is chosen on development data. Policy value uses one-third assignment probabilities; costs of $0–$1 per email are imposed sensitivity scenarios, not observed business costs. The RTX 4060 ran the neural model on CUDA.

At the imposed $0.25/email setting, the current v3 neural T-learner top-capacity minus random-capacity estimate is **−$0.02578/customer**, SE **$0.07122**, 95% row-level Wald interval **[−$0.16538, $0.11381]**. Ridge T-learner minus random capacity is **−$0.02967/customer** (95% interval **[−$0.16907, $0.10972]**). Historical-spend targeting minus random is **+$0.00846/customer** (95% interval **[−$0.14001, $0.15694]**). All intervals include zero; none shows a reliable gain over randomized allocation. Email-all versus never-email has point net value +$0.28845/customer under this imposed cost but a wide interval spanning zero. Do not interpret this as actual profit or campaign profitability.

The initial v1 evaluation was inspected; the same split was reused for Ridge/paired contrasts in v2 and to correct policy-arm-only target scaling in v3. The v1/v2 artifacts are superseded exploratory runs; v3 is the current development reference. The test partition is exposed and all results are development-only. Wald intervals assume one independent randomized customer per row; the challenge source has no event-time outcome release fields. The raw source has no explicit modern license and remains local-only. Source/protocol: `hillstrom_email_policy_development_protocol.md`; current aggregate metrics and checksums: `outputs/shiftguard_unified/real_data_development/hillstrom_email_policy_v3_20261026/`.

## Upworthy headline package selection — frozen fixed-horizon holdout

**Status:** one locked, project-relative holdout evaluation completed and independently reconstructed; not a sequential or economic-utility study. Protocol v1 was SHA-256 pinned before holdout acquisition. The text-only logistic CTR policy used the exploratory partition for grouped cross-validation and fitting, then selected one offered package in each eligible holdout experiment using headline/excerpt text only. The predeclared buffered assignment-risk window excluded 1,063 of 4,871 holdout tests; 3,808 tests and 18,278 arms remained. Selected-package CTR averaged 0.014455 versus 0.013453 for uniform package choice, an equal-test difference of **0.001002 (0.1002 percentage points)**. The 10,000-replicate week-cluster bootstrap 95% interval was **[0.000850, 0.001170]** (0.0850–0.1170 percentage points), with one-sided 95% lower bound 0.000872. The impression-weighted difference was 0.000981. The independently reconstructed point estimate, all per-test metrics, and bootstrap matched exactly. The evaluator-only best-arm average was 0.017467 and is an unattainable descriptive upper bound, not a comparator policy.

The evaluation partition is public and only project-relative; no global novelty or secrecy is implied. The archive has aggregate randomized outcomes, not impression-level feedback. Its outcome supports CTR only, and its old CSV lacks the publisher's later `Problem` flag; the date exclusion is a conservative mitigation, not proof of clean assignment. Do not infer sequential monitoring validity, delayed feedback, future platform performance, revenue, welfare, or net intervention value. Protocol, code and results: `upworthy_policy_selection_protocol_v1.md`, `upworthy_real_data_eligibility_audit.md`, and `outputs/shiftguard_unified/real_data_development/upworthy_policy_v1/`.

## Open Bandit Random/all: fixed-candidate real logged-feedback gate

Following an initial run that was stopped because the author implementation
solved a CVXPY program at every event, an algebraically exact optimizer for the
same two-dimensional concave quadratic was checked against the pinned MOPE
solver and used to finish the frozen v1 replay. The first 1,000 real evaluation
events were also run with the original CVXPY implementation; lower and upper
paths matched exactly, including an empty confidence set at event 866. An
independent full-run verifier reconstructed the training-selected action,
274,737 evaluation scores, all four daily aggregates, the confidence path,
decisions, and saved artifact checksums.

Training on UTC dates 2019-11-24 through 2019-11-26 selected item 41 for
position 1. On the forward dates 2019-11-27 through 2019-11-30, the candidate's
IPW click-value estimate was 0.005241 versus the Random logger's observed
0.003432, a difference of +0.001809. MOPE did not promote: its confidence set
first became empty at event 866, before any lower-bound crossing. The matched
fixed-horizon Hoeffding lower bound was −0.18499 and also did not promote.
Because the set becomes empty, its later numerical bounds are not interpretable
as a confidence interval. This is a negative gate outcome on one exposed
historical sequence, not evidence of false-alarm rate or candidate harm.

The fast optimizer equivalence evidence is in
[`MOPE optimizer validation`](mope_fast_optimizer_validation.md); the frozen
contract and aggregate run are in
[`OBD replay protocol`](open_bandit_mope_development_protocol_v1.md),
[`execution note`](open_bandit_mope_development_execution_note_2026-10-26.md),
[`runner`](../../scripts/reproduce_open_bandit_mope_development.py),
[`independent verifier`](../../scripts/verify_open_bandit_mope_development.py),
and
[`verified output`](../../outputs/shiftguard_unified/real_data_development/open_bandit_mope_v1/).
The evaluation dates had prior ShiftLab OPE exposure. No user/session or
complete-slate identifier, feature-release time, or click-arrival time is
verified; the item-position factorization is an assumption. Therefore this
replay does not validate MOPE's theorem on OBD, establish real-time validity,
or estimate revenue or welfare.
