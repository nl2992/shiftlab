# 14 Fair re-evaluation of findings (2026-11-01)

## 0. Status of this document

This is an interpretive layer. It does not change any registered protocol outcome.

- A1 KILL, A1b INCONCLUSIVE, A2 CONFINED TO LOOSE ALPHA, B1 MIXED, B2 MIXED, B-Q2 NOT SUPPORTED and
  the lane gate outcomes in `12_NOVELTY_DECISION.md` all remain on record exactly as registered.
- No numbers were re-run. Every number is taken from `12_NOVELTY_DECISION.md`,
  `13_A2_BRANCH_CONFLICT_THEORY.md`, `06_H2C_AND_HG_REPRODUCTION.md`, `08_SYNTHETIC_DEVELOPMENT.md`,
  `11_ADVERSARIAL_REVIEW.md`, `results/a1d/LOWER_BOUNDS.md`, `results/b2/summary.json` and
  `FINAL_RESEARCH_REPORT.md`, or from the orchestrator's recomputation of `results/b2/per_seed.npz`.
- Nothing here is confirmatory. All evidence is synthetic or exposed-holdout, development-stage.

## 1. Why the earlier grading was too harsh

The programme applied the 10% net-cost bar from the master prompt as a binary pass/fail gate on every
finding, so a verified 7.7-10.2% world-averaged saving with CIs excluding 0 was recorded as "stop as method"
and the overall class became BENCHMARK / NEGATIVE-RESULT PIVOT (`FINAL_RESEARCH_REPORT.md`, section 1). A
single threshold conflates "large enough to headline" with "real and useful", and it discards the
world-by-world structure, the validity argument and the design lessons.

## 2. Rubric

| Axis | Levels |
|---|---|
| Effect size (relative net-cost or power change) | Substantial (>= 10%); Meaningful (about 3-10%, CI excludes 0); Small (about 1-3%); Negligible (< 1%) |
| Validity | Proved; argued (written argument, not independently reviewed); empirical only |
| Novelty | New result; new evidence about known methods; known |
| Practical value | Who would use it, and for what |

Grades say how big and how well supported a finding is. They do not predict acceptance, and they do not
extend any claim beyond its stated generator, horizon or exposure.

## 3. Grades at a glance

| ID | Finding | Effect | Validity | Novelty | Practical value |
|---|---|---|---|---|---|
| F1 | Certified switching (P3b) vs simple policies | Substantial (useful challenger); Meaningful on average | Argued; conditional null only | New evidence about known methods | Insurance against promoting a useless challenger |
| F2 | Propensity-matched bet cap (B1 to B2) | Meaningful (3.5% to about 9-10%) | Same as F1 | Design lesson | Anyone using IPW-gated paired e-processes |
| F3 | Persistence-aware promotion (P4) | Negative | Plug-in | Known | None |
| F4 | Calendar optimality under tight risk | Exact zero gap in certified cells | Proved (Prop. 6, Thm 7); per-instance certificates | Plausibly new; audit pending | Fixed label schedule loses nothing |
| F5 | Risk-specific branch-conflict gap | Meaningful (>= 5.07%, >= 4.68%) | Proved lower bounds, small instances | Plausibly new; audit pending | Structural insight only |
| F6 | B=4, alpha=0.10 adaptive gap | Small (0.71-1.21%) | Proved two-sided bounds | New evidence; mechanism identified | Marginal |
| F7 | Joint vs calendar at programme risk levels | Negligible (<= 0.87%; exactly 0 in 108 tight cells) | Exact | Informative null | Do not pay for joint planning |
| F8 | H2c power gain | Meaningful to substantial (relative) | Analysis verified; cost-null DOC-ONLY | Composition | Component benchmark |
| F9 | HG power and harm | Small to meaningful | Cap repair verified; invalid under dependence | Repaired composition | Reference only |
| F10 | Negative and diagnostic results | Not an effect-size claim | Mixed | Mixed | Prevents wasted effort |

## 4. Finding-by-finding

### F1 Certified switching vs simple policies (B2)

Setup: P3b is a disagreement-gated paired e-process with structural zeros and a propensity-matched bet cap.
B2 used fresh seeds 20261101 with 500 seeds per cell (`results/b2/summary.json`). Comparators are never-switch,
always-switch and incumbent-alarm switching (P2).

World-averaged result (`12_NOVELTY_DECISION.md`, lane B row): net cost -7.7% to -10.2% against the best of
never / always / incumbent-alarm, CIs exclude 0 in all four (B, c_s) settings.

Per-world result (orchestrator recomputation from `results/b2/per_seed.npz`):

