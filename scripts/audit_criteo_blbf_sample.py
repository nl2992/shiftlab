"""Audit aggregate structure of Cornell's small Criteo BLBF sample.

The report deliberately excludes impression IDs, hashed visitor IDs, and raw
feature values. The parser also accepts the full text file when available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference_implementation_manifest(archive_path: Path | None) -> dict[str, object] | None:
    if archive_path is None:
        return None
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        selected: dict[str, str] = {}
        for logical_name, suffix in (
            ("parser.py", "/Scripts/parser.py"),
            ("scorer.py", "/Scripts/scorer.py"),
        ):
            matches = [name for name in names if name.endswith(suffix)]
            if len(matches) != 1:
                raise ValueError(f"expected exactly one {logical_name} in reference archive")
            selected[logical_name] = matches[0]
        return {
            "url": "https://www.cs.cornell.edu/~adith/Criteo/BLBF-DisplayAds.zip",
            "archive_sha256": sha256_file(archive_path),
            "parser_path": selected["parser.py"],
            "parser_sha256": hashlib.sha256(archive.read(selected["parser.py"])).hexdigest(),
            "scorer_path": selected["scorer.py"],
            "scorer_sha256": hashlib.sha256(archive.read(selected["scorer.py"])).hexdigest(),
            "execution_status": "source_inspected_not_executed",
        }


def audit(path: Path, reference_archive: Path | None = None) -> dict[str, object]:
    impressions = candidates_total = candidate_rows = 0
    click_headers = candidate_clicks = any_candidate_click = 0
    propensity_min = math.inf
    propensity_max = -math.inf
    propensity_sum = 0.0
    id_min = math.inf
    id_max = -math.inf
    id_inversions = 0
    previous_id: int | None = None
    slots: Counter[str] = Counter()
    candidate_counts: Counter[str] = Counter()
    malformed = 0
    line_number = 0

    with path.open("rt", encoding="utf-8", errors="strict") as stream:
        while True:
            line = stream.readline()
            if not line:
                break
            line_number += 1
            fields = line.split()
            if len(fields) < 7 or fields[0] != "example":
                raise ValueError(f"expected an impression header at line {line_number}")
            try:
                example_id = int(fields[1].rstrip(":"))
                click = int(fields[3])
                propensity = float(fields[4])
                n_slots = int(fields[5])
                n_candidates = int(fields[6])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"invalid impression header at line {line_number}") from exc
            if click not in (0, 1) or not math.isfinite(propensity) or not 0 < propensity <= 1:
                malformed += 1
            if n_slots < 1 or n_candidates < n_slots:
                malformed += 1

            impressions += 1
            click_headers += click
            candidates_total += n_candidates
            slots[str(n_slots)] += 1
            candidate_counts[str(n_candidates)] += 1
            propensity_min = min(propensity_min, propensity)
            propensity_max = max(propensity_max, propensity)
            propensity_sum += propensity
            id_min = min(id_min, example_id)
            id_max = max(id_max, example_id)
            if previous_id is not None and example_id < previous_id:
                id_inversions += 1
            previous_id = example_id

            impression_has_click = False
            for _ in range(n_candidates):
                candidate = stream.readline()
                if not candidate:
                    raise ValueError(f"truncated candidate block after line {line_number}")
                line_number += 1
                candidate_fields = candidate.split()
                if len(candidate_fields) < 2 or candidate_fields[1] != f"exid:{example_id}":
                    raise ValueError(f"candidate/impression ID mismatch at line {line_number}")
                try:
                    candidate_click = int(candidate_fields[0])
                except ValueError as exc:
                    raise ValueError(f"invalid candidate outcome at line {line_number}") from exc
                if candidate_click not in (0, 1):
                    malformed += 1
                candidate_clicks += candidate_click
                impression_has_click |= bool(candidate_click)
                candidate_rows += 1
            any_candidate_click += impression_has_click

    if impressions == 0:
        raise ValueError("input contains no impressions")

    return {
        "schema": "shiftlab.criteo_blbf_sample_audit.v1",
        "status": "sample_structure_audit_only",
        "source": {
            "url": "https://www.cs.cornell.edu/~adith/Criteo/sample.txt",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        },
        "reference_implementation": reference_implementation_manifest(reference_archive),
        "aggregates": {
            "impressions": impressions,
            "candidate_rows": candidate_rows,
            "candidate_rows_expected": candidates_total,
            "header_click_impressions": click_headers,
            "candidate_clicks": candidate_clicks,
            "impressions_with_any_candidate_click": any_candidate_click,
            "header_click_rate": click_headers / impressions,
            "mean_logged_banner_propensity": propensity_sum / impressions,
            "logged_banner_propensity_min": propensity_min,
            "logged_banner_propensity_max": propensity_max,
            "slot_count_histogram": dict(sorted(slots.items(), key=lambda x: int(x[0]))),
            "candidate_count_histogram": dict(
                sorted(candidate_counts.items(), key=lambda x: int(x[0]))
            ),
            "example_id_min": int(id_min),
            "example_id_max": int(id_max),
            "example_id_order_inversions": id_inversions,
            "invalid_value_count": malformed,
        },
        "limitations": [
            "The sample is not the full archive and is not an evaluation result.",
            "The publisher documents outcome-dependent sampling: only a random 10% of non-click impressions are logged; the published scorer applies a subsampling correction.",
            "The sample is not chronological; full-file event order must be checked before a temporal replay.",
            "The source describes event IDs as increasing with time, but supplies no wall-clock feature/label availability timestamps.",
            "This dataset supports logged contextual-bandit policy evaluation, not observed net business utility or guaranteed online adaptation benefit.",
            "The full archive is approximately 35 GB compressed / 250 GB raw and cannot be stored on the current C: volume, which has less than 1 GB free.",
            "The source page calls the data public and requests citation, but does not state a standard redistribution license; do not redistribute the sample or full archive.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Sample or full Criteo BLBF text file")
    parser.add_argument("--output", type=Path, required=True, help="Aggregate-only JSON output")
    parser.add_argument(
        "--reference-archive", type=Path, help="Optional official Cornell helper-code ZIP"
    )
    args = parser.parse_args()
    result = audit(args.input, args.reference_archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["aggregates"], indent=2))
    print(f"wrote aggregate audit: {args.output}")


if __name__ == "__main__":
    main()
