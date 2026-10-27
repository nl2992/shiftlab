# Independent Comparecast paired-cost alternative confirmation

**Status:** frozen before execution, 2026-10-26. This is an independent
positive-alternative confirmation of the pinned official Comparecast e-process
on the existing full-feedback paired-cost benchmark. It is not a head-to-head
validity comparison: Comparecast tests a weak running-average score null,
whereas ShiftLab's bounded mean e-process tests an eventwise conditional-mean
null.

## Question and scope

On fresh streams from the registered synthetic generator, how often does the
official Comparecast e-process cross after onset in four downstream-cost
alternatives, and how do those descriptive detection counts compare with the
ShiftLab conditional-mean process on the same realized increments?

Report each method and scenario separately. Do not test or claim superiority
from cross-method alarm-rate differences because the methods' null hypotheses
and guarantees differ. The prior 2,000-stream-per-control weak-null calibration
remains the false-escalation evidence for Comparecast; this confirmation does
not pool with or replace it.

## Frozen design

- Official source: `yjchoe/ComparingForecasters`, commit
  `52748c86e0429a9612dc79892c3be6156a524132`, unchanged e-process code.
- 300 independent seeds per scenario, seed block
  `99,100,000–99,100,299`. A repository scan of experiment manifests found no
  overlap with this block. It is disjoint from the 30-seed development screen
  and the 2,000-seed weak-null calibration.
- Six registered scenarios: stationary and benign-nuisance controls, plus
  boundary-local harm, residual-variance shift, recurring regimes, and harmful
  adaptation. `n=2,400`, `d=16`, alpha 0.05, paired-cost margin 0.10, immediate
  full feedback, monitor begins at event 800, and the generator uses CUDA.
- Both methods receive exactly the same paired cost increments. The official
  method uses support width `2B`; the ShiftLab method uses its registered
  conditional-mean e-process. The event horizon is 1,600 observations after
  monitor start; require all events to be processed.
- Primary descriptive outcomes: post-onset detection counts/rates by method
  and alternative scenario; report exact Clopper–Pearson intervals with
  Bonferroni familywise 95% coverage across the eight method-by-alternative
  cells. Also report pre-onset alarms and the two calibrated-control counts.
  No cross-method superiority test is planned.
- Require 300 streams in every method/scenario cell, the exact source commit
  and e-process hash to match the earlier calibration, finite e-values, valid
  increment support, and all 1,600 monitor events processed. Capture upstream
  NumPy warnings without editing or suppressing upstream code.
- The existing weak-null calibration is a hard execution gate. Its source
  commit, e-process hash, two population-null prefix audits, and simultaneous
  exact calibration must all be verified before launching this run.
- No plots are planned. Report a table and machine-readable metrics; no figure
  is needed for this fixed-cell confirmation.

## Reproduction

```powershell
uv run python scripts/confirm_comparecast_paired_cost.py `
  --comparecast-source C:\path\to\ComparingForecasters `
  --calibration-manifest outputs/shiftguard_unified/sota_reproductions/comparecast_weak_null_calibration_v2/manifest.json `
  --seeds 300 --seed-offset 99100000 --n 2400 --d 16 --device cuda `
  --output-dir outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1
```

This confirms one registered synthetic comparison under each method's stated
scope. It does not show that either method's theorem applies under other
feedback or dependence structures, and it does not establish real-data
performance or novelty.
