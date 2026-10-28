# Checkpoint-B machine-readable leaderboards

These CSV files are byte-for-byte copies of validated analysis outputs. They keep
every registered arm/cell visible in Git while raw path-level artifacts remain in
ignored `outputs/` directories. The corresponding results documents define the
estimands, fidelity labels, gates and limitations.

| Table | Rows represented | SHA-256 | Source |
|---|---:|---|---|
| `wp1_null_summary.csv` | every registered WP1 arm/scenario/budget null cell | `e34483bd66d377e51d7c0c31b7301ce25b873406e29a200ebc22e3162bfdd40c` | `outputs/gated_monitor_null/analysis/summary.csv` |
| `wp2_growth_summary.csv` | every registered WP2 working-law/K/allocation/budget summary | `a755c04623c06023c179fdb5c5d62d74feeddaaa356296214c373971c32e55ca` | `outputs/stratified_growth_prescreen_20/summary.csv` |
| `wp3_panel_summary.csv` | every registered WP3 arm/engine/detector/onset/budget summary | `1da55ce007459de3cbb4632c42b1e1810a173db1a47c3703012cd1f2f8f2ca28` | `outputs/data_efficient_prescreen_20/analysis/summary.csv` |
| `wp3_paired_comparisons.csv` | every candidate-versus-applicable-incumbent WP3 comparison | `d0678f4df216f8a13707fe241cf62351b569a7d23f2d11fe73272acd4f31c460` | `outputs/data_efficient_prescreen_20/analysis/paired.csv` |
| `wp1_s3_comparison_summary.csv` | every WP1 S3 scenario/budget/arm/engine cell | `670833915b3ec749882abd598d48dcff91df431e72eea9c81ce21dcef876ed03` | `outputs/gated_monitor_compare/analysis/summary.csv` |
| `wp4_eia_null_cells.csv` | every WP4 random-orientation null cell (primary and `epsilon = 0`) | `788932ab9100ecf6aef26957b84de0f8b141cb74257e725a39f378ebc6a4b5f2` | `outputs/eia_real_data_validity/null_cells.csv` |
| `wp4_eia_unmodified.csv` | every WP4 unmodified-stream arm/path/budget | `32575cb4bd1ade54c6ed487dbacc6e6b551ada1208bdab40c4ce38c5cb51aa4f` | `outputs/eia_real_data_validity/unmodified.csv` |
| `wp4_eia_injected.csv` | every WP4 injected-harm arm/path/onset/budget | `8d21426355112b134c8864412206bc38e597279e9ae7733b64cf81fc9d182cd7` | `outputs/eia_real_data_validity/injected.csv` |

WP1 S3 is a development comparison and WP4 is retrospective on previously examined
windows. No row here is confirmation evidence.
