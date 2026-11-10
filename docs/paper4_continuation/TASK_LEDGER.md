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
