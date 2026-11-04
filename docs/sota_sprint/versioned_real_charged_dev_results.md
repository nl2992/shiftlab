# Versioned challenger: prior charged results invalidated

**Status:** do not use the former results in comparisons or claims.

An audit found that the previous runner trained v2 with `y[:train2_end]`, which included every
label from the 1,000-event v1 scored window while charging only the 100-label boundary training
block. Those outcomes were not all purchased by the policies. The prior cost comparison therefore
used unacquired training labels and understated v2 training cost. This invalidates the tables and
rollback comparison formerly recorded in this file.

The runner now trains v2 on only the common initial labeled prefix and the exactly 100 purchased
boundary labels. Comparator acquisition schedules receive the same remaining 100-label query
budget. Corrected descriptive results and hashes are recorded in
[`versioned_real_provenance_fixed_results.md`](versioned_real_provenance_fixed_results.md).
