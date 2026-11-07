# 14. Real-data handoff (no real data accessed in this phase)

Freeze before any real-data use: `configs/sota_search/frozen_finalists_v1.json` (HG_brier γ=.99 gate 100; comparators pprm_tight, page_hinkley, cusum), α=.05, delay 5, tol 0, label rates 10%/20%, thresholds from `harness.calibrate`.
Required before a real-data claim: verified label timing, a decision cost grounded in the application, no reuse of exposed test periods, and calibration of Page–Hinkley/CUSUM on a real null segment. Stress tests of doc 12 (informative delay, dependence) must run first. Any real-data run must be a separate branch and protocol; results here carry no real-data evidence.
