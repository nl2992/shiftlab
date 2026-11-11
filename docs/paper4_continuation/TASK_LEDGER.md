# Task ledger (append-only)

| Time (2026-11-10) | Branch @ commit | Task | Status | Evidence |
|---|---|---|---|---|
| start | research/paper4-antitone-frontier-2026-11-09 @ 8e9366a7 | Remote state reconstructed: local == origin | COMPLETE | `git rev-parse` output in session |
| start | @ 8e9366a7 | ARIS/HKUSTDial inventory: skills present; external reviewer backends unavailable | COMPLETE (BLOCKED reviewers recorded) | `RESEARCH_CONTRACT.md`, `BLOCKERS.md` |
| A1 | @ affd5077 | Reproduce tests + certificates: 25 tests pass; C1–C6 U/L/risk/rows regenerate identically | COMPLETE | `scratchpad/a1_recheck.py` output in session; `RESEARCH_CONTRACT.md` |
| meta | — | HKUSTDial vibe-research-workflow applied | COMPLETE | `VIBE_RESEARCH_WORKFLOW.md` |
| D1, D2 | — | Complexity-parameter and separation screens with bounded tests from saved splits | COMPLETE WITH NEGATIVE RESULT | `FALLBACK_SCREENS.md` |
| A2, A3/A4, B, C, E | — | Launched to subagents (Sonnet ×3, Opus ×2) | IN PROGRESS | — |
| A2 | — | Shared stochastic root-mixture helper, guard, regression (9 tests), caller audit; historical activations all 1 | COMPLETE (lead-verified) | `ENGINEERING_AUDIT.md` §A2; `tests/test_root_mixture.py` |
| errata | — | Lead's A2 spec misattributed the 280952/2779205 failure to the "C2 IID policy, activation 1/2". It is C2 FCG iteration 6 (`q = 10/13`). The IID policy at `q = 1/2` gives exactly 1/10 under the old helper. `docs/paper4/RESEARCH_LEDGER.md` CP5 says only "C2" and stays unedited | RECORDED | `tests/test_root_mixture.py` |
| A3 harness | — | Ablation harness + smoke test (12 tests pass incl. root mixture); R2 = R1 justified | COMPLETE (campaign pending a quiet CPU) | `ENGINEERING_AUDIT.md` §A3 |
| A4 | — | T10D1 exploratory: 33 non-IID cuts at T=10; F0 slower than R0 (14.2 s vs 10.8 s); exact costs equal | COMPLETE (exploratory) | `results/a4_feasibility_v1.json` |
| E (literature) | — | HKUSTDial deep-research method: Q1–Q4 notes with read-status per source; lead spot-checked arXiv:1512.03873 (exists, matches) | COMPLETE (first pass) | `LITERATURE_NOTES.md` |
| WP C | — | Safety-premium theory: Z1 (narrow zero-premium), C3 (closed-form positive family), C4 and C5 NO-GO; lead re-verified C3 at T=4,6 and CE-6 exactly | COMPLETE (proof review pending in WP G) | `CAUSAL_SAFETY_PREMIUM_THEORY.md`, `theory_C/` |
| idea-eval C | — | HKUSTDial idea-evaluator on safety-premium theory: Accept with Revisions (narrowness + novelty MAJOR; Lemma U is the gate) | COMPLETE | `IDEA_EVALUATION_C.md` |
| WP B | — | B1–B4 all closed for HMM alternatives; Theorem B1-S (static alternative, tree-free certified V*) PROVED, not novel; lead verified 5 static cells == reference V* exactly | COMPLETE WITH NEGATIVE RESULT | `IMPLICIT_LEARNER_OPTIMIZATION.md`, `theory_B/results/` |
| lint note | — | 2 ruff E741 (variable named `l`) in theory_B/b1_pricing.py:97 and b1_run.py:85 kept unfixed on purpose: editing would change the script sha256 recorded in b1_*.json result provenance | RECORDED | ruff output |
| WP G (C proofs) | — | Proof review of WP C; 2 decisive corrections lead-verified | COMPLETE | `CAUSAL_SAFETY_PREMIUM_REVIEW_CORRECTIONS.md` |
| WP C follow-up | — | Lemma U unproved (12,060-cell numerics); N1 exact B=1 formula, S1, Zc proved (agent); new counterexamples lead-verified | COMPLETE (gate NOT passed by proof) | `CAUSAL_SAFETY_PREMIUM_THEORY.md` § Follow-up; `theory_C/fu_*.json` |
| D3, D4 | — | D3 closed (prior art; tree-free LB is the open problem); D4 drafted, pending-asymmetry value test queued after A3 | D3 COMPLETE WITH NEGATIVE RESULT; D4 IN PROGRESS | `FALLBACK_SCREENS.md` |
| WP E (survivors) | — | Source-grounded novelty audit of surviving results: none proved+distinct at main-track level; best = Γ characterisation (UNRESOLVED / PARTIAL OVERLAP) | COMPLETE | `NOVELTY_AUDIT_SURVIVORS.md` |
| H (skeleton) | — | HKUSTDial tech-paper-template: 2 CRITICAL chain breaks (multi-label case unproved; contributions exceed B=1 methodology) → no main-track skeleton | COMPLETE | `PAPER_SKELETON_CHECK.md` |

