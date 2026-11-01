# Research decision (interim, v2)
- **Carry forward as the strongest candidate:** H2c (Brier-guided discounted-Kelly betting on the decision-cost increment). Confirmed on an independent generator against the strongest cost-null comparator (+0.27 / +0.18 power, false alarm ≤ .011), with a stated cost-null guarantee. Not confirmed: advantage over Brier-evidence methods, other generators, random/outcome-dependent delay, real data.
- **Do not claim:** gated ONS improves on HG (C2b/C3b failed); any dependence-robust method (H3a only trades power for fewer false alarms); novelty (prior art unchecked; the construction is a composition of bounded-mean betting, prediction-powered increments and discounted Kelly).
- **Open:** G5, G6, delay stress, hard-budget audit, published-method reproductions, runtime/memory profiling, cross-method mechanism analysis, a frozen real-data protocol (candidate now exists: H2c).
- Legacy exit condition remains recorded as unmet.
