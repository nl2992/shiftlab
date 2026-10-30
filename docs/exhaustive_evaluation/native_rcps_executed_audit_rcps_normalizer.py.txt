"""Check the source normalization gradient without modifying the author code."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]


class ConstantVariance:
    def __call__(self, _features, _beta):
        return torch.tensor([0.25], dtype=torch.float64)

    def update(self, _observation):
        pass

    def min_val(self, _beta):
        return torch.tensor(0.25, dtype=torch.float64)


class FixedQuestion:
    curbeta = (0.9, 0.8, 0)
    _q_min = 0.1

    def addobs(self, **_kwargs):
        pass

    def update_q_min(self, _value):
        pass


def main():
    vendor = ROOT / "outputs/exhaustive_evaluation/active-rcps"
    sys.path.insert(0, str(vendor))
    spec = importlib.util.spec_from_file_location("native_player_audit", vendor / "Player.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    torch.set_default_dtype(torch.float64)
    rows = []
    for dual in [0.0, 1 - np.log(2)]:
        player = module.RiskPredictorPolicyPrimalPlayer(
            var_predictor=ConstantVariance(), q_min=0.1, target_rate=0.3, iwmart=FixedQuestion()
        )
        observation = ((torch.zeros((1, 1)), torch.zeros((1, 1))), torch.zeros((1, 1)))
        torch.manual_seed(17)
        prediction, _ = player.predict(observation)
        q = float(prediction[0].detach()[0])
        player.update(observation, prediction, dual)
        actual = float(player._norm_const.grad[0])
        expected = -1 - dual * q
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
        rows.append(
            {
                "dual": float(dual),
                "q_before": q,
                "source_gradient": actual,
                "source_loss_derivative": expected,
                "negative_eq75_payoff_derivative": 1 - dual * q,
                "normalizer_parameter_after_one_step": float(player._norm_const.detach()[0]),
            }
        )
    result = {
        "status": "verified",
        "scope": "source gradient at unclipped q=.5; not a theorem refutation or corrected algorithm efficacy test",
        "rows": rows,
        "source_sha256": hashlib.sha256((vendor / "Player.py").read_bytes()).hexdigest(),
    }
    output = ROOT / "docs/exhaustive_evaluation/author_rcps_normalizer_audit.json"
    if output.exists():
        raise FileExistsError("retain existing audit evidence")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
