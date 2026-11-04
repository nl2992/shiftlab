# ShiftLab SOTA sprint: execution report

**Date:** 2026-11-03.
**Branch:** `research/sota-sprint-24`, from `origin/main` 2171689.
**Protocol:** [benchmark_spec.md](benchmark_spec.md) and [validation_protocol.md](validation_protocol.md).
The protocol was locked before validation and amended four times. Amendments 1–3 were committed before
any validation row was read. Amendment 4 was registered afterwards and is labelled post-hoc.
**Contract:** T=2000, hard B=200, c_q=.05, c_s=5, α=.05, common simulator, paired streams.

## 1. Mandatory execution gate (brief §14A): MET

* **Implementation and screening.** All 24 candidates (A1–A6, B1–B6, C1–C6, D1–D6) were implemented,
  unit-tested and screened. There are 102 tests in `tests/sota_sprint`.
  * Per family: 9–12 diagnostic environments, 20 paired seeds, a null or adverse environment, and an
    environment outside the intended region.
  * Each candidate has a mechanism ablation, saved raw records, cost, efficacy and safety metrics, and a
    disposition.
* **Mechanical audit from raw records** ([gate_audit.json](gate_audit.json),
  `scripts/sota_sprint/gate_audit.py --root outputs/sota_sprint/gate`).
  * 24/24 PASS.
  * The audit is family-isolated: a candidate is credited only with runs from its own family's
    directories. This follows the ARIS milestone-1 audit finding that names were reused across families.
  * The re-screen was run at the committed revision. It reproduces 36,696 of 37,364 (98.2%) of the
    agents' original dev rows exactly. The remainder came from intermediate code revisions.
* **Ledger and leaderboard.** [candidates.json](candidates.json) and [leaderboard.json](leaderboard.json)
  hold the per-candidate dispositions. [leaderboard_views.md](leaderboard_views.md) has the seven ranked
  views (§12), with development and validated results kept apart.
* **Phase 7 combinations.**
  * Built and screened: X_A5B5, X_A6B5, X_A5C, X_D4A1, X_D6A1:mp and X_D6A1:cams
    ([combos/README.md](combos/README.md)).
  * Only X_A5C met the advance rule.
  * Not built, with reasons recorded: A2+C3, B5+C5, B6+A1 and D6+C2.

| family | dispositions (development) |
|---|---|
| A, dependence-aware certification | A1, A5 promising (valid for any ρ); A2, A3 fast but unsafe; A4 valid, no power; A6 = A5 |
| B, recovery | B2 promising vs its host (reversal); B1, B3–B6 negative |
| C, acquisition economics | C2, C6 weak (label saving only; did not replicate); C1, C3–C5 negative |
| D, safety for fast selectors | D1, D2, D6 promising (null control; transfer across 3 hosts); D3–D5 negative |

## 2. Validation (fresh seeds; registered hypotheses)

The full tables are in [validation/validation_results.md](validation/validation_results.md),
[validation/real_results.md](validation/real_results.md) and
[validation/transfer_results.md](validation/transfer_results.md).

* **Seeds:** 100 per regime over 21 regimes (base 2026110601); 1000 per null over 7 in-class nulls and
  2 out-of-class nulls.
* **Real data:** 5 fresh UCI chronological datasets with 62 episodes. They were registered (aeb2d4f)
  before any policy run. The 9 previously exposed streams are reported descriptively.

| registered test | result |
|---|---|
| H0, the Atlas v2 stop rule (A5b vs Xu / tuned pacing; CI<0 on ≥ 4/6) | **FAIL** (1/6) |
| H1, A5b class-scoped reliability, part 1 (safety, Wilson upper bound, 7 in-class nulls) | PASS (≤ .005) |
| H1, part 2 (each certified comparator fails a null or is cost-dominated) | PASS (11/11) |
| H1, part 3 (non-inferiority within +5 on ≥ 4/5 iid alternatives) | **FAIL** (1/5) |
| H2, cost superiority with safety (A5b, A1b, D1, D2, C2, C6, X_A5C, B2, B5) | **FAIL** for all; D2 is cheaper (4/5 Holm) but unsafe at ρ ≥ .8 |
| H4, combinations | only X_A5C advanced; its late-regime gain vs A5b is −0.5 / −0.9 |
| HR (Amendment 3), RMM transfer to ≥ 4/5 hosts | **FAIL** (3/5; all 3 certificate hosts pass) |
| HD (Amendment 4, post-hoc), deploy-gate transfer to 3/3 hosts | **FAIL** (Holm-significant 0/2/2 of 5; all safe on iid nulls) |

