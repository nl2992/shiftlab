# Upworthy headline policy selection — frozen holdout

**Status:** fixed-horizon project-held-out evaluation; aggregate CTR only.

Eligible holdout tests: 3,808 across 18,278 package arms.

The text-only policy achieved equal-test CTR 0.014455; uniform package choice achieved 0.013453; paired difference was +0.001002.

The week-clustered 95% interval for the difference was [+0.000850, +0.001170], with one-sided 95% lower bound +0.000872.

Selected `C`: 0.01. Grouped-CV contrasts by `C`: `{'0.01': 0.000763156615125184, '0.1': 0.0007441463157754362, '1.0': 0.0007009893400772256, '10.0': 0.0007311086664354962}`.

This does not test online monitoring, delayed labels, intervention costs, or net business utility. See `summary.json` and `per_test_metrics.csv` for aggregate evidence and provenance.
