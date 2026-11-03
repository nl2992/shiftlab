# B2 stored-seed reproduction — 2026-11-01

`python -B scripts/retrospective_audit/recompute_b2.py`: exit 0; four settings; zero mismatches in all policy world-average costs, selected comparator, paired means, original percentile intervals and relative reductions. Savings are 10.2017448%, 9.6450041%, 7.8769032%, 7.6726023%. Equal weights on four synthetic worlds and 500 seed indices reproduce the historical estimator. No simulator or boundary-null study was rerun.

Historical MIXED remains unchanged. BEST is the minimum evaluated average among P0/P1/P2, chosen on the same evaluation seeds. The existing bootstrap holds that selected comparator fixed; it is not selection-adjusted inference for a prespecified deployable baseline. Full train/dev/frozen comparator selection or nested resampling remains required. P6/fixed-batch parity is absent from these stored comparisons and must be examined separately. Numerically positive descriptive effects do not establish method novelty or conditional-null validity.

Source metadata records created_utc=2026-10-30T21:12:00.354972+00:00 and seed_base=20261101. A numeric seed is not an execution date. The fair reevaluation describes fresh seeds, but protocol-before-exposure chronology requires Git/provenance inspection rather than inference from the seed integer. No chronology violation is concluded from this metadata alone.

Exact world means and original intervals are in B2_RECOMPUTATION.json. G07 remains unsigned; reviewer is lead INTERNAL_ONLY.
