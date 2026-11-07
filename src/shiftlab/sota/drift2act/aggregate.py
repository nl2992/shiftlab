"""Aggregate shard JSONs -> markdown table (mean +- s.e. over episodes)."""

import collections
import glob
import json
import sys

import numpy as np

KEYS = ["C_tot", "C_act", "C_label", "V", "T_det", "T_rec_post_harm", "minAccwg"]


def load(d):
    rows = []
    for f in sorted(glob.glob(d + "/shard*.json")):
        with open(f, encoding="utf8") as fh:
            rows += json.load(fh)["rows"]
    return rows


def table(rows, by=None):
    g = collections.defaultdict(list)
    for r in rows:
        g[(r["method"],) if by is None else (r["method"], r[by])].append(r)
    lines = [
        "| method | " + ("group | " if by else "") + "n | " + " | ".join(KEYS) + " |",
        "|" + "---|" * (len(KEYS) + 2 + bool(by)),
    ]
    for k, rs in g.items():
        cells = []
        for key in KEYS:
            x = np.array([r[key] for r in rs], float)
            x = x[~np.isnan(x)]
            cells.append(
                f"{x.mean():.2f} ± {x.std(ddof=1) / np.sqrt(len(x)):.2f}" if len(x) > 1 else "nan"
            )
        lines.append(
            "| " + " | ".join([k[0]] + ([str(k[1])] if by else []) + [str(len(rs))] + cells) + " |"
        )
    return "\n".join(lines)


def paired(rows, base="alarm_only", keys=("V", "C_tot", "T_rec_post_harm", "minAccwg")):
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["method"]][r["seed"]] = r
    out = [
        "| method vs " + base + " | " + " | ".join("d" + k for k in keys) + " |",
        "|" + "---|" * (len(keys) + 1),
    ]
    for m, d in by.items():
        if m == base:
            continue
        cells = []
        for k in keys:
            x = np.array([d[s][k] - by[base][s][k] for s in d if s in by[base]], float)
            x = x[~np.isnan(x)]
            cells.append(f"{x.mean():+.2f} ± {x.std(ddof=1) / np.sqrt(len(x)):.2f}")
        out.append("| " + m + " | " + " | ".join(cells) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    rows = load(sys.argv[1])
    print(f"episodes={len({r['seed'] for r in rows})}\n")
    print(table(rows))
    print()
    print(paired(rows))
    print()
    print(
        table(
            [r for r in rows if r["method"] in ("ctrl_cert", "ctrl_no_cert", "alarm_only")], "drift"
        )
    )
