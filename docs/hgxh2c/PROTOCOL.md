# HG × H2c programme: protocol v1 (registered 2026-10-31, before any stage-2/3/4 result)

Status: design and registration. Nothing in this file is a result. Anchors: `00_ANCHOR_SPEC.md`
(H2c/HG formulas), `01_BASELINE_AUDIT.md` (existing ShiftLab implementations),
`02_NATIVE_REPRODUCTION.md` (author-code reruns).

Goal: find one or more bidirectional HG/H2c information-transfer mechanisms, or a deployable
selection rule over them, that lower cumulative cost relative to the strongest statistically
compatible baseline. Then show which transfer causes the gain and confirm its size on untouched
seeds. Pass/fail is decided by paired, multiplicity-adjusted inference against the frozen frontier.
There is no fixed relative-improvement bar such as 10%.

## 1. Stages and gates

| Stage | Output | Gate to next stage |
|---|---|---|
| 1 Native reproduction | `02_NATIVE_REPRODUCTION.md`, `outputs/hgxh2c/stage1/` | Each method gets a fidelity class. Unreproduced methods stay in, labelled with their class |
| 2 Common benchmark | `outputs/hgxh2c/stage2/frontier.json` (sha256 recorded in `FREEZE.json`) | Frontier frozen and hashed |
| 3 Combinatorial search | `outputs/hgxh2c/stage3/registry.parquet` (append-only), `finalists.json` | 3–5 finalists frozen and hashed, plus any selection rule |
| 4 Confirmation | `outputs/hgxh2c/stage4/confirmation.json`, `FINAL_REPORT.md` | — |

The orchestrator (`scripts/hgxh2c/pipeline.py`) enforces this order by checking hashes in
`outputs/hgxh2c/FREEZE.json`. It refuses to read confirmation seeds unless both the frontier and
finalist hashes are present.

## 2. Common event contract

Each scenario generates a latent tape with shape `[seeds, T]` (torch, GPU). Monitors only ever see
the released view.

- Free at issue time `t`: the proxy predictions `Bhat_t` (predictive loss) and `Chat_t` (economic
  cost), the deployed and reference actions, and the design constants (delay `d`, budget `B`, source
  calibration `theta_B`, `theta_C`).
- Labelled outcome: `B_t` (incumbent predictive loss, Brier in [0,1]) and `C_t` (economic excess cost
  of the deployed policy against the frozen reference, affinely normalised to [0,1] with a fixed
  map). Both become visible only if `Q_t = 1` and `t + d_t <= now`.
- Query: a monitor issues `q_t` in `[q_min, 1]`; `Q_t = 1{U_t < q_t}`, with `U_t` common across
  methods (common random numbers). The budget is pathwise: once `sum Q = B`, further queries are
  infeasible (`q_t := 0`). Methods that observe every label run with `q_t = 1` and pay for it.
- Evaluator only: change time `tau`, regime, magnitudes, unreleased labels. These are never passed
  to a monitor.

Track nulls (conditional, per step):
- B: `E[B_t - theta_B | F_{t-1}] <= 0`
- C: `E[C_t - theta_C | F_{t-1}] <= 0` (the H2c null)
- J: intersection of B and C.

A monitor is valid for a track if, under that track's null, its wealth is a nonnegative
supermartingale (or e-process) and it alarms at `log W >= log(1/alpha)`. `alpha = 0.05` per claim.
For track J, the combiner must be valid for the intersection: Bonferroni over the two tracks, a
fixed convex mixture of e-processes, or a product of e-processes when both are built on the same
filtration with sequential betting.

## 3. Scenario families (development grid)

Each family is crossed with delay d ∈ {0, 5, 20}, label regime ∈ {full, budget 20%, budget 5%},
and proxy ∈ {good, biased, noisy}. Development uses T = 2000.

| Family | B path | C path | Role |
|---|---|---|---|
| null_stationary | at theta | at theta | size |
| null_boundary | theta − small | theta − small | size near the boundary |
| null_ar | AR(0.9) around theta | AR(0.9) | dependence stress; reported, outside the i.i.d. guarantee |
| coshift | ↑ at tau | ↑ at tau | H2c's favourable case |
| cost_only | flat | ↑ | negative-transfer risk for B→C |
| pred_only | ↑ | flat | benign for C, harm for B |
| opposed | ↓ | ↑ | adversarial transfer |
| gradual | linear ramp in both | | drift |
| intermittent | ↑ in bursts | ↑ in bursts | restart and re-entry |
| lagged | ↑ at tau | ↑ at tau + 200 | leading-indicator transfer |

Magnitudes: three levels per alternative family. Change time tau is drawn uniformly from
[200, 1200].

