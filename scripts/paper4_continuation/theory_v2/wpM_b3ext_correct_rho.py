"""Correct the B=3 extension ratio enclosure using its recorded Gamma width."""
from __future__ import annotations

import hashlib
import json
import math
import os
from fractions import Fraction as F

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SOURCE = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_b3ext_v1.json")
OUT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_b3ext_rho_corrected_v1.json")


def down(value: float) -> F:
    return F.from_float(math.nextafter(value, -math.inf))


def up(value: float) -> F:
    return F.from_float(math.nextafter(value, math.inf))


def main():
    if os.path.exists(OUT):
        raise SystemExit(f"refusing to overwrite {OUT}")
    payload = json.load(open(SOURCE))
    rows = []
    for row in payload["cells"]:
        glo, ghi = down(row["Gamma"][0]), up(row["Gamma"][1])
        voi_lo = down(row["VOI"])
        voi_base_hi = up(row["VOI"])
        width = ghi - glo
        voi_hi = voi_base_hi + width
        assert glo > 0 and 0 < voi_lo < voi_hi
        rho_lo, rho_hi = glo / voi_hi, ghi / voi_lo
        rows.append(dict(
            t=row["t"], T=row["T"], B=row["B"], d=row["d"], alpha=row["alpha"],
            Gamma_outward=[str(glo), str(ghi)],
            VOI_outward=[str(voi_lo), str(voi_hi)],
            rho_exact=[str(rho_lo), str(rho_hi)],
            rho_float=[math.nextafter(float(rho_lo), -math.inf),
                       math.nextafter(float(rho_hi), math.inf)],
            source=row["source"],
        ))
    out = dict(
        input="docs/paper4_continuation/theory_v2/results/wpM_b3ext_v1.json",
        input_sha256=hashlib.sha256(open(SOURCE, "rb").read()).hexdigest(),
        script_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
        method=("Gamma endpoints and VOI lower endpoint are widened by one float ULP. "
                "Gamma_hi-Gamma_lo upper-bounds the IID value interval width, so "
                "VOI_upper <= VOI_lower_float_upper + Gamma_width_upper."),
        cells=rows,
    )
    with open(OUT, "x") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
