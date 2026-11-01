# Prospective transfer of the abandonment repair

2026-10-30. Previous goal turn made progress (identified abandonment and repaired the exposed controller class). This continuation freezes that same92-controller class and evaluates5 new overlap cells before changing any class parameters. Goal remains active.

## Design

Horizon6; budget/delay4/1,3/2,2/3 at alternative positive probability4/5; additionally budget4/delay1 at positive probabilities3/5 and9/10. Other costs and risk target unchanged: query1/100, switch1/10, alpha1/20, full-causal null positive probabilities<=1/2. No new start/stride/threshold options added after registration. The32-parent baseline is retained. Each method knows the declared alternative model; this is a known-model planning study, not learning an unknown model from real data.

Same classical sequence-form solver, node cap200000 and60-second native LP limit; no observed wait was treated as permission to restart. All5 cases finish. All selected class components are independently embedded in the full-history game; rational expected cost and causal-null risk match the compact evaluator exactly. The recovered full-history policy risk is independently verified and at most1/20. No reserved real outcomes read.

## Results

| H/B/d / alternative positive probability | Parent-class exact cost | Repaired-class exact cost | Verified reference-policy exact cost |
|---|---:|---:|---:|
|6/4/1 /.8 |69868/15625 |5577/1250 |5577/1250 |
|6/3/2 /.8 |28667/6250 |14331/3125 |14331/3125 |
|6/2/3 /.8 |37/8 |37/8 |37/8 |
|6/4/1 /.6 |709/200 |709/200 |709/200 |
|6/4/1 /.9 |116117/25000 |72503/15625 |72503/15625 |

The enriched class exactly matches the independently verified feasible reference cost in all5 prospective cells. The old class is strictly worse in3. At p=.8/delay1 or2, root evaluation probability2/5 and abandonment threshold3 are selected. At p=.9, evaluation probability4/5 and threshold4. At p=.6 or delay3/budget2, the class prefers a5% immediate-deployment root gamble plus95% never-deploy, buying no labels. These no-information solutions are important: a formal global-null probability allowance can be spent on an immediate random promotion without certifying benefit from observations. The mathematical benchmark permits that behavior; do not present it as empirical safety certification or a recommended deployment policy.

Class enumeration takes.043–.142seconds per case; unrestricted solve+recovery+verification takes.363–1.907seconds. These are single-host toy measurements with different construction shapes. They are not a demonstrated scalable matched-quality5× speedup family. Building the unrestricted game visits7412–41610 nodes. No timeouts/caps are omitted.

The analytical/numerical distinction remains: exact recovered feasible costs equal class costs, and numerical LP objectives match to solver tolerance. This does not give a certified unrestricted lower bound. A formal quality guarantee must separately certify the lower value or prove class sufficiency. Thus no optimality theorem or general approximation ratio follows even from zero observed differences.

## Interpretation

This is useful positive **engineering validation** of a standard early-abandonment baseline. It transfers beyond the exposed examples that motivated the repair. It does not reopen a novel-method claim: root randomization, sequential abandonment and finite-class search are established tools. It also reinforces why a weak streak-only baseline can manufacture an apparent planning advantage.

Remaining substantive questions: can a more compact sufficient controller family be proved for a nontrivial delayed model class, with valid unrestricted value bounds and a source-level difference from robust-FSC/sequential testing? Can a genuine acquisition/action coupling beat equally equipped policies on unknown changing streams? Neither follows from these IID known-model cases. The previous monitor combination screens remain negative globally and are not superseded by this unrelated finite-class match.

Next safe action is lower-certificate/sufficiency analysis before expanding a large synthesis grid; inspect how the exact reference's allowed root gambling relates to the intended operational risk event. Restrict any theorem to its actual comparator class. Full native robust-FSC execution and two-law mapping remain open. No requirement has been redefined around this passing small panel.

## Verification and artifacts

17 controller/sequence-form tests pass. All5 selected-policy embeddings and rational feasibility checks pass during execution. Ruff0.17.1 checks/format pass; frozen source and parent-class registration hashes verified. Runner refuses overwrite.

Registration: controller_transfer_registration.json. Terminal status: controller_transfer_status.json. Results: controller_transfer_results.json. Command: python scripts/exhaustive_evaluation/validate_controller_transfer.py. Source snapshots/hash manifest preserve executed versions. These5 cases are not an additional≥500-combination round. No paid services, external jobs or subagents used; no novelty, real utility or complete SOTA claim.
