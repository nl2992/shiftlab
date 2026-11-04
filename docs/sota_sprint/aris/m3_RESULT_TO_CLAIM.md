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

## C2 re-run after the known-null real experiment (2026-11-03)

**Verdict: partial**, medium confidence ([raw](p2_result_to_claim_rerun_codex.md)).

**What it supports:**
* Synthetic: 9/9 powered ports break the bound.
* Twin-null real K1 holds at 9/9, with rates up to .43.
* Harm is small.

**Corrections:**
1. K2 failed narrowly.
2. RMM is near zero on metro; .14–.62 is its range on the other persistent datasets.
3. A5b's power loss is not uniform. It still promotes about 1.0 on bike_hour and .94 on metro, where it
   loses through latency. The power loss is heavy on appliances, beijing and household_power.

**Adopted claim of record:**

> In the tested synthetic stationary Markov marginal-null family, all 9 powered certified ports
> exceeded the registered .0936 false-promotion bound at one or more tested persistence levels between
> .8 and .95, whereas A5b remained below it in those simulations. In five exchangeable-twin real-stream
> experiments, every powered certified port exceeded .0936 on at least one persistent dataset, with
> rates up to .43; RMM variants also showed elevated promotion on several datasets, up to .62. A5b had
> lower point estimates (0–.058), but its clustered-bootstrap upper bound exceeded .0936 on the smallest
> dataset. Most promotions were toward the twin with lower realised episode loss, so the
> marginal-validity failures generally had small realised decision-cost impact. Separate fresh-real
> experiments show substantial A5b power/cost loss on some, but not all, streams with empirically better
> challengers. Together, these results provide scoped empirical evidence of a validity–power trade-off
> for certified deployment under serial dependence; they do not establish a theorem or universal method
> ranking.

**Next experiments named:**
* More independent persistent datasets and split units.
* A registered power study with randomised, genuinely better challengers.
* Sensitivity to episode length and delay.
* A dependence-robust certificate without A5b's power loss.
