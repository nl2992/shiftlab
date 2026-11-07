# F8 fixed-challenger novelty audit (2026-11-07)

## Proposed method under review

Choose a model using pre-deployment validation, deploy the selected fixed challenger once when its
amortized expected gain exceeds switching cost, and optionally monitor for later harm and roll back.
The proposed F8 benefit is avoiding label cost and promotion delay in the rare-disagreement,
high-challenger-accuracy regime.

## Core claims and closest work

1. **Fixed candidate validation supports a predeployment choice.** Dai et al. study production model
   selection by sequential online experiments and a historical-log-trained Bayesian surrogate.
   Their work addresses selection among candidate models under limited online experiments.
   [Primary source](https://papers.neurips.cc/paper_files/paper/2020/hash/0c72cb7ee1512f800abe27823a792d03-Abstract.html).
2. **Fresh evidence can gate safe candidate promotion.** Karampatziakis et al. develop anytime-valid
   off-policy confidence sequences and explicitly apply them to gated production deployment.
   Feng et al. study sequential testing of model modifications with test-data reuse and error control.
   These cover validation and promotion.
   [Karampatziakis et al.](https://proceedings.mlr.press/v139/karampatziakis21a.html),
   [Feng et al.](https://proceedings.mlr.press/v180/feng22a.html).
3. **Cost-aware timing and a remaining horizon change switching decisions.** Regol et al.
   formulate when to retrain with limited observations, unknown shift, and explicit cost ratios;
   Taga et al. cast horizon-aware anytime-valid betting as finite-horizon control; Digalakis et al.
   analyze the economics and timing of incumbent–challenger replacement.
   [Regol et al.](https://proceedings.mlr.press/v267/regol25a.html),
   [Taga et al.](https://proceedings.mlr.press/v306/taga26a.html),
   [Digalakis et al.](https://arxiv.org/abs/2512.18390).
4. **Rollback after promotion is a new safeguard.** ShiftLab already has fixed-candidate
   certification and forward rollback in its ShiftGuard pipeline. Integrated efficacy results
   show that rollback does not recover losses accumulated before reversal
   (`papers/shiftguard_unified/fixed_candidate_null_protocol_v1.md` and
   `papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md`).

## Novelty assessment

The F8 finding is empirically interesting: on fresh synthetic `F8_rare_better` streams,
`fixed_challenger` is 6.174 cost units cheaper than CAMS (paired 95% CI [-6.857, -5.544]); an EIA
2026 replay also favors the preselected static challenger. But the synthetic scenario supplies the
challenger identity in advance, the 200-label budget is not binding (about 60 disagreements), and
the null and reversal controls show material harm from unconditional deployment. Adding a
validation gate and ordinary rollback imports known ingredients and, if the validation block is
outside the common 2,000-event/200-label contract, gives the candidate free information. Charging
its time, labels, and incumbent loss requires a new matched timeline and does not create a novelty
delta by itself.

The benefit is explained by conventional fixed/validation-selected deployment, not a new mechanism.
The trained EIA challenger profile screen failed its frozen two-of-three BA gate; the positive EIA
replay is one provider with simulated label timing and hypothetical costs. Elexon is a
metadata-verified chronological source candidate, but no outcome has been evaluated there.

**Verdict:** no distinct F8 method contribution is supported. Retain F8 as a benchmark/case-study
result. A manuscript may claim the scoped failure and positive fixed-policy comparison, but must
label the policy as conventional and must not claim method novelty. Do not implement a
validation-plus-rollback variant as a new method without a separate, non-obvious mechanism and
matched-cost evidence against the listed methods.

## Independent review

A read-only adversarial reviewer reached the same conclusion and identified the fairness constraint:
validation must be charged to the shared horizon, label budget, and incumbent loss; a free
predeployment block can manufacture the apparent advantage. The review trace is recorded in
`.aris/traces/novelty-check/2026-11-07_run01/` (local audit trace, not a paper artifact).

## Evidence reviewed

- `docs/failure_atlas_v2_flq/results/atlas_synthetic_discovery.md`, F8 section.
- `docs/scoped_method_research_2026-11-06/eia930_f8_synthetic_followup/PROTOCOL.md` and `RESULTS.md`.
- `research/scoped_method/pilots/eia930_f8_2026_confirmation_20261107/RUN_STATUS.md`.
- `research/scoped_method/pilots/eia930_f8_ml_challenger_20261107/DECISION.md`.
- `research/scoped_method/ELEXON_SOURCE_FEASIBILITY_20261107.md`.
- Primary papers linked above; targeted audit, not exhaustive survey of all related literature.
