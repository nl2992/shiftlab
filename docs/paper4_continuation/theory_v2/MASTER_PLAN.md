# Paper 4 theory_v2 — master plan (causal-safety premium Γ)

**Started:** 2026-11-10. **Branch:** `research/paper4-causal-premium-theory-2026-11-10`, cut from
`origin/research/paper4-antitone-frontier-2026-11-09` at `b1215242` (the directive's snapshot `76b9f744` is 5 commits
older; WP C follow-up, WP G review, WP D/E/H commits were already on the branch and are taken as the starting state).
**Lead:** Opus 5.5 (plans, verifies). Builders: Sonnet subagents. Reviewers: fresh-context native subagents —
`review_independence: same-family`, `acceptance_status: provisional` (BL-1: no cross-family backend loaded).

## Reconciled starting state (from `THEOREM_REGISTRY.md`, `CAUSAL_SAFETY_PREMIUM_THEORY.md`, review corrections)

| Result | Status at start |
|---|---|
| Lemma R (monotone Lagrangian minimisers for all λ ⇒ Γ=0) | PROVED; reviewed once (WP G, same-family) |
| Z1 / condition W (B=1) | PROVED; restated via W after review |
| C3′ corrected: Γ = α·min{(g−k)/2−c, g−2k} | CORRECTED; numerically verified |
| N1 exact Γ for B=1, any HMM, α≤1/2 | PROVED (agent); 2,000/2,000 cells; **not yet independently reviewed** |
| S1 static ⇒ Γ=0 (B=1) | PROVED (agent); not yet reviewed |
| Zc query-order coupling; Lemma P | PROVED (agent); not yet reviewed |
| Lemma U / U-M (TP2 + M_marg ⇒ Γ=0, any B) | CONJECTURED; 12,060 cells, no counterexample |
| Static any B; symmetric stationary persistent any B | CONJECTURED; no counterexample |
| Falsified | TP2+MLR⇒Γ=0 (B=1: 39/32000; B=2: 9/50000); symmetric kernels without stationary prior (Γ≈0.00216) |

## Work packages and owners

| WP | Task | Owner | Output |
|---|---|---|---|
| A | Independent proof audit + red team of R, Z1/W, S1, N1, Zc, P, C3′ | fresh Opus auditor | `THEOREM_PROOF_AUDIT.md` |
| B | Lemma U programme: U1/U2/U3 separated; static and symmetric-stationary proofs; targeted falsification | Opus theory agent; Sonnet builder for search | `MULTILABEL_ZERO_PREMIUM.md` |
| C | Stochastic anti-persistent positive premium (open region, lower bound, T/d/mixing behaviour, B≥2) | Opus theory agent | `STOCHASTIC_POSITIVE_PREMIUM.md` |
| D | Common structural quantity linking zero and positive premium | lead | `STRUCTURAL_CHARACTERIZATION.md` |
| E | Root-mixture recheck; A3 campaign results (run by the other session, not rerun here); ledger reconciliation | Sonnet auditor + lead | `ENGINEERING_COMPLETION.md` |
| F | Prior art (HKUSTDial deep-research + ARIS novelty-check protocol) | Sonnet retrieval, Opus novelty reviewer | `PRIOR_ART_AUDIT.md` |
| G | Three reviews: correctness, novelty, significance | fresh Opus reviewers | `REVIEW_REPORT.md` |
| H | Publication decision; manuscript only if warranted | lead | `PUBLICATION_DECISION.md` |

## Compute rule

The other session's A3 runtime campaign (`ablation_campaign.py`, worktree `failure-atlas-v2-sota-195428`) requires a
quiet CPU. Until it finishes, agents run at most one short exact-solver process each; heavy falsification sweeps are
queued and start after it ends. The campaign is not rerun here.

## Stop rules (per candidate, from the directive §13)

A candidate closes when falsified, found in prior art, too restrictive, built on a wrong information structure, a
routine corollary, or after a bounded targeted programme with the remaining obligation stated. Closing a candidate does
not close the programme.