## Corrections and theory_v2 continuation (appended 2026-11-10; rows above unchanged)

Corrections (from `theory_v2/ENGINEERING_COMPLETION.md` §E4):
- Commits for the rows above: meta/D1/D2 `b3e74c25`; A2 `a09683f9`; A3 harness + A4 `9c803de8`; literature `e7964dd8`;
  WP C `bf5a3c7d`; idea-eval C `870553e4`; WP B `ded27a0d`; lint note `76b9f744`; WP G `d30b3af0`; WP C follow-up
  `075a963d`; D3/D4 `ddd957c2`; WP E survivors `510aad8d`; H `b1215242`; A1 `affd5077`.
- Row "A2, A3/A4, B, C, E — IN PROGRESS" is SUPERSEDED by the later COMPLETE rows.
- A2: activations — LP candidates 1; e-process gate baselines 2/5 and 4/5 (deterministic). Root-mixture test file has
  11 tests, not 9. A1 evidence script (`a1_recheck.py`) was session scratch: not reproducible from the repo.
- A3 campaign: FINISHED (04:10 EST) in worktree `failure-atlas-v2-sota-195428`; read-only summary in
  `theory_v2/ENGINEERING_COMPLETION.md` (E2 addendum): no runtime gain attributable to FCG cut generation.
- D4 (pending-asymmetry value test) is no longer blocked by the campaign; carried over as an open fallback item.
- "WP E" names three different things across phases (literature; novelty survivors; theory_v2 engineering). In
  theory_v2 the letters follow the 2026-11-10 directive (A audit, B multi-label, C stochastic, D structure,
  E engineering, F prior art, G review, H publication).

| Task | Branch @ commit | Description | Status | Evidence |
|---|---|---|---|---|
| branch | `research/paper4-causal-premium-theory-2026-11-10` @ `a7a1673f` | theory_v2 continuation cut from `b1215242` | ACTIVE | `theory_v2/MASTER_PLAN.md` |
| v2-E | `18076429` | Root-mixture audit, ledger reconciliation, A3 read | COMPLETE | `theory_v2/ENGINEERING_COMPLETION.md` |
| v2-F | `447126a8`, `a40a2727` | Prior-art retrieval and novelty audit | COMPLETE | `PRIOR_ART_SOURCES.md`, `PRIOR_ART_AUDIT.md` |
| v2-A | `96dd637a` | Independent proof audit; C3′ falsified at T=2 → C3″ | COMPLETE | `THEOREM_PROOF_AUDIT.md` |
| v2-B | `6051f2b6`, `67d2d4ce` | S0 proved; Z2 falsified (incl. α ≤ 1/2); S+ open | COMPLETE | `MULTILABEL_ZERO_PREMIUM.md` |
| v2-G (S0) | `fe7d9a35` | S0 correctness review | COMPLETE | `REVIEW_S0.md` |
| v2-C | `df2ffcd6` | SP1 closed form (B=1, stochastic anti-persistent) | COMPLETE | `STOCHASTIC_POSITIVE_PREMIUM.md` |
| v2-D | `5be00d76` | Structural characterisation | COMPLETE | `STRUCTURAL_CHARACTERIZATION.md` |
| v2-G | `f29f8f8b`, `0d0427b2`, `813e7b1b` | Significance, SP1 correctness, consolidated report | COMPLETE | `REVIEW_*.md` |
| rule | `2e32258f` (branch), `a2bf3b21` (main) | Publication-outcome rule in `AGENTS.md` | COMPLETE | `AGENTS.md` |
| v2-C2 | — | Relative-premium scaling run (descriptive), 3 workers | IN PROGRESS | `scripts/paper4_continuation/theory_v2/wpC2_relative_premium.py` |
| v2-H | — | Publication decision | PENDING (after scaling) | `theory_v2/PUBLICATION_DECISION.md` |
