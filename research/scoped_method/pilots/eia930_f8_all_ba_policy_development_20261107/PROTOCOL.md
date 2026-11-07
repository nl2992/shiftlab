# EIA-930 F8 all-matching-BA policy development

**Status:** outcome-blind policy protocol, frozen after the profile-only gate passed. This is an
application comparison of existing published PFA-SR prior art, not a new-method claim.

## Question

On a real chronological replay with the frozen F8 rare-informative model-pair profile, does
`PFA-SR:gated_deployment` lower the registered net replay cost relative to (a) same-host RMM and
(b) the strongest feasible selector in the full frozen competitor panel? The panel includes CAMS,
which led Failure Atlas `F8_rare_better`; all methods run on the identical prediction/label stream,
horizon, feedback delay, pathwise budget, label cost, and switch cost.

## Population and split

Use all 11 BAs that passed the previously frozen profile screen, with no further selection:
`AZPS`, `BANC`, `EPE`, `ERCO`, `FMPP`, `FPC`, `MISO`, `NEVP`, `NYIS`, `SWPP`, `TIDC`. Refit the
same model separately on 2021 only; evaluate on 2022–2023 only. Partition valid observations into
nonoverlapping contiguous hourly 2,000-event episodes within each BA; discard incomplete tails and
never bridge a missing hour. This period is development because its profile was examined. Do not
open 2024 onward in this run.

Historical EIA values are current revised snapshots. The one-hour label-release delay is simulated.
The 11 BAs are correlated subclusters under one provider; they are not 11 independent data sources.
This is a real-data replay with simulated feedback, not observed deployment or actual electricity
market economics.

## Fixed model pair and costs

Use the trained-challenger `PROTOCOL.md` exactly: 2021 p90 actual-demand threshold; 24-hour
persistence incumbent; 2021-only HistGradientBoosting day-ahead challenger, fixed hyperparameters,
class weights, features, and missing/imputation rules. The episode target is binary high-load
classification. All methods receive only current predictions, observed labels after the simulated
one-hour delay, and their own past state.

For each 2,000-event episode: `T=2000`, pathwise label budget `B=200`, label price `0.05`, switch
cost `5`, delay `1`, and promotion alpha `.05`. Net replay cost is binary predictive errors + label
expenditure + switch expenditure. These are the Failure Atlas benchmark units, not field utility
estimates. Report the three components, labels, switches, promotions, rollbacks, and time to
promotion separately.

## Candidate and competitor panel

Primary candidate: `PFA-SR:gated_deployment`, using the existing PFA-weighted e-SR implementation
and existing gated host. No parameter tuning is allowed. Matched mechanism control:
`rmm:gated_deployment+RMM`. Frozen competitor panel:

`cams_adapter`, `online_llm_picker`, `model_selector_causal`, `model_picker_adapter`,
`gong_zhang_paid_obs`, `qiu_delayed_movement`, `variance_min_ipw`, `SMCS+retain-incumbent`,
`xu_acquisition_only`, `gated_deployment`, `gated_adaptive_range`, `E_rb:gated_deployment`,
`economic_replacement`, and `CONTROL_never_switch`.

Use the implementations in the frozen registry; report their fidelity labels and import errors.
In particular, Xu here is the ShiftLab acquisition-only adapter, not Xu's published certificate;
CAMS is the constant-policy adapter; this does not establish full native SOTA parity. The strongest
panel baseline is the minimum mean cost among the frozen competitors, calculated on this development
period and then explicitly frozen before any later confirmation window is opened.

## Seeds, estimands, and development gate

Use five paired policy seeds per BA/episode (`seed_base=2026110711` plus deterministic BA/episode
derivation). The primary contrasts are candidate minus same-host RMM and candidate minus the
strongest panel baseline in net cost per 2,000 events. Report each BA and an episode-clustered
paired 95% interval within BA; also report an equal-BA mean and an interval obtained by resampling
BAs then episodes. Mark that source-level inference is not available from this one provider. Do not
treat event rows, policy seeds, or the 11 BAs as independent providers.

Development signal for a separately frozen confirmation requires: (1) at least 5 units saved per
episode versus both RMM and the strongest panel baseline, (2) paired 95% intervals below zero for
both contrasts in at least 8 of 11 BAs, and (3) no BA with a statistically supported adverse cost
increase of 5 or more. The gate is intentionally not a claim of statistical significance across
independent providers. If it fails, retain all results and do not open the future years for this
candidate.

No conditional-null guarantee is claimed on serial EIA data. This experiment cannot estimate real
null promotion error because no known-null EIA episodes are available. No result here is independent
real-data confirmation or evidence of novelty.

## Reproduction and artifacts

Run from the repository root after verifying the checksums in the profile-stage source manifest:

```bash
uv run python scripts/sota_sprint/eia930/run_f8_all_ba_policy_development.py
```

The runner refuses to overwrite existing outcomes and writes a source/run manifest and paired
episode-level records under this directory. A positive development signal only permits a new frozen
protocol before any 2024+ outcomes are opened.
