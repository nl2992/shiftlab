# Paper 1 — 60-module EQSDp+cutoff combinatorial methods search

## Authorized objective

Develop extensions of the frozen policy `s2armr_H1100` on `nl2992/shiftlab`, branch `research/paper1-eqsdp-foundation-2026-11-08`, starting from commit `8ac1ce4c90a18b0a4010c0fc9b3a48b5cefaef0f`. Do **not** stop because a particular candidate fails the previous all-or-nothing Stage 5 publication advancement rule. Run a broad but computationally prioritized exploration of **60 distinct proposed add-ons in combinations of 1–5**. Optimize total deployment cost with prediction-error parity as a closely tracked objective; retain profitable scoped or component-wise discoveries.

**These are untested design hypotheses. Do not claim results or originality before implementation, tests, ablations, and prior-art audit.**

## Inputs to place in the repository

- `paper1_60_contraptions.json`: machine-readable 60-module catalogue, parameters, prior overlap, exact datasets and comparator names.
- `paper1_combo_sampler.py`: reproducible initial candidate manifest and a guided proposal phase.
- `paper1_initial_candidates.jsonl`: 620 combinations already generated (60 singles, 200 pairs, 160 triples, 120 fours, 80 fives); all marked `NOT_RUN`.
- `paper1_60_contraptions_and_protocol.md`: human-readable module catalogue.

The generator itself does not implement modules or run the simulator. Implement the modules and a deterministic compositor against the existing simulator; log every proposed query, policy action, active module and cause. Do not write success labels until experiments complete.

## Unchanged parent and data

- Parent: `s2armr_H1100` = EQSDp Arm R (lambda 0.98, gamma 0.3, stake off) plus `Stage1C1Stop(stop_h=1100)`; initial deployment model 0.
- Parent discounted disagreement counts, Beta posterior, pessimistic quantile economic-switching rule and the original cutoff remain the core. Add-ons may cause **explicitly logged** cutoff exceptions (reopen/monitor), evidence reweighting, or switching overlays. They must not silently replace the parent.
- Dataset list **exactly**: `sf_311`, `kc_311`, `montgomery_traffic`, `dallas_311`, `dc_311`, `austin_311`, `cincinnati_311`, `oakland_311`, `sandiego_311`. No culling.
- Contract **exactly**: T=2000, B=200, label price=0.05, switch cost=5, same registered per-dataset delays, same event/episode/seed derivation and 10 reference policy seeds on full evaluations.
- Dataset-level mean J is equally weighted across nine. No unauthorized access to hidden label or future event information in candidate policies. Policy can see only `(t, model_predictions, budget, pending requests, released purchased feedback)`. In this simulator, context may be None. Preserve release-before-deploy-before-query order.
- Exact 25 legacy comparator names are in the catalogue JSON and doc 18. Preserve and report their existing, appropriately matched results. Add **matched-cutoff Wald** `s2wald_l0.98_g0.3_H1100`, `s2wald_l0.97_g0.2_H1100`, as well as no-cutoff Wald and EQSDp. If an add-on can be attached fairly to Wald, test **Wald + the same add-on** for a method-transfer ablation; always distinguish this from unmodified Wald comparisons.

## Compositor requirements

Implement independently switchable modules with hooks in order:

1. At event arrival: free predictions-only monitors `A*`, prediction-only parts of `F*`.
2. At label release: update frozen EQSDp evidence and optional `C*` belief overlays; alarms must be based only on released labels.
3. At acquisition time: parent paced disagreement query propensity and cutoff, followed by `B*` gating/reserving; `A*` monitoring overrides and `E*` safeguards may explicitly reopen a query; enforce B=200 at simulator level.
4. On proposed switch: optional `D*` overlays, risk protectors `E*` and meta-arbitration `F*`.
5. Log `module_ids`, `p_parent`, `p_final`, event time, due pending labels, remaining budget, evidence state, switch proposal, final action and reason.

If two modules set incompatible state, either implement a documented deterministic combination (e.g. rule precedence and ablation) or mark `UNSUPPORTED_COMBO` with explanation; do not silently drop a module. Parent with all modules disabled must reproduce `s2armr_H1100` **bitwise** at all 9×episode×seed jobs on an appropriate deterministic sample. Smoke-test the canonical simulator loss and requested-label counts.

## Execution sequence (not a paper-significance gate)

**Phase 0 — safety/functionality tests.** All module constructors import; each operates within budget and causal feedback. Tests for cutoff exception, delayed feedback, no oracle fields, identity if off, randomized repeatability, and matched Wald query machinery. Run debug trace on `kc_311` odd episodes 37 and 39 as diagnostic cases, but do **not** optimize only on those two episodes.

