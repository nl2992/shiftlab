"""Phase 9: configuration coverage matrix with parameter-hash and behavioural (per-seed outcome) deduplication."""

import glob
import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

O = Path("outputs/gap_closure")
D = Path("docs/sota_gap_closure")
rows = []

# ---- legacy registries (previous phase; unique algorithm + parameters without the calibrated threshold)
LEG = {
    "mmd": "unlabeled drift detector",
    "c2st": "unlabeled drift detector",
    "bbsd": "unlabeled drift detector",
    "cusum": "classical sequential",
    "page_hinkley": "classical sequential",
    "twowin": "classical sequential",
    "pr_cs": "confidence sequence",
    "watch": "conformal martingale",
    "pprm": "risk evidence (e-process)",
    "pp_cost": "risk evidence (e-process)",
    "pprm_tight": "risk evidence (e-process)",
    "pp_cost_tight": "risk evidence (e-process)",
    "sr_cost_tight": "temporal aggregation (multi-start)",
    "sr_brier_tight": "temporal aggregation (multi-start)",
    "fix_brier": "bet adaptation / gating / allocation",
    "fix_cost": "bet adaptation / gating / allocation",
}
seen = set()
for f in sorted(glob.glob("outputs/sota_search/registry_*.sqlite")):
    for a, h in sqlite3.connect(f).execute("select candidate_algorithm, hyperparameters from runs"):
        a = json.loads(a) if a else a
        hp = json.loads(h) if h else {}
        hp.pop("threshold", None)
        key = (a, json.dumps(hp, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        base = a.replace("CTRL_", "").split("_")[0] if a not in LEG else a
        fam = LEG.get(a) or LEG.get(
            {"DK": "fix_cost", "HG": "fix_brier", "BD": "fix_cost"}.get(base, ""),
            "bet adaptation / gating / allocation",
        )
        rows.append(
            {
                "source": "previous phase",
                "objective": "Q1",
                "family": fam,
                "algorithm": a,
                "params": key[1],
                "worlds_per_config": 19 if f.find("heldout") < 0 else 8,
                "seeds_per_world": 200 if f.find("heldout") < 0 else 400,
                "generator": "G1 (dev) / G1 held-out",
            }
        )

# ---- engine configurations (gap closure)
con = sqlite3.connect(O / "registry.sqlite")
reg = pd.read_sql(
    "select exp, config, cfg_hash, cfg_json, n_worlds, seeds_per_world from runs", con
)
beh = {}
for pq in sorted(O.glob("e*/perseed.parquet")):
    exp = pq.parent.name
    import pyarrow.parquet as pqt

    if "config" not in pqt.read_schema(pq).names:
        continue
    d = pd.read_parquet(pq, columns=["world", "config", "seed", "alarm_t", "labels"])
    for cfg, g in d.groupby("config"):
        g = g.sort_values(["world", "seed"])
        beh[(exp, cfg)] = hashlib.sha256(
            pd.util.hash_pandas_object(g[["alarm_t", "labels"]], index=False).values.tobytes()
        ).hexdigest()[:12]


def fam_of(c):
    out = []
    if c.get("rel"):
        out.append("reliability gating")
    if c.get("alloc", "uniform") != "uniform":
        out.append("label allocation")
    if c.get("pacing", "none") != "none" or c.get("budget") is not None:
        out.append("budget pacing")
    if c.get("gamma", 1.0) < 1 or c.get("gate_w"):
        out.append("bet adaptation / gating")
    if c.get("release") != "prefix" or c.get("cap_mode") != "sup":
        out.append("delay handling / validity repair")
    if c.get("lrv"):
        out.append("dependence-robust bet")
    return " + ".join(out) or (
        "risk evidence (cost)" if c.get("risk") == "cost" else "risk evidence (Brier)"
    )


for _, r in reg.drop_duplicates(["exp", "cfg_hash"]).iterrows():
    c = json.loads(r.cfg_json)
    rows.append(
        {
            "source": "gap closure",
            "objective": "Q1",
            "family": fam_of(c),
            "algorithm": r.config,
            "params": json.dumps(
                {k: v for k, v in c.items() if v not in (None, False)}, sort_keys=True
            ),
            "worlds_per_config": r.n_worlds,
            "seeds_per_world": r.seeds_per_world,
            "generator": r.exp,
            "exp": r.exp,
            "config_name": r.config,
            "behaviour_hash": beh.get((r.exp, r.config)),
        }
    )
# multi-window mixtures (run through run_mixture, not in the registry)
for exp, nm in (("e14_fixes_dev2", "F3_multiwindow"), ("e15_confirm", "mixture")):
    pass

# ---- Q2, Q3, S07, S11, S12
q2 = pd.read_parquet(
    O / "e7_q2/perseed.parquet", columns=["method", "frac", "delay", "K", "T"]
).drop_duplicates()
for _, r in q2.drop_duplicates(["method", "frac", "delay"]).iterrows():
    rows.append(
        {
            "source": "gap closure",
            "objective": "Q2",
            "family": "multiple-model certification",
            "algorithm": r.method,
            "params": json.dumps({"frac": r.frac, "delay": int(r.delay)}),
            "worlds_per_config": int((q2.method == r.method).sum()),
            "seeds_per_world": "100-300",
            "generator": "Q2 worlds",
            "exp": "e7_q2",
        }
    )
q3 = pd.read_parquet(O / "e8_q3/perseed.parquet", columns=["policy", "cost"]).drop_duplicates()
for pol in q3.policy.unique():
    costs = [c for c in q3[q3.policy == pol].cost if pol == "cert_gated"] or ["(cost-blind)"]
    for c in costs:
        rows.append(
            {
                "source": "gap closure",
                "objective": "Q3",
                "family": "switching / intervention policy",
                "algorithm": pol,
                "params": json.dumps({"cost_setting": c}),
                "worlds_per_config": 6,
                "seeds_per_world": 120,
                "generator": "Q3 scenarios",
                "exp": "e8_q3",
            }
        )
s07 = pd.read_csv(O / "e9_s07_pool.csv")
for _, r in s07.drop_duplicates(["method", "factor", "value"]).iterrows():
    rows.append(
        {
            "source": "gap closure",
            "objective": "S07",
            "family": "pool-based active inference",
            "algorithm": r.method,
            "params": json.dumps({r.factor: r.value}),
            "worlds_per_config": 1,
            "seeds_per_world": 150,
            "generator": "pool world",
            "exp": "e9_s07",
        }
    )
if (O / "e11_s11_amortized_test.csv").exists():
    for pol in pd.read_csv(O / "e11_s11_amortized_test.csv").policy.unique():
        rows.append(
            {
                "source": "gap closure",
                "objective": "S11",
                "family": "computational approximation (amortised policy)",
                "algorithm": pol,
                "params": "{}",
                "worlds_per_config": 15,
                "seeds_per_world": "exact",
                "generator": "RPOQ toy",
                "exp": "e11",
            }
        )
if (O / "e12_s12_dist.csv").exists():
    for m in pd.read_csv(O / "e12_s12_dist.csv").method.unique():
        rows.append(
            {
                "source": "gap closure",
                "objective": "S12",
                "family": "computational approximation (drift tests)",
                "algorithm": m,
                "params": "{}",
                "worlds_per_config": 12,
                "seeds_per_world": 100,
                "generator": "Gaussian two-sample",
                "exp": "e12",
            }
        )
cov = pd.DataFrame(rows)
cov["param_key"] = (
    cov.algorithm.astype(str)
    + "|"
    + cov.params.astype(str)
    + "|"
    + cov.get("exp", pd.Series("", index=cov.index)).fillna("").astype(str)
)
cov.to_csv(D / "CONFIGURATION_COVERAGE_MATRIX.csv", index=False)


# ---- report
def uniq(df):
    pk = df.drop_duplicates(["param_key"]).shape[0]
    bh = df.dropna(subset=["behaviour_hash"]) if "behaviour_hash" in df else df.iloc[0:0]
    return pk, bh.behaviour_hash.nunique() + (
        len(df) - len(bh.drop_duplicates("param_key")) if len(bh) else len(df)
    )


fam = (
    cov.groupby(["objective", "family"])
    .apply(
        lambda g: pd.Series(
            {
                "distinct_param_configs": g.param_key.nunique(),
                "source": ",".join(sorted(g.source.unique())),
            }
        ),
        include_groups=False,
    )
    .reset_index()
)
tot_prev = cov[cov.source == "previous phase"].param_key.nunique()
eng = cov[(cov.source == "gap closure") & (cov.objective == "Q1")]
# engine behavioural dedupe: identical (algorithm hash across experiments with equal behaviour) counted once per experiment
eng_beh = eng.dropna(subset=["behaviour_hash"]).groupby("exp").behaviour_hash.nunique().sum()
eng_param = (
    reg.cfg_hash.nunique()
)  # across experiments: the same Cfg in two experiments counts once
eng_param_per_exp = eng.groupby("exp").param_key.nunique().sum()
other = cov[(cov.source == "gap closure") & (cov.objective != "Q1")].param_key.nunique()
lines = ["| objective | family | distinct configurations | source |", "|---|---|---|---|"] + [
    f"| {r.objective} | {r.family} | {r.distinct_param_configs} | {r.source} |"
    for r in fam.itertuples()
]
txt = f"""# Search completion report (Phase 9)
Counting rule: a configuration = algorithm + all hyperparameters (calibrated thresholds excluded), deduplicated by hash. Seeds, worlds and repeated runs are never counted as configurations. For engine experiments a second, **behavioural** deduplication hashes each configuration's per-seed (alarm time, label count) vectors over all worlds of its experiment; identical hashes behave identically (e.g. `rel=hard, fallback=none` equals the parent; S05 `conservative` mixtures with u < .5 all collapse to u=.5).

| quantity | count |
|---|---|
| executed registry rows, previous phase (5,999 runs) -> distinct (algorithm, params) | **{tot_prev}** |
| engine configurations, this phase, distinct by parameters across all experiments | **{eng_param}** |
| ... counted per experiment (same configuration re-run in another experiment counted again) | {eng_param_per_exp} |
| ... behaviourally distinct within experiments (per-seed outcome hash) | {eng_beh} |
| non-engine configurations (Q2 methods x (fraction, delay), Q3 policies, S07 method x variation, S11 policies, S12 methods), distinct | **{other}** |
| **total distinct configurations across the programme (parameter hash)** | **{tot_prev + eng_param + other}** |

Target in the mandate: 500-1,500 distinct *compatible, scientifically meaningful* configurations. The parameter-hash total is {"within" if 500 <= tot_prev + eng_param + other <= 1500 else "outside"} that range; the behaviourally distinct engine count and the fact that many S03 / S05 / S07 cells vary one dial of a single method mean the count of *genuinely different algorithms* is far smaller (the principal algorithm families are the {fam.family.nunique()} listed below). No sweep was inflated with duplicate seeds; no successive-halving was needed (cells are cheap), and the full S03 grid (432 per parent) and the S06 delay-1 / fraction-.01 cells of v2 were not run.

## Coverage by objective and family (distinct configurations)
{chr(10).join(lines)}

## Not covered (declared)
* Risk-evidence types beyond Brier / decision cost (e.g. pinball, calibration-error evidence): not implemented.
* Temporal aggregation: discounting, SR multi-start (previous phase), multi-window mixture (F3); BOCPD, ADWIN-exact: not implemented.
* Budget pacing: dynamic-programming pacing at scale: not implemented (exact toy only).
* Multiple-model certification: published SeqMCS / CAMS: not available, source-inspired only.
Per-configuration results and failures: `outputs/gap_closure/*/perseed.parquet`, registry `outputs/gap_closure/registry.sqlite`; the previous phase's registries are untouched.
"""
(D / "SEARCH_COMPLETION_REPORT.md").write_text(txt)
print(txt[:1500])
