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

## Amendment A1 (2026-10-31, before any stage-2/3/4 result): faithful-coverage audit against the brief

A line-by-line check against the programme brief found the gaps below. Each item is now binding.

A1.1 Stage-1 records. Every method's registry entry (`03_BASELINE_REGISTRY.md` and `registry.py`)
records:
- the exact paper equation(s);
- the original code URL and commit, or "none accessible";
- assumptions;
- the null hypothesis;
- the calibration rule;
- the output metric;
- the comparator role: DIRECT, ADAPTED or DIFFERENT_NULL;
- the fidelity class (SOURCE_REPRODUCED / SOURCE_FORMULA_VERIFIED / TASK_ADAPTED / SOURCE_INSPIRED /
  INVALID_OR_UNSUPPORTED).

For TASK_ADAPTED, the entry says whether the original guarantee survives. Only the first three
classes count as strong published-method comparisons.

Required native checks:
- Tenzer: label-shift, concept-shift, and the Appendix-E PPI comparator.
- Timans: authors' scripts, approx_grapa and grid grapa.
- Ryu–Wornell: notebooks/exps.ipynb, including universal portfolio.
- Xu: simulation.py.
- Csillag: independent reproduction of Algorithm 1, with tests for:
  - the full-label limit;
  - unqueried-label behaviour;
  - the exact conditional expectation under randomised querying (exact enumeration);
  - factor nonnegativity at the propensity floor 1 − a_t/b_t;
  - agreement with Algorithm 1 written step by step.
- PPRM: independent reproduction of the paper's predictive-risk experiments (batch risk estimator,
  source-risk upper bound, running-risk lower CS, threshold crossing; SRM; fixed vs adaptive
  reliance on synthetic labels).

Csillag and PPRM are labelled "independent reproduction" until formula-level fidelity is verified.

A1.2 Common adapter. `src/shiftlab/hgxh2c/contract.py` defines `StreamEvent`,
`ReleasedObservation` and the `SequentialMonitor` protocol (`propose_query`, `observe_release`,
`evidence`, `alarm`) exactly as in the brief.

A per-event reference runner drives any `SequentialMonitor` from a tape and releases only matured
labels. Every batched GPU monitor must match its per-event reference counterpart on a fixed set of
tapes (log-wealth to 1e-6, alarms identical). The batched engine is an accelerator, not a separate
definition.

A1.3 Endpoints added to §7 (stage-2 report and confirmation):
- loss accumulated before alarm;
- cumulative decision cost;
- intervention cost c_I = 5 per alarm-triggered intervention;
- switching cost c_S = 2 per policy switch (alarm → fallback, plus one switch back at the next
  restart if any);
- information-acquisition cost (c_q × labels);
- cost per incremental improvement (ΔJ per extra label versus the comparator);
- E log-wealth where meaningful;
- performance across magnitudes;
- runtime and peak GPU/CPU memory.

J_cost in §7 adds `c_I·#interventions + c_S·#switches`. Primary Delta_J is otherwise unchanged.

A1.4 Track membership, as in the brief:
- B: HG, Brier Kelly/ONS, a task-compatible PP e-process, and PPRM (null mismatch reported).
- C: H2c, cost Kelly/ONS, Timans, Csillag-style PP betting, and adapted Xu.
- J: independent HG/H2c, fixed mixtures, multiplicity-controlled separate tests
  (Bonferroni/Holm-in-time), Ryu–Wornell multivariate betting, and full-history contextual
  Kelly/ONS.

A1.5 Search. Rung-0 selection also scores runtime and *behavioural novelty*: the distance of the
candidate's alarm-time/stake trajectory from its nearest baseline and from already-kept candidates,
used as a diversity term in the Pareto selection. Search cells are oversampled from Failure Atlas
hard regimes, meaning cells where the frontier's best J is worst relative to the oracle-informed
reference. Rung-4 budget is 25–50, as in the brief.

A1.6 Confirmation sample size. N per cell is not fixed in advance. It is computed before stage 4,
from the rung-3 variance of paired J differences, as the smallest N giving 80% power to detect the
rung-3 effect shrunk by 50% (one-sided 0.05/Holm k). Floors: 1000 per cell; null families 20,000
streams. The calculation is written to `finalists.json` and frozen with it.

