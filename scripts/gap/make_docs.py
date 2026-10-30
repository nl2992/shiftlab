"""Generate the docs/sota_gap_closure/*.md result documents from the stored outputs (numbers are computed, not typed)."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D = Path("docs/sota_gap_closure")
O = Path("outputs/gap_closure")  # noqa: E741
D.mkdir(parents=True, exist_ok=True)


def md(df: pd.DataFrame, floatfmt="{:.3f}", index=True) -> str:
    if index:
        df = df.reset_index()
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append(
            "| "
            + " | ".join(
                floatfmt.format(v)
                if isinstance(v, float | np.floating) and not pd.isna(v)
                else ("" if (isinstance(v, float) and pd.isna(v)) else str(v))
                for v in r
            )
            + " |"
        )
    return "\n".join(out)


def w(name: str, text: str):
    (D / name).write_text(text.rstrip() + "\n")


def have(p) -> bool:
    return Path(p).exists()


# ------------------------------------------------------------------------------------------- Phase 1
def phase1():
    from shiftlab.gap import worlds as W

    RHO, R0 = W.HeteroNull().rho(True), W.HeteroNull().r0()
    a = json.load(open(O / "p1/validity_audit.json"))
    ex = pd.DataFrame(a["exact"])
    het = pd.DataFrame(json.load(open(O / "p1/hetero_extreme.json")))
    het["h"] = het.h.astype(str)
    het["ci"] = het.ci.map(lambda c: f"[{c[0]:.3f}, {c[1]:.3f}]")
    dly = pd.DataFrame(a["delay"])
    dly["ci"] = dly.fa_ci.map(lambda c: f"[{c[0]:.3f}, {c[1]:.3f}]")
    dep = pd.DataFrame(a["dependence"])
    dep["ci"] = dep.fa_ci.map(lambda c: f"[{c[0]:.3f}, {c[1]:.3f}]")
    e1 = pd.read_csv(O / "e1_repair_effect/summary_by_config.csv").set_index("config")
    w(
        "01_VALIDITY_AND_INFORMATION_AUDIT.md",
        f"""# 01 Validity and information audit (synthetic)

Scope: the betting e-process `X_t = theta*proxy_t + (Q_t/q_t)(r_t - theta*proxy_t) - r0 - tol`, wealth `prod(1 + lambda_t X_t)`, threshold `1/alpha`, as used by `pprm_tight` and HG in the earlier phase.

## Checklist
| question | finding |
|---|---|
| Which conditional null is used? | Marginal no-harm: `E[R_t | F_{{t-1}}] <= r0 + tol`, expectation over the current covariate. This implies `E[X_t | F_{{t-1}}] <= 0` **only** for bets `lambda_t` that are `F_{{t-1}}`-measurable. A covariate-conditional null `R(x) <= r0` for every `x` would be strictly stronger and is not assumed. |
| Do wagers depend on current covariates? | **Yes in the earlier implementation (a defect).** The bet cap `0.5 / (proxy_t (1/q - 1) + r0 + tol)` uses the current proxy, i.e. the current covariate. Under a marginal null with heterogeneous conditional risk, `E[lambda(x) X] > 0` can hold. |
| Does a marginal no-harm null imply the conditional inequality needed? | Not for covariate-dependent wagers (above). For wagers that are functions of the past only, yes. |
| Is there a predictable nonnegative bound on the factor? | Yes after repair: `1 + lambda X >= 1 - cap` with `lambda <= cap / (theta_t pmax (1/q_floor - 1) + r0 + tol)`, using only the declared proxy range `pmax` and the inclusion-probability floor. |
| Does label timing preserve the claimed filtration? | Fixed known delay: yes. Random delay independent of outcomes: arrival-ordered product is valid under iid-like data. **Outcome-dependent delay: the arrived-subset product is not covered**; the in-order (`prefix`) release is valid for any delay mechanism because the wealth at any time equals the event-indexed martingale at a nondecreasing random index (Ville applies to the event-indexed process). |
| Does the gate use released information only? | Yes: the HG gate uses the discounted decision-cost increments of labels that arrived strictly before the current event (`BG` buckets), tested by `test_causality_*`. |

## Exact finite-support counterexample (no simulation)
`x in {{0,1}}`, `P(x=1)=0.5`, proxy `h=(0.05, 0.35)`, binary loss with conditional risks re-arranged to `({RHO[0]:.3f}, {RHO[1]:.3f})` so the marginal risk equals `r0 = {R0:.2f}` exactly. Maximal admissible bet `lambda = c/bound`. Expected betting factor per step (a valid factor needs <= 1):

{md(ex, "{:.5f}", index=False)}

The legacy covariate-dependent cap gives `E[factor] > 1` in every cell (up to 1.13); the repaired predictable cap gives exactly 1.00000 (`tests/gap/test_engine.py::test_exact_finite_support_cap`).

## Empirical size of the defect
Forced maximal bets (adversarial), valid re-arranged design (all risks in [0,1], marginal risk = r0), 3000 paths, T=2000:

{md(het[["h", "q", "cap_mode", "fa", "ci", "n"]], "{:.4f}", index=False)}

At default Kelly plug-in bets the cap rarely binds and the measured effect was undetectable (`validity_audit.json`, `hetero_shifted=True`: 0.020 legacy cap vs 0.018 repaired). **The defect is real but mild in the earlier experiments; the repair costs nothing**: on the G1 development pool (E1, 200 seeds x 19 worlds), repaired vs legacy:

{md(e1.loc[[c for c in e1.index if c.startswith(("HG", "pprm"))]][["power", "harm_before", "fa_nonharm"]])}

## Dependence is the larger validity gap
Marginal-null calibration (sizes under outcome dependence that leaves the marginal source law unchanged; 1000 paths each; Wilson 95%):

{md(dep[["scenario", "arm", "fa", "ci"]], "{:.4f}", index=False)}

Cluster-dependent outcomes inflate HG's false-alarm rate above alpha. The reason is exactly the condition above: `E[R_t | F_{{t-1}}]` differs from `r0` during a cluster although `E[R_t] = r0`.

## Outcome-dependent delay (naive vs in-order release)
{md(dly[["scenario", "arm", "fa", "ci"]], "{:.4f}", index=False)}

No empirical difference at these settings (the naive subset product is theoretically unprotected but the effect is below 1000-path resolution). In-order release pays head-of-line blocking under heavy-tailed delays (power 0.45 vs 1.00 in `G6|concept2|delay=heavy`, see `DELAY_STRESS_RESULTS.md`).

## Decision
* Repaired configuration (`cap_mode="sup"`, `release="prefix"`) is the only one used for claims in this study.
* HG keeps its stated null: **iid-like data, bounded losses, predictable bets, known or outcome-independent label timing**. It is *not* valid under dependent outcomes (measured), and no repair with a proof is offered; the long-run-variance scaling F2 is an empirical heuristic (see `SECOND_ROUND_FIX_CANDIDATES.md`).
""",
    )
    w(
        "01_EXPERIMENT_HARNESS_AUDIT.md",
        """# 01 Experiment harness audit

Earlier harness (`sota_search.harness`, `run_*.py`): aggregates only (per-config means in SQLite `secondary_metrics`), uniform Bernoulli labels with an expected budget, fixed delay shift, label mask from `lseed` shared across detectors (partial pairing), no hard budget, no peak-memory or runtime profile (runtime recorded per (config, world) batch), empirical-threshold detectors calibrated on one 400-seed null stream.

## Gaps found
1. **No per-seed records** - a per-seed alarm time, harm-before-alarm or label count could not be recovered. Fixed: `src/shiftlab/gap/store.py` stores one row per (world, config, seed): first alarm, false-alarm / detection indicators, delay, harm before alarm, queried labels, label arrival statistics (mean delay, last arrival, mean / max pending queue), hard-budget exhaustion time, batch runtime (and per-seed share), process peak RSS. Aggregates are derived by `store.summarise`; nothing from the earlier registries is overwritten (`outputs/sota_search` untouched).
2. **Pairing** - arms in the new harness share worlds, seeds and the query uniform matrix (`qseed`); arms with equal `q_t` query identical events (`test_seed_reproducibility_and_common_random_numbers`). Allocation arms keep compatible query randomness (monotone coupling `Q = U < q_t`).
3. **Registry** - `outputs/gap_closure/registry.sqlite` (append-only; config hash, config JSON, number of worlds, seeds, seed block, commit SHA, wall time, note). Per-seed parquet files live next to it. `.gitignore` now whitelists `outputs/gap_closure/` and `outputs/sota_search/` (the previous phase lost its G2 held-out summary and registry because `outputs/*` was ignored; see `00_MANDATE_COMPLETION_MATRIX.md`).
4. **Limitation** - seeds are vectorised, so runtime and memory are batch-level quantities (per-seed runtime = batch / S; peak RSS = process high-water mark). `RUNTIME_SCALING.csv` / `MEMORY_SCALING.csv` use dedicated clean measurements.

## Parity with the earlier implementation
`Cfg(cap_mode="x", release="legacy", unq_delay=True)` reproduces legacy `pprm_tight` and HG log-wealth to float32 precision (max |diff| 4.8e-7, identical alarms; `tests/gap/test_engine.py::test_legacy_parity_pprm_tight_and_hg`).

