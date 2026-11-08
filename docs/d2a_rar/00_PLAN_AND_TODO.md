# Drift2Act / RAR SOTA-first autoresearch programme — plan and TODO

Branch `research/drift2act-rar-autoresearch-2026-11-07`, worktree `ICML/shiftlab-d2a-rar-2026-11-07`,
cut from `main@7354480a` on 2026-11-07. Full brief: the user's "SOTA-First Autonomous Methods
Research" mandate (copied verbatim to `docs/d2a_rar/MANDATE.md`).

Central question: can a justified modification to Drift2Act, RAR or another strong existing controller
achieve better statistically valid deployment decisions by exploiting actual observation gaps, the
economic value of delayed labels, or interactions between evidence and acquisition?

Exit states: `METHODS_CANDIDATE` / `BENCHMARK_ONLY` / `NEGATIVE_RESULT`. Prior ShiftLab (GAVE-R,
Atlas) findings are development knowledge, not confirmation.

## Operating rules

- Routing: Sonnet subagents do coding, reproduction, experiment running and write-ups; Haiku for
  lookups/greps; the Opus main session plans, verifies and decides. Opus re-checks every subagent
  claim against code and result files before ticking a box.
- HKUSTDial Supervisor-Skills guide doubtful decisions: `idea-evaluator` (candidate triage),
  `deep-research` (prior art), `benchmark-paper-template` / `tech-paper-template` (deciding methods
  vs benchmark framing), `paper-writer` (write-ups). Also `novelty-check`, `experiment-audit`,
  `result-to-claim` before any claim.
- Subagents do not commit; the coordinator commits after verification. No pushes without the user.
- Python: main checkout `.venv/Scripts/python.exe` with `PYTHONPATH=<this worktree>/src`.
- Long compute (> ~10 min) runs detached (Start-Process) with checkpoints on disk; status files in
  `docs/d2a_rar/status/`.
- Missing comparator? `git grep` all refs (incl. `origin/codex/*`, `research/continuation-2026-11-04`
  which has a Drift2Act reproduction audit) and port with a source-commit citation.
- Null discipline: every method has an entry in `registry/null_assumptions.yaml`; never score a
  conditional-null method on marginal-null false promotions.
- Grading: fair-evaluation standard (substantial >= 10%, meaningful 3-10% CI excl. 0, small 1-3%).
  Acceptance: mild novelty + beats strongest applicable SOTA on a shared failure, valid, ablated,
  not worse nearby, independently confirmed.

## Work packages

- [x] WP0 Failure ledger + null-assumption registry + `FAILURE_ATLAS_CORRECTED.md` (agent: ledger)
- [x] WP1a Drift2Act PAPER_RECONSTRUCTION + 40-ep synthetic repro + contract port (b31ff5e1). Paper V~0 NOT reproduced; Camelyon/DomainNet not run
- [x] WP1b RAR PAPER_RECONSTRUCTION + ELEC2/semi-synth repro + RAR/Binary/CostAwareBinary contract ports (af7a0494). Win windows ~12x narrower than paper
- [x] WP1c SOTA registry for C-F + WATCH/PPRM; implement Challenger GSE/OSE/LSE (agent: sota)
- [x] WP2 `BENCHMARK_CONTRACT.md` + common event-driven simulator with leakage/budget/cost tests (agent: sim)
- [x] WP1d Gong-Zhang paid-observation, ASI, Sethi Markov test comparators (after WP1c)
- [x] WP4 Prior-art ledger (first pass; verified structure; gaps: no GitHub code search, no OpenReview, Drift2Act App D.7 unread)
- [x] WP5 Candidate grammar + CANDIDATE_REGISTRY (1,957 ids) + AUTORESEARCH_PROGRAM.md + ledger + preflight (73e8438e)
- [ ] WP6 Stage A preflight + Stage B 300 s screens (initial 200) -> checkpoint review
- [ ] WP6c Stage C medium validation (<= 20) -> Pareto/ablation report
- [ ] WP7 Confirmation protocol registered BEFORE holdout -> <= 3 finalists -> confirmation results
- [ ] WP8 `METHODS_PAPER_DECISION.md`

Dependencies: WP5 after WP0+WP1a/b+WP2; WP6 after WP5; Q3 factorial only after a Q1 and a Q2 winner.

## Progress log

