# Economic headroom checkpoint — 2026-11-06

**Branch:** `codex/scoped-method-research-results-2026-11-06`  
**Purpose:** Decide whether the rollback/acquisition pilot leaves an identifiable economic gap worth a new method.  
**Status:** `BENCHMARK_ONLY`; one established-component composition screen is evaluated, with no new method claim.
**No confirmation claim:** Evidence is synthetic and previously exposed. No independent real-data confirmation has been performed.

## Evidence reconciled

The latest rollback/acquisition pilot is `research/scoped_method/pilots/rollback_acquisition_30seed_20261106/`, with 30 matched seeds in each of three regimes (90 episodes per policy), horizon 2,000, hard label budget 200, label price 0.05, and switch cost 5. Its registered net cost is predictive loss + label expenditure + switching expenditure. `summary.json` verifies that E_rb and B2 are exactly equal on their common seed/regime records.

Never-switch has lower mean net cost than E_rb in all three tested reversal/recurrent regimes. The paired E_rb-minus-never contrasts are:

| Regime | Mean net-cost difference | Paired 95% interval | Interpretation |
|---|---:|---:|---|
| F3_reversal_800 | +46.20 | [+38.46, +53.94] | E_rb costs more |
| F4_recurrent | +34.53 | [+26.04, +43.03] | E_rb costs more |
| S_reversal_400 | +26.93 | [+17.48, +36.38] | E_rb costs more |

E_rb does improve its gated-deployment host on F3 (difference -9.37, 95% interval [-14.20, -4.54]); its differences versus the host are not resolved from zero on F4 (+2.77 [-0.21, +5.75]) or S (-1.90 [-4.22, +0.42]). Thus the pilot identifies a host-specific reversal benefit, but not an economic advantage over the feasible never-switch control. The tested sample does not establish that rollback is generally harmful.

The pilot did **not** evaluate a direct front-loaded-acquisition-plus-E_rb arm. The SR/CUSUM variants are useful restart references, but their false-alarm control is not matched to an anytime probability-of-any-false-alarm certificate: E_srr has an ARL statement, not the RMM/E_rb Ville guarantee. Their cost comparisons cannot be presented as equal-safety comparisons.

## Existing synthetic headroom evidence

The corrected Failure Atlas v2 synthetic validation (`docs/failure_atlas_v2_flq/results/validation_synthetic.md`) covers 13 registered regimes with 100 paired streams each. It contains persistent alternatives (`V_better_*`), a delayed alternative (`V_late_600`), reversal/recurrent alternatives, and null/worse regimes, and reports the common net-cost contract and null behavior. It supplies useful existing discovery/validation evidence, not an independent confirmation set for this checkpoint.

On persistent alternatives, the valid-control `xu_acquisition_only` adapter has mean net costs 433.9, 312.2 and 473.0 versus never-switch at 458.7, 378.3 and 536.1. On `V_late_600`, it is 390.8 versus 403.3. This is an existing-policy advantage in the relevant setting, not evidence for a new repair. The name is literal: this adapter combines Xu-style acquisition with ShiftLab's certificate and is **not Xu et al.'s published certificate**. Its observed promotion rates were 0 on the two independent nulls and 0.03/0.06 on the dependent nulls at rho 0.5/0.8, below that report's 0.0936 screening bound; this does not establish validity outside those registered regimes.

On `V_reversal_1000`, never-switch costs 360.2 and the strongest listed certified policy (`discern_style`) costs 370.2. On `V_recurrent`, never-switch costs 388.5 and the strongest listed certified policy (`gated_adaptive_range`) costs 395.2. These are descriptive means; no newly computed uncertainty interval is claimed here. The adverse reversal results agree in direction with the 90-episode E_rb pilot.

The repaired adaptive-range code changed comparator validity. `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md` explicitly supersedes pre-fix numerical tables. The corrected 13-regime report is the source used above. Earlier reports that cite the old adaptive-range values or DISCERN port bug are not pooled into these contrasts.

## Mechanism and prior-art interpretation

The current evidence supports a trade-off, not a single rollback-speed failure. A rollback trigger can reduce host cost in one reversal regime and still lose economically to never-switch because promotion, label spending, delayed evidence and switch expenditure consume more than the saved predictive loss. For genuinely persistent or late improvement, existing certificate/acquisition adapters already beat never-switch in the registered synthetic regimes. The data do not isolate a novel joint acquisition/rollback mechanism, and the missing E_rb-plus-front-loaded arm prevents attributing any extra benefit to that combination.

The exact stationary economic-acquisition screen (`docs/switching_economic_acquisition_screen_v1.md`) rejects one-step VOI: it buys zero labels and costs 10, while a feasible adaptive multi-query policy has exact Bayes cost 539/64 (8.421875) and null-promotion probability 1/64. This is a counterexample to that one-step acquisition rule, not novelty: the finite-horizon Bellman comparator already closes the gap. Existing novelty audits (`references/novelty_audit.md` and `papers/shiftguard_unified/novelty_audit.md`) likewise do not support a generic cost-aware adaptation or restart-detector novelty claim.

