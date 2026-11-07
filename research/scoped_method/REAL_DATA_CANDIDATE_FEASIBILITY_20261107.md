# Real-data candidate feasibility — 2026-11-07

## Status

Metadata-only source triage. No archive was downloaded or opened, no model predictions were
generated, and no outcomes were inspected. This does not qualify as real-data validation.

The synthetic economic and novelty gates for a new repair have not passed. Therefore this source
is a prospective candidate only; it must not be opened as confirmation under the current protocol.

## Candidate: UCI ElectricityLoadDiagrams20112014

- Official source: https://archive.ics.uci.edu/dataset/321/electricityloadformatting
- DOI: `10.24432/C58C86`; stated license: CC BY 4.0.
- The repository describes 370 client series, 15-minute consumption measurements, and explicit
  date-time strings spanning 2011–2014. The listed raw file is 678.1 MB.
- Potential fit to Failure Atlas M1: chronological train and replay windows can be formed without
  using future records for preprocessing or model fitting. Client series offer source-level
  structure; common calendar and market shocks still induce dependence across clients.
- Known limitation: the source documentation does not establish when each consumption label
  becomes available to a decision-maker. A replay would need an explicit simulated release delay
  and must not call it authentic delayed feedback.
- Additional design issue: clients began contributing at different dates; zero-filled pre-entry
  values documented by UCI must be treated as missing/not-at-risk history, not as observed zero
  consumption for fitting or scoring.

## Eligibility decision

This source is promising for a later chronological model-pair replay with source-level uncertainty,
provided the development and novelty gates first pass. Any later analysis must use point-in-time
feature/label windows, a predeclared target regime, identical query and switch costs, and
cluster-aware uncertainty that accounts for both clients and common time blocks. It is not a
substitute for the currently missing positive method result or independent confirmation.

## Source checked

Official UCI metadata viewed 2026-11-07: https://archive.ics.uci.edu/dataset/321/electricityloadformatting.
The metadata state the sample frequency, number of clients, timestamp format, file size, license,
and the client-entry / daylight-saving conventions summarized above. No local raw archive was
present in `data/raw/` at this checkpoint.
