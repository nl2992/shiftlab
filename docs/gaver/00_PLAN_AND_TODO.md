# GAVE-R investigation: breakdown and todo

Branch `research/gave-r-2026-11-06` (worktree `ICML/shiftlab-gave-r-2026-11-06`), cut from
`main@7354480a` on 2026-11-06.

Source: external deep-research report "ShiftLab Methods Direction: Gap-Aware, Deadline-Aware
Evidence for Reversible Model Switching" (copy kept outside Git at
`C:/Users/nigel/Downloads/deep-research-report.md`). It expands
[failure_atlas_next_method_proposal_v1.md](../failure_atlas_next_method_proposal_v1.md). Its
candidates and scores are the report author's hypotheses, not measured results. The report's
citations (`cite...` tokens) are not resolvable from the text and must be re-checked before any
are used in a write-up.

## Ground rules

- Charter, AGENTS.md and the Atlas ledger take precedence. Cycle-7 outcomes stay as recorded.
- Fresh seeds only, allocated through `shiftlab.seed_registry.allocate` and registered in
  `configs/seed_registry.yaml` before use. No confirmation seeds are consumed in this branch.
- Synthetic oracle truth (onset, duration, rho, effect) is evaluator-side only.
- Model routing: Opus plans and reviews; Sonnet subagents code and run; Haiku does lookups.
- Anything longer than ~10 minutes runs detached with checkpoints (see `detached-long-runs`).
- Grade effects with the fair scale (substantial ≥10%, meaningful 3–10% with CI excluding 0,
  small 1–3%, negligible <1%). No single bar decides a verdict.

## Lowered completion bars (what "investigated" means here)

An item is **done** when it has a recorded verdict (positive, negative, or inconclusive with the
reason) in `docs/gaver/`, backed by code that runs and a smoke-scale result. This branch is
**development/screening only**, so the bars are deliberately lighter than the report's:

| Report's bar | Bar used here |
|---|---|
| 60 dev / 200 validation / 500 confirmation seeds per cell | 60 paired dev seeds per alternative cell (30 acceptable for a first read) |
| ≥2,000 null streams per null cell, 5–10k near threshold | 500 null streams per null cell; escalate to 2,000 only for a candidate that looks safe and useful |
| Full factorial grid (8 axes) | Atlas regression cells + their neighbours + a ≤12-cell slice over rho × delay × onset |
| Source-faithful SOTA comparators for every baseline | Existing registered Atlas comparators; external methods only where code already exists in the repo |
| Holm-corrected multi-contrast testing, simultaneous null bounds | Paired bootstrap CI on cost; Clopper–Pearson upper bound on null false promotion; Holm only if a claim is drafted |
| Real-data confirmation (Wild-Time) | Out of scope for this branch; feasibility note only |
| Tests | Light unit tests: factor expectation ≤1, budget/pending invariants, no-unreleased-label access. No exhaustive suites |

A component **passes screening** if: null false-promotion upper bound ≤ alpha (alpha = 0.1, the
Atlas contract) at rho ≤ 0.8; it shows at least a *small* paired cost or power gain over its
strongest in-repo comparator in its target cells; and it is not materially worse in the
neighbouring cells. rho = 0.95 is reported, not required.

## Work packages and todo

Status keys: `[ ]` open, `[~]` in progress, `[x]` done (verdict recorded), `[-]` dropped with reason.

### WP0. Contract and harness map (prerequisite, light)

- [ ] 0.1 Map the Atlas cycle-7 harness: where DSS/straddle, Markov LR comparator, E_rb,
      promotion/rollback, pending queue, cost accounting and the regression cells live; how to run
      one cell at smoke scale. Output `docs/gaver/01_HARNESS_MAP.md`.
- [ ] 0.2 Write the observation contract: filtration, predictable requests, fixed delay, pending
      labels never used as evidence, hard pathwise budget. One page, in the same file.
- [ ] 0.3 Allocate and register a fresh GAVE-R development seed block.

### WP1. Gap-Mix: actual-gap evidence (report priority 1 of the modules)

- [ ] 1.1 Implement the conservative gap envelope factor `u_g` (proposal §1) as an e-process under
      uniform acquisition. Unit test: conditional expectation ≤ 1 on a parameter grid.
- [ ] 1.2 Implement an exact-gap Markov likelihood comparator using `P^g`, with a safe treatment of
      the composite null (certified sup, not a coarse grid).
- [ ] 1.3 Add a small frozen restart mixture {0, .25T, .5T, .75T} with explicit weights.
- [ ] 1.4 Null calibration, uniform calendar: rho ∈ {0, .5, .8, .95}, 500 streams each, vs iid
      e-process, existing Markov LR, fixed gap 4 / gap 10 at matched label counts.
