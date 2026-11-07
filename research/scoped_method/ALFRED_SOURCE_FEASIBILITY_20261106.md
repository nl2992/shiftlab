# ALFRED as a point-in-time chronological source for a model-switching replay

**Status:** source-route feasibility only. A tiny public export was downloaded to verify the route; no observation values or README contents were opened, no outcome analysis was run, and no candidate method was evaluated.

## Why this source is a better lead

ALFRED provides historical vintages so a replay can reconstruct the value available at a past point, rather than training on current revised values. Its official documentation says the archive adds real-time periods for when values were originally released and later revised; ALFRED can return initial-release-only data and observations by vintage date. It also documents release dates and says the database is normally updated within one business day after a source release. See:

- [ALFRED overview](https://fred.stlouisfed.org/docs/api/fred/alfred.html)
- [ALFRED help: release-date provenance](https://alfred.stlouisfed.org/help)
- [Download Data Help: vintages and initial releases](https://alfred.stlouisfed.org/help/downloaddata)
- [UNRATE series page](https://alfred.stlouisfed.org/series?seid=UNRATE)

The UNRATE series page identifies the Bureau of Labor Statistics' Employment Situation release and lists monthly coverage and release-date history. This is a plausible chronological source for predicting the direction of a future monthly value with a release-day action time and a subsequent release-day label event.

## Fit to the Failure Atlas question

A small first task could freeze two classifiers to predict the sign of the next initial-release change in UNRATE from macro values available in the current vintage. Each action would occur on a published release date; the label for event t would arrive when the next target release is published. Release-day batches prevent fabricated within-day ordering. Predictor values must be reconstructed using vintages available by the action date; the target must use an explicit first-release definition so later revisions do not leak backwards.

This is a plausible real-data test of late improvement and scarce/delayed labels. It is not yet a candidate method or a positive environment: the dataset may show no paired model-comparison headroom, monthly sample size is limited, UNRATE is one source series, and the published release date can be a provider/database date rather than the exact public-availability time. Outcomes may also overlap across adjacent forecast events and require block-level uncertainty.

## Access and protocol constraints

The FRED API documents a registered API key requirement. This checkout has no `FRED_API_KEY` or `ALFRED_API_KEY` in its environment. A bounded source-route test confirmed that the public UNRATE form can return zipped CSV without an API key. The request for `Observations, Initial Release Only` with one vintage was correctly rejected because that output needs at least two releases; `Observations by Vintage Date, All Observations` with vintages `1960-03-15` and `1960-04-12` succeeded for a short 1960 observation range. The ZIP was 2,231 bytes and SHA-256 `a0e99ad35ba0f723907ebeac0f1fc0855d4745c524d8db80948ddf097d2398d9`; its member listing was README plus a 103-byte vintage CSV. I did not read the CSV or README contents. Temporary download and cookie files remain in `/tmp`; no series data was added to Git.

Before data access, a protocol should freeze:

1. series registry, source agency, vintage and first-release rules;
2. prediction and label batch timestamps, including how releases on the same date are ordered;
3. frozen incumbent/challenger training and vintage-safe feature construction;
4. the selected Failure Atlas operating region, paired label budget/cost and switching-cost convention;
5. strongest applicable published online model-selection and sequential monitoring baselines;
6. a development/confirmation cutoff and source-level/time-block uncertainty method.

The first go/no-go is whether the download workflow can provide raw vintage/release records with stable checksums and reconstruct features strictly as of each action date. Only then should any labels be opened for development. If the API-key/download requirement cannot be satisfied, no ALFRED model experiment has begun and no performance claim is warranted.
