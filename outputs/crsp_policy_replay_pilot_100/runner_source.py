"""Run the frozen retrospective CRSP decision-policy pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import torch

from shiftlab.data.provenance import sha256, write_json

TRANSACTION_COST_BPS = (0, 5, 10, 25)
RETURN_CAP = 0.10
BOOTSTRAP_REPLICATES = 2_000
BLOCK_DAYS = 20


def _panel_path(root: Path, version: str | None) -> Path:
    base = root / "processed" / "crsp_ciz_next_day"
    if version:
        path = base / version
        if not (path / "dataset_manifest.json").is_file():
            raise FileNotFoundError(path)
        return path
    candidates = sorted(
        (p for p in base.iterdir() if p.is_dir() and (p / "dataset_manifest.json").exists()),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        raise FileNotFoundError(f"no CRSP CIZ panel under {base}")
    return candidates[-1]


def _sample_training_permnos(
    dataset: ds.Dataset, *, securities: int, seed: int, batch_size: int
) -> tuple[np.ndarray, int]:
    identifiers: set[int] = set()
    for batch in dataset.scanner(columns=["permno", "split"], batch_size=batch_size).to_batches():
        part = batch.to_pandas()
        train_ids = part.loc[part.split.eq("train"), "permno"].dropna().astype("int64")
        identifiers.update(train_ids.unique().tolist())
    available = np.asarray(sorted(identifiers), dtype=np.int64)
    if len(available) < 10:
        raise ValueError(f"only {len(available)} training PERMNOs found")
    rng = np.random.default_rng(seed)
    selected = np.sort(rng.choice(available, size=min(securities, len(available)), replace=False))
    return selected, len(available)


def _load_sample(
    dataset: ds.Dataset, selected: np.ndarray, *, batch_size: int
) -> pd.DataFrame:
    filt = ds.field("permno").isin(selected.tolist()) & ds.field("split").isin(["train", "test"])
    columns = ["permno", "split", "features", "target", "dlycaldt"]
    frames = [
        batch.to_pandas()
        for batch in dataset.scanner(columns=columns, filter=filt, batch_size=batch_size).to_batches()
    ]
    if not frames:
        raise ValueError("no train/test rows found for sampled training PERMNOs")
    frame = pd.concat(frames, ignore_index=True)
    frame["dlycaldt"] = pd.to_datetime(frame.dlycaldt, errors="raise")
    frame.sort_values(["permno", "dlycaldt"], kind="stable", inplace=True)
    if frame.duplicated(["permno", "dlycaldt"]).any():
        raise ValueError("duplicate PERMNO/date rows in sampled CRSP panel")
    return frame


def _impute_scale_fit(train_x: np.ndarray, train_y: np.ndarray) -> tuple[np.ndarray, ...]:
    medians = np.nanmedian(train_x, axis=0)
    medians[~np.isfinite(medians)] = 0.0
    imputed = np.where(np.isfinite(train_x), train_x, medians)
    means = imputed.mean(axis=0)
    scales = imputed.std(axis=0)
    scales[scales <= 1e-12] = 1.0
    return medians, means, scales, np.asarray([train_y.mean()], dtype=np.float64)


def _ridge_predictions(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    *,
    device: torch.device,
    alpha: float = 1.0,
) -> tuple[np.ndarray, str]:
    medians, means, scales, target_mean = _impute_scale_fit(train_x, train_y)
    x_train = np.where(np.isfinite(train_x), train_x, medians)
    x_test = np.where(np.isfinite(test_x), test_x, medians)
    dtype = torch.float64
    tx = torch.as_tensor((x_train - means) / scales, dtype=dtype, device=device)
    ty = torch.as_tensor(train_y - target_mean[0], dtype=dtype, device=device)
    vx = torch.as_tensor((x_test - means) / scales, dtype=dtype, device=device)
    gram = tx.T @ tx
    regularizer = torch.eye(gram.shape[0], dtype=dtype, device=device) * alpha
    coef = torch.linalg.solve(gram + regularizer, tx.T @ ty)
    predictions = (vx @ coef + target_mean[0]).detach().cpu().numpy()
    return predictions, "training-only median imputation, standardization, Ridge(alpha=1)"


def _turnover(actions: np.ndarray, frame: pd.DataFrame) -> np.ndarray:
    result = np.zeros(len(frame), dtype=np.float64)
    for indices in frame.groupby("permno", sort=False).indices.values():
        actions_for_name = actions[indices].astype(np.float64)
        prior = np.r_[0.0, actions_for_name[:-1]]
        result[indices] = np.abs(actions_for_name - prior)
        if len(indices):
            result[indices[-1]] += actions_for_name[-1]  # close each position at test end
    return result


def _block_interval(
    daily_sum: np.ndarray,
    daily_count: np.ndarray,
    *,
    seed: int,
) -> list[float]:
    n = len(daily_sum)
    if n < BLOCK_DAYS:
        raise ValueError(f"only {n} dates; need at least {BLOCK_DAYS} for block intervals")
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n / BLOCK_DAYS)
    offsets = np.arange(BLOCK_DAYS)
    means = np.empty(BOOTSTRAP_REPLICATES, dtype=np.float64)
    for i in range(BOOTSTRAP_REPLICATES):
        starts = rng.integers(0, n, size=n_blocks)
        idx = np.concatenate([(start + offsets) % n for start in starts])[:n]
        means[i] = daily_sum[idx].sum() / daily_count[idx].sum()
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def evaluate(
    *, root: Path, version: str | None, securities: int, seed: int, batch_size: int,
    device_name: str, output: Path,
) -> Path:
    path = _panel_path(root, version)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    manifest_path = path / "dataset_manifest.json"
    panel_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observations_path = path / "observations.parquet"
    expected_hash = panel_manifest["files"]["observations.parquet"]
    if sha256(observations_path) != expected_hash:
        raise ValueError("CRSP panel checksum does not match its dataset manifest")
    dataset = ds.dataset(observations_path, format="parquet")
    chosen, train_universe_size = _sample_training_permnos(
        dataset, securities=securities, seed=seed, batch_size=batch_size
    )
    frame = _load_sample(dataset, chosen, batch_size=batch_size)
    train = frame.loc[frame.split.eq("train")].copy()
    test = frame.loc[frame.split.eq("test")].copy()
    if min(len(train), len(test)) < 100:
        raise ValueError("sampled training-selected cohort has fewer than 100 train or test rows")

    names = panel_manifest["feature_names"]
    market_index = names.index("vwretd")
    x_train = np.stack(train.features.map(lambda x: np.asarray(x, dtype=np.float64)))
    x_test = np.stack(test.features.map(lambda x: np.asarray(x, dtype=np.float64)))
    y_train = pd.to_numeric(train.target, errors="raise").to_numpy(dtype=np.float64)
    y_test = pd.to_numeric(test.target, errors="raise").to_numpy(dtype=np.float64)
    resolved = torch.device(
        "cuda" if device_name == "auto" and torch.cuda.is_available() else
        "cpu" if device_name == "auto" else device_name
    )
    if resolved.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    prediction, model_spec = _ridge_predictions(
        x_train, y_train, x_test, device=resolved
    )
    mean_prediction = float(y_train.mean())
    test = test.copy()
    test["prediction"] = prediction
    test["candidate_action"] = (prediction > 0.0).astype(np.int8)
    test["reference_action"] = (x_test[:, market_index] > 0.0).astype(np.int8)
    test["clipped_return"] = np.clip(y_test, -RETURN_CAP, RETURN_CAP)
    test.sort_values(["permno", "dlycaldt"], kind="stable", inplace=True)
    test.reset_index(drop=True, inplace=True)
    candidate = test.candidate_action.to_numpy(dtype=np.int8)
    reference = test.reference_action.to_numpy(dtype=np.int8)
    cand_turnover = _turnover(candidate, test)
    ref_turnover = _turnover(reference, test)
    clipped = test.clipped_return.to_numpy(dtype=np.float64)
    years = test.dlycaldt.dt.year.to_numpy(dtype=int)
    dates = test.dlycaldt.to_numpy()

    cost_rows: list[dict[str, object]] = []
    yearly_rows: list[dict[str, object]] = []
    for bps in TRANSACTION_COST_BPS:
        fee = bps / 10_000.0
        candidate_cost = -candidate * clipped + fee * cand_turnover
        reference_cost = -reference * clipped + fee * ref_turnover
        difference = candidate_cost - reference_cost
        daily = pd.DataFrame({"date": dates, "difference": difference}).groupby(
            "date", sort=True
        ).difference.agg(["sum", "count"])
        interval = _block_interval(
            daily["sum"].to_numpy(dtype=np.float64),
            daily["count"].to_numpy(dtype=np.float64),
            seed=seed + 9_411 + bps,
        )
        cost_rows.append(
            {
                "transaction_cost_bps_per_turnover": bps,
                "n_test_events": len(test),
                "mean_candidate_cost": float(candidate_cost.mean()),
                "mean_reference_cost": float(reference_cost.mean()),
                "mean_candidate_minus_reference_cost": float(difference.mean()),
                "circular_20_day_block_interval_95": interval,
                "candidate_long_action_rate": float(candidate.mean()),
                "reference_long_action_rate": float(reference.mean()),
                "return_clipped_fraction": float(np.mean(np.abs(y_test) > RETURN_CAP)),
            }
        )
        for year in sorted(np.unique(years)):
            mask = years == year
            yearly_rows.append(
                {
                    "year": int(year),
                    "transaction_cost_bps_per_turnover": bps,
                    "n": int(mask.sum()),
                    "candidate_mean_cost": float(candidate_cost[mask].mean()),
                    "reference_mean_cost": float(reference_cost[mask].mean()),
                    "candidate_minus_reference_cost": float(difference[mask].mean()),
                }
            )

    report = {
        "experiment": "CRSP CIZ retrospective decision-policy pilot",
        "dataset": panel_manifest["dataset"],
        "dataset_version": panel_manifest["version"],
        "dataset_manifest_sha256": sha256(manifest_path),
        "observations_sha256": expected_hash,
        "seed": seed,
        "cohort_rule": "sample PERMNOs only from train-split identifiers; no test-presence condition",
        "training_universe_permnos": train_universe_size,
        "sampled_training_permnos": len(chosen),
        "test_permno_count": int(test.permno.nunique()),
        "train_rows": len(train),
        "test_rows": len(test),
        "train_dates": [str(train.dlycaldt.min().date()), str(train.dlycaldt.max().date())],
        "test_dates": [str(test.dlycaldt.min().date()), str(test.dlycaldt.max().date())],
        "model": model_spec,
        "model_device": str(resolved),
        "model_rmse": float(np.sqrt(np.mean((prediction - y_test) ** 2))),
        "training_mean_rmse": float(np.sqrt(np.mean((mean_prediction - y_test) ** 2))),
        "candidate_policy": "long if train-only Ridge prediction of next observed return is positive",
        "reference_policy": "long if same-date value-weighted CRSP market return (vwretd) is positive",
        "utility": {
            "definition": "negative long-action times next return clipped to [-0.10, +0.10], plus per-turnover charge",
            "return_cap": RETURN_CAP,
            "transaction_cost_bps": list(TRANSACTION_COST_BPS),
            "turnover": "entry, position changes, and terminal close within each sampled PERMNO test path",
        },
        "cost_comparison": cost_rows,
        "yearly_cost_comparison": yearly_rows,
        "uncertainty": {
            "method": "circular moving-block bootstrap of date-level paired cost sums/counts",
            "block_trading_dates": BLOCK_DAYS,
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": seed,
            "interpretation": "descriptive only; does not establish sequential validity or transport to a live market",
        },
        "limitations": [
            "Training-selected 100-PERMNO pilot is not representative inference over the CRSP universe.",
            "CRSP timestamps encode retrospective daily-close ordering, not verified historical publication times.",
            "Returns are dependent across securities and dates; block intervals do not prove e-process assumptions.",
            "The capped long-only utility and transaction costs are imposed sensitivity values, not a sourced trading-cost model.",
            "Results are retrospective diagnostics, not trading profitability or deployment evidence.",
        ],
        "script_sha256": sha256(Path(__file__)),
        "created_utc": datetime.now(UTC).isoformat(),
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "report.json", report)
    pd.DataFrame(cost_rows).to_csv(output / "cost_summary.csv", index=False)
    pd.DataFrame(yearly_rows).to_csv(output / "yearly_cost_summary.csv", index=False)
    checksums = []
    for artifact in sorted(output.iterdir()):
        if artifact.name != "checksums.sha256":
            checksums.append(f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}")
    (output / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--version")
    parser.add_argument("--securities", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--batch-size", type=int, default=200_000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--output", type=Path, default=Path("outputs/crsp_policy_replay_pilot_100"))
    args = parser.parse_args()
    if args.securities < 10 or args.batch_size < 1:
        parser.error("--securities must be at least 10 and batch size positive")
    evaluate(
        root=args.root,
        version=args.version,
        securities=args.securities,
        seed=args.seed,
        batch_size=args.batch_size,
        device_name=args.device,
        output=args.output,
    )


if __name__ == "__main__":
    main()
