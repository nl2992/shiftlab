# Independent critical review

**Reviewer role:** internal, read-only research audit; 2026-11-06. This is an independent review within the project, not external peer review. I reviewed the scoped-research artifacts, the corrected replay audit, relevant historical reports, and the bounded rollback/acquisition pilot. No untouched real holdout was opened. This review does not validate a theorem or independently rerun the analyses.

## Decision

The evidence supports **`BENCHMARK_OR_CASE_STUDY_ONLY`**. It does not support a new method contribution or independent real-world transfer. The bounded pilot strengthens the negative decision: it finds no stable improvement from the rollback/acquisition variants tested, and the straightforward E_rb composition is already represented in the repository. This is a bounded rejection of the tested proposal, not evidence that no useful method can exist.

## Four contribution gates

| Contribution | Review status | Evidence and limitations |
|---|---|---|
| **1. Diagnosis** | **PARTIAL** | Failure Atlas and corrected Sprint 2 replays make late-improvement cost, promotion behavior, and synthetic reversal/rollback behavior reproducible under specified simulator contracts. Corrected adaptive-range replays repair a consequential implementation defect. However, the exposed real streams are constructed paired-loss replays with imposed label delays; real episode classes are retrospective, not causal or online-observable regimes. This supports a scoped benchmark diagnosis, not a real-world operational diagnosis. See `docs/scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md`, `docs/scoped_method_research_2026-11-06/FAILURE_ATLAS_UPDATE.md`, and `docs/scoped_method_research/02_FAILURE_ATLAS_UPDATE.md`. |
| **2. Explanation** | **PARTIAL** | Existing controls and replay traces support a cost-allocation explanation for several late synthetic cells: C2/C6 reduce label spend while promotion remains at 0–1%; front-loading explains a substantial part of gains against unmodified Gated. The pilot further shows alpha sensitivity and detector-dependent reversal outcomes, with never-switch cheaper on all three sampled regimes. But some pilot contrasts change multiple components (`E_srr_noacq`, B5), there is no rollback truth/error decomposition in the pilot report, and 30 seeds over three reused regimes cannot establish broad mechanism generality. E_rb is identical to B2 on the reported paired rows, which is a fidelity/identity result rather than new mechanism evidence. |
| **3. Targeted repair** | **FAIL** | No new repair was frozen, implemented, and shown to beat the strongest matched comparator in a prespecified region. The proposed reserve/front-load/E_rb combination uses existing components; prior-art review classifies the core as known composition or incremental and novelty unverified. In the pilot, E_rb loses to never-switch in every tested regime; alpha .05 helps one reversal regime, is unresolved in another, and costs in recurrent shift. CUSUM/SR results are mixed and have differing error criteria. The pilot did not include a direct front-loaded-plus-E_rb policy, a sufficiently tuned E_rb threshold/start-grid family, a full matched acquisition factorial, or a matched guarantee/error comparison. These omissions prevent a strong claim that the entire design space is exhausted, but do not rescue the current repair claim. |
| **4. Validation** | **FAIL** | There is no fresh-seed confirmation of a frozen method and no eligible untouched real-world evaluation. The 14 source-cluster real replay is exposed, retrospectively generated, uses proxy paired predictions and imposed delays, and includes related sources. Its source-level interval is correctly described as retrospective rather than independent transfer. Wild-Time timing documentation is insufficient for authentic delayed label chronology; OPSD/Binance holdouts remain locked. |

## Statistical and source-independence audit

The package generally separates iid conditional nulls from dependent/marginal stress cases and economic cost, and correctly notes that empirical null rates do not prove an anytime guarantee. Continue to describe E_rb's conditional guarantee only under its actual filtration and assumptions. E_srr/SRR's ARL interpretation is not equivalent to a per-horizon false-alarm bound; pilot cost differences do not establish equal risk. The 0/1000, 1/1000, and 1/1000 iid-null promotion figures are empirical rates with sampling uncertainty, not proofs of nominal control. Out-of-class stress rates should not be presented as violations of an in-class theorem, nor omitted when discussing robustness.

