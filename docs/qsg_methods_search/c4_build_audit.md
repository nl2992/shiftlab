# C4 build audit (coordinator, before any sealed window is opened)

Each built source is audited against `c4_source_brief.md` (rule 3: features known at event time,
before the label is determined; no fields recorded at or after resolution). Decisions here are
made from module code and documentation only. No sealed array has been read.

| source | builder gates | audit | counted? |
|---|---|---|---|
| austin_animal | eligible (43 ep) | **FAIL rule 3.** Each event is the outcome event. `sex_upon_outcome` (spay/neuter state) is recorded at resolution and is changed by the adoption process; outcome hour is set with the outcome type. | **no** (excluded 2026-11-08, pre-opening) |
| la_crime | eligible (100 ep) | pass. Report-time fields only. Limitation: the label (status ≠ IC at the 2024 freeze) has a maturity trend, since older cases had longer to clear. | yes |
| sf_311 | eligible (100 ep) | pass. Opening-time fields; closure fields only in the label; the window ends > 1 year before the download, so labels are mature. | yes |
| nyc_collisions | eligible (88 ep) | pass. Police-report fields known when the report is created (contributing factor, vehicle types and count); injury and death counts only in the label. | yes |
| chicago_crimes | ineligible (disagreement 2.1%) | — | no |
| eia_ba | ineligible (17 episodes < 35) | — | no |
| nyc_tlc_taxi | ineligible (disagreement 0.5%) | — | no |
| uk_police | ineligible (disagreement 0.6%) | — | no |
| seattle_spd | ineligible (disagreement 0.6%) | — | no |
| nyc_311 | ineligible (disagreement 2.7%) | — | no |
| nyc_restaurant_inspections | ineligible (20 episodes) | — | no |
| boston_311 | eligible (42 ep) | pass. Opening-time fields; queue/department excluded (intake assignment undocumented); closure/SLA/on-time excluded. | yes |
| kc_311 | eligible (80 ep) | pass. `department_work_group` is the documented default per request type (known at opening). Crash fix: zip parsed from the address instead of a non-selectable computed column; same intent, label unchanged. | yes |
| montgomery_traffic | eligible (49 ep) | pass with caveat. Stop-condition flags (accident, injury, property damage) describe the event before the citation decision; demographics, charge/article and arrest type excluded. | yes |
| chicago_taxi | ineligible (disagreement 0.15%; base rate 0.94) | note: fetch hit its 1M-row limit, so the true window end is earlier than declared | no |
| citibike | ineligible (disagreement 0.23%) | — | no |
| dallas_311 | eligible (100 ep) | pass. Department, estimated response time and priority are assigned at intake by request type; status/closed/due fields excluded. | yes |
| dc_311 | eligible (100 ep) | pass with caveat. Organisation and priority are treated as intake-time (service-code driven); due/status/inspection fields excluded. The agent read one raw record to check the schema and computed no statistic. Fetch-only fix (parallel paged fetch). | yes |
| philly_311 | eligible (100 ep) | pass with caveat. `agency_responsible` is treated as routed at intake by service type; status/notes/expected fields excluded. | yes |

**Counted set (K = 9; one per organisation and per city):** la_crime (LA), sf_311 (SF), nyc_collisions (NYC), boston_311 (Boston), kc_311 (Kansas City), montgomery_traffic (Montgomery County MD), dallas_311 (Dallas), dc_311 (DC), philly_311 (Philadelphia).
Sources tried: 16. Ineligible by gate: 8. Excluded by audit: 1 (austin_animal).

## Batch 2 (Amendment A2; candidate pool chosen after batch-1 results, favouring 311-type streams)

| source | builder gates | audit | counted? |
|---|---|---|---|
| austin_311 | eligible (100 ep) | pass. Department routed by request type at intake. | yes |
| cincinnati_311 | eligible (67 ep) | pass. Priority, group and department at intake; planned/SLA and dispatch fields excluded. | yes |
| nola_311 | eligible (61 ep) | pass. Responsible agency routed by type; contractor and status excluded. | yes |
| oakland_311 | eligible (55 ep) | pass. Description, category, source, district, beat and zip at creation. | yes |
| sandiego_311 | eligible (100 ep) | pass. Record type, service, district, community plan, zip and origin. Status/age/closed only in the label (Referred counts as resolved, fixed pre-build). | yes |
| sacramento_311 | eligible (100 ep) | pass. Categories, district, source, neighbourhood and zip at creation. | yes |
| baltimore_311 | eligible (83 ep) | pass. Type, method, agency (routed by type), neighbourhood, council, police and zip. | yes |
| buffalo_311 | ineligible (incumbent error 0.60) | — | no |
| detroit_311 | ineligible (incumbent error 0.68) | — | no |
| houston_311, louisville_311, cambridge_311 | not built (builder agent hit a usage limit) | — | batch 3 candidates |
