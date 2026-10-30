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
