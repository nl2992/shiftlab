"""Analysis for P2_HARM_CONFIRMATION_REGISTRATION.md. Usage: p2_confirm_analyze.py <OUT> <DOC>
Per-cell rates as p2_controls_analyze.py; primary statistic: pooled certified-port harmful-promotion rate, BSWAP minus PERM,
with a split-cluster bootstrap stratified by dataset and paired across conditions (same splits)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

OUT, DOC = Path(sys.argv[1]), Path(sys.argv[2])
CONDS, BOUND, NB = ["ORIG", "PERM", "BSWAP", "ESWAP"], 0.0936, 4000
CERT = ["gated_deployment", "discern_style", "gated_adaptive_range", "gated_adaptive_range+front", "discern_design_floor",
        "SMCS+retain-incumbent", "choe_ramdas_eb", "choe_ramdas_eb+front", "gated_deployment+QCE", "gated_deployment+QCE+front"]
rng = np.random.default_rng(20261108)
rows, ep_tab = [], []
for c in CONDS:
    r = pd.read_json(OUT / f"run_{c}" / "records.jsonl", lines=True)
    for ds, g in r.groupby("regime"):
        z = np.load(OUT / c / f"{ds}.npz")
        adv = (z["l0"].astype(int) - z["l1"]).mean(1); split = z["split"]
        g = g.assign(split=split[g.ep.values], adv=adv[g.ep.values])
        g = g.assign(harmful=((g.ever_promote == 1) & (g.adv <= 0)).astype(float))
        sp = np.unique(split); name = ds.removeprefix("twin_")
        for pol, h in g.groupby("policy"):
            per = h.groupby("split")[["ever_promote", "harmful"]].mean().reindex(sp)
            bs = per.values[rng.integers(0, len(sp), (2000, len(sp)))].mean(1)
            rows.append(dict(cond=c, dataset=name, policy=pol, n=len(h), promote=float(h.ever_promote.mean()),
                             lo=float(np.quantile(bs[:, 0], .025)), hi=float(np.quantile(bs[:, 0], .975)),
                             harmful=float(h.harmful.mean()), harmful_lo=float(np.quantile(bs[:, 1], .025)),
                             harmful_hi=float(np.quantile(bs[:, 1], .975)), net=float(h.net.mean())))
        e = g[g.policy.isin(CERT)].groupby("ep").agg(H=("harmful", "mean"), P=("ever_promote", "mean"))
        e["split"] = split[e.index.values]; e["cond"] = c; e["dataset"] = name
        ep_tab.append(e.reset_index())
d = pd.DataFrame(rows); d.to_csv(DOC / "p2_confirm_rates.csv", index=False)
E = pd.concat(ep_tab)


def pooled(cond, col, idx=None):
    x = E[E.cond == cond]
    return float(x[col].mean())


def boot(stat):
    """Stratified split-cluster bootstrap: resample splits within each dataset; same draw for every condition."""
    dss = sorted(E.dataset.unique()); out = []
    sp = {ds: np.unique(E[E.dataset == ds].split) for ds in dss}
    for _ in range(NB):
        pick = {ds: rng.choice(sp[ds], len(sp[ds])) for ds in dss}
        parts = []
        for ds in dss:
            x = E[E.dataset == ds]
            cnt = pd.Series(pick[ds]).value_counts()
            w = x.split.map(cnt).fillna(0).to_numpy()
            parts.append(x.assign(w=w))
        out.append(stat(pd.concat(parts)))
    return np.array(out)


def wmean(x, cond, col):
    y = x[x.cond == cond]; return float(np.average(y[col], weights=y.w)) if y.w.sum() > 0 else np.nan


delta = lambda x: wmean(x, "BSWAP", "H") - wmean(x, "PERM", "H")
bd = boot(delta); bp = boot(lambda x: wmean(x, "PERM", "H")); bb = boot(lambda x: wmean(x, "BSWAP", "P"))
v = {"primary_pool": sorted(E.dataset.unique()), "episodes": {ds: int((E[(E.cond == "ORIG") & (E.dataset == ds)]).shape[0]) for ds in E.dataset.unique()},
     "H_BSWAP": pooled("BSWAP", "H"), "H_PERM": pooled("PERM", "H"), "H_ORIG": pooled("ORIG", "H"), "H_ESWAP": pooled("ESWAP", "H"),
     "P_BSWAP": pooled("BSWAP", "P"), "P_PERM": pooled("PERM", "P"), "P_ORIG": pooled("ORIG", "P"), "P_ESWAP": pooled("ESWAP", "P"),
     "HC1_delta": pooled("BSWAP", "H") - pooled("PERM", "H"), "HC1_delta_ci": [float(np.quantile(bd, .025)), float(np.quantile(bd, .975))],
     "HC2_H_PERM_upper": float(np.quantile(bp, .975)), "power_gate_P_BSWAP_ci": [float(np.quantile(bb, .025)), float(np.quantile(bb, .975))]}
v["HC1_pass"] = v["HC1_delta_ci"][0] > 0
v["HC2_pass"] = v["HC2_H_PERM_upper"] <= 0.005
v["underpowered"] = v["P_BSWAP"] < 0.02
v["HC3_per_dataset_delta"] = {ds: float(E[(E.cond == "BSWAP") & (E.dataset == ds)].H.mean() - E[(E.cond == "PERM") & (E.dataset == ds)].H.mean()) for ds in sorted(E.dataset.unique())}
v["HC3_pass"] = sum(x > 0 for x in v["HC3_per_dataset_delta"].values()) >= 2
broken = lambda x: (x.promote > BOUND) & (x.lo > 0.05)
for c in CONDS:
    x = d[(d.cond == c) & d.policy.isin(CERT)]
    v[c] = {"ports_breaking_on_some_dataset": sorted(x[broken(x)].policy.unique()), "ports_with_upper_ci_above_bound": sorted(x[x.hi > BOUND].policy.unique()),
            "max_promote": float(x.promote.max())}
v["S1_ESWAP_valid"] = len(v["ESWAP"]["ports_with_upper_ci_above_bound"]) == 0
v["S2_BSWAP_ge3_ports_break"] = len(v["BSWAP"]["ports_breaking_on_some_dataset"]) >= 3
v["CONFIRMED"] = bool(v["HC1_pass"] and v["HC2_pass"] and not v["underpowered"])
(DOC / "p2_confirm_verdicts.json").write_text(json.dumps(v, indent=1, default=float))
print(json.dumps(v, indent=1, default=float))
piv = d[d.policy.isin(CERT + ["xu_acquisition_only", "A5b", "model_picker_adapter", "cams_adapter"])].pivot_table(
    index=["policy", "dataset"], columns="cond", values=["promote", "harmful"]).round(3)
print(piv.to_string())