## Direct front-loading-plus-E_rb falsification screen

The previously omitted combination was added as a development arm using the existing `RecoveryMonitor` rollback code and the corrected `GatedAdaptiveRange(front=True)` host. No rollback rule or acquisition rule was changed. Before opening outcomes, `research/scoped_method/pilots/direct_frontload_erb_20261106/protocol.md` froze the 4-cell matrix, 20 paired seeds/cell, seed base `2026110618`, contract, comparator set, and a 5-unit practical threshold. The run completed 80 jobs in 108.6 seconds.

Primary paired differences (candidate minus comparator; negative is cheaper):

| Regime | Versus paced E_rb | Versus front-loaded host | Versus never-switch |
|---|---:|---:|---:|
| F0_better | -21.45 [-31.70, -11.20] | -3.86 [-12.35, +4.64] | -61.35 [-75.67, -47.03] |
| V_late_600 | -9.65 [-19.89, +0.59] | -61.20 [-77.30, -45.10] | -51.20 [-67.30, -35.10] |
| F3_reversal_800 | +18.20 [-3.88, +40.28] | -22.85 [-40.73, -4.97] | +60.65 [+42.52, +78.78] |
| F0_null | +1.20 [-1.31, +3.71] | +0.33 [-0.36, +1.01] | +11.20 [+8.69, +13.71] |

All intervals are two-sided paired t intervals over the 20 common seeds. The candidate missed the frozen development bar: in F0_better its incremental saving over the front-loaded host was under 5 units and unresolved; in V_late_600 its difference from paced E_rb was unresolved. It also incurred 60.65 more mean cost than never-switch on F3_reversal_800, exceeding the permitted 5-unit adverse-regime tolerance. It did reduce mean V_late_600 promotion time from 1,095.85 events for paced E_rb to 783.25, but that timing improvement did not beat the frozen economic criteria against all comparators.

Cost decomposition confirms that labels were not the source of the large null/reversal effects: the candidate requested all 200 labels (cost 10) in every cell. Mean candidate costs were F0_better: loss 344.55 + labels 10 + switches 4.75 = 359.30; V_late_600: 341.40 + 10 + 4 = 355.40; F3_reversal_800: 383.50 + 10 + 7 = 400.50; F0_null: 358 + 10 + 0.25 = 368.25. Never-switch costs were respectively 420.65, 406.60, 339.85 and 357.05. On F0_null, 1/20 episodes promoted (Wilson 95% interval [0.009, 0.236]); this pilot is far too small to validate a nominal 0.05 error rate.

This is a useful negative composition result: front-loading helps versus never-switch when a real improvement is late, but the direct combination does not show a stable increment over paced E_rb and has an adverse reversal trade-off. The benefit is explained by existing acquisition and rollback components; the run provides no novelty basis.

## Decision

**`BENCHMARK_ONLY`.** The rollback pilot loses to never-switch on all three tested reversal/recurrent regimes. The direct E_rb-plus-front-loading arm fails the preregistered development threshold and is worse than never-switch under reversal. Existing policies can earn gains on persistent and delayed-persistent alternatives, so the evidence does not justify `NO_ECONOMIC_HEADROOM` for the whole research question. It does reject this candidate composition and does not support `DISTINCT_REPAIR_WORTH_CONFIRMING`. Do not launch real-data confirmation or another rollback search for this mechanism.

**Smallest next action:** incorporate this negative result and the corrected comparator provenance into the claim-bounded benchmark manuscript; do not implement another candidate or open real-data confirmation for this mechanism.

## Reproduction pointers

- Pilot manifest and raw paired records: `research/scoped_method/pilots/rollback_acquisition_30seed_20261106/manifest.json`, `records.jsonl`.
- Pilot summary and contrasts: `research/scoped_method/pilots/rollback_acquisition_30seed_20261106/summary.json`.
- Corrected matrix results: `docs/failure_atlas_v2_flq/results/validation_synthetic.md` and `validation_summary.json`.
- Comparator correction: `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md`.
- Economic acquisition counterexample: `docs/switching_economic_acquisition_screen_v1.md` and `outputs/switching_economic_acquisition_screen_v1/results.json`.
- Direct composition screen protocol, raw records, manifest, summary, and analyzer: `research/scoped_method/pilots/direct_frontload_erb_20261106/` and `research/scoped_method/analyze_direct_frontload_erb.py`.
- Direct-screen SHA-256: `records.jsonl` `a1a83a1de7d101ce6e89d58461715529cb243aea0474618a31dc36a7225a09f1`; `summary.json` `08ffb4ec158640df1a7fb8d3c8a640fff3fa852d0233a204bec4e8b12a50d56d`; `manifest.json` `dc70ee343843432f7130c5019df065b04cbd7d093fee14cbcc15101251dea74b`.
