"""Recompute Atlas Amendment-6 point criteria from archived null-twin counts."""

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATED = (
    "episode_geo",
    "episode_equal",
    "episode_front",
    "allonset_edetector",
    "c2_rho0.75",
    "c1_hmm_cs",
    "online_fwer_spending",
)


def pool(twins):
    n = sum(t["n"] for t in twins)
    return {
        m: {"k": sum(t["k"][m] for t in twins), "n": n, "rate": sum(t["k"][m] for t in twins) / n}
        for m in GATED
    }


def main():
    result = {}
    for family in ("family3", "family4"):
        folder = ROOT.parent / "shift-research-starter/outputs/failure_atlas_v1_cycle5" / family
        state = json.loads((folder / "state.json").read_text(encoding="utf-8"))
        archive = [
            json.loads(x)
            for x in (folder / "archive.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        archived = {r["payload"]["twin"]: r["payload"] for r in archive if r["kind"] == "nullbase"}
        twins = state["nullbase"]["twins"]
        if set(archived) != set(twins) or any(
            any(twins[key].get(field) != value for field, value in archived[key].items())
            for key in archived
        ):
            raise ValueError("archive/state null count mismatch")
        report = {
            "twins": len(twins),
            "state_sha256": hashlib.sha256((folder / "state.json").read_bytes()).hexdigest(),
            "archive_sha256": hashlib.sha256((folder / "archive.jsonl").read_bytes()).hexdigest(),
            "archive_state_agree": True,
            "reported_seeds": state["nullbase"]["seeds"],
        }
        values = list(twins.values())
        if family == "family3":
            rates = {
                str(rho): pool([t for t in values if t["rho"] == rho]) for rho in (0.0, 0.5, 0.8)
            }
            best = max(GATED, key=lambda m: rates["0.8"][m]["rate"])
            monotone = {
                m: all(
                    a <= b
                    for a, b in itertools.pairwise(
                        rates[str(r)][m]["rate"] for r in (0.0, 0.5, 0.8)
                    )
                )
                for m in GATED
            }
            report.update(
                rates=rates,
                D1=bool(rates["0.8"][best]["rate"] > 0.15),
                D1_highest={"method": best, **rates["0.8"][best]},
                D2=all(monotone.values()),
                monotone_methods=monotone,
            )
        else:
            u = pool([t for t in values if t["delays"][1] == 3 * t["delays"][0] and t["d"] == 10])
            f = pool([t for t in values if t["delays"][0] == 3 * t["delays"][1]])
            report.update(
                I1=any(v["rate"] > 0.15 for v in u.values()),
                I1_rates=u,
                I2=all(v["rate"] <= 0.1 for v in f.values()),
                I2_rates=f,
            )
        result[family] = report
    result["scope"] = (
        "Historical aggregate count reproduction, matching archive/state. Point thresholds only; no raw null streams replayed, no dependence-robust coverage proved. Family3 is declared marginal-null misspecification, not conditional-null theorem refutation."
    )
    (ROOT / "docs/retrospective_audit_2026_11_01/ATLAS_FAMILY34_COUNTS.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "D1": result["family3"]["D1"],
                "D1_highest": result["family3"]["D1_highest"],
                "D2": result["family3"]["D2"],
                "monotone_count": sum(result["family3"]["monotone_methods"].values()),
                "I1": result["family4"]["I1"],
                "I2": result["family4"]["I2"],
            }
        )
    )


if __name__ == "__main__":
    main()
