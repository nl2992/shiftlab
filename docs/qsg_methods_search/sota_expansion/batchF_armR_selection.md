# Batch F, arm R selection (protocol 10 §3)

Selected 2026-11-08, before any batch-F source was built.

- Run: `sota_nine.py dev --policies outputs/qsg_methods_search/sota_expansion/dev_eqsdp_grid.txt`
  (14 development streams, 230 episodes, 5 seeds, seed base 2026111401).
- Arm B check: it reproduces the earlier dev run exactly (1,150 rows, max |ΔJ| = 0).
- Rule: the lowest equal-stream-weight mean J over the grid.

| policy | dev mean J |
|---|---|
| **EQSDp_l0.98_g0.3 (arm R)** | **403.14** |
| EQSDp_l0.98_g0.2 | 403.54 |
| EQSDp_l0.98_g0.1 | 404.71 |
| EQSDp_l0.95_g0.1 | 405.74 |
| EQSDp_l0.95_g0.2 | 405.91 |
| EQSDp_l0.98_g0.5 | 406.60 |
| EQSDp_l0.95_g0.3 | 406.85 |
| EQSDp_l0.9_g0.1 | 407.98 |
| EQSDp_l0.9_g0.2 (arm B) | 410.43 |
| EQSDp_l0.9_g0.3 | 412.67 |
| EQSDp_l0.95_g0.5 | 413.90 |
| EQSDp_l0.9_g0.5 | 429.45 |

λ = .98 is the edge of the grid. The grid was fixed in advance (`d3_extra`), so it is not extended.

Batch-F policy list: [batchF_policies.txt](batchF_policies.txt). Both econF configurations (SD
mo5 m5 and RD mo5 m0) are descriptive.
