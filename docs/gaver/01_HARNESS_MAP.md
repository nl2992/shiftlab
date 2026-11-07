# GAVE-R WP0: harness map, observation contract, seed block

Date 2026-11-06, branch `research/gave-r-2026-11-06`, base `main@7354480a`. Everything below was
read from the code at that commit; descriptions say what the code does, not what the docs intend.
Development-only; no claim here is a result.

## 0.1 Harness map

All paths are relative to the repo root. `fa` = `src/shiftlab/dive/failure_atlas.py`, `se` =
`src/shiftlab/dive/switching_explore.py`, `ac` = `src/shiftlab/dive/atlas_components.py`,
`adb` = `src/shiftlab/dive/atlas_dependence_baselines.py`.

### Core loop and accounting

| Piece | Where | What it does |
|---|---|---|
| Round loop | `se:run(stream, method, cfg)` | For t=1..T: release labels due at t, call `method.step(t, due)` -> `(action, query)`, charge budget, schedule the label at `t+d`. Method sees only `(t, released)`; `Truth` is never passed. |
| Family-4 loop | `atlas_release_hook.py:run_informative` (via `fa:run_for`) | Same contract but release delay depends on the label (favourable `d_f`, else `d_u`). Not used by cycle-7 primary cells. |
| Config | `se:Config(T,B,d,c,s,h,alpha,seed)` | T horizon (1000), B hard label budget, d fixed delay, c query cost (0.01), s switch cost, h hurdle (0.1), alpha (0.1). |
| Cost accounting | `se:score_actions` | `per_round = loss(action) + c*query_mask + s*(action != prev)`, action 0 at t=0 (initial incumbent). `cost = sum`; scripts report `cost/T`. So J = loss + c N_q + s N_s exactly, with N_q = queries requested (pending included) and N_s = number of action changes (promotions and rollbacks both). |
| Evaluator truth | `se:Truth(regime_mean, regime, hmm)`, `Stream(loss0, loss1, truth)` | `D = clip(loss1 - loss0)`. Streams use `loss0=Y`, `loss1=1-Y`, so `D=-1` (favourable to candidate) iff `Y=1`. `RunResult.fp_regime` = promotions in rounds with `regime_mean >= -h` (the "false promotion" score) is computed in `score_actions`, evaluator side only. |
| Method base | `se:Method.step/start/can_query` | `step` ingests released labels (`self.labels`, `self.pending_events.discard`), calls `decide`, then **silently drops** a query if `used >= B` or `t+d > T` (`can_query`), so `BudgetExceeded` in `run` is a backstop, not the live guard. |

### Stream/cell generator (`fa`)

| Piece | Where | Notes |
|---|---|---|
| Family 1 cells (iid) | `fa:CellSpec`, `make_family1_stream` | onset {.1,.3,.6,.8}, duration {.15,.3,.6,1.0} (1.0 = to end), effect {strong .1/.9, medium, weak}, off {neutral, harmful}, d {1,10,50}, budget_frac {.05,.1,.25}, s {.05,.1,.5}. Onset jitter U(-.05,.05)*T. |
| Family 3 cells (Markov rho) | `fa:Family3CellSpec`, `make_markov_stream(cell, seed, FAMILY3_TAG=30003)` | rho {0,.5,.8} (null grid adds .95), onset {.3,.6}, duration {.6,1.0}, effect {strong, medium}, d {1,10}, budget {.05,.1}, s = 0.1. Within-regime Y is a 2-state chain with stationary mean p and autocorrelation rho: `markov_transitions(p, rho) = (p(1-rho), p+rho(1-p))`; first round uses p. |
| Family 4 | `fa:Family4CellSpec` | Outcome-dependent delay `same|u3|f3`. Out of scope for WP1-3. |
| Null twin | `.null_twin()` | Never-on path with constant favourable prob `(1+h)/2 = 0.55` (boundary null), canonicalised to onset .3 / dur .6 / strong / harmful, id gets `_NULL`. Family 3 twins keep rho, d, B, s. |
| Neighbours | `fa:neighbours(cell)` | One-level change on one axis, per family grid. |
| Dispatch | `fa:make_stream(cell, seed)`, `fa:run_for` | RNG is `default_rng([seed, tag, crc32(cell_id)])`, so streams are paired across methods for a given (cell, seed). |
| Delay | `Config.d` | Constant, same for all labels (families 1/3). |
| Budget / switch cost | `cell.B = round(budget_frac*T)`, `cell.s` | |

