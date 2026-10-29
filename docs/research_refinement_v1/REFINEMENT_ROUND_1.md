# Refinement round 1: research proposal

**Recorded 2026-10-28, loop tick 6.** It follows the ARIS `research-refine` proposal structure
(problem anchor, technical gap, thesis, claim-driven validation) together with every field the
brief requires.

**Status labels:**
- **[established]**: a frozen, verified repository result or a published theorem;
- **[elementary]**: a short exact derivation, checked numerically, not yet written as a proof;
- **[hypothesis]**: an untested empirical prediction;
- **[heuristic]**: an engineering rule.

# Proposal: When does decision-aware monitoring and intervention help? A matched-information benchmark of paired decision harm under distribution shift

## Problem anchor (frozen for all rounds)

A deployed policy `π_t` can become worse than an explicit reference `π_ref` in **downstream
decision loss** without any reliable signal from distribution-shift or predictive-risk monitors,
and vice versa. Practitioners must choose among:
- monitors: feature drift, predictive risk, paired decision harm;
- label-acquisition rules: uniform, gated, paced;
- responses: continue, revert to the reference, certify and promote a candidate, or a full
  pipeline.

The literature evaluates these pieces under different estimands, feedback contracts and budgets.
That makes "which works, where, and why" unanswerable from published results.

## Technical gap

No published study compares decision-harm monitors and intervention rules **on the same paths,
the same null, the same label and dollar budgets and the same engines**, with calibrated null
control and a mechanism-level explanation of the rankings. Prior work:
- Ahmed et al. 2026 audit label-free monitoring and test-time adaptation on predictive endpoints
  for one natural shift pair.
- DISCERN (Balachandran 2026) supplies gating theory, not a composed benchmark.
- Timans et al. UAI 2025, PPRM ICML 2026 and WATCH ICML 2025 each evaluate their own estimand.

(Matrix §1 and B2; Codex Appendix G.)

## Thesis (one dominant claim)

**Claim A (dominant).** On a matched-information benchmark of paired decision harm, the rankings
of published monitors and intervention rules are governed by two quantities:
1. **how many labels land on events where the paired cost can be nonzero**, which explains the
   gating and pacing results;
2. **whether a safe reference policy is available and stays safe**, which explains when reverting
   beats certifying.

Novel mechanisms add nothing beyond these: every candidate mechanism screened failed its
registered margin.

Claim A is supported by four headline findings, each tied to a frozen, verified artifact:

| ID | Finding | Status | Artifact |
|---|---|---|---|
| H1 | **Label waste.** Ungated sparse-label monitoring spends most labels on events with known zero paired cost. Gated HT grows evidence 7.20× faster than correctly bounded uniform PPI at `r = 0.20` (95% interval 6.88–7.55), and detects in 100 of 100 discordant streams at `r = 0.05`, with 0 losses. | [established] | `docs/gated_monitor_comparison_results.md`; `outputs/gated_monitor_compare/analysis/decision.json` |
| H2 | **Analytic growth law.** G1's pre-registered analytic prediction (18 / 18 / 15 / 7.5) matched the measured ratios (17.5 / 20.6 / 14.7 / 7.2) at all four budgets. | [established] | same |
| H3 | **Pacing reversal.** Fixed gating is at least as good as past-paced gating under bursty disagreement: S3 `harmful_adaptation` (0.86 against 0.76 detection at `r = 0.10`) and EIA injected harm (fixed matches the full-feedback delay in 10/10 cells from `r = 0.05`). | [established] | S3 results; `docs/eia_real_data_validity_results.md` |
| H4 | **Revert versus certify.** In the frozen integrated confirmation (100 seeds per profile), monitor-then-revert gains +664.6 / +685.9 / +448.0 on boundary harm, monitor-aligned adaptation and recurring regimes. The full pipeline gains +118.0 / +161.2 / 0, and fixed-candidate certification +285.9 / +263.1 / 0. Reverting loses −1,148.5 after a post-promotion reversal, where the full pipeline loses −143.8. It gets 0 on native adaptation, where certification gains +263.1. | [established; previously unreported] | `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv` |

**Supporting claim S (at most one).** *Label-invariance proposition* [elementary]. For a gated HT
increment with predictable propensity `q_t`, a paired cost in `[−C, C]`, an anchor `h = 0` and a
stake set to a fixed fraction `c` of the predictable cap (`λ_t = c/B_t`, with `B_t = C/q_t + ε`),
the expected log-wealth gain **per label spent** equals:

`E[ log(1 + c(Z − εq)/(C + εq)) | F ] − (1 − q)·cε/(C + εq)` + O(cεq).

