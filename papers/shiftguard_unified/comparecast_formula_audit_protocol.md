# Comparecast gamma-exponential formula audit

## Question

Do the NumPy masked-log warnings in the pinned ComparingForecasters e-process
change returned gamma-exponential mixture values, or indicate a discrepancy
with the paper's formula?

## Frozen source and reference

- Repository: `yjchoe/ComparingForecasters`.
- Commit: `52748c86e0429a9612dc79892c3be6156a524132`.
- Source file: `comparecast/eprocess.py`, SHA-256 recorded in the output.
- Mathematical reference: Choe and Ramdas, *Comparing Sequential Forecasters*,
  Appendix C, equation (49): https://arxiv.org/abs/2110.00115.

The audit compares the upstream function with an independent implementation
using initialized output buffers for masked logarithms and direct numerical
quadrature. It covers the positive-z exact mixture, the nonpositive-z
conservative upper-bound branch, and the zero-sum/zero-intrinsic-time limit.
The small deterministic grid is a numerical correctness check, not a
statistical calibration, power study, or reproduction of published
experiments. It does not change the upstream source.

## Pass criteria

- The paper-formula implementation agrees with numerical quadrature for
  positive z to absolute error at most `1e-10`.
- The conservative branch is at least the numerically integrated mixture for
  the frozen nonpositive-z diagnostic cases.
- Upstream returned log-e-values are finite, exactly repeatable, and match the
  safe paper-formula implementation on the frozen grid.

## Reproduction

```powershell
uv run python scripts/audit_comparecast_formula.py `
  --comparecast-source C:\path\to\ComparingForecasters `
  --output-dir outputs/shiftguard_unified/sota_reproductions/comparecast_formula_audit_v2
```

The audit records the exact external commit/file hash, local runner hash,
protocol hash, warning count, numerical comparisons, and output hashes. Keep
the warning diagnostic distinct from null calibration: passing this check
establishes numerical agreement for these cases only.