## 4. Seed partitions (disjoint torch generator streams)

| Partition | Seed base | Used by |
|---|---|---|
| dev | 10_000_000 | stage 2 frontier, stage 3 rungs 0–2 |
| stress | 20_000_000 | stage 3 cross-regime stress (rung 3) |
| audit | 30_000_000 | stage 3 equivalence and theory audit, null checks |
| confirm | 90_000_000 | stage 4 only, after the freeze |

## 5. Baselines (stage 2)

Each baseline is registered with its fidelity class from stages 1 and 2. The registry lives in
`src/shiftlab/hgxh2c/registry.py` and `03_BASELINE_REGISTRY.md`.

- Paper suite: PPRM (B, running-risk estimand, null differs and is reported as such); Timans
  approx-GRAPA and grid-GRAPA (C and B); Csillag PP e-values (C and B); Tenzer imputed / LRT / PPI
  (different-null reference on the distribution-shift null); Ryu–Wornell multivariate gambling
  (J); Xu active betting (C, with querying).
- Anchors: HG (B), H2c (C), C1 discounted Kelly on cost, C2 cost ONS, Brier Kelly/ONS.
- Strong controls: (1) independent HG + H2c; (2) joint-history contextual ONS/Kelly, where each
  track's stake is a linear function of both tracks' released histories, fitted by ONS; (3) fixed
  mixtures `w E^B + (1-w) E^C` with w ∈ {0.25, 0.5, 0.75}; (4) CUSUM and Page–Hinkley with
  thresholds calibrated on null_stationary audit seeds. Item (4) is labelled empirical-alarm and is
  not anytime-valid.

Frontier: for each (track, scenario cell, endpoint), the set of baselines not Pareto-dominated on
(J-cost, power, delay) with null FAR Clopper–Pearson lower bound ≤ alpha. The frontier is frozen
with its dev-seed estimates.

## 6. The 64 basic transfer structures and the typed grammar

There are two directions, HG→H2c (B→C) and H2c→HG (C→B). In each direction there are three
channels, and each channel is either off or on, which gives 2^3 × 2^3 = 64 basic structures:

| Channel | What the source track may change in the target track | Typed operators (each has a small parameter grid) |
|---|---|---|
| S stake | the target's predictable stake lambda_t | ratio guidance (H2c style: scale by a clipped moment ratio of the source's evidence); additive prior shift; sign-agreement gate; source-evidence-tempered cap |
| Q query | the target's query probability q_t | boost when source log-wealth rises; straddle (query while the source is undecided); variance-optimal IPW allocation using the source's residual variance; budget pacing shared between tracks |
| R restart | the target's restart / start-time mixture | restart the target when the source crosses level k; add a start-time component at the source's last up-crossing; switch the target's discount factor gamma on source evidence |

A candidate is (structure, one operator per active channel, operator params, track-J combiner ∈
{bonferroni, mixture w, product}, base engines for B and C ∈ {Kelly-discounted, ONS, GRAPA}).
Multiple operators per channel are allowed up to depth 2, composed in a fixed order. The full
canonical space is in the millions. Stage 3 enumerates and canonicalises it.

Validity by construction (typing rule). An operator may touch only quantities that are predictable
with respect to the released filtration: stakes, query probabilities with floor `q_min`, restart
indicators decided from released data, and mixture weights fixed before t. Each factor keeps the
form `1 + lambda_t * Y_t`, where `Y_t` is the observed centred increment or its IPW / prediction-
powered correction (Csillag form). `lambda_t` is clipped so that `1 + lambda_t * Y_t >= 0` holds
surely given `q_min`. Under each track's null and for martingale-difference outcomes, every
candidate's per-track wealth is then a test supermartingale. The J combiners are valid for the
intersection. Restart mixtures use predictable weights (sum of start-time-indexed e-processes with
fixed prior weights), so they remain e-processes. Candidates that break typing are rejected and
logged with reason `UNTYPED`. Dependence (null_ar) is outside the guarantee and is reported as a
stress result.

Canonicalisation rejects (and logs as `EQUIVALENT_TO:<rule>`):
- an active channel whose parameter makes it the identity;
- an S-channel ratio guidance with a constant moment ratio, which reduces to discounted Kelly
  (known result: X1, max |dlogW| = 9e-16);
- a candidate whose stakes are numerically identical to joint contextual ONS on audit seeds (max
  |dlogW| < 1e-9).

## 7. Endpoints

Fixed constants: c_q = 0.02 per label, c_FA = 50 per false alarm, horizon T. Excess cost counts
`(C_t - theta_C)` over steps in [tau, alarm ∧ T] in C-harm worlds, and the same with B for B-harm.

