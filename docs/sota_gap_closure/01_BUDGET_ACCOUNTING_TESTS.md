# 01 Budget accounting
Two contracts are implemented and not interchangeable.
* **Expected budget** (`budget=None`): Bernoulli queries with mean fraction `frac`; realised label counts vary by path (reported as `labels`).
* **Hard budget** (`budget=B`): on every sample path `sum_t Q_t <= B`. A request is charged when issued (`spent += Q`), never when the label arrives; pending labels are tracked (`mean_pending`, `max_pending`). After exhaustion the event is **inactive** (inclusion probability 0, factor 1, no moment update), which preserves the evidence rule: events with `q_t = 0` are excluded rather than treated as unlabelled with a proxy (that would bias the increment). Inclusion probabilities are the nominal `q_t` while `spent_{t-1} < B`, hence unbiased IPW.
Tests: `test_hard_budget_pathwise` (six pacing rules, `labels.max() <= B`, forced exhaustion reaches exactly B), `test_budget_exhaustion_freezes_wealth`.
The earlier phase's experiments used the expected-budget contract only; they are not hard-budget results.
