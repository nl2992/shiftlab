# ShiftLab SOTA sprint: execution report

**Date:** 2026-11-03.
**Branch:** `research/sota-sprint-24`, from `origin/main` 2171689.
**Protocol:** [benchmark_spec.md](benchmark_spec.md) and [validation_protocol.md](validation_protocol.md).
The protocol was locked before validation and amended five times.
* Amendments 1–3 were committed before any validation row was read.
* Amendment 4 was registered afterwards and is labelled post-hoc.
* Amendment 5 registers the certificate-host RMM claim before its fresh run. It follows from the ARIS
  result-to-claim review.
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
* **Bounded follow-up loop (§14C).** It ran: Amendment 5 targets the evidence gap that result-to-claim
  named first.
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
| **HC (Amendment 5), RMM on 4 certificate hosts: family < host, late vs best certified (Holm over 8), iid safety, all 4/4** | **PASS** (family −14.5 to −47.2; late −14.6 to −30.3 vs Xu, all Holm p < 1e-6; reversal +3 to +35 for 3 of 4 hosts; ρ=.8 null .12–.18, ρ=.95 null ≈ .71, as declared) |

## 3. Best mechanisms and the evidence for them

1. **RMM on certificate hosts (gated, corrected DISCERN, SMCS; the registered Amendment 5 adds the strong gated re-port).** On fresh seeds (Amendment 5, [amend5_results.md](validation/amend5_results.md)) the results replicate, with family −41.4, −47.2, −14.5 and −32.1.
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

* **SOTA: `SOTA_NOT_MET`** under the brief's full success gate (§14B).
  * The registered, fresh-seed **scoped synthetic SOTA** is now established: RMM attached to four
    certificate hosts beats the strongest certified published comparator (Xu) on late-improvement
    regimes by 15–30 per 2000 events (HC PASS).
  * Gate items 1–4 hold for that scope: advantage, iid-null safety, fresh reproducibility, ablations.
  * Item 5 (credible real-world relevance) is **not met**. The fresh real streams contain no
    late-improvement episode. On them, gated+RMM beats its own host by 48–156 but is mixed against
    the best certified method (2 wins, 3 losses).
  * Item 6 (result-to-claim) is **yes** for the narrowly scoped synthetic claim (re-run after
    Amendment 5). The reviewer still names real-data relevance as missing.
  * The method also loses on reversals and fails persistent nulls, as declared in advance.
* **Main-track candidates** (addendum criteria; the full table is in the [register](publication_register.md)).
  * **P2, MAIN-TRACK CANDIDATE**, recommended first. It is a benchmark and empirical paper on certified
    deployment under serial dependence, framed as an empirical validity-power trade-off on the tested
    Markov family. Result-to-claim rated it *partial* with the revised wording. Missing: a formal
    trade-off argument and known-null real streams.
  * **P1, MAIN-TRACK CANDIDATE**, second. RMM is a transferable extension for certificate hosts, with a
    registered scoped synthetic SOTA on late improvement. Result-to-claim rated it *yes* (narrow).
    Missing: real late-improvement streams, independent generators, and a fix for the reversal cost.
  * **P3–P6:** not supported as standalone contributions, pending evidence. They are kept as findings
    and negative results within P2.
  * "Main-track candidate" means the contribution warrants paper development. It is not a claim of
    acceptance.

## 4b. P2 follow-up: known-null real streams (exchangeable twins)

The protocol ([p2_known_null_protocol.md](p2_known_null_protocol.md)) was registered before any build.
It uses 5 fresh datasets × 20 splits, about 1240 episodes × 3 seeds
([validation/twin_null_results.md](validation/twin_null_results.md)).

* **K1: PASS (9/9).** Every powered certified published port breaks the .0936 bound on real persistent
  known-null streams, at up to .43.
* **K2: FAIL, narrowly.** A5b reaches .000–.058 everywhere, with a bootstrap upper bound of .100 on
  the smallest dataset.
* **RMM (four certificate hosts): .14–.62.** Its iid-null guarantee does not survive real persistence.
* **Qualifier.** Harmful promotions are rare (≤ .07): excess promotions follow the twin that is
  realised better within the episode. The finding is therefore a violation of the marginal
  guarantee with small decision harm. It is not a large economic loss.