| World | What it is | P3b vs never-switch | P3b vs incumbent-alarm P2 | Reading |
|---|---|---|---|---|
| W1 | Useful challenger | -36.7% to -40.5% | -15.5% to -28% | Large gain. At B200 cs5: P0 480, P2 403, P3b 289, oracle 233, so about 77% of headroom captured |
| W2 | Useless challenger | +2.1% to +4.2% (query cost only; 0/500 false promotions) | P2 is +7.5% to +15.6% over never-switch (promotes a worse model) | P3b is the safe policy |
| W3 | Reversal | +6.6% to +14.3% | Roughly equal to P2 (246 vs 246, 253 vs 247, 254 vs 267, 264 vs 269) | No advantage over P2 |
| W4 | Benign | +5% to +10% | P3b and P2 both +5% to +10% | Pure query cost |

Interpretation: an insurance profile. P3b weakly dominates incumbent-alarm switching in nearly every world.
It pays a small query premium in W2-W4 and collects a large gain in W1. This directly addresses the
programme's central failure pattern 1: detecting incumbent deterioration is not certifying a useful challenger.

Grade:

- Effect: Substantial in the useful-challenger world; Meaningful on average (7.7-10.2%).
- Validity: argued. Boundary-null false promotion was 3.05% (B=200) and 2.67% (B=400) at 20k paths, which is
  valid. The guarantee is conditional-null only: under a persistent-regime marginal null, false promotion was
  20.8% (`11_ADVERSARIAL_REVIEW.md`).
- Novelty: new evidence about known methods. The components (IPW paired increments, structural zeros,
  predictable bets) are known from CAMS and Xu et al.
- Practical value: a team with a deployed incumbent, a candidate challenger and a label budget, that must
  avoid promoting a worse model.

Caveats that stay attached to F1:

- Stylised four-world generator, fixed delay 5, one generator family, hand-weighted worlds.
- The adversarial review's untuned fixed-sample paired batch test matched P3b within 0-0.9 percentage points
  (-0.2 to 3.0 cost units). Its error control was not established, so this is not a clean comparison. An
  in-sample-tuned version ties or beats P3b by up to 2.8 cost units at B=400. An advantage of anytime-valid
  testing over a batch paired test is therefore not shown.
- A weaker-signal generator reduced the gain to 3.0-5.4%.
- B2 is development round 2, informed by B1.
- The comparator set omits faithful CAMS-style, SR/CUSUM and economic retraining baselines.
- No real-data result.

### F2 Propensity-matched bet cap (B1 to B2)

P3 gave 3.5% and P3b about 9-10% at the same validity (`FINAL_RESEARCH_REPORT.md`, `12_NOVELTY_DECISION.md`).
The lesson: a bet cap should use the issued query propensity, not the minimum propensity.

- Effect: Meaningful. Validity: same argued status as F1. Novelty: design lesson on known machinery.
- Practical value: anyone building IPW-gated e-processes with structural zeros.
- Caveat: shown in one generator family; B2 is a second round on the same family.

### F3 Persistence-aware promotion (P4)

NOT SUPPORTED. P4 gains 0.24-0.82% over P3 in W3 and loses 9.50-23.93% in W1 (`FINAL_RESEARCH_REPORT.md`,
lane B-Q2). The hazard is a declared plug-in. Graded negative; this remains a stop.

### F4 Calendar optimality under tight risk (Lane A)

Proved: Proposition 6 (support certificate) and Theorem 7 (chain reduction: promotion needs unanimous
evidence, so the optimum is a single chain of queries). Per-instance certificates
(`12_NOVELTY_DECISION.md`, A3 section):

| B | alpha | Cells | Result |
|---|---|---|---|
| 3 | 0.05 and 0.10 | 108 | All calendar-optimal |
| 4 | 0.05 | 54 | All calendar-optimal |
| 4 | 0.10 | 54 | Not certified; see F6 |

- Effect: the gap is exactly zero in certified cells. This is a simplification result.
- Practical value: a practitioner can use a fixed label-acquisition schedule with zero loss under tight
  false-promotion control. Joint planning adds nothing there.
- Novelty: plausibly new as a structural result in this setting. The literature audit is pending, so no
  novelty claim is made yet.
- Open: Conjecture 8 (model-level threshold). Limits: one HMM family class, B <= 4.

### F5 Risk-specific branch-conflict gap at intermediate alpha

Proven lower bounds on the mixture gap at T = 9 (`results/a1d/LOWER_BOUNDS.md`):

