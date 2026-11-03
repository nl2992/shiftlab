"""Build a bounded, source-anchored initial claim and numeric-gate ledger."""

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/retrospective_audit_2026_11_01"
FIELDS = [
    "claim_id",
    "topic",
    "verbatim_historical_claim",
    "claim_type",
    "source_path",
    "branch",
    "source_commit",
    "source_lines",
    "original_gate",
    "original_verdict",
    "estimand",
    "null_class",
    "filtration",
    "feedback_regime",
    "comparison_set",
    "metric",
    "point_estimate",
    "ci_or_bound",
    "replication_status",
    "seed_exposure",
    "data_exposure",
    "validity_status",
    "novelty_status",
    "practical_value",
    "corrected_scope",
    "proposed_verdict",
    "correction_reason",
    "corrective_action",
    "new_experiment_id",
    "reviewer",
    "artifact_links",
    "status",
]


def source_commit(path):
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "e74fdc3", "--", path], text=True
    ).strip()


def main():
    records = []
    sources = [
        ("docs/promising_directions/14_FAIR_REEVALUATION.md", "FAIR"),
        ("docs/promising_directions/12_NOVELTY_DECISION.md", "LANE"),
    ]
    for path, prefix in sources:
        for line_no, line in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
            cells = [x.strip() for x in line.split("|")[1:-1]]
            if prefix == "FAIR" and (not cells or cells[0] not in {f"F{i}" for i in range(1, 11)}):
                continue
            if prefix == "LANE" and (
                not cells
                or not any(
                    cells[0].startswith(k + " ")
                    for k in ["A", "B", "B-Q2", "C", "D", "E", "F", "G"]
                )
            ):
                continue
            r = {k: "NOT_YET_AUDITED" for k in FIELDS}
            r.update(
                claim_id=prefix + "-" + cells[0].split()[0],
                topic=cells[1] if prefix == "FAIR" else cells[0],
                verbatim_historical_claim=line,
                claim_type="HISTORICAL_SOURCE_STATEMENT",
                source_path=path,
                branch="origin/main at e74fdc3",
                source_commit=source_commit(path),
                source_lines=str(line_no),
                original_verdict=cells[4]
                if prefix == "LANE"
                else "Interpretive grade; not registered outcome",
                point_estimate=cells[2],
                validity_status="NOT_YET_AUDITED (source grading is not auditor verification)",
                novelty_status="NOT_YET_AUDITED",
                practical_value=cells[-1],
                corrected_scope="Pending claim-level audit; retain historical statement without adopting it",
                proposed_verdict="NOT_YET_AUDITED",
                reviewer="lead extraction only; no independent review",
                artifact_links=path + ":" + str(line_no),
                status="NOT_YET_AUDITED",
                new_experiment_id="NONE",
            )
            records.append(r)
    # Reproduced B3 numbers remain separate from inherited claim grades.
    path = "docs/promising_directions/results/b3/summary.json"
    r = {k: "NOT_YET_AUDITED" for k in FIELDS}
    r.update(
        claim_id="B3-REGISTERED-COUNTS",
        topic="B3 net-cost comparisons",
        verbatim_historical_claim="WIN: CI(P3b-P0) hi<0 and mean P3b<=mean P2; SAFE: P3b<=P0+spend+2%P0",
        claim_type="RESULT_RECOMPUTATION",
        source_path=path,
        source_commit=source_commit(path),
        branch="origin/main at e74fdc3",
        source_lines="7",
        original_gate="WIN >=3 streams and SAFE every stream",
        original_verdict="HISTORICAL_REGISTERED_PASS",
        estimand="Seed-averaged per-episode deployment loss + query fees + switching fees",
        null_class="WIN cost CI; SAFE descriptive inequality; distinct from conditional certification null",
        feedback_regime="Imposed fixed delay; 100 paired query-randomization seeds per episode",
        comparison_set="P0/P1/P2/P3b/P6",
        metric="Net cost per 2000-event episode",
        point_estimate="WIN 3/7; SAFE 7/7; P6 cheaper on 5/7",
        replication_status="Raw stored episodes and historical bootstrap reproduced; zero mismatches",
        seed_exposure="Historical query-randomization seeds exposed",
        data_exposure="B3 test windows now exposed",
        validity_status="Population CI coverage and certification proof not independently certified",
        novelty_status="NOT_YET_AUDITED",
        practical_value="Scoped retrospective evidence with imposed economics",
        corrected_scope="Preserve registered pass; seed CI for K<5 is conditional on fixed source episodes",
        proposed_verdict="NARROWED",
        correction_reason="One spam episode and three weather episodes do not support across-episode precision via seed bootstrap",
        corrective_action="Add scope interpretation; retain historic result",
        new_experiment_id="NONE",
        reviewer="lead INTERNAL_ONLY",
        artifact_links="17_B3_RECOMPUTATION.md;B3_EPISODE_RECOMPUTATION.json",
        status="INCONCLUSIVE",
    )
    records.append(r)
    with (OUT / "03_CLAIM_MASTER_LEDGER.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(records)
    (OUT / "CLAIM_LEDGER_COVERAGE.md").write_text(
        "# Claim ledger coverage\n\nInitial bounded extraction: F1–F10, A–G plus B-Q2 lane rows, and B3 recomputed counts. This is not the exhaustive W01 census. The decision candidate file remains unreviewed. Source claims are quoted verbatim and NOT_YET_AUDITED, not adopted as findings. B3 has partial reproduced evidence and an unsigned proposed scope correction. No scientific phase gate passes from this ledger.\n",
        encoding="utf-8",
    )
    print("initial source-anchored claims:", len(records))


if __name__ == "__main__":
    main()
