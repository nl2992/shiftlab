"""Protocol 07a section 3: descriptive dev evaluation of the core arms on the 12 new-source DEV windows."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "outputs/paper1_scale25/c1/dev"
NAMES = {"P2_K2__E48_F60": "v1", "s2wald_l0.98_g0.3_H1100": "Wcut", "s2armr_H1100": "EQcut",
         "P4W__P2_K2__E48_F60": "Wpair", "EQSDp_l0.98_g0.3": "armR"}  # fmt: skip
man = json.loads((ROOT / "outputs/paper1_scale25/c1/dev_manifest.json").read_text())
rows = []
for d in man["datasets"]:
    x = pd.read_json(D / d["name"] / "records.jsonl", lines=True, dtype={"config_id": str})
    x = x.drop_duplicates(["ep", "seed", "config_id"])
    assert x.groupby("config_id").size().eq(d["episodes"] * 10).all(), d["name"]
    m = x.groupby(["ep", "config_id"]).net.mean().unstack() / 2000 * 100
    J = m.mean().rename(NAMES)
    r = {
        "dataset": d["name"],
        "episodes": d["episodes"],
        **{f"J_{k}": J[k] for k in NAMES.values()},
    }
    r["r_v1_vs_Wcut_pct"] = 100 * (J["Wcut"] - J["v1"]) / J["Wcut"]
    rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(ROOT / "docs/paper1_scale25/c1_dev_eval.csv", index=False, float_format="%.4f")
print(df.round(3).to_string())
r = df.r_v1_vs_Wcut_pct
print("mean r", r.mean(), "neg/pos/zero", (r < 0).sum(), (r > 0).sum(), (r == 0).sum())
