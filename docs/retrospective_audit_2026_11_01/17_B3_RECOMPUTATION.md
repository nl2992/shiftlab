# B3 raw episode recomputation — 2026-11-01

Status: descriptive reproduction of historical evidence; G07 remains unsigned. Reviewer: lead, INTERNAL_ONLY. No independent statistical signoff.

Command: `python -B scripts/retrospective_audit/recompute_b3.py` (exit 0). All seven streams, all three stored settings, all five policy means and all four paired comparisons reproduce from raw `cost_seeds` arrays. Every bootstrap mean and both percentile endpoints match the historical summary within absolute tolerance 1e-9. No historical artifact was changed; no new confirmation was run. Input SHA-256 hashes and recomputed values are in B3_EPISODE_RECOMPUTATION.json.

| Stream | Episodes | Inference unit |
|---|---:|---|
| airlines | 50 | episode bootstrap; temporal independence not established |
| weather | 3 | conditional query randomization on these fixed episodes |
| spam | 1 | conditional query randomization on these fixed episodes |
| bank | 8 | episode bootstrap; temporal independence not established |
| rialto | 16 | episode bootstrap; temporal independence not established |
| elec2 | 4 | conditional query randomization on these fixed episodes |
| criteo | 50 | episode bootstrap; temporal independence not established |

The registered outcome remains WIN 3/7 (spam, weather, rialto), SAFE 7/7. P6 is cheaper on five primary streams; P3b is cheaper on spam and rialto. These counts were separately checked from summary arithmetic in B3_SUMMARY_ARITHMETIC.json.

The original protocol explicitly requests seed bootstrap when K<5 (`protocols/B3-real-data-certified-switching.md`, Metrics); the implementation follows it (`scripts/promising_directions/b3_real_data.py:597`). It is not a code mismatch. The corrected current interpretation must separate conditional randomization precision from across-episode generalization. A seed bootstrap on one spam tape cannot estimate population variability among future spam episodes. Nonoverlapping chronological episodes also do not establish temporal independence, so the episode bootstrap requires an additional dependence justification for population coverage.

SAFE is the registered descriptive inequality `mean(P3b) <= mean(P0) + .05*mean(P3b labels) + .02*mean(P0)`. It is not a test of noninferiority, a false-promotion guarantee, or a theorem about future switching utility. All release delays and economic parameters are imposed. P6's exchangeable-disagreement assumption is recorded in the protocol and is not verified by cheaper realized cost.

Remaining G07 requirements include boundary-null recalibration/B1-B2 reconstruction, comparator source fidelity, selection/exposure chronology, data-clock review, and independent critical review. No superiority over all comparators or independent new confirmation is claimed.

Audit-tool checks: `python -B -m pytest tests/retrospective_audit/test_recompute_b3.py -q` — exit 0, 3 passed. Checks reject duplicate episode IDs and inconsistent stored/raw means, and preserve low-episode conditional scope. Initial invocation failed from Windows default text decoding; explicit UTF-8 fixed the audit reader, then the complete reconstruction passed.
