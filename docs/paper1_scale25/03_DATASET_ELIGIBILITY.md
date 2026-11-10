# 03 - Dataset eligibility decisions (WS-A)

Statuses follow `DATASET_ELIGIBILITY_PROTOCOL.md`. CONFIRM windows were never built or inspected; only counts and date ranges were read.

## A. Existing recipes (44)

| dataset | domain | D0 | D1 / registration | dev window | confirmation window |
|---|---|---|---|---|---|
| la_crime | public-safety | eligible | gate-pass (registered, opened) | 2020-01-01..2025-01-01 | none: 2025-01-01..2026-07-01 verified count 0 |
| sf_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-07-01..2025-07-01; also fresh 2025-07-01..2026-07-01 (opened eligible) | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| nyc_collisions | public-safety | eligible | gate-pass (registered, opened) | 2022-01-01..2025-10-01 | none: 2025-10-01..2026-07-01 verified count 63681 |
| boston_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-01-01..2025-01-01 | 2025-01-01..2026-01-01: available (verified-count-query; n=276093) |
| kc_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2023-07-01..2025-07-01; also fresh 2025-07-01..2026-07-01 (opened eligible) | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| montgomery_traffic | public-safety | eligible | gate-pass (registered, opened) | 2024-07-01..2026-07-01 | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| dallas_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-07-01..2025-07-01; also fresh 2025-07-01..2026-07-01 (opened eligible) | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| dc_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-01-01..2025-01-01; also fresh 2025-01-01..2026-01-01 (opened eligible) | 2026-01-01..2026-07-01: available (verified-count-query; n=250354) |
| philly_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-07-01..2025-07-01 | 2025-07-01..2026-07-01: available (verified-count-query; n=528651) |
| austin_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-01-01..2025-07-01; also fresh 2025-07-01..2026-07-01 (opened eligible) | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| cincinnati_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2023-07-01..2025-07-01; also fresh 2025-07-01..2026-07-01 (opened eligible) | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| nola_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2023-01-01..2025-07-01 | none: 2025-07-01..2026-07-01 verified count 89391 |
| oakland_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2023-07-01..2025-07-01; also fresh 2025-07-01..2026-07-01 (opened ineligible) | none: 2026-07-01..2026-07-01 empty interval after 2026-07-01 settling cap |
| sandiego_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-01-01..2025-01-01; also fresh 2025-01-01..2026-01-01 (opened eligible) | 2026-01-01..2026-07-01: available (estimated (dev-year rate ~423k/yr x 0.5yr ~ 210k; 2026 closed-requests file |
| sacramento_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-01-01..2025-01-01 | 2025-01-01..2026-01-01: available (verified-count-query; n=569850) |
| baltimore_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-09-01..2025-01-01 | 2025-01-01..2025-05-01: available (verified-count-query; n=274834) |
| miamidade_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2022-01-01..2024-01-01 | unverified: 2024-01-01..2026-01-01: 2024-26 layers use a new schema (Created_Date, Subject, SubType, Departmen |
| minneapolis_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2023-01-01..2025-01-01 | none: 2025-01-01..2026-07-01 verified count 149804 |
| louisville_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2023-01-01..2025-01-01 | 2025-01-01..2026-07-01: available (verified-count-query; n=283011) |
| chicago_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2024-01-01..2025-01-01 | 2025-01-01..2026-01-01: available (verified-count-query; n=1960595) |
| denver_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2022-01-01..2024-01-01 | unverified: 2024-01-01..2026-01-01: no 2024/2025 per-year layers in the publisher's ArcGIS org (only 2007-2023 |
| pittsburgh_311 | municipal-311 | eligible | gate-pass (registered, opened) | 2022-07-01..2024-07-01 | none: 2024-07-01..2026-07-01 verified count 58402 |
| bts_ontime | transport | eligible | gate-pass (registered, opened) | 2025-05-01..2025-07-01 | 2025-07-01..2025-09-01: available (estimated (monthly zips 2025-07, 2025-08 exist, ['32208704', '30864245'] by |
| sf_building_permits | permits-enforcement | eligible | gate-pass (registered, opened) | 2015-01-01..2025-07-01 | none: 2025-07-01..2026-07-01 verified count 24999 |
| chicago_traffic_crashes | public-safety | eligible | gate-pass (registered, opened) | 2021-01-01..2023-01-01 | 2023-01-01..2025-01-01: available (verified-count-query; n=222810) |
| dallas_animal_shelter | health-animal | eligible | gate-pass (registered, opened) | 2015-10-01..2024-10-01 | none: 2024-10-01..2026-07-01 verified count 40404 |
| austin_animal | health-animal | ineligible | gate-pass (not registered) | 2013-10-01..2025-06-01 | not assessed (ineligible dev build) |
| chicago_crimes | public-safety | eligible | gate-fail: disagreement (disagreement 0.0215, err_inc 0.105, err_chal  | 2023-10-01..2025-10-01 | not assessed (ineligible dev build) |
| eia_ba | energy | ineligible | gate-fail: episodes (disagreement 0.0810, err_inc 0.146, err_chal 0.15 | full available history of the selected BA (UTC hours with D and DF both present) | not assessed (ineligible dev build) |
| nyc_tlc_taxi | transport | eligible | gate-fail: disagreement (disagreement 0.0053, err_inc 0.241, err_chal  | 2025-08-01..2025-11-01 | not assessed (ineligible dev build) |
| uk_police | public-safety | eligible | gate-fail: disagreement (disagreement 0.0060, err_inc 0.204, err_chal  | 2025-01 to 2025-05 reporting months (archive snapshot 2026-06) | not assessed (ineligible dev build) |
| seattle_spd | public-safety | eligible | gate-fail: disagreement (disagreement 0.0057, err_inc 0.050, err_chal  | 2025-10-01..2026-10-01 | not assessed (ineligible dev build) |
| nyc_311 | municipal-311 | eligible | gate-fail: disagreement (disagreement 0.0274, err_inc 0.134, err_chal  | 2025-01-01..2025-04-01 | not assessed (ineligible dev build) |
| nyc_restaurant_inspections | health-inspection | ineligible | gate-fail: episodes (disagreement 0.1313, err_inc 0.357, err_chal 0.36 | 2022-01-01..2026-10-01 | not assessed (ineligible dev build) |
| chicago_taxi | transport | eligible | gate-fail: disagreement (disagreement 0.0015, err_inc 0.065, err_chal  | 2024-01-01..2024-07-01 | not assessed (ineligible dev build) |
| citibike | transport | eligible | gate-fail: disagreement (disagreement 0.0023, err_inc 0.280, err_chal  | 2026-04-01..2026-05-01 | not assessed (ineligible dev build) |
| buffalo_311 | municipal-311 | eligible | gate-fail: err_incumbent (disagreement 0.6510, err_inc 0.596, err_chal | 2021-06-01..2024-05-01 | not assessed (ineligible dev build) |
| detroit_311 | municipal-311 | eligible | gate-fail: err_incumbent (disagreement 0.5423, err_inc 0.681, err_chal | 2024-01-01..2026-01-01 | not assessed (ineligible dev build) |
| cambridge_311 | municipal-311 | ineligible | gate-fail: episodes (disagreement 0.2949, err_inc 0.197, err_chal 0.36 | 2023-01-01..2025-01-01 | not assessed (ineligible dev build) |
| gainesville_311 | municipal-311 | ineligible | gate-fail: episodes (disagreement 0.2490, err_inc 0.322, err_chal 0.29 | 2019-06-01..2021-06-01 | not assessed (ineligible dev build) |
| chicago_food_inspections | health-inspection | eligible | gate-fail: err_incumbent (disagreement 0.1308, err_inc 0.508, err_chal | 2013-01-01..2026-07-01 | not assessed (ineligible dev build) |
| seattle_building_permits | permits-enforcement | ineligible | gate-fail: episodes (disagreement 0.1827, err_inc 0.274, err_chal 0.22 | 2016-01-01..2025-07-01 | not assessed (ineligible dev build) |
| cfpb_complaints | finance-economics | eligible | gate-fail: disagreement (disagreement 0.0188, err_inc 0.205, err_chal  | 2018-07-01..2020-01-01 | not assessed (ineligible dev build) |
| sonoma_animal_shelter | health-animal | ineligible | gate-fail: episodes (disagreement 0.0497, err_inc 0.086, err_chal 0.08 | 2014-01-01..2025-01-01 | not assessed (ineligible dev build) |

## B. New sources with a recipe (dev builds)

| dataset | domain | D1 | episodes | confirmation window | notes |
|---|---|---|---|---|---|
| edmonton_311 | municipal-311 | gate-pass | 100 | 2025-07-01..2026-07-01: available (verified count 943,709; latest event 2026-11-08) | Canadian municipality; Socrata CSV paged fetch |
| winnipeg_311 | municipal-311 | gate-pass | 100 | 2025-07-01..2026-07-01: available (verified count 843,400; latest event 2026-11-08) | Canadian municipality |
| mc311_montgomery | municipal-311 | gate-pass | 100 | 2025-07-01..2026-07-01: available (verified count 543,705; latest event 2026-11-08) | County, not city |
| calgary_311 | municipal-311 | gate-pass | 100 | 2025-07-01..2026-07-01: available (verified count 494,674; latest event 2026-11-08) | Canadian city |
| nyc_ems_response | emergency-services | gate-pass | 100 | 2025-07-01..2026-07-01: available (verified count 1,605,880; latest event 2026-09-30) | NYC Open Data; different organisation unit from nyc_311/nyc_collisions (same city) |
| nyc_fire_response | emergency-services | gate-pass | 100 | 2025-07-01..2026-07-01: available (verified count 688,649; latest event 2026-09-30) | Same agency (FDNY) as nyc_ems_response, different dataset and event process (fire vs EMS); |
| divvy_chicago | transport | gate-pass | 100 | see notes | Archive vintage rule: DEV = 2024-07..2025-06 monthly zips, CONFIRM = 2025-07..2026-06 (zip |
| capitalbikeshare_dc | transport | gate-pass | 100 | see notes | Same operator (Lyft) as divvy_chicago; organisation-sensitivity count merges them |
| epa_aqi_county | environment | gate-pass | 100 | see notes | 2026 file is partial (394 kB at 2026-07-13); CONFIRM = 2025-07..2026-06 limited to publish |
| ghcn_us_rain | environment | gate-pass | 100 | see notes | by_year files 2024 (177 MB) and 2025 (166 MB) |
| eia930_pooled | energy | gate-pass | 100 | see notes | Uses the local EBA.zip (checksum verified against its receipt; ends 2026-10-20). Shares pa |
| montgomery_police_dispatch | public-safety | gate-pass | 78 | 2025-07-01..2026-07-01: available (verified count 196,112; latest event 2026-11-09) | DEV is the full 24-month span (count under 800k); same county as mc311_montgomery and mont |
| usac_erate_invoices | finance-economics | gate-fail: err_incumbent | 100 | 2025-07-01..2026-07-01: available (verified count 292,146; latest event 2026-11-02) | Federal programme data, not municipal; DEV is the 24-month span |
| nyc_forestry_work_orders | public-works | build-failed: ValueError('This solver needs samples of at le |  | 2025-07-01..2026-07-01: available (verified count 172,745; latest event 2026-11-06) | Different agency (Parks) from the FDNY recipes |

## C. Other new candidates reviewed by hand

| dataset | D0 | reason |
|---|---|---|
| soc_cos_data_crg2_ssqd (City of Seattle) | ineligible | CONFIRM count below 150k (83,465); review-task rows, not independent events |
| soc_data_7ixm_mnvx (Public Works Business Office) | dev-only | CONFIRM count below 150k (71,658); DEV 189,550 |
| soc_data_8ced_xbvn (The City of Calgary) | ineligible | DEV 149,512 and CONFIRM 41,630 below 150k |
| soc_data_vnsz_a3wp (City of Cincinnati) | dev-only | CONFIRM count below 150k (97,127); DEV 194,810 over 24 months |
| soc_data_4pt5_3vv4 (Department of Parks and Recrea) | pending-review | NYC Forestry inspections; label horizon not designed; same agency (Parks) as work orders |
| soc_data_bkfu_528j (data.cityofnewyork.us) | pending-review | counts pass; label/feature design and outcome-timing review not done |
| soc_data_d6zx_ckhd (Police Department (NYPD)) | pending-review | NYPD calls-for-service historic; 14.1M rows in DEV; ends 2025-12-31 (2026 lives in a separate YTD dataset n2zq-pubd) so CONFIRM would span two dataset |
| soc_data_kegn_anvq (Department of Records and Info) | ineligible | CONFIRM count below 150k (93,408) |
| soc_data_mu46_p9is (Department of Parks and Recrea) | dev-only | CONFIRM count below 150k (92,592) |
| soc_data_7hsn_idqi (data.edmonton.ca) | dev-only | CONFIRM count below 150k (80,259) |
| soc_datahub_38mr_dwji (City of Austin, Texas - data.a) | ineligible | DEV 149,737 below 150k and CONFIRM 77,809 below 150k |
| bluebikes_boston (Bluebikes / Lyft (Boston)) | eligible | same archive-vintage rule; not built (third Lyft system adds no organisation diversity) |
| toronto_311 (City of Toronto) | ineligible | no closure timestamp, so no resolvable label with delay |
| philly_permits (City of Philadelphia (L&I)) | ineligible | DEV and CONFIRM counts below 150k |
| philly_incidents (Philadelphia Police Department) | ineligible | no outcome observed after the event (no delay semantics) |
| uk_stats19_collisions (UK Department for Transport) | ineligible | annual vintages of about 100k rows: 2022-2023 DEV is about 200k, CONFIRM (2024 or 2025) about 100k below 150k; rows not counted |
| openfda_faers (US FDA (openFDA drug adverse e) | pending-review | size ok; raw JSON is about 10 kB per report so a 12-month window is multi-GB (estimated); not built |
| elec2_nsw (Harries (NSW electricity, via ) | ineligible | 45k rows (below 150k), finite static file (no later confirmation window), no event timestamps beyond a normalised day index |
| airlines_openml_1169 (OpenML 1169 (Elwell & Polikar ) | ineligible | ordered stream without event timestamps; finite file so no later confirmation window |
| weather_elwell_polikar (Elwell & Polikar (NOAA Offutt)) | ineligible | 18k rows; finite static file |
| spam_katakis (Katakis et al.) | ineligible | 9k rows, text bag-of-words, static |
| gas_sensor_drift (UCI 224 gas sensor array drift) | ineligible | 13.9k rows, multiclass, static |
| rialto_stream (Losing et al. (Rialto bridge)) | ineligible | 82k rows, multiclass image features, static |
| criteo_attribution (Criteo) | ineligible | conversion is a rare event per the dataset README (rate not measured here), so the disagreement gate is expected to fail; static file; non-commercial  |
| open_bandit (ZOZO Open Bandit Dataset) | ineligible | rare clicks (per dataset paper), one week of data, static file |
| folktables_acs (US Census ACS PUMS via folktab) | ineligible | no per-event timestamps (annual snapshots only) |
| opsd_power (Open Power System Data) | ineligible | 2020 snapshot with no later window; hourly series (about 8.8k rows per year per series) |
| binance_klines (Binance public data) | ineligible | licence not an explicit open licence; only a few local months |
| crsp_licensed (CRSP / WRDS (licensed)) | ineligible | licensed data outside the public cohort; retrospective stress-test dataset only |
| civilcomments_wilds (WILDS CivilComments (HF mirror) | ineligible | no per-event timestamps in the local mirror; text features outside the frozen C4 model pair |

## D. Mechanically screened Socrata probes (232 ineligible by size, probe error or non-outcome date pair)

Full rows with counts are in the ledger (`origin = socrata-probe`). Reasons by type:

- size: 224
- close column is a planned permit expiry (dates to 2115): 1
- start/end are procurement notice dates (scheduled), CONFIRM 72,879: 1
- probe failed: 1
- end column is the planned variance end (dates to 2028); no outcome label: 1
- expired_date is a scheduled permit expiry, not an outcome: 1
- radon test start/end are measurement dates, no event outcome: 1
- close column is an (extended) expiration date, a scheduled quantity, not an outcome: 1
- integration (non-production) Socrata host; scheduled vs actual end: 1
