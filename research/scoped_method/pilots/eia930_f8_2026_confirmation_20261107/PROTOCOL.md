# EIA-930 F8 static-challenger temporal confirmation

**Status:** frozen before retrieving or scoring the 2026 EIA outcome rows. Tests the already frozen
F8-selected challenger control on a new temporal window. No method novelty is claimed by this test.

## Question and scope

For the 11 EIA-930 balancing authorities (BAs) that met the registered F8 profile on 2022–2023
development streams, does the preselected static challenger retain a net-cost advantage over CAMS
on the chronologically later 2026 period? Does it outperform other registered methods under the
same information, horizon, label budget, and costs?

This is a held-out temporal replay on one EIA data provider. BAs are the analysis clusters; they are
not independent provider-level sources. The result cannot establish cross-provider generalization,
operational economics, or real-time availability of revised historical values. Label and switching
prices are hypothetical Failure Atlas units.

## Source and protected period

- Source: EIA official electricity balancing authority bulk archive `https://www.eia.gov/opendata/bulk/EBA.zip`.
- Frozen snapshot retrieved 2026-10-20; required SHA-256:
  `3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f`.
- Evaluation dates: 2026-01-01 00:00 UTC through the last complete common test event available,
  bounded by 2026-10-19. The preexisting coverage audit inspected only coverage, not 2026 outcomes.
- Fixed BA registry, inherited without filtering from the completed 2022–2023 profile gate:
  `AZPS, BANC, EPE, ERCO, FMPP, FPC, MISO, NEVP, NYIS, SWPP, TIDC`.
- Raw archive values are current revisions. The EIA source does not provide point-in-time feature
  publication logs. Event-time replay and one-hour feedback maturity are explicit approximations.

## Frozen model pair and event contract

Recreate the exact existing pair per BA: incumbent is 24-hour persistence; challenger is the
registered `HistGradientBoostingClassifier` fit only on eligible 2021 rows using the existing
feature and threshold definitions. Training p90 demand threshold, class weights, fixed model
parameters and 0.5 decision threshold are taken unchanged from
`research/scoped_method/pilots/eia930_f8_all_ba_development_20261107/PROTOCOL.md`.

At event hour `t`, the predictor sees day-ahead forecast for `t`, actual-demand lags through `t-1`,
rolling summaries ending at `t-1`, and UTC calendar features. It predicts whether actual demand at
`t` exceeds the BA's 2021 p90 threshold. Exclude the same rows as the development protocol, including
rows with imputed demand. Do not carry values across gaps. A requested label matures at `t+1h`, the
same assumed delay as development. Prediction/event and feedback times are retrospective source
times, not verified publication times.

The candidate is fixed before the confirmation window is opened: always deploy model 1 (challenger),
request zero labels, and charge one switch cost of 5 at each episode start. Its model choice follows
the 2022–2023 frozen profile screen and development control audit. No 2026 profile, outcome, or
episode may change that choice.

## Episodes, costs, and methods

Within each BA, form non-overlapping episodes of 2,000 consecutive eligible hourly events. Do not
join across any missing hour; report all dropped gaps, incomplete runs, and incomplete tails. Reset
policy state and budget per episode. Contract: `T=2000`, pathwise label cap `B=200`, label price
`0.05`, switch price `5`, `alpha=0.05`, one-hour assumed feedback delay.

Primary comparator: `cams_adapter`, frozen as the strongest published-method Atlas F8 discovery
comparator. Secondary panel, all registered before 2026 scoring: PFA-SR on the gated deployment
host; corrected RMM; E_rb; SMCS+retain-incumbent; Xu acquisition-only; gated deployment; CAMS;
Model Selector adapter; Model Picker adapter; Online LLM Picker; Gong-Zhang; Qiu; variance-min IPW;
economic replacement; fixed incumbent; never switch; and fixed challenger. Published-method labels
and adapter status follow the existing baseline fidelity table. Every method sees the same model
predictions, event order, label queue, episode boundaries and costs.

Primary outcome is net cost per 2,000 events, decomposed as predictive errors + label expenditure +
switch expenditure. Also report labels, switches, first promotion time, promotion and rollback
counts, predictive loss, budget violations, and cost-identity residuals. Compare candidate minus
CAMS with equal-BA weighting. The frozen pass criterion is mean savings of at least 5 units per
episode and an upper endpoint below zero for a paired 95% hierarchical bootstrap interval that first
resamples BAs and then whole chronological 2,000-event episodes within BA (10,000 draws, seed
`2026110719`). Provide BA-specific intervals and every BA result. The single-provider limitation
remains even if this gate passes.

## Outcome lock and stop rules

Before accessing 2026 outcome metrics, save a test-opening marker with source, protocol, code and
training-model hashes; BA list; exact test period; and command. The evaluator must refuse to overwrite
existing results. Never write row-level demand, predictions, losses or labels to Git. Stop before
scoring if the source hash differs, chronology or train-only fitting cannot be verified, an outcome
was previously scored, predictions use future features, source gaps are bridged, or labels mature
before their assumed release time. Preserve failures and negative BA/regime results.

Artifacts: frozen prediction-stream hashes, source receipt, eligibility/gap audit, complete
episode-by-method records without raw rows, per-BA and aggregate decomposition, paired uncertainty,
reproducibility manifest, run log, and interpretation report.
