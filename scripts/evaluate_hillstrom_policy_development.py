"""Evaluate a fixed-horizon email-allocation policy on the Hillstrom RCT.

The runner writes aggregate metrics and provenance only. Raw customer records stay
under data/raw/ and are excluded from version control.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from torch import nn

NUMERIC_FEATURES = ["recency", "history", "mens", "womens", "newbie"]
CATEGORICAL_FEATURES = ["history_segment", "zip_code", "channel"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
OUTCOMES = ["spend", "conversion", "visit"]
EXPECTED_COLUMNS = [
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
]
ARM_WOMENS = "Womens E-Mail"
ARM_CONTROL = "No E-Mail"
ARM_MENS = "Mens E-Mail"
ARM_PROBABILITY = 1.0 / 3.0
CAPACITY = 10_000 / 64_000
COST_GRID = [0.0, 0.05, 0.10, 0.25, 0.50, 1.00]
PRIMARY_COST = 0.25


class OutcomeMLP(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.layers(values).squeeze(-1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/raw/hillstrom/hillstrom_email_challenge_2008.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "outputs/shiftguard_unified/real_data_development/hillstrom_email_policy_v3_20261026"
        ),
    )
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--patience", type=int, default=12)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_frame(frame: pd.DataFrame) -> None:
    if list(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected Hillstrom schema; expected columns in source order: {EXPECTED_COLUMNS}"
        )
    if len(frame) != 64_000:
        raise ValueError(f"Expected 64,000 records, observed {len(frame)}")
    if frame.isna().any().any():
        raise ValueError("Hillstrom source contains missing cells")
    if set(frame["segment"].unique()) != {ARM_MENS, ARM_WOMENS, ARM_CONTROL}:
        raise ValueError("Unexpected randomized assignment labels")
    for name in ["mens", "womens", "newbie", "conversion", "visit"]:
        if not set(frame[name].unique()).issubset({0, 1}):
            raise ValueError(f"{name} must be binary")
    if (frame["spend"] < 0).any() or not np.isfinite(frame["spend"]).all():
        raise ValueError("spend must be finite and non-negative")


def split_indices(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    permutation = np.random.default_rng(seed).permutation(n)
    n_train = int(n * 0.50)
    n_dev = int(n * 0.20)
    return (
        permutation[:n_train],
        permutation[n_train : n_train + n_dev],
        permutation[n_train + n_dev :],
    )


def build_transformer(train: pd.DataFrame) -> ColumnTransformer:
    transformer = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    transformer.fit(train[FEATURES])
    return transformer


def _train_arm_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_dev: np.ndarray,
    y_dev: np.ndarray,
    *,
    device: torch.device,
    seed: int,
    epochs: int,
    patience: int,
) -> tuple[OutcomeMLP, int, float]:
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = OutcomeMLP(x_train.shape[1]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.MSELoss()
    x_train_t = torch.as_tensor(x_train, dtype=torch.float32, device=device)
    y_train_t = torch.as_tensor(y_train, dtype=torch.float32, device=device)
    x_dev_t = torch.as_tensor(x_dev, dtype=torch.float32, device=device)
    y_dev_t = torch.as_tensor(y_dev, dtype=torch.float32, device=device)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    batch_size = min(1024, len(x_train))
    best_loss = math.inf
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None
    stale = 0

    for epoch in range(1, epochs + 1):
        model.train()
        order = torch.randperm(len(x_train_t), generator=generator)
        for batch_start in range(0, len(order), batch_size):
            indices = order[batch_start : batch_start + batch_size].to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(x_train_t[indices]), y_train_t[indices])
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            dev_loss = float(loss_fn(model(x_dev_t), y_dev_t).item())
        if dev_loss < best_loss - 1e-8:
            best_loss = dev_loss
            best_epoch = epoch
            best_state = {
                key: value.detach().cpu().clone() for key, value in model.state_dict().items()
            }
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break

    if best_state is None:
        raise RuntimeError("Outcome model did not produce a finite development loss")
    model.load_state_dict(best_state)
    model.eval()
    return model, best_epoch, best_loss


def predict(model: OutcomeMLP, x: np.ndarray, device: torch.device) -> np.ndarray:
    with torch.no_grad():
        values = torch.as_tensor(x, dtype=torch.float32, device=device)
        return model(values).detach().cpu().numpy()


def make_capacity_policy(scores: np.ndarray, capacity: float) -> np.ndarray:
    n_treat = round(len(scores) * capacity)
    policy = np.zeros(len(scores), dtype=np.float64)
    if n_treat:
        chosen = np.argsort(-scores, kind="stable")[:n_treat]
        policy[chosen] = 1.0
    return policy


def ipw_policy_score(
    assignment: np.ndarray,
    outcome: np.ndarray,
    policy_probability: np.ndarray,
) -> np.ndarray:
    """IPW value score for Women's email vs no email in the three-arm RCT."""
    womens = assignment == ARM_WOMENS
    control = assignment == ARM_CONTROL
    return (
        womens * policy_probability * outcome / ARM_PROBABILITY
        + control * (1.0 - policy_probability) * outcome / ARM_PROBABILITY
    )


