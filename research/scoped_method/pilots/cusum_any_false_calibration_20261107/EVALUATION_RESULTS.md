# E-CUSUM independent evaluation results

**Decision: economic gate FAIL; stop this frozen CUSUM operating-point lane.**
The calibrated CUSUM passes the independent null screen but does not meet the primary
cost-improvement requirement against every registered comparator.

This is an empirical check of a known detector, not a novel-method result. All intervals
are paired two-sided 95% Student t intervals across shared episode seeds. Lower net cost is
better. The contract is T=2,000, B=200, label cost 0.05, switch cost 5, and alpha values
as frozen in `EVALUATION_FREEZE.md`.

## Cell outcomes and cost decomposition

Mean promotion time is conditional on promotion (the raw `-1` sentinel for never-promoted
episodes is excluded). Net cost equals predictive loss + label expenditure + switching
expenditure; expenditure is recomputed from mean counts and the frozen unit costs.

| Cell | Policy | Net cost | Predictive loss | Label cost | Switch cost | Labels | Switches | Promoted | Rollbacks | Mean first promotion if promoted |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_null | E_srr:gated_deployment | 369.59 | 359.56 | 10.00 | 0.03 | 200.00 | 0.006 | 0.006 | 0.000 | 983.50 |
| F0_null | E_swcert | 369.63 | 359.52 | 9.99 | 0.11 | 199.71 | 0.023 | 0.021 | 0.002 | 455.14 |
| F0_null | E_rb:gated_adaptive_range | 369.54 | 359.52 | 10.00 | 0.02 | 200.00 | 0.004 | 0.004 | 0.000 | 946.75 |
| F0_null | E_srrSR:gated_deployment | 369.66 | 359.56 | 10.00 | 0.11 | 200.00 | 0.021 | 0.021 | 0.000 | 1189.62 |
| F0_null | CONTROL_never_switch | 359.51 | 359.51 | 0.00 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | NA |
| F3_reversal_1200 | E_srr:gated_deployment | 398.56 | 381.74 | 10.00 | 6.83 | 200.00 | 1.365 | 0.990 | 0.375 | 585.68 |
| F3_reversal_1200 | E_swcert | 395.97 | 380.44 | 9.98 | 5.55 | 199.62 | 1.110 | 0.860 | 0.250 | 508.33 |
| F3_reversal_1200 | E_rb:gated_adaptive_range | 398.26 | 381.26 | 10.00 | 7.00 | 200.00 | 1.400 | 0.975 | 0.425 | 600.27 |
| F3_reversal_1200 | E_srrSR:gated_deployment | 400.17 | 383.35 | 10.00 | 6.83 | 199.99 | 1.365 | 0.995 | 0.370 | 598.79 |
| F3_reversal_1200 | CONTROL_never_switch | 377.63 | 377.63 | 0.00 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | NA |
| F3_reversal_800 | E_srr:gated_deployment | 394.90 | 377.18 | 10.00 | 7.72 | 200.00 | 1.545 | 0.875 | 0.670 | 541.91 |
| F3_reversal_800 | E_swcert | 398.87 | 382.58 | 9.98 | 6.30 | 199.68 | 1.260 | 0.800 | 0.460 | 426.86 |
| F3_reversal_800 | E_rb:gated_adaptive_range | 388.77 | 370.89 | 10.00 | 7.88 | 200.00 | 1.575 | 0.845 | 0.730 | 555.51 |
| F3_reversal_800 | E_srrSR:gated_deployment | 396.74 | 378.17 | 10.00 | 8.58 | 200.00 | 1.715 | 0.925 | 0.790 | 567.48 |
| F3_reversal_800 | CONTROL_never_switch | 346.45 | 346.45 | 0.00 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | NA |

## Null gate

The candidate promoted in 6/1000 independent `F0_null` streams; the
one-sided 95% Wilson upper bound is 0.01156. The frozen maximum was 0.05:
**PASS**. This does not establish a theorem or apply beyond the registered null.

