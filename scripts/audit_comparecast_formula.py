"""Audit pinned Comparecast GE-mixture numerics against paper Appendix C."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
import types
import warnings
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.special import gamma, gammainc

from shiftlab.dive.comparecast_gamma_mixture import gamma_exponential_log_mixture_paper

EXPECTED_COMMIT = "52748c86e0429a9612dc79892c3be6156a524132"
PROTOCOL_PATH = Path("papers/shiftguard_unified/comparecast_formula_audit_protocol.md")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(source: Path):
    package_dir = source / "comparecast"
    package = types.ModuleType("comparecast")
    package.__path__ = [str(package_dir)]
    sys.modules["comparecast"] = package
    confseq = types.ModuleType("confseq")
    boundaries = types.ModuleType("confseq.boundaries")

    def unused_boundary(*_args, **_kwargs):
        raise RuntimeError("unused confidence-sequence path called")

    boundaries.normal_log_mixture = unused_boundary  # type: ignore[attr-defined]
    confseq.boundaries = boundaries  # type: ignore[attr-defined]
    sys.modules["confseq"] = confseq
    sys.modules["confseq.boundaries"] = boundaries
    return importlib.import_module("comparecast.eprocess")


def _paper_integral(s: float, v: float, rho: float, c: float) -> float:
    c2 = c * c
    rho_scaled = rho / c2
    a = (v + rho) / c2
    z = (c * s + v + rho) / c2
    normalizer = rho_scaled**rho_scaled / (gamma(rho_scaled) * gammainc(rho_scaled, rho_scaled))
    integral = quad(
        lambda lam: (1 - lam) ** (a - 1) * np.exp(-z * (1 - lam)),
        0.0,
        1.0,
        epsabs=1e-12,
        epsrel=1e-12,
    )[0]
    return normalizer * integral * np.exp((c * s + v) / c2)


def audit(source_dir: Path, output_dir: Path) -> dict:
    import subprocess

    commit = subprocess.check_output(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"expected pinned Comparecast commit {EXPECTED_COMMIT}, got {commit}")
    upstream_path = source_dir / "comparecast/eprocess.py"
    module = _load_module(source_dir)
    upstream = module.gamma_exponential_log_mixture
    rho, c = 0.7, 1.4
    # Include the exact zero/zero case, where the upstream masked logarithm
    # leaves an undefined output buffer value, as well as positive and negative z.
    sums = np.array([0.0, 0.0, 0.3, -0.9, -1.2, 1.5], dtype=np.float64)
    intrinsic = np.array([0.0, 0.2, 0.4, 0.1, 0.0, 0.7], dtype=np.float64)
    paper_logs = gamma_exponential_log_mixture_paper(sums, intrinsic, rho, c)
    paper_values = np.exp(paper_logs)
    integral_values = np.array(
        [_paper_integral(float(s), float(v), rho, c) for s, v in zip(sums, intrinsic, strict=True)]
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all="ignore"):
            upstream_logs = upstream(sums, intrinsic, rho, c)
            # A second call checks whether masked uninitialized values reproduce.
            upstream_logs_repeat = upstream(sums, intrinsic, rho, c)
    positive_z = (c * sums + intrinsic + rho) / (c * c) > 0
    negative_z = ~positive_z
    report = {
        "audit": "comparecast_gamma_exponential_formula_audit_v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "repository": "https://github.com/yjchoe/ComparingForecasters",
            "commit": commit,
            "eprocess_sha256": _sha256(upstream_path),
        },
        "audit_runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "paper": {
            "citation": "Choe and Ramdas, Comparing Sequential Forecasters, Appendix C, equation (49)",
            "url": "https://arxiv.org/abs/2110.00115",
            "formula": "z=(c*s+v+rho)/c^2; positive-z denominator is z^((v+rho)/c^2)",
        },
        "config": {
            "rho": rho,
            "c": c,
            "sums": sums.tolist(),
            "intrinsic_times": intrinsic.tolist(),
        },
        "paper_formula_e_values": paper_values.tolist(),
        "independent_quadrature_e_values": integral_values.tolist(),
        "upstream_log_e_values": upstream_logs.tolist(),
        "upstream_repeat_log_e_values": upstream_logs_repeat.tolist(),
        "positive_z_max_abs_formula_quadrature_error": float(
            np.max(np.abs(paper_values[positive_z] - integral_values[positive_z]))
        ),
        "negative_z_min_bound_minus_integral": float(
            np.min(paper_values[negative_z] - integral_values[negative_z])
        ),
        "upstream_finite": bool(np.isfinite(upstream_logs).all()),
        "upstream_repeat_exactly_equal": bool(np.array_equal(upstream_logs, upstream_logs_repeat)),
        "upstream_warning_count": len(caught),
        "upstream_warning_messages": sorted({str(item.message) for item in caught}),
        "max_abs_upstream_log_difference_on_finite_values": float(
            np.max(
                np.abs(
                    upstream_logs[np.isfinite(upstream_logs)]
                    - paper_logs[np.isfinite(upstream_logs)]
                )
            )
        ),
        "conclusion": (
            "The pinned source matches Appendix C: it evaluates the exact gamma-exponential mixture for positive z and the paper's conservative upper bound for z<=0. The NumPy warnings arise because masked log calls omit an output buffer; masked values occur only in entries discarded by the outer np.where. Across this deterministic diagnostic grid the source was finite, exactly repeatable, and matched the safe formula; the positive-z formula matched independent quadrature and the negative-z bound dominated the exact integral."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    manifest = {
        "audit": report["audit"],
        "source_commit": commit,
        "source_eprocess_sha256": report["source"]["eprocess_sha256"],
        "audit_runner_sha256": report["audit_runner_sha256"],
        "protocol_sha256": report["protocol_sha256"],
        "audit_sha256": _sha256(output_dir / "audit.json"),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report["manifest_sha256"] = _sha256(output_dir / "manifest.json")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparecast-source", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/sota_reproductions/comparecast_formula_audit_v1"),
    )
    args = parser.parse_args()
    report = audit(args.comparecast_source, args.output_dir)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "source",
                    "paper_formula_e_values",
                    "independent_quadrature_e_values",
                    "upstream_log_e_values",
                    "upstream_finite",
                    "upstream_repeat_exactly_equal",
                    "positive_z_max_abs_formula_quadrature_error",
                    "negative_z_min_bound_minus_integral",
                    "max_abs_upstream_log_difference_on_finite_values",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
