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

## Batch F (protocols `sota_expansion/10` and `11`; audited from module code and builder records before opening)

| source | builder gates | audit | registered? |
|---|---|---|---|
| miamidade_311 | eligible (100 ep) | **pass with caveat.** `case_owner` is treated as the department routed by issue type at intake. `issue_description` is empty (a harmless null feature). | yes |
| minneapolis_311 | eligible (53 ep) | **pass with caveat.** `TITLE` is treated as intake-time. Validation base rate .83 (label kept as locked). | yes |
| louisville_311 | eligible (85 ep) | **pass.** `agency_responsible` routed by type. Fetch-only fix: the page size went 2000 → 1000 because the server caps pages at 1000; the first build was truncated. Label and features unchanged; the receipts match the server count. | yes |
| chicago_311 | eligible (100 ep) | **pass.** `created_department` (not `owner_department`) is used. One-year window to fit the size limit. Validation base rate .80. | yes |
| denver_311 | eligible (100 ep) | **pass with caveat.** Agency and division routed by type at intake. Validation base rate .845. | yes |
| pittsburgh_311 | eligible (48 ep) | **pass with caveat.** Closures propagate from parent to grouped child tickets, as the codebook documents. | yes |
| bts_ontime | eligible (100 ep) | **pass.** Schedule-time features only. Zip check: exactly one CSV is read; the bundled `readme.html` is never opened. | yes |
| sf_building_permits | eligible (85 ep) | **pass.** Filing-time fields only; status, issue, approval and revised-cost fields excluded. Same city as sf_311 (different department). | yes |
| chicago_traffic_crashes | eligible (54 ep) | **pass.** Scene-condition fields only; damage, injury, crash_type, causes and hit-and-run excluded. Dataset id 85ca-t3if (the brief's id was wrong). | yes |
| dallas_animal_shelter | eligible (76 ep) | **pass with caveat.** Intake records and intake-time fields only (unlike austin_animal). Rows with no outcome are dropped. Re-impounds are present. Same city as dallas_311 (different department). | yes |
| cambridge_311 | ineligible (7 ep) | — | no |
| gainesville_311 | ineligible (1 ep) | — | no |
| chicago_food_inspections | ineligible (err_incumbent .508 > .5) | — | no |
| seattle_building_permits | ineligible (17 ep) | — | no |
| cfpb_complaints | ineligible (disagreement 1.9%) | — | no |
| sonoma_animal_shelter | ineligible (7 ep) | — | no |
| houston_311, seattle_csr, norfolk_311, somerville_311, bloomington_311, fortworth_311 | not buildable | no closure timestamp, no export, or too small | no |

**Registered (K = 10; 801 episodes):** `c4_registration_batchF.json`, with hashes recomputed from the
sealed arrays. 6 are 311 streams (protocol 10 primary); 4 come from other domains (air travel,
permitting, road safety, animal shelter). By city: Chicago appears twice in batch F (311 and crashes);
SF and Dallas also appear in the seen tier.