- 2026-11-07: branch + worktree created; WP0, WP1a, WP1b, WP1c, WP2 launched as Sonnet subagents.
- 2026-11-07: WP4 first pass landed (10 families; most room: pending/deadline-aware querying, RAR Gate-2, canary exposure). WP2 verified (33 tests); WP2b sent (retrospective queries, canary split, retrain-window loss, seed registry).
- 2026-11-07: WP1c committed 6f0e6d88 (Challenger 12 tests; Lending Club not reproduced). WP2+WP2b committed 7a9743c4 (55 tests). WP1d relaunched paper-only (auto-mode blocked cloning/executing author repos); WP1e in-repo ports launched.
- 2026-11-07: WP0 committed (49 ledger rows, 29 null entries, 13 P2 null-mismatched measurements; 57 UNVERIFIED fields to be filled by baseline agents; HGxH2c FINAL_REPORT and Lane A docs not yet mined).
- 2026-11-07: WP1e committed a7fcc291 (33 in-repo adapters, 22 regression tests incl. bit-for-bit). Open: H2c/HG/PPRM need proxy predictions + source calibration in ObservableState (WP2c, do with Drift2Act sensing port); original E_rb + RMM restart wrapper not ported.
- 2026-11-07: WP1d committed 1a32f1a2 (Sethi/ASI/Gong-Zhang PAPER_RECONSTRUCTION, 36 tests; no author code read or run). Caveats: Gong-Zhang Alg2 printed eta form appears inconsistent with Thm 3.2 on one instance (both forms kept via eta_form); Table-2 repro 3004.8 vs 2899.75 with guessed generator; ASI streaming cond-null evidence is our derivation (MC-checked only).
- 2026-11-07 (resume run, ~06:50): WP1a/WP1b detached runs had finished (Drift2Act 8x5 episodes; RAR 3 streams x 4 seeds); docs + code were uncommitted, code untracked. Opus ran tests (151 pass after fixing RMM verbatim test to compare ASTs — port had been auto-formatted). Commit blocked by ruff hook (93 lint errors, plus a real syntax error and a NameError in drift2act/aggregate.py). Relaunched Sonnet finishers: WP1a-finish and WP1b-finish (lint, repro write-ups, COMMON_CONTRACT_PORT adapters in new adapters_drift2act.py / adapters_rar.py); WP5 launched in parallel (grammar, registry, ledger, preflight, AUTORESEARCH_PROGRAM.md).
- 2026-11-07: WP1a committed b31ff5e1, WP1b committed af7a0494 (Opus re-derived headline tables from result json: exact match; 165 tests pass). Key facts for WP5/6: (i) Drift2Act certificate at tau=0.2 needs ~370 in-window labels, gate open 30% of steps, controller abstains ~99% -> certification latency is a live failure mode on the host; (ii) RAR fixed gates suppress retrains — Rollback-Only and Cost-Aware Binary beat Full RAR everywhere measured, so any RAR-host candidate must beat Cost-Aware Binary, not just RAR. Contract-port caveats: no corruption channel (R2/hard hold unmapped), constants untuned, smoke-tested only.
- 2026-11-07: WP5 committed 73e8438e (Opus verified: 29 tests, deterministic rebuild --check OK, 1,957 unique ids, batch 200 = Q1 42 / Q2 158; preflight with real adapters: 171 ELIGIBLE, 27 BLOCKED_HOOK_MISSING, 2 BLOCKED_HOST_NOT_PORTED). Review note: 83/200 batch slots are HIGH_OVERLAP/KNOWN baseline-or-ablation arms — revisit weighting at the 200-checkpoint. Dev-suite gaps (reversal, hazard, subgroup, tight-deadline, proxy streams) listed in DEV_SUITE.json TODO. WP6 Stage-B runner + tranche 1 launched (Sonnet; detached run with status in status/wp6_stage_b.md).
- 2026-11-07 ~08:00: WP6 Stage-B tranche 1 complete (Opus verified ledger hash chain: 60 records = 3 smoke + 57; DISCARD 15, DUPLICATE 40, UNVERIFIED 5, KEEP 0, CRASH/INVALID 0; 17 stage_b tests pass). Coverage: of the 200 batch, 61 implemented, 29 blocked (27 hook missing, 2 Challenger not ported), 110 not implemented (all 39 Q1 evidence identities: d2a.evidence_log_lik sees only monitor proxies, not label-chain outcomes).
  CHECKPOINT FINDINGS (Opus): (1) Most Drift2Act/RAR hooked variants are INERT on the dev suite (ΔJ vs host = 0: delays << horizon so feasibility/deadline gates never fire; RAR gates never reached under the 50-label cap) — 30 of 40 DUPLICATEs collapse onto two host-identical behaviours. These are NOT evidence against the mechanisms; the dev suite does not exercise them. (2) The ported hosts are dominated by simple controls (Drift2Act port J ~645 vs episode_front/uniform_query ~300-510), so "beat strongest comparator" is unreachable from these hosts as ported — a strawman-host risk, not a candidate result. (3) Contract-native promotion/replacement candidates beat their host by 23-275 J but lose to uniform_query: genuine NEGATIVE vs simple control at screen scale. (4) Drift2Act host violates its abs-risk certificate on 13/80 seed-cells (0.1625; pooled-window variant is heuristic, as documented in DRIFT2ACT.md §2).
  NEXT (before tranche 2, do not just run more identities): (a) host-port calibration audit — why does each port lose to uniform_query; fix porting errors only (frozen constants from the paper where stated), preregister the calibrated host before any candidate rerun; (b) add dev-suite cells that exercise the hooks (delay tail comparable to horizon / tight deadline, label cap large enough for RAR Gate-2, reversal, hazard) — add as NEW cells, keep the frozen ones; (c) expose missing seams (d2a.action_selector, d2a.rollback_schedule, rar.rollback_rule) and a label-outcome Q1 evidence hook; (d) re-weight batch away from HIGH_OVERLAP arms. Mandate Q2 stop rule: if, after (a)-(b), Q2 candidates still only match a pending cap/fixed schedule, record NEGATIVE for Q2.
