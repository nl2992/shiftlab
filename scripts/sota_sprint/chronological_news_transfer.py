"""Prospective chronological news replay for the frozen PFA-SR transfer protocol.

`prepare` uses the registered training and validation windows only. `open-test` writes and
fsyncs a test-opening manifest before calculating any test losses or policy outcomes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import pickle
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/raw/chronological_news_transfer_20261106/uci_news_aggregator_359.zip"
RAW_DIR = ROOT / "data/raw/chronological_news_transfer_20261106/uci_news_aggregator_359"
RUN_DIR = (
    ROOT
    / "research/scoped_method/pilots/chronological_news_transfer_20261106/run/uci_news_aggregator_359"
)
LABELS = {"b": 0, "t": 1, "e": 2, "m": 3}
FIELDS = ("id", "title", "url", "publisher", "category", "story", "hostname", "timestamp")
TRAIN0 = ("2014-03-10", "2014-04-21")  # half-open
TRAIN1 = ("2014-04-21", "2014-06-02")
VALID = ("2014-06-02", "2014-07-01")
TEST = ("2014-07-01", "2014-08-11")
DELAY_HOURS = 24
ALPHA = 0.05
LABEL_PRICE = 0.05
SWITCH_COST = 5.0
SEED = 2026110641


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def window_bounds(window: tuple[str, str]) -> tuple[datetime, datetime]:
    return datetime.fromisoformat(window[0]).replace(tzinfo=UTC), datetime.fromisoformat(
        window[1]
    ).replace(tzinfo=UTC)


def read_rows(*, include_test: bool) -> list[dict]:
    """Read only development windows unless the explicit test-opening stage is requested."""
    windows = [TRAIN0, TRAIN1, VALID] + ([TEST] if include_test else [])
    lower = window_bounds((min(x[0] for x in windows), max(x[1] for x in windows)))[0]
    upper = window_bounds((min(x[0] for x in windows), max(x[1] for x in windows)))[1]
    rows: list[dict] = []
    with zipfile.ZipFile(ARCHIVE) as zf, zf.open("newsCorpora.csv") as raw:
        reader = csv.DictReader(
            io.TextIOWrapper(raw, encoding="utf-8"), fieldnames=FIELDS, delimiter="\t"
        )
        for row in reader:
            try:
                ts = datetime.fromtimestamp(int(row["timestamp"]) / 1000, tz=UTC)
            except (ValueError, OverflowError, OSError):
                continue
            if ts < lower or ts >= upper:
                continue
            if not row["id"].isdigit() or not row["title"] or row["category"] not in LABELS:
                continue
            row["_time"] = ts
            row["_y"] = LABELS[row["category"]]
            rows.append(row)
    rows.sort(key=lambda r: (r["_time"], int(r["id"])))
    return rows


def in_window(row: dict, window: tuple[str, str]) -> bool:
    start, end = window_bounds(window)
    return start <= row["_time"] < end


def make_model() -> tuple[HashingVectorizer, SGDClassifier]:
    vectorizer = HashingVectorizer(
        n_features=2**18,
        ngram_range=(1, 2),
        lowercase=True,
        stop_words="english",
        alternate_sign=False,
        norm="l2",
    )
    classifier = SGDClassifier(loss="log_loss", penalty="l2", random_state=SEED)
    return vectorizer, classifier


def fit_pair(rows: list[dict]) -> dict[str, tuple[HashingVectorizer, SGDClassifier]]:
    pair = {}
    for key, window in (("incumbent", TRAIN0), ("challenger", TRAIN1)):
        train = [row for row in rows if in_window(row, window)]
        classes = np.unique([row["_y"] for row in train])
        if not np.array_equal(classes, np.arange(4)):
            raise RuntimeError(
                f"{key} training window lacks one or more classes: {classes.tolist()}"
            )
        vec, clf = make_model()
        x = vec.transform([r["title"] for r in train])
        clf.fit(x, np.asarray([r["_y"] for r in train], dtype=np.int8))
        pair[key] = (vec, clf)
    return pair


def predictions(pair: dict, rows: list[dict]) -> np.ndarray:
    titles = [row["title"] for row in rows]
    return np.column_stack(
        [
            pair[name][1].predict(pair[name][0].transform(titles))
            for name in ("incumbent", "challenger")
        ]
    ).astype(np.int8)


def eligibility(pair: dict, rows: list[dict]) -> dict:
    valid = [r for r in rows if in_window(r, VALID)]
    pred = predictions(pair, valid)
    y = np.asarray([r["_y"] for r in valid], dtype=np.int8)
    losses = (pred != y[:, None]).astype(np.int8)
    signed = losses[:, 0] - losses[:, 1]
    disagree = pred[:, 0] != pred[:, 1]
    blocks = np.array_split(np.arange(len(valid)), 3)
    block_advantages = [float(signed[b].mean()) if len(b) else None for b in blocks]
    publisher_counts: dict[str, int] = {}
    for row in valid:
        publisher_counts[row["publisher"]] = publisher_counts.get(row["publisher"], 0) + 1
    publishers = sorted(p for p, n in publisher_counts.items() if n >= 100)
    signed_disagree = float(signed[disagree].mean()) if disagree.any() else None
    overall = float(signed.mean()) if len(signed) else None
    checks = {
        "at_least_100_disagreements": int(disagree.sum()) >= 100,
        "overall_advantage_at_least_0_03": overall is not None and overall >= 0.03,
        "conditional_disagreement_advantage_at_least_0_20": signed_disagree is not None
        and signed_disagree >= 0.20,
        "challenger_better_in_at_least_2_of_3_blocks": sum(
            value is not None and value > 0 for value in block_advantages
        )
        >= 2,
    }
    return {
        "source": "uci_news_aggregator_359",
        "eligible": all(checks.values()),
        "checks": checks,
        "validation_rows": len(valid),
        "validation_disagreements": int(disagree.sum()),
        "validation_overall_error_advantage": overall,
        "validation_conditional_disagreement_advantage": signed_disagree,
        "validation_block_advantages": block_advantages,
        "publisher_clusters_frozen": publishers,
        "model_classes": {k: pair[k][1].classes_.tolist() for k in pair},
    }


def prepare() -> None:
    if not ARCHIVE.is_file():
        raise FileNotFoundError(ARCHIVE)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_rows(include_test=False)
    pair = fit_pair(rows)
    eligible = eligibility(pair, rows)
    eligibility_path = RUN_DIR / "source_eligibility.json"
    eligibility_path.write_text(json.dumps(eligible, indent=2) + "\n")
    model_path = RAW_DIR / "frozen_models.pkl"
    model_path.write_bytes(pickle.dumps(pair, protocol=pickle.HIGHEST_PROTOCOL))
    manifest = {
        "stage": "pretest_validation_only",
        "archive_sha256": sha256(ARCHIVE),
        "models_sha256": sha256(model_path),
        "eligibility_sha256": sha256(eligibility_path),
        "windows": {"incumbent_train": TRAIN0, "challenger_train": TRAIN1, "validation": VALID},
        "vectorizer": {
            "type": "HashingVectorizer",
            "n_features": 2**18,
            "ngram_range": [1, 2],
            "lowercase": True,
            "stop_words": "english",
            "alternate_sign": False,
            "norm": "l2",
        },
        "classifier": {
            "type": "SGDClassifier",
            "loss": "log_loss",
            "penalty": "l2",
            "random_state": SEED,
        },
        "validation": eligible,
    }
    (RUN_DIR / "pretest_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(eligible, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "open-test"))
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare()
    else:
        raise NotImplementedError(
            "test opening is intentionally gated pending independent protocol review"
        )


if __name__ == "__main__":
    main()
