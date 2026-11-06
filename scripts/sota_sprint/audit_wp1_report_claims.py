#!/usr/bin/env python3
"""Reconcile headline WP1 Markdown claims with their corresponding saved analyses.

This checks report transcription and rounding only. The source JSON is separately regenerated from
saved records by audit_raw_to_reports.py; neither audit establishes causal labels or validity.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/sprint2/wp1/RESULTS.md"
SOURCE = ROOT / "docs/sprint2/wp1/results_amended_no_xu.json"


def table_after(text: str, marker: str) -> list[list[str]]:
    tail = text.split(marker, 1)[1]
    lines, started = [], False
    for line in tail.splitlines():
        if line.strip().startswith("|"):
            started = True
            lines.append(line.strip())
        elif started:
            break
    cells = [[c.strip() for c in line.strip("|").split("|")] for line in lines]
    return cells[0:1] + cells[2:]


def number(s: str) -> float:
    return float(s.replace("−", "-").replace("+", ""))


def within_rounded(actual: float, displayed: str) -> bool:
    token = displayed.strip().replace("−", "-").replace("+", "")
    decimals = len(token.split(".", 1)[1]) if "." in token else 0
    return abs(actual - float(token)) <= 0.5 * 10 ** (-decimals) + 1e-9


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("docs/sprint2/wp1/report_claim_audit.json"))
    args = ap.parse_args()
    src = json.loads(SOURCE.read_text())
    historical = json.loads((SOURCE.parent / "results.json").read_text())
    report = REPORT.read_text()
    checks: list[dict] = []

    # Episode/class count table: recompute source-family totals from the saved classifier output.
    count_table = table_after(report, "Episode-level class counts:")
    count_map = {r[0].replace("**", ""): r for r in count_table[1:]}
    mismatch = []
    checked = 0
    families = {
        "cached (9 streams)": ["cached"],
        "fresh fixed pairs (5)": ["fresh"],
        "new `win` (5)": ["late_win"],
        "new `exp` (5)": ["late_exp"],
        "twin known-null (splits 0-1)": ["twin"],
    }
    for display, source_keys in families.items():
        row = count_map.get(display)
        if row is None:
            mismatch.append(f"missing class-count row: {display}")
            continue
        expected_episodes = sum(sum(src["class_counts"][k].values()) for k in source_keys)
        got = int(row[1])
        checked += 1
        if got != expected_episodes:
            mismatch.append(f"{display} episodes {got} != {expected_episodes}")
        for cls in (
            "late_improvement",
            "early_improvement",
            "reversal",
            "stationary_better",
            "null",
        ):
            actual = sum(src["class_counts"][k].get(cls, 0) for k in source_keys)
            try:
                shown = int(
                    row[
                        2
                        + (
                            "late_improvement",
                            "early_improvement",
                            "reversal",
                            "stationary_better",
                            "null",
                        ).index(cls)
                    ]
                )
            except (ValueError, IndexError):
                mismatch.append(f"{display}: missing {cls} count")
                continue
            checked += 1
            if shown != actual:
                mismatch.append(f"{display}/{cls}: {shown} != {actual}")
    total = count_map.get("real total")
    if total is None:
        mismatch.append("missing real-total row")
    else:
        for idx, cls in enumerate(
            (
                "episodes",
                "late_improvement",
                "early_improvement",
                "reversal",
                "stationary_better",
                "null",
            ),
            start=1,
        ):
            actual = (
                sum(
                    sum(src["class_counts"][k].values())
                    for k in ("cached", "fresh", "late_win", "late_exp")
                )
                if cls == "episodes"
                else sum(
                    src["class_counts"][k].get(cls, 0)
                    for k in ("cached", "fresh", "late_win", "late_exp")
                )
            )
            displayed = re.search(r"\d+", total[idx]).group(0)
            checked += 1
            if int(displayed) != actual:
                mismatch.append(f"real total/{cls}: {displayed} != {actual}")
        late_clusters = len(src["class_clusters"]["late_improvement"])
        rev_clusters = len(src["class_clusters"]["reversal"])
        if not re.search(rf"10 \({late_clusters} clusters\)", total[2]):
            mismatch.append("real-total late episode/cluster annotation is inconsistent")
        if not re.search(rf"16 \({rev_clusters} clusters\)", total[4]):
            mismatch.append("real-total reversal episode/cluster annotation is inconsistent")
    checks.append(
        {
            "name": "WP1 episode and class counts",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    # Reconcile outcome-blind classifier diagnostics and named cluster summaries directly from
    # the frozen per-episode class file, including both registered delta sensitivities.
    classes = json.loads((ROOT / "outputs/sprint2/WP1/classes.json").read_text())
    real_rows = [r for r in classes if r["family"] != "twin"]
    twin_rows = [r for r in classes if r["family"] == "twin"]
    late_by_cluster, reversal_by_cluster = {}, {}
    for r in real_rows:
        if r["class"] == "late_improvement":
            late_by_cluster[r["cluster"]] = late_by_cluster.get(r["cluster"], 0) + 1
        if r["class"] == "reversal":
            reversal_by_cluster[r["cluster"]] = reversal_by_cluster.get(r["cluster"], 0) + 1
    late_line = report.split("* Late episodes by dataset:", 1)[1].split("\n*", 1)[0]
    reversal_line = report.split("* Reversal episodes by dataset:", 1)[1].split("\n*", 1)[0]
    classifier_line = report.split("* Classifier false-positive check:", 1)[1].split("\n*", 1)[0]
    sens_line = report.split("* Rule sensitivity:", 1)[1].split("\n*", 1)[0]
    mismatch, checked = [], 0
    for cls, observed, expected in (
        ("twin changed", sum(r["p"] <= 0.01 for r in twin_rows), 3),
        ("real changed", sum(r["p"] <= 0.01 for r in real_rows), 62),
        (
            "real changed with effect/sign",
            sum(
                r["p"] <= 0.01
                and r["class"] in ("late_improvement", "early_improvement", "reversal")
                for r in real_rows
            ),
            26,
        ),
    ):
        checked += 1
        if observed != expected:
            mismatch.append(f"{cls}: computed {observed}, claimed {expected}")
    if not all(s in classifier_line for s in ("3 of 124", "62/348", "26 of them")):
        mismatch.append("classifier false-positive/screen summary text differs from frozen labels")
    else:
        checked += 1
    for delta, cat, expected in (
        ("0.005", "late_improvement", 8),
        ("0.005", "reversal", 16),
        ("0.02", "late_improvement", 12),
        ("0.02", "reversal", 15),
    ):
        observed = sum(r["sens"][delta] == cat for r in real_rows)
        checked += 1
        if observed != expected:
            mismatch.append(f"delta={delta}/{cat}: {observed} != {expected}")
    if not all(
        s in sens_line for s in (".005 gives late 8, reversal 16", ".02 gives late 12, reversal 15")
    ):
        mismatch.append("classifier rule-sensitivity summary text differs from frozen labels")
    else:
        checked += 1
    for label, dist, line in (
        ("late", late_by_cluster, late_line),
        ("reversal", reversal_by_cluster, reversal_line),
    ):
        checked += len(dist)
        for cluster, count in dist.items():
            if count == 1 and label == "reversal":
                if "one each from" not in line or cluster not in line:
                    mismatch.append(f"{label} cluster distribution omits {cluster} (one episode)")
            elif f"{cluster} {count}" not in line:
                mismatch.append(f"{label} cluster distribution omits {cluster} {count}")
    checks.append(
        {
            "name": "WP1 classifier and episode distribution claims",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    # The primary table is report prose rather than a generated artifact: check each displayed
    # paired estimate against the exact cluster-bootstrap result and selected comparator in JSON.
    primary_table = table_after(report, "## 2. Primary: per-class paired contrasts")
    mismatch, checked = [], 0
    methods = [
        "rmm:gated_deployment+RMM",
        "rmm:discern_style+RMM",
        "rmm:SMCS+retain-incumbent+RMM",
        "rmm:gated_adaptive_range+RMM",
    ]
    host = ["gated_deployment", "discern_style", "SMCS+retain-incumbent", "gated_adaptive_range"]
    srr = [
        "E_srr:gated_deployment",
        "E_srr:discern_style",
        "E_srr:SMCS+retain-incumbent",
        "E_srr:gated_adaptive_range",
    ]
    for row in primary_table[1:]:
        if len(row) < 6:
            continue
        m = re.match(r"^([a-z_ ]+?)(?: \((\d+)/(\d+)\))?:\s*(vs .*)$", row[0])
        if not m:
            continue
        cls, n_ep, n_cl, comparison = m.groups()
        cls = {"late": "late_improvement", "all real": "all"}.get(cls.strip(), cls.strip())
        if cls not in src["primary"]:
            continue
        record = src["primary"][cls]
        for label, token, expected in (
            ("n_ep", n_ep, record.get("n_ep")),
            ("n_cl", n_cl, record.get("n_cl")),
        ):
            if token is not None and expected is not None:
                got = int(token)
                checked += 1
                if got != expected:
                    mismatch.append(f"{cls}/{label}: {got} != {expected}")
        if comparison.startswith("vs best certified"):
            comp = record["best_certified"]
        elif comparison.startswith("vs own host"):
            comp = None
        elif comparison.startswith("vs E_srr"):
            comp = "E_srr"
        else:
            continue
        for i, method in enumerate(methods):
            if comp is None:
                comparator = host[i]
            elif comp == "E_srr":
                comparator = srr[i]
            else:
                comparator = comp
            key = f"{method} - {comparator}"
            contrast = record.get("contrasts", {}).get(key)
            cell = row[2 + i]
            if not cell.strip():
                continue
            vals = re.search(
                r"([+−-]?\d+(?:\.\d+)?)\s*\[\s*([+−-]?\d+(?:\.\d+)?)\s*,\s*([+−-]?\d+(?:\.\d+)?)\s*\]",
                cell,
            )
            if contrast is None or vals is None:
                mismatch.append(
                    f"{cls}/{comparison}/method {i}: missing source or parseable estimate"
                )
                continue
            checked += 3
            for field, displayed in zip(("mean", "lo", "hi"), vals.groups()):
                if not within_rounded(float(contrast[field]), displayed):
                    mismatch.append(
                        f"{cls}/{comparison}/{method}/{field}: source {contrast[field]} vs {displayed}"
                    )
    checks.append(
        {
            "name": "WP1 primary contrast table",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch[:50],
        }
    )

    # Registered one-factor sensitivity table: the chosen best certified comparator is recalculated
    # per sensitivity cell in the amended result JSON.
    sensitivity_table = table_after(report, "## 6. Sensitivity")
    sens_names = {
        "native (reference)": "sens_delay1",
        "delay x0.5": "sens_delay0.5",
        "delay x2": "sens_delay2",
        "B = 100": "sens_B100",
        "B = 400": "sens_B400",
        "c_s = 2": "sens_cs2",
        "c_s = 10": "sens_cs10",
    }
    mismatch, checked = [], 0
    for row in sensitivity_table[1:]:
        if len(row) != 4:
            continue
        setting = row[0].replace("**", "")
        source_key = sens_names.get(setting)
        if source_key is None:
            mismatch.append(f"unrecognized sensitivity row {setting!r}")
            continue
        # The sensitivity table is explicitly historical and retains Xu's acquisition adapter in
        # its selected comparator panel; compare it to that registered result, not the amended pool.
        block = historical["sensitivity"][source_key]
        late = block["late_improvement"]
        comparator = late["best_certified"]
        contrasts = [
            late["contrasts"].get(f"rmm:gated_deployment+RMM - {comparator}"),
            late["contrasts"].get(f"rmm:gated_adaptive_range+RMM - {comparator}"),
            block["reversal"]["contrasts"].get("E_rb:gated_deployment - rmm:gated_deployment+RMM"),
        ]
        for col, expected in zip(row[1:], contrasts):
            if expected is None:
                mismatch.append(f"{setting}: missing source contrast")
                continue
            parsed = re.search(
                r"([+−-]?\d+(?:\.\d+)?)\s*\[\s*([+−-]?\d+(?:\.\d+)?)\s*,\s*([+−-]?\d+(?:\.\d+)?)\s*\]",
                col,
            )
            if parsed is None:
                mismatch.append(f"{setting}: unparseable sensitivity cell {col!r}")
                continue
            checked += 3
            for field, displayed in zip(("mean", "lo", "hi"), parsed.groups()):
                if not within_rounded(float(expected[field]), displayed):
                    mismatch.append(f"{setting}/{field}: source {expected[field]} vs {displayed}")
    checks.append(
        {
            "name": "WP1 sensitivity contrast table",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch[:50],
        }
    )

    # Late-class mean costs and registered decision are key topline claims.
    late = src["primary"]["late_improvement"]["mean_J"]
    mean_claims = {
        "RMM gated": "rmm:gated_deployment+RMM",
        "E_srr gated": "E_srr:gated_deployment",
        "rmm:LRMD": "rmm:LRMD",
        "qiu_delayed_movement": "qiu_delayed_movement",
        "E_swcert": "E_swcert",
        "gar+front": "gated_adaptive_range+front",
        "choe+front": "choe_ramdas_eb+front",
        "Xu": "xu_acquisition_only",
        "A5b": "A5b",
        "control": "CONTROL_never_switch",
    }
    mismatch = []
    late_section = report.split("**Mean J on late_improvement:**", 1)[1].split(
        "\n* **Heterogeneity", 1
    )[0]
    for label, method in mean_claims.items():
        pattern = rf"(?<![\w]){re.escape(label)}\s+([+−-]?\d+(?:\.\d+)?)"
        match = re.search(pattern, late_section)
        if not match:
            mismatch.append(f"missing late-class mean J claim for {label}")
            continue
        if not within_rounded(float(late[method]), match.group(1)):
            mismatch.append(f"late mean J/{label}: {late[method]} != {match.group(1)}")
    checked = len(mean_claims)
    if src["H_late"]["verdict"] not in report or "NOT_SUPPORTED" not in report:
        mismatch.append("registered H_late verdict missing or inconsistent")
    else:
        checked += 1
    checks.append(
        {
            "name": "WP1 late-class topline and verdict",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    # Post-switch false-rollback counts are descriptive evaluator labels. Verify the report's
    # numerator/denominator sequence against the trace-summary JSON without treating them as rates
    # available to the deployed policy.
    rollback = json.loads((ROOT / "docs/sprint2/wp1/false_rollback_audit.json").read_text())
    paragraph = report.split("**False-rollback trace diagnostic.**", 1)[1].split("\n\n## 4.", 1)[0]
    paragraph = " ".join(paragraph.split())
    policy_order = [
        "gated_deployment",
        "discern_style",
        "SMCS+retain-incumbent",
        "gated_adaptive_range",
    ]
    expected_labels = ["late_improvement", "reversal", "stationary_better", "null"]
    mismatch, checked = [], 0
    for cls in expected_labels:
        ratios = []
        for host_name in policy_order:
            row = rollback["summary"][f"E_rb:{host_name}|{cls}"]
            ratios.append(f"{row['false_rollbacks']}/{row['rollbacks']}")
        checked += 4
        if cls == "late_improvement":
            marker = "late-improvement class"
        elif cls == "stationary_better":
            marker = "stationary-better episodes"
        elif cls == "null":
            marker = "null episodes"
        else:
            marker = f"{cls} class"
        pos = paragraph.find(marker)
        if pos < 0:
            mismatch.append(f"missing rollback class narrative: {marker}")
            continue
        later = paragraph[pos:]
        for ratio in ratios:
            at = later.find(ratio)
            if at < 0:
                mismatch.append(f"{marker}: missing reported rollback fraction {ratio}")
            else:
                later = later[at + len(ratio) :]
    for value in ("1,044 episode-seed jobs", "4,176 policy rows"):
        checked += 1
        if value not in paragraph:
            mismatch.append(f"false-rollback replay scope omits {value}")
    checks.append(
        {
            "name": "WP1 false-rollback narrative counts",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    # Reversal-class operating table: transition rates come from evaluator diagnostics; J is the
    # class mean in the amended primary analysis.
    reversal_table = table_after(
        report, "## 3. Reversal, post-switch monitoring and certified rollback"
    )
    display_policies = {
        "RMM gated": "rmm:gated_deployment+RMM",
        "E_rb gated": "E_rb:gated_deployment",
        "E_srr gated": "E_srr:gated_deployment",
        "Xu": "xu_acquisition_only",
        "control": "CONTROL_never_switch",
    }
    mismatch, checked = [], 0
    diagnostics = src["diagnostics"]["reversal"]
    mean_j = src["primary"]["reversal"]["mean_J"]
    for row in reversal_table[1:]:
        if len(row) != 5:
            continue
        policy = display_policies.get(row[0])
        if policy is None:
            mismatch.append(f"unrecognized reversal operating-table row {row[0]!r}")
            continue
        for field, displayed in zip(("promote", "rollbacks", "switches"), row[1:4]):
            checked += 1
            if not within_rounded(float(diagnostics[policy][field]), displayed):
                mismatch.append(
                    f"reversal {policy}/{field}: {diagnostics[policy][field]} != {displayed}"
                )
        checked += 1
        if not within_rounded(float(mean_j[policy]), row[4]):
            mismatch.append(f"reversal {policy}/J: {mean_j[policy]} != {row[4]}")
    checks.append(
        {
            "name": "WP1 reversal operating table",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    # Track-V twin-null promotion rates: parse the displayed values and bind them to the amended
    # source results. This verifies transcription, not the null validity of any method.
    twin_src = src["twin_promotion"]
    twin_section = report.split("## 4. Track V: twin known-null promotion", 1)[1].split(
        "\n## 5.", 1
    )[0]
    twin_claims = {
        "RMM gated / discern / SMCS / gar": [
            "rmm:gated_deployment+RMM",
            "rmm:discern_style+RMM",
            "rmm:SMCS+retain-incumbent+RMM",
            "rmm:gated_adaptive_range+RMM",
        ],
        "E_rb gated / discern / SMCS / gar": [
            "E_rb:gated_deployment",
            "E_rb:discern_style",
            "E_rb:SMCS+retain-incumbent",
            "E_rb:gated_adaptive_range",
        ],
        "E_srr gated / gar": ["E_srr:gated_deployment", "E_srr:gated_adaptive_range"],
        "E_swcert": ["E_swcert"],
        "Xu": ["xu_acquisition_only"],
        "A5b (V2)": ["A5b"],
        "control": ["CONTROL_never_switch"],
    }
    mismatch, checked = [], 0
    for label, methods_for_label in twin_claims.items():
        line = next((ln for ln in twin_section.splitlines() if ln.startswith(f"| {label} |")), None)
        if line is None:
            mismatch.append(f"missing twin-promotion row: {label}")
            continue
        # E_rb's display is a relational statement, not a duplicated numeric rate row.
        if label.startswith("E_rb"):
            checked += len(methods_for_label)
            if "identical to their RMM hosts" not in line:
                mismatch.append("E_rb twin row no longer states first-promotion equality")
            for host_name, erb_name in zip(
                twin_claims["RMM gated / discern / SMCS / gar"], methods_for_label
            ):
                if (
                    abs(float(twin_src[host_name]["rate"]) - float(twin_src[erb_name]["rate"]))
                    > 1e-12
                ):
                    mismatch.append(f"E_rb/RMM first-promotion rates differ for {erb_name}")
            continue
        shown = re.findall(r"(?<![A-Za-z])(?:0?\.\d+|0)(?![A-Za-z])", line.split("|", 2)[2])
        if not shown:
            mismatch.append(f"missing displayed rate: {label}")
            continue
        expected = [float(twin_src[m]["rate"]) for m in methods_for_label]
        if len(shown) != len(expected):
            mismatch.append(f"{label}: displayed {len(shown)} values, expected {len(expected)}")
            continue
        checked += len(expected)
        for method, got, want in zip(methods_for_label, shown, expected):
            if not within_rounded(want, got):
                mismatch.append(f"{label}/{method}: {got} != {want}")
    checks.append(
        {
            "name": "WP1 twin-null promotion table",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    # E_swcert's post-hoc R10 statement must distinguish the observed point risk from its CI upper
    # bound, and the displayed Xu R10 point must not be represented as an R5 selection.
    r10_src = json.loads((ROOT / "docs/sprint2/wp1/trackR_E_swcert.json").read_text())
    r10 = r10_src["curves"]["R10"]["E_swcert"]
    r10_text = report.split("## E_swcert Track R", 1)[1].split("\n## ", 1)[0]
    xu_line = next(
        (ln for ln in report.splitlines() if ln.startswith("| xu_acquisition_only |")), ""
    )
    mismatch, checked = [], 0
    if not within_rounded(
        float(r10["risk"]), re.search(r"Evaluation risks were ([.\d]+)", r10_text).group(1)
    ):
        mismatch.append("E_swcert R10 point risk differs from Track-R JSON")
    else:
        checked += 1
    ci = re.search(r"95% Wilson \[([.\d]+),([.\d]+)\]", r10_text)
    if not ci or not within_rounded(float(r10["risk_ci"][1]), ci.group(2)):
        mismatch.append("E_swcert R10 Wilson upper bound differs from Track-R JSON")
    else:
        checked += 1
    if not (
        float(r10["risk"]) < 0.10 < float(r10["risk_ci"][1])
        and "point risk below the .10 target" in r10_text
        and "upper bound" in r10_text
    ):
        mismatch.append("E_swcert R10 point/interval target interpretation is missing or incorrect")
    else:
        checked += 1
    if "R5: none; R10:" not in xu_line:
        mismatch.append("Xu Track-R table does not explicitly separate R5 and R10")
    else:
        checked += 1
    checks.append(
        {
            "name": "WP1 Track-R target and operating-point wording",
            "status": "PASS" if not mismatch else "FAIL",
            "cell_count": checked,
            "differences": mismatch,
        }
    )

    result = {
        "audit": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "sources": {
            "primary": str(SOURCE.relative_to(ROOT)),
            "historical_sensitivity": str((SOURCE.parent / "results.json").relative_to(ROOT)),
        },
        "report": str(REPORT.relative_to(ROOT)),
        "checks": checks,
        "limitations": [
            "Checks selected headline claims and the primary/sensitivity tables, not every WP1 table or diagnostic sentence.",
            "It does not validate classifier assumptions, causal labels, independent confirmation, or theorem validity.",
        ],
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["audit"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