| prior1 | alpha | Proven lower bound | Unconstrained gap |
|---|---|---|---|
| 1/10 | 1/4 | 5.07% | 1.62% |
| 1/5 | 1/2 | 4.68% | 1.20% |

Upper values reach about 5.8% (prior1 1/10, alpha 1/2: [4.80%, 5.80%]). The gap grows with T to about 5.0% at
T = 12 (alpha 1/5), per the A1c summary in `12_NOVELTY_DECISION.md`. Mechanism: the promotion branch needs
confirmation slots, the non-promotion branch needs a delayed re-check, and the risk budget cannot cover both
(`13_A2_BRANCH_CONFLICT_THEORY.md`).

- Effect: Meaningful, and well above the unconstrained gap, so a real phenomenon.
- Validity: proved lower bounds for the listed instances. The general-family statement is descriptive, not proved.
- Novelty: plausibly new; audit pending.
- Limits: small models only (T <= 12), loose alpha (>= 3/20, above the programme's declared 0.05/0.10 levels).
  At prior1 = 3/10 the lower bound is weak and inconclusive at alpha 1/2. This is a theory finding, not a
  deployable method.

### F6 B=4, alpha=0.10 adaptive gap

Proven two-sided mixture gap of 0.71-1.21% over all calendar mixtures in the six largest-gap families (A3c).
Mechanism: promotion on 3 positive labels out of 4 breaks unanimity. Grade: Small. It is not risk-specific,
because the constrained gap is smaller than the unconstrained gap (2.71-5.56%).

### F7 Joint vs calendar at programme risk levels

A1 max relative gap 0.87% (288 cells); A2: exactly 0 in all 108 tight cells (alpha 0.05 and 0.10, 54
families each). Grade: Negligible. It is still informative: joint planning is not worth its cost at the
programme's risk levels, and the zero is not vacuous (every optimum is a contiguous confirmation burst, and
the constraint costs 1.12-1.84x; `12_NOVELTY_DECISION.md`). The A1 KILL is unchanged.

### F8 H2c

Source: `06_H2C_AND_HG_REPRODUCTION.md`, G5, 600 seeds, analysis-level reproduction VERIFIED.

| Budget | H2c power | Advantage vs better of local discounted Kelly / ONS | Implied baseline power | Relative gain |
|---|---|---|---|---|
| 10% labels | 0.382 | +0.086 [0.059, 0.113] | about 0.296 | about +29% |
| 20% labels | 0.640 | +0.094 [0.063, 0.125] | about 0.546 | about +17% |

The baseline and relative figures are derived here as H2c power minus the advantage. The comparator is chosen
per cell from realised means, so they are approximate.

- Effect: Meaningful to substantial in relative power. The absolute gain is +0.086 / +0.094.
- Validity: cost-null validity is DOC-ONLY (no unit test). Under AR rho = .98 Brier-null e-processes exceed
  alpha (up to .36).
- Novelty: composition; H2c reduces exactly to discounted Kelly with a substituted moment ratio (max abs
  dlogW 8.9e-16).
- Caveats: nominal cost known; fixed delay 5; one generator family; reverses on exposed Gas (242-824 events
  later than cost-only Kelly/ONS); unknown-nominal power about 0 for n_cal <= 1000; the empirically
  calibrated C7a is more powerful by 0.19 / 0.13 but has no guarantee; simulation only partly re-run.

### F9 HG

- Power: +0.029 [0.012, 0.046] and +0.052 [0.020, 0.090] over the PPRM parent (Holm p 0.004 and 0.003).
- Harm before alarm: 15% / 25% lower in harm worlds (raw -28.9 / -33.9). The earlier "~21/24" figure was
  a MISMATCH and is not used.
- Validity: predictable cap repair verified (18 tests). Invalid under dependence (FAR up to .23).
- Grade: Small to meaningful, and only against its own parent. It loses to Page-Hinkley / CUSUM
  (-0.066 / -0.110, not significant). It is a reference, not a win. CRSP RPOQ is exposed and negative.

### F10 Negative and diagnostic results with value

| Result | Why it is useful | Source |
|---|---|---|
| Dependence coupling bound, alpha + eps(1+(T-1)delta) | Necessary condition on power under dependence | `FINAL_RESEARCH_REPORT.md`, lane D |
| Calibration-size dominance | Unknown-nominal power about 0 for n_cal <= 1000; EB at n_cal = 50,000 gives .535/.850 vs .603/.902 known | `06_H2C_AND_HG_REPRODUCTION.md` |
| X1 guidance-alignment failure mode | Guidance helps +.03 to +.14 only when Brier co-shifts; loses up to .59 when flat or opposed | `06_H2C_AND_HG_REPRODUCTION.md` |
| Null-class accounting | Separates boundary null (valid) from marginal persistent-regime null (20.8%) | `11_ADVERSARIAL_REVIEW.md`, `12_NOVELTY_DECISION.md` |
| Corrected vacuous mixture lemma | Original A1d grid values were upper bounds only; two-sided bounds now exist | `13_A2_BRANCH_CONFLICT_THEORY.md`, `results/a1d/LOWER_BOUNDS.md` |