**Cell-id grammar** (`fa:CellSpec.cell_id`, `Family3CellSpec.cell_id`; parser `scripts/run_atlas_dss_tuning_v1.py:build_cell` using `F3_RE`):

- Family 1: `on{onset:g}_L{duration:g}_{effect}_{off_type}_d{d}_b{budget_frac:g}_s{s:g}[_T{T}][_NULL]`,
  e.g. `on0.6_L1_strong_harmful_d50_b0.05_s0.1` = onset 0.6T, runs to end, strong effect,
  harmful off-state, delay 50, B=0.05T=50, switch cost 0.1.
- Family 3: same with prefix `f3_rho{rho:g}_`, e.g. `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`.
- Dependence-null configs (cycle 6/7): `scripts/run_atlas_cycle6_validity_v1.py:config_list(T)` ids
  `dep_rho{rho}_bt{bt}_d{d}` (rho {0,.5,.8,.95} x bt {.05,.1,.25,.5} x d {1,10} = 32);
  `build_null_cell("dep", p, T)` = `Family3CellSpec(rho,.3,.6,"strong","harmful",d,bt).null_twin()`.
- `build_cell(id)` handles `f3_...` via regex and family 1 via lookup in `fa.all_cells(T)`.

### Methods

| Method | Where | What it does |
|---|---|---|
| Spec/registry | `ac:CandidateSpec` (slots acquisition, evidence, memory, decision, params), `validate_spec`, `build_candidate(spec) -> ComposedMethod` | Typed composition; `spec_id` is a hash of the content. |
| DSS (straddle/undecided-only) controller | `ac:ComposedMethod._query` (straddle branch), `ac:dss_spec(gap, delay_switch)` | Request at t iff `(undecided or keepalive) and used < cap(t) and len(pending_events) < pending_cap` and, for DSS, `t - last_query >= gap`. `undecided`: before promotion, no alarm and `ben > h - margin` (ben = -mean of last m released labels of the episode; None counts as undecided); after promotion, `ben_post < h + margin`. `cap = ceil(burst_frac*B) + floor(2*B*t/T)`; `keepalive = max(d+1, ceil(4*T/B))`. |
| Fixed pending cap | `pending_cap = ParamSpec(2, 1, 2)` in `ac` (lines ~127/137); enforced in `_query` as `len(self.pending_events) < pending_cap` | Frozen cycle-7 DSS: `pending_cap=2, gap=4, margin=.15, burst_frac=.1, keepalive_mult=4, delay_switch=True`, spec id `5b5c77b635e5` (source straddle `b1a17927d9ad`). |
| Delay switch | `ComposedMethod._init`: `dss_uniform = delay_switch and d >= P*T/(B+P)` | Data-independent. When true, DSS *is* the uniform calendar. Consequence: in `on0.6_L1_strong_harmful_d50_b0.05_s0.1` (d=50, B=50: 50 >= 38.5) DSS = uniform exactly (smoke run below shows identical cost). |
| Uniform acquisition | `se:uniform_calendar(T,B,d)` + `acquisition="uniform"` | Up to B rounds equally spaced in [1, T-d]. Also the `*_gate` baselines' calendar. |
| iid e-process gate (DSS's evidence) | `ac:_Evidence(kind="started_mixture_eprocess")` -> `se:started_gate` -> `eprocess.py:VectorizedStartedMixtureEProcess(bound=1+h, alpha, starts)` | Bounded-mean started-mixture betting e-process on `-D - h`; at most 32 start positions (label index) with uniform weights; alarm at wealth >= 1/alpha_j. |
| Markov LR comparator | `adb:MarkovLREProcess`, `adb:MarkovLRGate` (name `markov_lr_gate`), `adb:null_sup_loglik`, built by `adb:build_dep` | Mixture over <=8 starts of (fixed alt-grid LR) / (exact sup over null Markov chains, bisection on boundary). Binarises `z = 1[D<0]`; treats the released skeleton as ONE homogeneous chain (declared approximation: gaps not modelled). Calendar = uniform, alpha all in episode 0 (`episode_front`). |
| Thinned comparator | `adb:ThinnedHedgedGate` (`thinned_hedged_gate`) | Same shell; iid e-process fed labels >= 10 rounds apart (`G_THIN`). |
| Other registered baselines | `fa:make_method`, `se:build_method`, names in `scripts/run_atlas_cycle7_validation_v1.py:BASELINES` | `episode_geo/equal/front`, `allonset_edetector`, `online_fwer_spending`, plus `SUPPLEMENTARY` ungated R6 methods (`atlas_r6_baselines.py`). |
| Promotion logic | `ComposedMethod.decide`, act==0 branch | Promote at the first round where `ep.alarm` AND `(T-t+1)*ben > econ_mult*s` (ben = -mean of last 10 episode labels) AND hysteresis streak (k=1 for DSS). Evidence is fed only from labels with event round `ev >= ep_start`. |
| Rollback | same, act==1 branch, `decision="rollback_monitor"` | Page CUSUM `cus = max(0, cus + x - ref)` on post-promotion released labels with `ev >= promo_t`, `ref = (-ben_at_promotion - h)/2`; rollback when `cus >= kappa` (=2.0). Then `_new_episode(j+1, t)`: fresh evidence with `alpha_j = alpha*2^-(j+1)`. See discrepancy 1 below: there is no object called `E_rb` in the code. |
| Pending-label queue | `se:run`: `pending: dict[release_round -> [(query_round, D)]]`; mirror in `Method.pending_events` (set of requested rounds not yet released) | Release semantics below. |
| Fallback-gap diagnostic | `scripts/run_atlas_fallback_diagnostic_v1.py:FallbackGapDiagnostic` | Precedent for subclassing `ComposedMethod` and overriding `_query`. |

### Cycle-7 cell lists, runs, outputs

- Primary (16 cells): `F1_CELLS` (5 family-1 ids in `scripts/run_atlas_dss_tuning_v1.py`) + `f3_failure_ids()` (11 ids parsed from the "Reproduced failures" table of `outputs/failure_atlas_v1_cycle5/family3/summary.md`).
  F1: `on0.3_L0.6_strong_harmful_d10_b0.05_s0.1`, `on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`, `on0.6_L1_strong_harmful_d50_b0.05_s0.1`, `on0.1_L0.6_strong_harmful_d1_b0.05_s0.1`, `on0.1_L0.6_strong_harmful_d10_b0.05_s0.5`.
  F3 (rho_onset_L_d_b, all strong/harmful/s0.1): `0.5_0.6_0.6_d1_b.05`, `0_0.3_0.6_d1_b.05`, `0.5_0.3_0.6_d1_b.05`, `0.5_0.6_1_d1_b.05`, `0_0.6_0.6_d1_b.05`, `0.5_0.6_0.6_d10_b.05`, `0_0.6_1_d1_b.05`, `0.5_0.3_0.6_d10_b.05`, `0_0.3_0.6_d1_b.1`, `0.8_0.6_0.6_d1_b.05`, `0.8_0.6_1_d10_b.05`.
  The two mandatory regression cells of the plan are `on0.6_L1_strong_harmful_d50_b0.05_s0.1` (F1) and `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1` (F3).
- Neighbours: `fa.neighbours` of each primary cell are also run (methods: baselines + all 4 variants + supplementary).
- Null/dependence cells: the 32 `dep_*` configs above, 200 streams each, methods = baselines + variants + supplementary. Acceptance A3 requires absolute FP <= .15 for rho=0 and rho=.5 with bt<=.1; relative (<= best baseline + .05) for rho=.8; rho=.95 and B/T=.5 stress only.
- Variants: `VARIANTS = (dss, no_delay_switch, gap1, uniform)` from `comp.dss_spec(4, True)` and `comp.dss_ablations`.
- Seeds: cycle-7 validation 290000-290199 (smoke 180000-180001), tuning 160000-161040, fallback diagnostic 181000-181040. GAVE-R seeds are in the registered block below, disjoint from all of these.
- Outputs (gitignored `outputs/`): `outputs/failure_atlas_v1_cycle7/{tuning,validation,validation_smoke,fallback_diagnostic,dependence_pilot}/`; validation has `manifest.json`, `records.jsonl` (one line per (cell, 10-seed chunk), resumable), `results.json`, `summary.md`, and also writes `docs/failure_atlas_cycle7_validation_results_v1.md`. Verdicts in `docs/failure_atlas_cycle7_decision_v1.md` (accepted: False; A1 passed 13/16 cells; neighbourhood and dependence safety failed).
- NOTE for this worktree: `outputs/` is not checked out here. `run_atlas_dss_tuning_v1.f3_failure_ids()` and `run_atlas_cycle7_validation_v1.design()` read `outputs/failure_atlas_v1_cycle5/family3/summary.md` and `outputs/failure_atlas_v1_cycle7/tuning/frozen.json`; copy them from `C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/` before using those entry points. The one-cell command below does not need them.
- Tests: `tests/test_atlas_components.py`, `test_atlas_dependence_baselines.py`, `test_atlas_cycle7_validation.py`, `test_failure_atlas.py`.

### Extension points for new components

1. **Evidence engine (Gap-Mix).** Protocol used everywhere: an object with `update(value: float)` (value = `-D - h`, bound `1+h`), `alarm: bool`, `log_e_value`. Plug-in routes: (a) add a `kind` branch in `ac:_Evidence.__init__` plus a `_c(...)` entry in the evidence slot of the component registry and `E_EVIDENCE` (so `is_safety_gated` holds); (b) subclass `adb:_FrontGated` overriding `_make_ep(alpha)`, `_feed(ev, x) -> bool`, `_reset_feed()` (this is how `MarkovLRGate` is written, and it is the easier route for a comparator). **Gap awareness needs one signature change:** `_Evidence.update(x)` does not receive the label's event round, although `decide` has `ev` in the `released` tuples `(event_round, D)`; `_FrontGated._feed(ev, x)` already gets it. Gap g = difference of consecutive used event rounds; labels arrive in event order for fixed delay.
2. **Acquisition governor (PAVE).** Override `ComposedMethod._query(self, t) -> bool` (precedent: `FallbackGapDiagnostic`), or add an `acquisition` name + branch in `_query` and a `ParamSpec` entry. Available state at call time: `self.cfg`, `self.used`, `self.pending_events` (requested-not-released rounds, so ages are `t - e`), `self.last_query`, `self.act` (deployment), `self.ep` (evidence object), `self.ep_labels`, `self.post`, `self.j`, `self.ep_start`, `self.promo_t`, `self.keepalive`, `self.rng`. `Method.step` still enforces `used < B` and `t+d <= T`, so a governor cannot overspend even if buggy; add the pathwise-cap assertion in tests anyway.
3. **Decision/rollback (FreshCheck).** `ComposedMethod.decide`, act==1 branch and `_new_episode`; the decision slot (`rollback_monitor`, `hysteresis`, `certificate_econ`) is the registry hook.
4. **Runner.** `scripts/run_atlas_cycle7_validation_v1.py:make_method(name, cfg, sp)` maps names to `Method` instances (variants -> `comp.build_candidate`, `DEP_METHODS` -> `build_dep`, else `fa.make_method`); `task()` shows the per-(cell, seed) loop and metric extraction (`cost, loss, query_cost, switch_cost, queries, switches, fp, promoted, correct`); `analyse()` + `fmt` for paired CIs (`se:paired_ci`, `se:wilson`). New code should live in `src/shiftlab/gaver/` and call these, not edit them.

### Run ONE cell at smoke scale (10 seeds)

Verified 2026-11-06 in this worktree. Driver is a throwaway script kept outside the repo (a copy
is in the session scratchpad); create and run it from the repo root:

```bash
cd "C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-gave-r-2026-11-06"
export PYTHONPATH="$PWD/src" PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY="C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe"
$PY - <<'E'
import sys, time, numpy as np
sys.path[:0] = ["scripts"]
from run_atlas_dss_tuning_v1 import build_cell
from run_atlas_cycle7_validation_v1 import make_method, specs
from shiftlab.dive import failure_atlas as fa
cid, s0, n = "on0.6_L1_strong_harmful_d50_b0.05_s0.1", 101080000, 10   # change CELL_ID here
cell, sp = build_cell(cid), specs()
methods = ["dss", "uniform", "markov_lr_gate", "episode_front"]
t0 = time.time(); cost = {m: [] for m in methods}; fp = {m: [] for m in methods}; q = {m: [] for m in methods}
for sd in range(s0, s0 + n):
    cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
    for m in methods:
        r = fa.run_for(cell, stream, make_method(m, cfg, sp), cfg)
        assert r.queries <= cfg.B
        cost[m].append(r.cost / cell.T); fp[m].append(int((r.fp_regime or 0) > 0)); q[m].append(r.queries)
for m in methods:
    print(f"{m:16s} cost/round {np.mean(cost[m]):.4f} fp {np.mean(fp[m]):.2f} queries {np.mean(q[m]):.1f}")
print(f"wall {time.time()-t0:.1f}s")
E
```

Observed (10 seeds 101080000-101080009, 4 methods, T=1000): `on0.6_L1_strong_harmful_d50_b0.05_s0.1`
dss 0.3981 = uniform 0.3981, markov_lr_gate 0.4155, episode_front 0.3906, fp 0 for all, **1.2 s**
compute (~4 s including interpreter start). `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`:
dss 0.4371 (53 queries), uniform 0.3849, markov_lr_gate 0.5590, episode_front 0.3253, fp 0, **1.8 s**.
Do not read anything into these 10-seed means; they only show the harness runs. (They do show that
`episode_front` beats DSS in both regression cells at 10 seeds, consistent with the recorded cycle-7 adverse cells.)
Whole-script smoke: `python scripts/run_atlas_cycle7_validation_v1.py --smoke --workers 4` (needs the two output files noted above).

## 0.2 Observation contract (what the code actually does)

Scope: families 1 and 3 (fixed delay), `se:run` + `ac:ComposedMethod`. One reading per row,
with code reference.

1. **Filtration.** `F_t` = {t, config (T,B,d,c,s,h,alpha,seed), own past actions and requests, and the multiset of released labels `(query_round, D)` with `query_round + d <= t`}. Within round t the order is: release labels due at t -> method picks `(action_t, request_t)` -> loss at t is realised. A label requested at t becomes visible only at round t+d, before that round's decision. Labels requested at t with t+d > T are never requested (`can_query`). (`se:run`, `Method.can_query`)
2. **Predictable requests.** `request_t` is a function of F_t and, for `bernoulli_pacing` only, an independent RNG `default_rng([seed,778])`. DSS/uniform use no randomness. No code path reads `Stream`, `Truth`, or unreleased `D`. (`ComposedMethod._query`, `decide`)
3. **Fixed delay.** A single constant `cfg.d` for every label in families 1 and 3, so release order = request order. Family 4 breaks this on purpose (`run_informative`); keep it out of Gap-Mix/PAVE scope.
4. **Pending labels never evidence.** `Method.step` adds a label to `self.labels` only when it appears in `released`; `ep.update` is called only inside the `for ev, x in released` loop; the straddle rule uses `ep_labels`/`post` (released only). Pending count/ages are used for acquisition only (`pending_events`).
5. **Budget charged at request.** `step` increments `used` and `pending_events` at the request round; `score_actions` charges `c` per request regardless of release; the pending label is not refundable. Budget is therefore consumed by pending requests (this is what makes a fixed `pending_cap` bind).
6. **Hard pathwise cap.** `can_query` returns False when `used >= B`, so `queries <= B` on every path; the cycle-7 runner additionally asserts `r.queries <= cfg.B`. `se:run` raises `BudgetExceeded` if a method bypasses `step`. No expectation-only caps.
7. **Evaluator-only information.** `Stream.loss0/loss1/D` for unrequested rounds, `Truth.regime_mean/regime/hmm`, onset, duration, rho, effect size, `fp_regime`/`fp_pred`, `true_predictive_mean`. Methods see `Config.h`, `alpha`, `s`, `c`, `B`, `d`, `T` (known costs and the hurdle are part of the problem).
8. **Paired identifiability.** `D = loss1 - loss0` is observed only on requested rounds; the realised loss of the *deployed* action is not separately revealed. Decision quality is scored by the evaluator from full streams. Fine for this simulator; a real-data analogue would need a stated design.

### Discrepancies and caveats found

1. **No `E_rb` in the code.** The plan's "E_rb rollback" corresponds to `decision="rollback_monitor"`: a heuristic Page-CUSUM on released post-promotion labels with `kappa=2.0` plus fresh-episode alpha spending (`alpha*2^-(j+1)`). It is not an e-process; the "rollback is safe" claim has no certificate. WP3 should treat it as a heuristic baseline and not as an existing e-value.
2. **Null class mismatch.** The module docstring's validity argument assumes `E[-D_t | F] <= h` conditional on the available information. A boundary-null Markov chain with rho>0 violates this conditionally on the previous released label (`p + (z-p)rho^g > q0`), which is exactly the rho=.8 failure; the iid gate is valid only for conditional-mean null, and "gated" in the code means "has an e-process shell", not "valid under dependence".
3. **Query-rule predictability is an assumption.** DSS depends on released labels only, but the evidence start positions are label-count indices, so the mixture is data-independent only if the label stream is the sequence of released labels. After a rollback, labels with `ev < ep_start` that are still pending are silently ignored for the new episode (selection by event time, fine, but they were paid for).
4. **Skeleton approximation in Markov LR.** One homogeneous chain over the released skeleton although DSS-style gaps are irregular; with the uniform calendar gaps differ by at most 1. Source docs call this declared, not proved.
5. **DSS == uniform whenever the delay switch fires** (`d >= P*T/(B+P)`, P=2, i.e. d >= 2000/(B+2) at T=1000). In the grids this means d=50 with B<=~38 or 50 (e.g. `..._d50_b0.05`: 50 >= 38.5) and never d=1 or d=10. Cells with d=50 therefore cannot show any acquisition effect of DSS over uniform.
6. **Silent budget clamp.** `Method.step` drops over-budget requests rather than raising; a governor that mis-counts will look budget-compliant. Test `used` bookkeeping directly.
7. **`fp_regime` is per-promotion-round vs. instantaneous `regime_mean`**; a rollback-then-repromotion within a null stream counts each promotion. `fp` in scripts = any false promotion per stream.

## 0.3 Seed block

Allocated with `shiftlab.seed_registry.allocate(200000)` -> **101000000-101199999** (inclusive), registered as
`gaver_screening_development` in `configs/seed_registry.yaml` (status `development`; purpose "GAVE-R
screening development, branch research/gave-r-2026-11-06; no confirmation use"). Registry test
`tests/test_seed_registry.py`: 7 passed; `undisclosed_overlaps(load_registry())` is empty; next fresh
block starts at 101200000. Per-study seeds are `start + index`; keep one stream seed per (cell, replicate), shared across methods.

| Work package | Sub-range (inclusive) |
|---|---|
| WP1 null | 101000000-101039999 |
| WP1 alt | 101040000-101079999 |
| WP2 | 101080000-101119999 |
| WP3 | 101120000-101159999 |
| WP5 | 101160000-101199999 |

The smoke runs above used 101080000-101080009 (WP2 head). They were development-only; WP2 should
either skip those ten ids or note they were looked at. No confirmation seeds are used.
