# Research red-team and second-pass refinement: loop control

**Started 2026-10-27.** This folder holds the red-team and refinement pass that the user requested
on 2026-10-27 (brief kept verbatim in `BRIEF.md`). Each 20-minute loop tick reads this file, does
the next unchecked step, updates the checklist and the tick log, and stops at an exit condition.
Historical audit files elsewhere in the repository are never overwritten.

## Standing constraints (from the brief, AGENTS.md and the user)

- **Read-only by default.** Do not rerun frozen evaluations, touch held-out data, launch sweeps,
  modify frozen protocols, or delete or relabel negative results. A rerun needs a written
  verification reason in the tick log first.
- **Prior decisions stand unless new evidence reverses them.** These are the 2026-10-26 decision
  gate (NO-GO on a new RIVE/ASC/unified algorithm) and the 2026-10-27 phase checkpoint B (NO-GO on
  a new Paper 1 monitoring algorithm; see `docs/phase_report_stratified_monitor.md` and
  `docs/algorithm_search_exit_ledger.md`). NEW_METHOD needs a concrete published-method limitation
  and a falsifiable mechanism.
- **Literature.** Primary sources through 2026-10-27. Never justify novelty from an abstract
  alone. Mark inaccessible papers as unverified.
- **Labels.** Mark every statement as one of: established theorem, plausible unproved theorem,
  engineering heuristic, or empirical hypothesis.
- **Git.** The user asked on 2026-10-27 that every update be committed and merged into `main`.
  After each tick's changes, commit on `research/phase-progress-2026-10-27` (end the message with
  the Co-Authored-By line), then fast-forward the local `main` with `git fetch . HEAD:main`, with
  no checkout. If that is not a fast-forward, stop and ask. Never push (not authorised). Keep
  licensed or raw data (CRSP, raw EIA) out of everything, including reviewer prompts.
- **Figures.** Use PaperBanana if a figure is needed; if it is unavailable, report that.

## Tooling status

| Item | Status |
|---|---|
| ARIS | Cloned at `~/aris_repo` (commit `18bceb3`, 2026-10-24). 16 skills copied to `~/.claude/skills`: research-lit, novelty-check, research-review, research-refine, research-refine-pipeline, experiment-plan, kill-argument, result-to-claim, proof-checker, citation-audit, experiment-audit, paper-claim-audit, arxiv, semantic-scholar, openalex, shared-references. Scanned for risky instructions before install. Skills installed mid-session may not load until a restart, so read `~/.claude/skills/<name>/SKILL.md` directly and follow it. |
| Codex reviewer (independent, cross-model) | Binary `~/.codex/plugins/.plugin-appserver/codex.exe` (codex-cli 0.163.0-alpha.10.2) is signed in. **Available again from 2026-10-27 (smoke test returned `REVIEWER_OK GPT-6`; the session header shows model `gpt-6.1-sol`).** An earlier usage limit blocked it until the user restored access. The ARIS MCP bridge (`~/aris_repo/mcp-servers/codex-exec/server.py`) is **not registered**: no `claude` CLI on PATH, and `python3` is the Store stub, so use `C:/Users/nigel/AppData/Local/Programs/Python/Python313/python.exe` and `CODEX_BIN=<binary above>`. Run reviews with `codex exec --sandbox read-only` (use `codex exec resume <session id>` to continue a review thread). If it fails, retry once, then run the Claude persona fallback below and record the review as **not independent**. |
| Persona fallback | Four Claude subagents (statistical theorist, prior-art specialist, empirical ML reviewer, skeptical PC member), each with fresh context. Label the output "same-family review, not an independent cross-model review". Queue a Codex re-review once access returns. |

## Checklist (one or more steps per tick)

- [x] A1 `REPOSITORY_STATE_AUDIT.md`: remotes, branch, ahead/behind, working tree, unpublished
      commits, file availability, test-suite status.
- [x] A2 `RESEARCH_EVIDENCE_INVENTORY.md`: methods with code locations; intended versus implemented
      assumptions; experiments, datasets, comparators, metrics, results and artifacts; positive,
      inconclusive and negative findings; reproduction, hash and seed status; leakage risks;
      unsupported claims; doc-versus-code conflicts. Fan out read-only Explore subagents by area
      (DIVE/monitoring, PPI/querying/sequential, Target-Scout/selection, shadow/promotion/rollback,
      synthetic, CRSP, EIA, Upworthy, ShiftGuard).
