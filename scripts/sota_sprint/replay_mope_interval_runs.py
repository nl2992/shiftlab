#!/usr/bin/env python3
"""Replay runs that consume MOPE's two-sided CS after interval-intersection correction."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "_mopeinterval_20261106"


def affected(policy: str) -> bool:
    p = str(policy)
    gated_c = {"C1-uniformbase", "C2-noadapt", "C2-floorskip", "C6-no_deadline",
               "C6-no_shadow", "C6-no_two_stage"}
    return (
        "gated_deployment" in p or "gated_adaptive_range" in p
        or p.startswith(("rmm:gated", "M_RMMSUI_gar", "T2:gated"))
        or (p.startswith("T6:") and ("xC2" in p or "xC6" in p))
        or p in {"B0_host", "C1", "C2", "C5", "C6", "Cchk:gated_uniform", "Cchk:gated_front", *gated_c}
        or p.startswith(("C1-k", "C2-g", "C6-f"))
    )


def replace_option(args: list[str], option: str, value: str) -> list[str]:
    out = list(args)
    try:
        i = out.index(option)
    except ValueError:
        out += [option, value]
    else:
        out[i + 1] = value
    return out


def available_output(out: Path, cmd: list[str]) -> tuple[Path, list[str]] | None:
    if not out.exists():
        return out, cmd
    if (out / "manifest.json").is_file():
        return None
    n = 1
    while out.with_name(out.name + f"_retry{n}").exists():
        n += 1
    retry = out.with_name(out.name + f"_retry{n}")
    return retry, replace_option(cmd, "--out", str(retry))


def command(manifest_path: Path, workers: int):
    manifest = json.loads(manifest_path.read_text())
    argv = manifest.get("argv")
    if isinstance(argv, dict):
        raw = argv.get("policies", manifest.get("policies", []))
        policies = raw if isinstance(raw, list) else str(raw).split(",")
        policies = [str(p) for p in policies if affected(str(p))]
        if not policies:
            return None
        old_out = Path(argv.get("out", manifest_path.parent))
        new_out = old_out.with_name(old_out.name + TAG)
        if "kind" in argv and "regimes" in argv:
            runner = "scripts/sota_sprint/screen.py"
            cmd = ["uv", "run", "python", runner, "--kind", str(argv["kind"]),
                   "--regimes", str(argv["regimes"]), "--policies", ",".join(policies),
                   "--seeds", str(argv.get("seeds", 20)), "--seed-base", str(argv.get("seed_base", 0)),
                   "--workers", str(workers), "--out", str(new_out)]
            if "alpha" in argv:
                cmd += ["--alpha", str(argv["alpha"])]
            return cmd, new_out, policies
        if "sources" in argv:
            runner = "scripts/sota_sprint/wp2_run.py"
            cmd = ["uv", "run", "python", runner, "--sources", str(argv["sources"]),
                   "--policies", ",".join(policies), "--seeds", str(argv.get("seeds", 20)),
                   "--seed-base", str(argv["seed_base"]), "--workers", str(workers),
                   "--alpha", str(argv.get("alpha", 0.05)), "--delay-mult", str(argv.get("delay_mult", 1.0)),
                   "--out", str(new_out)]
            if argv.get("episodes"):
                cmd += ["--episodes", str(argv["episodes"])]
            return cmd, new_out, policies
        return None

    if isinstance(argv, list) and argv:
        old_out = Path(manifest.get("out", argv[argv.index("--out") + 1]))
        try:
            i = argv.index("--policies") + 1
            policies = [p for p in argv[i].split(",") if affected(p)]
        except (ValueError, IndexError):
            return None
        if not policies:
            return None
        new_out = old_out.with_name(old_out.name + TAG)
        cmd = replace_option(argv, "--policies", ",".join(policies))
        cmd = replace_option(cmd, "--out", str(new_out))
        cmd = replace_option(cmd, "--workers", str(workers))
        if "--seed-base" not in cmd and manifest.get("seed_base") is not None:
            cmd += ["--seed-base", str(manifest["seed_base"])]
        return ["uv", "run", "python", *cmd], new_out, policies
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("outputs"))
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    manifests = [a.run_dir / "manifest.json"] if a.run_dir else sorted(a.root.rglob("manifest.json"))
    tasks = []
    skip_tags = ("_wmaxfix_20261105", TAG)
    for f in manifests:
        if any(tag in str(f) for tag in skip_tags) or not f.is_file():
            continue
        try:
            task = command(f, a.workers)
        except (OSError, json.JSONDecodeError, ValueError, IndexError):
            continue
        if task:
            cmd, out, policies = task
            av = available_output(out, cmd)
            if av is not None:
                out, cmd = av
                tasks.append((f, cmd, out, policies))
    # A recovered Family-H source directory has no manifest; its command is recorded in the
    # replay audit and the adaptive-range correction schedule.
    orphan = ROOT / "outputs/sprint2/H/screen1"
    if (not a.run_dir or a.run_dir == Path("outputs/sprint2/H/screen1")) and (orphan / "records.jsonl").exists():
        out = orphan.with_name(orphan.name + TAG)
        cmd = ["uv", "run", "python", "scripts/sota_sprint/screen.py", "--kind", "synthetic",
               "--regimes", "F0_better,F7_near_better", "--policies", "gated_adaptive_range+front",
               "--seeds", "20", "--seed-base", "2026110701", "--workers", str(a.workers), "--out", str(out)]
        av = available_output(out, cmd)
        if av is not None:
            out, cmd = av
            tasks.append((orphan / "records.jsonl", cmd, out, ["gated_adaptive_range+front"]))
    if a.limit:
        tasks = tasks[:a.limit]
    print(f"scheduled {len(tasks)} MOPE interval-correction runs")
    for i, (source, cmd, out, policies) in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] source={source.parent} output={out} policies={','.join(policies)}")
        if a.execute:
            result = subprocess.run(cmd, cwd=ROOT, check=False)
            if result.returncode:
                raise SystemExit(f"replay failed ({result.returncode}): {source}")


if __name__ == "__main__":
    main()
