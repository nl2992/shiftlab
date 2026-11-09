# Paper 1 EQSDp foundation: scope

Branch `research/paper1-eqsdp-foundation-2026-11-08` (cut from 1bb6d055), local only. Programme
scope follows the user's direction: only the nine datasets listed below are used for Paper 1
artifacts on this branch; no table, figure or text for any other dataset is produced here. The
full research record remains in `docs/qsg_methods_search/` and is not edited.

## Datasets

Selection basis: **datasets supporting the registered C4 claim (`docs/qsg_methods_search/c4_cumulative_b2.txt`)**,
i.e. the rows with `supports = True` there (5 of 9 in batch 1, 4 of 7 in batch 2). Organisation names are
those printed in that file; episode counts are the episodes present in the record files.

| source | path | lines | sha256 |
|---|---|---|---|
| batch1_panel | `outputs/qsg_methods_search/sota_expansion/nine/records.jsonl` | 333960 | `540a925815f08ca8...` |
| batch1_armR | `outputs/qsg_methods_search/sota_expansion/nine_armR/records.jsonl` | 7590 | `fe8a9b28bae9ad04...` |
| batch2_panel_and_armR | `outputs/qsg_methods_search/sota_expansion/batch2/records.jsonl` | 254700 | `19761e5791b5b619...` |

| dataset | org | C4 batch | episodes | policies | seeds | rows used |
|---|---|---|---|---|---|---|
| sf_311 | City and County of San Francisco (DataSF / SF311) | 1 | 100 | 45 | 10 | 45000 |
| kc_311 | City of Kansas City, Missouri (311 Call Center / MyKCMO) | 1 | 80 | 45 | 10 | 36000 |
| montgomery_traffic | Montgomery County, Maryland (Dept of Police / dataMontgomery) | 1 | 49 | 45 | 10 | 22050 |
| dallas_311 | City of Dallas (311 / dallasopendata.com) | 1 | 100 | 45 | 10 | 45000 |
| dc_311 | Government of the District of Columbia (DC 311 / DCGIS) | 1 | 100 | 45 | 10 | 45000 |
| austin_311 | City of Austin (Austin 311 Unified Data) | 2 | 100 | 45 | 10 | 45000 |
| cincinnati_311 | City of Cincinnati (311 Non-Emergency Service Requests) | 2 | 67 | 45 | 10 | 30150 |
| oakland_311 | City of Oakland (OAK 311 Call Center) | 2 | 55 | 45 | 10 | 24750 |
| sandiego_311 | City of San Diego (Get It Done) | 2 | 100 | 45 | 10 | 45000 |

Total rows used: 337950; distinct policies: 45

## Arms, contract, scoring unit

- Arm B = `EQSDp_l0.9_g0.2` (the registered C4 arm; `EQSD(stake=False, lam=.9, gamma=.2)`, 02_BASELINE_FIDELITY.md section on EQSDp).
- Arm R = `EQSDp_l0.98_g0.3` (selected on development streams in batch-F preparation, commit 8496433c; run on these nine datasets afterwards with the same seeds). It was not tuned on these datasets in this branch; whether the development selection used these data is recorded in `docs/qsg_methods_search/sota_expansion/` and should be checked before any confirmatory claim.
- Contract: label budget B=200, label price c_q=0.05, switch cost c_s=5, horizon T=2000 events per episode, 10 policy seeds (base 2026111201), feedback delay per dataset (field `delay`). `c4_pilot.CFG` (scripts/qsg_methods_search/c4_pilot.py:54).
- Panel: 44 policies in the batch-1 and batch-2 panels (the task description said 43; the files contain 44) plus arm R = 45 distinct policies. Taxonomy: 14 published-method adapters + 11 uncertified controls = 25 uncertified comparators (`analyze_all.py` ADAPTERS, CONTROLS); 15 certified methods (NOT COMPARABLE); 4 EQSDp variants (2 arms + 2 others, 'own'); CONTROL_never_switch (frozen-incumbent reference).
- The analysis unit is the episode (seed-mean per episode); episodes are resampled within dataset.

## Status of the evidence

Everything here is a **retrospective, descriptive re-analysis** of already-run records (batch 1 and batch 2 were opened under their registrations; arm R on batch 1 is a separate run, nine_armR). No policy was rerun or altered. Numbers support descriptions of past runs, not new confirmatory claims. The 25-comparator 'at least as good as every uncertified comparator' rule is from `11_AMENDMENT_ALL_DATA.md`, not a new registered rule.

## Reproduce

```
export OPENBLAS_NUM_THREADS=1
PY="<main checkout>/.venv/Scripts/python.exe"
$PY scripts/paper1_eqsdp/data.py        # provenance table above
$PY scripts/paper1_eqsdp/matrix.py      # outputs/paper1_eqsdp/matrix_*.csv + cross-check
$PY scripts/paper1_eqsdp/measures.py    # outputs/paper1_eqsdp/measure_*.csv
$PY scripts/paper1_eqsdp/make_docs.py   # tables/*.csv, 02_*.md, 03_*.md
$PY -m pytest scripts/paper1_eqsdp/tests -q
```
Record files are read from the main checkout (override with `P1_RECORDS_ROOT`).