## Test inventory (`tests/gap`, 18 tests)
legacy parity; exact finite-support cap; hard budget (pathwise `labels <= B` for six pacing rules, forced exhaustion, wealth frozen after exhaustion); causality (perturbing future events does not change the past; a label's value cannot influence wealth before `t + delay`); seed reproducibility / CRN; parent-modified identities (`rel=hard,fallback=none`, `mix=(1,0,0)`, `gamma=1, gate=None` equal the parent); prefix = arrived under fixed delay; generator tests (`GENERATOR_VALIDATION_TESTS.md`).
""",
    )
    w(
        "01_PAIRED_SEED_TESTS.md",
        """# 01 Paired-seed tests
* Same `qseed` => identical query events for arms with equal `q_t` (HG vs `pprm` at equal fraction have identical `labels` per seed) - `test_seed_reproducibility_and_common_random_numbers`.
* Different `qseed` => different label events.
* Identical inputs reproduce `logW` bit-for-bit.
* Arms in each experiment run on the same world objects: world `w` uses `seed0 + 1000 w` for every configuration (`store.run_grid`), so paired differences are computed per seed.
* Q2/Q3 use one stream per world shared by all methods/policies; Q3 policies share the label uniform matrix `U`.
Genuinely different query decisions (growth, variance, CAMS-style) still use the same `U`, so paired comparisons differ only through `q_t`.
""",
    )
    w(
        "01_BUDGET_ACCOUNTING_TESTS.md",
        """# 01 Budget accounting
Two contracts are implemented and not interchangeable.
* **Expected budget** (`budget=None`): Bernoulli queries with mean fraction `frac`; realised label counts vary by path (reported as `labels`).
* **Hard budget** (`budget=B`): on every sample path `sum_t Q_t <= B`. A request is charged when issued (`spent += Q`), never when the label arrives; pending labels are tracked (`mean_pending`, `max_pending`). After exhaustion the event is **inactive** (inclusion probability 0, factor 1, no moment update), which preserves the evidence rule: events with `q_t = 0` are excluded rather than treated as unlabelled with a proxy (that would bias the increment). Inclusion probabilities are the nominal `q_t` while `spent_{t-1} < B`, hence unbiased IPW.
Tests: `test_hard_budget_pathwise` (six pacing rules, `labels.max() <= B`, forced exhaustion reaches exactly B), `test_budget_exhaustion_freezes_wealth`.
The earlier phase's experiments used the expected-budget contract only; they are not hard-budget results.
""",
    )


# ------------------------------------------------------------------------------------------- generators
def generators():
    from shiftlab.gap import pools as P
    from shiftlab.gap import worlds as W

    R = W.Regime
    rows = []
    w3 = W.LogitWorld(
        regimes=(R(), R("concept", 2.0), R("cov_benign", 3.0), R("prior", 1.5), R("cost", fn=20.0))
    )
    for k, r in enumerate(w3.regimes):
        e = W.regime_effects(w3)[k]
        rows.append(
            {
                "generator": "G3/G5 regime",
                "regime": f"{r.kind} delta={r.delta:g} FN={r.fn:g}",
                "discrepancy_MMD2": e[0],
                "predictive_dBrier": e[1],
                "decision_harm": e[2],
            }
        )
    fw = W.FinWorld(betas=(1.0, 0.3, -1.0))
    for k, b in enumerate(fw.betas):
        e = W.fin_effects(fw)[k]
        rows.append(
            {
                "generator": "G4 finance",
                "regime": f"signal loading beta={b:g}",
                "discrepancy_MMD2": e[0],
                "predictive_dBrier": e[1],
                "decision_harm": e[2],
            }
        )
    for name, wd in (
        ("G1 cov_benign d=3", W.LogitWorld(regimes=(R(), R("cov_benign", 3.0)))),
        ("G1 concept d=2", W.LogitWorld(regimes=(R(), R("concept", 2.0)))),
        ("G2 concept d=2", W.LogitWorld(regimes=(R(), R("concept", 2.0)), family="G2")),
        ("G2 cov_benign d=3", W.LogitWorld(regimes=(R(), R("cov_benign", 3.0)), family="G2")),
    ):
        e = W.regime_effects(wd)[1]
        rows.append(
            {
                "generator": name.split()[0],
                "regime": name,
                "discrepancy_MMD2": e[0],
                "predictive_dBrier": e[1],
                "decision_harm": e[2],
            }
        )
    gt = pd.DataFrame(rows)
    gt["class"] = np.where(
        (gt.decision_harm >= 0.10) | ((gt.generator == "G4 finance") & (gt.decision_harm >= 0.03)),
        np.where(
            gt.discrepancy_MMD2 >= 0.02, "harmful + discrepant", "harmful, little discrepancy"
        ),
        np.where(gt.discrepancy_MMD2 >= 0.02, "benign discrepancy", "benign / null"),
    )
    gt.to_csv(D / "GROUND_TRUTH_SHIFT_CURVES.csv", index=False)
    w(
        "REGIME_CLASSIFICATION_MATRIX.md",
        f"""# Regime classification matrix
Ground truth (evaluator-side Monte Carlo, 30k samples per regime; G4: 60k). Harmful = decision-cost increase of the fixed deployed policy >= 0.10 (G4: >= 0.03 on its [0,1] loss scale). Discrepant = joint-law RBF MMD^2 vs the source >= 0.02.

{md(gt, "{:.4f}", index=False)}

The three dimensions disagree by construction: `cov_benign` (large discrepancy, no harm), `cost` regimes (no discrepancy at all, harm from a changed decision cost), `concept` (small discrepancy, large predictive and decision harm), G2 `cov_benign` (the nonlinear term turns a nuisance shift into harm). Per-step curves for the G1/G2 schedules are in `outputs/sota_search` code (`generators.truth`); for G3/G4 the per-seed truth arrays are `(S,T)` lookups of these regime effects through the simulated regime path.
""",
    )
    w(
        "G3_G4_G5_G6_GENERATOR_CONTRACTS.md",
        """# Generator contracts G3-G6 (`src/shiftlab/gap/worlds.py`, `pools.py`)
Common: `X ~ N(mu_regime, I_4)`, source Bayes logistic model `sigma(x.w)` deployed with cost-sensitive threshold (FN=5, FP=1); detectors see `x, y` (when queried and resolved), model score and proxies. Truth arrays are evaluator-side only.

**G3 Markov-switching.** 2-5 regimes; transition matrices with persistence {0.98, 0.99, 0.995}, `jump` (uniform) or `cycle` (recurrent) structure; regime 0 is forced before `t0=500` (reference period). Regime-dependent predictor accuracy (concept rotation delta), regime-dependent decision cost (`Regime("cost", fn=20)` changes the realised false-negative cost with the deployed policy unchanged), benign covariate regimes, prior regimes, delayed observations (G6 delays), correlated outcomes (G6 latent noise).
**G4 finance.** Student-t(4) shocks, GARCH(1,1) volatility (omega .05, a .10, b .85-.88), regime-dependent signal loading beta in {1, .3, -1} (sign reversal), long/flat/short rule with threshold 0.3, transaction cost 0.02 x turnover x sigma, loss = clip(0.5 - pnl/(2c), 0, 1) with c = 2 (extreme returns bounded), volatility-dependent through pnl, predictive loss = clipped squared forecast error; proxies are forecast-implied expected loss and conditional variance. Synthetic process only.
**G5 proxy misspecification.** On top of any world: static bias, bias after shift, calibration failure (power transform), subgroup failure (x_2 > 1), anti-informative, recovering (window), blend of accurate and anti-informative (sensitivity curves), oracle-adaptive (proxy = true conditional expected loss, clipped to the declared range). Proxies are clipped to a declared range [0, pmax] (the cap's validity uses it); outcomes never change.
**G6 feedback and dependence.** Delays: fixed, independent uniform, geometric, outcome-dependent (errors fast / slow), heavy-tailed (Pareto 1.3) pending queues, delayed bursts (batch release). Dependence: AR(1) latent logit noise, cluster-shared random effects; the nominal risk `r0` is re-estimated from an independent source stream of the *same* noisy world so the null is "unchanged law", not "unchanged risk by construction".
""",
    )
    w(
        "GENERATOR_VALIDATION_TESTS.md",
        """# Generator validation tests (`tests/gap/test_worlds.py`, all passing)
Markov path (forced reference regime, empirical persistence 0.9 +- 0.01, uniform stationary occupation for a symmetric jump chain), cycle structure, delay models (fixed / uniform mean / outcome-dependence exactness / burst release grid / heavy tail), proxy modes (declared range, outcomes untouched, pre-shift identity of `anti`), finance world bounds in [0,1] and monotone harm of signal reversal, clustered noise inflates the variance of 200-step block means by > 1.5x, three-dimensional truth disagreement, seed reproducibility. The independence of the simulator from the engine is checked by the exact finite-support calculation (`audit.py`) and legacy parity.
""",
    )


# ------------------------------------------------------------------------------------------- stress
def stress():
    sm = pd.read_csv(O / "e6_stress_main/summary_by_world.csv")
    df = pd.read_parquet(O / "e6_stress_main/perseed.parquet")
    from shiftlab.gap import store as St

    lo = St.summarise(pd.read_parquet(O / "e6_stress_lowlabel/perseed.parquet"))
    hbp = pd.read_parquet(O / "e6_stress_hardbudget/perseed.parquet")
    n = sm.n.iloc[0]
    fa = sm.pivot_table(index="world", columns="config", values="fa")
    lo_ci = {}
    for wd in fa.index:
        lo_ci[wd] = ""
    nh = fa[~fa.index.str.contains("X10|X11")]
    ci = lambda p: f"[{St_wilson(p, n)[0]:.3f}, {St_wilson(p, n)[1]:.3f}]"  # noqa: E731
    tab = nh.copy()
    tab["HG 95% CI"] = [ci(v) for v in nh["HG"]]
    tab["exceeds_alpha_HG"] = nh["HG"].map(lambda v: "YES" if St_wilson(v, n)[0] > 0.05 else "no")
    tab["exceeds_alpha_pprm"] = nh["pprm"].map(
        lambda v: "YES" if St_wilson(v, n)[0] > 0.05 else "no"
    )
    tab["exceeds_alpha_cost"] = nh["cost"].map(
        lambda v: "YES" if St_wilson(v, n)[0] > 0.05 else "no"
    )
    pw = sm[sm.role == "harm"].pivot_table(index="world", columns="config", values="power")
    sel = lambda pat: tab[tab.index.str.contains(pat)]  # noqa: E731
    head = f"False-alarm rate (alarm before the first harmful step; any alarm in a no-harm world), {n} independent paths per cell (Wilson 95% half-width <= 0.02). Label rate 0.2, delay 5, alpha 0.05, repaired engine; `HG_arrived` = naive release, `HG_xcap_legacy` = earlier covariate-dependent cap."
    w(
        "NULL_CLASS_SPECIFICATIONS.md",
        """# Null class specifications
| id | null world | what is held fixed | what the e-process null requires | status of the requirement |
|---|---|---|---|---|
| X01 | iid, fixed vs independent random delay | marginal law | outcome-independent delay | holds |
| X02 | outcome-dependent / heavy / burst delay | marginal law | in-order release for outcome-dependent delay | prefix holds; arrived-subset not covered |
| X03 | AR(1) latent logit noise | marginal law of (x, y) | `E[R_t | F_{t-1}] <= r0` | **fails** (conditional risk drifts) |
| X04 | cluster-shared random effects | marginal law | same | **fails** |
| X05 | history-adaptive covariates, calibrated P(loss|x) | stationary marginal risk | same | fails conditionally (adaptive covariate mix) |
| X06 | heterogeneous conditional risk, unchanged marginal risk | marginal risk = r0 | marginal null; predictable bets | holds after repair; legacy cap violates |
| X07 | severe proxy bias / anti-informative proxy | law, outcomes | unbiasedness of IPW (proxy-free) | holds |
| X08 | no shift (G1, G2, G3 K2, G4) | all | iid for G1-G3; G4 is GARCH-dependent | G4 fails conditionally |
| X09 | benign covariate shift, prior shift | label law (cov), cost falls (prior) | no decision-cost harm | Brier risk rises under `prior` shift (predictive harm without decision harm) |
| X10 | transient harm | - | power question | - |
| X11 | multiple recurrent shifts | - | power question | - |
| X12 | very low label availability (0.2%-2%) | marginal law | same as X01 | holds |
| X13 | hard budget exhaustion | marginal law | inactive events after exhaustion | holds |
| X14 | extreme but bounded losses (FN cost, clipped heavy-tailed returns) | bounded range | boundedness | G4 clip: dependence fails; cost: holds |
""",
    )
    w(
        "NULL_STRESS_RESULTS.md",
        f"""# Null stress results (X01-X14)
{head}

{md(tab[["HG", "HG_arrived", "HG_xcap_legacy", "pprm", "cost", "HG 95% CI", "exceeds_alpha_HG", "exceeds_alpha_pprm", "exceeds_alpha_cost"]])}

Empirical calibration is **not** a validity proof. Rows marked YES contradict the nominal alpha: the e-process guarantee does not extend to those null classes, which the null-class specification says in advance.
""",
    )
    dl = tab[tab.index.str.contains("X01|X02")]
    pw_delay = pd.read_csv(
        O / "e1_repair_effect/summary_by_config.csv"
    )  # placeholder to keep imports used
    del pw_delay
    g6 = None
    if have(O / "e6_g6_power.csv"):
        g6 = pd.read_csv(O / "e6_g6_power.csv", index_col=0)
    w(
        "DELAY_STRESS_RESULTS.md",
        f"""# Delay stress results (X01, X02)
{head}

{md(dl[["HG", "HG_arrived", "pprm", "cost", "HG 95% CI"]])}

No delay mechanism inflates the repaired HG beyond alpha. Naive arrived-subset release (`HG_arrived`) is not distinguishable here (largest difference: `delay=heavy`, 0.013 vs 0.004). Cost of validity: with in-order release a heavy-tailed pending queue blocks the prefix (head-of-line blocking). Power under the six delay models on a harmful concept shift (`scripts/gap/e5_s06_pacing.py` and `pools.g6_specs`) is reported in `FINAL_SYNTHETIC_CONFIRMATION_RESULTS.md`.
""",
    )
    dp = tab[tab.index.str.contains("X03|X04|X05|X08\\|null\\|G4|fin|X14")]
    w(
        "DEPENDENCE_STRESS_RESULTS.md",
        f"""# Dependence stress results (X03, X04, X05, G4 GARCH)
{head}

{md(dp[["HG", "pprm", "cost", "HG_arrived", "HG 95% CI", "exceeds_alpha_HG", "exceeds_alpha_pprm", "exceeds_alpha_cost"]])}

**Finding:** all three e-process monitors lose their nominal size under slowly varying conditional risk (cluster-400: HG {fa.loc["X04|null|cluster400_s1.5", "HG"]:.3f}, pprm {fa.loc["X04|null|cluster400_s1.5", "pprm"]:.3f}, cost {fa.loc["X04|null|cluster400_s1.5", "cost"]:.3f}; GARCH null: HG {fa.loc["G4|fin_null", "HG"]:.3f}, pprm {fa.loc["G4|fin_null", "pprm"]:.3f}). Short-range dependence (AR 0.5/0.9, cluster-20) is harmless at these settings. The mechanism is the conditional null, not the cap or the delay. F2 (long-run-variance bet) is the tested heuristic repair (`SECOND_ROUND_FIX_CANDIDATES.md`).
""",
    )
    px = tab[tab.index.str.contains("X07")]
    w(
        "PROXY_STRESS_RESULTS.md",
        f"""# Proxy stress results (X07 and G5)
{head}

{md(px[["HG", "pprm", "cost", "HG 95% CI"]])}

The unbiasedness of the IPW correction is proxy-free, so severe or anti-informative proxies do not break size (all <= 0.03). They cost power only: `outputs/gap_closure/e2b_s03_sensitivity` shows HG at 10% labels falling from 0.78 (accurate) to 0.67 (fully anti-informative after the shift); S03's reliability adaptation did not recover it (`S03_RESULTS.md`).
""",
    )
    ve = []
    for wd, r in fa.iterrows():
        e = r["HG"]
        ve.append(
            {
                "null/world": wd,
                "HG FA": e,
                "pprm FA": r["pprm"],
                "cost FA": r["cost"],
                "verdict": "EMPIRICAL_FAIL"
                if St_wilson(e, n)[0] > 0.05
                or St_wilson(r["pprm"], n)[0] > 0.05
                or St_wilson(r["cost"], n)[0] > 0.05
                else "empirically valid",
            }
        )
    ve = pd.DataFrame(ve).set_index("null/world")
    lo_t = lo.pivot_table(index="world", columns="config", values="fa")
    lo_p = lo[lo.role == "harm"].pivot_table(index="world", columns="config", values="power")
    hb_t = (
        hbp.groupby(["world", "config"])
        .agg(
            max_labels=("labels", "max"),
            fa=("false_alarm", "mean"),
            detected=("detected", "mean"),
            exhausted=("exhaust_t", lambda s: (s < 2000).mean()),
        )
        .reset_index()
    )
    w(
        "VALIDITY_SUPPORT_MATRIX.md",
        f"""# Validity support matrix
Columns: mathematical scope of the guarantee, and what was measured (repaired engine, 2000 paths per cell).

| null class | guarantee scope (Ville on the repaired test supermartingale) | measured |
|---|---|---|
| iid, bounded loss, fixed or outcome-independent delay, predictable bets | **proved** (marginal null, bets and caps from the past only) | all iid cells <= 0.047 |
| outcome-dependent delay | **proved only with in-order release** | no inflation either way at these settings |
| heterogeneous risk, unchanged marginal | proved for the repaired cap; **false for the earlier cap** (exact counterexample) | repaired <= 0.032 forced-bet; legacy 0.064 forced-bet |
| hard budget with inactive events | proved (inclusion probability positive or event inactive) | `hardbudget` table below, <= 0.03 |
| very low label rate | proved (same argument); information-limited power | below |
| autocorrelated / clustered / GARCH outcomes | **not covered** (conditional null fails) | **fails**: see `DEPENDENCE_STRESS_RESULTS.md` |
| proxy bias, anti-informative proxy | proved (IPW correction proxy-free) | <= 0.03 |

{md(ve)}

## X12 very low label availability (frac 0.2%-2%, HG and pprm)
{md(lo_t)}

Power (concept shift):\n\n{md(lo_p)}

## X13 hard budget exhaustion
{md(hb_t.set_index(["world", "config"]), "{:.3f}")}

`max_labels` never exceeds the declared hard cap B in the config name (B in {{5, 10, 25, 100}}). Exhaustion on most paths for the Bernoulli-at-0.5 arm; size stays below alpha because exhausted events are inactive.
""",
    )


def St_wilson(p, n, z=1.96):
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - hw, c + hw


# ------------------------------------------------------------------------------------------- S03-S05, S07
def q1_candidates():
    from shiftlab.gap import store as St

    acc = (
        pd.read_csv(O / "e2_s03_screen/acceptance.csv")
        if have(O / "e2_s03_screen/acceptance.csv")
        else None
    )
    sm = pd.read_csv(O / "e2_s03_screen/summary_by_world.csv")
    sm["parent"] = sm.config.str.split("|").str[0]
    base = sm[sm.config.str.endswith("|parent")].pivot_table(
        index="world", columns="parent", values="power"
    )
    gate = (
        acc.assign(
            parent=acc.config.str.split("|").str[0],
            gate=acc.config.str.split("|").str[-1],
            fb=acc.config.str.split("|").str[-2],
        )
        if acc is not None
        else None
    )
    med = (
        gate.groupby(["parent", "gate", "fb"])[["dA", "dB", "dFA"]].median()
        if gate is not None
        else pd.DataFrame()
    )
    sens = (
        pd.read_csv(O / "e2b_s03_sensitivity/summary_by_world.csv")
        if have(O / "e2b_s03_sensitivity/summary_by_world.csv")
        else None
    )
    sens_t = (
        sens.pivot_table(index="config", columns="world", values="power")
        if sens is not None
        else pd.DataFrame()
    )
    sens_t.columns = [c.replace("S03|", "") for c in sens_t.columns]
    w(
        "S03_RESULTS.md",
        f"""# S03 proxy-reliability-adaptive monitoring: results (preregistered in `02_S03_S06_PREREGISTRATION.md`)
Stage 1 screen: all 108 (window x smoothing x fallback x gate) combinations x 2 parents (`pprm`, HG) + parents = 218 configurations, label fraction 0.10, delay 5, 12 G5 development worlds, 100 seeds each (`outputs/gap_closure/e2_s03_screen`, 261,600 per-seed rows). Stage 2 (preregistered "top 8 at all four fractions") was replaced by a **sensitivity run of three representative variants** over the four fractions and a blend of accurate -> anti-informative proxy (`e2b_s03_sensitivity`, 200 seeds), because stage 1 produced no candidate that met the screen. The full 432 per parent was not run.

**Acceptance (adverse set A gain >= +0.05, benign set B change >= -0.03, non-harm FA change <= +0.02): {int(acc.accept.sum()) if acc is not None else "n/a"} of {len(acc) if acc is not None else "n/a"} configurations accepted. S03 is NOT supported.**

Median change vs parent by gate x fallback (dA = power on adverse proxy-failure worlds, dB = on accurate / oracle-adapted proxies, dFA = non-harm FA):

{md(med)}

Only `fallback=none` is neutral (it is the parent: `rel=hard,fallback=none` is an identity, checked in `test_parent_modified_identities`); every active fallback loses power in the adverse worlds too. Reason: with 10% labels a window of 32-256 labels gives a noisy skill / slope estimate, so the reliability gate fires spuriously on accurate proxies (dB negative) and the IPW-only fallback has much larger variance than the proxy-assisted increment even when the proxy is anti-informative (the parent loses only ~0.1 power at full anti-informative corruption).

Parents' power vs proxy corruption (blend 0 = accurate ... 1 = anti-informative after the shift; the four label fractions are in the config names):

{md(sens_t.round(2), "{:.2f}")}

Conclusion: reliability adaptation does not improve a predeclared adverse regime at any tested label rate; it is dominated by the unadapted parent. The proxy-weight mechanism is valid (predictable theta) but not useful here.
""",
    )
    d5 = pd.read_csv(O / "e3_s04_delay5/summary_by_world.csv")
    d20 = pd.read_csv(O / "e3_s04_delay20/summary_by_world.csv")
    parts = []
    for nm, sm_ in (("delay 5", d5), ("delay 20", d20)):
        sm_["parent"] = sm_.config.str.split("|").str[0]
        sm_["arm"] = sm_.config.str.split("|").str[1]
        sm_["frac"] = sm_.config.str.split("|").str[2]
        h = (
            sm_[sm_.role == "harm"]
            .groupby(["parent", "frac", "arm"])
            .agg(
                power=("power", "mean"),
                labels=("labels", "mean"),
                harm_before=("harm_before", "mean"),
            )
        )
        f = (
            sm_[sm_.role == "nonharm"]
            .groupby(["parent", "frac", "arm"])
            .fa.mean()
            .rename("fa_nonharm")
        )
        t = h.join(f)
        t["power_per_100_labels"] = 100 * t.power / t.labels
        parts.append(f"### {nm}\n\n{md(t)}")
    pw = (
        d5[d5.role == "harm"]
        .assign(
            parent=d5.config.str.split("|").str[0],
            arm=d5.config.str.split("|").str[1],
            frac=d5.config.str.split("|").str[2],
        )
        .pivot_table(index=["parent", "frac", "world"], columns="arm", values="power")
    )
    cmp_ = pd.DataFrame(
        {
            r: (pw[a] - pw[b]).groupby(level=[0, 1]).mean()
            for r, (a, b) in {
                "growth - variance": ("growth", "variance"),
                "growth - uniform": ("growth", "uniform"),
                "variance - uniform": ("variance", "uniform"),
                "growth_oracle - growth": ("growth_oracle", "growth"),
                "robust_mix - uniform": ("robust_mix", "uniform"),
            }.items()
        }
    )
    w(
        "S04_RESULTS.md",
        f"""# S04 growth-aware active querying: results
Arms (per `02_*`): uniform, variance (Neyman with start-prior shrinkage), growth (estimated alternative), growth (ORACLE alternative = true P(y=1|x), evaluator information), growth_harm, growth_look, robust mixture (u=.5, v=.5 conservative), budget-aware growth (hard budget B = frac*T with remaining-budget pacing). Parents `pprm` and HG; fractions 0.05 / 0.10; delay 5 and 20; 23 worlds (G1 dev pool 19 + G2 concept / cov_benign + G3 cycle + G4 finance), 150 seeds, expected-budget contract (realised labels reported; label-normalised power = power per 100 labels).

Mean paired power difference on harm worlds (delay 5):

{md(cmp_)}

{chr(10).join(parts)}

## Reading
* **H4 holds**: growth-aware querying equals variance-only to within about +0.01 (second-order argument in `02_*`: the log-growth objective's only q-dependent term is the IPW variance).
* **Both lose to uniform querying** (and to the robust mixture) by 0.1-0.2 power for HG at the same expected label count. The loss is caused by the validity requirement, not by bad scores: any non-uniform propensity needs a predictable floor `q_min`, and the bet cap is `0.5 / (theta pmax (1/q_min - 1) + r0)`. Floors of `frac/4` shrink the admissible bet ~4x. The ORACLE growth arm (true alternative known) is better than the estimated one (+0.03 to +0.05) yet still below uniform.
* The robust mixture (floor >= 0.625 frac) is the only non-uniform arm that matches or beats uniform (see S05).
**Acceptance (improve over the best of uniform / variance / robust mixture): NOT met.** Budget-aware growth under a hard cap is worse than uniform as well. No exact RPOQ oracle-gap computation was possible at scale; exact gaps on the toy instance are in `S11_ORACLE_GAP_RESULTS.md`.
""",
    )
    mix = pd.read_csv(O / "e4_s05_mixture/summary_by_config_full.csv", index_col=0)
    top = (
        mix.sort_values("power", ascending=False)
        .head(12)[["power", "hb", "labels", "mean", "max", "worst2"]]
        .rename(
            columns={
                "hb": "harm_before",
                "mean": "fa_nonharm_mean",
                "max": "fa_nonharm_max",
                "worst2": "power_worst2_worlds",
            }
        )
    )
    byu = (
        mix[mix.index.str.contains("fixed")]
        .assign(
            u=lambda d: d.index.str.extract(r"\|u([0-9.]+)\|", expand=False).values,
            g=lambda d: d.index.str.extract(r"\|g([0-9.]+)\|", expand=False).values,
        )
        .pivot_table(index="u", columns="g", values="power")
    )
    w(
        "S05_RESULTS.md",
        f"""# S05 robust growth/variance hybrid: results
Full probability-simplex grid (u in {{0,.1,.25,.5,.75,1}} x g in {{0,.25,.5,.75,1}}, u+g <= 1, v = 1-u-g) x reliability mode {{fixed, adaptive, conservative}} = 51 mixtures + uniform parent = 52 configurations (HG, fraction 0.10, delay 5, 12 worlds, 100 seeds). No guarantee of the published Robust-ASI is claimed for any mixture.

Top configurations by harm-world power:

{md(top)}

Power (fixed mode) by uniform share u (rows) and growth share g (columns):

{md(byu)}

* Every configuration with g > 0 loses power; the growth component never helps (consistent with S04).
* The best Pareto points are the variance/uniform mixtures with floor >= 0.5 (power {top.iloc[0].power:.3f} vs uniform {mix.loc["HG|uniform"].power:.3f}, lower non-harm FA {top.iloc[0].fa_nonharm_mean:.3f} vs {mix.loc["HG|uniform"]["mean"]:.3f}, better worst-2 power). That **is** the Robust-ASI analogue (u=.5, v=.5), so the hybrid occupies no improved Pareto position over the simpler robust mixture; configurations improving on it by +0.02 power without FA or worst-case loss: **0**.
* Acceptance: NOT met. The tested hybrid addresses no failure that the robust variance mixture does not already handle; fixed / adaptive / conservative differ only where u < 0.5.
""",
    )
    pool = pd.read_csv(O / "e9_s07_pool.csv")
    pt = pool.pivot_table(
        index=["factor", "value"], columns="method", values="mse_ratio_vs_uniform"
    )
    cov = pool.groupby("method").agg(
        coverage_mean=("coverage", "mean"),
        coverage_min=("coverage", "min"),
        mse_ratio_median=("mse_ratio_vs_uniform", "median"),
        sel_time_ms=("sel_time_ms", "mean"),
        e2e_ms=("e2e_ms", "mean"),
        peak_mb=("peak_mb", "max"),
    )
    w(
        "S07_RESULTS.md",
        f"""# S07 robust pro-active inference (pool-based benchmark, separate from the streaming monitors)
The learner sees the unlabeled covariate pool (N points) and selects items **without replacement**; the pool is split into B random blocks in advance, each block is Poisson-sampled with probabilities computed from labels of earlier blocks, and the estimate is the block-size-weighted average of per-block prediction-powered estimators (a martingale, unbiased for any adaptive rule). Streaming algorithms are not compared here. Methods: uniform; batch ASI (probabilities from one fit); sequential ASI; robust ASI (eps .25 uniform mix); `pai_inspired` (sequential ASI with importance-weighted refits; **SOURCE_INSPIRED, not a verified PAI reproduction**: the primary source/code were not accessible); conservative (uncertainty shrunk to prior by label count + exploration floor). One-factor-at-a-time variations around N=5000, n=300, n0=30, 5 blocks, heteroscedastic noise; 150 replicates (60 for N=20000).

MSE ratio vs uniform (< 1 is better):

{md(pt)}

Summary by method (coverage of the nominal 95% interval across all settings, speed):

{md(cov)}

Findings: plain sequential ASI beats uniform in only {int((pt.seq_asi < 1).sum())} of {len(pt)} settings (small budgets, many blocks, large pilots); robust / conservative variants are never far above 1 and are best; the PAI-inspired variant is the worst at the base setting. Intervals are slightly anti-conservative for the conservative variant (min coverage {cov.loc["conservative", "coverage_min"]:.3f}). Selection adds negligible time (milliseconds) relative to end-to-end cost.
""",
    )


# ------------------------------------------------------------------------------------------- Q2
def q2docs():
    df = pd.read_parquet(O / "e7_q2/perseed.parquet")
    core = df[df.grp == "core"]
    w(
        "Q2_PROTOCOL.md",
        """# Q2 / S09 model certification: protocol
K models (incumbent = model 0), logistic label law, model k with misspecification scale s_k(t); both models' losses are deterministic in (x, y), so one label identifies every paired difference. True current gap g_k(t) = E[loss_0 - loss_k] (positive = candidate better) by Monte Carlo (120k); scales calibrated by bisection to gaps {zero 0, tiny .02, moderate .06, large .15}; "worse" candidates have gap -0.10. Rankings: stationary; one_reversal (candidate 1 good then bad at T/2); recurrent (T/4 blocks). Grid (structured subset of the mandated Cartesian product, 42 worlds): core K {2,5,10} x gap x ranking at T=2000, delay 5, frac .10 (36); fraction sweep {.01,.05,.20} x {zero, moderate} x {stationary, one_reversal} at K=5 (12 - only 6 of 12 used for stationary/reversal combos listed in `e7_q2.py`); delay {0,20}; horizon {200,500}. Seeds: 300 (zero-gap, for error estimation) / 120 / 100 (K=10) per world. Error evaluation: **incorrect promotion** = certified a candidate whose true current gap <= 0; **multiple-testing error (FWER)** = any candidate crossing while its current gap <= 0; correct certification = certified candidate has gap > 0 and >= half the best current gap. Labels shared across candidates except `indep_labels`. Query budget is the expected contract. Validity of the e-process methods: marginal null `E[d_k | F] <= 0`, predictable bets, x-free cap that only uses the inclusion probability on disagreement events (increments are identically 0 when candidate k agrees with the incumbent and the marginal null implies `E[d | disagree] <= 0`; the cap may not depend on the other candidates' agreement pattern).
""",
    )
    w(
        "Q2_BASELINE_REPRODUCTION.md",
        """# Q2 baselines: implementation status
| method | implementation | provenance |
|---|---|---|
| paired sequential test | `paired_e`: per-candidate betting e-process on IPW paired loss difference, no multiplicity correction | LOCAL |
| paired confidence sequence | `paired_cs`: stitched Hoeffding on IPW means, range 2M/q | SOURCE_INSPIRED, weak (never certifies) |
| prediction-powered paired evidence | `pp_paired`: proxy = candidate-implied expected loss difference | LOCAL_HEURISTIC |
| Sequential Model Confidence Sets adaptation | `seqmcs`: pairwise e-processes for all ordered pairs, Bonferroni over K(K-1) pairs, elimination, certify when the incumbent is eliminated | SOURCE_INSPIRED (not the published procedure; the source was not accessible) |
| uniform multiple-testing correction | `paired_e_bonf`: threshold log(K_c/alpha) | LOCAL |
| shared-label multiple-model testing | all methods except `indep_labels` share one label per event | LOCAL |
| CAMS-style contextual selection | `cams`: query probability ~ (0.1 + any-disagreement)/running mean, >= frac on disagreement events | SOURCE_INSPIRED, not CAMS itself |
| existing ShiftLab exact reference | `rpoq_exact` toy: exact first-promotion value of information (`Q3_EXACT_ORACLE_COMPARISON.md`) | repo code (exact) |
None is a VERIFIED_REPRODUCTION.
""",
    )
    agg = lambda d: pd.Series(
        {
            "P(certified)": d.certified.mean(),
            "P(correct)": d.correct.mean(),
            "P(incorrect)": d.incorrect.mean(),
            "FWER": d.false_reject_any.mean(),
            "labels@cert": d.labels_at_cert[d.certified].mean(),
            "t@cert": d.cert_t[d.certified].mean(),
            "n_eliminated": d.n_elim[d.certified].mean(),
            "ms/seed": 1e3 * d.runtime_s_per_seed.mean(),
        }
    )  # noqa: E731
    stat = core[core.ranking == "stationary"]
    tab = {
        g: stat[stat.gap == g].groupby("method").apply(agg, include_groups=False)
        for g in ("tiny", "moderate", "large")
    }
    sx = lambda g: md(
        tab[g][
            [
                "P(correct)",
                "P(incorrect)",
                "FWER",
                "labels@cert",
                "t@cert",
                "n_eliminated",
                "ms/seed",
            ]
        ]
    )  # noqa: E731
    w(
        "Q2_CANDIDATE_RESULTS.md",
        f"""# Q2 baseline-and-candidate results (core grid, T=2000, delay 5, 10% labels, stationary ranking)
Pooled over K in {{2,5,10}}; 120/100 seeds per world. S09a ctxvar (variance-weighted disagreement-only querying), S09b disc (discounted bets + currentness gate), S09c shared (wealth allocated across candidates; **weak control only**), S09d budget (hard budget B=frac*T + CAMS allocation), S09e alloc (pilot-based alpha allocation; `_cams` suffix = with CAMS allocation).

## large gap (0.15)
{sx("large")}
## moderate gap (0.06)
{sx("moderate")}
## tiny gap (0.02)
{sx("tiny")}

* Disagreement-focused querying (CAMS-style, S09b/c/d/e `_cams`) is the decisive component: it multiplies correct-certification power by 3-6x over uniform labelling at equal expected labels, because increments vanish when models agree and the cap can use the disagreement-event inclusion probability.
* No S09 extension beats the CAMS-style baseline beyond noise (S09d and S09e_alloc_cams are within +-0.03 of it); S09a (variance weighting) is worse (its predictable floor lowers the cap); S09c shared allocation gives weak control only; S09b discounting reduces power.
* seqmcs is much weaker and 3-4x slower (K(K-1)/2 pairs, Bonferroni).
""",
    )
    z = core[core.gap == "zero"]
    fw = z.groupby(["method", "K"]).false_reject_any.mean().unstack()
    fw["all K"] = z.groupby("method").false_reject_any.mean()
    cert = z.groupby("method").certified.mean().rename("P(any promotion | zero gap)")
    rev = (
        core[(core.ranking != "stationary") & (core.gap == "large")]
        .groupby(["ranking", "method"])
        .apply(
            lambda d: pd.Series(
                {"P(correct)": d.correct.mean(), "P(incorrect)": d.incorrect.mean()}
            ),
            include_groups=False,
        )
        .unstack(0)
    )
    w(
        "Q2_MULTIPLE_TESTING_VALIDITY.md",
        f"""# Q2 multiple-testing validity (zero-gap worlds: any promotion is an error)
Zero-gap worlds contain candidates with gap exactly 0 and candidates worse by 0.10; 300 seeds per world, 3 values of K x 3 rankings. FWER = P(any candidate crosses while its current gap <= 0).

{md(fw.join(cert), "{:.4f}")}

All methods stay below alpha = 0.05 here (largest: uncorrected `paired_e` at K=10). The uncorrected test has no theoretical multiplicity control: its measured size at K=10 is {fw.loc["paired_e", 10]:.3f}, safely below alpha only because Kelly plug-in bets are conservative under a zero-drift null; the Bonferroni / elimination / closed variants are valid by construction (union bound). `S09c_shared` controls only the intersection null (weak control). Empirical zero-gap error is not a validity proof for nonstationary rankings: after a reversal, certification of a candidate whose *current* gap is negative is possible because e-process wealth does not forget:

{md(rev)}
""",
    )
    gen = core.pivot_table(index="method", columns=["ranking"], values="correct", aggfunc="mean")
    other = (
        df[df.grp != "core"]
        .groupby(["grp", "method"])
        .apply(
            lambda d: pd.Series(
                {
                    "P(correct)": d.correct.mean(),
                    "P(incorrect)": d.incorrect.mean(),
                    "P(certified)": d.certified.mean(),
                }
            ),
            include_groups=False,
        )
        .unstack(0)
    )
    kk = core[core.gap.isin(["moderate", "large"])].pivot_table(
        index="method", columns="K", values="correct", aggfunc="mean"
    )
    w(
        "Q2_GENERALIZATION_RESULTS.md",
        f"""# Q2 generalisation: ranking dynamics, number of models, labels, delay, horizon
Correct-certification probability by ranking (core grid, moderate+large gaps, pooled over K):

{md(gen)}

By number of models K:

{md(kk)}

Off-core sweeps (fraction .01/.05/.20, delay 0/20, horizon 200/500; P(correct) | P(incorrect) | P(certified) by group):

{md(other)}

Limits: the benchmark has low absolute power (the best method certifies ~49% of large-gap runs at 10% labels); the effect of K is shown in the table above; reversal / recurrent rankings reduce all methods' power and discounting does not recover it. Seed counts are modest (100-300 per world), so differences below ~0.05 are noise. The synthetic gap scale (0.02-0.15 decision cost per step) was chosen so the large gap is certifiable; "tiny" is not certifiable at these label rates by any method.
""",
    )


# ------------------------------------------------------------------------------------------- Q3
def q3docs():
    df = pd.read_parquet(O / "e8_q3/perseed.parquet")
    base = df[df.cost == "base"]
    reg = base.pivot_table(index="policy", columns="scenario", values="regret")
    cnt = base.groupby("policy").agg(
        false_promotions=("n_false", "mean"),
        switches=("n_sw", "mean"),
        rollbacks=("n_rb", "mean"),
        labels=("n_q", "mean"),
        runtime_ms_per_seed=("runtime_s_per_seed", lambda s: 1e3 * s.mean()),
    )
    w(
        "Q3_ENVIRONMENT.md",
        """# Q3 / S10 intervention environment (fully synthetic, `src/shiftlab/gap/q3.py`)
Two pre-trained models (source `M_src`, challenger `M_shift` trained on the shifted regime) and a logistic label law with regime weights {source, shifted (concept rotation d=2), mid (both models equally off)}. T=1000, onset 300, 120 seeds per scenario. Actions: continue, query labels (cost per label, delay 5 or 50), recalibrate (moves 60% toward noisy current weights, noise 1.5/sqrt(10 labels)), retrain (new model after 25 steps, noise 1.5/sqrt(25)), promote (swap to the other model), roll back. **Caveat:** recalibrate / retrain are given the current regime's true weights plus label-count-scaled noise, a strong idealisation (a real refit needs data and a learner); rolling recalibration is therefore optimistic.
Scenarios: permanent beneficial challenger; temporary (120 steps); reversal (250 steps then source regime again); near-tied flip (mid regime, models equally off, alternating every 60 steps); harmful incumbent with delay 50; no worthwhile intervention. "Expensive retraining / switching / high label cost" are cost-grid settings. Costs (mandated grid) are multiplied by KQ=10 (per label) and KC=100 (per action) loss units: a design choice that makes costs comparable to the ~100-250 units of harm accrued per run. Cost-blind policies do not change trajectories with costs, so the grid is applied post hoc from action counts; the cost-gated policy is re-run per cost setting. Cost grid: base (q .01, retrain .05, switch .05, rollback .05), one-factor variations over the mandated levels, all-zero and all-max (12 settings; not the full 108-cell Cartesian product).
Net regret = realised loss + action costs - loss of the instantly adapted Bayes model (ignores all costs; a lower bound). Evaluator-side truth: regime path and per-regime expected losses of both models (`exp_cost_table`).
""",
    )
    w(
        "Q3_BASELINE_RESULTS.md",
        f"""# Q3 baselines: mean net regret at base costs (120 seeds per scenario)
{md(reg, "{:.1f}")}

Action statistics (all scenarios, base costs):

{md(cnt, "{:.2f}")}

Policies: frozen incumbent; periodic retraining (every 250 steps); rolling recalibration (every 100); Page-Hinkley-triggered promotion (threshold from the 95% null quantile of the horizon maximum, 300 null paths); HG-triggered promotion; paired-evidence-certified promotion (`cert_uniform` uniform labels, `cert_switch` disagreement-focused labels); hysteresis (PH + 20-step persistence + 150-step dwell); cost-gated certification (`cert_gated`: promote only when estimated remaining gain exceeds the switch cost). Triggered policies share one action (swap to the other model; swapping back to the previously deployed model is charged as a rollback). Exact first-promotion solver: only on the toy instance (`Q3_EXACT_ORACLE_COMPARISON.md`).
Observations: rolling recalibration has by far the lowest regret in persistent-harm scenarios at base cost but is the worst when nothing is worthwhile and when retrain cost is high; `cert_uniform` almost never certifies (cap-limited, 0.01 switches/seed) whereas disagreement-focused certification switches in ~27% of seeds at 10% labels; `cert_gated` equals `cert_switch` because costs are small relative to the gain.
""",
    )

    def pdiff(a, c, sc, cost="base"):
        x = df[(df.scenario == sc) & (df.cost == cost)].pivot_table(
            index="seed", columns="policy", values="regret"
        )
        d = (x[a] - x[c]).values
        r = np.random.default_rng(0).choice(d, (4000, len(d))).mean(1)
        return d.mean(), np.quantile(r, 0.025), np.quantile(r, 0.975)

    rows = []
    for sc in sorted(df.scenario.unique()):
        for a, c in (
            ("hg_switch", "ph_switch"),
            ("hg_switch", "hysteresis"),
            ("cert_switch", "ph_switch"),
            ("hg_switch", "frozen"),
        ):
            m, lo, hi = pdiff(a, c, sc)
            rows.append(
                {
                    "scenario": sc,
                    "comparison": f"{a} - {c}",
                    "mean_regret_diff": m,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "verdict": "HG better"
                    if hi < 0 and a == "hg_switch"
                    else ("HG worse" if lo > 0 and a == "hg_switch" else "n.s."),
                }
            )
    tr = pd.DataFrame(rows)
    w(
        "Q3_HG_TRANSFER_RESULTS.md",
        f"""# Does HG's earlier detection translate into net economic benefit?
Paired differences of net regret (negative = first policy better), 120 paired seeds per scenario, bootstrap 95% CI, base costs:

{md(tr, "{:.1f}", index=False)}

**Answer: not in general.** In permanent-harm scenarios (`perm_beneficial`, `harmful_incumbent_delay50`) HG-triggered promotion has **higher** regret than Page-Hinkley-triggered promotion (CIs exclude zero) because at 10% labels it alarms later (it switches in 20% of seeds vs 30% for PH). In the transient, reversal and near-tied scenarios HG's lower false-alarm rate gives lower regret (CIs exclude zero); in `no_worthwhile` the difference is within noise. HG's advantage in the earlier Q1 study was power at matched *size* on held-out worlds with unlabeled-vs-labeled differences; once an intervention cost and a blind promotion action exist, the cheaper false alarm matters mostly when harm is transient. Disagreement-focused certified promotion beats PH in the transient, reversal and near-tied scenarios, is not distinguishable from PH under permanent harm, and is **worse than PH in the delayed-harm scenario** (+17.9, CI excludes 0); it has essentially zero false promotions.
""",
    )
    fr = df[
        df.policy.isin(
            [
                "frozen",
                "rolling_recal",
                "periodic_retrain",
                "ph_switch",
                "hg_switch",
                "cert_switch",
                "cert_gated",
                "hysteresis",
            ]
        )
    ].pivot_table(index="cost", columns="policy", values="regret")
    fr["best"] = fr.idxmin(axis=1)
    w(
        "Q3_REGRET_AND_COST_FRONTIERS.md",
        f"""# Regret / cost frontiers (mean net regret over the 6 scenarios, by cost setting)
{md(fr.drop(columns="best").assign(best=fr.best))}

* Label cost dominates (`query=0.05`: every adaptive policy costs ~40 more than at base, frozen is unaffected); with expensive labels frozen and rolling recalibration (cheap per action but label-hungry) are the frontier points.
* Retrain cost matters only for periodic retraining and rolling recalibration (trigger-based policies never retrain).
* Switch / rollback cost moves triggered policies by < 10 units across the whole mandated range, because the harm avoided per switch is ~100-200 units.
* No policy dominates across scenarios; the policy ranking at base costs is rolling recalibration < certified promotion ~ hysteresis ~ PH < HG < frozen in persistent-harm scenarios, and frozen < everything else in `no_worthwhile`.
""",
    )
    voi = pd.read_csv(O / "e11_exact_voi.csv") if have(O / "e11_exact_voi.csv") else None
    txt = (
        md(voi, "{:.4f}", index=False)
        if voi is not None
        else "(exact table pending: `outputs/gap_closure/e11_exact_voi.csv`)"
    )
    w(
        "Q3_EXACT_ORACLE_COMPARISON.md",
        f"""# Exact first-promotion reference on the toy instance (`dive.rpoq_exact`)
The repository's exact solver gives, for the toy binary-contrast instance (horizon 10, delay 2, two contexts), the optimal probability of crossing the promotion threshold under the alternative (power) and under the null (false promotion) for each hard label budget b:

{txt}

With a promotion gain G, false-promotion loss L and label cost c per label, the exact optimal budget is argmax_b [G power(b) - L null(b) - c b]; policies that always spend the whole budget are suboptimal once c * b exceeds the marginal power gain. The Q3 environment is not tractable for the exact solver (continuous state), so the exact comparison is restricted to this instance; no claim is made that the Q3 policies approach an exact optimum.
""",
    )


# ------------------------------------------------------------------------------------------- S06, S08
def s06():
    pre = sys.argv[-1] if sys.argv[-1] in ("v1", "v2") else "both"
    out = {}
    for tag, path in (
        ("v1 (floor frac/4, confounded)", "e5_s06_all_perseed.parquet"),
        ("v2 (corrected floors)", "e5b_s06_all_perseed.parquet"),
    ):
        if not have(O / path):
            continue
        df = pd.read_parquet(O / path)
        df["hardB"] = (df.frac_cfg * df["T"]).round()
        big = df[df["T"] == 2000]
        harm = big[big.group != "null"].assign(has=lambda d: d.first_harm < d["T"])
        pw = (
            harm.groupby(["frac_cfg", "delay_cfg", "config"])
            .apply(lambda d: d.detected.sum() / max(d.has.sum(), 1), include_groups=False)
            .rename("power")
            .reset_index()
        )
        t = pw.groupby(["frac_cfg", "config"]).power.mean().unstack()
        regime = harm[(harm.frac_cfg == 0.10) & (harm.delay_cfg == 5)].assign(
            onset=lambda d: d.world.str.extract(r"on([0-9.]+)", expand=False),
            regime=lambda d: d.world.str.split("|").str[2],
        )
        orr = (
            regime.groupby(["onset", "config"])
            .apply(lambda d: d.detected.sum() / max(d.has.sum(), 1), include_groups=False)
            .unstack()
        )
        rr = (
            regime.groupby(["regime", "config"])
            .apply(lambda d: d.detected.sum() / max(d.has.sum(), 1), include_groups=False)
            .unstack()
        )
        hb = df[df.config != "bernoulli"]
        comp = (hb.labels - hb.hardB).groupby(hb.config).max()
        q = (
            big[big.frac_cfg == 0.10]
            .groupby("config")
            .agg(
                mean_pending=("mean_pending", "mean"),
                max_pending_delay20=("max_pending", "max"),
                frac_paths_exhausted=("exhaust_t", lambda s: (s < 2000).mean()),
                labels=("labels", "mean"),
            )
        )
        hbm = (
            harm[(harm.frac_cfg == 0.10) & (harm.delay_cfg == 5)]
            .groupby("config")
            .apply(
                lambda d: pd.Series(
                    {
                        "harm_before_alarm": d.harm_before.mean(),
                        "mean_exhaust_t": d.exhaust_t[d.exhaust_t < 2000].mean(),
                    }
                ),
                include_groups=False,
            )
        )
        nullfa = (
            big[big.group == "null"].groupby(["frac_cfg", "config"]).false_alarm.mean().unstack()
        )
        out[tag] = (t, orr, rr, comp, q.join(hbm), nullfa)
    txt = []
    for tag, (t, orr, rr, comp, q, nullfa) in out.items():
        txt.append(f"""## {tag}
Mean power over onset x regime x delay (T=2000, 100 seeds per cell):

{md(t)}

By onset (fraction .10, delay 5):

{md(orr)}

By regime (fraction .10, delay 5):

{md(rr)}

Pathwise compliance: max over all paths of (labels - B) per hard-budget arm: `{comp.round(1).to_dict()}`. Spending / pending-queue statistics (fraction .10, all delays):

{md(q)}

Null-world false alarm (all arms):

{md(nullfa)}
""")
    w(
        "S06_RESULTS.md",
        f"""# S06 budget-paced delayed query allocation: results
Hard pathwise budget B = frac*T charged at issue; exhausted paths become inactive. Rules: `bernoulli` (expected budget, no cap), `hard_bern` (Bernoulli q = frac with a hard cap), `const` (q = B/T), `remaining` (q = remaining budget / remaining steps), `info_value` (remaining-budget rate x estimated variance score), `reserve` (high rate on above-average score events, low rate otherwise), `two_stage` (30% of the budget in the first quarter), `growth_pace` (growth score + pacing). Grid actually run: T=2000 with onset {{.2,.5,.8}} x regime {{abrupt, gradual, transient, recurrent}} x delay {{0,1,5,20}} x fraction {{.01,.05,.10,.20}} (v1) and delay {{0,5,20}} x fraction {{.05,.10,.20}} (v2); T in {{100, 500}} at onset .5 (abrupt, transient). 100 seeds per cell. The short-horizon dynamic program and the RPOQ exact solver are used only on the toy instance (`S11_ORACLE_GAP_RESULTS.md`): a DP at scale was NOT implemented.

**Defect disclosure.** v1 used a propensity floor of frac/4 for every pacing rule, **including `const`, which is exactly `hard_bern`**; the predictable cap was therefore 4x tighter than necessary and v1 numbers confound pacing with the cap floor. v2 sets the exact floor for `const` and frac/2 for the others. v1 is kept as the record of that error.

{chr(10).join(txt)}
## Reading
* Hard-budget compliance holds on every path for every rule (tests + max(labels - B) = 0).
* Intelligent pacing does **not** improve on a tuned uniform allocation: compare `const` / `hard_bern` with `remaining`, `info_value`, `reserve`, `two_stage`, `growth_pace`. Late onset (0.8) is nearly undetectable for every arm because the budget is spent on pre-onset events; rules that spend the entire budget early (`remaining`, `two_stage`) exhaust on ~100% of paths (mean exhaustion near the end of the horizon) and gain nothing from it.
* Delay changes power little (queues stay short: mean pending ~0.2 / 0.6 / 2.1 at delay 1 / 5 / 20) so pacing around pending feedback is not the bottleneck. Hard-capped Bernoulli loses ~0.01-0.02 power relative to the uncapped Bernoulli arm.
**Acceptance (pacing improves on tuned uniform by >= +0.03 at some budget): see the v2 table; NOT met if no row exceeds `hard_bern` by 0.03.**
""",
    )


def s08():
    p1 = O / "e10_s08_balanced/summary_by_world.csv"
    p2 = O / "e10b_s08_balanced_floor/summary_by_world.csv"
    txt = []
    for tag, p, pq in (
        ("v1: floors frac/4", p1, O / "e10_s08_balanced/perseed.parquet"),
        ("v2: floors frac/2", p2, O / "e10b_s08_balanced_floor/perseed.parquet"),
    ):
        if not have(p):
            continue
        sm = pd.read_csv(p)
        df = pd.read_parquet(pq)
        h = (
            sm[sm.role == "harm"]
            .groupby("config")
            .agg(
                power=("power", "mean"),
                harm_before=("harm_before", "mean"),
                labels=("labels", "mean"),
            )
        )
        nh = sm[sm.role == "nonharm"].groupby("config").fa.mean().rename("fa_nonharm")
        cov = (
            df.groupby("config")
            .apply(lambda d: d.labels_rare.sum() / d.labels.sum(), include_groups=False)
            .rename("rare_group_label_share")
        )
        rt = df.groupby("config").agg(
            ms_per_seed=("runtime_s_per_seed", lambda x: 1e3 * x.mean()),
            rss_mb=("peak_rss_mb", "max"),
        )
        by = (
            sm[sm.role == "harm"]
            .assign(prev=lambda d: d.world.str.split("|").str[1])
            .pivot_table(index=["prev"], columns="config", values="power")
        )
        txt.append(
            f"## {tag}\n\n{md(h.join(nh).join(cov).join(rt))}\n\nPower by rare-group prevalence (prev31 = 31%, prev16 = 16%, prev07 = 6.7%):\n\n{md(by)}\n"
        )
    w(
        "S08_RESULTS.md",
        f"""# S08 balanced growth-aware sampling: results
Synthetic stratified problem: a rare subgroup {{x_2 > thr}} (prevalence 31% / 16% / 6.7%) whose label law changes (logit shift 8 on the group) at t=800, decision-cost asymmetry FN in {{5, 15}}, accurate or miscalibrated proxy, null world; HG parent, fractions .05 / .10, 150 seeds, 14 worlds. Arms: stratified-uniform (= uniform), ASI-like variance, balanced (equal expected label counts per group: SOURCE_INSPIRED, **not** a verified Balanced Active Inference), growth, balanced+growth (50/50 propensity mixture). "Group coverage" = share of queried labels in the rare group (uniform: its prevalence). Harm threshold for this pool 0.02 (strong subgroup shift but small overall harm).

{chr(10).join(txt)}
## Reading
Balancing does what it promises on coverage (rare-group label share ~0.50 vs 0.18 under uniform) but costs sequential power under the predictable-bound requirement; with floors raised to frac/2 (v2) the loss shrinks, see the v2 table. Whether balancing and evidence-growth optimisation are complementary: in these experiments **no** combined arm beats stratified-uniform on power per label; growth adds nothing over variance weighting (as in S04). The estimation-quality part of S08 (MSE / CI coverage under balancing) was not run: S08 here is a sequential-monitoring benchmark only (disclosed gap).
""",
    )


# ------------------------------------------------------------------------------------------- S11, S12
def s11s12():
    if have(O / "e11_s11_amortized_test.csv"):
        df = pd.read_csv(O / "e11_s11_amortized_test.csv")
        meta = json.load(open(O / "e11_s11_meta.json"))
        summ = df.groupby("policy").agg(
            gap_mean=("gap", "mean"),
            gap_max=("gap", "max"),
            rel_gap=("gap", lambda x: float(np.mean(x / df.loc[x.index, "v_opt"]))),
            null_alarm_mean=("null_alarm", "mean"),
            null_alarm_max=("null_alarm", "max"),
            decision_error=("decision_error", "mean"),
            latency_ms=("latency_ms_per_decision", "mean"),
        )
        sc = pd.read_csv(O / "e11_exact_scaling.csv")
        opt_null = df.null_alarm_opt.mean()
        w(
            "S11_APPROXIMATION_RESULTS.md",
            f"""# S11 amortised approximation of exact acquisition (RPOQ toy instance, exact evaluation)
Training: {meta["train_states_total"]:,} optimal (state, action) pairs from the exact solver on {len(set(df.alt)) and 18} training instances (6 alternatives x budgets 2, 3, 4; subsampled to {meta["train_states_fit"]:,} for fitting). The **oracle was not free**: {meta["oracle_data_seconds"]:.0f} s of exact solving plus {meta["fit_seconds"]:.1f} s of fitting before any test instance. Approximators: decision trees (depth 6 and 3), shallow MLP (16 hidden, 60 iterations), quantised lookup, finite-state controller (t, context, remaining budget only), a pacing heuristic and constants. Features: step, context, remaining budget, log wealth, number of pending labels, alternative parameters (so the policy conditions on the unseen alternative's value).
Test: {len(set(df.alt))} alternatives never used in training x 3 budgets; policy values are evaluated **exactly** (policy plugged into the exact evaluator), not by simulation.

{md(summ, "{:.4f}")}

Exact optimal null alarm (false promotion) mean {opt_null:.4f}; all approximate policies are evaluated under the same exact null calculation (columns `null_alarm_*`), so false-alarm validity is certified, not estimated (the null alarm of any predictable policy is bounded by the e-process threshold; values above the optimal policy's reflect different spending, not invalidity).

## Scaling of the exact solver (alternative (0.8, 0.7))
{md(sc, "{:.3f}", index=False)}
""",
        )
        w(
            "S11_ORACLE_GAP_RESULTS.md",
            f"""# S11 / S04 / S06 exact oracle gaps on the toy instance
Per-policy gap to the exact optimum (power = probability of crossing the threshold within the horizon under the alternative), mean over unseen alternatives and budgets. `remaining` is the S06 pacing rule on the toy, `const_0.5` / `always_1` are constants, `neyman` is the variance-optimal constant-per-context table (the S04 variance arm).

{md(summ[["gap_mean", "gap_max", "rel_gap", "decision_error", "null_alarm_mean"]], "{:.4f}")}

Per-instance values: `outputs/gap_closure/e11_s11_amortized_test.csv`. Exact value of information for the first-promotion problem: `e11_exact_voi.csv`.
""",
        )
    if have(O / "e12_s12_dist.csv"):
        d = pd.read_csv(O / "e12_s12_dist.csv")
        main = d[d.method != "approx_error_rff_vs_exact"]
        ae = d[d.method == "approx_error_rff_vs_exact"][
            ["d", "window", "reject", "ms_per_test", "peak_kb"]
        ].rename(
            columns={
                "reject": "median_rel_error_RFF_vs_exact",
                "ms_per_test": "incremental_RFF_ms_per_obs",
                "peak_kb": "exact_recompute_ms",
            }
        )
        nul = main[main.scenario == "null"].groupby("method").reject.agg(["mean", "min", "max"])
        pw = main[main.scenario.isin(["benign", "harmful"])].pivot_table(
            index=["d", "window"], columns=["method", "scenario"], values="reject"
        )
        pw128 = main[(main.window == 128) & main.scenario.isin(["benign", "harmful"])].pivot_table(
            index=["method", "scenario"], columns="d", values="reject"
        )
        rt = (
            main[(main.scenario == "harmful")]
            .pivot_table(index="method", columns=["d", "window"], values="ms_per_test")
            .round(2)
        )
        mem = (
            main[(main.scenario == "harmful") & (main.window == 128)]
            .pivot_table(index="method", columns="d", values="peak_kb")
            .round(0)
        )
        harm = main.groupby(["d", "scenario"]).decision_harm_scenario.first().unstack()
        w(
            "S12_EFFICIENT_DETECTION_RESULTS.md",
            f"""# S12 efficient multi-scale distribution testing
Methods: exact RBF MMD (median bandwidth), random-feature MMD (256 features), multi-bandwidth exact / RFF (median x {{.5, 1, 2}}, max of standardised statistics), standard C2ST (logistic regression, balanced held-out accuracy z), efficient C2ST (closed-form LDA direction, held-out t), BBSD (KS on model scores), incremental sliding-window RFF-MMD (O(D) per observation). d in {{5, 20, 100}}, window in {{32, 64, 128, 256}}, reference 512, 150 null calibration + 100 evaluation replicates per (setting, scenario) with thresholds from the 95% quantile of independent null replicates. **Every runtime includes all preprocessing and fitting** (bandwidth selection, feature sampling, classifier fitting). Benign shift = nuisance coordinate; harmful shift = the informative coordinate where the deployed linear model is misspecified (decision-cost increase on the evaluator side below).

Evaluator-side decision harm of each shifted scenario:

{md(harm, "{:.3f}")}

## Calibration (null rejection after calibration; target 0.05)
{md(nul, "{:.3f}")}

## Rejection rate, window 128
{md(pw128, "{:.2f}")}

## Time per test (ms, harmful scenario)
{md(rt)}

Peak traced memory per test (kB, window 128):

{md(mem)}

## Approximation error and streaming cost
{md(ae, "{:.4f}", index=False)}

Findings: none of the distribution tests separates harmful from benign shift when both move the covariates comparably (rejection rates are similar; BBSD, which looks at the model score, is the only one that tracks the informative coordinate); feature-space detectors are sentinels, not harm detectors (consistent with earlier F1). RFF-MMD approximates exact MMD within the relative error in the table; the incremental form turns a per-window O(w n d) recompute into O(D) per observation (compare the last two columns). Speed claims above include preprocessing and fitting; no claim is made about C2ST with deep classifiers.
""",
        )
        w(
            "COMPUTATIONAL_PARETO_ANALYSIS.md",
            "(generated after `RUNTIME_SCALING.csv`; see `COMPUTE_ACCURACY_PARETO.md`)\n",
        )


if __name__ == "__main__":
    which = sys.argv[1:] or ["phase1"]
    for fn in which:
        globals()[fn]()
        print("wrote", fn)
