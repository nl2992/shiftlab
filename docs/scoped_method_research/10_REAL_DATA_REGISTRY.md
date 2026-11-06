# Real-data registry and eligibility

No source in this table supplied independent confirmation evidence during this execution.

| Candidate/source | Chronology and potential role | Exposure / eligibility limitation | Status |
|---|---|---|---|
| Existing UCI-derived and repository streams (metro, Beijing PM2.5, bike, appliances, household power, etc.) | Paired-loss retrospective replay | Previously exposed; constructed model-pair streams; imposed rather than observed label-release delays; overlapping source families | Development/retrospective only |
| Wild-Time HuffPost and arXiv | Chronological text classification tasks, potentially independent sources | Task timestamps do not establish point-in-time model training, prediction chronology or authentic label-release times. Version/checksum and label delay must be frozen. | Candidate only; not run for confirmation |
| OPSD load-reserve task | Hourly time series with external ENTSO-E publication clock | Raw data absent locally; historic handoff reserves holdout pending method freeze and one-opening runner; revisions/vintage and task choice threaten blind transfer | Holdout locked; not run |
| Binance momentum task | Chronological hourly market bars | Raw data absent locally; holdout locked; one-bar label release imposed and fee costs are proxies | Holdout locked; not run |
| UCI Online Retail II | Chronological transaction data | Requires prospective target/model schedule and defensible label-release process; source familiarity/exposure must be audited | Candidate only |
| Other justified time-series domain | To be selected only under frozen method applicability | Must supply source-level independent cluster, training/prediction/label-release timestamps, policy-pair identifiability, license and checksum | Not selected |

The exposed replay's 14 dataset-source clusters are summarized in
[`corrected_real_14_source_clusters.json`](../scoped_method_research_2026-11-06/corrected_real_14_source_clusters.json).
They are not 14 untouched independent domains. Source-level intervals are in
[`CORRECTED_REPLAY_AUDIT.md`](../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md).
Dataset dates alone do not establish causal change time or availability of labels. No favorable
episode may be retrospectively selected as an independent source.

## 2026-11-06 append-only status update

The Wild-Time HuffPost candidate was later source-audited and opened once for the registered
published PFA-SR transfer case study; arXiv remains unopened. HuffPost passed the frozen validation
gate, while UCI News Aggregator and MN-DS did not and stayed locked. The test result is adverse to
PFA-SR: on one HuffPost source cluster with simulated 24-hour feedback, PFA-SR cost more than
same-host RMM and Xu acquisition-only. This updates the table's historical “not run for
confirmation” line without changing its warning that the replay is not authentic label-release
confirmation or independent multi-source transfer. Details: `../scoped_method_research_2026-11-06/REAL_DATA_AUDIT.md`.
