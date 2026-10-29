# Fixed-calendar acquisition with fully adaptive safe switching: registered comparison

**Registered:** 2026-10-28 before execution. **Purpose:** test whether the fixed-cohort gap survives a stronger baseline that optimizes promotion, holding and rollback while using a predetermined query calendar. This is a small structural comparison, not efficacy confirmation.

## Frozen growing family

Use horizon-budget pairs `(T,B) in {(4,2),(5,2),(6,3)}`, fixed delay `d=1`, risk `alpha=1/10`, query fee `c=1/100`, switch fee `k=1/10`, and the same recurrent HMM at every horizon: transition rates `1/4`, emissions `(1/20,19/20)`, prior `1/2`. The HMM determines expected economic cost only. False-promotion risk is the same history-adaptive conditional null, and pending labels consume budget at request time.

For each cell, enumerate every deterministic query calendar of size at most `B` from events `1,...,T-d`, so each scheduled label can arrive by the horizon. For a fixed calendar, optimize the learner's full action policy over the causal sequence-form LP: promotion, continued deployment, rollback, and any later re-promotion remain possible. Nature retains the same full-history information and endpoint response class as the registered causal game. Compare the best fixed-calendar class value with the unrestricted adaptive-query sequence-form policy. Query timing is deterministic in this class; it does not include a lottery over calendars. The separate randomized fixed-cohort comparator does include such a lottery but restricts action to one terminal decision. The unrestricted `T=6,B=3` cell also has the saved exact rational oracle bracket.

## Evaluation and limits

Report every calendar's recovered exact risk and cost, the selected calendar, the unrestricted recovered policy cost, and all LP diagnostics. Query timing is the only restriction within each calendar; the controller receives the same outcome labels, delay, pathwise cap, switching economics and risk constraint. Policies are recovered from numerical LP solutions and rationally checked for cost/risk. Rationalized LP duals must be independently verified without an optimizer for all calendars. This is a comparison to optimized deterministic acquisition, not randomized acquisition or the strongest adaptive sequential-design composition; a gap does not establish novelty.

Run with `$env:PYTHONPATH='src;.'; python scripts/compare_switching_fixed_calendar_action_oracle.py`, then independently verify with `$env:PYTHONPATH='src;.'; python scripts/verify_switching_fixed_calendar_action_oracle.py`. Save all calendars, exact recovered evaluations, rational duals and source hashes under `outputs/switching_fixed_calendar_action_oracle_v1/results.json`.

## Results and interpretation

Across 7, 11 and 26 deterministic calendars, the smallest fixed-calendar optimal costs are respectively `77717/40000`, `194219/80000`, and at least `2.897389374997843...`; the selected calendar in each cell is the earliest admissible schedule. Their unrestricted adaptive feasible-policy costs are `77157/40000`, `193099/80000`, and `461083/160000`. Independently checked dual certificates establish fixed-calendar versus adaptive-feasible gaps of `7/500`, `7/500`, and more than `1562/100000`, respectively. In the first two cells every fixed-calendar dual bracket has zero width; in the six-round cell 15 of 26 have nonzero correction, with maximum bracket width below `8.7e-12`. The verifier checks all 44 saved dual certificates and recovered policies without invoking an optimizer. Full exact rational bounds are in the results JSON.

This is a finite separation from deterministic query calendars even when action control is fully optimized. It is not a growing-family theorem, does not compare with randomized calendar mixtures or adaptive controlled sensing, and does not isolate which adaptive action freedom creates the value. The fixed-cohort lottery remains a relevant stronger acquisition comparator; the `T=6` fixed-cohort gap is smaller but still positive. Treat the result as G1 evidence and a baseline target, not a novel algorithm or efficacy result.
