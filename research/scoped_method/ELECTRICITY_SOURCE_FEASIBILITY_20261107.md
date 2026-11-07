# Electricity-market source feasibility audit (2026-11-07)

**Status: metadata-only source audit. No observations, model predictions, labels, or outcomes were
opened.** This checks whether an electricity-market domain could support a genuinely chronological
external replay. It does not confirm a method or authorize an evaluation run.

## EIA-930: promising event and label chronology, but version capture is unresolved

EIA-930 covers hourly grid operation reported by U.S. balancing authorities (BAs), with demand,
day-ahead demand forecasts, generation, and interchange. EIA provides historical submissions
through downloads/API; the API and interactive history start in 2019, while flat-file submissions
extend to the beginning of collection. EIA documents that demand is typically available one hour
after an operating hour, and the day-ahead demand forecast is typically available by 11:00 a.m.
Eastern. These are useful inputs and target timings for paired load-forecasting models.

The chronology is not automatically point-in-time safe. BAs report in different local zones, some
do not observe daylight saving time, and EIA states that the demand values collected after the hour
and again at 7 a.m. the next day may differ. Respondents may later correct historical values. The
current API has no update field and directly accesses databases that EIA says are updated
continuously, not at regular intervals. A present-day download therefore cannot stand in for the
historical value version available at a past decision time. Before model construction, we would need
either an archived submission/version feed with verifiable timestamps or a separate archived
historical snapshot collection; absent that, this is ineligible for strict real-time replay.

There are multiple BAs, but they share the U.S. grid, weather shocks, and national policy. They
cannot be treated as independent source clusters merely because the reporting entity differs.
Useful target panels would likely be BA-level demand forecast errors, with time blocks and
interconnected-region clusters respected. Several BAs have documented forecast/actual comparability
issues tied to commercial scheduling arrangements, so any registry must exclude or separately
stratify them before the outcome window is inspected.

## ENTSO-E: broad geographic coverage, access and revision provenance unresolved

ENTSO-E's Transparency Platform publishes load, generation, transmission, and balancing data
submitted by European data providers under the EU transparency regime. The official platform page
states that it launched in 2015 and that data from 2011–2014 are also available. This offers a
potentially distinct regulatory and market domain, as well as many reporting zones.

The platform requires additional chronology checks. Data providers can submit corrections, so the
latest value is not necessarily the value visible at the historical decision time. Although platform
documentation is more promising than initially established: its official consumer manual says the
platform interface can show the submission date/time and older versions, and that viewing the
platform does not require registration. The ENTSO-E FAQ confirms that providers may submit updates,
including past values, at their discretion; the platform does not itself know which local changes
have not been submitted. This is a concrete route to reconstructing published information sets,
provided the chosen products and zones actually retain usable versions. The REST API/data download
does require a registered user, and this audit did not request credentials or download data. The
next eligibility step can inspect a small, preselected load product through the public interface,
record version timestamps, then determine the permitted reproducible extraction route.

Official chronology sources: [ENTSO-E Manual of Procedures, consumer registration and version
history](https://www.entsoe.eu/Documents/MC%20documents/Transparency%20Platform/MOP/00_ENTSO-E%20Manual%20of%20Procedures_V2R1.pdf)
and [ENTSO-E Transparency Platform FAQ, updates](https://www.entsoe.eu/Documents/MC%20documents/Transparency%20Platform/Transparency_platform_FAQ.pdf).

## Decision and source registry status

| Source | Independent domain potential | Chronology evidence | Current status |
|---|---|---|---|
| EIA-930 | U.S. electricity operations; BAs are correlated subclusters | Operating-hour and forecast availability schedules documented; revisions acknowledged; historical point-in-time snapshots not yet established | Promising, not eligible yet |
| ENTSO-E Transparency Platform | European electricity market, distinct from U.S. macro and grid governance | Official manual documents public-interface submission timestamps and older versions; provider corrections are discretionary; selected-product retention and reproducible extraction remain to be checked | Strong candidate, not yet eligible |

Official sources checked: [EIA-930 data description and availability](https://www.eia.gov/electricity/930-content/about.html),
[EIA API update behavior](https://www.eia.gov/opendata/faqs.php), and
[ENTSO-E Transparency Platform](https://www.entsoe.eu/data/transparency-platform/).

No observations were accessed. The next safe step, if a synthetic candidate later passes its frozen
gate, is a metadata/schema-only check for retained versions and access terms on one EIA BA panel and
one ENTSO-E load series. Proceed to feature/prediction construction only if historical versions
support the claimed decision-time information set. If not, reject the source for this purpose rather
than treating the final corrected series as historical truth.

## Relation to the current method decision

The frozen CUSUM evaluation failed its practical cost gate against the strongest applicable
comparators and failed the adverse-regime harm gate. This source audit does not reverse those
results. The ALFRED audit remains another metadata-only route, with several U.S. macro series but
only one national economy. Neither data route currently supplies real-world confirmation for a
repair.
