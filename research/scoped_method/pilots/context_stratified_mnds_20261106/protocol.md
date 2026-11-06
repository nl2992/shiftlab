# Publisher-stratified deployment replay — MN-DS v1

**Status:** frozen pre-test protocol; no October–December 2019 model losses or policy results have
been computed.  
**Question:** can a context-stratified promotion/rollback controller retain a challenger where it
helps and avoid it where it harms, when a global challenger comparison averages those effects
together?  
**Target finding from development only:** on the July–September validation window, the frozen
challenger's overall error advantage is `-0.01578`; publisher-specific advantages are `+0.078` for
Sputnik, `-0.108` for TASS, and `+0.016` for Evening Standard. These are selection/development
statistics, not confirmation results.  
**Confirmation data:** MN-DS v1, 2019-10-01 through 2019-12-31. The one previously previewed test
row (`data_id=1809`) is excluded. No confirmation losses are available in this worktree as of this
freeze.

## Claim boundary and assumptions

This is a chronological real-data replay with a simulated 24-hour label-release contract. It can
support a source-specific predictive deployment-cost comparison; it cannot establish authentic
annotation release timing, causal policy value, performance under live production feedback, or
transfer of an iid conditional-null guarantee to serial news data. The controller is a standard
context-wise composition of bounded e-process gates. It is not claimed as a new statistical test.

The policy sees event timestamp, the frozen model predictions, and the source string before acting.
It sees a queried target only after its simulated release time. Both model losses are then
identifiable from that same target. It never sees unqueried labels, future source events, or
confirmation outcomes before a policy decision. Any statistical guarantee is conditional on the
stated bounded conditional-mean model; this replay alone does not validate those assumptions.

## Frozen stream and contexts

- Source: Zenodo record `7394851`, MN-DS version 1, local raw file
  `data/raw/chronological_news_transfer_20261106/mn_ds_news_classification.csv`; the source receipt,
  byte count, SHA-256, license, and provenance remain in
  `research/scoped_method/pilots/chronological_news_transfer_20261106/PROTOCOL_AMENDMENT_20261106.md`.
- Pair: the existing frozen `HashingVectorizer` + `SGDClassifier` pair trained on 2019 Q1 and Q2,
  as recorded in `run/mn_ds_zenodo_7394851/pretest_manifest.json`. No retraining or model selection
  is allowed after this protocol freeze.
- Development window: 2019 Q3 only. Test window: 2019 Q4 only. Event order is `published_utc`,
  then stable `data_id`; predictions are fixed before test targets are evaluated.
- Contexts: the three source names with at least 100 Q3 records in the frozen eligibility artifact
  (`eveningstandard`, `sputnik`, `tass`) and one `other` bucket containing every remaining source.
  The source labels are observable before prediction. Membership is fixed from Q3 and cannot be
  changed using Q4 values.
- Test rows with missing timestamp, source, title, or registered first-level class are excluded
  under the existing parser rules. `data_id=1809` is excluded regardless. Counts and the ordered
  row-ID hash are recorded before policy outcomes are emitted.

## Candidate: publisher-stratified certified gate

For each of the four fixed contexts, maintain an independent promotion and rollback bounded-mean
e-process on the paired 0/1 error difference

`g_t = 1[p_incumbent != y_t] - 1[p_challenger != y_t]`,

so positive gain favors the challenger. Let `p_s` be context `s`'s frequency in the Q3 validation
window and `T` the registered total Q4 test-event count. Both are frozen before test outcomes are
opened. For promotion at global event `t`, estimate the remaining context exposure as
`h_(s,t) = (T-t) * p_s` and set `kappa_(s,t) = 5/h_(s,t)` when `h_(s,t) > 5`; otherwise promotion
is disabled because the expected remaining context exposure cannot recover the five-unit switch
cost. This uses only a frozen validation frequency and the global event index; it does not use the
future context sequence.
For a released gain `g_t`, update each fixed stake component by
`E_t(lambda) = E_(t-1)(lambda) * (1 + lambda * (g_t-kappa_t)/(1+kappa_t))`.
For rollback use `-g_t`, the same predeclared five-unit recovery-rate rule, and the same formula. The
component mixture is equal-weighted over stakes `{0.05, 0.1, 0.2, 0.4, 0.8}`. The bound and
recovery rate depend only on global event index, Q3 context frequency, and the frozen horizon, so
they are known before the outcome. Each context-stage receives alpha
`0.05 / (4 contexts * 2 stages) = 0.00625`.
Agreement events have known paired gain zero and update the process with zero without requesting a
label. For disagreement events, issue a label and update only when it is released. Buffer updates
until each context's event order is complete; never update on future or unreleased feedback. If a
context quota is exhausted, stop issuing queries and stop starting new updates after all already
requested labels for that context are processed. At most one promotion and one rollback are allowed
in each context; after rollback that context remains on the incumbent. No alpha recycling or
repeated promotion is allowed.