## 4c. P1 x P2 merge (Amendment 6): NOT MET

Restart monitoring on A5b's dependence-robust evidence ([merge/merge_results.md](merge/merge_results.md)).

* **Synthetic validity holds.** False promotion is ≤ .016 up to ρ=.95.
* **Real twin-null validity fails.** bike_hour reaches .100 with upper bound .153.
* **Late-change benefit is partial.** V_late_600 is −5.8 vs Xu (significant) and W_late_1000 is −2.0
  (not significant). That is 13–22% of the iid RMM gain retained.
* **Real-data power is poor:** +68 to +207 vs the best certified method.
* **Conclusion.** This is recorded as a further point on the P2 validity-power trade-off. A
  result-to-claim review was not run because no positive claim is made.

## 5. Independent reviews

* **Milestones 1–2.** [review_milestone12.md](review_milestone12.md), by a native Claude reviewer. Its
  objections O1–O14 were handled by Amendment 2 before any validation row was read.
* **ARIS `experiment-audit`, milestone 1.** [aris/m1_EXPERIMENT_AUDIT.md](aris/m1_EXPERIMENT_AUDIT.md).
  Run by Codex `gpt-reserve`, a different model family. Verdict FAIL on gate-audit name pooling, now
  fixed.
* **ARIS `experiment-audit`, milestone 3** ([aris/m3_EXPERIMENT_AUDIT.md](aris/m3_EXPERIMENT_AUDIT.md)).
  * Run 1 was **FAIL**. It audited a mid-run state while Amendment 5 was still executing.
  * Run 2, on the complete state, was **WARN**. It found no fabrication or mismatch and flagged four
    fail-open or provenance weaknesses. All four are fixed.
* **ARIS `result-to-claim`, milestone 3** ([aris/m3_RESULT_TO_CLAIM.md](aris/m3_RESULT_TO_CLAIM.md)).
  * The first pass rated C1 (RMM), C2 (persistence trade-off) and C3 (verdicts) all **partial**, with
    high confidence. The reviewer's revised wordings were adopted as the claims of record.
  * The ARIS `partial` routing then ran the supplementary registered experiment (Amendment 5) and
    re-ran C1. The re-run verdict is **yes**, narrowly scoped to the registered synthetic experiment,
    with high confidence ([raw](aris/m3_result_to_claim_C1_rerun_codex.md)).
* **Independence.** Every ARIS review used Codex (`gpt-reserve`), a different model family from the
  executor. The milestone 1-2 review was a same-family Claude subagent.
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

### Shared adaptive-range correction (2026-11-05)

A source-level audit found a predictable-betting range-ordering defect in the shared adaptive-range
host. The fix is in `strong_hosts.py` and its certificate-stop hook; corrected failure-atlas
validation replays are complete for synthetic and cached-real suites. A same-seed replay of the
1,000-seed, seven-regime null suite is now running at
`outputs/sota_sprint/validation/null1000_wmaxfix_20261105/`. The semantic manifest audit identifies
130 affected execution runs across this report and Sprint 2, plus six aggregate manifests; it
includes aliases for M_RMMSUI_gar, T2/T6 transfers, and Family-C gated controllers. Record-only
directories without manifests are listed separately for provenance recovery. Therefore the original null, B5, fresh
and exposed real, QCE/betting, and out-of-class runs are completed historically, but any comparison
depending on these adaptive-range entries remains provisional until the corrected replays and
downstream analyses finish. See `docs/sprint2/adaptive_gate_impact.md` and the commands in
`docs/sprint2/REPRODUCIBILITY.md`.

* Every comparator is a common-contract port, not author code.
* Development used 20 seeds.
* Real episodes are consecutive windows, so their CIs are optimistic.
* Four of the five part-3 regimes were exposed in Atlas v2, with other seeds.
* Family C held-out seeds shared the null-check base.
* The fresh real streams contain almost no harmful-switch episodes (6/62), so they mostly measure
  promotion cost.
* PaperBanana was not used; no figures were produced.
* `validation_spec.VAL_SEEDS` and `NULL_SEEDS` duplicate literals in the run scripts. This drift risk
  was flagged by the ARIS audit; the values agree (100 and 1000).
