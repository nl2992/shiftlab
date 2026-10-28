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
