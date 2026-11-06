"""Render the separate WP1 adaptive-gate correction sensitivity from its saved analysis JSON."""

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    r = json.loads(a.input.read_text())
    late = r["primary"]["late_improvement"]
    lines = [
        "# WP1 adaptive-gate correction sensitivity", "",
        "Affected policies are replaced by same-seed rows from the corrected adaptive-gate implementation, "
        "joined on exact stream, episode, seed, and policy keys. This is a correction sensitivity on "
        "previously used data, not independent confirmation. Registered WP1 outputs are unchanged.", "",
        f"**Verdict:** `{r['H_late']['verdict']}`; {r['H_late']['hosts_supporting']}/4 RMM hosts support "
        f"improvement over the strongest certified comparator; enough episodes: {r['H_late']['enough_episodes']}. ", "",
        f"Late-improvement episodes: {late.get('n_ep', 0)} across {late.get('n_cl', 0)} clusters. "
        f"Selected best certified comparator: `{late.get('best_certified')}`.", "",
        "| RMM host | Contrast | Mean Δ cost [95% interval] | Episodes |", "|---|---|---:|---:|",
    ]
    for host in ("rmm:gated_deployment+RMM", "rmm:discern_style+RMM",
                 "rmm:SMCS+retain-incumbent+RMM", "rmm:gated_adaptive_range+RMM"):
        key = f"{host} - {late.get('best_certified')}"
        v = late.get("contrasts", {}).get(key)
        if v:
            interval = "unavailable" if v["lo"] is None else f"[{v['lo']:+.2f}, {v['hi']:+.2f}]"
            lines.append(f"| `{host}` | vs `{late.get('best_certified')}` | {v['mean']:+.2f} {interval} | {v['n_ep']} |")
        else:
            lines.append(f"| `{host}` | vs `{late.get('best_certified')}` | not estimable | 0 |")
    lines += ["", "## Interpretation", "",
              "This report evaluates whether the code correction changes the WP1 conclusion. The retrospective "
              "episode classifier is not causal ground truth, and its episodes come from previously exposed "
              "datasets. The result does not establish real-world late-improvement transfer or a deployment guarantee.", "",
              f"Analysis status: {r.get('analysis_status', 'not recorded')}.", ""]
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
