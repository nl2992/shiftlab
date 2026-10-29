# Correction to the T=10 stress output summary

Preserve `iid_relaxation_t10_stress_v1.json` unchanged. The candidate cost, exact
risk, lower bound, certified gap, robust-reference metrics and exhaustive
calendar results are valid. Two summary fields require correction:

1. The `certified_gap` fraction evaluates to approximately `1.5218859452e-11`,
   not `1.52e-6` as stated in an interim progress message. The exact fraction in
   the output is authoritative.
2. `resources.total_elapsed_seconds` is `3.534`, which is invalid because a
   per-calendar timer reused and overwrote the total-start variable. The recorded
   candidate, reference and exhaustive-calendar component times are respectively
   114.8448603s, 58.0138689s and 376.1029145s, for a measured component subtotal
   of 548.9616437s. Use those stage values and do not use the corrupted total.

The runner SHA in the original output identifies the executed source that
contains this timer bug. The result JSON is preserved; this note corrects its
interpretation without rewriting the output or rerunning the experiment.
