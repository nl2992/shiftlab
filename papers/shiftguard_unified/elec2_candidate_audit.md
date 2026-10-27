# ELEC2 public benchmark candidate audit

**Audit date:** 2026-10-26  
**Decision:** retain as a possible exploratory classification benchmark; exclude from final online or decision-utility confirmation.

## Source and integrity

OpenML lists dataset 151, `electricity`, version 1, as public ARFF data, with 45,312 rows and the normalized electricity benchmark schema. Its metadata gives the original source page as `http://www.inescporto.pt/~jgama/ales/ales_5.html`, which is currently unavailable to this audit. The downloaded file was `https://www.openml.org/data/download/2419/electricity-normalized.arff`. Its MD5 is `8ca97867d960ae029ae3a9ac2c923d34`, exactly matching OpenML metadata; the audited SHA-256 is `2d86fbc74c69a5c04bcede0119bce280dd6d8efa0115987edc75b77ccf024d7f2`.

The ARFF schema is `date`, `day`, `period`, `nswprice`, `nswdemand`, `vicprice`, `vicdemand`, `transfer`, and `class`. The target is `UP`/`DOWN`; counts are 19,237 and 26,075. The file contains 45,312 rows, 3,092,013 bytes, and no invalid or nonfinite numeric cells. OpenML marks the licence as “Public”; this is metadata, not a verified source-specific redistribution grant.

## Chronology and integrity findings

The available `date` and `period` columns do not define a trustworthy unique event key:

- `date` is a normalized numeric field from 0 to 1 with 933 distinct values, rather than a documented timestamp.
- There are 528 duplicated `(date, period)` groups, containing 528 excess rows. These are not exact full-row duplicates; their market fields or labels differ.
- File order has five decreases in the `date` field, 943 within-file period resets, and 44,369 adjacent pairs with the same normalized date value.
- The downloadable normalized file reproduces the known duplicated block: `(date=0.442326, period=0)` occurs at zero-based row indices 17,376 and 17,424. The records are not identical.

An independent public audit reports a duplicated 48-observation day and advises dropping the date/day fields and the duplicated block. That recommendation does not repair the 528 ambiguous date-period groups observed in this exact OpenML file, so we do not apply that cleaning rule as if it restored verified chronology. See [ELEC2 data audit](https://el-hult.github.io/2023/12/21/elec2.html). The official MOA catalogue describes 45,312 half-hourly observations and the binary moving-average direction target, but does not resolve these row-level timestamp ambiguities ([MOA dataset catalogue](https://moa.cms.waikato.ac.nz/datasets/)).

## Research suitability

ELEC2 could support an offline common-label classifier comparison or a carefully labelled exploratory row-order replay. The label is a market-price direction benchmark target; it does not identify executable trading returns, counterfactual policy outcomes, or a source-grounded decision cost. An imposed false-positive/false-negative cost would measure a declared classification decision loss only. The normalized features also need a feature-time audit before assigning them to a learner filtration.

The benchmark therefore cannot close the project's real-data gate for online monitoring, sequential detection delay, or cost-aware intervention. It supplies no verified event/release clock, costs, causal action outcome, or clean independent confirmation split in this repository. It is not a replacement for the existing EIA/CRSP retrospectives, which have their own documented limits.

Raw data are retained locally at the ignored path `data/raw/elec2/electricity-normalized.arff`; they were not added to the repository's canonical dataset inventory or Git history. The captured aggregate audit is at `outputs/shiftguard_unified/real_data_development/elec2_integrity_v1/audit.json`. Reproduce it with:

```powershell
uv run python scripts/audit_elec2_candidate.py data/raw/elec2/electricity-normalized.arff --output outputs/shiftguard_unified/real_data_development/elec2_integrity_v1/audit.json
```

The script emits aggregate metadata and example duplicate keys, not the dataset rows. No plots or predictive experiments were produced.

