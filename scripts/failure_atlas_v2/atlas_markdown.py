"""Render markdown tables (net-cost gap to row best, promotion rate, regret, labels) from a summary."""

import json
import sys

with open(sys.argv[1]) as source:
    S = json.load(source)
cols = sys.argv[2].split(",")
short = dict(x.split("=") for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else {}
hdr = "| source | " + " | ".join(short.get(c, c) for c in cols) + " | row best (net) |"
sep = "|---|" + "---:|" * (len(cols) + 1)


def block(title, fn):
    print(f"\n**{title}**\n\n{hdr}\n{sep}")
    for src, e in S.items():
        P = e["policies"]
        print(
            f"| {src} | "
            + " | ".join(fn(P, c) if c in P else "-" for c in cols)
            + f" | {min(P[c]['net'] for c in cols if c in P):.1f} |"
        )


block(
    "Net cost minus row best (mean over seeds/replays)",
    lambda P, c: f"{P[c]['net'] - min(P[k]['net'] for k in cols if k in P):.1f}",
)
block("Ever promoted challenger (fraction)", lambda P, c: f"{P[c]['ever_promote']:.2f}")
block(
    "Regret vs expected-oracle path (evaluator-only diagnostic)",
    lambda P, c: f"{P[c]['regret_expected_oracle']:.1f}",
)
block("Labels used / switches", lambda P, c: f"{P[c]['labels']:.0f}/{P[c]['switches']:.1f}")
block(
    "Median first promotion time",
    lambda P, c: (
        "-" if P[c]["median_first_deploy"] is None else f"{P[c]['median_first_deploy']:.0f}"
    ),
)
