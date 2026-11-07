"""Print a compact net-cost matrix (gap to row minimum) and promotion rates from a summary JSON."""
import json
import sys

S = json.load(open(sys.argv[1]))
cols = sys.argv[2].split(",")
w = max(6, max(len(c) for c in cols) // 2)
print(f"{'source':20s}" + "".join(f"{c[:11]:>12s}" for c in cols) + "    min")
for src, e in S.items():
    P = e["policies"]
    b = min(P[c]["net"] for c in cols if c in P)
    print(f"{src:20s}" + "".join(f"{P[c]['net'] - b:12.1f}" if c in P else f"{'-':>12s}" for c in cols)
          + f"  {b:7.1f}")
print("\never-promote rate")
for src, e in S.items():
    P = e["policies"]
    print(f"{src:20s}" + "".join(f"{P[c]['ever_promote']:12.2f}" if c in P else f"{'-':>12s}" for c in cols))
