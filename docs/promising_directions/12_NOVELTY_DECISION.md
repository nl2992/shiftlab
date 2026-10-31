# 12 Novelty decision by lane

This file applies the mandatory IF/THEN controller to the evidence in files 00–11. The Lane A
row depends on A1b (`protocols/A1b-growing-family.md`); see the A1b section.

| Lane | Question | Best result | Strongest baseline | Gate outcome | Novelty status | Recommendation |
|---|---|---|---|---|---|---|
| A joint acquisition + switching | Information-matched joint vs separable gap | Registered A1 grid of 488 exact cells: max 0.874%, KILL. Critic's post-hoc family: 0.50 → 3.89% over T = 6..10 at alpha = 1/5 | Slot-skippable calendar with exact risk-constrained switching | A1 KILL under its protocol; A1b decides whether the critic's family survives | Proposition A0: any information-matched gap is a timing-adaptivity gap. Existence is standard belief-DP; novelty would require a growing-family lower bound | **Close for the programme's risk levels; INCONCLUSIVE residual at alpha = 1/5** (see A1b) |
| B paired-benefit certification | Does a valid paired certificate cut net switching cost? | B2: P3b −7.7 to −10.2% vs best of never / always / incumbent-alarm, all CIs exclude 0 | Critic's untuned fixed-sample paired batch test: −7.3 to −9.3%, within 0–0.9 percentage points of P3b (−0.2 to 3.0 cost units). In-sample-tuned version ties or beats P3b | B1 MIXED; B2 MIXED. No setting passes against the batch test | Composition of IPW paired increments, structural zero and predictable betting (CAMS / Xu et al.) | **Stop as method.** Keep as benchmark finding: propensity-matched bet caps matter (3.5% → ~9%), and certification beats incumbent-alarm switching in this generator |
| B-Q2 persistence-aware promotion | Does known-hazard promotion help under reversal? | +0.2–0.8% in W3 | P3 | NOT SUPPORTED (P4 loses 9.5–23.9% in W1) | Plug-in decision theory | **Stop** |
| C H2c | Within-class power gain | G5 +0.086 / +0.094, verified at analysis level | Per-cell better of discounted Kelly / ONS (local parents) | Better only than local parents. Reduces exactly to discounted Kelly with a substituted moment ratio. Reverses on exposed Gas. Power ≈ 0 with unknown nominal, n_cal ≤ 1000 | Composition | **Retain as component-level benchmark** (controller rule) |
| D HG | Decision-harm monitoring vs classical detectors | +0.029 / +0.052 power vs PPRM parent; harm 15% / 25% lower on harm worlds | Page–Hinkley / CUSUM (HG −0.066 / −0.110, n.s.) | Inferior to PH/CUSUM; invalid under dependence (FAR up to .23) | Repaired composition | **Retain as reference; stop generic betting refinements** |
| E disagreement querying | Gain beyond CAMS-style querying | Structural-zero querying is used inside P3 / P3b | CAMS-style / batch paired test | CAMS-style methods attain the mechanism | Not novel | **Treat CAMS as the baseline** |
| F action-set-aware regime harm | When does a conditional alarm justify action? | Inherited stylised result: 601.5 → 298.0 vs oracle 213.4 with a useful fallback; +6–10% worse without one | Regime-aware oracle / no-switch | Explanatory. Critic: P3b false-promotes 20.8% under a persistent-regime *marginal* null | Conditional monitoring + decision theory | **Benchmark / explanatory finding only** |
| G risk-preserving optimisation | Scalable controller with value guarantee | Abandonment controller class matches the sequence-form reference in all tested cells (inherited) | Exact decomposed planner | A1b found no gap at the programme's alpha levels | — | **Stop**: no material gap to approximate |

## Contradictions resolved

- The sweet-lovelace "DP-implied, so not novel" kill does not satisfy the user-approved R2. This
  programme closes lanes on registered empirical gates and on Proposition A0, not on ingredient
  ancestry alone.
- The critic was right that A1's three-horizon trend rule had low power. A1b addresses this.

## A1b section

