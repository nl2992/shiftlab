# Final decision

**Decision: `BENCHMARK_OR_CASE_STUDY_ONLY`.** The bounded rollback/acquisition pilot is complete.
It found no distinct repair: E_rb and B2 match exactly on all 90 paired episodes; E_rb costs more
than never-switch in all three regimes; alpha tuning, SR/CUSUM and B5 have mixed or confounded
results. The prior-art audit classifies the apparent composition as known. No confirmation gate was
passed, and no holdout was opened. Do not expand the candidate search under this claim.

| Contribution | Status | Evidence and limitation | Smallest next action |
|---|---|---|---|
| 1. Diagnosis | PARTIAL | Corrected simulator/replay suites and the pilot show late-cell label spending and reversal sensitivity; null error depends on the null class. Results are exposed/development evidence and limited to stated simulator contracts. | For a benchmark paper, reproduce the exact environments and report this scope. |
| 2. Explanation | PARTIAL | Cost decomposition and pilot support label-thrift/front-loading explanations and E_rb threshold sensitivity; E_rb=B2 and never-switch is cheaper in all pilot regimes. No novel joint mechanism is established. | Preserve these negative ablations and state the remaining causal-attribution gaps. |
| 3. Repair | FAIL | C2/C6 and front schedules pre-exist; rollback threshold/restart tuning and reserve composition are known. The pilot yields no distinct, practically supported advantage. | Stop the method claim; no additional search is warranted. |
| 4. Validation | FAIL | No fresh synthetic confirmation for a frozen novel method and no authentic independent real-data chronology/source confirmation. | Only for a future, distinct claim: prospectively freeze registry and one-opening runner before holdout access. |

Exact corrected replay artifacts, run hashes, source-cluster intervals and limitations are in
[`CORRECTED_REPLAY_AUDIT.md`](../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md). Pilot
records and results are in
[`07_DEVELOPMENT_RESULTS.md`](07_DEVELOPMENT_RESULTS.md) and
`research/scoped_method/pilots/rollback_acquisition_30seed_20261106/`. The smallest next action for
the benchmark/case-study track is to assemble manuscript tables from these validated records and
retain an independent methods review; no new data acquisition or method search is justified by the
current evidence. PaperBanana's unavailability is recorded in `14_PUBLICATION_CLAIMS.md`.


## 2026-11-06 bounded follow-up addendum

The previously missing direct front-loaded acquisition plus E_rb composition was subsequently run as a 20-seed-per-cell development screen. It failed its stated practical gate: compared with the front-loaded host, savings on `F0_better` were only 3.86 units and unresolved (95% paired interval [-12.35, 4.64]); versus paced E_rb on `V_late_600`, savings were 9.65 but unresolved ([-19.89, 0.59]); under `F3_reversal_800`, it cost 60.65 more than never-switch ([42.52, 78.78]). The independent reviewer recomputed contrasts and cost accounting from all 400 rows and found them consistent. The screen did not establish a new method or justify confirmation. Its protocol was not committed/checksummed before execution and its manifest used a dirty snapshot with truncated hashes, so it is reported as a development result, not an auditable preregistered experiment. Details and all comparator contrasts are in [the economic headroom checkpoint](../../research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md) and the [independent critical review](../scoped_method_research_2026-11-06/DIRECT_FRONTLOAD_ERB_CRITICAL_REVIEW.md). The decision remains `BENCHMARK_OR_CASE_STUDY_ONLY`.
