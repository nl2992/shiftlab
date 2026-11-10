# Paper 4: certified approximate optimisation under full-history causal-null risk

Branch `research/paper4-antitone-frontier-2026-11-09`. Final status: **NO-GO — Prior art** (main-track
novelty). FCG-fast is retained as an exact certified solver. See `publication/PUBLICATION_DECISION.md`.

## Index

| Directive item | File |
|---|---|
| Ledger (§20) | `RESEARCH_LEDGER.md` |
| Prior-art matrix (§11) | `PRIOR_ART_MATRIX.md` |
| WP1 structural theorem audit | `theory/01_structural_theorem_audit.md` |
| WP2 symbolic verification (gate-limited) | `theory/02_symbolic_verification.md` |
| WP3 optimisation and certificates | `theory/03_optimization_and_certificates.md` |
| WP4 scaling and comparators | `experiments/04_scaling_and_comparators.md` |
| Protocols / results | `experiments/protocols/`, `experiments/results/` |
| Theorem status, contribution, reviewer objections, decision | `publication/` |
| Counterexample library (§13), items A–L incl. I | `tests/paper4/test_counterexample_library.py` (25 Paper 4 tests pass) |
| Code | `src/shiftlab/paper4/`, `scripts/paper4/`, `tests/paper4/` |
| Earlier Paper 4 closures | `../risk_preserving_approx/PAPER4_VALUE_SHIELD_DECISION_V1.md`, `../risk_preserving_approx/PAPER4_G1_NOVELTY_REDUCTION_V1.md` |

## Reconstructed failure record (directive §6)

Each status is taken from the candidate's own document in `../risk_preserving_approx/`.

| Directive item | Evidence | Why it failed |
|---|---|---|
| Belief gridding is expensive | `CANDIDATE_A1_COMPLEXITY_AUDIT_V1.md`: "do not implement the proposed denominator-grid planner" | Grid size grows with the denominators of the exact belief; complexity no-go |
| Posterior-only compression destroys risk information | `../switching_alt_belief_risk_alias_counterexample_v1.md` | Equal alternative posteriors can carry different causal-risk continuations |
| A universal exact null-response quotient can be exponential | `CANDIDATE_C_RESPONSE_QUOTIENT_LOWER_BOUND_V1.md` | `binom(T-2, q)` distinguishable transcripts. This bounds a universal quotient only, not every approximator |
| IID-relaxed belief DP did not compress the graph | `CANDIDATE_G_*`: "PROVED — STANDARD REDUCTION"; 4,867 belief states = 4,867 public histories | The hidden-root belief, pending queue and budget keep histories distinct |
| Scalarised Bellman DP missed its runtime target | `PRIOR_ART_EQUIVALENCE_AUDIT.md` (Candidate G): 60.80 s against a registered 29.01 s and the 58.01 s reference | No state compression, plus multiplier search overhead |
| Generic policy-column generation did not fix pricing | `CANDIDATE_B_POLICY_PRICING_AUDIT_V1.md`; `CANDIDATE_B_PRICING_STATE_COUNTEREXAMPLE_V1.md`: "a pricing DP cannot merge public learner" histories | The pricing subproblem needs the full public history state |
| Automaton pricing | `CANDIDATE_H_AUTOMATON_PRICING_AUDIT_V1.md`: compactness and novelty "NOT ESTABLISHED" | Exact but not compact |
| Finite-window CPOMDP | `CANDIDATE_A2_FINITE_WINDOW_CPOMDP_AUDIT_V1.md`: "no direct transfer to the full causal-null risk objective" | Filter stability does not control a full-history null |
| Rare-history safe pruning | `CANDIDATE_E_*`, `candidate_e_pruning_feasibility_v1.json`: max 5/122 columns removable | Too few rare histories; the envelope needs the full tree |
| Value-sensitive pruning (Paper 4 v1) | `PAPER4_VALUE_SHIELD_DECISION_V1.md`: 0 histories at δ ≤ 1/20 | The relaxation lower bound is loose (D ≥ 0.156) |
| Monotone promotion is economically restrictive | `../switching_monotone_class_separation_v1.md` | Under reversals the best monotone value is 0, against ≥ 19/200 unrestricted |
| Ordinary CPOMDP / OSPOSG representation is not novel | `CANDIDATE_D_*`, `../switching_lagrangian_posg_reduction_v1.md` | Standard reductions (Horák et al.) |
| Adaptive bet gate | `CANDIDATE_F_ADAPTIVE_BET_GATE_AUDIT_V1.md`: "exact safety lemma is an established" result | Established e-process safety |
| Antitone-frontier verifier (this directive) | `theory/01` §3; `../risk_preserving_approx/PAPER4_G1_NOVELTY_REDUCTION_V1.md` | Krale et al. prior art; the verifier is not the bottleneck |
| Frontier-cut generation (this directive) | `experiments/04` | Double-oracle prior art. Cuts never fire at T=10, and where they do fire (T ≤ 8) FCG is slower than the reference |

**Reading coverage, stated honestly.** `RESEARCH_BRIEF.md` (650 lines) and `WORKING_PLAN.md` (853 lines) were
consulted only through the decision and status sections of the candidate documents. They were not read
end-to-end.
