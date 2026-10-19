# Full Phase 1 completion audit — in progress

The user objective is the entire comprehensive data brief, not just its minimum working-source
gate. The preceding version-control turn made verified progress (commits, hooks and a clean
worktree). This continuation has added source adapters, structured references, task definitions
and decision-stress controls. Full completion is still unproven.

| Brief section | Current evidence | Remaining work / verification |
|---|---|---|
| A: architecture | Functional modules under `data/`, no empty scaffold; legacy API retained | Continue separating functional components when needed, not empty names |
| B: schema/observability | Schema 1.1, numeric/structured references, immutable Request/Label, oracle-only files; delayed-feedback tests | Audit every new adapter and shared benchmark for the same invariants |
| C1: controls | IID/nonlinear/AR1/ARMA/GARCH/heteroskedastic/t5 implementations and replicated tests | Broaden analytic temporal variance validation; recheck stationarity after changes |
| C2: covariates | Mean, variance, rotation, correlation, mixture, new component, tails/skew, nuisance shifts | Per-mechanism independent covariance/conditional checks beyond generic oracle-risk tests |
| C3: targets | Prior/imbalance/corruption/level/variance/tail frequency and explicit factorization table in `docs/dgp_factorizations.md` | Preserve distinctions between pure class-prior shift, observed-label corruption, and conditional regression shifts |
| C4: concept | Coefficient/nonlinear/interaction/sign/latent/variance changes with gradual patterns | Independent oracle conditional-function interface and complete parameter-by-regime metadata |
| C5: temporal | Nine patterns; true times or intervals stored; zero-strength null | Adversarial timing below; source schedule tests cover current patterns |
| C6: decisions | Nuisance/boundary/cost/constraint controls; new small covariate and rare-high-cost cases; actual indistinguishable generated worlds when labels missing | Bind all ten requested case names to documented policy/loss/oracle definitions in a preset catalogue |
| C7: conformal stress | Normal/t5/lognormal/mixture CDF quantiles, conditional/marginal variance labels, delayed/missing calibration data | Complete named case presets and check conditional-vs-marginal targets in every report |
| C8: adaptation stress | Compute-budget accounting, deployment/transient-loss controls, ex ante adversarial pattern; executed Gaussian fixed-candidate full-information reference; named contrast map | Oracle is intentionally restricted to independent single-update decisions, not a dynamic controller or a fitted-update guarantee; task-specific recalibration references still required |
| C9: performative | Separate interactive state/action environment, causal specification, verified stable AR1 variance, joint actions, local saturation and explicit unstable state dynamics | Preserve distinction between local feedback instability and global divergence |
| D: parameter plans | Balanced marginal plan covers all listed levels in 12 profiles with 30 paired seeds; executed resource/coverage preview; smoke/medium/GPU presets | Scientific interaction selection and final 100-seed experiments are user-configurable; no power guarantee |
| E1: Folktables | NJ 2018 ACSIncome acquired; five task adapters | Selected CA/NY/TX/FL/NJ cross-year panel, all five task executions, explicit domain comparison plans |
| E2: gas | Ten batches, 13,910 rows, 128 features; actual per-batch class/missingness/feature tables and train-only classifier/probability/decision-loss evidence | Unknown within-batch order prevents temporal inference; IID descriptive SE is explicitly qualified |
| E3: OPSD | DE/DE-LU + DK_1 hourly/daily task configs with load/wind/solar/prices; overlapping coverage gate, full-day missingness, source definitions/UTC/local offsets and outcome-end purging | Price zones and country load remain distinct; availability unknown; bad early epoch version stays retired |
| E4: EIA | Credentialed v2 adapter, paging, units/calendar gaps, sanitized snapshots; fixtures | Live key absent: documented external prerequisite, no false acquisition claim |
| E5: NOAA | JFK/Boston/Chicago 2023 fixed panel acquired; seven weather/accumulation fields, flags, strict-later same-station outcomes and shared purged event-time splits | Availability remains unknown; irregular source horizons must not be described as strictly hourly forecasts |
| E6: Monash | Five verified record mappings; TSF parser; official fixed-origin holdouts; M4 hourly downloaded with publisher MD5 match | Exercise other prioritized formats and preserve actual declared horizons; no invented covariates |
| E7: WILDS | Five lazy adapters; real package/metric fixture test; native-equivalent reduction compatibility | Live source certificate expired (upstream issue documented); do not bypass TLS or substitute another benchmark |
| E8: Criteo | Source/license/size verified; delayed outcomes and censoring adapter; fixtures | Linked archive unavailable; delay units must be verified from an accessible source README/local export |
| E9: Binance | BTCUSDT daily and ETHUSDT January 2025 hourly acquired; publisher SHA256, exact UTC month/bar endpoints and ms/us precision validated | Historical release latency remains unknown; no invented online availability |
| E10: FRED/ALFRED | Vintage intervals, as-of selector, conservative date-resolution availability, fixtures | Live key absent; explicit dated-vintage forecasting task rather than treating revised levels as past features |
| E11: licensed | Local import with license, original fields, explicit timestamp mappings; fixture | No licensed dataset supplied; report that limitation rather than inventing one |
| F: tasks | Registered forecast/quantile/volatility/excess/binary/multiclass tasks; capacity/cost/abstention/bounded actions | Bind dataset task specs and utility provenance consistently; test source task horizons and masks |
| G: diagnostics | Means/covariance/frequencies/KS, moving-block intervals; regression plot/report | Residual/rolling loss, group performance, calibration and decision-loss evidence for supported real tasks, with valid assumptions and inconclusive attribution |
| H: GPU | RTX 4060 detected; actual CUDA generation/preprocessing parity and throughput; chunk/memory controls | Re-audit backend dtype/memory/determinism and device-utilization logging scope |
| I: storage/provenance | Immutable Parquet/JSON, raw checksums/receipts, atomic publication, code hashes; strong ETag/If-Range or publisher-hash resume; length/budget/encoding gates tested | Continue source-specific provenance audit and external input integrity checks |
| J: leakage | Future features/labels, chronological splits, training-only scaling, missingness and UTC/DST tests | Expand all these gates to new sources and derived tasks; validate schema across storage chunk boundaries |
| K: statistics | Replicated oracle-risk and selected moment/quantile/autocorrelation tests; rare-event uncertainty corrected | Broaden independent per-generator analytic checks and export executed statistical validation evidence |
| L: reports | Aggregate quality/provenance/readiness/shift/baseline reports and plots rebuilt for 52 stored versions; zero validation errors; NOAA figure visually inspected; historical summary explicitly labelled | Complete remaining source/task and independent statistical evidence; 52 versions include historical duplicates, not independent replicates |
| M: CLI | All named entry points functional; dry-run acquisition; clear credential/source errors | Exercise exact fresh CPU/optional GPU commands and new configs in final audit |
| N: milestones | Minimum foundation passed; broader milestones partially verified | Complete rows above and report remaining genuine external conditions honestly |
| O: completion gates | Earlier minimum gate evidence exists; actual source count now six | Final requirement-by-requirement audit remains required; do not mark goal complete yet |

Remote-repository setup is complete: private `https://github.com/nl2992/shiftlab`, `origin`
configured, `main` tracking `origin/main`, and the historical data-foundation tag pushed.
Raw/processed data and credentials remain ignored; aggregate evidence is version controlled.
