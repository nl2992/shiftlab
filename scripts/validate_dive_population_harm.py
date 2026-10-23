"""Generate a deterministic population-null/alternative report for DIVE scenarios."""

from __future__ import annotations

import argparse
import hashlib
from datetime import UTC, datetime
from pathlib import Path

from shiftlab.dive.oracle_diagnostics import gaussian_threshold_excess_risk


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/reports/dive_population_harm_validation.md")
    )
    parser.add_argument("--margin", type=float, default=0.10)
    args = parser.parse_args()
    if args.margin < 0:
        parser.error("--margin must be nonnegative")

    cases = (
        ("stationary", 0.0, "Population null: no shift"),
        (
            "benign_nuisance",
            0.0,
            "Population null: nuisance coordinates shift; signal law is unchanged",
        ),
        (
            "boundary_local_harm",
            1.5,
            "Harmful alternative: positive outcomes increase near the boundary",
        ),
        ("residual_variance", 1.5, "Harmful alternative: residual scale increases"),
    )
    rows = []
    for scenario, severity, interpretation in cases:
        risk = gaussian_threshold_excess_risk(scenario, severity=severity)
        rows.append((scenario, severity, risk, risk - args.margin, interpretation))

    source_path = Path("src/shiftlab/dive/oracle_diagnostics.py")
    lines = [
        "# DIVE population decision-harm validation",
        "",
        f"Generated: `{datetime.now(UTC).isoformat()}`",
        "",
        "This is deterministic one-dimensional adaptive quadrature of the benchmark's ",
        "population paired cost difference. It is independent of the finite stream seeds used ",
        "for monitor evaluation. The score is `S=X0-0.9*X1 ~ Normal(0, 1.81)`. The incumbent ",
        "uses the source posterior 0.5 threshold; the reference uses the asymmetric-cost ",
        "threshold `C_FP/(C_FN+C_FP)`. Nuisance features do not enter either policy.",
        "",
        f"Configured material-harm margin: **{args.margin:.6f} cost units**.",
        "",
        "| Scenario | Severity | Population excess cost | Excess minus margin | Interpretation |",
        "|---|---:|---:|---:|---|",
    ]
    for scenario, severity, risk, centered, interpretation in rows:
        lines.append(
            f"| `{scenario}` | {severity:.2f} | {risk:.8f} | {centered:+.8f} | {interpretation} |"
        )
    lines.extend(
        [
            "",
            "The stationary and benign-nuisance scenarios satisfy the population conditional-mean ",
            "null for the fixed 0.10 margin. A finite stream can still have an oracle average above ",
            "the margin because its realized covariates vary; that pathwise flag is not itself the ",
            "null parameter or a false-alarm event. False escalation is a monitor crossing under the ",
            "population null. The boundary-local and residual-variance cases are alternatives only ",
            "when their population excess cost exceeds the configured margin.",
            "",
            "The report validates these four Gaussian-score cases only. It does not prove the ",
            "monitor's guarantee, estimate real-world utility, or cover delayed/selective feedback.",
            "",
            f"Oracle integration source SHA-256: `{sha256(source_path)}`.",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    for scenario, _, risk, _, _ in rows:
        print(f"{scenario}: population excess cost={risk:.8f}")


if __name__ == "__main__":
    main()
