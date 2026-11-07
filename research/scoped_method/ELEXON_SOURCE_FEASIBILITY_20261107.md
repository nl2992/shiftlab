# Elexon BMRS source feasibility audit (2026-11-07)

**Status: official-documentation lead only. No data were downloaded and no outcomes were
computed.** The documentation identifies a potentially useful independent chronological
electricity-market source. This note does not make it eligible for confirmatory evaluation.

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

The endpoint pages could not be inspected as static page text in this audit because the current
documentation UI is JavaScript-rendered. The field and release details above are a source lead
from the official documentation, and must be rechecked against a raw, versioned API response before
any model or method outcomes are opened.

## Eligibility gates before any outcome evaluation

1. Verify API access and capture a small metadata-only response for preselected historical periods.
   Record request parameters, response schema, retrieval time, and checksums.
2. Establish that the first forecast revision available by a frozen decision cutoff can be selected
   from `publishTime` and revision metadata. Later revisions must not leak into predictions.
3. Establish actual-label release time from the corresponding publication metadata; represent
   delayed or missing labels explicitly.
4. Freeze one chronological train/development/confirmation registry and a real model-pair protocol.
   Any pair must be trained only on data available before its prediction window.
5. Keep costs explicitly hypothetical unless an application supplies defensible utility and label
   costs. A single system operator remains one independent source cluster; many settlement periods
   do not create independent source-level replication.

## Current decision

Elexon is a promising independent-domain candidate relative to U.S. EIA-930, but it is not yet an
eligible real-data confirmation source. The immediate next action is a bounded schema/vintage audit,
not a method outcome run. This source lead does not reverse the existing negative repair gates or
the current `BENCHMARK_OR_CASE_STUDY_ONLY` decision.
