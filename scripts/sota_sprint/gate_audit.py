"""Mechanical audit of the sprint's mandatory execution gate (brief section 14A) from RAW records.

For each of the 24 candidates it checks, from saved records under ``outputs/sota_sprint/{A,B,C,D,X}``
(not from ledger prose): executed in the simulator; >= 4 diagnostic environments; paired seeds
(same seed set as a published comparator in the same run); >= 1 null environment; >= 1 environment
outside the intended advantage region; a mechanism ablation row (another policy whose name extends
the candidate's, or a registered ablation alias); cost/efficacy/safety metrics present; and a
manifest whose recorded source hash for the family module matches a committed revision.

    uv run python scripts/sota_sprint/gate_audit.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTS = ROOT / "outputs/sota_sprint"
IDS = [f"{f}{i}" for f in "ABCD" for i in range(1, 7)]
NULLS = {"F0_null", "F0_worse", "F5_dep_null_r8", "F5_dep_null_r95", "S_rare_null"}
# environments outside each family's intended advantage region (declared in the family briefs)
OUTSIDE = {
    "A": {"F1_late_800", "F1_late_1200", "F3_reversal_800", "F4_recurrent", "F2_transient"},
    "B": {"F0_better", "F9_bursty_better", "F7_near_better"},
    "C": {"F1_late_800", "F3_reversal_800", "F4_recurrent"},
    "D": {"F3_reversal_800", "F4_recurrent"},
}
# ablation aliases where an ablation is not named "<id>-..." (from the family ledgers)
ABLATION_ALIAS = {
    "B5": [
        "B5-reserve",
        "B5-rollback",
        "B5-deadline",
        "B5_no_reserve",
        "B5_no_rollback",
        "B5_no_deadline",
    ],
    "A5": ["A5-fixedgap6", "A1"],
    "A6": ["A6-noinflight", "A5"],
    "D6": ["D1", "D6-D1params:ms"],
    "D5": ["D5-standin_env8", "D2"],
    "D4": ["D4-no_reserve", "D4-r10", "D1"],
    "D2": ["D2-host_only"],
    "C5": ["C2", "C1"],
    "C6": ["C6@discern"],
    "C3": ["QSG", "QSG-r25"],
    "C4": ["discern_design_floor+pace_tuned"],
    "C1": ["C1-kappa1"],
    "B1": ["B1_r10", "B1_r15", "B1_r25"],
    # single-mechanism candidates: the host without the mechanism is the ablation
    "A4": ["QSG", "A1"],
    "B2": ["B0_host"],
    "B3": ["B0_host"],
    "B4": ["B0_host"],
    "B6": ["B5"],
}
PUBLISHED = {
    "xu_acquisition_only",
    "gated_adaptive_range",
    "gated_adaptive_range+front",
    "discern_style",
    "discern_design_floor",
    "SMCS+retain-incumbent",
    "model_picker_adapter",
    "cams_adapter",
    "model_selector_causal",
}


def _blob_hashes(name: str) -> set[str]:
    """sha256[:16] of every committed revision of scripts/sota_sprint/<name>."""
    revs = subprocess.run(
        ["git", "log", "--format=%H", "--", f"scripts/sota_sprint/{name}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    ).stdout.split()
    out = set()
    for r in revs:
        b = subprocess.run(
            ["git", "show", f"{r}:scripts/sota_sprint/{name}"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).stdout
        if b:
            out.add(hashlib.sha256(b).hexdigest()[:16])
    return out


def main(roots=None):
    """``roots``: {family letter: [run dirs]}; default = every run under outputs/sota_sprint/<F>/.
    Records are keyed by FAMILY as well as policy name, so a candidate is credited only with runs
    from its own family's directories (ARIS milestone-1 audit: names are reused across families)."""
    regs = defaultdict(set)
    seeds = defaultdict(lambda: defaultdict(set))
    runs = defaultdict(set)
    metric_ok = defaultdict(bool)
    roots = roots or {f: [OUTS / f] for f in "ABCD"}
    for fam, dirs in roots.items():
        for rec in (x for d in dirs for x in Path(d).rglob("records.jsonl")):
            run = rec.parent
            with open(rec) as f:
                for line in f:
                    r = json.loads(line)
                    p = (fam, r["policy"])
                    regs[p].add(r["regime"])
                    seeds[(run, r["regime"])][p].add((r["ep"], r["seed"]))
                    runs[p].add(run)
                    metric_ok[p] = metric_ok[p] or all(
                        k in r
                        for k in (
                            "net",
                            "loss",
                            "labels",
                            "switches",
                            "ever_promote",
                            "regret_expected_oracle",
                        )
                    )
    hashes = {n: _blob_hashes(n) for n in ("fam_a.py", "fam_b.py", "fam_c.py", "fam_d.py")}
    report = {}
    for cid in IDS:
        fam = cid[0]
        mine = {p[1] for p in regs if p[0] == fam}
        alias = {"B1": ["B1_r15", "B1_r10", "B1_r25"], "D6": ["D6:mp", "D6:cams", "D6:ms"]}
        names = [n for n in [cid] + alias.get(cid, []) if n in mine]
        main_name = (fam, names[0]) if names else None
        ok = {}
        if main_name is None:
            report[cid] = {"executed": False}
            continue
        rs = regs[main_name]
        ok["executed"] = True
        ok["n_envs"] = len(rs)
        ok["envs_ge4"] = len(rs) >= 4
        ok["null_env"] = bool(rs & NULLS)
        ok["outside_env"] = bool(rs & OUTSIDE[fam])
        abl = [
            n
            for n in mine
            if n != main_name[1]
            and (n.startswith((cid + "-", cid + "_")) or n in ABLATION_ALIAS.get(cid, []))
        ]
        ok["ablation_rows"] = sorted(abl)[:6]
        ok["ablation"] = bool(abl)
        paired = False
        for (run, reg), d in seeds.items():
            if main_name in d and any(
                (fam, c) in d and d[(fam, c)] == d[main_name] for c in PUBLISHED
            ):
                paired = True
                break
        ok["paired_with_published"] = paired
        ok["metrics"] = metric_ok[main_name]
        mf_ok = []
        for run in runs[main_name]:
            m = run / "manifest.json"
            if m.exists():
                srcd = json.loads(m.read_text()).get("sources", {})
                src = srcd.get(f"fam_{fam.lower()}.py") or srcd.get(
                    f"scripts/sota_sprint/fam_{fam.lower()}.py"
                )
                mf_ok.append(src in hashes[f"fam_{fam.lower()}.py"] if src else None)
        ok["manifest_hash_committed"] = any(mf_ok)
        ok["runs"] = sorted(str(r.relative_to(ROOT)) for r in runs[main_name])
        ok["PASS"] = all(
            ok[k]
            for k in (
                "executed",
                "envs_ge4",
                "null_env",
                "outside_env",
                "ablation",
                "paired_with_published",
                "metrics",
                "manifest_hash_committed",
            )
        )
        report[cid] = ok
    out = ROOT / "docs/sota_sprint/gate_audit.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    for cid, ok in report.items():
        miss = [
            k
            for k in (
                "executed",
                "envs_ge4",
                "null_env",
                "outside_env",
                "ablation",
                "paired_with_published",
                "metrics",
                "manifest_hash_committed",
            )
            if not ok.get(k)
        ]
        print(
            f"{cid}: {'PASS' if ok.get('PASS') else 'FAIL'} envs={ok.get('n_envs')} "
            f"missing={miss} abl={ok.get('ablation_rows', [])[:3]}"
        )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root", default="", help="dir with A/ B/ C/ D/ subdirs (e.g. the gate re-screen)"
    )
    a = ap.parse_args()
    main({f: [(ROOT / a.root / f).resolve()] for f in "ABCD"} if a.root else None)
