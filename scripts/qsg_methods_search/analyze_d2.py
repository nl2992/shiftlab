"""D2 analysis: family mean net cost, change/guard splits, paired CIs."""

import sys

import numpy as np
import pandas as pd
from scipy import stats

CHANGE = [
    "F1_late_400",
    "F1_late_800",
    "F1_late_1200",
    "F2_transient",
    "F3_reversal_800",
    "F3_reversal_1200",
    "F4_recurrent",
    "V_late_600",
    "V_reversal_1000",
    "V_recurrent",
]
GUARD = ["F0_better", "F0_null", "V_worse", "V_null"]


def seedmean(d, regs):
    return d[d.regime.isin(regs)].pivot_table(
        index="seed", columns="policy", values="net", aggfunc="mean"
    )


def ci(x):
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    h = stats.t.ppf(0.975, len(x) - 1) * se
    return f"{m:+.2f} [{m - h:+.2f},{m + h:+.2f}]"


if __name__ == "__main__":
    d = pd.read_json(sys.argv[1], lines=True)
    fam, ch, gu = seedmean(d, CHANGE + GUARD), seedmean(d, CHANGE), seedmean(d, GUARD)
    out = pd.DataFrame({"family": fam.mean(), "change": ch.mean(), "guard": gu.mean()})
    out["null_prom"] = (
        d[d.regime.isin(["F0_null", "V_null", "V_worse"])].groupby("policy").ever_promote.mean()
    )
    out["sw_null"] = d[d.regime.isin(["F0_null", "V_null"])].groupby("policy").switches.mean()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 300)
    print(out.sort_values("family").round(2).to_string())
    for a, b in [x.split(":") for x in sys.argv[2:]]:
        print(
            f"{a} - {b}: family {ci(fam[a] - fam[b])}  change {ci(ch[a] - ch[b])}  guard {ci(gu[a] - gu[b])}"
        )
    pv = d.pivot_table(index="policy", columns="regime", values="net", aggfunc="mean").round(1)
    keep = out.sort_values("family").index[:6].tolist() + [
        "gong_zhang_paid_obs",
        "qiu_delayed_movement",
        "econF_mo5_m5",
        "CONTROL_never_switch",
    ]
    print(pv.loc[list(dict.fromkeys(keep)), CHANGE + GUARD].to_string())
