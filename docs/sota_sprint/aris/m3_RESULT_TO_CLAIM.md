# Result-to-claim review, milestone 3 (ARIS `result-to-claim`, cross-model)

**Date:** 2026-11-03.

**Reviewer:** Codex CLI with `gpt-reserve` at medium effort, run read-only. It reported `Reviewer-Model: gpt-5`.

**Executor:** claude-opus-5-5.

**Skill:** ARIS `result-to-claim`, SKILL.md at f76ec8d.

**Evidence pre-check (Step 1.5):** all 12 cited numbers were verified (`.aris/traces/sota-sprint/2026-11-03_m3/precheck.json`).

**Raw response:** [m3_result_to_claim_codex.md](m3_result_to_claim_codex.md).

**Integrity status:** see the milestone-3 experiment audit, [m3_EXPERIMENT_AUDIT.md](m3_EXPERIMENT_AUDIT.md).

| claim | verdict | confidence | adopted revision |
|---|---|---|---|
| C1, RMM transfer (P1) | **partial** | high | "On fresh synthetic seeds, RMM substantially lowers cost when attached to three tested certified deployment hosts and improves late-improvement cost relative to Xu, while preserving IID-null first-promotion control. These gains are specific to the tested certificate hosts and late-improvement regimes; transfer to arbitrary hosts, robustness to persistent dependence, reversal performance, and real-data late-improvement behavior remain unestablished." |
| C2, persistence trade-off (P2) | **partial** | high | "In the tested stationary Markov marginal-null family, most powered certified ports violate the registered false-promotion bound somewhere between rho=.8 and .95, whereas A5b remains below the bound on the tested grid and two descriptive out-of-class nulls. This robustness is purchased with a substantial loss of power/cost performance on the tested real streams. The results demonstrate an empirical validity-power trade-off, not a general theorem about unknown persistence." |
| C3, verdicts | **partial** | high | "The sprint verdict is SOTA_NOT_MET. P2 is the strongest empirical paper candidate, and P1 is a promising but currently synthetic, narrowly scoped method candidate. P3 and P4/P6 should be described as unsupported as standalone contributions pending additional evidence; P5 is not supported as a standalone contribution." |

## Routing (ARIS Step 4, `partial`)

1. **Update the working claims.** Done: the revisions above replace the register and report wording.
2. **Run supplementary experiments.** The reviewer's first experiment for C1 ("Register the narrower
   three-host claim before rerunning it. Add a fourth certified host.") is registered as Amendment 5 and
   run on fresh seeds. Its result is in [../validation/amend5_results.md](../validation/amend5_results.md).
   The remaining gaps cannot be closed with compute in this sprint:
   * C1 has no real late-improvement streams.
   * C2 lacks a formal trade-off argument and has no known-null real streams.
   * Comparators are not run from author code.
3. **Re-run result-to-claim** on C1 after Amendment 5. The re-run is recorded below.
