# Versioned streaming decision contract

**Contract version:** `shiftlab-decision-stream-1.0.0`
**Implementation:** `src/shiftlab/data/streaming.py`

## Message scopes

| Message | Visible to learner/monitor | Required timing and contents | Explicitly absent |
|---|---|---|---|
| `DecisionRequest` | Yes | Sample ID; event, feature-availability and prediction times; feature vector; entity/domain/context; policy, reference-policy and decision-cost versions | Target, true probabilities, change schedule, regime truth, oracle action or oracle risk |
| `PolicyDecision` | Yes / audit log | Action time; deployed and reference action; label-query choice made before outcome; query propensity when queried | Future outcome or evaluator truth |
| `DecisionFeedback` | At `available_time` | Sample ID; label event time; availability time; observed target | Unqueried labels and oracle fields |
| `OracleDecisionRecord` | Evaluator only | True positive probability; oracle action/cost; deployed/reference expected costs; regime and true change time | Never an argument to `replay_decision_stream` |

All times are finite numeric clock values in the in-memory API. Requests require
`event_time <= feature_available_time <= prediction_time`. An action is committed at prediction
time before labels are emitted. Label event time cannot precede the request, and its availability
cannot precede the action. The replay groups all requests/actions at a timestamp before labels
becoming available at that same timestamp. Missing feedback is allowed only when the label was
queried; a supplied propensity must be in `[0,1]`, and queried labels require a positive propensity.

The API is a capability boundary for accidental leakage, not a security sandbox: do not pass the
evaluator table to monitor/model code. Real data should preserve source clocks and unknown times;
never substitute download time, event date, or an inferred timestamp for a missing feature release
clock without an explicit retrospective protocol. Existing table schema `1.1.0` remains the dataset
contract; this message API is separately versioned because adding actions and cost versions changes
stream semantics.

## Decision estimands

For policy action `a` and binary outcome `Y`, costs are explicitly versioned and supplied to both
policies. The benchmark reports the expected deployed/reference contrast
`E[c(pi(X),Y)-c(pi_ref(X),Y)]`, predictive squared-error change, and feature RBF-MMD² separately.
It also reports synthetic oracle expected regret, which is available only on the evaluator side.
The benchmark's paired-cost e-process uses the observed loss difference only under full feedback;
the API's query propensity field does not itself make missing/selective feedback valid.

## Extension points before production use

This contract does not claim that a label queried for one action identifies the counterfactual loss
of another action. If actions affect outcomes, paired comparisons require randomization, logged
action propensities with positivity and a justified estimator, or a narrowed estimand. Delayed
labels can be emitted by the replay API, but this initial sequential test example only handles
complete feedback. Any adaptive policy update must be predictable with respect to the stated
filtration; version IDs alone do not establish predictability.
