# Gap-conditioned evidence development screen

Status: development only; no confirmation or SOTA claim.
Manifest SHA256: `e490e3238a7373568881963e1aa2b7f413640beb0426232f785b805a078919fb`; seeds `[700000,700040)`.

## Aggregate alternative cost contrasts

| method | eligible cells | delta vs Markov LR [95% paired CI] | cells lower cost | advance screen |
|---|---:|---:|---:|---|
| gap_envelope_rho08 | 11 | -0.0347 [-0.0393,-0.0301] | 11 | False |
| gap_envelope_rho95 | 11 | +0.0035 [+0.0021,+0.0048] | 1 | False |

## Null promotion by configuration

Full per-cell frequencies and Wilson intervals are retained in `summary.json`; no rate is an independent validity proof.

## Cellwise cost and decision metrics

Full per-seed records are retained in `records.jsonl`; the summary JSON contains cellwise means.

## Mandatory adverse-cost cells

Paired cost delta is candidate minus the lower-mean-cost reference among `episode_front` and `markov_lr_gate`; negative favors the candidate.

| method | cell | selected reference | delta mean [95% paired CI] | upper <= +0.01 |
|---|---|---|---:|---|
| gap_envelope_rho08 | `on0.6_L1_strong_harmful_d50_b0.05_s0.1` | episode_front | +0.0141 [+0.0076,+0.0206] | False |
| gap_envelope_rho08 | `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1` | episode_front | +0.1058 [+0.0865,+0.1251] | False |
| gap_envelope_rho95 | `on0.6_L1_strong_harmful_d50_b0.05_s0.1` | episode_front | +0.0141 [+0.0076,+0.0206] | False |
| gap_envelope_rho95 | `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1` | episode_front | +0.2476 [+0.2254,+0.2698] | False |


Advance gates are development stopping rules only. A passing row requires a newly frozen validation protocol.
