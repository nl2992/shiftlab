"""Analysis for P2_CONTROLS_REGISTRATION.md: promotion and harmful-promotion rates per condition x dataset x policy,
95% CI by cluster bootstrap over splits (as the original analysis), plus the registered attribution verdicts."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

OUT = Path(sys.argv[1]); DOC = Path(sys.argv[2])
CONDS, BOUND = ["ORIG", "PERM", "BSWAP", "ESWAP"], 0.0936
CERT = ["gated_deployment", "discern_style", "gated_adaptive_range", "gated_adaptive_range+front", "discern_design_floor",
        "SMCS+retain-incumbent", "choe_ramdas_eb", "choe_ramdas_eb+front", "gated_deployment+QCE",
        "gated_deployment+QCE+front"]            # xu_acquisition_only reported but NOT counted as a published certified port
MOPE_AFFECTED = {"gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "gated_deployment+QCE",
                 "gated_deployment+QCE+front"}
rng = np.random.default_rng(0)
rows = []
for c in CONDS:
    r = pd.read_json(OUT / f"run_{c}" / "records.jsonl", lines=True)
    for ds, g in r.groupby("regime"):
        z = np.load(OUT / c / f"{ds}.npz")
        adv = (z["l0"].astype(int) - z["l1"]).mean(1)            # realised challenger advantage per episode
        split = z["split"]
        g = g.assign(split=split[g.ep.values], adv=adv[g.ep.values])
        g = g.assign(harmful=(g.ever_promote == 1) & (g.adv <= 0))
        sp = np.unique(split)
        for pol, h in g.groupby("policy"):
            per = h.groupby("split")[["ever_promote", "harmful"]].mean().reindex(sp)
            bs = per.values[rng.integers(0, len(sp), (2000, len(sp)))].mean(1)
            rows.append(dict(cond=c, dataset=ds.removeprefix("twin_"), policy=pol, n=len(h),
                             promote=float(h.ever_promote.mean()), lo=float(np.quantile(bs[:, 0], .025)),
                             hi=float(np.quantile(bs[:, 0], .975)), harmful=float(h.harmful.mean()),
                             harmful_hi=float(np.quantile(bs[:, 1], .975)), net=float(h.net.mean())))
d = pd.DataFrame(rows)
d.to_csv(DOC / "p2_controls_rates.csv", index=False)
broken = lambda x: (x.promote > BOUND) & (x.lo > 0.05)
v = {}
for c in CONDS:
    x = d[(d.cond == c) & d.policy.isin(CERT)]
    v[c] = {"ports_breaking_on_some_dataset": sorted(x[broken(x)].policy.unique().tolist()),
            "ports_with_upper_ci_above_bound": sorted(x[x.hi > BOUND].policy.unique().tolist()),
            "max_promote": float(x.promote.max())}
# registered ratio for HP2-a: PERM / ORIG promotion over ORIG-broken certified cells
o = d[(d.cond == "ORIG") & d.policy.isin(CERT)].set_index(["dataset", "policy"])
p = d[(d.cond == "PERM") & d.policy.isin(CERT)].set_index(["dataset", "policy"])
cells = o[broken(o)].index
v["HP2a_perm_over_orig_ratio_mean"] = float((p.loc[cells, "promote"] / o.loc[cells, "promote"]).mean()) if len(cells) else None
v["HP2a_cells"] = len(cells)
v["note_mope_affected_ports"] = sorted(MOPE_AFFECTED)
(DOC / "p2_controls_verdicts.json").write_text(json.dumps(v, indent=1))
print(json.dumps(v, indent=1))
piv = d[d.policy.isin(CERT + ["xu_acquisition_only", "A5b", "model_picker_adapter", "cams_adapter"])].pivot_table(
    index=["policy", "dataset"], columns="cond", values="promote").round(3)
print(piv[CONDS].to_string())
