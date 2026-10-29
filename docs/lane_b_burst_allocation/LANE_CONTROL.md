# Lane B: evidence-responsive budget allocation under unknown bursts (Claude lane)

**Opened 2026-10-28.** This is an iterative research loop working toward the user's methodological
goal (as Codex records it in `docs/budgeted_switching_research_goals.md`, in the main checkout): one
genuinely new acquisition-and-switching mechanism under a hard observation budget and delayed
feedback, with a defensible theorem and matched-budget evidence. ShiftGuard is the platform, not
the contribution.

**Status: no mechanism, novelty or theorem established.**

## Coordination with the Codex lane (do not duplicate)

| | Lane A (Codex, main checkout, uncommitted files `docs/switching_*`) | Lane B (Claude, this worktree, branch `research/claude-lane-burst-allocation`) |
|---|---|---|
| Question | G1 theory-first novelty gate for two-policy economic switching: comparator, false-switch event, lower bounds, finite Bellman/LP references | **How to spend a hard label reserve when the learner cannot tell in advance whether a disagreement burst is harmful** |
| Already covered there (do not redo) | one-step VOI (rejected); receding burst rollout (standard); risk-budget Bellman planner (rejected); movement-compatible channel selection (rejected); Cheng paid observation; Prabhu controlled sensing; dynamic indicator regret; delayed switching-cost optimisation; Shin–Ramdas–Rinaldo e-detector all-onset mixture (baseline); noisy delay-budget-safety lower bound; current-regime vs null validity | — |
| Motivating evidence | integrated efficacy confirmation (late harm, certification delay, reversal loss, inert controller) | **E2 confirmation (`docs/research_refinement_v1/stage1/STAGE2_RESULTS.md`)**: paced gating loses 8–22 points to fixed in harmful post-onset bursts; fixed loses up to 99 points to paced under harmless pre-onset bursts; the horizon cap is a compromise that loses in both |

Rules:
- Lane B never edits Lane A's files and never stages files in the main checkout.
- Lane B commits only on its own branch, and fast-forwards `main` only if `main` has not diverged.
- Before each tick, read the latest checkpoint in `docs/budgeted_switching_research_goals.md` in the
  main checkout. If Lane A has started on burst allocation, stop and reconcile.
- Lane A's baselines (e-detector mixture, Cheng-style paid observation) are reused as comparators
  and credited.
- `docs/LANE_COORDINATION.md` in the main checkout (untracked, for Codex to read) mirrors this
  table.

## Research question (B1, to be made precise)

There is a hard label budget `B`, label prices, and a stream with a free disagreement indicator
`D_t`. Bursts of disagreements arrive, and each burst is harmful (`E[Z_t] > ε`) or harmless
(`E[Z_t] ≤ ε`); harmfulness is unknown before labels arrive. Labels have delay `d`, and the
budget is charged at request. The decision layer is an anytime-valid switch (alarm, then revert)
with false-switch control under the charter null.

**Conjecture (falsifiable):**
1. **Lower bound.** Every oblivious rule (fixed, paced or horizon-capped `q_t`, a function of
   `D` history and budget only, not of label values) has detection-delay regret Ω(·) against an
   oracle in at least one of the two burst classes.
2. **Upper bound.** An *evidence-responsive* rule, whose `q_t` is a predictable function of the
   running e-process or CUSUM-type statistic, retains anytime validity and achieves regret within
   O(·) of the oracle in both classes under a stated burst model.

Both parts are research targets, not results.

## Gates and exit conditions

| Gate | Deliverable | Pass | Exit (stop or pivot the lane) |
|---|---|---|---|
| B0 novelty pre-screen | `B0_prior_art.md`: DE-CuSum (Banerjee–Veeravalli 1211.3729), on-off observation control (1105.1361), Hou–Bidkhori–Banerjee 2412.20207, budgeted/data-efficient QCD with hard sampling budgets, bandits-with-knapsacks and online-knapsack allocation, Geng–Bayraktar–Lai, Zhang–Cheung, DISCERN 2609.17560; plus Lane A's controlled-sensing and observation-control audits (read, do not redo) | Precise residual: what none of them gives (hard pathwise budget + unknown burst harmfulness + anytime-valid null + delayed labels) | **A published method already gives an evidence-responsive sampling rule with a hard budget and an anytime false-alarm guarantee, with a delay bound in both burst regimes → pivot** |
| B1 problem + separation | `B1_problem.md`: burst model, oracle comparator, the oblivious-rule lower bound (proof or a finite-instance numerical counterexample) | The separation holds under a nontrivial model | The lower bound fails (some oblivious rule is near-oracle in both classes) → stop |
| B2 mechanism + validity | Rule pseudocode; anytime-validity proof (a predictable `q` from past wealth suffices; check it); an upper-bound attempt | Validity proved; upper bound proved or numerically supported on a finite instance | Validity needs non-predictable information → redesign once, then stop |
| B3 dev prototype | `src/shiftlab/dive/lane_b_*.py` plus tests; E2 platform cells on a **new registry dev block** | Beats the best of {fixed, paced, horizon, DE-CuSum-style, e-detector mixture} in **both** burst classes on dev, at matched budget, with no validity loss | It fails to beat the best oblivious rule in both classes → record the negative result and stop |
| B4 switching tie-in | Alarm → revert/promote on the E3 platform, with net utility including query and switch costs | Gain in net utility, not only detection | — |
| B5 confirm | Frozen protocol, Codex review, fresh seeds, real-data eligibility audit | Registered gain | — |

