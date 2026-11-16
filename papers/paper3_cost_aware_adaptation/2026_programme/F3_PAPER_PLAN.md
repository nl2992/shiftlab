# F3 paper plan (2026-11-16)

Target: ICML main track, 8 pages + appendix, `paper/f3_riskbudget/main.tex` using the official
ICML 2026 style files already in `paper/b3_plus/`. Every number comes from a committed result file
listed below; every citation is verified. Positioning: new problem setting plus a method with a
matching lower bound and a predicted, then confirmed, regime map.

## Working title
A Pathwise Budget on Intervention Harm: Reversible Model Promotion under Delayed, Missing and
Scarce Feedback

## One-paragraph story
Promoting a challenger model is an intervention whose harm is only revealed through delayed,
partial and possibly missing labels. Certifying that a switch will pay for itself is impossible
without a drift assumption (reversal impossibility). We instead bound the harm the intervention
actually causes: with probability 1 - delta, cumulative excess loss plus switching fees never
exceeds a budget R, for every loss sequence, under arbitrary delays and missing labels. A shield
around any promotion rule achieves this with a design-based anytime bound and two reserves (the
rollback fee, and the worst case of feedback still in transit). A matching lower bound shows both
reserves are necessary and that the shield is exactly tight. The same bound predicts the price of
safety: it is governed by x = r d / h, the exposure inside one label delay relative to the budget
headroom. Registered experiments and 14 real streams confirm zero violations where every
comparator (including a naive stop-loss and CUSUM rollback) breaks the budget, and confirm the
regime map: below x = .5 the shield keeps ~90-96% of the unshielded rule's gain; above x = 1 no
valid controller can keep any.

## Contributions (each tied to evidence)
1. Formulation: pathwise high-probability budget on realised intervention harm under a stated
   observation model (O1-O4). Contrast with payback certification (06_THEOREM_LEDGER T0/T1, stated
   as background, not claimed new) and with conservative bandits (immediate feedback, no switching
   fee, no label budget) -- the drafting step must verify and position this prior art fairly.
2. Method: shield + anytime IPW bound (Lemma 1 Bennett; Lemma 1' exact coin mixture with
   settlement accounting) + label pacing. Theorem 2 / 6.1 validity.
3. Theory: Proposition 3 (reserves necessary; shield attains the bound with equality, checked in
   12/12 cells); Proposition 4 (price of safety, first spell; ruin bound tight at d = 1).
4. Regime map: x = r d / h predicts the cost; 6/6 pre-stated tests supported.
5. Evidence: registered confirmation C1-C6 (all supported, 30k runs per arm); real streams
   14 x 3 feedback conditions; ablations.

## Section plan (8 pages)
1. Introduction (1 p): running example (challenger promotion with delayed labels), why payback
   certification fails, what F3 bounds instead, contributions, headline numbers.
2. Setting (1 p): contract (rounds, losses, disagreement flag, query, delay, budget B, fee k),
   harm H_t, target (F3), observation model O1-O4, what is not assumed.
3. Method (1.5 p): anytime bound (Lemma 1/1'), shield rule with W_t, reserves, ride-out, label
   pacing and settlement (v2). Algorithm box.
4. Theory (1.5 p): Theorem 2, Proposition 3, Proposition 4, corollary: regime map in x.
5. Experiments (2.5 p): setup and comparators (fidelity labels), registered confirmation table,
   real-stream table (3 conditions), regime-map table, ablations; label-scarce v3 attempt briefly.
6. Related work (0.5 p).
7. Limitations and conclusion (0.25 p): no mean-cost win; real streams previously exposed; cost
   large when x > 1; simulation has exogenous outcomes; in-house baselines.
Appendix: full proofs, protocols 04F/05F, seed ranges, all tables, v3 selection, numerical checks.

## Source files for numbers
`F_RESULTS.md`; `results/riskbudget/{confirm_summary.json, real_tables.md, real_summary.json,
exposure_ratio_test.json, props_check.json, dev_tables.md, dev_v2_tables.md, v3_*_tables.md,
real_v3_tables.md}`; `03F_RISK_BUDGET_DESIGN.md` (definitions, proofs); `04F_...`, `05F_...`.
