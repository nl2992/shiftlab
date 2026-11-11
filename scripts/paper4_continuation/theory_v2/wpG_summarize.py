"""Print wpG grid tables: rho at fixed alpha and max over alpha <= 1/2, rows B, columns T-B."""
import json, sys
for path in sys.argv[1:]:
    d = json.load(open(path)); rows = d["rows"]
    e = rows[0]["e"]; Bs = sorted({r["B"] for r in rows}); dts = sorted({r["T"] - r["B"] for r in rows})
    for a in ("1/20", "1/4", "max"):
        print(f"\n== e={e}  alpha={a}: rho (rows B, cols T-B = {dts})")
        for B in Bs:
            cells = []
            for dT in dts:
                rs = [r for r in rows if r["B"] == B and r["T"] - r["B"] == dT and (a == "max" or r["alpha"] == a)]
                cells.append("  -  " if not rs else "%.3f" % max((r["rho"] or 0) for r in rs))
            print(f"B={B:2d} " + " ".join(cells))
