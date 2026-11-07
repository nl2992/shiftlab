# T3 matched-host Track-R follow-up

Registered 2026-11-05 before the follow-up Track-R result is inspected. This closes a missing
separate-seed operating-characteristic panel for T3; it is post-development and does not alter the
candidate's Track-E result, selection, or the historical family verdict.

## Question and scope

Estimate the empirical cost-risk operating points for the two T3 A5b variants and their matched
corrected-DISCERN hosts, using the shared Sprint 2 risk-null and alternative mixes. Include A5b and
D2 as cross-family references. The panel is descriptive; it does not establish an anytime-valid
guarantee, correct the original candidate selection, or represent independent replication.

## Frozen protocol

- Contract and regimes: `bench2` defaults, T=2000, B=200, `RISK_NULLS`, `RISK_ALTS`,
  `RISK_TARGETS`, and `ALPHA_GRID`.
- Policies: `T3:discern/a5b`, `T3:discern/a5b+front`, `discern_design_floor`,
  `discern_design_floor+front`, `A5b`, and `D2`.
- Development seeds: 20 per regime, base `2026110701`.
- Evaluation seeds: 20 per regime, base `2026110711`.
- Nominal alpha: every value in `bench2.ALPHA_GRID`; common paired streams within each phase.
- Calibration: for each policy and target, choose the largest nominal alpha whose pooled promotion
  rate over the four registered development null regimes is at most the target. No operating point
  is reported when none qualifies.
- Evaluation: use only the separate evaluation seed block. Report pooled null promotion rate with
  Wilson 95% interval and mean alternative net cost with the registered `risk_curves.py` interval.
  The script's Pareto flags compare only the six policies in this T3 panel.
- Workers: 2. Raw runs and their manifests remain under ignored `outputs/sprint2/T/T3_trackR/`.

## Reproduction

Run the `screen.py` command for each alpha in
`0.005 0.01 0.02 0.05 0.1 0.2 0.3 0.5`, once with development seed base and once with
evaluation seed base. Output paths use `dev_a<alpha>` and `eval_a<alpha>`. Then run:

```sh
uv run python scripts/sota_sprint/risk_curves.py \
  --dev outputs/sprint2/T/T3_trackR/dev_a* \
  --eval outputs/sprint2/T/T3_trackR/eval_a* \
  --out docs/sprint2/family_t/T3_trackR_followup.json
```

Keep the output separate from the historical family-wide curve until its source and row lineage
have been audited. This protocol uses the already registered Sprint 2 seed blocks and exposed
synthetic regimes; it is not confirmatory evidence.
