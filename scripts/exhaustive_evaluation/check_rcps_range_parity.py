"""Check fixed-question ranges, increments, FTL stakes and factors against author code."""

import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from scripts.exhaustive_evaluation.smoke_author_rcps import load_author_simulation
from shiftlab.sota_search.active_rcps_learning import FixedRiskPredictor

ROOT = Path(__file__).resolve().parents[2]


class LowerPredictor:
    def __init__(self, minimum):
        self.minimum = minimum

    def min_val(self, betas):
        return np.full(np.shape(betas), self.minimum)

    def predict(self, _features, _beta):
        return self.value


def main():
    load_author_simulation()
    from Features import sim_featurize
    from IwUpperMartingale import PartialIwUpperMartingale
    from Predictor import LinearRiskPredictor

    rng = np.random.default_rng(202656000)
    knots = torch.linspace(0, 1, 3)
    native = LinearRiskPredictor(
        beta_knots=knots,
        risk_knots=knots,
        featurize_fn=lambda p, b: sim_featurize(p, b, knots, knots),
        risk_fn=lambda *_: torch.zeros(1),
        pretr_fn=lambda _p, b: torch.zeros(torch.as_tensor(b).numel()),
        n_beta_min=0.5,
        n_beta_max=0.5,
        n_betas=1,
    )
    port = FixedRiskPredictor(1)
    errors = {
        k: 0.0
        for k in ["predictor_min", "predictor_max", "stake_cap", "increment", "ftl_stake", "factor"]
    }
    for _ in range(200):
        weights = rng.normal(0, 0.3, 13)
        port.optimizer.value[0] = weights
        native._linear.weight.data.copy_(torch.tensor(weights[:12].reshape(1, 12)))
        native._linear.bias.data.copy_(torch.tensor(weights[12:]))
        # Reconstruct the native bound state exactly as LinearRiskPredictor.update.
        reshape = native._linear.weight.data.reshape(4, 3)
        y_knots = reshape[-1].reshape(1, -1) + reshape[:-1] + native._linear.bias.data
        native._beta_mins = y_knots.min(dim=1).values
        native._beta_maxes = y_knots.max(dim=1).values
        lower, upper = port.bounds()
        errors["predictor_min"] = max(
            errors["predictor_min"], abs(lower[0] - float(native.min_val(0.5)))
        )
        errors["predictor_max"] = max(
            errors["predictor_max"], abs(upper[0] - float(native.max_val(0.5)))
        )
        floor = float(rng.uniform(0.05, 1))
        theta = 0.495
        cmin = float(lower[0])
        predictor = LowerPredictor(cmin)
        mart = PartialIwUpperMartingale(
            rho=lambda observation, betas: torch.full(tuple(betas.shape), observation[1]),
            q_min=floor,
            theta=theta,
            cv_predictor=predictor,
            n_betas=2,
            n_beta_min=0.5,
            alpha=0.05,
        )
        minimum = theta + (1 / floor - 1) * cmin - 1 / floor
        cap = 0.5 / abs(minimum)
        expected_cap = float(np.asarray(mart._maxlam(np.array([0.5])))[0])
        errors["stake_cap"] = max(errors["stake_cap"], abs(cap - expected_cap))
        q = float(rng.uniform(floor, 1))
        cv = float(rng.uniform(cmin, 1))
        risk = float(rng.random())
        label = int(rng.random() < q)
        observation = ((None, None), risk)
        predictor.value = cv
        xi = theta - cv + label / q * (cv - risk)
        native_xi = float(np.asarray(mart.xi(observation, q, label, np.array([0.5]), cv))[0])
        errors["increment"] = max(errors["increment"], abs(xi - native_xi))
        # Let original addobs update FTL; zero initial stake makes this first factor1.
        mart.addobs(observation, q, label, predictor)
        one = xi
        raw = one / (one + one * one) if one + one * one != 0 else 0
        stake = float(np.clip(raw, 0, cap))
        errors["ftl_stake"] = max(errors["ftl_stake"], abs(stake - float(mart._curlam[0])))
        errors["factor"] = max(
            errors["factor"], abs((1 + stake * xi) - (1 + float(mart._curlam[0]) * native_xi))
        )
    assert max(errors.values()) < 1e-12, errors
    output = ROOT / "docs/exhaustive_evaluation/rcps_range_component_parity.json"
    if output.exists():
        raise FileExistsError("retain parity evidence")
    result = {
        "status": "passed",
        "random_states": 200,
        "maximum_errors": errors,
        "scope": "component formulas at fixed question; supplied fresh bounds; not native full-loop timing/grid parity",
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in [
                "src/shiftlab/sota_search/active_rcps_learning.py",
                "scripts/exhaustive_evaluation/check_rcps_range_parity.py",
                "outputs/exhaustive_evaluation/active-rcps/IwUpperMartingale.py",
            ]
        },
    }
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
