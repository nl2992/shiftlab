"""Write 02_DATASET_INVENTORY.csv (metadata only: shapes, recorded build metadata; no loss statistic)."""

import csv
import json
from pathlib import Path

import numpy as np

from shiftlab.paper3.transfer import streams as S

BUILDS = Path(
    "C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/qsg_methods_search/c4_builds"
)
SAES = {  # recorded in docs/qsg_methods_search/real_data_inventory.md and data/sprint_fresh_losses/README.md
    "airlines": (
        "https://www.openml.org/d/1169",
        "n/a (OpenML 1169, ordered rows)",
        "binary flight delay",
        "domain: aviation",
    ),
    "bank": (
        "https://archive.ics.uci.edu/dataset/222",
        "2008-2010 (UCI 222)",
        "binary term-deposit subscription",
        "",
    ),
    "beijing_pm25": (
        "https://archive.ics.uci.edu/static/public/381/beijing+pm2+5+data.zip",
        "2010-2014",
        "PM2.5 threshold",
        "",
    ),
    "bike_hour": (
        "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip",
        "2011-2012",
        "demand threshold",
        "",
    ),
    "appliances": (
        "https://archive.ics.uci.edu/static/public/374/appliances+energy+prediction.zip",
        "2016-01 to 2016-05",
        "energy threshold",
        "",
    ),
    "household_power": (
        "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip",
        "2006-2010",
        "power threshold",
        "",
    ),
    "metro": (
        "https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip",
        "2012-10 to 2018-09",
        "median-threshold traffic",
        "",
    ),
    "elec2": (
        "https://www.openml.org/search?q=electricity-normalized",
        "1996-1998 (NSW price)",
        "price direction",
        "chronology untrusted per prior audit",
    ),
    "rialto": ("recorded as Losing mirror, no declared licence", "n/a", "1-vs-9 image task", ""),
    "spam": ("recorded as Katakis spam stream, no declared licence", "n/a", "binary spam", ""),
    "weather": (
        "recorded as Elwell-Polikar Offutt AFB, no declared licence",
        "n/a",
        "daily rain",
        "",
    ),
}
rows = []
for n, (d, fam) in sorted(S.REGISTRY.items()):
    z = np.load(S.path_of(n), allow_pickle=False)
    K, T = z["l0"].shape
    delay = int(z["delay"])
    sealed = fam in S.SEALED_FAMILIES
    url = period = nev = task = ""
    if d == "c4_sealed":
        j = json.load(open(BUILDS / f"{n}.json"))  # noqa: SIM115
        m = j["meta"]
        url, period, task = m["url"], "-".join(m["window"]).replace("T00:00:00", ""), m["task"]
        nev = j["n"]
    else:
        url, period, task, _ = SAES[n]
        nev = K * T
    if sealed:
        elig = "SEALED_FINAL_TEST_NOT_OPENED"
    elif K < S.MIN_EPISODES:
        elig = f"ineligible: {K} episodes < {S.MIN_EPISODES}"
    else:
        elig = f"dev (fold={fam})"
    rows.append(
        {
            "name": n,
            "domain_family": fam,
            "fold": S.SEALED_GROUP_NAME if sealed else fam,
            "source_dir": f"data/{d}",
            "source_url": url,
            "period": period,
            "task": task,
            "n_events_in_cache": nev,
            "episodes": K,
            "episode_len": T,
            "label_delay_semantics": f"constant {delay} events; label of event t released at t+{delay} (simulated clock, not an authentic release timestamp)",
            "exposure": "EXPOSED_PAPERS_1_2"
            + ("; sealed in Paper 3 D" if sealed else "; exploratory in Paper 3 D"),
            "eligibility": elig,
        }
    )
for fam in ["S1_static", "S2_markov_regime", "S3_ar_drift", "S4_ramp", "S5_sticky_outcomes"]:
    rows.append(
        {
            "name": f"{fam}_0..5",
            "domain_family": fam,
            "fold": fam,
            "source_dir": "synthetic (src/shiftlab/paper3/transfer/synth.py)",
            "source_url": "",
            "period": "",
            "task": "synthetic paired disagreement outcomes",
            "n_events_in_cache": 6 * 40 * 2000,
            "episodes": "6 streams x 40",
            "episode_len": 2000,
            "label_delay_semantics": "constant delay in {24,50,100,144}",
            "exposure": "synthetic; training augmentation + synthetic folds",
            "eligibility": "dev synthetic",
        }
    )
rows.append(
    {
        "name": "sprint_fresh_losses/{appliances,beijing_pm25,bike_hour,household_power,metro}",
        "domain_family": "uci_sensor",
        "fold": "(duplicate)",
        "source_dir": "data/sprint_fresh_losses",
        "source_url": "",
        "period": "",
        "task": "",
        "n_events_in_cache": "",
        "episodes": "",
        "episode_len": "",
        "label_delay_semantics": "",
        "exposure": "EXPOSED",
        "eligibility": "duplicate of data/saes_dev arrays (identical loss/disagreement statistics); not used twice",
    }
)
out = Path("papers/paper3_cost_aware_adaptation/2026_programme/02_DATASET_INVENTORY.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows ->", out)
