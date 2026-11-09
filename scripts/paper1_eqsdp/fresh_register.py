"""Write docs/paper1_eqsdp/fresh_registration.json from the fresh build records (doc 19 section 2)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "docs/paper1_eqsdp/fresh_builds"
NAMES = ["sf_311", "dallas_311", "kc_311", "austin_311", "cincinnati_311", "oakland_311",
         "dc_311", "sandiego_311"]  # fmt: skip


def main():
    ds = []
    for n in NAMES:
        r = json.loads((B / f"{n}.json").read_text(encoding="utf-8"))
        e = {"eligible": r["eligible"], "gates": r["gates"], "validation": r["validation"],
             "n_after_filter": r["n_after_filter"], "subsample": r["subsample"]}  # fmt: skip
        d = {"name": n, "org": r["meta"]["publisher"], "window": r["meta"]["window"],
             "episodes": r["episodes"], "delay": r["meta"]["delay"], "built_utc": r["built_utc"],
             "eligibility": e}  # fmt: skip
        if r["eligible"]:
            d["sealed_path"] = r["sealed"]["path"]
            d["array_content_sha256"] = r["sealed"]["array_content_sha256"]
        ds.append(d)
    reg = {"registered": "2026-11-09", "batch": "fresh",
           "protocol": "docs/paper1_eqsdp/19_FRESH_CONFIRMATION_PROTOCOL.md",
           "contract": {"budget": 200, "cq": 0.05, "cs": 5.0, "T_episode": 2000},
           "policy_seeds": 10, "seed_base": 2026111901,
           "excluded_in_advance": {"montgomery_traffic": "no later period exists (doc 19 section 2)"},
           "datasets": ds}  # fmt: skip
    out = ROOT / "docs/paper1_eqsdp/fresh_registration.json"
    out.write_text(json.dumps(reg, indent=1) + "\n", encoding="utf-8")
    print([(d["name"], d["episodes"], d["eligibility"]["eligible"]) for d in ds])


if __name__ == "__main__":
    main()