**Phase 1 — one-module screening.** All 60 singletons on exactly the nine datasets, using a deterministic low-cost subset of episodes and 2 policy seeds for the *screen only*, with two parameter settings per module and the unchanged parent on identical keys. Record costs even for losing modules; retain all components in catalogue. Do not require 95% statistical significance to proceed. Rank by mean ΔJ vs parent, change in L/T, worst paired event/episode cost, tail risk, budget consumption and module runtime.

**Phase 2 — 1–5 combinatorial sampling.** Use provided 620-manifest across sizes 1–5. Run cheap matched screens, with candidate module interactions captured. Do not require each ingredient to have been a winning singleton—synergies can be useful. Budget up to the 620 proposed configurations plus one controlled local parameter adjustment each, subject to actual compute constraints. A module is allowed to lose in isolation if it improves a combined method. Optionally use the guided mode after collecting initial labeled candidate results (CSV columns `combo_id`, `delta_j` candidate-minus-parent, `delta_loss_pp`, `se_j`). It uses Bayesian ridge/Thompson-style guided candidate proposals—not a substitute for experiments.

**Phase 3 — full matched development evaluation.** Take the best ≈40 diversified proposals from Phases 1–2; run *all* episodes of *all nine datasets* with the original 10 policy seeds. Use paired equal-dataset J and L/T, labels, switches, late adoption, false promotion, per-dataset effects, p95 and CVaR95 of paired cost. Evaluate strong no-cutoff comparator panel and same-cutoff Wald controls. Keep a Pareto archive of at least: lowest cost, best error parity, strongest downside protection, highest interaction synergy, best late-change subgroup. Every archive entry must carry the full nine-dataset comparison.

**Phase 4 — interaction search.** Fit guided model to observed candidate performances (not oracle losses). Propose new unique 2–5-module combos, enforce supported compositions and explore unexplored cross-family interactions. Compare the full combo to all single-removal ablations and the strongest pair/triple within it. Synergy: `J(A+B) - J(A) - J(B) + J(parent)`, negative means complementary gains. Do not report a combo's entire gain as novel if a trivial calendar/cutoff control reproduces it.

**Phase 5 — decision and reporting.** Present best configurations for each complexity size k=1..5, the full nine-dataset table, J/loss difference vs parent, matched Wald+cutoff, and the original 25 comparator panel. Separate direct Wald superiority, a Wald-transferable add-on, and wins over weak unchanged comparator adapters. Provide uncertainty estimates and ablations for final candidates, but no mandatory single-dataset worst-loss cap or minimum percentage gain during exploration. Report all selection exposure accurately; these nine datasets and their odd/even episode splits are now all development-exposed. If a paper claim needs independent confirmation, that is a separate future step—not a reason to refuse this search.

## Anchor combinations to test deliberately

In addition to the sampled manifest, explicitly include these compatibility-reviewed leads (sizes 2 to 5):

1. `A01+B13`: periodic late sentinel + reserved label budget.
2. `A06+B20`: prediction-pair change sensor + pattern-stratified acquisitions.
3. `A04+B16+F53`: disagreement CUSUM + pending cap + alarm-triggered reserve.
4. `A09+B11+C23`: stale-feedback sentinel + maximum eligible-query gap + posterior soft reset.
5. `B14+D32+D33`: post-promotion label reserve + probation + rapid rollback.
6. `A09+C21+E45`: stale-feedback monitoring + dual-timescale posterior + parent fallback.
7. `A07+B16+F54`: disagreement burst + pending cap + surprise-driven purchases.
8. `A01+D33+E49`: sentinel + fast rollback + posterior lock-in detection.
9. `A04+B13+D37+E45`: CUSUM + late reserve + alert-dependent emergency entry + parent fallback.
10. `A06+B20+C28+E45+F55`: directional prediction sensor + stratified labels + age-aware evidence + parent fallback + sensor fusion.
11. `A09+B14+C26+D32+E42`: feedback-age sentinel + post-switch reserve + persistent-regime belief + probation + tail-risk querying.
12. `B13+C21+D37+E41+F53`: reserved labels + dual-timescale evidence + emergency entry + missed-switch-cost estimate + conditional reserve release.

## Reporting requirements

Write an append-only experiment ledger per candidate with module IDs, parameter values, code SHA, raw episode-seed costs and seeds, benchmark/contract IDs, and failure diagnostics. Keep all attempted combinations (including weak ones) in the experiment registry. Do not change experimental results after viewing them. A mechanism's prior-literature novelty is **unknown** until audited, even if it wins empirically.

Deliver code implementing tested modules, actual candidate-cost results, ablation table, pairwise interaction heatmap, top 1–5-module policies and source paths for all outputs. If compute becomes a constraint, prioritize meaningful tested partial coverage instead of declaring the programme closed due to a statistical gate.
