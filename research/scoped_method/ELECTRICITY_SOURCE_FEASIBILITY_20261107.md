# Electricity-market source feasibility audit (2026-11-07)

**Status: source/schema audit with a two-row API smoke inspection.** No model predictions,
loss streams, or method outcomes were evaluated. The official API returned one PJM demand value
and its paired day-ahead forecast for 2025-01-01T01 UTC. This checks source feasibility only; it
does not confirm a method.

## EIA-930: promising event and label chronology, but version capture is unresolved

EIA-930 covers hourly grid operation reported by U.S. balancing authorities (BAs), with demand,
day-ahead demand forecasts, generation, and interchange. The official API route
`/v2/electricity/rto/region-data/data/` exposes hourly UTC records with respondent and type facets;
type `DF` is the day-ahead demand forecast and type `D` is realized demand. A two-row inspection
for PJM at `2025-01-01T01` returned both values, showing that the forecast/target pair is available
through a reproducible public interface. EIA documents that the day-ahead forecast is typically
available by 11:00 a.m. Eastern and demand is typically available one hour after the operating hour.
These provide a defensible **simulated feedback schedule** for chronological model-pair replay.
Historical submissions through the API start in 2019; longer flat-file submissions are available.

The chronology is not automatically point-in-time safe. BAs report in different local zones, some
do not observe daylight saving time, and EIA states that the demand values collected after the hour
and again at 7 a.m. the next day may differ. Respondents may later correct historical values. The
current API has no update field and directly accesses databases that EIA says are updated
continuously, not at regular intervals. A present-day download therefore cannot stand in for the
historical value version available at a past decision time. The data are eligible for a replay only
under an explicit **simulated-feedback contract**: use the current historical values as fixed
targets, assign the documented nominal availability schedule, and label the experiment as simulated
release timing with retrospectively revised targets. They are not eligible for a claim about
historically available label versions unless an archived submission/version feed is recovered.

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

During a read-only interface check, ENTSO-E displayed a Terms/Privacy acceptance dialog and rejected
the deep-linked product URL as expired. No terms were accepted and no data were retrieved. The
manual's documented interface capability therefore remains a strong source lead, while direct
product-level verification is pending a valid navigation path and any required user acceptance.

Official chronology sources: [ENTSO-E Manual of Procedures, consumer registration and version
history](https://www.entsoe.eu/Documents/MC%20documents/Transparency%20Platform/MOP/00_ENTSO-E%20Manual%20of%20Procedures_V2R1.pdf)
and [ENTSO-E Transparency Platform FAQ, updates](https://www.entsoe.eu/Documents/MC%20documents/Transparency%20Platform/Transparency_platform_FAQ.pdf).

## Decision and source registry status

| Source | Independent domain potential | Chronology evidence | Current status |
|---|---|---|---|
| EIA-930 | U.S. electricity operations; BAs are correlated subclusters | Forecast and realized demand fields verified in the API; nominal release schedule documented; revisions acknowledged; historical point-in-time snapshots not established | Eligible for simulated-feedback replay; not authentic-vintage confirmation |
| ENTSO-E Transparency Platform | European electricity market, distinct from U.S. macro and grid governance | Official manual documents public-interface submission timestamps and older versions; provider corrections are discretionary; selected-product retention and reproducible extraction remain to be checked | Strong candidate, not yet eligible |

Official sources checked: [EIA-930 data description and availability](https://www.eia.gov/electricity/930-content/about.html),
[EIA API update behavior](https://www.eia.gov/opendata/faqs.php), and
[ENTSO-E Transparency Platform](https://www.entsoe.eu/data/transparency-platform/).

The API inspection used the public `DEMO_KEY`, queried one timestamp for `PJM` under each type
`D` and `DF`, and retained no downloaded dataset or model outcome. A bounded development replay may
now be built using EIA-930 with simulated release timing, provided its time splits, BA registry,
prediction models, feedback delay, cost sensitivity, and method comparison are frozen before model
outcomes are examined. It must not be described as real-time label-version validation. For stronger
generalization, pair this domain with independent sources; multiple BAs alone are correlated
subclusters rather than independent data sources.

## Relation to the current method decision

The frozen CUSUM evaluation failed its practical cost gate against the strongest applicable
comparators and failed the adverse-regime harm gate. This source audit does not reverse those
results. The ALFRED audit remains another metadata-only route, with several U.S. macro series but
only one national economy. Neither data route currently supplies real-world confirmation for a
repair.
