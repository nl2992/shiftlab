# WP-G — Review report (theory_v2)

All reviews are fresh-context native Opus 5.5 subagents: `review_independence: same-family`,
`acceptance_status: provisional`. No cross-family reviewer was available (BL-1: no Codex/Grok/Antigravity/
claude-review backend loaded). No external reviewer identities are claimed. A review does not replace a proof.

| Reviewer | Responsibility | Scope | File | Verdict |
|---|---|---|---|---|
| A (WP-A auditor) | Correctness + red team | Lemma R/R′, Zc, P, Z1/W, N1, S1, C3 | `THEOREM_PROOF_AUDIT.md` | All proofs survive; C3′ FALSIFIED at T=2 → C3″; odd-T alternation Γ=0 PROVED; N1 needs α ≤ 1/2 (necessary) |
| R1a | Correctness | Theorem S0 | `REVIEW_S0.md` | PROVED with minor corrections (post-promotion queries also greedy; "any c" remark not established) |
| R1b | Correctness | Theorem SP1 and corollaries | `REVIEW_SP1.md` | SP1 ACCEPTED (2,420/2,420 adversarial certified cells); SP1-D bullet wrong at T=d+1 (CE-18); d-monotonicity fails at small T (CE-19); minor text errors |
| R2 | Novelty (reduce to literature) | all results | `PRIOR_ART_AUDIT.md` | No result is a main-track-level new theorem: zero side = sequential stochastic domination (Doerr §1.8) + LP duality (Walraven–Spaan); B=1 results = single-observation composite tests + an LP over query times; Γ definition an instance of Fauß–Zoubir–Poor rectangular laws; S0's G/D induction the only untraced step |
| R3 | Significance (skeptical ML reviewer; HKUSTDial idea-evaluator; ARIS research-review rubric) | whole package | `REVIEW_SIGNIFICANCE.md` | Main track NO-GO (too restrictive / routine corollary), 3/10 as is, 5–6/10 best realistic; workshop/short note CONDITIONAL GO |

## Major objections and disposition

| Objection | Source | Disposition |
|---|---|---|
| Exact results only at B = 1, where the null has one lever per query time; adaptivity is real only at B ≥ 2 | R2, R3 | **Accepted.** No B ≥ 2 theorem outside static + free labels (S0). Recorded as the decisive limitation |
| Premiums are tiny in absolute terms | R3 | **Partly addressed:** B=1 ceiling Γ ≤ (C₀ − V*_IID)/2 proved (lead-verified); relative-premium scaling measured descriptively (`RELATIVE_PREMIUM_SCALING.md`) |
| Anti-persistence with odd release lag lacks practical motivation | R3 | **Accepted** as a limitation; SP1 is a mechanism theorem, not an application claim |
| Zero-premium side is classical stochastic domination | R2 | **Accepted.** Lemma R/R′/Zc reclassified as supporting mathematics (PRIOR ART in substance) |
| Γ > 0 contrasts with zero asymptotic exponent gap for adaptive adversaries (Modak et al., read via summaries) | R2 | Recorded as context: Γ > 0 is a finite-horizon effect; not verified from the primary text |
| All evidence synthetic, T ≤ 10 | R3 | **Accepted**; the package makes no empirical claim |

## Skills actually used in this continuation

- ARIS: `proof-checker` method (obligation ledger, taxonomy, red team) in WP-A, R1a, R1b; `novelty-check` protocol in
  R2; `research-review` rubric in R3. Their Codex reviewer slots were BLOCKED (BL-1); native subagents substituted.
- HKUSTDial: `deep-research` (WP-F retrieval and R2), `idea-evaluator` (R3).
- Not run in this continuation: `tech-paper-template` and `pre-submission-reviewer` (no main-track paper candidate
  survived, see `PUBLICATION_DECISION.md`; the earlier `PAPER_SKELETON_CHECK.md` already recorded 2 CRITICAL breaks);
  `vibe-research-workflow` was applied in the earlier phase (`VIBE_RESEARCH_WORKFLOW.md`) and the same lead-plans /
  builders-build / fresh-reviewers-check structure was followed here.