Results: `results/a1b/cells.jsonl`, sha256 `0d8fe33d…eb89`. Each gap was recomputed from exact
rationals by the orchestrator, and J ≤ C* holds in every solved cell.

| alpha | T=6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|
| 1/5 | 0.500% | 0.799% | 1.178% | 2.885% | 3.889% | 4.641% | not run (registered node cap exceeded) |
| 1/10 | — | — | — | 0 | 0 | 0 | — |

The best calendar moves from [1, 2, 3] to [2, 3, 4] at T ≥ 10.

The run crashed at T = 12 because the runner caught only MemoryError. T = 12 was recorded as
failed and was not retried with altered settings. The exception handling was then widened, and
the run resumed for the secondary cells. `run1_crash.log` and `run2.log` are kept.

Mechanical decision:

- **INCONCLUSIVE.** CONTINUE requires g ≥ 0.10, or three increments each ≥ 0.005 with
  g(T_max) ≥ 0.05. The increments are 0.0171, 0.0100 and 0.0075, so the first part holds, but
  g(11) = 0.0464 < 0.05.
- KILL requires the last increment to be < 0.0025. It is 0.0075, so KILL does not apply either.

Interpretation, not a registered outcome:

- The increments are shrinking, roughly geometrically (×0.59, ×0.75). A plateau below the 10%
  practical threshold is plausible, but extrapolating past T = 11 is not evidence.
- At alpha = 1/10, which is in the programme's declared null-risk levels {0.05, 0.10}, the
  same family has **zero** gap through T = 11.
- So the only information-matched separation found needs a 20% false-promotion tolerance.
  It is the timing-adaptivity gap of a known-model HMM sensing problem, which is a classical
  POMDP sensor-scheduling effect.

Lane A verdict: no joint-acquisition method claim at the programme's risk levels. What
remains open is a theory question, not a method lead: does the adaptivity gap in this family
scale with T at loose alpha, and why does tightening alpha remove it? Pursuing it needs either
a larger node cap (a registered settings change) or an analytical bound.

## A1c / A1d addendum (mechanism probe after A1b)

**A1c** (`protocols/A1c-alpha-mechanism.md`, results `results/a1c/`, verified from exact rationals)

- At T = 9, the gap g(alpha) is 0 for alpha ≤ 1/8.
- It turns positive at alpha = 3/20 for every prior1 tested (1/10, 1/5, 3/10).
- It reaches 4.7–6.1% at alpha ∈ [1/4, 1/2].
- Without a risk constraint (alpha = 1) the gap is only 0.9–1.6%.
- The constraint binds in every cell: raw risk = alpha, activation 1.
- g(12) = 5.02% at alpha = 1/5, with increments falling below the A1b CONTINUE thresholds.
- Mechanism (P5, T = 8, alpha = 1/5): both policies query at t = 1. After a *negative* first
  label, the joint planner re-checks at t = 4 with probability 0.6; the calendar never
  re-checks. The joint planner promotes with probability 0.255 and never rolls back. The
  calendar promotes with probability 0.205 and rolls back with probability 0.009.

**A1d** (`protocols/A1d-mixture-comparator.md`, results `results/a1d/`)

A1c compared J against pure calendars, a non-convex class. A1d replaces this with public-coin
mixtures of calendars, each solved at its own risk level: 3,906 exact calendar solves with no
failures. The orchestrator recomputed the lower convex envelope independently and found
J ≤ C_mix ≤ C* everywhere.

Mixing removes part of the gap:

| prior1, alpha | g (A1c) | g_mix (A1d) |
|---|---|---|
| 1/5, 1/5 | 2.89% | 1.46% |
| 3/10, alpha ≤ 1/4 | up to 1.81% | 0 |

At intermediate risk levels the gap remains:

| prior1 | alpha | g_mix | g_mix(1) |
|---|---|---|---|
| 1/10 | 1/4 | 5.07% | 1.62% |
| 1/10 | 3/10 | 5.19% | 1.62% |
| 1/10 | 1/2 | 5.80% | 1.62% |
| 1/5 | 1/4 | 2.57% | 1.20% |
| 1/5 | 3/10 | 4.04% | 1.20% |
| 1/5 | 1/2 | 4.73% | 1.20% |
| 3/10 | 3/10 | 1.98% | 0.92% |
| 3/10 | 1/2 | 5.60% | 0.92% |

