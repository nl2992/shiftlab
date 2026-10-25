# Delayed PPI fixed-start mixture: development grid results

**Development nomination: FAIL.** The 60-seed CUDA grid completed all 720 planned rows. The fixed equal-weight mixture improved detection in this setting, but the closed-loop comparison also changed evidence-directed query decisions and used more labels, so it did not meet the preregistered cost-constrained advancement rule.

For the primary evidence-directed query policy, equally averaging the three onset fractions gave 65/180 post-onset detections (36.1%) for the eight-start mixture and 35/180 (19.4%) for the full-stream monitor. The paired difference was **+16.7 percentage points** (seed-cluster bootstrap 95% interval [+9.4, +24.4]); the paired rows had 34 mixture-only and 4 full-stream-only detections. The mixture used **49.7 more labels per stream** on average (95% seed-cluster interval [+38.3, +60.6]), so the frozen requirement of no higher label use failed. There were no cap violations, unresolved labels, event-count mismatches, or pre-onset alarms.

| Harm onset | Evidence query: full stream | Evidence query: start mixture | Uniform query: full stream | Uniform query: start mixture |
| --- | ---: | ---: | ---: | ---: |
| 25% (event 600) | 22/60 (36.7%) | 37/60 (61.7%) | 28/60 (46.7%) | 41/60 (68.3%) |
| 50% (event 1,200) | 12/60 (20.0%) | 21/60 (35.0%) | 6/60 (10.0%) | 28/60 (46.7%) |
| 75% (event 1,800) | 1/60 (1.7%) | 7/60 (11.7%) | 0/60 (0.0%) | 9/60 (15.0%) |

In the evidence-query arm, the start mixture increased mean labels at each onset: 243.0 versus 184.1 (early), 221.9 versus 169.0 (middle), and 187.5 versus 150.3 (late). Under uniform querying, the monitor variants shared the same query rule and the mixture used slightly fewer labels on average, but this was not the primary registered contrast. The evidence-directed policy uses its monitoring e-value to set future query propensities, so changing the monitor changes both monitoring and acquisition; this grid therefore evaluates a joint closed-loop policy rather than isolating monitor power at equal acquisition cost.

The result does **not** advance the mixture to independent calibration under the frozen rule. A separately frozen, fresh-seed shadow-monitor comparison will hold acquisition propensities fixed using the full-stream monitor and continue both shadow monitors through the same event horizon. That follow-up will isolate whether the start mixture improves detection when labels and costs are exactly matched. The e-process convex-mixture argument is standard and is not claimed as a new theorem or algorithm. See the frozen [development protocol](delayed_evidence_ppi_start_mixture_grid_protocol.md) and complete [CSV/Parquet metrics and manifest](../outputs/delayed_evidence_ppi_start_mixture_grid_60/).
