# Family-R held-out Track-R coverage follow-up

Registered 2026-11-05 before running this panel. The current Family-R Track-R calibration map
contains 30 policies. Seventeen have at least one held-out operating point in the original report;
nine additional policies have a development-feasible alpha for at least one R5–R30 target but no
evaluation point because they were absent from the original eval screens. This follow-up evaluates
the 26 policies with at least one development-feasible operating point on one common new evaluation
seed block. Four policies with no feasible alpha at any target and policies with no executable risk
calibration are excluded from this policy panel and remain recorded in the original calibration map.

## Question and estimand

Do the existing development-selected alpha operating points for the eligible Family-R policies
retain their empirical null-promotion frequency and alternative net cost on a new seed block? The
alpha-selection map is frozen to the committed `outputs/sprint2/R/analysis/risk_curves.json`
development map. No threshold is reselected or changed after this registration. The estimate uses
the existing `risk_curves.py` procedure: pooled promotion rate across `bench2.RISK_NULLS`, pooled
alternative net cost across `bench2.RISK_ALTS`, Wilson 95% risk intervals and t intervals over
per-seed alternative means. Pareto flags are local to this 26-policy follow-up panel.

This is a new simulator replicate on reused regimes, not independent real-data confirmation or a
formal guarantee. It does not replace the original Family-R output; the follow-up is reported
separately so the original evidence remains immutable.

## Frozen policies and execution

Eligible policies are `A5b`, `C6`, `CONTROL_never_switch`, `D2`, `H1-iid1`, `H2`, `R2`,
`R2-floor25`, `R2-qc`, `R3-alloc`, `R3-base`, `R3-near`, `R3-plugin`, `R3-plugnear`, `R4-both`,
`R4-comb`, `R5`, `R6:D2-always`, `R6:D2-floor25`, `R:economic_stop`,
`R:xu_acquisition_only@alpha`, `SMCS+retain-incumbent`, `choe_ramdas_eb+front`,
`gated_adaptive_range+front`, `gated_deployment`, and `xu_acquisition_only`.

- Alpha grid: `bench2.ALPHA_GRID` = `.005, .01, .02, .05, .1, .2, .3, .5`.
- Regimes: the four `bench2.RISK_NULLS` and six `bench2.RISK_ALTS`.
- Development calibration: the immutable existing development runs used for the original
  `risk_curves.json` (`dev_screen_a05`, `trackR/dev_a*`, and `trackR_H/dev_a*`).
- Evaluation: 20 seeds per regime, seed base `2026111311`, all eight alpha values.
- Runner: `scripts/sota_sprint/run_r_trackr_coverage_followup.sh`.
- Derived report: `risk_curves.py` over the existing development directories and the eight new
  evaluation directories. Per-run manifests and record hashes will be indexed before reporting.

The evaluated policy set and alpha grid are frozen. Policies without any development-feasible
point are not assigned an evaluation operating point after seeing these results.
