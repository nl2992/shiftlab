"""Fit frozen MN-DS model pairs and report validation eligibility only.

The one MN-DS test record previewed during schema inspection (data_id 1809) is explicitly
excluded from all later test replay. This script never computes test-period model losses.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/raw/chronological_news_transfer_20261106/mn_ds_news_classification.csv"
RAW_DIR = ROOT / "data/raw/chronological_news_transfer_20261106/mn_ds_zenodo_7394851"
RUN_DIR = (
    ROOT
    / "research/scoped_method/pilots/chronological_news_transfer_20261106/run/mn_ds_zenodo_7394851"
)
WINDOWS = {
    "incumbent": ("2019-01-01", "2019-04-01"),
    "challenger": ("2019-04-01", "2019-07-01"),
    "validation": ("2019-07-01", "2019-10-01"),
}
SEED = 2026110641


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_development_rows() -> pd.DataFrame:
    """Keep only pre-test rows; do not retain or summarize test targets."""
    chunks = []
    for chunk in pd.read_csv(
        ARCHIVE,
        usecols=["data_id", "id", "published_utc", "source", "title", "category_level_1"],
        chunksize=2000,
        dtype={"data_id": str, "id": str, "source": str, "title": str},
    ):
        ts = pd.to_datetime(
            pd.to_numeric(chunk["published_utc"], errors="coerce"), unit="s", utc=True
        )
        keep = (ts >= "2019-01-01") & (ts < "2019-10-01")
        dev = chunk.loc[keep].copy()
        dev["_time"] = ts.loc[keep]
        chunks.append(dev.dropna(subset=["_time", "title", "category_level_1", "source"]))
    rows = pd.concat(chunks, ignore_index=True)
    return rows.sort_values(["_time", "data_id"], kind="stable").reset_index(drop=True)


def fit_pair(rows: pd.DataFrame) -> tuple[dict, list[str]]:
    start_classes = sorted(
        set(rows.loc[rows["_time"] < "2019-07-01", "category_level_1"].astype(str))
    )
    if len(start_classes) != 17:
        raise RuntimeError(
            f"expected 17 observed first-level training classes; found {len(start_classes)}"
        )
    code = {label: i for i, label in enumerate(start_classes)}
    models = {}
    for name in ("incumbent", "challenger"):
        start, end = WINDOWS[name]
        train = rows[(rows["_time"] >= start) & (rows["_time"] < end)]
        y = train["category_level_1"].astype(str).map(code).to_numpy(dtype=np.int8)
        if set(np.unique(y)) != set(range(len(start_classes))):
            raise RuntimeError(f"{name} train window does not contain all frozen classes")
        vectorizer = HashingVectorizer(
            n_features=2**18,
            ngram_range=(1, 2),
            lowercase=True,
            stop_words="english",
            alternate_sign=False,
            norm="l2",
        )
        classifier = SGDClassifier(loss="log_loss", penalty="l2", random_state=SEED)
        classifier.fit(vectorizer.transform(train["title"].astype(str)), y)
        models[name] = (vectorizer, classifier)
    return models, start_classes


def assess(models: dict, classes: list[str], rows: pd.DataFrame) -> dict:
    start, end = WINDOWS["validation"]
    valid = rows[(rows["_time"] >= start) & (rows["_time"] < end)].copy()
    x = valid["title"].astype(str).tolist()
    pred = np.column_stack(
        [models[k][1].predict(models[k][0].transform(x)) for k in ("incumbent", "challenger")]
    )
    y = (
        valid["category_level_1"]
        .astype(str)
        .map({label: i for i, label in enumerate(classes)})
        .to_numpy()
    )
    losses = (pred != y[:, None]).astype(np.int8)
    signed = losses[:, 0] - losses[:, 1]
    disagree = pred[:, 0] != pred[:, 1]
    blocks = np.array_split(np.arange(len(valid)), 3)
    block_adv = [float(signed[b].mean()) if len(b) else None for b in blocks]
    counts = valid["source"].value_counts().to_dict()
    sources = sorted(str(s) for s, n in counts.items() if n >= 100)
    conditional_adv = float(signed[disagree].mean()) if disagree.any() else None
    overall_adv = float(signed.mean()) if len(valid) else None
    checks = {
        "at_least_100_disagreements": int(disagree.sum()) >= 100,
        "overall_advantage_at_least_0_03": overall_adv is not None and overall_adv >= 0.03,
        "conditional_disagreement_advantage_at_least_0_20": conditional_adv is not None
        and conditional_adv >= 0.20,
        "challenger_better_in_at_least_2_of_3_blocks": sum(
            v is not None and v > 0 for v in block_adv
        )
        >= 2,
    }
    return {
        "source": "mn_ds_zenodo_7394851",
        "eligible": all(checks.values()),
        "checks": checks,
        "validation_rows": len(valid),
        "validation_disagreements": int(disagree.sum()),
        "validation_overall_error_advantage": overall_adv,
        "validation_conditional_disagreement_advantage": conditional_adv,
        "validation_block_advantages": block_adv,
        "publisher_clusters_frozen": sources,
        "n_frozen_classes": len(classes),
        "excluded_test_ids": ["1809"],
    }


def main() -> None:
    if not ARCHIVE.is_file():
        raise FileNotFoundError(ARCHIVE)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_development_rows()
    models, classes = fit_pair(rows)
    result = assess(models, classes, rows)
    eligibility_path = RUN_DIR / "source_eligibility.json"
    eligibility_path.write_text(json.dumps(result, indent=2) + "\n")
    model_path = RAW_DIR / "frozen_models.pkl"
    model_path.write_bytes(
        pickle.dumps({"models": models, "classes": classes}, protocol=pickle.HIGHEST_PROTOCOL)
    )
    manifest = {
        "stage": "pretest_validation_only",
        "dataset": "MN-DS v1, Zenodo 7394851",
        "source_url": "https://zenodo.org/records/7394851",
        "archive_sha256": sha256(ARCHIVE),
        "models_sha256": sha256(model_path),
        "eligibility_sha256": sha256(eligibility_path),
        "windows": WINDOWS,
        "excluded_test_data_id": "1809",
        "vectorizer": {"n_features": 2**18, "ngram_range": [1, 2], "alternate_sign": False},
        "classifier": {
            "type": "SGDClassifier",
            "loss": "log_loss",
            "penalty": "l2",
            "random_state": SEED,
        },
        "validation": result,
    }
    (RUN_DIR / "pretest_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