## 5. Revised overall assessment

**Revised classification: CONDITIONAL GO for a scoped paper. Not a new-algorithm headline.**

The previous classification, BENCHMARK / NEGATIVE-RESULT PIVOT, was too harsh. It let one 10% gate override a
verified, world-structured 7.7-10.2% saving, a proved structural result and a set of design lessons. It stays
on record as the registered-protocol classification.

Proposed paper: "Certify the challenger, not the alarm: budgeted, delayed, risk-controlled model switching."

| Part | Contributions | Role |
|---|---|---|
| Empirical, with guarantee | F1 + F2 | Certified switching vs alarm-triggered switching; propensity-matched caps; insurance profile |
| Structural theory | F4 + F5 (F6, F7 as scope) | Calendar optimality under tight risk; branch-conflict gap at intermediate alpha |
| Benchmark | F8 + F9 + F10 | H2c, HG and diagnostics as component benchmarks with explicit failure modes |

What the paper must not claim: that anytime-valid testing beats a well-designed batch paired test (not shown);
a marginal-null guarantee (20.8% false promotion); any real-data benefit; novelty of the components; or
value from joint acquisition and switching at the programme's risk levels.

### Gaps remaining before submission, ranked

| Rank | Gap | Why it matters | Notes |
|---|---|---|---|
| 1 | Real-data validation of F1 on a dataset with challenger headroom | All F1 evidence is from a stylised generator | Gas Sensor shows a 12.3% challenger gain but is exposed; an unexposed domain is needed |
| 2 | Faithful CAMS / Xu et al. baselines and a valid-threshold batch test baseline | The batch test matched P3b within 0-0.9 pp and its error control was not established | Without this, the case for the e-process over a batch test is open |
| 3 | A second, structurally distinct synthetic generator for F1, registered in advance | The weaker-signal variant cut the gain to 3.0-5.4%; one generator family so far | Register thresholds and worlds before running |
| 4 | Literature audit for F4 and F5 | Novelty of both structural results is unaudited | The CAMS audit file is also missing |
| 5 | Proof of Conjecture 8 (model-level threshold) | Would turn per-instance certificates into a general statement | F4 stands as per-instance without it |

Continue / pivot / stop: continue on gaps 1-3 as a gate for the F1 contribution. If gap 1 shows no headroom on
an unexposed dataset, or gap 2 shows a valid batch test matches P3b, fall back to the benchmark and theory
paper (F4, F5, F8-F10) and treat F1 as a design lesson.

## 6. Suitable venues (phrasing, no acceptance prediction)

- A venue or track on sequential decision-making, anytime-valid inference or e-processes, if gaps 1-3 are
  closed and F1 is presented as an empirical study with a conditional guarantee.
- A theory-oriented venue for F4 and F5 as structural results on risk-constrained sequential acquisition,
  once the literature audit and, ideally, Conjecture 8 are done.
- A datasets-and-benchmarks or reproducibility track for F8-F10 as a benchmark of monitoring components with
  documented failure modes.
- A workshop on distribution shift or ML monitoring is a reasonable first outlet for the combined scoped paper
  while the open gaps are being closed.

Venue fit depends on closing the ranked gaps. No statement here is a forecast.

## Update 2026-11-01: real-data validation (gap 1)

B3 (`16_REAL_DATA_RESULTS.md`) evaluated the frozen P3b on 7 chronological streams. Five of them
are unexposed. The registered outcome is **SUCCESS**:

- WIN on weather, spam and rialto, with 6–70% lower net cost than never switching;
- SAFE on all 7 streams;
- better than incumbent-alarm switching on all 7 (point estimates).

On streams where the challenger is worse, certified switching costs only +0.6–2.1%. Blind
deployment of the challenger costs +10.6–187% on the same streams.

This closes the real-data gap at the level of real data with imposed delays and costs. Two
caveats remain:

- Two of the three WIN streams have fewer than 5 episodes.
- Release timing is not drawn from real contracts.

The remaining gaps are 2–5 from section 5, plus a larger-episode replication of weather and
spam if longer streams become available.