- [x] B1 `PRIOR_ART_AND_NOVELTY_MATRIX.md`, part 1: verify the existing bibliography
      (`docs/closest_prior_work.md`, `papers/shiftguard_unified/novelty_audit.md`, SOTA supplement).
- [x] B2 Part 2: fresh search through 2026-10-27 (ARIS research-lit and novelty-check;
      arXiv/OpenReview/PMLR). Fill the full column set and run the "two existing algorithms" test on
      each claim.
- [ ] C1 `COMPETING_RESEARCH_DIRECTIONS.md`: paths A–D (and others found), every assessment
      field, a ranking, and a minimal falsification experiment for each.
- [ ] D1 `REFINEMENT_ROUND_1.md`: proposal for the strongest surviving direction, following ARIS
      research-refine.
- [ ] E1 `ADVERSARIAL_REVIEW_1.md`: four perspectives; fatal and major weaknesses, remedies,
      required evidence.
- [ ] E2 `REFINEMENT_ROUND_2.md`: claim-by-claim response.
- [ ] E3 `ADVERSARIAL_REVIEW_2.md`: a full second review. Run rounds 3–5 only while they resolve
      significant objections, as `REFINEMENT_ROUND_n.md` / `ADVERSARIAL_REVIEW_n.md`.
- [ ] F1 `FINAL_RESEARCH_PROPOSAL.md`: decision BENCHMARK_PAPER, NEW_METHOD, PIVOT or NO_GO, plus
      the abandonment criterion.
- [ ] F2 `IMPLEMENTATION_READINESS_GATE.md`, `CLAIM_TO_EVIDENCE_MATRIX.md` and `handoff.json`
      (approved tasks, rejected approaches, unresolved blockers).
- [ ] F3 Final consistency check across all files. Stop the loop and report to the user.

## Exit conditions (stop the loop on any of these)

1. **Done.** F3 is complete.
2. **Converged.** A refinement round introduces no new evidence and resolves no significant
   objection. Go straight to F1.
3. **Blocked.** The next step needs something only the user can give: authorisation for a rerun,
   data access, a paid service, or a decision the brief leaves open. Record the blocker, stop, and
   ask.
4. **Stalled.** Two consecutive ticks make no checklist progress. Stop and report why.
5. **Budget.** 24 ticks (about 8 hours) without reaching F3. Stop and report status.

The loop must never extend itself past these conditions to polish wording or chase a reviewer
score.

## Tick log

| Tick | UTC | Steps done | Notes |
|---|---|---|---|
| 0 | 2026-10-27 | Setup | ARIS installed; Codex limit hit until 2026-11-02; cron job `1bdae48e` (`7-59/20 * * * *`; replaced `99821f78` to add the commit-and-merge rule) |
| 1 | 2026-10-27 | A1 drafted | No GitLab remote; 42 local commits unpublished; full pytest 1,869 passed, 1 skipped |
| 1b | 2026-10-27 | Tooling | Codex reviewer restored and smoke-tested (`REVIEWER_OK GPT-6`) |
| 2 | 2026-10-27 | A2 | Four Sonnet surveys plus lead synthesis and verification. Key: `q1_fallback` dominates integrated system on 3 profiles (undiscussed); no untouched real holdout; S2 seed-doc typo; 2 undisclosed seed overlaps; Target-Scout hash drift |
| 3 | 2026-10-28 | B1 | Three Sonnet clusters plus lead identity checks. Combination test: Q1, Q2 generic and Q3a all YES (reject). Narrow survivors: bandit-feedback paired harm, persistence-aware post-switch certificate, validity through intervention, finite-budget burst allocation theorem. Uncited: Drift2Act, Zhang-Wu-Qian 2609.13714, Zhou-Li-Zhu 2610.10393; DISCERN missing from manuscript. Ledger M8 wording overstated. RADAR identity needs user |
| 4 | 2026-10-28 | B2 | Full reads, G1-G4 search, PPRM resolved (no implementation error). **First independent review: Codex gpt-6.1-sol xhigh** (dossier `NOVELTY_DOSSIER_B2.md`). Verdicts: G4 PROCEED (only gap passing both tests), G2 narrow (prospective-certifiability theorem), G3 reject generic, G1 section only. No NO-GO reversal. RADAR identity confirmed by user. 9 Codex-added papers (2 lead-fetched) |
