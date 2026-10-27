# Target-Scout versus fixed sample-split certification

**Status:** frozen development comparison, 2026-10-26. This protocol tests a
specific Q2 comparator gap; it is not a calibration or independent confirmation
of Target-Scout.

## Question

On matched candidate families, target streams, query uniforms, and label caps,
does selecting a context-to-candidate policy from a target scout slice and
certifying that frozen policy on the remaining slice improve expected future
net decision gain over (a) a fixed source-validation selection followed by an
independent target-monitor certificate and (b) pooled-rank sequential
candidate certification?

The fixed-split baseline selects a candidate separately for each learner-visible
context using source validation labels, freezes that mapping, and tests it on
the whole independent monitor slice. Target-Scout uses the first half of the
target monitor for policy selection and the second half for certification.
Both use the same candidate family, full monitor period, direct-IPW feedback,
alpha 0.05, 40% hard query cap, and deployment start after the monitor ends.
The pooled-rank comparator monitors the validation-ranked candidate family on
that same target monitor. Methods are project-specific selection/certification
workflows; no novelty claim is made.

## Frozen design

- `n=3,200`, `d=16`; 60 matched seed IDs beginning at `20,265,000`.
- Factorial: context prevalence 0.10/0.50/0.90, target cost-signal delta
  0/0.05/0.10, and visible-proxy error 0/0.10/0.25 (27 cells).
- Candidate costs FN=5 and FP=1, one-time switching charge 0.05, uniform
  querying, direct-IPW paired-cost estimator, fixed-mixture e-process, and
  alpha 0.05.
- The 40% monitor-label cap is pathwise and shared. Each method uses the same
  generated stream and query-uniform path within a seed/cell. Target-Scout's
  scout labels count against this cap; it cannot reuse them for certification.
- The evaluator's latent group, true outcome probabilities, and future
  potential-policy costs are used only to score outcomes, never for candidate
  selection, query choice, or certification.
- Primary endpoint: evaluator-known cumulative future net decision gain,
  including switching cost, at the 40% cap. Report promotion, harmful
  promotion, queried labels, monitor/certification rounds, and stop reason.
- Primary family: the 18 positive-signal cells, weighted equally. Compare
  Target-Scout minus fixed sample split and Target-Scout minus pooled rank.
  Resample matched seed IDs as blocks and use 97.5% intervals for the two
  contrasts. Practical margin is +1 cumulative utility unit.
- Zero-signal cells are negative controls. All 27 cells remain in per-cell
  artifacts; no selecting a best cell after seeing results.

## Run budget and decision rule

Run one 60-seed development grid (1,620 matched stream/cell blocks and three
methods per block). Do not extend the seed range or tune from these data. The
grid diagnoses whether the existing fixed-split baseline changes the
interpretation of Target-Scout's earlier comparison. It cannot establish a
population-level superiority claim or replace a separate method-specific null
calibration. If Target-Scout does not exceed the fixed-split comparator by the
registered +1 margin on the equal-cell primary endpoint, do not commission a
new efficacy confirmation for this comparison. Preserve all outcomes.

## Reproduction

```powershell
uv run python scripts/compare_target_scout_fixed_split.py `
  --seeds 60 --seed-offset 20265000 --device cuda `
  --output outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_dev_v1
```
