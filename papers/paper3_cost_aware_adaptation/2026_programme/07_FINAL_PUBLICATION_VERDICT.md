# Paper 3 — results summary, negative results, review audit and publication verdict

Date 2026-11-10. Branch `research/paper3-safe-budgeted-intervention-2026-11-09` (pushed).
This file serves as 05_RESULTS_SUMMARY, 05_NEGATIVE_RESULTS, 06_REVIEW_AUDIT and
07_FINAL_PUBLICATION_VERDICT; per-workstream detail is in A_RESULTS.md, 06_THEOREM_LEDGER.md,
06_PROOF_AUDIT_B.md, C_*.md, D_RESULTS.md, E_RESULTS.md, 05_CONFIRMATION_RESULTS.md.

## Verdict: `EMPIRICAL_BENCHMARK_CANDIDATE` (no method contribution; `NOT_NOVEL` for A–E as methods)

No candidate method (A0–A5, B2, C1/C3, D1–D4, E-split) has an attributable economic gain over the
strongest fairly tuned deployable comparator (discounted Wald/LCB switcher + late-label cutoff,
ported from Paper 1). The 2.5% stretch target was not reached by any method; the best was A0 at
+1.9% (worse) on confirmation. What survives is a set of **limits findings** that replicated on
unopened seeds under a registration locked before opening (2190f95f). They support a
benchmark/limits paper only after the gaps listed below are closed. No manuscript was drafted:
the evidence does not yet support one (G5 external validity and G6 paper-readiness are not met).

## Confirmed findings (registered, opened once; commit 480a669b)
| H | Finding | Statistic (95% CI) | Grade |
|---|---|---|---|
| H1 | Best joint VOI/belief planner (A0, tuned on 32 configs) does not beat tuned Wald+cutoff | ΔJ = +1.28 [+0.92, +1.62], +1.9% (worse); A1/A3/A5 +5.3–7.4% worse | small, adverse |
| H2 | Repeated-look recent-window payback hurdles certify the wrong sign on a flat null; the time-uniform B2 certificate does not | B0w .635 [.605,.664], B0b .857 [.834,.877], B0a .149; B2 .001 [.0002,.0056] at α=.1 | substantial (validity) |
| H3 | Alarm-metric ranking disagrees with deployment-cost ranking | inversion freq .514 [.448,.541]; τ(EDD,J) −.174 [−.198,−.132]; Spearman(dwell,τ)=+.91 | meaningful (synthetic only) |
| H4 | Prequential certification remains valid when the challenger is retrained on the same paid labels | FP .031 [.029,.033] (m=5), .030 (m=40) at α=.05 | validity confirmed (not novel) |
| H5 | Cross-family transfer recommender gives no meaningful gain on 4 sealed real streams | mean ΔJ −1.28 (−0.30%), 3/4 favourable | negligible (descriptive) |

Exact-oracle diagnostic (dev): with the true model, planning error of A0/A1/A3/A5 is ≤2.7% of the
exact DP optimum (T≤12, B≤3), so the economic headroom from smarter joint planning is small; the
gap to Wald is information, not planning.

## Negative results (all retained)
- **A** (dfda60a6): every joint controller worse than Wald+cutoff on dev; the A0 label saving
  (22.5 vs 38 labels) disappears at matched labels (+0.37 [−0.38, +1.04]). Gated planners exceed α
  under AR(1) ρ=.95 nulls (FP .47–.57). Classification: ALREADY_COVERED (constrained POMDP).
- **B** (f8f5d470, audit 1b8be025): T0–T5 proven/verified with fixable gaps (T1 clipping, T2/T3b
  assume known τ and unit variance; "2.4x tight" holds only at α=.05, β=.2 — 1.5–4.7x on a wider
  grid). T6–T8 unverified conjectures. Ingredients are standard (Le Cam, variation budget,
  confidence sequences); B2 certifies later and realises ~13% less net payback than B0 in-class.
- **C** (d3f8a4de): DISCERN ψ_E fix verified against Waudby-Smith & Ramdas; it changes no v2-subset
  outcome. Repairs C1/C3 give no gain over the strongest valid gate (C1 ≈ Markov skeleton; worse
  than Gated by +1.75). Inversions are **not** reproduced on 8 usable real streams (τ +.26, inversion
  .24), and `never_switch` was cheapest in every synthetic cell, which may inflate inversions.
- **D** (f3525867): learned recommenders lose to global-fixed and per-stream tuning on 33 real dev
  streams (+1.7 to +4.0 J); headroom of the best fixed setting over hindsight is ~1.1%; generic GRU
  +124 J; structured GRU ≈ Wald (undertrained, 46–91 updates).
- **E** (8d62545d): STOP — the promoted-version gap requires drift and affects holdout equally.

## Review audit (06_REVIEW_AUDIT; all MANUAL_FALLBACK)
- No cross-model reviewer was available (no codex/gemini CLI, no reviewer MCP). All reviews are
  same-family (Claude) and **not independent** in the cross-model sense. No ARIS command ran.
- Novelty review (01_*): read full PDFs for 10 sources; abstract-only for 5; snippet-only for
  Goebel and Lopes; Liu TPAMI unretrieved (occupancy claim unverified).
- Proof audit (06_PROOF_AUDIT_B.md): see B above.
- Result-to-claim: each claim above is traced to `results/confirm/h*_summary.json`; the PI session
  recomputed H1 ΔJ (69.504 − 68.226), H2 counts (635/1000, 857/1000) and H4 (1243/40000) from the
  raw summaries.