A1.7 Validity is not established by simulation alone. Stage 4 writes `docs/hgxh2c/THEORY_AUDIT.md`
with a proof, under each finalist's stated assumptions (filtration, delay/feedback regime,
predictability of stake/query/restart, martingale-difference outcomes, q_min), that each per-track
wealth is a test supermartingale and that the J combiner is valid for the intersection null. Any
assumption the proof cannot cover is listed as such. A novelty/equivalence audit
(`NOVELTY_AUDIT.md`) tests reducibility to contextual ONS, to multivariate betting and to
prediction-powered e-values (Csillag's framework may contain the candidate as a special case). The
HKUSTDial `proof-checker`, `novelty-check`, `experiment-audit` and `result-to-claim` skills are run
on these outputs.

A1.8 Practical magnitude. Report absolute and relative gains with CIs, labels used, and all cost
components. No percentage pass threshold is applied. Report robustness failures and
negative-transfer regimes explicitly.

A1.9 Deliverables add:
- original-paper reproduction tables, plus plots via PaperBanana if available, otherwise recorded
  as a missing dependency;
- the frozen stage-2 results database;
- the failure-mechanism atlas over cells;
- a final decision that separates methodological novelty, empirical improvement and finance
  relevance.

Finance relevance is only *assessed*. A walk-forward finance dataset (point-in-time observations,
delayed outcomes, implementation costs) is future work. It must never be used to select the
synthetic winner and must never be presented as independent validation of that selection.

## Amendment A2 (2026-10-31, before any stage-3 result): search budget aligned to the brief

Facts that prompted this amendment:
- The canonical grammar space is 5.08e10 candidates (raw 4.6e12), which is far beyond "millions".
- The §8 rung-1 fidelity (64 seeds × all 648 cells × T=2000) costs about 1.3 GPU-s per candidate,
  so 1e5 candidates would be infeasible on one RTX 4060.

§8 is replaced by the brief's own stage table. The ceilings below are maxima, not targets.

| Brief stage | Rung | Candidates | Fidelity | Partition | Selection |
|---|---|---|---|---|---|
| Generate and canonicalise | gen | 1e6 drawn by structure-stratified random sampling (seed 0) from the canonical space; every structure gets equal quota | — | — | well-typed, canonical, deduplicated |
| Broad exploratory screening | 0 | up to 1e6 (at least 2e5) | 16 seeds × 32 cells stratified over families × T=1000 | dev | Delta_J vs frontier, null-FAR screen, runtime, behavioural novelty (A1.5) |
| Mechanism-focused development | 1 | 10,000 | 64 seeds × all 648 dev cells × T=2000 | dev | improvement vs the baseline frontier (Delta_J), Pareto with power and labels |
| Cross-regime stress | 2 | 500 | 128 seeds × stress grid (d ∈ {0,5,20,50}, AR, sparse labels) | stress | stability; negative-transfer regimes logged |
| Source-equivalence and theory audit | 3 | 25–50 | 256 seeds | audit | numerical equivalence to contextual ONS / multivariate / PP e-values; per-channel ablation; cyclic-shift control |
| Frozen confirmation | 4 (stage 4) | 3–5 finalists + selector | A1.6 power-based N | confirm | §9 |

The sampling seed and per-structure quotas are logged in the registry. Everything outside the
sample is recorded as NOT_SAMPLED and is not considered rejected.

Rung 0 stops at the first multiple of 2e5 sampled candidates after which the top-10,000 set
changes by less than 5% (Jaccard) between consecutive increments, or at 1e6.

A1.7 split. `THEORY_AUDIT.md` proves validity for the whole typed grammar ahead of time, so any
finalist is covered by its typing. Stage 4 adds per-finalist automated equivalence checks.
`NOVELTY_AUDIT.md` contains the literature-reducibility analysis and is written before results. A
post-results addendum, together with the `result-to-claim` and `experiment-audit` skill runs,
happens in the next attended session.

## Amendment A3 (2026-10-31, before any stage-3 result): fixes from THEORY_AUDIT.md

A3.1 Product J combiner is removed. The same-step product (1+aX^B)(1+bX^C) is not valid for the
intersection null, because the cross-term ab·E[X^B X^C] is positive when the two tracks are
dependent. Evidence:
- Rademacher counterexample: P(sup W ≥ 20) = 0.185.
- Engine null_stationary, full labels: FAR 0.091 against 0.037 (Bonferroni) and 0.040 (mixture).

The product is replaced by the *linear vector factor* 1 + a_t X^B_t + b_t X^C_t, with a_t, b_t ≥ 0
predictable and clipped so the factor is ≥ 0 surely. Its conditional mean is ≤ 1 under H_0^B ∩
H_0^C. This is a Ryu–Wornell-type portfolio and is labelled as such in the novelty audit.

Product candidates are logged as INVALID:product_cross_term. They are not counted as search
failures.

A3.2 Each channel declares a read set. Stake (S) and restart (R) operators may read only released
labels and past state. Only Q operators may read the current free proxy at issue time. Candidates
that violate this are UNTYPED.

A3.3 GRAPA stakes are clamped after the hooks have been applied.

A3.4 Wording fix for §6 R channel. The implemented restarts reset the *stake-estimator moments*,
never wealth, and that is the reason they are valid. A wealth-level restart is admissible only as a
capital-ledger start-time mixture with predictable weights.

A3.5 Joint-history null. Transfer requires the per-track null to hold conditional on the joint
released history: E[X^C_t | F^{B,C}_{t-1}] ≤ 0. Every claim states this stronger null.

A3.6 Stage 4 runs the equivalence tests E1–E11 from NOVELTY_AUDIT.md on every finalist.

A3.7 The proof gate has status SELF_REVIEW_ONLY. The external reviewer was unavailable. No claim
may describe validity as independently reviewed until an external review passes.