It is exactly independent of `q` when `ε = 0`. **Corollary:** for any predictable allocation
rule, evidence at time `t` is determined to first order by the number of labels spent on
disagreement events with positive conditional excess, that is, after onset.

Two of the headlines follow:
- **H1 and H2:** gating raises the informative fraction from about `ρ` to 1.
- **H3:** a past-paced rule throttles post-onset spending during bursts, so it spends fewer
  informative labels per unit time. Fixed gating at `q = 1` spends them all.

## Formal setup and filtration

- **Events and information.** Events `t = 1, 2, …` carry covariates `X_t`; a deployed action
  `π_t(X_t)` and reference action `π_ref(X_t)`, both predictable (`F_{t−1}`-measurable rules); a
  disagreement indicator `D_t = 1{π_t(X_t) ≠ π_ref(X_t)}`, observed for free; a query decision
  `G_t ~ Bernoulli(q_t D_t)` with `q_t` predictable given `F_{t−1}` and `X_t`; and, if queried,
  an outcome `Y_t`. `F_t` is generated by all of these, with `Y_s` included only for queried `s`.
- **Feedback model.** The common-label contract: `Y_t` identifies both actions' costs, so
  `Z_t = c(π_t(X_t), Y_t) − c(π_ref(X_t), Y_t)` is observed whenever queried. **This holds in the
  synthetic generators and the imposed-cost EIA reserve task only.** It is not assumed for action-
  dependent outcomes; those are out of scope (the matrix's G1 and G3). In the frozen S3 and WP4
  runs the label delay is 0. Delayed feedback is reported from the separate delayed-feedback line
  and is not pooled.
- **Estimand and null.** For decision harm, the conditional excess-cost null is
  `H_0: E[Z_t − ε | F_{t−1}, X_t] ≤ 0` for all `t` (charter). The benchmark also reports the
  distributional-change and predictive-risk endpoints in separate panels, never pooled.
  Intervention panels use evaluator-side expected utility, an oracle quantity visible only to the
  evaluator.
- **Validity.** Each monitor's type-I control is the published or derived guarantee for its own
  engine under this conditional null: predictable `q_t ≥ q_min`, bounded increments and the
  predictable cap. **The benchmark does not claim new validity.** It reports Monte Carlo null
  calibration (S2: 2,000 streams per cell, simultaneous Bonferroni exact upper bounds ≤ 5%) and,
  on real paths, per-path random-orientation nulls (WP4: 68/68 cells pass). These are calibration
  evidence, not proofs.
- **How the hard cases are handled:**
  - *Candidate selection:* candidates are frozen before evaluation (Target-Scout and fixed
    certification use registered splits).
  - *Adaptive sampling:* propensities are predictable and recorded.
  - *Delayed labels:* excluded from the primary panels; delay is a separate line.
  - *Repeated testing:* one e-process per registered arm and cell, with Bonferroni across cells
    for calibration and Holm for paired comparisons.
  - *Optional stopping:* e-process validity at arbitrary stopping times holds under the
    conditional null. The intervention panels stop at the first alarm. **Composition validity
    across monitor → certify → promote is not claimed** (matrix G3).

## Algorithm

**No new algorithm is proposed.** The benchmark uses existing, source-fidelity-labelled
implementations: gated HT/PPI with Timans GRAPA, PPE, Xu active betting and fixed stakes; horizon
SR/CUSUM; Target-Scout; fixed-candidate certification; MOPE/OCS; the two-gate pipeline;
`q1_fallback`; and the full pipeline. Proposition S motivates no new rule. It explains existing
rankings.

## Assumptions required

1. The common-label contract (identification of both action costs). This holds only in the
   synthetic generators and EIA imposed costs.
2. A predictable `q_t` with a floor; bounded `Z`.
3. The conditional null as stated. Mixed-null failure is documented in
   `docs/residual_variance_context_null_audit.md`.
4. Oracle utility only on the evaluator side (synthetic only).
5. Real-data panels are retrospective and on previously examined windows. **No confirmatory
   real-data claim.**

## Theory: proof obligations

| Item | Status | Obligation |
|---|---|---|
| Proposition S (label invariance) | [elementary] | Write the exact identity. Bound the O(cεq) remainder. Extend to the PPI anchor (bound `(C+ε)(2/q−1)`) and to a mixture over stakes (does the invariance survive mixing with a fixed stake grid?). State the hard reserve stop as a stopping rule that does not affect invariance up to exhaustion. |
| Corollary (evidence is set by informative labels) | [elementary] | Give the first-order delay approximation `τ ≈ log(1/α)/(g · n_informative rate)` and its conditions (bounded `Z`, stationarity after onset). |
| Analytic growth law (H2) | [established, pre-registered prediction] | Restate as a consequence of S with `ρ` the disagreement rate; reconcile with DISCERN's Θ(1/ρ) (Thm 9) and **credit it**. |
| Validity of each engine | [established, published] | Cite. No new validity theorem is claimed. |

## Minimal sufficient baselines

- Uniform PPI, correctly bounded.
- Gated HT fixed and paced, under fixed-stake, Timans GRAPA and PPE engines.
- Xu active betting.
- Full feedback, as an unmatched reference.
- Feature ADWIN, a label-free sentinel.
- Intervention panel: continue, `q1_fallback`, two-gate, fixed-candidate certification, the full
  pipeline and their controller variants.

All are already implemented and frozen.

## Three core experiment blocks

1. **E1. Independent re-verification (no new seeds).** A Haiku- or Sonnet-written verifier,
   independent of the original analysis scripts, recomputes H1–H4 and the S2/WP4 null tables from
   the frozen artifacts with hash checks. It must fix the documentation errors: the S2 seed-block
   typo and the Target-Scout hash drift (re-run its manifest check or record non-equivalence).
2. **E2. Mechanism decomposition (descriptive, frozen outputs).** For S3 and WP4 arms, compute
   post-onset informative labels per arm and regress delay on them. For the integrated
   confirmation, decompose utility by profile into (a) whether the reference is safe after the
   alarm and (b) whether the candidate persists. This needs only existing per-stream outputs; if
   post-onset label counts are not stored, record that E3 must log them.
3. **E3. One pre-registered falsification cell for Proposition S (new seeds, CPU-sized).**
   - *Design:* match fixed and paced gating on post-onset informative labels by giving the pacer an
     onset-oblivious rate that spends the same expected post-onset budget.
   - *Prediction:* equal detection delay within a registered margin, in both a weak-signal cell
     (`μ` small) and a strong-signal cell (`μ` large).
   - *Registration:* freeze the protocol and a fresh seed block, disjoint by **machine-checked
     registry**, before running.

## Metrics

- **Primary:** per-panel detection probability by horizon with exact intervals; censored delay;
  labels; dollars; null false-alarm rate (exact upper bound); for intervention, paired expected
  utility against continue, Holm-adjusted.
- **Secondary:** H2 prediction error; E2 regression slope and fit; post-onset informative labels.

## Expected failure modes

- E1 may not reproduce a headline (hash drift, missing per-stream fields).
- Proposition S may fail for the mixture engine or the PPI anchor. The corollary would then hold
  only for fixed-fraction stakes.
- E2 may not have post-onset label counts stored.
- H4 is evaluator-oracle and synthetic. A reviewer may call it obvious ("of course reverting helps
  when the reference is safe").
- The overlap with Ahmed et al. and DISCERN may be judged too large for a main-track venue.

## Falsifiable success criteria

- **Claim A survives** if all of: (i) E1 reproduces H1–H4 exactly, up to the recorded tolerances;
  (ii) E2 finds that post-onset informative labels explain the fixed/paced and gated/ungated delay
  differences (registered threshold R² ≥ 0.8 across arms within a cell); (iii) E3 matched arms
  differ by less than the registered margin (|Δ detection| ≤ 5 points, delay ratio within
  [0.8, 1.25]) in both signal cells.
- **Claim S is falsified** if E3 matched arms differ beyond the margin in either cell, or the
  exact identity fails for the engines actually used.
- **Abandon Path A as a standalone paper** if:
  - two or more of H1–H4 fail E1; or
  - a published matched-information decision-harm benchmark covering H1–H4 is found; or
  - Claim S fails **and** E2 explains less than half the variance, leaving the benchmark without
    a mechanism.

  The decision then moves to NO_GO, with the findings folded into a workshop or technical report.

## Separately gated track (not part of Claim A)

**G4 / Paper 3 theory pre-screen.** After the tick-6 correction, G4 reduces to budget allocation
against an unknown onset and bursts. Before any implementation, the pre-screen must show that the
minimax schedule differs from fixed gating **and** does not map onto Geng–Bayraktar–Lai sampling
rights or Zhang–Cheung reservation. **Expected outcome: stop.** It is recorded here only so it is
not lost.

## Compute and timeline

- **E1:** about 1–2 hours of CPU, with no new data.
- **E2:** under 1 hour on existing outputs.
- **E3:** about 1 hour of CPU at the S3 scale for one cell pair. It needs registration first.
- **Writing:** the manuscript draft exists (`manuscript_draft_v0.md`) and needs restructuring
  around Claim A.
