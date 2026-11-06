# Heavy-tail PFA-SR development screen results

**Decision:** candidate failed its frozen development gate. This finite-budget tail-prior
parameterization does not merit confirmatory evaluation. It is reported in full and does
not revise the earlier canonical PFA-SR confirmation.

The run has 30 paired streams per cell and 840 policy rows. Net cost is loss + 0.05 × labels
+ 5 × switches. Intervals are paired two-sided 95% t intervals over the shared seeds; no
multiplicity correction. This is a development screen, not independent confirmation.

## All policies

| Cell | Policy | Net cost | Loss | Labels | Switches | Promotions | Rollbacks |
|---|---|---:|---:|---:|---:|---:|---:|
| PFA_tail_late_scarce@B100 | `CONTROL_never_switch` | 429.30 | 429.30 | 0.0 | 0.00 | 0/30 | 0.00 |
| PFA_tail_late_scarce@B100 | `xu_acquisition_only` | 430.38 | 424.80 | 94.9 | 0.17 | 5/30 | 0.00 |
| PFA_tail_late_scarce@B100 | `E_rb:gated_adaptive_range` | 429.17 | 422.67 | 100.0 | 0.30 | 9/30 | 0.00 |
| PFA_tail_late_scarce@B100 | `rmm:gated_adaptive_range+RMM` | 429.17 | 422.67 | 100.0 | 0.30 | 9/30 | 0.00 |
| PFA_tail_late_scarce@B100 | `E_swcert` | 432.16 | 426.00 | 99.9 | 0.23 | 7/30 | 0.00 |
| PFA_tail_late_scarce@B100 | `PFA-SR:gated_adaptive_range` | 430.07 | 424.57 | 100.0 | 0.10 | 3/30 | 0.00 |
| PFA_tail_late_scarce@B100 | `PFA-SR:q1.2:gated_adaptive_range` | 434.47 | 429.30 | 100.0 | 0.03 | 1/30 | 0.00 |
| PFA_confirm_persistent | `CONTROL_never_switch` | 487.00 | 487.00 | 0.0 | 0.00 | 0/30 | 0.00 |
| PFA_confirm_persistent | `xu_acquisition_only` | 393.94 | 379.47 | 192.9 | 0.97 | 29/30 | 0.00 |
| PFA_confirm_persistent | `E_rb:gated_adaptive_range` | 378.60 | 363.77 | 200.0 | 0.97 | 29/30 | 0.00 |
| PFA_confirm_persistent | `rmm:gated_adaptive_range+RMM` | 378.60 | 363.77 | 200.0 | 0.97 | 29/30 | 0.00 |
| PFA_confirm_persistent | `E_swcert` | 406.49 | 392.00 | 199.8 | 0.90 | 27/30 | 0.00 |
| PFA_confirm_persistent | `PFA-SR:gated_adaptive_range` | 367.70 | 352.70 | 200.0 | 1.00 | 30/30 | 0.00 |
| PFA_confirm_persistent | `PFA-SR:q1.2:gated_adaptive_range` | 367.40 | 352.40 | 200.0 | 1.00 | 30/30 | 0.00 |
| PFA_confirm_null | `CONTROL_never_switch` | 399.77 | 399.77 | 0.0 | 0.00 | 0/30 | 0.00 |
| PFA_confirm_null | `xu_acquisition_only` | 410.56 | 400.63 | 195.3 | 0.03 | 1/30 | 0.00 |
| PFA_confirm_null | `E_rb:gated_adaptive_range` | 409.77 | 399.77 | 200.0 | 0.00 | 0/30 | 0.00 |
| PFA_confirm_null | `rmm:gated_adaptive_range+RMM` | 409.77 | 399.77 | 200.0 | 0.00 | 0/30 | 0.00 |
| PFA_confirm_null | `E_swcert` | 409.75 | 399.77 | 199.7 | 0.00 | 0/30 | 0.00 |
| PFA_confirm_null | `PFA-SR:gated_adaptive_range` | 409.77 | 399.77 | 200.0 | 0.00 | 0/30 | 0.00 |
| PFA_confirm_null | `PFA-SR:q1.2:gated_adaptive_range` | 409.77 | 399.77 | 200.0 | 0.00 | 0/30 | 0.00 |
| F3_reversal_800 | `CONTROL_never_switch` | 343.30 | 343.30 | 0.0 | 0.00 | 0/30 | 0.00 |
| F3_reversal_800 | `xu_acquisition_only` | 406.46 | 389.23 | 197.9 | 1.47 | 27/30 | 0.57 |
| F3_reversal_800 | `E_rb:gated_adaptive_range` | 387.97 | 369.47 | 200.0 | 1.70 | 26/30 | 0.83 |
| F3_reversal_800 | `rmm:gated_adaptive_range+RMM` | 397.67 | 379.67 | 200.0 | 1.60 | 26/30 | 0.73 |
| F3_reversal_800 | `E_swcert` | 394.95 | 377.63 | 199.7 | 1.47 | 26/30 | 0.60 |
| F3_reversal_800 | `PFA-SR:gated_adaptive_range` | 406.80 | 388.80 | 200.0 | 1.60 | 30/30 | 0.60 |
| F3_reversal_800 | `PFA-SR:q1.2:gated_adaptive_range` | 401.27 | 383.93 | 200.0 | 1.47 | 27/30 | 0.57 |

## Frozen primary paired contrasts: late improvement with delay and B=100

Candidate minus comparator net cost; a pass requires at least 5 units savings and the
entire 95% interval below zero against canonical PFA-SR, same-host RMM and Xu adapter.

| Comparator | Difference [95% CI] | ≥5-unit gate |
|---|---:|---|
| `PFA-SR:gated_adaptive_range` | +4.40 [-1.27, +10.07] | no |
| `rmm:gated_adaptive_range+RMM` | +5.30 [-0.01, +10.61] | no |
| `xu_acquisition_only` | +4.09 [-0.48, +8.66] | no |

## Gate and interpretation

Primary late/scarce gate passed: `False`.
Null promotions: 0/30 (screen only).
Reversal candidate-minus-never mean: +57.97 [+48.50, +67.44].
Adverse/null development gate passed: `False`.

The candidate did not clear the primary gate. In the registered late/scarce cell it
cost 4.40 more than canonical PFA-SR [−1.27, +10.07], 5.30 more than same-host RMM
[−0.01, +10.61], and 4.09 more than Xu [−0.48, +8.66]. It promoted 1/30 times
versus 3/30 for canonical PFA-SR and 9/30 for same-host RMM; lower promotion here came
with no cost advantage. In the reversal cell it cost materially more than never-switch.
The candidate is stopped under its frozen development rule. A positive strong-persistent
PFA-SR result remains the earlier published-method application signal, not evidence for
this heavier-tail adjustment.

Maximum net-cost accounting residual: 0.

## Provenance

- Run manifest SHA-256: `3cf79254fdbaf4cd1ad17f78453f0c40285ad50100423cf9bce9214149fd4dc7`.
- Raw records SHA-256: `4a3c37dbd5cbd5e7577c3003340fe4a1f8d3d04008220b6680514f15e7e97984`.
- Frozen protocol SHA-256: `b6b14d2b08635e8ec899d6c7656b24609226113a05c9b1ceb918ccaa87d7c0c1`.
- Candidate source SHA-256: `0bb017f3ce4a68556d28b66969b558db442fdfdb083f0ae0aba16bae55e5b085`.
- Source revision in run manifest: `dff49b111aa5d2b472fa13379fa52c57f42522c1`.
