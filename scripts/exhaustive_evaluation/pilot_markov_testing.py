"""Small native notebook-function pilot and exact skipped-transition diagnostic."""

import ast
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.linalg import eig
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    notebook = ROOT / "outputs/exhaustive_evaluation/markov_testing/G3_ParametricFamily.ipynb"
    output = DOC / "markov_native_pilot_results.json"
    registration = DOC / "markov_native_pilot_registration.json"
    if registration.exists():
        raise FileExistsError("retain pilot; inspect existing process before restart")
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "author_commit": "9414edf5938127c80544261212e28b95a4ffc287",
        "scope": "native function reduced2-state pilot, not paper-scale reproduction or selective-label switching adaptation",
        "seeds": [17, 29, 43],
        "null_theta": 0.6,
        "alternative_theta": -0.6,
        "null_family": [0.4, 0.8],
        "alpha": 0.05,
        "horizon": 2000,
        "source_sha256": hashlib.sha256(notebook.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    registration.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    cells = json.loads(notebook.read_text())["cells"]
    nodes = []
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        try:
            tree = ast.parse("".join(cell["source"]))
        except SyntaxError:
            continue
        nodes += [
            n
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))
            and n.name in ["build_P_theta", "SequentialMarkovChainTest"]
        ]
    assert len(nodes) == 2
    namespace = {"np": np, "eig": eig, "minimize_scalar": minimize_scalar}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(notebook), "exec"), namespace)  # noqa: S102 -- pinned inspected author functions only.
    build = namespace["build_P_theta"]
    test_class = namespace["SequentialMarkovChainTest"]
    base = np.array([[0.8, 0.2], [0.3, 0.7]])
    feature = np.array([-1.0, 1.0])
    rows = []
    for label, theta in [("null", 0.6), ("alternative", -0.6)]:
        transition, _, _ = build(theta, base, feature)
        assert np.all(transition > 0)
        np.testing.assert_allclose(transition.sum(1), 1)
        for seed in reg["seeds"]:
            rng = np.random.default_rng(seed)
            state = int(rng.integers(2))
            test = test_class(
                m=2, alpha=0.05, theta_bounds=(0.4, 0.8), P0=base, f=feature, build_P_theta=build
            )
            stopped = False
            for t in range(1, 2001):
                next_state = int(rng.choice(2, p=transition[state]))
                stopped, lt, bound, fit = test.step(state, next_state)
                state = next_state
                assert np.isfinite([lt, bound, fit]).all()
                if stopped:
                    break
            assert test.Nxy.sum() == t
            rows.append(
                {
                    "case": label,
                    "seed": seed,
                    "stopped": bool(stopped),
                    "transitions": t,
                    "statistic": float(lt),
                    "threshold": float(bound),
                    "fitted_null_theta": float(fit),
                }
            )
        print(label, "three native paths complete", flush=True)
    # Constant gaps change the observed kernel; a hidden non-lumpable aggregation
    # is another reason a loss sequence need not be the fully observed chain.
    p = np.array([[0.9, 0.1], [0.2, 0.8]])
    p2 = p @ p
    assert not np.allclose(p, p2)
    hidden = np.array([[0.8, 0.1, 0.1], [0.1, 0.2, 0.7], [0.2, 0.3, 0.5]])
    assert hidden[0, 2] != hidden[1, 2]
    result = {
        "status": "completed",
        "rows": rows,
        "skipped_transition_check": {
            "P": p.tolist(),
            "P_squared": p2.tolist(),
            "max_difference": float(np.max(np.abs(p - p2))),
            "meaning": "observing every second state gives P^2, not P; known fixed gaps can be modeled explicitly",
        },
        "non_lumpable_loss_aggregation": {
            "matrix": hidden.tolist(),
            "aggregation": "states0,1 map loss0; state2 maps loss1",
            "next_loss1_given_hidden0": float(hidden[0, 2]),
            "next_loss1_given_hidden1": float(hidden[1, 2]),
            "meaning": "same observed loss can conceal states with different next-loss laws; no guaranteed homogeneous Markov loss process",
        },
        "limits": "six paths cannot validate alpha or asymptotic efficiency; no general theorem refutation",
    }
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