## 3. Best mechanisms and the evidence for them

1. **RMM on certificate hosts (gated, corrected DISCERN, SMCS).**
   * Family cost vs host: −44.2, −47.3 and −13.3.
   * Late improvement vs the best certified published method (Xu): −15 to −27 for every host.
   * Independent-null safety holds.
   * Attribution: the restart mixture contributes −2.4 to −5.5 and continued acquisition −8 to −11.
   * Losses: reversal and recurrence +20 to +37; ρ=.8 null promotion .15.
2. **A5b (gap-indexed sequential universal inference certificate plus adaptive density).**
   * The only powered certified method that stays within the bound for every ρ ≤ .95. It also holds on
     two out-of-class nulls (.048, .018).
   * Stationary cost is within +7.4 of the cheapest unsafe certified port.
   * It fails on real time-series data (+61 to +257). Measured real persistence is ρ̂ .4–.98.
3. **Deploy gate on fast selectors.**
   * Native null promotion of 64–100% falls to about .015 on the three hosts.
   * D2 (CAMS) beats the best certified method on 4/5 fresh real datasets.
   * Its synthetic superiority did not replicate on new seeds.

## 4. Research verdicts

* **SOTA: `SOTA_NOT_MET`.**
  * No candidate satisfies every success-gate item (brief §14B) for a registered claim.
  * The strongest result is RMM's late-improvement advantage on certificate hosts, which is real.
    However, it rests on a post-hoc scope (certificate hosts only) after a registered 5-host test failed,
    and it has no real-data late-change confirmation.
* **Main-track candidates:** see the [publication register](publication_register.md) and §5.

## 5. Independent reviews

* **Milestones 1–2.** [review_milestone12.md](review_milestone12.md), by a native Claude reviewer. Its
  objections O1–O14 were handled by Amendment 2 before any validation row was read.
* **ARIS `experiment-audit`, milestone 1.** [aris/m1_EXPERIMENT_AUDIT.md](aris/m1_EXPERIMENT_AUDIT.md).
  Run by Codex `gpt-reserve`, a different model family. Verdict FAIL on gate-audit name pooling, now
  fixed.
* **ARIS `experiment-audit` and `result-to-claim`, milestone 3.** In [aris/](aris/); see the addendum
  below.
* **Novelty.** [novelty_audit.md](novelty_audit.md).

## 6. Reproduction

    uv run pytest -q tests/sota_sprint
    ./docs/sota_sprint/run_scripts/run_validation.sh      # synthetic, nulls, B5, real, QCE, out-of-class
    ./docs/sota_sprint/run_scripts/run_rmm_transfer.sh    # Amendments 3 and 4
    ./docs/sota_sprint/run_scripts/run_gate.sh            # family-isolated gate re-screen
    uv run python scripts/sota_sprint/analyze_validation.py
    uv run python scripts/sota_sprint/analyze_real.py
    uv run python scripts/sota_sprint/analyze_transfer.py
    uv run python scripts/sota_sprint/gate_audit.py --root outputs/sota_sprint/gate
    uv run python scripts/sota_sprint/leaderboard_views.py
    uv run python scripts/sota_sprint/fresh_real.py   # rebuilds the fresh loss caches from UCI

The run scripts are committed in `docs/sota_sprint/run_scripts/` (run from the repo root; `run_gate.sh` reads its policy/regime lists from `outputs/sota_sprint/`, copies of which are alongside); each run also records its argv in
its `manifest.json`. Raw records stay local.

## 7. Limitations

* Every comparator is a common-contract port, not author code.
* Development used 20 seeds.
* Real episodes are consecutive windows, so their CIs are optimistic.
* Four of the five part-3 regimes were exposed in Atlas v2, with other seeds.
* Family C held-out seeds shared the null-check base.
* The fresh real streams contain almost no harmful-switch episodes (6/62), so they mostly measure
  promotion cost.
* PaperBanana was not used; no figures were produced.