- 2026-11-07 ~09:00: Host-port calibration audit done (status/wp6_host_audit.md; Opus re-derived Q1[2] dJ vs uniform_query from results/d2a_rar/host_audit/frozen_cell.json: d2a_cal +327.4, rar_cal +326.7, J 637.5 — match; rad(50,0.05)=0.336 checked by hand; 228 tests pass). 3 porting errors fixed as opt-in profile calibrated_v1 (native_v0 default bit-identical, golden tests): Drift2Act audit pacing + T/1500 scaling; RAR/CAB/Binary paced label policy. Hosts STILL lose to uniform_query/fixed_schedule/pending_cap on 8/8 frozen cells — causes are method x contract (D): at a 5% label rate Drift2Act's certificate can never open (rad(50)=0.336 vs tau=0.5) and ADWIN never fires on RAR/CAB/Binary. This is a legitimate BENCHMARK finding (SOTA hosts dominated by simple controls under a tight-label contract), not a candidate result.
  DEV_SUITE_v2 (15 cells: tight deadline, RAR label-rich, certifiable risk, reversal, hazard; each with alt + correct null + neighbouring control) shows the inert hooks are reached there. Caveat: naive GainSwitch controls false-promote on large-cap null cells, so never_switch must be a v2 comparator.
  DECISION (Opus): v2 becomes the Stage-B tranche-2 suite, used ALONGSIDE the frozen v1 suite (v1 results stand). Before tranche 2: (1) preregister v2 + calibrated_v1 hosts + comparator set (add never_switch) in AUTORESEARCH_PROGRAM.md §3 amendment; (2) wire per-cell T / label cap / cost vector + host profile into stage_b.py; (3) re-run only identities that were inert (DUPLICATE-of-host) or UNVERIFIED for lack of a family; (4) Q1 evidence hook still missing. Framing note: the mounting evidence (dominated hosts; inert mechanisms at realistic label rates) points toward BENCHMARK_ONLY as a plausible exit; evaluate with benchmark-paper-template at the 200-checkpoint, not now.
- 2026-11-07 ~15:50: Resumed after limit. Registered amendment A1 (1cbadd17): DEV_SUITE_v2 alongside v1, calibrated_v1 hosts, comparator set incl. never_switch + Gap-Mix exact0.8_s4 + gap-10 thinned gate, tranche-2 scope <=140. Launched (Sonnet) tranche-2 wiring+detached run, and Q1 label-outcome evidence seam (no Stage-B runs until an A1 scope-(iii) line names the hook commit). Note: auto mode refused converting the resume task to a recurring cron; use one-shot resume tasks set when usage nears the limit.
- 2026-11-07 ~18:00: Tranche 2 committed 60b8c028 (Opus verified ledger chain, 149 records; decision counts recomputed; best Q1 near-KEEP CAND-0c6c168c rechecked: S1a -34.4 [-49.1,-20.1] vs Gap-Mix but extra promotion on Q1_3/S3c controls, -31% vs rmm_detector on S2d -> DISCARD correct). Stage-B total 143, KEEP 0. Q2 stop rule NEGATIVE. Q3 not applicable (no Q1 or Q2 winner). Deviations recorded: (1) scope-iii timeout switched mid-run from 300 s wall-clock to 300 CPU-s after 6 contention CRASHes (CRASH records retained, identities re-run); (2) A1 text calls Gap-Mix exact0.8_s4 a cond-null promoter but its adapter declares marg (cond=marg truth on all v2 cells, no decision affected); (3) rmm_detector was also used as a comparator (stricter than A1). NEXT: final A2 round (<=57 slots: Q1 repairs of near-KEEP control-cell failures + RAR canary-exposure with new RAR-native family) is being DRAFTED; coordinator must review+register A2 before any run. Then the 200-checkpoint decision (benchmark-paper-template; BENCHMARK_ONLY is the leading exit).
- 2026-11-07 ~19:30: A2 registered (52bd12b7: corrected control reading for A2 records only; S3c all-null-false and host-spend comparison verified by Opus) and RAR-arm family/suite hashes registered (d5b2db1c, recomputed). A2 Q1 arm running detached; RAR arm (G0 reference, K2, ablations K1/L) given go. NEXT after A2 decided: verify records (both readings), then the 200-checkpoint decision with benchmark-paper-template -> METHODS_PAPER_DECISION.md; if no KEEP, exit BENCHMARK_ONLY candidate, write-up by Sonnet.
- 2026-11-07 ~20:00: Disclosure: the A2 agent turned the registered G0 'reference' into a host-sanity GATE (thresholds set after registration but before any candidate record, from host/NoCanary reference runs only; failing G0 -> RAR arm UNVERIFIED, no records). Opus accepts it as a conservative check that cannot create a KEEP; it is not part of §3b and must be reported as an added rule. Both arms are running detached with 6 workers each.