- Experiment audit checklist: no simulator truth in PolicyView (tested); request-time budget and
  pending reservation (tested, 40 random seeds); equal tuning budgets (32 configs) for A and
  baselines; disjoint seed blocks; sealed real group hash verified on opening. Open issues:
  ported comparators are adapters (DOCUMENTED_ADAPTER / IN_HOUSE_HEURISTIC), no native author code
  for Drift2Act, RAR, WISE-ATTA, DISCERN; all real streams except the sealed four were previously
  exposed by Papers 1/2.
- Citation audit: the novelty reviewer found and this branch fixed a wrong Chick et al. DOI in
  `docs/g1_deadline_aligned_acquisition_kill_v1.md` (ad5a6dab). references.bib not independently
  re-audited.
- Figures: PaperBanana is not installed; no research figures were produced. Numeric source tables
  are in `results/`.

## Fair assessment
The strongest defensible Paper 3 is a limits/benchmark paper: "under delayed paid feedback,
neither smarter joint planning nor cross-stream transfer beats a tuned confidence-bound switcher,
and common repeated-look payback hurdles are invalid while a time-uniform drift-class certificate
is valid but conservative." H2 is the strongest finding (large, validity-level, confirmed);
H1/H5 are confirmed null results with exact-oracle support. Weaknesses that block a submission:
(1) external validity — H2 and H3 are synthetic, and H3 did not replicate on real streams;
(2) comparators are adapters, not native code; (3) B's theory is standard and has open gaps;
(4) no figures. Continue / pivot / stop: **continue only as a benchmark paper**, contingent on
the real-data payback test in 07_NEXT_ACTIONS.md; stop all method searches in A, D and E.

## Addendum 2026-11-10: R1, real-stream payback test (registered 0e41146c, exploratory tier)
Decision per rule: **R1-INCONCLUSIVE**. 27 streams, 2,169 episodes, d=100, h=100, c_q=0.
B2 − B0x realised net payback per episode: B0a −1.70 [−3.51, −0.32]; B0w −2.74 [−5.17, −0.81];
B0b −1.16 [−3.75, +1.02]. The PI recomputed the three point estimates from `per_episode.csv`.

Interpretation (PI, not part of the registered decision): the direction is against the H2
anchor. On real streams the valid certificates (B1, B2) almost never certify (B2 in 0.08% of
episodes): at real effect sizes, with ±1 labels and d=100, they are vacuous, as 03B predicted
(non-vacuity needs L ≈ .45). The invalid hurdles act. B0w and B0b certify the wrong sign in
34% and 62% of their certifications. Even so, B0a and B0w earn more in total, because 5 streams
with a persistent challenger advantage (dc_311, sf_311, dallas_animal_shelter, boston_311,
nola_311) carry the gains; B0w and B0b are net negative on about 15 streams.

Consequence for the verdict: H2 remains a confirmed validity finding, but it does not translate
into a real-data economic advantage for the valid certificate. The limits paper therefore has no
practical anchor without a variance-adaptive (Bernstein/betting) certificate that is non-vacuous
at real effect sizes. That would be new method work, not a benchmark claim. Verdict stays
`EMPIRICAL_BENCHMARK_CANDIDATE`, with materially weaker standing; per the registered
consequence, fresh real data are required before any decision.

## Addendum 2: B3 variance-adaptive certificate (development; even-episode selection, odd evaluated once)
B3 is a one-sided predictable-plug-in empirical-Bernstein lower confidence sequence with drift
age penalty, a single sequence per episode, and validity as a PROOF_SKETCH (not audited).
- Synthetic: valid in every tested null (wrong-sign ≤ .007, Wilson upper ≤ .014 at α=.1;
  optional continuation peaks at .0395). It certifies more and sooner than B2 (drift class .83
  vs .77; sparse p=.45: .26 vs .003).
- Real c4 odd episodes (1,080; h=100; c_q=0): 3 certifications. B3−B0a −1.85 [−3.73, −0.40];
  B3−B0w −2.94 [−5.44, −0.89]; B3−B0b −1.25 [−3.97, +1.02]; B3−B2 +0.08 [0.00, 0.21]. The PI
  recomputed the point estimates from the CSVs.
- Diagnosis: the binding constraint is the declared drift slack, not the variance radius. The
  hurdle is k/h + v(d+(h−1)/2) = .03 + .002·149.5 = .329, while real stream mean advantages are
  −.04 to .24. This is Theorem T1 operating on real data. The streams' measured drift
  (.0008–.0036 per round) exceeds a declaration small enough (v=.0005) to make B3 competitive
  with B0b. With the real label delay d=100, valid future-payback certification under an honest
  drift class is therefore structurally vacuous on these streams.

Updated assessment: the variance-adaptive repair improves the valid branch but cannot reverse
R1. The defensible content of B is a limits result: invalid hurdles act and sometimes earn,
while valid ones cannot act at real delays and drifts. This is a negative/limits section, not
a method. Paper 3 overall remains `EMPIRICAL_BENCHMARK_CANDIDATE`, weak; no method contribution.
Recommended decision: stop new Paper 3 method work and archive. Alternatively, write the limits
paper only if a fresh real batch with shorter label delays becomes available, since shorter
delay is the one lever T1 says can make valid certification non-vacuous.
