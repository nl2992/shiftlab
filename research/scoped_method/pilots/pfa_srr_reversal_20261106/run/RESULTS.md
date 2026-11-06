# PFA-SR published-baseline development screen

**Status:** development evidence only. The PFA-SR result is not pooled with the later matched-host confirmation. This 30-seed screen compares PFA-SR on `gated_deployment` with RMM on `gated_adaptive_range`; the host mismatch confounds any detector-specific contrast. The frozen protocol and raw 840 policy rows are retained for provenance.

Cost = loss + 0.05 × labels + 5 × switches. The table reports PFA-SR costs and paired differences from never-switch; paired intervals are two-sided t intervals over 30 streams. They do not adjust for multiple cells.

| Cell | PFA-SR net | Promotions | PFA-SR minus never [95% CI] | Interpretation |
|---|---:|---:|---:|---|
| `F0_better` | 365.37 | 29/30 | −58.13 [−69.27, −47.00] | Development signal only; RMM host mismatch prevents attribution. |
| `F0_null` | 378.67 | 0/30 | +10.00 [+10.00, +10.00] | Screening null only; sample too small to establish alpha. |
| `F3_reversal_1200` | 389.67 | 30/30 | +17.90 [+9.09, +26.71] | More costly than never-switch despite worthwhile transient improvement. |
| `F3_reversal_800` | 401.60 | 27/30 | +60.20 [+51.40, +69.00] | Material adverse reversal result. |

In `F0_better`, mean RMM net cost is 379.27, but that row uses a different deployment host; this cannot be treated as a matched comparison. The correction was to freeze and run `pfa_srr_transfer_confirmation_20261106/`, which compares PFA-SR and RMM on identical hosts and fresh seeds. The initial screen is not confirmatory and does not support a novelty claim.

Reproduce from the command and seed base in `protocol.md`; all outcomes are in `records.jsonl`, with code/source fingerprints in `manifest.json`.