Mechanical decision: **H-risk SURVIVES**. The largest excess over the unconstrained gap is
4.7 percentage points.

**Status.**

- A *risk-specific* information-matched separation exists in exact small instances. A binding
  false-promotion constraint makes history-dependent acquisition timing valuable beyond the
  unconstrained adaptivity gap and beyond any public-coin mixture of calendars.
- The plausible structure is *risk-ledger-dependent acquisition*: the planner spends queries
  conditionally on whether the risk budget is likely to be consumed by a promotion.
- This is the first lead in this programme that is not a known unconstrained effect.

**Limits.**

- One model family.
- T ≤ 12.
- Every gap is below the 10% practical threshold (maximum 6.1% pure, 5.8% mixture).
- It appears only at alpha ≥ 3/20, which is above the programme's declared 0.05/0.10 levels.
- No theorem exists yet.

**Next gate (A2).** Gate A2 asks whether a growing family has a provable lower bound on
g_mix that is specific to the risk constraint. Until that question is answered, this is a
theory lead, not a method claim. The overall programme classification stays BENCHMARK /
NEGATIVE-RESULT PIVOT, with Lane A upgraded from "closed" to "open theory lead at loose alpha".

## A2 addendum (binding-alpha screen)

Protocol: `protocols/A2-binding-alpha-screen.md` (`ba93246`). Results: `results/a2/`
(`screen.jsonl` sha256 `404cd582…f3e4`).

The orchestrator recomputed every gap from exact rationals. All 162 cells completed, with no
failures.

**Gap by alpha (54 families each).** The families cross accuracy {0.9, 0.95, 0.98}, transition
{1/20, 1/10, 1/5}, prior1 {1/20, 1/10, 1/5} and cs {1/20, 1/5}, at T = 8, B = 3, d = 1.

| alpha | gap > 0 | largest gap |
|---|---|---|
| 1/20 | 0 of 54 | exactly 0 |
| 1/10 | 0 of 54 | exactly 0 |
| 1 (unconstrained) | 31 of 54 | 4.37% |

**The zero gap is not vacuous.** At both tight levels, every family's optimum uses all three
queries as a contiguous confirmation burst: [2,3,4] in 30 families, [3,4,5] in 18, [1,2,3] in
6. No shorter calendar ties it. J(1/10)/J(1) lies between 1.12 and 1.84, so the risk
constraint is costly. Because the burst does not depend on the labels, a fixed calendar is
exactly optimal. Unconstrained optima spread their queries out instead ([2,4,6], [1,3,5]).

**Decision: CONFINED TO LOOSE ALPHA.** No family survived the screen, so the A2b mixture check
had nothing to run on.

**Three-regime picture.** This is consistent with `13_A2_BRANCH_CONFLICT_THEORY.md`, which is
descriptive here and not proved in general:

1. *Tight alpha* (≤ 1/10 in every family tested). The risk budget forces a label-independent
   confirmation burst, and calendars are exactly optimal.
2. *Intermediate alpha* (≈ 3/20 to 1/2 in the A1c family). The promotion branch needs
   confirmation slots, the non-promotion branch needs a delayed re-check, and the budget
   cannot cover both. This branch conflict produces the risk-specific gap: g_mix up to 5.8%.
3. *Unconstrained*. Only the ordinary timing-adaptivity gap remains, up to 4.4%.

**Lane A verdict (final for this programme).**

- At the programme's declared risk levels (0.05, 0.10), joint acquisition and switching gives
  **no** value over a fixed calendar in any of the 54 + 288 exact families tested (A2, A1).
- The risk-specific separation is real, but it is confined to looser false-promotion
  tolerances (alpha ≥ 3/20) and stays below the 10% practical threshold.
- It is a publishable *structural/benchmark* observation about tight risk constraints, if it
  survives the literature audit. It does not support a method claim.

Limits:

- T ≤ 8 for the screen.
- B = 3 only. A larger B might fit both a burst and a re-check, which is untested.
- One HMM family class.
