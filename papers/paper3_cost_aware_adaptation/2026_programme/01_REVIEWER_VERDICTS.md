# 01 Reviewer verdicts

## Independence statement

Cross-model review: **UNAVAILABLE in this session.** `where codex` and `where gemini` found no executable; no cross-model reviewer MCP tool is exposed to this agent (the connector tools available are unrelated: Drive, Gmail, browser). A second reviewer from the same model family would not be independent. Therefore everything below is a **MANUAL_FALLBACK** review by a single agent (Claude Sonnet 5.5). **No ARIS review ran, and none is claimed.** Verdicts are advisory, unverified by any independent party.

## Reviewer 1 (adversarial, MANUAL_FALLBACK)

Scope: bounded prior-art audit. 18 sources were opened at the depth in `01_PRIOR_ART_MATRIX.md` (4 full PDFs extracted and skimmed for statements: Atan, Regol, Challenger, ATTA; plus Cheng, Reyzin, WISE-ATTA, Drift2Act, RAR, Gafni extracted; abstracts or snippets for the rest). Three triage sources are unretrieved or snippet-only (Goebel, Lopes, Liu). I did not read proofs.

| Candidate | Verdict | Confidence | Rationale |
|---|---|---|---|
| A joint QVOI / risk-envelope / dual / learned / reversal | **REJECT as a novelty/advantage paper** (retain A2 as baseline/ablation) | High on empirical headroom (repo data), medium on theory | Augmented-state (C)POMDP; Chick/Cheng/Atan/Drift2Act occupy components; repo planner gap 0.7-1.2% and calendar-optimality at tight risk. |
| B future payback certification | **WEAK-ACCEPT as a conditional theory target** | Low-medium | Different estimand from Drift2Act, Podkopaev-Ramdas; but internal envelope exists and variation-budget antecedents are unretrieved. Survives only with matching lower bound + optional-continuation counterexample. |
| C dependence-aware atlas | **REVISE (benchmark track only)** | Medium | Needs fidelity repair; occupied framing (Ahmed 2026, Cerqueira KDD'26). Venue fit depends on an isolated mechanism. |
| D cross-stream transfer | **REJECT unless LOFO beats per-domain tuning** | Medium | Meta-recommendation (Lopes), published LODO (Cerqueira), repo evidence that tuning ties mechanisms. |
| E dual-use labels | **PROMISING-BUT-UNVERIFIED; gate on a cheap counterexample test** | Low | Not found in retrieved sources; Challenger models part of it; prequential reuse may dissolve it. Highest conditional ceiling on label cost. |

### Specific objections to anticipate

1. "Joint label+compute+switch budgets" is a re-parameterisation unless a theorem or a separation instance depends on the joint structure.
2. Any improvement claim must be graded against tuned Wald and calendar baselines at equal tuning budget; the repo's accumulated ties make small gains non-credible without CIs.
3. Time-uniform validity must be stated against a filtration that includes pending queries; Lindon-Kallus show arm-specific event-time filtrations are needed and treatment-effect error is not a martingale under any filtration, a caution for any paired pending-label certificate.
4. Do not cite Liu (TPAMI 2026), Goebel, or Lopes for anything beyond bibliographic existence until text is retrieved.

### Process caveats

- Fetches used a page-summarising tool for several pages; statements are checked against summaries and extracted PDF text, not rendered PDFs.
- Only one search each for candidate E's label-reuse question and D's transfer question; absence of hits is weak evidence.
- Triage kill tests were used as the checklist but none was executed empirically here (no experiments were in scope).

## Recommended next independent review

When a Codex/Gemini backend or a human reviewer is available, give them: `01_NOVELTY_REJECTION_MEMOS.md`, the Candidate E counterexample test, and the three unretrieved sources.