**Global stop:** after 12 ticks without passing B1, stop the lane and report.

## Tooling

- **Python:** from this worktree run
  `PYTHONIOENCODING=utf-8 PYTHONPATH=$PWD/src UV_PROJECT_ENVIRONMENT=<main>/.venv uv run --no-sync python ...`.
  `<main>` is `C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter`.
- **Subagents:** Haiku for fetching and reading papers, Sonnet for drafts and code, Opus for
  verification.
- **Codex reviewer:** run with `codex exec --sandbox read-only ... < /dev/null`, and phrase reviews as
  methodology questions.
- **Data:** no downloads. Raw data is read only from `<main>/data`.

## Tick log

| Tick | Date | Gate | Outcome |
|---|---|---|---|
| 0 | 2026-10-28 | setup | Worktree, lane control and coordination note created. E2–E4 confirmation results recorded on `main` (`6527fe9`). P4 external adapter paused (benchmark is no longer the contribution; resume only if needed as a comparator). |
| 1 | 2026-10-28 | B0 | **PASS with combination risk** (`B0_prior_art.md`; mostly abstract/summary-level reads). Closest: Geng–Bayraktar–Lai 1309.5396 (hard cap N, posterior-driven sampling, Bayesian PFA, iid pre-change; Prop. 2 says uniform is first-order optimal under iid), DE-CuSum/RDE-CUSUM (average duty cycle, ARL), DISCERN (anytime mean CS under predictable routing; no cap, no change). Predictable-q validity is not new (DISCERN Thm 5). The contribution must be the burst-model delay theorem; the separation needs non-iid pre-change bursts; check Zhang–Cheung NeurIPS 2024 inventory-reserving lower bound before claiming B1. Next: full reads of Geng limited-sampling section, Zhang–Cheung lower bound, DISCERN Thms 7–9, then B1. |
| 2 | 2026-10-28 | B0b/B1 | Lane A checked: newest checkpoints (uniform+mixture weak, cost-adaptive observation prior, reversal diagnostic rejected, alpha-spending baseline) do not touch burst/reserve allocation. Started full reads of Geng / Zhang–Cheung / DISCERN (Haiku). Lead drafted `B1_problem_draft.md`: two instances with identical disagreement law, separation of order log(1/alpha)/KL between oblivious and evidence-responsive allocation; flagged HIGH mechanism combination risk (DE-CuSum on-off principle), the possible contribution being the theorem. Registered dev block lane_b_toy_development 100600000–100699999; numerical separation check started (Sonnet). |
| 2b | 2026-10-28 | B0b | Full reads in `B0b_full_reads.md`. **Correction to B0:** Geng's Prop. 2 is only an upper bound for uniform sampling; the first-order-optimal rule under iid pre-change data is greedy (sample whenever a right is available, Remarks 9–10), which is itself oblivious. Zhang–Cheung (Thm 4.2 O(log(η_max/η_min)) competitive ratio, Thm 4.5 matching lower bound) uses a deterministic piecewise-efficiency instance with observed rewards. Its lower bound does not cover the case where harmfulness is revealed only by buying labels, so it neither implies nor refutes Claim 1; the exact statement needs a check (PDF symbols garbled). DISCERN's budget is Bernoulli, not a hard cap. |
| 3 | 2026-10-28 | B1 | **Numerical check NEGATIVE as specified** (`B1_numerical_check.md`, 1000 seeds per cell, null control passes). The best oblivious rule (skip the burst by run length, then sample the sparse phase) is at least as good as both responsive rules on detection in every informative cell. Responsive rules gain only 8–29% delay at d=0 with generous budgets and lose P_N, because harmless burst labels drain the shared e-process wealth. The deficit grows from alpha=0.05 to 0.001, the opposite of the conjecture. **Diagnosis:** the instance violated the claim's premise (harm in H persisted after the burst, so H never needed burst spending). **One registered corrective check, fixed before results:** (i) H harm is transient (burst only; null after it); (ii) all-onset e-detector mixture (Lane A baseline, Shin–Ramdas–Rinaldo) instead of a single e-process; (iii) same grids, B and alpha, seeds from the lane block. **Exit if any oblivious rule is within 0.05 of the responsive rule's min(P_H, P_N) at every tight B.** No further instance changes after this. |
| 4 | 2026-10-28 | B1 | **Corrective check MIXED** (`B1_corrective_check.md`; criterion applied per (rho, d, alpha) family). The separation is **not refuted** in 6/8 families. At d=0, alpha=0.05 the responsive stop rule beats the best oblivious rule by +0.09 to +0.36 in min(P_H,P_N) at every tight B. It is **refuted** in 2/8 (alpha=0.001, d=20: no rule has power). At d=20 the responsive rules lose at B=40/60 (pending labels charged at request; the stop arrives about 20 labels late). The predicted growth of the gap as alpha falls is **not seen**. The winner is the SPRT stop with a known harmful mean (a mild oracle); DE-CuSum wins only 4/24. Null control passes. **Seed overrun disclosed:** the first check used seeds up to 100830999, past the block; registered as lane_b_toy_first_check_overflow. **B1 status: partial**: an empirical separation at low delay and moderate alpha only; the theory sketch's alpha scaling contradicted. Next: Codex methodology review of whether a delay-aware responsive rule plus a separation theorem is a worthwhile, non-combination target, or whether to stop. |
| 5 | 2026-10-28 | B1 review | **Codex verdict: PIVOT** (`CODEX_REVIEW_1.md`). Lead errors it found, all accepted:
- **Wrong endpoint.** Both checks scored H alarms anywhere before T rather than within the burst.
- **Wrong null.** Disagreement-only scoring tests a conditional null; under the charter's population null, N is null throughout (sparse harm rho*mu <= eps), so N "power" is not charter harm.
- **Mislabelled correction.** Calling the persistent-harm instance a premise violation was wrong; the correction is a disclosed forking path.
- **Missing comparator.** Randomised mixtures of oblivious rules leave only 3/8 families not refuted (exploratory).
- **Implementation issues.** P_H counts post-harm alarms; P_N includes pre-onset alarms; delayed spend is mis-timed.
- **Missed prior art.** Chandar–Tchamkerten transient detection with multistage adaptive sampling (arXiv 1501.05930, 1302.6574).
- **Geng correction.** Greedy optimality there applies to replenishing rights only.

