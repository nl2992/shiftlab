# P2-NAD real data

## Roles and exposure

| Set | Sources | Episodes | Role in P2-NAD | Prior exposure |
|---|---|---|---|---|
| UCI fresh | metro, beijing_pm25, bike_hour, appliances, household_power | 62 | real development (`outputs/p2/realdev*`) | P2 benchmark development and W4 |
| Atlas v2 | airlines, bank, criteo, elec2, openml_ldpa, rialto, spam, uci_occupancy, weather | 168 | real development | Failure Atlas, SOTA sprint |
| UCI twins v1 (v3 rebuild pending) | the five UCI sources, exact marginal nulls | 100 (v1) | real-data validity (descriptive) | P2 W2/W4 |
| **Chronological replacement C4** | 27 municipal and transport streams (below) | 2,097 | **confirmation only; never run in P2 before the freeze** | Built for Paper 1 (EQSDp C4). Not used for any P2-NAD design choice |

The 14 development streams are exposed. The NAD-2S and NAD-m80 choices were made with them in
view, so they are not confirmation evidence.

## C4 chronological replacement streams

Construction (Paper 1 `docs/qsg_methods_search/c4_plan.md`, in the main checkout): chronological
split into train-old, train-new, validation and test. The incumbent is a standardised logistic
regression trained on train-old; the challenger is a HistGradientBoosting classifier trained on
train-new. Preprocessing is fitted on each model's own window. Episodes are non-overlapping
2,000-event windows of the test period. The label delay is **imposed** (100 events for record
streams). These are not recorded label-release times.

| Source | Episodes | Delay | Disagreement rate | Mean l0 − l1 | Content hash (l0‖l1, first 16) |
|---|---|---|---|---|---|
| austin_311 | 100 | 100 | 0.106 | +0.0178 | 46f88092f765bba8 |
| austin_animal | 43 | 100 | 0.140 | +0.0124 | 7cd8d074e7189395 |
| baltimore_311 | 83 | 100 | 0.084 | +0.0354 | 540c6e67d22fad7a |
| boston_311 | 42 | 100 | 0.164 | +0.1025 | 827113402daf5729 |
| bts_ontime | 100 | 100 | 0.093 | +0.0060 | 685e1dd91f357e72 |
| chicago_311 | 100 | 100 | 0.077 | +0.0075 | 9f18ebd3f514f35b |
| chicago_traffic_crashes | 54 | 100 | 0.049 | +0.0014 | 7e3d23f43acb88ca |
| cincinnati_311 | 67 | 100 | 0.174 | +0.0398 | ecae274ffdc7f750 |
| dallas_311 | 100 | 100 | 0.167 | +0.0475 | e0c0c96173fa2ac9 |
| dallas_animal_shelter | 76 | 100 | 0.301 | +0.1407 | 64c40099df467a82 |
| dc_311 | 100 | 100 | 0.432 | +0.2374 | ec73315b3fedd00e |
| denver_311 | 100 | 100 | 0.061 | +0.0076 | 1b4b6b4b5d3c2883 |
| kc_311 | 80 | 100 | 0.318 | −0.0583 | 1950f2a300f9a5d2 |
| la_crime | 100 | 100 | 0.040 | +0.0032 | f3af35938dec103f |
| louisville_311 | 85 | 100 | 0.135 | −0.0045 | a7b1f7ac050512e4 |
| miamidade_311 | 100 | 100 | 0.096 | −0.0395 | b41f8cc76f4f38cf |
| minneapolis_311 | 53 | 100 | 0.123 | −0.0414 | d9366806639c7bd4 |
| montgomery_traffic | 49 | 100 | 0.067 | +0.0044 | 529c79b23cf7c798 |
| nola_311 | 61 | 100 | 0.183 | +0.1240 | c767e3c537e33463 |
| nyc_collisions | 88 | 100 | 0.052 | +0.0050 | 7ece649cc207cd5c |
| oakland_311 | 55 | 100 | 0.060 | +0.0183 | 328a4bf8a1a620a7 |
| philly_311 | 100 | 100 | 0.050 | +0.0123 | a934a5c78c3b41ad |
| pittsburgh_311 | 48 | 100 | 0.318 | +0.0476 | db0aeac57a0d8893 |
| sacramento_311 | 100 | 100 | 0.070 | +0.0210 | 913cfa93f59ab7e6 |
| sandiego_311 | 100 | 100 | 0.191 | +0.0150 | e5834033b0cda555 |
| sf_311 | 100 | 100 | 0.400 | +0.2161 | d1af902cceba07ce |
| sf_building_permits | 85 | 100 | 0.054 | +0.0072 | e2a6b2daeda6896c |

The disagreement-sequence lag-1 autocorrelation is ≤ .23 on all 27 (`scripts/p2/real_dependence.py`).
These streams are weakly dependent. They test whether a dependence-robust method gives up too
much when dependence is weak (FA7). They do not test validity under strong dependence. Four
sources have a worse challenger on average (kc, louisville, miamidade, minneapolis), which makes
them a real-data harm check.

Not used: W5 untouched sources (Online Retail II, arXiv, NYC taxi). They need downloads and a
pair-construction pipeline. They remain the next real-data option.
