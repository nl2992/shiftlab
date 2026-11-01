"""Run the author's six-arm simulation function unchanged, with type compatibility.

Extract its original function AST so unused CLI/plot/data-download imports are
not required. This is an original-function smoke test, not a paper-scale run.
"""

import ast
import hashlib
import json
import shutil
import sys
from copy import copy
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def load_author_simulation():
    source = ROOT / "outputs/exhaustive_evaluation/active-rcps"
    predictor_text = (source / "Predictor.py").read_text()
    try:
        ast.parse(predictor_text)
    except SyntaxError as exc:
        failure = {
            "status": "unmodified_author_code_syntax_error",
            "file": "Predictor.py",
            "line": exc.lineno,
            "message": str(exc),
            "source_commit": "a67f85d603df2bb3e32ef007f445191923ebd990",
        }
        failure_path = DOC / "author_rcps_unmodified_failure.json"
        if not failure_path.exists():
            failure_path.write_text(json.dumps(failure, indent=2), encoding="utf-8")
    compatibility = ROOT / "outputs/exhaustive_evaluation/active-rcps-compat"
    if not compatibility.exists():
        shutil.copytree(
            source,
            compatibility,
            ignore=shutil.ignore_patterns(".git", "data", "figures", "__pycache__"),
        )
        assert predictor_text.count("self._beta_knots. if") == 1
        repaired = predictor_text.replace("self._beta_knots. if", "self._beta_knots if")
        (compatibility / "Predictor.py").write_text(repaired, encoding="utf-8")
    sys.path.insert(0, str(compatibility))
    import IwUpperMartingale as mart
    from cocob import COCOB
    from Features import sim_featurize
    from LogisticRegression import DummyRegressor, MultilabelRegressor
    from OnlineMinimax import OnlineMinimax, WindowedBeTheLeader
    from Player import Player
    from Predictor import FalsePositivePredictor, LinearRiskPredictor
    from Risk import FalsePositiveRho

    # LinearRiskPredictor is defined in Predictor in this upstream revision.
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(1)
    original = mart.PartialIwUpperMartingale.ximin

    def compatible(self, betas):
        return np.asarray(original(self, betas))

    mart.PartialIwUpperMartingale.ximin = compatible
    text = (source / "simulation.py").read_text()
    function = next(
        n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "test_once"
    )
    namespace = {
        "np": np,
        "torch": torch,
        "copy": copy,
        "tqdm": tqdm,
        "COCOB": COCOB,
        "sim_featurize": sim_featurize,
        "DummyRegressor": DummyRegressor,
        "LinearRiskPredictor": LinearRiskPredictor,
        "MultilabelRegressor": MultilabelRegressor,
        "OnlineMinimax": OnlineMinimax,
        "WindowedBeTheLeader": WindowedBeTheLeader,
        "Player": Player,
        "FalsePositivePredictor": FalsePositivePredictor,
        "FalsePositiveRho": FalsePositiveRho,
        "PartialIwUpperMartingale": mart.PartialIwUpperMartingale,
        "FullyObservedUpperMartingale": mart.FullyObservedUpperMartingale,
    }
    exec(  # noqa: S102 -- explicitly requested execution of pinned, inspected author function.
        compile(
            ast.Module(body=[function], type_ignores=[]), str(source / "simulation.py"), "exec"
        ),
        namespace,
    )
    return namespace["test_once"], source


def main():
    test_once, source = load_author_simulation()
    reg = {
        "seed": 17,
        "label_ct": 20,
        "theta": 0.05,
        "q_min": 0.1,
        "target_rate": 0.3,
        "beta_dim": 3,
        "est_loss_dim": 3,
    }
    record = {
        "status": "registered",
        "parameters": reg,
        "source_commit": "a67f85d603df2bb3e32ef007f445191923ebd990",
        "simulation_sha256": hashlib.sha256((source / "simulation.py").read_bytes()).hexdigest(),
        "scope": "author six-arm function with declared syntax/type repairs; not unmodified reproduction or cost-risk adaptation",
        "repairs": [
            "remove dangling dot in add_pretrain branch (False for every tested arm)",
            "convert ximin return to numpy for modern numpy/torch assert interoperability",
        ],
    }
    output = DOC / "author_rcps_six_arm_smoke.json"
    if output.exists():
        raise FileExistsError("retain existing smoke artifact")
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    try:
        result = test_once(**reg)
        record["status"] = "completed"
        record["arms"] = [
            {
                "name": name,
                "labels": float(agent._primal_player._suml),
                "final_beta": float(betas[-1]),
                "data_points": int(data[-1]),
            }
            for name, agent, labels, betas, data in zip(*result, strict=True)
        ]
        assert len(record["arms"]) == 6
        assert all(a["labels"] >= reg["label_ct"] for a in record["arms"])
    except Exception as exc:
        record.update(status="failed", exception_type=type(exc).__name__, error=str(exc))
        output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        raise
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