Per seed, J-cost is
`J = sum_{t >= tau}^{alarm ∧ T} (C_t - theta_C) + c_q * #queries + c_FA * 1{alarm in a world where track-C's null holds}`.

- Primary (per claim): the cumulative paired gain `Delta_J = mean over the registered scenario
  mixture of E[J_base - J_cand]`. The mixture puts equal weight on every development cell. This is
  the "cumulative" criterion: beating the baseline summed over all regimes, not in one cell.
- Secondary: paired detection-power difference within a window of 800 steps after tau; detection
  delay, with misses counted as T − tau; null FAR with Clopper–Pearson interval; E log-wealth;
  labels used; runtime.
- A "rule" claim compares a deployable selector `r(d, label regime, proxy calibration score
  measured on source data)` → candidate. It is fitted on dev seeds and evaluated with the same
  Delta_J on confirm seeds. The selector may use only design-time observables, never the latent
  scenario.

## 8. Search (stage 3)

Successive halving over multiple fidelities. The rung sizes are maxima; the run stops early if the
space is smaller.

| Rung | Candidates | Seeds/cell × cells | T | Keep |
|---|---|---|---|---|
| 0 | all canonical (≤ 1e6) | 16 × 30 random cells | 1000 | top 10% by Delta_J vs frontier, null-FAR screen |
| 1 | ≤ 1e5 | 64 × all cells | 2000 | top 10,000 |
| 2 | ≤ 1e4 | 256 × all cells | 2000 | Pareto(Delta_J, power, labels) top 500 |
| 3 stress | ≤ 500 | stress seeds, d ∈ {0,5,20,50}, AR, sparse labels | 2000 | top 50 |
| 4 audit | ≤ 50 | audit seeds: equivalence to contextual ONS / multivariate / PP; ablations | 2000 | 3–5 finalists + selector |

The null-FAR screen at rungs 0–2 removes a candidate only if its Clopper–Pearson lower bound on
FAR exceeds alpha in a null family covered by the guarantee. This screen catches implementation
bugs, because typed candidates are valid by construction.

Every evaluated configuration, including duplicates, rejects and failures, is appended to
`registry.parquet` with its rung, scores, hash and reason.

## 9. Confirmation (stage 4)

- Freeze the finalists, the selector and the frontier (hashes in `FREEZE.json`). Then draw confirm
  seeds: N = 2000 per cell for harm/benign cells and 20,000 per null family for FAR (CI half-width
  about 0.3 pp at 5%).
- For each finalist A and each frontier baseline b: paired Delta_J with a cluster bootstrap (cells,
  then seeds; 4000 resamples) and a one-sided paired test. A claim of "beats the frontier" requires
  A to beat every frontier member. This is an intersection–union test, so it needs no multiplicity
  adjustment within the claim.
- Holm adjustment across finalists × {primary endpoint} at family-wise 0.05. Secondary endpoints
  are reported with unadjusted CIs and marked as such.
- Mechanism evidence on confirm seeds:
  - ablate each active channel;
  - replace the transfer with joint contextual ONS;
  - negative control: time-shuffle the source track by a random cyclic shift, which keeps the
    marginals and breaks cross-risk alignment.
- The outcome is assigned from the decision table in §10 and reported together with the failures
  and the regimes where transfer was negative.

## 10. Decision table (copied from the brief)

| Result | Interpretation |
|---|---|
| beats independent HG+H2c, not contextual ONS | useful combination, weak novelty |
| beats contextual ONS, not multivariate betting | task-specific; narrow the novelty claim |
| beats all applicable baselines in one regime | promising scoped result |
| beats all strong baselines across regimes, valid | stronger conference candidate |
| better detection, not better J | monitoring contribution only |
| better J, not better detection | decision-policy contribution |
| nothing survives | negative result: keep the failure atlas and stop the mechanism |

## 11. Execution

- GPU: torch batched over [candidates × cells × seeds], with a Python loop over t. The runner uses
  `.venv/Scripts/python.exe` (torch 2.9.1+cu130).
- Unattended: `scripts/hgxh2c/pipeline.py` keeps per-step checkpoints and is idempotent. A Windows
  scheduled task `ShiftLab-HGxH2c-watchdog` relaunches it every 30 min unless it is running (PID
  lock) or `outputs/hgxh2c/DONE` exists. Remove it with
  `schtasks /Delete /TN ShiftLab-HGxH2c-watchdog /F`.
- PaperBanana is required for figures (AGENTS.md). If it is unavailable when the pipeline runs, the
  report records the missing dependency and emits only tables. It never substitutes another
  figure generator.