**The B1 claim as drafted is withdrawn** (W-B1). **New target (pivot within acquisition):** a minimax budget–duration–delay frontier for hard-budget screening across multiple indistinguishable finite harmful windows with delayed labels, with a lower bound over ALL adaptive policies and a matching implementable rule, benchmarked against the strongest multistage-screening composition. **Theory first; no simulation sweep until the theorem is frozen.** Stop if ordinary screening plus a capped detector attains the frontier (keep the two-window result as a note). |
| 6 | 2026-10-28 | reconcile | **The pivot target duplicates Lane A; stopped.**
- **Already done in Lane A.** `switching_budget_delay_lower_bound_v1.md` already proves a finite-horizon obstruction in B, d, pulse duration and global false promotion over adaptive randomised query policies. Lane A has also audited Chandar–Tchamkerten scout/confirm (Lemma 1), Geng finite rights, Ryabchenko fixed-delay capacity scheduling and DAL restarts. Lane B's minimax screening frontier would repeat that work, so per the coordination rule the algorithm search in Lane B is closed: B1 is withdrawn and the pivot is a duplicate.
- **New Lane B mission (non-duplicative, unblocks Lane A's G4).** A real-data testbed with *verifiable* observation timing on local datasets that Lane A's eligibility audit (`switching_real_data_eligibility_v1.md`: CRSP, Criteo, CriteoPrivateAds, OBD, WILDS) did not cover: **Binance** (exact trade timestamps, known return-horizon label delay, published fee schedule as switching cost, finance motivation), plus OPSD, NOAA, FRED, elec2, gas_sensor and Monash.
- **New gates.**
  - **R0:** metadata-only eligibility audit against Lane A's contract: paired common-label outcome, verified availability clocks, chronological untouched windows, cost interpretation, licence, exposure. No values go in docs.
  - **R1:** a frozen task spec for the best candidate, with a timing audit.
  - **R2:** an adapter to the contract interface and a smoke run with existing baselines.
- **Exit:** if no dataset passes R0, record the precise missing information and stop the lane.
- The Chandar–Tchamkerten reader already running is allowed to finish (no new work started). |
| 7 | 2026-10-28 | R0 | Metadata-only audit (`R0_real_data_eligibility.md`).
- **OPSD hourly German load is ELIGIBLE-CANDIDATE.** It pairs the ENTSO-E day-ahead forecast with a frozen forecaster on the common actual load. 2015–2017 and 2020-01 to 2020-09 appear unexposed. Caveats: the publication clock is not in the data (the ENTSO-E deadline is external and unverified); there is no licence field; costs are imposed; disagreement density is unknown. Choosing 2020 (which includes the COVID disturbance) as the holdout is a forking path and must be declared before opening.
- **Binance has the best clock** (exact UTC bars; label delay of one bar) but is DEVELOPMENT-ONLY locally (one hourly month). Making it eligible needs about 12 months of ETHUSDT 1h klines (about 500 KB) and a dated fee-schedule snapshot. That is a download, so it is **blocked pending user OK** under the standing no-download rule.
- **Other datasets.** Gas sensor, NOAA and Monash are DEVELOPMENT-ONLY; elec2, FRED and Folktables are INELIGIBLE.
- **Cross-cutting.** Labels are free everywhere, so the budget, the switching cost and the burst structure are imposed on every dataset.
- **Next:** R1, a frozen OPSD task spec with a declared clock assumption and a holdout declaration. |
| 8 | 2026-10-28 | R1 | The user granted data-fetch permission ("feel free to fetch data… we already have loads locally"); recorded in memory, with local data still first. Fetched ETHUSDT 1h klines 2025-02 to 2026-09 from data.binance.vision into `<main>/data/raw/binance/` (20 files, publisher checksums verified, receipts in the existing format; gitignored). R1 frozen task specs (OPSD primary, Binance secondary) started by Sonnet, specs to be written before any outcome inspection. |
| 9 | 2026-10-28 | R1 | Two frozen task specs written before any outcome inspection (`R1_task_specs.md`).
- **(A) OPSD:** ENTSO-E day-ahead forecast vs a frozen per-hour ridge (2015–16 training), reserve-cost action, decision D-1 10:00 UTC, d=2 rounds, development 2018–19, locked 2020-01..09. The forking path is stated: the 2020 disturbance is public knowledge.
- **(B) Binance:** 24- vs 168-bar momentum long/flat, d=1, fee 0.1% per side, development 2025, locked 2026-01..09. Disagreement is dense (about 0.38, from an approximation), which is fine for Lane A's switching contract but not a sparse-burst testbed.
- **Not a G4 pass alone.** Neither task passes G4 by itself (Binance is stronger on clocks and costs; OPSD on the policy pair and drift).
- **External refs only partly verified.** The ENTSO-E rule and Binance fee page are only partially verified (WAF challenges blocked scripted fetches; noted for a human check). OPSD revision status and the DE zone across the 2018-10 split are unverified.
- **Next:** R2, measuring disagreement density on development windows only, then a contract-interface adapter and a smoke run with existing baselines. |
| 10 | 2026-10-28 | R1b/R2 | The user asked for assumptions or a browser check instead of manual steps. ENTSO-E Art. 6(2) clocks, the Binance 0.100% fee and the OPSD DE series definition were verified in the built-in browser (no bot challenge); A1–A5 declared (`R1b_verified_refs_and_assumptions.md`). Lane A's newest checkpoints (monotonicity LP, response-adaptive switching-cost prior) show no real-data overlap. R2 started (Sonnet): task adapters with a code-enforced holdout guard, and disagreement density measured on development windows only. |
| 11 | 2026-10-28 | R2 | Adapters `src/shiftlab/real_tasks/` with a code-enforced holdout guard; 21 tests. **Development only:**
- **OPSD 2018–19:** 728 rounds, disagreement 21.7% (158 rounds), runs mean 2.9 / max 5 against 1.28 if independent (short workweek blocks), mean Z on disagreement rounds 0.033 (sd 0.147). Informative under the R1 rule.
- **Binance 2025:** 8,590 rounds, disagreement 39.9%, runs mean 6.2 / max 62, mean Z 0.0017 (sd 0.037). Dense, with a near-zero, noisy signal.
- **Harness smoke** (zero-delay upper bound): no alarms at the primary budgets; uniform HT spends 60–79% of labels on agreements.
- **Amendment A-B2:** Binance Z is now the position-return difference only, with fees moved to the switching channel (agreement means Z=0).
- **Disclosed:** the OPSD ridge penalty sits at the grid edge.
- **Next:** R3, freeze both tasks (protocol plus freeze record, with the delay-aware harness noted), Codex methodology review, then hand off to Lane A via the coordination note. |
| 12 | 2026-10-28 | R2 | Waiting: the A-B2 implementation (Binance Z = position-return difference) is still running, so no duplicate was started. Lane A's newest checkpoints (six-round oracle certificate; belief-grid FSC not a novelty candidate) do not overlap; there are no OPSD or Binance mentions there. Note: the global stop rule (12 ticks without passing B1) applied to the withdrawn algorithm search; the real-data mission has passed R0–R2 and continues to R3 freeze and handoff. |
| 13 | 2026-10-29 | R3 | A-B2 implemented (`5625425`): Z=0 on all agreement rounds. **Codex pre-freeze review: DO-NOT-FREEZE for both tasks** (`CODEX_R3_REVIEW_1.md`).
- **Shared issue: outcomes leak into the public features.** OPSD loads and Binance returns reconstruct the paired losses without queries, so the budget would be fictitious. Lead decision: declare the monitor a **label-limited auditor**. Its filtration is the actions, disagreement, prices, queried Z and calendar features only. The frozen policies may use public data, but evaluator-side only.
- **OPSD fixes:** align delivery blocks to CET/CEST local days (the UTC day spans two forecast deadlines); keep scheduled rounds when the label is missing; embargo the split boundaries using availability timestamps; the holdout reader must check the timestamp before parsing a row.
- **Binance fixes:** choose gross clipped signal loss plus a constant imposed k (turnover accounting removed from the switching cost, or declared separately); freeze the exact normalised and clipped Z formula; preserve microsecond close timestamps.
- **Assumptions:** A2 and A3 stay disclosed as unresolved.
- Fixes sent to the R2 implementer. |
| 14 | 2026-10-29 | R3 | Waiting: the A-R3 fix implementer is still running (edits visible in the worktree), so no duplicate was started. Lane A's newest checkpoints (monotone terminal tests; delayed-reversal oracle cell) do not overlap. |
| 15 | 2026-10-29 | R3 | Amendment A-R3 implemented: label-limited auditor (public x = calendar features only; tests scramble outcomes), Europe/Berlin local-day rounds with the decision at 10:00 local D-1, missing labels kept as missing feedback, embargoed boundaries, timestamp-prefix holdout reader, Binance Z frozen as gross clipped signal loss with k = f/(2*0.10), hour-boundary decisions. Lead decision: drop the OPSD hour-07 lag (the only early-information feature); OPSD development aggregates unchanged (0.230, 168 rounds). 30 tests pass. Next: Codex pre-freeze recheck. |
| 16 | 2026-10-29 | R3 | The Codex pre-freeze recheck of A-R3 **did not run**: Codex usage limit (retry after 10:43 PM local). No review result is claimed. Both tasks stay unfrozen until the recheck runs. **Next tick after 10:43 PM:** rerun the narrow recheck (prompt as in tick 15 context; the review base is CODEX_R3_REVIEW_1.md, commit 51d3ffb). |
| 17 | 2026-10-29 | R3 | 20:50 local, so Codex is still blocked (until 22:43). Drafted `R3_freeze_and_handoff_DRAFT.md`: freeze file list, raw-data pins, handoff table for Lane A, limitations, opening rule. Not frozen. Lane A's newest checkpoints (fixed-cohort separation) do not overlap. |
| 18 | 2026-10-29 | R3 side task | The user asked for parallel work while Codex is blocked. Started **contract harness v2** (Sonnet): label delay, pending-query budget reservation, missing feedback, and an optional switching layer with net-utility accounting, following Lane A's event order in `switching_problem_v1.md`. v1 is kept bit-identical, plus a development-only smoke run on OPSD and Binance. Checked for no overlap: Lane A has a delayed-Hedge reference policy, not a contract harness. |
| 19 | 2026-10-29 | R3 | 21:20 local. Codex is still blocked (until 22:43); the harness v2 implementer is still running, so no duplicate was started. Lane A unchanged since tick 17 (no overlap). |
| 20 | 2026-10-29 | R3 side task | **Contract harness v2 done** (`harness_v2.py`, `interface_v2.py`, `baselines_v2.py`, `real_tasks/v2_smoke.py`; v1, interface.py and the sandbox untouched).
- **Features:** per-event release delays (never early, out-of-order allowed), pending-query budget reservation, explicit MissingFeedback, and a Switcher layer with net utility = -(deployed loss) - c*queries - k*switches.
- **Parity:** bit-identical to v1 at delay 0 with no missing labels.
- **Development smoke (descriptive):** no alarms on OPSD or Binance at the primary budgets, so alarm-then-switch never switched. Net utility is not comparable across arms (different processed prefixes after the reserve stop).
- **Validity limits:** validity of e-process updating under delay is not claimed. False promotions are reported only with an evaluator null mask (an extension of Lane A's definition). |
| 21 | 2026-10-29 | R3 side task | 21:50 local; Codex still blocked. Lead note `R3_delayed_update_validity_note.md` (not reviewed): release-time updates in v2's DelayedHT are valid under fixed delay (time-shifted Ville), under calendar-driven delays independent of outcomes (release-order supermartingale), and under missing-at-random labels (validity with lost power). Informative delay or missingness is not covered. It goes to Codex together with the R3 recheck once the limit resets. |
| 22 | 2026-10-29 | R3 | Codex was live early (22:20). **Recheck** (`CODEX_R3_REVIEW_2.md`):
- **Binance: FREEZE-WITH-NOTES.** It may only be read as a narrowed audit-budget benchmark: imposed costs, idealised execution, descriptive real-stream claims.
- **OPSD: DO-NOT-FREEZE.** (a) The autumn-DST 48-hour lag reaches Saturday 00:00 before Saturday's label releases; (b) future timestamp irregularities veto policy pairs without a decision-time justification.
- **Validity note: INCORRECT.** The out-of-order delay claim is withdrawn (counterexample, P ≥ 0.075). The fixed-delay derivation is qualified. A missing label must apply −ε, not skip. OPSD's delay is actually fixed d=2. The note is corrected in place.
- **Both tasks are frozen together after the OPSD fix** (they share one protocol file).
- **Fixes sent:** the OPSD DST lag and availability mask, the timestamp-veto rule, the DelayedHT missing-label increment, and the release-offset sentinel. |
| 23 | 2026-10-29 | R3 | Waiting: the A-R3b fix implementer is still running (OPSD DST lag and availability veto, release sentinel, DelayedHT missing-label and out-of-order fixes), so no duplicate was started. Lane A's new checkpoint (small-family separation from deterministic query calendars) does not overlap. |
| 24 | 2026-10-29 | R3 | A-R3b implementation and development rerun are committed (`4be7609`). The corrected task-specific suite passes **108 tests** (`test_real_tasks.py`, `test_contract.py`, `test_contract_v2.py`). Development-only OPSD: 729 rounds, disagreement 22.1%, maximum run 5 days, mean disagreement `Z=0.0061` (sd 0.139); Binance: 8,590 rounds, disagreement 39.9%, maximum run 62 bars, mean disagreement `Z=0.00135` (sd 0.0366). No holdout read. Codex checked the R3 handoff and found it stale: the protocol and freeze list omitted A-R3b/v2, and its claimed one-opening locked reader does not exist. Updated the draft to distinguish a task-contract freeze from a method freeze; neither permits reading holdout until a runner verifies both freezes and creates an `O_EXCL` marker before any data access. Null-validity evidence remains separate from current-regime value, including after a reversal. Next: finish the task freeze manifest after this draft/protocol are committed; do not open either holdout. |
| 25 | 2026-10-29 | R3 | Created `R3_task_freeze.json` after committing the protocol and task evidence. It hashes 26 files including the A-R3b adapters, v2 delayed-feedback harness and baselines, tests, `uv.lock`, seed registry, and R2 outputs; `check_freeze` reports no problems. This freezes the task contract only. The R3 report now records the freeze. Holdouts remain closed until a separate method-specific Lane A freeze and a tested one-opening runner exist. |

## Phase C: back to the original goal, a new algorithm (opened 2026-10-29)

The user's instruction: "please follow our initial goal… developing a potentially bloody algo". The real-task testbed is frozen (`R3_task_freeze.json`, merged to main by Lane A), so Lane B returns to algorithm development. The target is one new acquisition-and-switching algorithm under a hard label budget and delayed feedback, with a defensible theorem and matched-budget wins over the strongest baselines on synthetic data (E2/E3 platform) and on real data (OPSD and Binance development windows, then a frozen holdout).

**Constraint:** Lane A's G1 work rejects or audits many generic routes as prior art: one-step VOI, receding rollout, risk-budget Bellman, channel selection, Cheng paid observation, Prabhu controlled sensing, dynamic indicator regret, delayed switching-cost optimisation, e-detector all-onset mixtures, randomised alpha spending, futility stopping, delayed-POMDP information state, constrained POMDP/RC-POMDP, costed two-phase bandits, Markov state-sensing planners, DAL restart. A candidate must say why it is none of these.

| Gate | Deliverable | Pass | Exit |
|---|---|---|---|
| C0 candidates | `C0_candidates.md`: at most three mechanisms, each with an explicit 'why not prior art X' against every Lane A audit, a falsifiable theorem target, and a 1-day synthetic test | At least one survives a Codex methodology screen | None survive → write a pivot memo for the user |
| C1 prototype | Runnable rule plus tests on the E3/E2 synthetic platform, against the strongest baselines (ShiftGuard full pipeline, q1_fallback, e-detector plus uniform or gated query, Cheng-style paid observation, DAL-style restart) under identical budget, delay and costs | Beats the strongest baseline on net utility in dev cells, with safety held | Fails → record and try the next candidate |
| C2 theory | Proof or counterexample of the theorem target | Proved or sharply bounded | Disproved → back to C0 |
| C3 real data | OPSD and Binance development windows through harness v2 | Same ordering as synthetic | — |
| C4 confirm | Frozen protocol, Codex review, fresh seeds, holdout opened once | Registered win | — |
| C-1 | 2026-10-29 | C0 | `C0_candidates.md`: **RLS (recurrence-locked switching) survives conditionally**. Split-clock switching needs a surrogate channel (high novelty risk); harm-budgeted deployment is discarded (constant-sum symmetry). **Codex screen: NARROW** (`CODEX_C0_REVIEW_1.md`).
- **Comparator class:** the "needs post-change evidence" class is legitimate but too narrow, and has a loophole (switch one round early).
- **Prior art:** no verified prior theorem gives the RLS bound under budget, delay and the causal null. Mandatory competitors: Periodic EXP4 (Oh–Meetoo Appavoo–Gilbert, ICALP 2019), Cheng 2023 Thm 2, and a duration-aware forecasting controller.
- **Theorem defects:** accumulated vs bounded jitter; future information in the error term; chronological bisection unproved; the reactive lower bound assumes a schedule; certification needs power and budget-exhaustion terms; switch costs on both sides; no proved iff transition.
- **Real-data arithmetic:** the Binance figure is an evidence scale, not a minimum (about 70% power at 3,428 labels); OPSD halves are descriptive only.
- **Next (C0→C2 narrowed):** known period, latent offset, explicit emission law, one jitter model; prove causal localisation and promotion validity before any efficacy grid. Kill if a contract-matched schedule learner or duration-aware controller attains the same rate by standard composition. |
| C-2 | 2026-10-29 | C2 | Merged main. Lane A's newest no-go (positive-prefix acquisition is group-sequential futility; kept as a baseline) leaves G1 open only for recurrent delayed two-law gains, which is the RLS area. RLS is claimed in `docs/LANE_COORDINATION.md` (main checkout and branch) to avoid duplication. The narrowed RLS theory and small-instance check are still running, so no duplicate was started. |
| C-3 | 2026-10-29 | C2 | Merged main (Lane A's newest no-go: generic finite-window belief compression is established; no RLS overlap). The RLS theory agent's 2,000-seed small-instance run is still in progress (draft files present, uncommitted), so no duplicate was started. |
| C-4 | 2026-10-29 | C2 → EXIT | **RLS killed** (`C2_rls_narrowed_theory.md`, 2,000 seeds per cell, seeds 100696000–100699999). It is equivalent to a duration-aware MLE forecaster plus a standard planner and gate; the design edge is standard BED, and Thompson sampling matches or beats it at primary budgets. No other C0 candidate survives on the frozen information structure. **Phase C exit rule applied:** `C_PIVOT_MEMO.md` written, loop stopped. Recommended pivot: delay-heterogeneous label channels (split-clock) with an OPSD fast-surrogate task; alternatives are multi-candidate shared labels and selective labels. |

## Phase D: split-clock (delay-heterogeneous label channels), opened 2026-10-29

The user chose pivot 1 from `C_PIVOT_MEMO.md`. **Structure:** each disagreement can be labelled through a fast, biased surrogate channel (short delay `d_f`, price `c_f`) and/or a slow gold channel (long delay `d_g > d_f`, price `c_g`). The question is how to allocate the budget across channels and time, using the fast channel for rollback (which needs no alpha-certification) and the gold channel for certified promotion. **Target:** a per-reversal gain of order Δ·(d_g − d_f) over every single-channel method and over standard compositions, with promotion validity kept on gold evidence.

| Gate | Deliverable | Pass | Exit |
|---|---|---|---|
| D0 audit | `D0_prior_art.md`: controlled sensing (Prabhu et al.; read Lane A's audit, do not redo), the repo's delayed-PPI and evidence-directed PPI work, prediction-powered e-values and active inference, multi-fidelity bandits and BO, bandits with intermediate or surrogate observations and delays, surrogate-index methods, multi-source change detection with sensing costs | A precise residual that is not a composition | A published or in-repo method already gives a fast-surrogate rollback plus gold-certified promotion rule with a delay-gap advantage → stop and choose the next pivot |
| D1 task | `D1_opsd_split_clock_task.md`: an OPSD fast-surrogate task spec (clocks, surrogate definition and bias, prices, development and holdout windows, Codex review, freeze) | Frozen, with a measured development surrogate-gold correlation | No usable fast channel → evaluate a Binance alternative (short-horizon return as surrogate for a long-horizon P&L label) |
| D2 mechanism + theorem | Rule plus proof or counterexample of the delay-gap advantage | Proved or sharply bounded | Reduces to a composition → stop |
| D3 synthetic | E3-style simulator with two channels; baselines: gold-only, surrogate-only (invalid-promotion control), PPI-composed, controlled-sensing planner | Wins on net utility with safety held | Fails → stop |
| D4 real data | OPSD (and Binance) development windows via harness v2, extended to two channels | Same ordering | — |
| D5 confirm | Frozen protocol, Codex review, holdout opened once | Registered win | — |

**Global stop:** 16 ticks without passing D2.
| D-1 | 2026-10-29 | D0 | **Narrow, conditional PASS** (`D0_prior_art.md`; many reads are summary or snippet level).
- **Target corrected.** The composition C* (gold-certified delayed PPI promotion, a surrogate CUSUM/e-detector rollback, a fixed split with a paired-calibration bias UCB) already attains rollback without certification, gold-valid promotion, and the delta*(d_g - d_f) gain over gold-only. **D2 must separate from C*, not from single-channel methods.** The realistic gain is a constant/log or regime-dependent factor.
- **Residual.** A hard-budget, delayed-release allocation across channels and time that beats the best stationary split, with rollback that stays safe when the surrogate bias is learned from late gold labels and may shift at the reversal. The biggest exit risk is reduction to a delay-shifted controlled-sensing index plus a bias margin.
- **Closest sources.** Kandasamy MF-MAB; Ao et al. 2601.21471 (anytime CS over a cheap biased judge plus gold audits; snippet only); the repo's CertifiedPromotionRollback plus delayed PPI.
- **Before freezing D2:** a targeted search on multi-rate change detection, guardrail rollback with surrogate metrics, and early stopping on proxies.
- D1 (OPSD task) is still running. |
| D-2 | 2026-10-29 | D1 | **The OPSD fast channel fails** (`D1_opsd_split_clock_task.md`). The fast label is the hours 00–07 partial reserve loss, with d_f=1 and d_g=2 (the clock holds), but the surrogate is uninformative on development data: sign agreement 0.069 (floor 0.6), Zf=0 on 89.4% of rounds, Pearson 0.21. Only 3% of disagreeing hours fall in 00–07 because the forecasts diverge at the daytime peak; a later cutoff erases the gap. By D1's exit rule the Binance alternative is next: fast = 1-bar return, gold = 24-bar P&L label (gap of 23 rounds). That needs a development surrogate–gold measurement and a dependence statement for overlapping labels. 44 tests pass. |
| D-3 | 2026-10-29 | D1b | **The Binance split-clock task misses the floor** (`D1b_binance_split_clock_task.md`). Fast = 1-bar loss (d_f=1), gold = 24-bar P&L loss (d_g=24). Sign agreement is 0.563 (< 0.6), Pearson 0.18, bias about 0. Overlapping gold labels (lag-1 autocorrelation 0.77) must be thinned to one per 24 rounds for valid certification (a design argument, not verified). Valid gold labels are then **count-limited, not delay-limited** (fast collects its evidence about 3.7x sooner at similar cost).
- **Lead decision (pre-registered floor applied literally):** no real-data task has an informative fast channel. Binance is kept as a declared low-quality-surrogate stress case. **D2 and D3 proceed on synthetic two-channel models, sweeping surrogate quality around 0.56.** No second-look 'richer' fast label on exposed 2025 data (forking path). Real-data relevance of any D2 result is limited and must be stated.
- Next: D2 mechanism and theorem against the composition C*, after the targeted search D0 required (multi-rate change detection, guardrail rollback on surrogate metrics, early stopping on proxies). |
| D-4 | 2026-10-29 | D2 | Merged main (no Lane A split-clock or surrogate overlap). The D2 agent is still running (simulation script and seed-registry edit in progress, uncommitted), so no duplicate was started. Ticks without passing D2: 1/16. |
| D-5 | 2026-10-29 | D2 → EXIT | **Phase D exits** (`D2_split_clock_mechanism.md`). The candidate is a composition (per-phase index, surrogate CUSUM, gold backstop, scout/confirm). Proved impossibility: rollback before d_g is impossible when the bias shift b ≥ 2βΔ. Monte Carlo: the plain two-phase composition wins 8/9 cells; the fast channel helps only at sign agreement 0.8 with no shift. Disclosed: detector settings tuned on smoke seeds; best-of-family selection on evaluation seeds. Seed block lane_b_d2_split_clock_development 100900000–100919999 registered. Pivot memo updated; loop stopped. |

## Phase E: many candidates sharing one queried label (opened 2026-10-29)

The user chose pivot 1 from `C_PIVOT_MEMO.md`. **Structure:** an incumbent plus K frozen candidates. One queried event reveals the paired losses of *all* K candidates against the incumbent (common label). Label cost does not grow with K, but certification multiplicity does (any-false-promotion over K, or over a growing candidate stream). The disagreement set depends on which candidates are still alive. Delay, hard budget and reversible switching as before.

**Question:** how to allocate queries (which events, given the live candidates' disagreement patterns) and when to promote, demote or switch among candidates, with a multiplicity-controlled any-false-promotion guarantee. The target is a theorem showing a gain over (i) per-candidate testing with Bonferroni or alpha spending, (ii) e-BH-style multiple testing, and (iii) best-arm identification with full information, as K grows. Example: a sample cost that grows like log K with an acquisition rule that exploits the overlap structure of disagreement sets.

| Gate | Deliverable | Pass | Exit |
|---|---|---|---|
| E0 audit | `E0_prior_art.md`: best-arm identification (full-information / shared-observation, fixed confidence, anytime), pure exploration with feedback graphs, AnyRank, OCS, Digalakis Challenger, e-BH and online multiple testing with e-values, selective inference and conformal selection, and Lane A's audits (do not redo) | A precise non-composition residual | A known method already gives the shared-label, delayed, hard-budget, multiplicity-controlled switching rule with the target scaling → stop |
| E1 mechanism + theorem | Rule plus proof or counterexample of the K-scaling advantage over the baseline class | Proved or sharply bounded, and not equivalent to a standard estimator plus planner | Composition → stop |
| E2 synthetic | Monte Carlo with K in {2, 8, 32}, matched budget, delay and costs | Wins on net utility with any-false-promotion controlled | Fails → stop |
| E3 real data | K-candidate versions of OPSD (ridge variants) and Binance (momentum lookbacks), development windows only | Same ordering | — |
| E4 confirm | Frozen protocol, Codex review, holdout opened once | Registered win | — |

**Global stop:** 16 ticks without passing E1.

