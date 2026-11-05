"""Audit the frozen S0 B3+ mechanism ablation and emit corrected tables.

This reads only the checked-in JSONL and provenance files. It does not rerun or
retune the method. Paired intervals follow b3_plus_analysis.py: episode bootstrap
when at least five episodes exist, otherwise seed bootstrap, flagged low-power.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/promising_directions/results/b3_plus/ablation"
OUT = ROOT / "outputs/b3_plus_attribution_audit"
STREAMS = ("spam", "rialto", "weather")
METHODS = ("P3b", "P7b", "P7a", "P4ref", "P7s")
BOOTSTRAPS = 20_000
BOOT_SEED = 20261108
EXPECTED_SOURCE_HASHES = {
    "b3_plus_policy.py": "1d0569f38126edf46c9c497fada488ce24c09c61cf815562bbbb845fdb4bbb9f",
    "b3_plus_baselines.py": "794051b75770aa35d1ead89e506c652c1e97e70d53e2a959bc892769eb16aec5",
    "b3_plus_experiments.py": "15937830826c2e106576b32ffba8e98cc9b8d18a43e32dcb73d30151cad297d7",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_data() -> dict[str, list[dict]]:
    sums = {}
    for line in (DATA / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        sums[name.lstrip("*")] = digest
    rows: dict[str, list[dict]] = {}
    for stream in STREAMS:
        path = DATA / f"{stream}__S0__h2000.jsonl"
        if sha256(path) != sums.get(path.name):
            raise ValueError(f"raw input checksum mismatch: {path.name}")
        parsed = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
        ]
        if not parsed:
            raise ValueError(f"no episodes found for {stream}")
        if any(row["config"] != "S0" or row["horizon"] != 2000 for row in parsed):
            raise ValueError(f"unexpected protocol settings in {stream}")
        if any(set(METHODS) - row["variants"].keys() for row in parsed):
            raise ValueError(f"missing matched method for {stream}")
        if (
            len({row["n_seeds"] for row in parsed}) != 1
            or len({row["seed_base"] for row in parsed}) != 1
        ):
            raise ValueError(f"inconsistent seed metadata for {stream}")
        rows[stream] = parsed
    return rows


def paired_interval(
    episode_delta: np.ndarray, seed_delta: np.ndarray, rng: np.random.Generator
) -> dict:
    low_power = len(episode_delta) < 5
    values = seed_delta if low_power else episode_delta
    indexes = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    means = values[indexes].mean(axis=1)
    return {
        "mean": float(episode_delta.mean()),
        "lo": float(np.quantile(means, 0.025)),
        "hi": float(np.quantile(means, 0.975)),
        "bootstrap_unit": "seed" if low_power else "episode",
        "low_power": low_power,
    }


def audit(rows: dict[str, list[dict]]) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    result = {"streams": {}, "checks": {}}
    decomposition_max_error = 0.0
    for stream, episodes in rows.items():
        names = [row["episode"] for row in episodes]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate episodes in {stream}")
        per_episode = {
            method: np.array([r["variants"][method]["mean_cost"] for r in episodes])
            for method in METHODS
        }
        per_seed = {
            method: np.mean([r["variants"][method]["cost_seeds"] for r in episodes], axis=0)
            for method in METHODS
        }
        reference_episode = per_episode["P3b"]
        reference_seed = per_seed["P3b"]
        methods = {}
        for method in METHODS:
            means = [r["variants"][method] for r in episodes]
            cost = float(per_episode[method].mean())
            labels = float(np.mean([m["mean_labels"] for m in means]))
            loss = float(np.mean([m["mean_loss"] for m in means]))
            switches = float(np.mean([m["mean_switches"] for m in means]))
            reconstruct = loss + episodes[0]["cq"] * labels + episodes[0]["cs"] * switches
            decomposition_max_error = max(decomposition_max_error, abs(cost - reconstruct))
            methods[method] = {
                "mean_net_cost": cost,
                "mean_deployment_loss": loss,
                "mean_labels": labels,
                "mean_switches": switches,
                "mean_promotions": float(np.mean([m["promotion_rate"] for m in means])),
                "delta_vs_P3b": paired_interval(
                    per_episode[method] - reference_episode,
                    per_seed[method] - reference_seed,
                    rng,
                )
                if method != "P3b"
                else None,
                "labels_saved_vs_P3b": float(
                    np.mean(
                        [
                            r["variants"]["P3b"]["mean_labels"]
                            - r["variants"][method]["mean_labels"]
                            for r in episodes
                        ]
                    )
                ),
                "deployment_loss_delta_vs_P3b": loss
                - float(np.mean([r["variants"]["P3b"]["mean_loss"] for r in episodes])),
                "switch_delta_vs_P3b": switches
                - float(np.mean([r["variants"]["P3b"]["mean_switches"] for r in episodes])),
            }
        result["streams"][stream] = {"episodes": len(episodes), "methods": methods}
    provenance = json.loads((DATA / "provenance.json").read_text(encoding="utf-8"))
    run = provenance["runs"][0]
    for filename, expected in EXPECTED_SOURCE_HASHES.items():
        source_label = filename.removeprefix("b3_plus_").removesuffix(".py")
        if run[f"b3_plus_{source_label}_sha256"] != expected:
            raise ValueError(f"run source hash changed in provenance for {filename}")
        if sha256(ROOT / "scripts/promising_directions" / filename) != expected:
            raise ValueError(f"current source does not match recorded run source: {filename}")
    result["checks"] = {
        "raw_file_checksums": "pass",
        "source_hashes_match_recorded_run": True,
        "streams": list(rows),
        "episode_counts": {s: len(v) for s, v in rows.items()},
        "seeds_per_episode": {s: rows[s][0]["n_seeds"] for s in rows},
        "seed_base": {s: rows[s][0]["seed_base"] for s in rows},
        "cost_decomposition_max_absolute_error": decomposition_max_error,
        "bootstrap_draws": BOOTSTRAPS,
        "bootstrap_seed": BOOT_SEED,
    }
    return result


def make_markdown(result: dict) -> str:
    lines = [
        "# B3+ settled-acquisition ablation audit",
        "",
        "Reanalysis of the pre-existing frozen S0 ablation JSONL; no new model, method, data, or seed was run.",
        "The original records contain paired query-randomisation seeds within each episode. Confidence intervals use episode bootstrap when K≥5; otherwise they use seed bootstrap and are marked low-power.",
        "",
        "The cost identity audited per method is `deployment loss + c_q × labels + c_s × switches`.",
        "",
    ]
    for stream, data in result["streams"].items():
        lines += [
            f"## {stream} (K={data['episodes']})",
            "",
            "| Variant | Net cost | Δ vs P3b (95% interval) | labels saved | deployment-loss Δ | switch Δ |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for method in METHODS:
            d = data["methods"][method]
            ci = d["delta_vs_P3b"]
            interval = (
                "reference"
                if ci is None
                else f"{ci['mean']:+.2f} [{ci['lo']:+.2f}, {ci['hi']:+.2f}]"
                + (" (seed bootstrap; low power)" if ci["low_power"] else "")
            )
            lines.append(
                f"| {method} | {d['mean_net_cost']:.2f} | {interval} | {d['labels_saved_vs_P3b']:+.1f} | {d['deployment_loss_delta_vs_P3b']:+.2f} | {d['switch_delta_vs_P3b']:+.3f} |"
            )
        lines.append("")
    lines += [
        "## Interpretation and scope",
        "",
        "P7s is the corrected method: P7b is the hopeless-state-only ablation and is not the final method. The direct P7s–P7b contrast isolates the additional settled-state gate on these streams. The ablation supports a query-cost mechanism on spam, rialto, and weather only. It does not isolate the mechanism on openml_ldpa, which was evaluated later in screening and has no matching P7a/P7b/P4ref ablation in this artifact.",
        "",
        "This evidence is descriptive of selected streams, not a SOTA result. Query suppression after a deployment choice is related to value-of-information and active sensing; the contribution must be framed as anytime-valid post-promotion monitoring under a hard query budget, with the rollback/validity trade-off measured, rather than generic decision-aware acquisition.",
        "",
        "## Integrity checks",
        "",
        "```json",
        json.dumps(result["checks"], indent=2),
        "```",
    ]
    return "\n".join(lines) + "\n"


def make_latex(result: dict) -> str:
    labels = {
        "P3b": "P3b (anytime certificate)",
        "P4ref": "P4ref (persistence cost rule)",
        "P7a": "P7a (promotion gate only)",
        "P7b": "P7b (hopeless gate only)",
        "P7s": r"\textbf{P7s (settled-state acquisition)}",
    }
    order = ("P3b", "P4ref", "P7a", "P7b", "P7s")
    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r" & \multicolumn{2}{c}{spam ($K{=}1$)} & \multicolumn{2}{c}{rialto ($K{=}16$)} & \multicolumn{2}{c}{weather ($K{=}3$)} "
        + chr(92) * 2,
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
        r"Variant & cost & $\Delta$ & cost & $\Delta$ & cost & $\Delta$ " + chr(92) * 2,
        r"\midrule",
    ]
    for method in order:
        cells = [labels[method]]
        for stream in ("spam", "rialto", "weather"):
            d = result["streams"][stream]["methods"][method]
            interval = d["delta_vs_P3b"]
            delta = "--" if interval is None else f"{interval['mean']:+.2f}"
            cells.extend([f"{d['mean_net_cost']:.2f}", delta])
        lines.append(" & ".join(cells) + " " + chr(92) * 2)
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = read_data()
    result = audit(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (OUT / "report.md").write_text(make_markdown(result), encoding="utf-8")
    (ROOT / "paper/b3_plus/tables/table3_ablation.tex").write_text(
        make_latex(result), encoding="utf-8"
    )
    print(str(OUT / "report.md").encode("ascii", "backslashreplace").decode())
    for stream, data in result["streams"].items():
        print(stream, "K=", data["episodes"])
        for method, values in data["methods"].items():
            ci = values["delta_vs_P3b"]
            print(
                method,
                round(values["mean_net_cost"], 3),
                None
                if ci is None
                else (round(ci["mean"], 3), round(ci["lo"], 3), round(ci["hi"], 3)),
                round(values["labels_saved_vs_P3b"], 1),
            )


if __name__ == "__main__":
    main()
