# Novelty dossier for the cross-model reviewer (B2, 2026-10-28)

You are an independent reviewer (a different model family from the author). Read this file, and
optionally the files it cites, which are in this repository. **Do not edit any file.** Return your
verdict as plain text in the format at the end.

## Context

The ShiftLab programme studies decision harm under distribution shift: paired decision loss of a
deployed policy against a reference policy, `R_t(pi_t) - R_t(pi_ref)`. Two prior project decisions
stand:
- NO-GO on a unified monitor/certify/intervene algorithm (2026-10-26);
- NO-GO on a new Paper 1 monitoring algorithm (2026-10-27).

The second rests on disagreement gating (DISCERN) plus published betting engines reproducing the
project's best monitor. Every broad framing (detection, promotion, costed intervention) fails the
test "could a knowledgeable reviewer obtain this by combining two existing algorithms?" (see
`docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` §1). Four narrow candidate gaps
remain. Judge each.

## Candidate gaps and the closest prior art found (verification level in brackets)

**G1. Anytime-valid monitoring of paired policy harm when only the deployed action's outcome is
observed (bandit feedback), with a harm margin and delayed or selective feedback.**
- Waudby-Smith et al., arXiv 2210.10768, §3.3 Prop. 4 [primary PDF read]: an e-process for the
  paired policy-value difference from logged data with importance weights. Adaptive logging is
  allowed; it tests a running-average weak null; overlap is required.
- Karampatziakis et al. ICML 2021 (off-policy CS, gated deployment) [partial].
- Zheng–Wiberg–Zhu arXiv 2608.29465 (incumbent decision regret under shift; asymptotic)
  [abstract].
- DISCERN, Timans (UAI 2025), PPE and Xu all assume the label identifies both actions' losses.
- Note: with a deterministic deployed policy, the reference counterfactual is not identifiable
  without randomisation.

**G2. A finite-sample or anytime-valid certificate on the future net benefit of a selected
replacement over a post-switch horizon, net of switching cost, when the improvement need not
persist, under delayed or adaptive feedback.**
- Chandak et al. NeurIPS 2020 (safe policy improvement for non-stationary MDPs; forecasted
  performance under a smooth trend; asymptotic coverage) [theorem statements].
- Liu et al. 2023 (asymptotic CI for future policy value) [theorem statements].
- Zhang–Wu–Qian arXiv 2609.13714 (paired fixed-n slice-wise non-regression with incumbent
  fallback; no anytime validity or drift) [full main text].
- Zhou–Li–Zhu arXiv 2610.10393 (offline schedule under an expected-unsafe-update budget;
  plug-in or i.i.d. trajectories) [partial-high].
- Digalakis et al. arXiv 2512.18390 (switching cost, trending gains; regret, not a certificate)
  [abstract].
- DISCERN §5.7: under drift there is no fixed Δ to certify; it certifies a traffic-weighted
  average [lead-verified].

**G3. Validity of sequential evidence through the intervention it triggers: a monitor triggers a
retrain or switch, which changes the deployed policy and possibly the data stream.**
- DISCERN Prop. 13: an unbounded promotion sequence from one error budget, but under an i.i.d.
  stream independent of the deployed model [full].
- Drift2Act arXiv 2603.08578: per-window Hoeffding plus union-bound certificates under uniform
  audit sampling; design-based; silent on post-intervention risk; heuristic action choice
  [partial-high].
- Csillag et al. ICML 2025 and Cook et al. (predictable adaptation) [abstract].
- E-detector restart accounting (arXiv 2607.28322, 2608.12660) [abstract].
- Han & Qu arXiv 2608.30502 (empirical closed-loop failures) [abstract].

**G4. A minimax or regret theorem for allocating a hard, finite label budget over time to a gated
anytime-valid monitor when informative (disagreement) events arrive in unknown bursts.** The
trade-off is reserve exhaustion against inflation of the importance-weight bound. Empirical
motivation from the project: a past-paced pacer lost to fixed gating under bursts, in both
synthetic and EIA data.
- Bayraktar–Kravitz (finite observation rights; Bayesian; no bursts) [abstract or statements].
- Cheng et al. arXiv 2609.29140 (hard-budget minimax for repeated evaluation with disagreement
  certificates; static) [lead-fetched abstract].
- Xu et al. active betting (regret on an expected budget; stationary).
- Banerjee–Veeravalli DE-CuSum (known likelihoods, rate constraint).
- Non-stationary bandits-with-knapsacks (NeurIPS 2022; rewards, not inference).
- Sfyraki & Wang ICLR 2026 (uniform querying near-optimal when stationary).
- The project's own related screen (M4, an evidence-driven observation controller) failed against
  an onset-informed temporal baseline.

## Questions

For each of G1–G4:
1. Is the gap real? If a specific published paper or preprint already contains the result, name
   it.
2. Apply the project's stricter test: could a knowledgeable reviewer obtain essentially the same
   result by combining two existing algorithms without a substantive new insight? Name the two.
3. Is a theorem plausibly provable under reasonable assumptions? State the key assumption that
   would make or break it.
4. What is the single most damaging reviewer objection?
5. Is it important enough to anchor an ICML/NeurIPS paper, or only a section of a benchmark
   paper?

Then: rank G1–G4, and say whether any of them should reverse the existing NO-GO decisions.

=== NOVELTY VERDICT LIMITS (these bound how you judge, never how widely you search) ===
Search exhaustively; judge calibrated. Two failures waste months equally:
passing an idea a published paper already contains, and killing a viable idea
because the territory has neighbors.
1. Proximity is information, not a verdict. Someone working nearby goes in the
   report; it is not by itself a reason to reject.
2. ABANDON has exactly one qualification: a specific published paper already
   contains this result — name that paper. No named paper, no ABANDON.
3. Crowded-but-deltaed is PROCEED: state the delta in one sentence a reviewer
   could verify. Thin or contested delta is PROCEED WITH CAUTION — say what
   would make it carry, not why it should die. CAUTION is not a safe middle:
   if you cannot name the specific thing that makes the delta thin, the
   verdict is PROCEED.
4. Concurrent or competing work is not a veto. That is a race — report it and
   let the user decide whether to run it.
5. A direct attack on a central problem is legitimate novelty when nobody has
   executed it well. "This area is hot" does not mean "this area is taken."
6. This check is an early gate, never the last one — more triage, pilots, or
   external review still stand between any idea and a paper, whatever order
   this run uses. A wrongly passed idea dies cheaply at one of them; a wrongly
   killed idea is never seen again. When torn between two verdicts, choose the
   more permissive one.
Say plainly when an idea clears the check. Do not manufacture overlap.

The project additionally requires: if the "two existing algorithms" test (Q2) answers yes, the
novelty claim must be rejected or narrowed, even when the ARIS verdict would be PROCEED. Report
both verdicts.

## Output format

For each gap: `ARIS verdict (PROCEED / PROCEED WITH CAUTION / ABANDON + named paper)`,
`Two-algorithm test (yes/no + the two)`, `Provability (key assumption)`, `Worst objection`,
`Paper-anchor or section`. Then the ranking, a NO-GO reversal yes/no, and any prior art you know
that is missing from this dossier (with full citation and your confidence).
