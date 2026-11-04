# Versioned challenger: corrected real-data label provenance screen

**Status:** exploratory development only. One deterministic run per dataset, on five already
exposed chronological datasets. This is not independent confirmation, population inference, or a
SOTA claim.

## Why this rerun was necessary

An independent code audit found that the prior “charged” versioned real-data runner trained v2 on
`y[:train2_end]`. That included all 1,000 outcomes in the preceding v1 scored window, even though
they were not all purchased by any policy. The runner charged only 100 new training labels. This
was label leakage and understated the cost; it invalidates the previous versioned real-data cost
comparisons, including the rollback comparison. See the prior report's invalidation notice and the
corrected runner below.

## Corrected protocol and provenance

- Runner: [`scripts/sota_sprint/versioned_real_dev.py`](../../scripts/sota_sprint/versioned_real_dev.py).
- Source checkout at execution: branch `research/continuation-2026-11-04`, HEAD `de9aaaa3`
  (uncommitted development edits); runner SHA-256 `91ccab55cc83658a2ac236f7a4b27976bf5d67527be28b244b4099e4fbf4ef36`.
- Raw output: `outputs/sota_sprint/versioned_real_dev_provenance_fixed_2026-11-04/records.json`
  (ignored/local), SHA-256 `cc53f8dd784330b2a01fce8e0f4d4f4fd4359428109b1ecc45e43b30b14694ee`.
- All five streams use the registered chronological UCI loaders and two 1,000-event scored
  windows. The 100-row training block lies between windows and is not scored.
- v2 fits on the common sunk initial labeled prefix plus exactly the 100 purchased labels from the
  boundary block `[train2_start, train2_end)`. No labels from the preceding scored window enter v2.
  Preprocessing is fit on those same known training rows. Model indices are immutable across both
  windows.
- Every policy pays the same 100 training-label costs and receives a 100-label query budget from
  the total 200-label cap. Comparator pacers are constructed with that remaining 100-label budget.
- Same fixed policy seeds and one run per dataset as the prior development screen. There is no
  across-dataset population claim; the five datasets were already exposed during development.

## Corrected results

Net costs include prediction error, the 100 purchased training labels, policy query cost, and switch
cost. Lower is better. The table is descriptive, with no inferential interpretation.

| Dataset | v0/v1 error, window 1 | v0/v2 error, window 2 | Version gate | Rollback gate | RMM | Front cert | Model Picker |
|---|---:|---:|---:|---:|---:|---:|---:|
| metro | .332 / .043 | .293 / .043 | 111.85 | 113.10 | 140.00 | 120.15 | 110.65 |
| beijing_pm25 | .350 / .350 | .234 / .141 | 523.85 | 524.75 | 527.00 | 594.00 | 510.10 |
| bike_hour | .339 / .069 | .267 / .069 | 183.55 | 179.40 | 190.00 | 176.35 | 167.25 |
| appliances | .396 / .205 | .440 / .213 | 470.80 | 470.75 | 578.00 | 471.00 | 458.75 |
| household_power | .365 / .333 | .348 / .448 | 826.00 | 827.20 | 829.00 | 826.35 | 822.25 |

| Policy | Mean cost | Mean total labels (training + query) | Datasets promoting |
|---|---:|---:|---:|
| Version gate | 423.21 | 152.2 | 5/5 |
| Version gate + rollback | 423.04 | 164.8 | 5/5 |
| Version gate, post-hoc 1:3 allocation | 421.86 | 137.2 | 5/5 |
| RMM | 452.80 | 200.0 | 5/5 |
| Front-loaded certificate | 437.57 | 159.4 | 4/5 |
| Version-aware Model Picker | 413.80 | 136.0 | 5/5 |

Across these five selected streams, version gate minus RMM averaged −29.59 cost units (descriptive
SE 19.96), and minus front certificate −14.36 (SE 14.16). It cost +9.41 more than Model Picker
(SE 2.94), with Model Picker lower-cost on all five datasets. The rollback monitor changed mean
cost by only −0.17 relative to the promotion-only gate (SE 1.02); the post-hoc 1:3 allocation
changed mean cost by −1.35 (SE 1.64). These tiny, exposed-sample comparisons do not support
choosing those variants.

Household power still contains a real-looking reversal: v1 improves from .365 to .333 error in the
first scored window, then has .448 error versus the .348 incumbent in the second. The corrected v2
training procedure does not repair it: v2 has .448 error too. Version gate promotes v1 at event 276
and does not roll back in this corrected run. This is descriptive evidence of a model-update failure
case, not evidence that the proposed gate improves deployment outcomes.

## Decision

The corrected accounting restores a fair comparison and shows that the version gate can beat the
certified comparators on this selected panel while remaining more costly than the fast Model Picker.
The RMM comparison is especially sensitive to appliances. Do not claim a practical improvement yet.
The next useful step is an independent, label-provenance-correct evaluation on streams with
predeclared retraining times, including no-improvement, improvement, and degradation cases, plus a
strong Model Picker / active-selection comparator. A valid null calibration and an independent
novelty audit are still required.
