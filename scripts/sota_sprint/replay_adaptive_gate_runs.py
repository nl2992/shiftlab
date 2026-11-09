#!/usr/bin/env python3
"""Replay saved runs that used GatedAdaptiveRange under corrected predictable bet ordering."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "_wmaxfix_20261105"
NEEDLE = "gated_adaptive_range"
GATED_C_EXACT = {
    "C1",
    "C1-uniformbase",
    "C2",
    "C2-noadapt",
    "C2-floorskip",
    "C5",
    "C6",
    "C6-no_deadline",
    "C6-no_shadow",
    "C6-no_two_stage",
    "Cchk:gated_uniform",
    "Cchk:gated_front",
}


def _affected_policy(policy: str) -> bool:
    return (
        NEEDLE in policy
        or policy in GATED_C_EXACT
        or policy.startswith(("C1-k", "C2-g", "C6-f", "M_RMMSUI_gar", "T2:gated"))
        or (policy.startswith("T6:") and ("xC2" in policy or "xC6" in policy))
    )


def _replace_option(args: list[str], option: str, value: str) -> list[str]:
    out = list(args)
    try:
        i = out.index(option)
    except ValueError:
        out += [option, value]
    else:
        out[i + 1] = value
    return out


def _available_output(out: Path, cmd: list[str]) -> tuple[Path, list[str]] | None:
    if not out.exists():
        return out, cmd
    if (out / "manifest.json").is_file():
        return None
    n = 1
    while out.with_name(out.name + f"_retry{n}").exists():
        n += 1
    retry = out.with_name(out.name + f"_retry{n}")
    return retry, _replace_option(cmd, "--out", str(retry))


def _command(manifest_path: Path, workers: int) -> tuple[list[str], Path, list[str]] | None:
    manifest = json.loads(manifest_path.read_text())
    argv = manifest.get("argv")
    if isinstance(argv, dict):
        policies_value = argv.get("policies", manifest.get("policies", []))
        policies = (
            policies_value if isinstance(policies_value, list) else str(policies_value).split(",")
        )
        policies = [str(p) for p in policies if _affected_policy(str(p))]
        if not policies:
            return None
        old_out = Path(argv.get("out", manifest_path.parent))
        new_out = old_out.with_name(old_out.name + TAG)
        if "kind" in argv and "regimes" in argv:
            runner = "scripts/sota_sprint/screen.py"
            cmd = [
                "uv",
                "run",
                "python",
                runner,
                "--kind",
                str(argv["kind"]),
                "--regimes",
                str(argv["regimes"]),
                "--policies",
                ",".join(policies),
                "--seeds",
                str(argv.get("seeds", 20)),
                "--seed-base",
                str(argv.get("seed_base", 0)),
                "--workers",
                str(workers),
                "--out",
                str(new_out),
            ]
            if "alpha" in argv:
                cmd += ["--alpha", str(argv["alpha"])]
            return cmd, new_out, policies
        if "sources" in argv:
            runner = "scripts/sota_sprint/wp2_run.py"
            cmd = [
                "uv",
                "run",
                "python",
                runner,
                "--sources",
                str(argv["sources"]),
                "--policies",
                ",".join(policies),
                "--seeds",
                str(argv.get("seeds", 20)),
                "--seed-base",
                str(argv["seed_base"]),
                "--workers",
                str(workers),
                "--alpha",
                str(argv.get("alpha", 0.05)),
                "--delay-mult",
                str(argv.get("delay_mult", 1.0)),
                "--out",
                str(new_out),
            ]
            if argv.get("episodes"):
                cmd += ["--episodes", str(argv["episodes"])]
            return cmd, new_out, policies
        return None

    if isinstance(argv, list) and argv:
        old_out_value = manifest.get("out")
        if old_out_value:
            old_out = Path(old_out_value)
        else:
            try:
                old_out = Path(argv[argv.index("--out") + 1])
            except (ValueError, IndexError):
                return None
        new_out = old_out.with_name(old_out.name + TAG)
        try:
            policies_i = argv.index("--policies") + 1
            policies = [p for p in argv[policies_i].split(",") if _affected_policy(p)]
        except (ValueError, IndexError):
            return None
        cmd = _replace_option(argv, "--policies", ",".join(policies))
        cmd = _replace_option(cmd, "--out", str(new_out))
        cmd = _replace_option(cmd, "--workers", str(workers))
        if "--seed-base" not in cmd and manifest.get("seed_base") is not None:
            cmd += ["--seed-base", str(manifest["seed_base"])]
        return ["uv", "run", "python", *cmd], new_out, policies
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("outputs"))
    parser.add_argument("--run-dir", type=Path, help="replay one original run directory")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0, help="maximum number of runs; 0 means all")
    parser.add_argument(
        "--execute", action="store_true", help="execute commands; default prints them"
    )
    args = parser.parse_args()

    paths = (
        [args.run_dir / "manifest.json"]
        if args.run_dir
        else sorted(args.root.rglob("manifest.json"))
    )
    tasks = []
    for path in paths:
        if "_wmaxfix_20261105" in str(path):
            continue
        if not path.is_file():
            continue
        try:
            task = _command(path, args.workers)
        except (OSError, json.JSONDecodeError):
            continue
        if task:
            cmd, out, policies = task
            available = _available_output(out, cmd)
            if available is None:
                print(f"already complete, skipping {out}")
                continue
            out, cmd = available
            tasks.append((path, cmd, out, policies))
    orphan = ROOT / "outputs/sprint2/H/screen1"
    if (not args.run_dir or args.run_dir == Path("outputs/sprint2/H/screen1")) and not (
        orphan / "manifest.json"
    ).exists():
        source_records = orphan / "records.jsonl"
        if source_records.exists():
            out = orphan.with_name(orphan.name + TAG)
            cmd = [
                "uv",
                "run",
                "python",
                "scripts/sota_sprint/screen.py",
                "--kind",
                "synthetic",
                "--regimes",
                "F0_better,F7_near_better",
                "--policies",
                "gated_adaptive_range+front",
                "--seeds",
                "20",
                "--seed-base",
                "2026110701",
                "--workers",
                str(args.workers),
                "--out",
                str(out),
            ]
            available = _available_output(out, cmd)
            if available is None:
                print(f"already complete, skipping {out}")
            else:
                out, cmd = available
                tasks.append((source_records, cmd, out, ["gated_adaptive_range+front"]))
    if args.limit:
        tasks = tasks[: args.limit]
    print(f"scheduled {len(tasks)} corrected runs")
    for index, (manifest, cmd, out, policies) in enumerate(tasks, 1):
        print(
            f"[{index}/{len(tasks)}] source={manifest.parent} output={out} policies={','.join(policies)}"
        )
        print("  " + " ".join(cmd))
        if args.execute:
            result = subprocess.run(cmd, cwd=ROOT, check=False)
            if result.returncode:
                raise SystemExit(f"replay failed ({result.returncode}): {manifest}")


if __name__ == "__main__":
    main()