The real-data analysis appropriately uses source-level rather than episode-level intervals, but the 14 units are *dataset-source clusters in an exposed replay*, not 14 independent untouched domains. Any summary must retain the exposure and dependence caveat. The small number of clusters also makes a t interval fragile; report source effects and treat the interval as descriptive. Do not call the five-source `real_fresh` cohort “fresh confirmation”: fresh refers to its replay cohort/seed lineage, not an untouched data source or protocol.

## Bounded pilot adequacy and interpretation

The pilot is methodologically adequate as a **development falsification screen**: it states the regimes, seeds, common contract, code/data artifact hashes, paired contrasts, and non-confirmatory status; it discloses adverse regimes and information limits; and it keeps holdouts closed. Thirty paired seeds per reused regime can reveal large instability, but paired t intervals are exploratory and do not address prior selection, multiple contrasts, or population transport. Combining the three regimes into a population interval would be invalid; the report correctly presents them separately.

It is not an adequate confirmatory baseline-fidelity or novelty experiment. In particular, the written mechanism proposal names front-loaded acquisition plus E_rb as the candidate, while the executed policy list does not include that combination. E_rb's alpha comparison changes alpha only, but no start-grid/threshold tuning is matched, although historical reports identify start-grid sensitivity. CUSUM/SR are not calibrated to a common in-scope false-alarm criterion, and the pilot explicitly reports no per-rollback correctness classification. B5 changes reserve, rollback, and deadline together; `E_srr_noacq` changes detector and acquisition together. Thus it can reject the specific simple proposal as currently motivated, but cannot isolate every component or show superiority against the strongest fully tuned, equal-validity published comparator. The report's closing recommendation to stop this development branch is justified; wording should remain “no distinct candidate identified in this bounded screen,” not “all plausible repairs were tested.”

## Claim corrections and smallest next action

1. Preserve the decision as **`BENCHMARK_OR_CASE_STUDY_ONLY`**, with C1/C2 **PARTIAL**, C3/C4 **FAIL**. Do not promote a method claim from the corrected replays or pilot.
2. Keep all real replay contrasts explicitly labeled exposed, constructed, and retrospective. Do not infer independent transfer from the combined 14-source interval.
3. Keep risk claims tied to the exact null, release-time filtration, query predictability, and alpha allocation. Do not use a cost advantage as evidence of certificate validity.
4. The smallest next action for a *method* claim is not to open a holdout. First decide whether to stop the current branch (recommended) or authorize one new, prospectively bounded development question. If continuing, the minimum useful design is a direct, paired comparison of the named joint policy against a tuned E_rb start-grid/alpha baseline and calibrated two-sided SR/CUSUM, with acquisition held/matched, rollback truth and in-scope null errors reported, and a prespecified practical margin. Only a surviving non-separable effect plus a defensible novelty delta should trigger a new freeze and untouched evaluation. For the current case-study paper, the smallest action is to finalize the manuscript outline with the negative results and corrected-replay provenance; no holdout access is needed.

## Artifacts reviewed

- `docs/scoped_method_research/00_STATE_AUDIT.md`
- `docs/scoped_method_research/02_FAILURE_ATLAS_UPDATE.md`
- `docs/scoped_method_research/03_PRIOR_ART_AND_NOVELTY.md`
- `docs/scoped_method_research/04_BASELINE_FIDELITY.md`
- `docs/scoped_method_research/05_MECHANISM_PROPOSALS.md`
- `docs/scoped_method_research/06_DEVELOPMENT_PROTOCOL.md`
- `docs/scoped_method_research/07_DEVELOPMENT_RESULTS.md`
- `docs/scoped_method_research/08_FROZEN_CONFIRMATION_PROTOCOL.md`
- `docs/scoped_method_research/09_SYNTHETIC_CONFIRMATION.md`
- `docs/scoped_method_research/10_REAL_DATA_REGISTRY.md`
- `docs/scoped_method_research/11_REAL_DATA_CONFIRMATION.md`
- `docs/scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md`
- `docs/scoped_method_research_2026-11-06/FINAL_ASSESSMENT.md`
- `docs/scoped_method_research_2026-11-06/MECHANISM_ABLATION.md`
- `docs/scoped_method_research_2026-11-06/METHOD_SPECIFICATION.md`