def estimate_policy(
    *,
    name: str,
    assignment: np.ndarray,
    outcomes: dict[str, np.ndarray],
    policy_probability: np.ndarray,
    cost: float,
) -> dict[str, float | str]:
    intensity = float(np.mean(policy_probability))
    score_spend = ipw_policy_score(assignment, outcomes["spend"], policy_probability)
    net_score = score_spend - cost * policy_probability
    n = len(assignment)
    mean = float(np.mean(net_score))
    se = float(np.std(net_score, ddof=1) / math.sqrt(n))
    return {
        "policy": name,
        "cost_per_email_usd": cost,
        "email_rate": intensity,
        "gross_spend_value_per_customer": float(np.mean(score_spend)),
        "imposed_cost_per_customer": cost * intensity,
        "net_value_per_customer": mean,
        "net_value_se": se,
        "net_value_ci95_low": mean - 1.96 * se,
        "net_value_ci95_high": mean + 1.96 * se,
        "conversion_value_per_customer": float(
            np.mean(ipw_policy_score(assignment, outcomes["conversion"], policy_probability))
        ),
        "visit_value_per_customer": float(
            np.mean(ipw_policy_score(assignment, outcomes["visit"], policy_probability))
        ),
    }


def paired_net_contrast(
    *,
    policy_a_name: str,
    policy_b_name: str,
    assignment: np.ndarray,
    spend: np.ndarray,
    policy_a: np.ndarray,
    policy_b: np.ndarray,
    cost: float,
) -> dict[str, float | str | int]:
    score_a = ipw_policy_score(assignment, spend, policy_a) - cost * policy_a
    score_b = ipw_policy_score(assignment, spend, policy_b) - cost * policy_b
    paired = score_a - score_b
    estimate = float(np.mean(paired))
    standard_error = float(np.std(paired, ddof=1) / math.sqrt(len(paired)))
    return {
        "policy_a": policy_a_name,
        "policy_b": policy_b_name,
        "cost_per_email_usd": cost,
        "paired_net_value_difference_per_customer": estimate,
        "standard_error": standard_error,
        "ci95_low": estimate - 1.96 * standard_error,
        "ci95_high": estimate + 1.96 * standard_error,
        "evaluation_rows": len(paired),
    }


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    source_path = args.data.resolve()
    output_path = args.output.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was explicitly requested but is unavailable")
    device_name = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device_name == "auto":
        device_name = "cpu"
    device = torch.device(device_name)

    frame = pd.read_csv(source_path)
    validate_frame(frame)
    train_idx, dev_idx, eval_idx = split_indices(len(frame), args.seed)
    train = frame.iloc[train_idx].reset_index(drop=True)
    dev = frame.iloc[dev_idx].reset_index(drop=True)
    evaluation = frame.iloc[eval_idx].reset_index(drop=True)

    transform = build_transformer(train)
    x_train = transform.transform(train[FEATURES]).astype(np.float32)
    x_dev = transform.transform(dev[FEATURES]).astype(np.float32)
    x_eval = transform.transform(evaluation[FEATURES]).astype(np.float32)
    policy_arm_train = train["segment"].isin([ARM_WOMENS, ARM_CONTROL])
    policy_arm_spend = train.loc[policy_arm_train, "spend"]
    y_center = float(policy_arm_spend.mean())
    y_scale = float(policy_arm_spend.std(ddof=0))
    if not np.isfinite(y_scale) or y_scale <= 0:
        raise ValueError("Training spend scale must be positive and finite")

    train_w = train["segment"].to_numpy() == ARM_WOMENS
    train_c = train["segment"].to_numpy() == ARM_CONTROL
    dev_w = dev["segment"].to_numpy() == ARM_WOMENS
    dev_c = dev["segment"].to_numpy() == ARM_CONTROL
    models: dict[str, OutcomeMLP] = {}
    training_details: dict[str, dict[str, float | int]] = {}
    for arm, train_mask, dev_mask in [
        ("womens", train_w, dev_w),
        ("control", train_c, dev_c),
    ]:
        model, best_epoch, best_dev_mse = _train_arm_model(
            x_train[train_mask],
            ((train.loc[train_mask, "spend"].to_numpy(dtype=np.float32) - y_center) / y_scale),
            x_dev[dev_mask],
            ((dev.loc[dev_mask, "spend"].to_numpy(dtype=np.float32) - y_center) / y_scale),
            device=device,
            seed=args.seed + (0 if arm == "womens" else 1),
            epochs=args.epochs,
            patience=args.patience,
        )
        models[arm] = model
        training_details[arm] = {
            "training_rows": int(np.sum(train_mask)),
            "development_rows": int(np.sum(dev_mask)),
            "best_epoch": best_epoch,
            "best_standardized_mse": best_dev_mse,
        }

    mu_w = predict(models["womens"], x_eval, device) * y_scale + y_center
    mu_c = predict(models["control"], x_eval, device) * y_scale + y_center
    uplift = mu_w - mu_c

    ridge_models: dict[str, Ridge] = {}
    ridge_details: dict[str, dict[str, float]] = {}
    for arm, train_mask, dev_mask in [
        ("womens", train_w, dev_w),
        ("control", train_c, dev_c),
    ]:
        arm_y_train = (
            train.loc[train_mask, "spend"].to_numpy(dtype=np.float64) - y_center
        ) / y_scale
        arm_y_dev = (dev.loc[dev_mask, "spend"].to_numpy(dtype=np.float64) - y_center) / y_scale
        candidates: list[tuple[float, float, Ridge]] = []
        for alpha in [0.1, 1.0, 10.0, 100.0]:
            candidate = Ridge(alpha=alpha)
            candidate.fit(x_train[train_mask], arm_y_train)
            dev_prediction = candidate.predict(x_dev[dev_mask])
            dev_mse = float(np.mean((dev_prediction - arm_y_dev) ** 2))
            candidates.append((dev_mse, alpha, candidate))
        best_mse, best_alpha, best_model = min(candidates, key=lambda item: item[0])
        ridge_models[arm] = best_model
        ridge_details[arm] = {
            "selected_alpha": best_alpha,
            "development_standardized_mse": best_mse,
        }
    ridge_uplift = (
        ridge_models["womens"].predict(x_eval) - ridge_models["control"].predict(x_eval)
    ) * y_scale
    history_policy = make_capacity_policy(evaluation["history"].to_numpy(), CAPACITY)
    uplift_policy = make_capacity_policy(uplift, CAPACITY)
    ridge_policy = make_capacity_policy(ridge_uplift, CAPACITY)
    policies = {
        "never_email": np.zeros(len(evaluation), dtype=np.float64),
        "email_all": np.ones(len(evaluation), dtype=np.float64),
        "random_10000_of_64000": np.full(len(evaluation), CAPACITY, dtype=np.float64),
        "history_top_capacity": history_policy,
        "tlearner_uplift_top_capacity": uplift_policy,
        "ridge_tlearner_uplift_top_capacity": ridge_policy,
    }
    assignment = evaluation["segment"].to_numpy()
    outcomes = {name: evaluation[name].to_numpy(dtype=np.float64) for name in OUTCOMES}

    rows: list[dict[str, Any]] = []
    for cost in COST_GRID:
        for name, policy in policies.items():
            rows.append(
                estimate_policy(
                    name=name,
                    assignment=assignment,
                    outcomes=outcomes,
                    policy_probability=policy,
                    cost=cost,
                )
            )
    metrics = pd.DataFrame(rows)

    contrast_rows: list[dict[str, float | str | int]] = []
    for cost in COST_GRID:
        for policy_name in [
            "email_all",
            "history_top_capacity",
            "tlearner_uplift_top_capacity",
            "ridge_tlearner_uplift_top_capacity",
        ]:
            contrast_rows.append(
                paired_net_contrast(
                    policy_a_name=policy_name,
                    policy_b_name="never_email",
                    assignment=assignment,
                    spend=outcomes["spend"],
                    policy_a=policies[policy_name],
                    policy_b=policies["never_email"],
                    cost=cost,
                )
            )
        for policy_name in [
            "history_top_capacity",
            "tlearner_uplift_top_capacity",
            "ridge_tlearner_uplift_top_capacity",
        ]:
            contrast_rows.append(
                paired_net_contrast(
                    policy_a_name=policy_name,
                    policy_b_name="random_10000_of_64000",
                    assignment=assignment,
                    spend=outcomes["spend"],
                    policy_a=policies[policy_name],
                    policy_b=policies["random_10000_of_64000"],
                    cost=cost,
                )
            )
    contrasts = pd.DataFrame(contrast_rows)

    candidate_score = ipw_policy_score(assignment, outcomes["spend"], uplift_policy)
    random_score = ipw_policy_score(
        assignment, outcomes["spend"], np.full(len(evaluation), CAPACITY)
    )
    primary_difference = candidate_score - random_score - PRIMARY_COST * (uplift_policy - CAPACITY)
    difference = float(np.mean(primary_difference))
    difference_se = float(np.std(primary_difference, ddof=1) / math.sqrt(len(evaluation)))
    primary = {
        "contrast": "tlearner_uplift_top_capacity_minus_random_capacity",
        "outcome": "net spend per customer (USD) under imposed $0.25/email cost",
        "mean_difference": difference,
        "standard_error": difference_se,
        "ci95_low": difference - 1.96 * difference_se,
        "ci95_high": difference + 1.96 * difference_se,
        "test_rows": len(evaluation),
        "independent_unit_assumption": "one randomized customer per source row",
    }

    output_path.mkdir(parents=True)
    metrics.to_csv(output_path / "policy_metrics.csv", index=False)
    contrasts.to_csv(output_path / "paired_contrasts.csv", index=False)
    (output_path / "primary_contrast.json").write_text(
        json.dumps(primary, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "protocol_id": "hillstrom_email_policy_v3_exploratory",
        "status": "exploratory single-source development; this split was exposed by earlier runs",
        "source": {
            "publisher": "MineThatData / Kevin Hillstrom",
            "official_challenge_page": "https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html",
            "download_url": "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv",
            "local_raw_file": "data/raw/hillstrom/hillstrom_email_challenge_2008.csv",
            "sha256": sha256_file(source_path),
            "bytes": source_path.stat().st_size,
            "rows": len(frame),
            "license_note": "Publicly offered for the 2008 research challenge; no explicit modern license identified. Raw file is local-only and not committed.",
        },
        "task": {
            "unit": "customer",
            "action": "assign Women's email versus no email",
            "outcome_window": "two weeks after the campaign, per publisher description",
            "primary_outcome": "gross spend in USD",
            "secondary_outcomes": ["conversion", "visit"],
            "decision_cost": "research-imposed sensitivity grid; not an observed email cost or profit",
            "features": FEATURES,
            "assignment_propensity_assumption": 1.0 / 3.0,
            "policy_capacity_fraction": CAPACITY,
            "policy_capacity_source": "10,000 of 64,000 customers, as a fixed benchmark constraint",
        },
        "split": {
            "seed": args.seed,
            "row_index_permutation": "NumPy default_rng(seed)",
            "train_fraction": 0.50,
            "development_fraction": 0.20,
            "evaluation_fraction": 0.30,
            "train_rows": len(train),
            "development_rows": len(dev),
            "evaluation_rows": len(evaluation),
            "evaluation_exposed_to_prior_method_development": True,
            "prior_runs_on_same_split": [
                "hillstrom_email_policy_v1_20261026",
                "hillstrom_email_policy_v2_20261026",
            ],
        },
        "method": {
            "candidates": [
                "separate-arm two-model MLP trained on spend; rank predicted incremental spend; target fixed capacity",
                "separate-arm ridge T-learner; alpha selected from [0.1, 1, 10, 100] on development split; rank predicted incremental spend",
            ],
            "baselines": list(policies),
            "estimator": "three-arm Horvitz-Thompson policy value with 1/3 randomized assignment probabilities",
            "uncertainty": "paired row-level influence-score Wald interval; assumes independent customers and the stated randomization design",
            "cost_grid_usd_per_email": COST_GRID,
            "primary_cost_usd_per_email": PRIMARY_COST,
            "primary_comparison": primary["contrast"],
        },
        "execution": {
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_device": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
            "training_details": training_details,
            "ridge_development_details": ridge_details,
            "elapsed_seconds": time.perf_counter() - started,
            "completed_at_utc": datetime.now(UTC).isoformat(),
        },
        "artifacts": {
            "policy_metrics.csv": sha256_file(output_path / "policy_metrics.csv"),
            "paired_contrasts.csv": sha256_file(output_path / "paired_contrasts.csv"),
            "primary_contrast.json": sha256_file(output_path / "primary_contrast.json"),
        },
        "limitations": [
            "This is a retrospective fixed-horizon randomized allocation study, not sequential monitoring or delayed feedback.",
            "The two-week outcome period is not an individual label-release timestamp.",
            "Email costs are imposed scenarios; spend is observed gross customer spend, not profit.",
            "The source is openly offered for a research challenge but no explicit modern license was found; raw data is not redistributed.",
            "The result is development evidence on one source and cannot satisfy the two-family final confirmation gate.",
            "The current split was already inspected in v1 and is not an untouched confirmatory holdout.",
        ],
    }
    (output_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "output": str(output_path),
                "device": str(device),
                "rows": len(frame),
                "eval_rows": len(evaluation),
                "primary_contrast": primary,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
