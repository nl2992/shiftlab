# Elexon BMRS source feasibility audit (2026-11-07)

**Status: bounded raw-API metadata audit passed; no method outcomes were computed.** Public Elexon
endpoints returned historical forecast and actual records with publication times, valid times,
document identifiers, and revision fields. This makes the source a stronger point-in-time replay
candidate than a latest-value-only dataset. It does not yet make it eligible for confirmation: the
data window, model pair, and method protocol still need to be frozen, and source-level replication
is one system operator.

## Candidate data and chronology

Elexon's Balancing Mechanism Reporting Service documents total-load actual (ATL) and day-ahead
total-load forecast (DATL) datasets. The stream endpoints expose publication and valid-time fields,
including `publishTime`, `startTime`, settlement date/period, quantity, and a document revision
number. The API documentation describes `publishDateTime` filters, which may support reconstructing
the information available at a prediction cutoff. Elexon states that actual load is published no
later than one hour after the settlement period; its service page describes a day-ahead forecast
publication deadline before gate closure. These are promising source-level chronology semantics,
not yet verified by a retained response or historical vintage replay.

Official references:

- [ATL stream API](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/ATL/stream)
- [DATL stream API](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/DATL/stream)
- [Total load actual and day-ahead forecast service page](https://bmrs.elexon.co.uk/total-load-actual-and-day-ahead)
- [Actual total load endpoint](https://bmrs.elexon.co.uk/api-documentation/endpoint/demand/actual/total)
- [Balancing Mechanism Reporting Agent requirements](https://bscdocs.elexon.co.uk/bsc-module/user-requirements-specifications/balancing-mechanism-reporting-agent)

The official documentation UI is JavaScript-rendered, but the documented schema was verified
against the raw API. The API uses `publishDateTimeFrom` and `publishDateTimeTo` query parameters and
returns JSON records. It did not require authentication for these requests.

## Bounded raw-response audit

On 2026-11-07, `https://data.elexon.co.uk/bmrs/api/v1/datasets/{DATL|ATL}/stream` was queried with
publication-time windows for 2023-01-01, 2024-01-01, 2025-01-01, and 2026-01-01 (each one UTC day).
The following were observed:

| Dataset/window | Rows | Distinct valid times | Versions/revision fields | Response SHA-256 |
|---|---:|---:|---|---|
| DATL 2023-01-01 | 0 | 0 | none | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| DATL 2024-01-01 | 48 | 48 | one document, revision 1; published 12:00:08Z for 2024-01-02 | `61d2fa9f238be208022d5b4e65c8a4a3ca741da376cd964bb2018e099065221f` |
| DATL 2025-01-01 | 48 | 48 | one document, revision 1; published 12:00:06Z for 2025-01-02 | `d73519a1665b8669d1f931817eb38331910bbeb2c189f18e0244826ecec519d5` |
| DATL 2026-01-01 | 0 | 0 | none | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| ATL 2023-01-01 | 0 | 0 | none | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| ATL 2024-01-01 | 48 | 48 | 48 documents, revision 1; 00:25:09Z–23:55:08Z | `4efaf6df1c4ca8f2ca1a11a99672ffe082071d90ac3d7cbde73819ad09a254ed` |
| ATL 2025-01-01 | 48 | 48 | 48 documents, revision 1; 00:25:06Z–23:55:06Z | `de957aeeccdabdf67c82cb314311650213fa86ab773584d6c0962e1a79c936c2` |
| ATL 2026-01-01 | 48 | 48 | 48 documents, revision 1; 00:25:06Z–23:55:05Z | `8c5341df21a3ab7e604be6aaf4083285616f0b09cdf3216da65f13808dabab8e` |

Empty windows on 2023-01-01 and 2026-01-01 apply to the *publication-time query window* and are
not evidence that the dataset lacks those years. A separate coverage audit is required.

Spot coverage probes returned zero rows for both ATL and DATL on 2022-06-01 and 2023-06-01, but
48 rows for each on 2023-11-01 and 2024-06-01. This supports a possible late-2023 training start,
but it is not a coverage guarantee; exact onset, gaps, and retention need a bounded registry audit
before any model pair is frozen. The four 2023-11-01/2024-06-01 response hashes are ATL
`27616afc8f5e04738f0a684e1430384f40d87e001f833d5adec1d387df7d2a5e` and
`9eaf66265084103f7ee818c4b4cbd639d73fb153a247a4706c7bfa05015a4082`, DATL
`0b58ed8e8a65fa90fb0bec0651feb30070f99b03b37f0935015a96cebed5abad` and
`f50eb26ba772bdc4e444e631b0e4b0386f71d67ec42c301cbfae590984298d12`.

A second audit queried the full January 2025 publication window. DATL returned 1,392 records for
1,344 valid times and 29 documents; ATL returned 1,489 records for 1,485 valid times and 1,489
documents. Every observed `documentRevisionNumber` was 1, but some valid times appeared in multiple
documents. For example, the DATL records for 2025-01-21 were published in separate documents at
09:00:06Z and 12:00:06Z on the prior day; ATL had duplicated valid times with later publication
times. Thus `documentRevisionNumber` alone is not a sufficient vintage key. A replay must order by
`publishTime` and preserve `documentId`, and select only the latest record actually available by
its decision cutoff. The full-month response SHA-256 values were `120692db696b6d9d464369778a41e01eb20d31572033a4731302c2dd3f34dcac` (DATL) and `5568f5453a10e68b27466df9ebcc909efff5ff5f2c022b4e13b98698746d8eae` (ATL).

Daylight-saving edge checks confirm that fixed 48-row local-day assumptions would be wrong. For
ATL publication windows on 2024-03-31 and 2024-10-27, the API returned 46 and 50 valid times,
respectively; adjacent sampled days returned 48. On 2024-03-31, DATL contained three daily forecast
documents (09:00:09Z, 12:00:09Z, and 15:00:09Z) for the same 48 valid times. UTC `startTime` plus
publication/document metadata is therefore required for alignment and vintage selection. The
sampled response SHA-256 values are:

| Dataset/window | Rows | Documents | Response SHA-256 |
|---|---:|---:|---|
| ATL 2024-03-31 | 46 | 46 | `e48ad9b91216c262482fbf24029f95db5ee17c89783f60976af2dc0b6d5d35e5` |
| ATL 2024-04-01 | 48 | 48 | `6348e27781035c727052293ff4e5c6b944cb38e9a0b65c003d86dba216d6e9f7` |
| ATL 2024-10-27 | 50 | 50 | `f45ffd5ef97952ba2ef7db61dc9dc6545d555e61e6c119c2f42b1c4ce329d4` |
| ATL 2024-10-28 | 48 | 48 | `465131f3bf35ae7e04095dcf473f4cec2392ba2049cbd0eb9c22838f11d990cb` |
| DATL 2024-03-31 | 144 | 3 | `c3f5605f213e1fac5b214adf02e63db8003ca169fdefa4a211acc0d7a1eb68d9` |
| DATL 2024-04-01 | 48 | 1 | `caa6723d295d2e7add3d0150cf798f4f087af3aa7ea0843d3930e203cc1d2c84` |
| DATL 2024-10-27 | 48 | 1 | `11c64cec5b3b29c8a3526885542335c0bc390a3f25ea56806f950617a965de98` |
| DATL 2024-10-28 | 48 | 1 | `1a843397896d995353249e69e674fc82e2eb63f8e75744f0b292962e7602ec33` |

For the 48 ATL rows published on 2025-01-01, publication occurred about 25 minutes after the
settlement interval end (the API's `startTime` plus 30 minutes). This empirically supports a delayed
label schedule for those sampled intervals. It is not a full guarantee across all dates, daylight
saving transitions, missing periods, or later corrections.

## Eligibility gates before any outcome evaluation

1. Audit coverage, empty windows, daylight-saving transitions, and missing periods over a proposed
   chronological registry.
2. Define vintage selection on `publishTime` plus `documentId` (not just revision number), and
   verify forecast versions available at a frozen decision cutoff. Later reports must not leak into
   predictions.
3. Verify actual-label release timing and duplicate/correction handling over that registry; encode
   delayed or missing labels explicitly.
4. Verify historical coverage and then freeze one chronological train/development/confirmation
   registry and a real model-pair protocol. Any pair must be trained only on data available before
   its prediction window.
5. Keep costs explicitly hypothetical unless an application supplies defensible utility and label
   costs. A single system operator remains one independent source cluster; many settlement periods
   do not create independent source-level replication.

## Current decision

Reproduce the bounded schema, vintage, DST, coverage, and response-hash audit (13 fixed UTC windows
for each dataset) with:

```bash
python3 research/scoped_method/audit_elexon_metadata.py
```

The script reports counts and timestamps only; it does not save or print load quantities.

Elexon is a promising independent-domain candidate relative to U.S. EIA-930, but it is not yet an
eligible real-data confirmation source. The immediate next action is a bounded schema/vintage audit,
not a method outcome run. This source lead does not reverse the existing negative repair gates or
the current `BENCHMARK_OR_CASE_STUDY_ONLY` decision.
