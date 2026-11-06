# Adaptive-gate correction replay differences

Matched old versus corrected output rows use the same stream, episode, seed and policy. These are correction replays after a discovered implementation defect; they are not independent validation or new confirmatory data.

- Corrected run directories with matched output: **1**
- Matched regime-policy cells: **21**
- Machine-readable row-level table: `outputs/sprint2/adaptive_gate_replay_differences.csv`
- JSON with source manifest SHA256 values: `outputs/sprint2/adaptive_gate_replay_differences.json`

| Source run | Regime | Policy | n | Promote old → corrected | Changed | Δ net [95% paired CI] | Δ labels | Δ switches |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `outputs/sota_sprint/validation/null1000` | V_null | gated_adaptive_range | 1000 | 0/1000 → 0/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null | gated_adaptive_range+front | 1000 | 1/1000 → 1/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null | gated_adaptive_range+pace_tuned | 1000 | 1/1000 → 1/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null_dep_r5 | gated_adaptive_range | 1000 | 0/1000 → 0/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null_dep_r5 | gated_adaptive_range+front | 1000 | 10/1000 → 10/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null_dep_r5 | gated_adaptive_range+pace_tuned | 1000 | 10/1000 → 10/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null_dep_r8 | gated_adaptive_range | 1000 | 9/1000 → 9/1000 | 0 | -0.00 [-0.00,+0.00] | -0.01 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null_dep_r8 | gated_adaptive_range+front | 1000 | 106/1000 → 106/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_null_dep_r8 | gated_adaptive_range+pace_tuned | 1000 | 105/1000 → 105/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_worse | gated_adaptive_range | 1000 | 0/1000 → 0/1000 | 0 | -0.00 [-0.01,+0.00] | -0.05 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_worse | gated_adaptive_range+front | 1000 | 0/1000 → 0/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | V_worse | gated_adaptive_range+pace_tuned | 1000 | 0/1000 → 0/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_null_dep_r9 | gated_adaptive_range | 1000 | 21/1000 → 22/1000 | 1 | +0.01 [-0.04,+0.06] | -0.20 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_null_dep_r9 | gated_adaptive_range+front | 1000 | 218/1000 → 218/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_null_dep_r9 | gated_adaptive_range+pace_tuned | 1000 | 214/1000 → 214/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_null_dep_r95 | gated_adaptive_range | 1000 | 112/1000 → 115/1000 | 3 | -0.04 [-0.26,+0.19] | -0.71 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_null_dep_r95 | gated_adaptive_range+front | 1000 | 386/1000 → 386/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_null_dep_r95 | gated_adaptive_range+pace_tuned | 1000 | 385/1000 → 385/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_worse_dep_r8 | gated_adaptive_range | 1000 | 1/1000 → 1/1000 | 0 | -0.01 [-0.03,+0.01] | -0.14 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_worse_dep_r8 | gated_adaptive_range+front | 1000 | 14/1000 → 14/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
| `outputs/sota_sprint/validation/null1000` | W_worse_dep_r8 | gated_adaptive_range+pace_tuned | 1000 | 14/1000 → 14/1000 | 0 | +0.00 [+0.00,+0.00] | +0.00 | +0.00 |