- [ ] 1.5 Power/delay on early, late and transient alternatives at the same budgets.
- [ ] 1.6 Verdict: `docs/gaver/10_GAPMIX_RESULTS.md`. Stop rule: if no valid variant has useful
      power at the available budgets, record it and narrow the dependence range openly.

### WP2. PAVE: pending-aware value-of-label governor

- [ ] 2.1 Implement the governor on top of the *unchanged* existing evidence engine: state =
      evidence, proxy gap, remaining horizon, budget, pending count/ages, deployment state,
      rollback reserve. Short rollout over 2–3 candidate next-request gaps; query iff estimated
      net value > 0.
- [ ] 2.2 Replace the fixed pending cap with `ceil(delay * remaining_budget / remaining_horizon)`
      as a simple control (diagnostic, not a novelty claim).
- [ ] 2.3 Run the two mandatory regression cells
      (`on0.6_L1_strong_harmful_d50_b0.05_s0.1`, `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`),
      their neighbours, and the cycle-7 primary cells at 60 dev seeds vs DSS, uniform, and
      undecided-only.
- [ ] 2.4 Small factorial ablation: pending state on/off × deadline value on/off × reserve on/off.
- [ ] 2.5 Verdict: `docs/gaver/20_PAVE_RESULTS.md`. Stop rule: no attributable benefit over
      uniform with the same evidence.

### WP3. FreshCheck: separate promotion and current-value evidence

- [ ] 3.1 Implement: retire promotion wealth at switch; start a fresh post-switch evidence process
      for keep/rollback, with a small label reserve.
- [ ] 3.2 Compare with promotion-only, E_rb, two-phase persistence and simple hysteresis on
      reversal, transient and persistent alternatives (60 dev seeds/cell).
- [ ] 3.3 Ablations: reuse old wealth vs fresh; reserve vs none.
- [ ] 3.4 Verdict: `docs/gaver/30_FRESHCHECK_RESULTS.md`. Pass if post-reversal harm drops without
      losing more than a *small* amount of persistent-case value.

### WP4. Prior-art spot check (parallel, light)

- [x] 4.1 Verify the report's key neighbours exist and say what the report claims: Drift2Act,
      Gong & Zhang (Cost of Information), Sethi et al. Markov sequential tests, Gafni–Iyengar–Zeevi,
      WATCH, PPRM, The Challenger, Lau & Tay. Record title/authors/venue/link and one line on overlap
      with each of Gap-Mix, PAVE, FreshCheck. Output `docs/gaver/40_PRIOR_ART_CHECK.md`.
      Bar: abstract-level verification; full-text reading only for the two closest.

### WP5. GAVE-R integration (only after WP1–3 verdicts)

- [ ] 5.1 Combine only the components that passed screening.
- [ ] 5.2 2×2(×2) interaction study: evidence × acquisition (× FreshCheck) on the regression +
      primary cells. Report whether the joint gain exceeds the sum of the parts.
- [ ] 5.3 Verdict and decision-tree outcome (report §"Decision tree"):
      `docs/gaver/50_INTEGRATION_RESULTS.md`.

### WP6. Wrap-up

- [ ] 6.1 Fair grading of every finding, continue/pivot/stop assessment, reproducible commands and
      commit hashes: `docs/gaver/90_SUMMARY.md`.
- [ ] 6.2 Update the Atlas ledger with a pointer (no rewriting of earlier outcomes).

### Deferred (not in this branch unless WP1–5 justify it)

- Candidates C5–C10 (Straddle-Safe, Usable-Life Hazard, Gap-H2c, Dual-Budget, ATC-RMM,
  Gap Portfolio). C5 is the cheap fallback if Gap-Mix is powerless.
- Fresh confirmation runs, Wild-Time real-data replay, external comparators without in-repo code.

## Execution order

WP0 first (short). Then WP1, WP2, WP3 and WP4 in parallel, each in its own files
(`src/shiftlab/gaver/{gapmix,pave,freshcheck}.py`, `scripts/gaver/`, `tests/test_gaver_*.py`,
`outputs/gaver/<wp>/`). WP5 waits for the three verdicts.

## Progress log

- 2026-11-06: branch and plan created.
- 2026-11-06: WP4 done (abstract/snippet level). Closest threats: Gap-Mix–Sethi et al.; PAVE–Gong & Zhang; FreshCheck–The Challenger/Drift2Act. PPRM venue and Sethi e-process framing unverified.
