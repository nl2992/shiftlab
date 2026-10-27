"""Exact two-dimensional QP solver for MOPE's general-distribution betting step.

MOPE's pinned reference solves this same concave quadratic program with CVXPY
on every event. This module enumerates the stationary point, each feasible
edge optimum, and polygon vertices, which exactly covers a concave quadratic
maximum over its bounded 2-D feasible polygon.
"""

from __future__ import annotations

import itertools

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
_PSI = 2.0 - 4.0 * np.log(2.0)


def solve_gd_exact(wmax: float, a: FloatArray, b: FloatArray) -> FloatArray:
    """Maximize MOPE's concave quadratic over the reference 4-halfspace set."""
    matrix = np.asarray(a, dtype=np.float64)
    linear = np.asarray(b, dtype=np.float64)
    if matrix.shape != (2, 2) or linear.shape != (2,):
        raise ValueError("MOPE general-distribution QP requires a 2x2 matrix and 2-vector")
    if not np.isfinite(matrix).all() or not np.isfinite(linear).all() or wmax <= 1.0:
        raise ValueError("MOPE QP inputs must be finite and wmax must exceed one")
    matrix = (matrix + matrix.T) * 0.5
    if np.linalg.eigvalsh(matrix)[0] < -1e-9:
        raise ValueError("MOPE quadratic matrix must be positive semidefinite")

    # These are the exact four constraints used by the pinned solve_gd.
    constraints = np.array(
        [[-1.0, 1.0], [-1.0, -2.0], [wmax - 1.0, -1.0], [wmax - 1.0, wmax]],
        dtype=np.float64,
    )
    candidates: list[FloatArray] = []

    def is_feasible(point: FloatArray) -> bool:
        return bool(np.all(constraints @ point >= -0.5 - 1e-9))

    # Every vertex is the intersection of two active boundary constraints.
    for i, j in itertools.combinations(range(len(constraints)), 2):
        active = constraints[[i, j]]
        determinant = float(np.linalg.det(active))
        if abs(determinant) > 1e-12:
            point = np.linalg.solve(active, np.array([-0.5, -0.5]))
            if is_feasible(point):
                candidates.append(point)

    # The unconstrained stationary point, when the Hessian is nonsingular.
    hessian = 2.0 * _PSI * matrix
    determinant = float(np.linalg.det(hessian))
    scale = max(1.0, float(np.linalg.norm(hessian, ord=np.inf)))
    if abs(determinant) > 1e-14 * scale * scale:
        point = np.linalg.solve(hessian, -linear)
        if is_feasible(point):
            candidates.append(point)

    # The maximum on each straight edge is its one-dimensional stationary
    # point when concave; endpoint optima are already among the vertices.
    for normal in constraints:
        origin = -0.5 * normal / float(normal @ normal)
        tangent = np.array([-normal[1], normal[0]], dtype=np.float64)
        quadratic = _PSI * float(tangent @ matrix @ tangent)
        slope = 2.0 * _PSI * float(tangent @ matrix @ origin) + float(linear @ tangent)
        if quadratic < -1e-14:
            point = origin - (slope / (2.0 * quadratic)) * tangent
            if is_feasible(point):
                candidates.append(point)

    if not candidates:
        raise ArithmeticError("Could not enumerate a feasible MOPE QP optimum")

    def objective(point: FloatArray) -> float:
        return _PSI * float(point @ matrix @ point) + float(linear @ point)

    return np.asarray(max(candidates, key=objective), dtype=np.float64)
