# Baselines (code: `scripts/multimodel_bcr/policies.py`)

Every Wald-family policy uses the same evidence. For each pair (i, j), it keeps a
label-clock-discounted, self-normalised IPW estimate of the mean of l_i − l_j over the query
region, weighted by w = 1/q with q the frozen issue-time propensity, plus its standard error. The
query region R is the set of events where not all models agree, or all events under uniform
acquisition. Estimates are therefore consistent under any acquisition rule with q > 0 on R.
Deployment rule: switch to argmax_j of (LCB_ij · r_R · (T−t) − c_s) when that value is > 0.

| ID | Policy | Notes |
|---|---|---|
| B0 | never switch | |
| B1 | K-Wald + uniform pacing (`kw_uniform_*`) | tuned over λ{.85,.9,.95} × γ{.05,.1,.15,.25} |
| B2 | K-Wald + disagreement pacing (`kw_anydis_*`) | same grid; budget-paced over R events |
| B3 | Model Picker deployment adapter (`model_picker`) | fidelity-audited port of Karimi et al. 2021 (`competitors/model_picker.py`); deviations marked `# ADAPTER` (delayed IPW labels, hard cap, deploy the argmax-posterior recommendation) |
| B4 | Model Picker acquisition + K-Wald economic deployment (`kw_mp_*`) | MP's published query probability (floor .02) feeding the shared IPW evidence and the Wald payback rule |
| B5 | BCR prototype (`bcr_*`) | 04_METHOD_DESIGN.md |

The Model Selector causal adapter exists in the repo, but its pool-based query rule cannot be
represented in this simulator (see its docstring), so it was not used. Every comparator was
tuned in-sample on the same seeds as BCR.
