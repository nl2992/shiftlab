"""Native fixed-question predictor/query parity, before delayed efficacy studies."""

import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from scripts.exhaustive_evaluation.smoke_author_rcps import load_author_simulation
from shiftlab.sota_search.active_rcps_learning import (
    FixedRiskPredictor,
    QueryNormalizer,
    fixed_question_features,
)

ROOT = Path(__file__).resolve().parents[2]


class FixedQuestion:
    curbeta = (0.5, 0.5, 0)
    _q_min = 0.05

    def addobs(self, **_kwargs):
        pass

    def update_q_min(self, _value):
        pass


def main():
    load_author_simulation()
    from Features import sim_featurize
    from OnlineMinimax import WindowedBeTheLeader
    from Player import RiskPredictorPolicyPrimalPlayer
    from Predictor import LinearRiskPredictor

    knots = torch.linspace(0, 1, 3)

    def make_predictor(column):
        return LinearRiskPredictor(
            beta_knots=knots,
            risk_knots=knots,
            featurize_fn=lambda p, b: sim_featurize(p, b, knots, knots),
            risk_fn=lambda observation, betas: observation[1].reshape(-1).expand(len(betas)),
            pretr_fn=lambda features, betas: features[0][0, column].expand(
                torch.as_tensor(betas).numel()
            ),
            n_beta_min=0.5,
            n_beta_max=0.5,
            n_betas=1,
        )

    native_mean, native_var = make_predictor(0), make_predictor(1)
    native = RiskPredictorPolicyPrimalPlayer(
        var_predictor=native_var,
        cv_predictor=native_mean,
        q_min=0.05,
        target_rate=0.2,
        iwmart=FixedQuestion(),
    )
    dual = WindowedBeTheLeader(max_dual=1 - np.log(2), window_size=256)
    mean, variance, norm = FixedRiskPredictor(1), FixedRiskPredictor(1), QueryNormalizer(1)
    rng = np.random.default_rng(202652000)
    errors = {k: 0.0 for k in ["q", "cv", "mean_weights", "variance_weights", "normalizer"]}
    for t in range(160):
        guesses = rng.random(2)
        risk = float(rng.random())
        observation = (
            (torch.tensor(guesses[None, :]), torch.zeros((1, 1))),
            torch.tensor([[risk]]),
        )
        prediction, cons = native.predict(observation)
        fm, fv = fixed_question_features(guesses[:1]), fixed_question_features(guesses[1:])
        q, raw, inverse = norm.predict(variance.predict(fv))
        cv = mean.predict(fm)
        errors["q"] = max(errors["q"], abs(float(prediction[0].detach()[0]) - q[0]))
        errors["cv"] = max(errors["cv"], abs(float(prediction[2].reshape(-1)[0]) - cv[0]))
        # Replay identical externally chosen query indicators; sampling coins are not optimizer inputs.
        query = bool(rng.random() < 0.4)
        d = dual.predict(-cons)
        dual.update(-cons)
        native.update(observation, (prediction[0], torch.tensor([float(query)]), prediction[2]), d)
        norm.update(q, raw, inverse, np.ones(1, dtype=bool))
        mean.update(fm, np.array([risk]), np.array([query]))
        variance.update(fv, np.array([risk]), np.array([query]))
        for key, model, native_model in [
            ("mean_weights", mean, native_mean),
            ("variance_weights", variance, native_var),
        ]:
            expected = np.r_[
                native_model._linear.weight.detach().numpy().ravel(),
                native_model._linear.bias.detach().numpy(),
            ]
            errors[key] = max(
                errors[key], float(np.max(np.abs(model.optimizer.value[0] - expected)))
            )
        errors["normalizer"] = max(
            errors["normalizer"],
            abs(norm.optimizer.value[0] - float(native._norm_const.detach()[0])),
        )
        assert max(errors.values()) < 1e-10, (t, errors)
    result = {
        "status": "passed",
        "updates": 160,
        "maximum_errors": errors,
        "scope": "source-as-written fixed beta=.5 with three knots; query/CV and learning/normalization parity, not grid inversion or delayed theorem",
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in [
                "src/shiftlab/sota_search/active_rcps_learning.py",
                "scripts/exhaustive_evaluation/check_learned_rcps_parity.py",
                "outputs/exhaustive_evaluation/active-rcps-compat/Predictor.py",
                "outputs/exhaustive_evaluation/active-rcps/Player.py",
            ]
        },
    }
    output = ROOT / "docs/exhaustive_evaluation/learned_rcps_component_parity_v2.json"
    if output.exists():
        raise FileExistsError("retain original parity evidence")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
