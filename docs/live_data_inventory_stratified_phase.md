# Local live-source inventory for this phase

Inventory observation: 2026-10-27T14:38:09.984415Z. This is a local receipt audit,
not a new pull, publication-time audit or real-data monitor experiment.
The full ignored receipt is `outputs/tmp/live_source_inventory.json`.

| Source family | Receipts |
|---|---:|
| Binance | 4 |
| NOAA | 4 |
| EIA | 2 |
| FRED | 8 |
| Folktables | 15 |
| Monash | 5 |
| OPSD | 2 |
| Gas Sensor | 1 |
| WILDS | 1 |
| Criteo Attribution | 2 |
| Criteo PrivateAd | 288 |

All 332 local payloads are present and match recorded sizes. Of these, 59 payloads
at most 16 MiB were SHA-256 checked and matched; 273 larger payloads were not rehashed
in this inventory. The EIA bulk hash was already independently verified in the
[phase execution record](stratified_monitor_phase_execution.md). The PrivateAd
receipt family has no exact catalogue entry and is retained as unmapped; no
availability or licensing status is inferred from its name.

The EIA snapshot was retrieved 2026-10-20T01:32:49.393495Z. CISO/ERCO demand reaches
2026-10-19T18:00Z. Forecast coverage reaches 2026-10-20T07:00Z for CISO and 05:00Z
for ERCO. Publisher release times and historical availability are unknown. This
snapshot is not current through the inventory date and remains development data.
No new API/archive/bulk downloads were made.

There is no frozen EIA policy/model-weight/task bundle for this phase, so no
prospective clock has started and no prospective observations are claimed.
Existing synthetic-code freezes do not start that clock. No per-path randomized
null or injected-harm result is available for this phase. A date for a confirmation
window cannot be given before a real-data task freeze and window-size decision.

The user confirmed that the relevant pulls should already be represented in the
repository. No additional outside-checkout pull was supplied for this audit, so
the repository is the complete known local inventory for this phase. This does
not prove that no other copy exists. WP4's adapter and randomized-null minimum is
a condition of checkpoint A. Checkpoint B instead requires the evidenced WP2
stop and completed WP1/WP3 exits; this inventory does not assert that A is satisfied.
