# P6 fixed Beta(2,1) restart prior: bounded development protocol

Registered before this experiment's outcomes are generated or inspected. This is a bounded
development comparison only; it cannot serve as untouched confirmation or establish method
novelty.

## Candidate and hypothesis

Candidate `P6_LRMD_BETA2` replaces P6's uniform finite restart-start prior with fixed integrated
Beta(2,1) bin masses `(2j-1)/n^2`, favoring later starts. The host, detector update, threshold,
acquisition, switching, costs, simulator and information rules are otherwise unchanged from
`P6_LRMD_U`. The predeclared directional hypothesis is lower mean net deployment cost on a late
improvement with a scarce label budget. This is a conventional prior-weight change; novelty is not
claimed.

## Frozen comparison

- Primary regime: `S_late_1500@B100`, 100 paired seeds, seed base `2026110713`.
- Secondary/adverse regimes: `F1_late_1200@B100`, `F6_delay400_better@B100`,
  `F3_reversal_800@B100`, `F0_better@B100`, `F5_dep_null_r8@B100`, each on the same 100 paired
  seed indices and seed base.
- Contract: existing simulator with `T=2000`, `c_q=0.05`, `c_s=5`, `alpha=0.05`, and hard
  query budget `B=100` in every listed regime. Label timing, budget enforcement, and pathwise
  pairing follow `screen.py` and the registered regime implementations.
- Fixed policy panel: `P6_LRMD_U`, `P6_LRMD_BETA2`, `PFA-SR:gated_adaptive_range`,
  `rmm:gated_adaptive_range+RMM`, `E_rb:gated_adaptive_range+front`,
  `gated_adaptive_range+front`, `CONTROL_never_switch`, and `xu_acquisition_only`.
  Xu is an acquisition-only adapter and is not represented as Xu's published certificate.
- Primary endpoint: per-seed difference in net deployment cost,
  `P6_LRMD_BETA2 - comparator`, where negative favors the candidate. Net cost includes prediction
  loss, requested-label cost and switch cost, as returned by the common simulator.
- Inference: paired 95% percentile bootstrap confidence intervals over the 100 seed blocks, using
  10,000 resamples and a fixed analysis RNG seed `2026110714`. Report the candidate versus every
  panel method on the primary regime; no post-hoc selection of a single comparator. Practical
  improvement is predeclared as at least 5 net-cost units in mean saving, with the paired interval
  entirely below zero against the strongest applicable published comparator on the primary regime.
- Safety/adverse reporting: report label and switch expenditures, promotion timing, false promotions
  on `F5_dep_null_r8`, and full paired cost intervals on every regime. No pooling across regimes to
  hide adverse outcomes. This 100-seed null panel is diagnostic, not a certification of a 5% error
  guarantee.

## Decision rule and stopping rule

If the candidate fails to achieve the primary improvement threshold against the strongest
applicable published comparator, or incurs a material adverse-regime cost, stop this candidate lane
without tuning. Even if it passes, the result remains development evidence because the weighting is
standard and the seed outcomes are used for this decision. No real-data confirmation will be opened
from this candidate without an independently justified novelty claim and a separately frozen,
untouched confirmation protocol.

## Reproducibility

- Source revision at registration: `f128988c` (`Add fixed beta-weighted P6 restart candidate`).
- Runner: `PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py`;
  analysis: this protocol's paired bootstrap endpoint. The first attempted launch omitted this
  import path and exited before generating any episode records; this correction was made before
  outcomes existed.
- Results path: `outputs/scoped_method/p6_beta2_bounded_development_20261107/` (kept out of Git
  if it contains bulky raw outputs; a compact summary and checksums will be registered in this
  folder).
- No new or previously locked real-data outcomes are part of this experiment.