Queries are requested only on model-disagreement events, with predictable propensity 1 until a
context's fixed 50-label quota is exhausted. The total hard budget is 200 labels. Unused quota is
not reallocated. The candidate uses the source string and current model predictions before acting;
the query decision precedes delivery of labels with the same timestamp. A label is delivered at
`published_utc + 24 hours`; the delay is imposed, not observed. The event clock and label-release
queue are timestamp-aware. Each switch costs 5 and each queried label costs 0.05. The policy never
receives future source-specific outcome rates. All methods see the same event and release clock;
each may choose which eligible disagreement labels to request, subject to the shared pathwise cap.

## Frozen comparator set

Every method uses the same frozen predictions, ordered rows, event horizon, delayed release
contract, maximum 200-label pathwise budget, label price, and switch price.

1. `never_switch` (incumbent throughout).
2. `global_PFA-SR:gated_adaptive_range`.
3. `global_RMM:gated_adaptive_range`.
4. `global_E_rb:gated_adaptive_range`.
5. `global_E_swcert`.
6. `global_Xu_acquisition_only` (explicitly an acquisition adapter with ShiftLab's host/certificate,
   not Xu et al.'s full published algorithm).
7. `validation_selected_source_static`: for each of the four contexts, deploy the challenger from
   the start only if its Q3 mean gain is at least 0.03, it has at least 100 Q3 records, and its gain
   is positive in at least two of three chronological Q3 blocks. This is a feasible no-test-label
   baseline. The `other` context uses its pooled Q3 aggregate. Each selected context pays the same
   five-unit boundary switch cost; it has no query cost at test time.
8. Evaluator-only per-context test oracle, reported strictly as an upper bound and never as a
   feasible competitor.

All global monitor baselines use their registered common-contract adapters and alpha `0.05`;
their nulls and assumptions are reported individually. E-SR/SR ARL behavior is not described as
per-horizon familywise control. Empirical costs are not converted into a guarantee.

## Outcomes and decision rules

The primary outcome is net cost per 1,000 eligible Q4 events:

`1000 * (prediction errors + 0.05 * queried labels + 5 * deployment switches) / T`.

Also report raw predictive errors, label count and expenditure, switches and expenditure,
promotion/rollback counts and timestamps by context, and budget compliance. Paired contrasts use
the identical stream. For the four repeatedly compared monitor baselines, report Holm-adjusted
paired moving-block intervals using 7-calendar-day blocks and 2,000 bootstrap replicates with seed
`2026110642`. Report raw intervals as well. The validation-selected static policy is the key
no-monitor comparator and is not dropped if it underperforms.

The replay advances to a scoped real-data case study only if the stratified candidate saves at
least 5 net-cost units per 1,000 events versus both (a) the best registered global monitor and (b)
the validation-selected static policy, with Holm-adjusted 95% paired intervals below zero, and it
does not add more than 5 units per 1,000 in any of the three named publisher contexts. Otherwise
the candidate is falsified for this source/contract. A positive result still supports only this
source and simulated-delay replay; source-level transfer requires an independent dataset and a
separately frozen protocol.

Publisher-specific contrasts are reported separately. There are only three named publishers, so
do not claim reliable population-level source generalization from a publisher bootstrap. Use
calendar-block intervals within each publisher and treat the four contexts as the complete
registered target, not a random sample of all news publishers.

## Opening sequence and integrity

Before computing test predictions, losses, or policy outcomes, the runner must write and fsync an
exclusive opening manifest containing the protocol hash, code and model hashes, source archive
hash, exact event-time window, source-context registry, eligible test-row count and stable row-ID
hash. It then computes policies once and writes raw event records and a manifest with source/code/
model hashes, runtime versions, label-release convention, and run command. It refuses to overwrite
any existing opening or result artifact. Raw/licensed data and model weights stay local and out of
Git; aggregate results and reproducibility metadata may be committed.

## Current development evidence and smallest action

The validation selection rule and publisher-specific statistics are preserved in
`run/mn_ds_zenodo_7394851/source_eligibility.json`. Development suggests opposing publisher-level
effects but does not establish that they persist in Q4. The next action is an independent code and
protocol review, then implement the one-shot runner and open Q4 only if the review finds the
chronology, cost accounting, and no-overwrite gate correct. No thresholds, groups, comparator, or
primary outcome may change after Q4 is opened.
