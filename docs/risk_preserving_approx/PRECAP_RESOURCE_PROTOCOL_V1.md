# Pre-promotion cap: repeated resource comparison protocol v1

Registered 2026-10-29 after the initial cap screen and full T=7 certificate, but
before this timing run. This is a repeated performance check on the same known
models, not independent efficacy or confirmation.

Compare the unchanged first-promotion oracle (B=3) and pre-promotion cap m=2,
both with full B=3 after first promotion. Use the same registered HMM and costs
as `PREPROMOTION_CAP_PROTOCOL_V1.md`, T in {6,7,8}, five fresh-process repetitions
per algorithm per horizon. Alternate order on successive repetitions. Use the same
200,000 node and 60-second LP limits. Record each process's build, solve and
independent exact policy-evaluation times, objective, recovered cost/risk, solver
residuals, node and variable counts, continuation-cache size and failures.

Measure peak working set from *inside the actual worker interpreter* using
`psutil.Process().memory_info().peak_wset` on Windows. Record the worker PID and
method; if unavailable or unsupported, report memory unavailable, not launcher
RSS. Record Python, package versions, process hashes and all raw repetitions.
Require each policy's full causal-null risk <=1/10 or record its exact safe root
repair. Check T=6 m=2 against its verified lower certificate and T=7 m=2 against
`full_t7_certificate_v1.json`; report exact a-posteriori gap bounds. T=8 has no
independent completed full-sequence oracle certificate. Full B=3 m=2 can exceed
the restricted pre-promotion cap only after the first promotion; retain delay,
query and switching semantics.

Report medians and all individual measurements; avoid general complexity or
statistical-efficacy conclusions. Preserve failures without replacing cells. This
comparison is against the exact solver, not the full set of strong research
baselines. No synthetic seeds or real data/holdouts are opened. Store new output
without overwriting earlier screens.