## Paired cost contrasts

Candidate minus comparator in net cost; negative favors CUSUM. The primary criterion
requires both a mean of at most -5 and an upper 95% confidence limit below zero for each
registered primary comparator.

| Cell | Comparator | Mean paired difference | Paired 95% CI |
|---|---|---:|---:|
| F0_null | E_swcert | -0.03 | [-0.20, 0.13] |
| F0_null | E_rb:gated_adaptive_range | 0.05 | [-0.04, 0.14] |
| F0_null | E_srrSR:gated_deployment | -0.07 | [-0.17, 0.03] |
| F0_null | CONTROL_never_switch | 10.08 | [9.99, 10.16] |
| F3_reversal_1200 | E_swcert | 2.59 | [-1.20, 6.38] |
| F3_reversal_1200 | E_rb:gated_adaptive_range | 0.29 | [-2.68, 3.27] |
| F3_reversal_1200 | E_srrSR:gated_deployment | -1.61 | [-3.38, 0.15] |
| F3_reversal_1200 | CONTROL_never_switch | 20.93 | [17.53, 24.33] |
| F3_reversal_800 | E_swcert | -3.97 | [-9.09, 1.15] |
| F3_reversal_800 | E_rb:gated_adaptive_range | 6.13 | [1.84, 10.42] |
| F3_reversal_800 | E_srrSR:gated_deployment | -1.84 | [-5.30, 1.62] |
| F3_reversal_800 | CONTROL_never_switch | 48.45 | [44.56, 52.33] |

## Gate decision and interpretation

- Independent null gate: **PASS** (upper 0.01156).
- Primary cost gate: **FAIL**.
- Adverse short-reversal cost gate: **FAIL**.

The calibrated CUSUM is not cheaper than the strongest frozen certificate/RMM references
on the worthwhile reversal target and has large excess cost against never-switch. Its null
calibration is useful baseline-fidelity evidence, but the operating point does not repair
the economic failure. Per the frozen rule, do not adjust alpha or substitute another method
using these evaluation outcomes. No real data was opened.

## Raw artifact hashes

SHA-256 hashes bind every independent evaluation record file:

| Run | Records SHA-256 | Manifest SHA-256 |
|---|---|---|
| eval_candidate_null | `834541b89c9db12704feb1c5dfb7e245e7472a0e121fd82f7ed3c8acbeab276b` | `412ce7dfbacc0550aa5b52a9d404780fca5c34d92dee7019fef996bdf09ef2b6` |
| eval_candidate_reversal | `de847c4c46a41a665ad671ae40ce6aa0e1a399c981970f3686ed7562f6146527` | `212009622e37ef6c2f1da0c8b6bc08c232eb712601d07b09afde0bcc885f3473` |
| eval_references_null | `e016e34a5d0677e59173cb79401203af96360d7c8267e540c4541bd40c5379c2` | `df1fab1786b67fcb956f1304ea681371b83e6152910c206d710e30acd9161092` |
| eval_references_reversal | `57f54dfe8cf4e2d0402d713da30f0b31c3ff4dc94226156be6904137e1fb4631` | `0eb1770396a153973dadb5ca42d1d3e0d550bc3b0e0402051d6d9c042f48edbe` |
| eval_esr_null | `d081d73fd7c85491fbc041bb7adb0ebc32a3b0b1e9a86eacf3f2b45cfb8dbf56` | `0e90c775af3674ca51a5675087a4766671a30f8ba6a6accc826ba2b564bdc3d9` |
| eval_esr_reversal | `7d5e66bcdf979f9a3cbdcfb52ebc31b2a837808c2d7b3c6f95e93e2b64c7fd5c` | `6c3e2a2455198cca142b4b73edb0bc4fddd7cec91839c386eaf6cbdff4144e75` |
