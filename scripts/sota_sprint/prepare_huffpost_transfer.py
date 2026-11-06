"""Fit Wild-Time HuffPost model pairs and report validation eligibility only."""

from __future__ import annotations

import hashlib
import json
import pickle
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/raw/chronological_news_transfer_20261106/News_Category_Dataset_v2.json"
RAW_DIR = ROOT / "data/raw/chronological_news_transfer_20261106/wildtime_huffpost"
RUN_DIR = (
    ROOT
    / "research/scoped_method/pilots/chronological_news_transfer_20261106/run/wildtime_huffpost"
)
CATEGORIES = [
    "BLACK VOICES",
    "BUSINESS",
    "COMEDY",
    "CRIME",
    "ENTERTAINMENT",
    "IMPACT",
    "QUEER VOICES",
    "SCIENCE",
    "SPORTS",
    "TECH",
    "TRAVEL",
]
CLASS_ID = {name: i for i, name in enumerate(CATEGORIES)}
WINDOWS = {
    "incumbent": (date(2012, 1, 1), date(2014, 1, 1)),
    "challenger": (date(2014, 1, 1), date(2017, 1, 1)),
    "validation": (date(2017, 1, 1), date(2018, 1, 1)),
}
SEED = 2026110641


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_development_rows() -> list[dict]:
    """Retain only the three registered pre-test windows from the JSONL archive."""
    rows = []
    with ARCHIVE.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            row = json.loads(line)
            try:
                published = date.fromisoformat(row["date"])
            except (KeyError, TypeError, ValueError):
                continue
            if not date(2012, 1, 1) <= published < date(2018, 1, 1):
                continue
            category = str(row.get("category", "")).upper()
            title = row.get("headline")
            if category not in CLASS_ID or not isinstance(title, str) or not title.strip():
                continue
            rows.append(
                {
                    "date": published,
                    "id": line_number,
                    "title": title,
                    "y": CLASS_ID[category],
                    "source": "HuffPost",
                }
            )
    rows.sort(key=lambda r: (r["date"], r["id"]))
    return rows


def fit_pair(rows: list[dict]) -> dict:
    pair = {}
    for name in ("incumbent", "challenger"):
        start, end = WINDOWS[name]
        train = [r for r in rows if start <= r["date"] < end]
        y = np.asarray([r["y"] for r in train], dtype=np.int8)
        classes = np.unique(y)
        if not np.array_equal(classes, np.arange(len(CATEGORIES))):
            raise RuntimeError(f"{name} window lacks one or more frozen Wild-Time classes")
        vectorizer = HashingVectorizer(
            n_features=2**18,
            ngram_range=(1, 2),
            lowercase=True,
            stop_words="english",
            alternate_sign=False,
            norm="l2",
        )
        classifier = SGDClassifier(loss="log_loss", penalty="l2", random_state=SEED)
        classifier.fit(vectorizer.transform([r["title"] for r in train]), y)
        pair[name] = (vectorizer, classifier)
    return pair


def assess(pair: dict, rows: list[dict]) -> dict:
    start, end = WINDOWS["validation"]
    valid = [r for r in rows if start <= r["date"] < end]
    titles = [r["title"] for r in valid]
    pred = np.column_stack(
        [pair[k][1].predict(pair[k][0].transform(titles)) for k in ("incumbent", "challenger")]
    )
    y = np.asarray([r["y"] for r in valid], dtype=np.int8)
    losses = (pred != y[:, None]).astype(np.int8)
    signed = losses[:, 0] - losses[:, 1]
    disagree = pred[:, 0] != pred[:, 1]
    blocks = np.array_split(np.arange(len(valid)), 3)
    block_adv = [float(signed[b].mean()) if len(b) else None for b in blocks]
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
        "source": "wildtime_huffpost",
        "eligible": all(checks.values()),
        "checks": checks,
        "validation_rows": len(valid),
        "validation_disagreements": int(disagree.sum()),
        "validation_overall_error_advantage": overall_adv,
        "validation_conditional_disagreement_advantage": conditional_adv,
        "validation_block_advantages": block_adv,
        "publisher_clusters_frozen": ["HuffPost"],
        "n_frozen_classes": len(CATEGORIES),
    }


def main() -> None:
    if not ARCHIVE.is_file():
        raise FileNotFoundError(ARCHIVE)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_development_rows()
    pair = fit_pair(rows)
    result = assess(pair, rows)
    eligibility_path = RUN_DIR / "source_eligibility.json"
    eligibility_path.write_text(json.dumps(result, indent=2) + "\n")
    model_path = RAW_DIR / "frozen_models.pkl"
    model_path.write_bytes(pickle.dumps(pair, protocol=pickle.HIGHEST_PROTOCOL))
    manifest = {
        "stage": "pretest_validation_only",
        "dataset": "Wild-Time HuffPost / News Category Dataset v2",
        "upstream_revision": "khalidalt/HuffPost@01020533529fc1cda0af7d99231eb96e7837f883",
        "archive_sha256": sha256(ARCHIVE),
        "models_sha256": sha256(model_path),
        "eligibility_sha256": sha256(eligibility_path),
        "windows": WINDOWS,
        "categories": CATEGORIES,
        "vectorizer": {"n_features": 2**18, "ngram_range": [1, 2], "alternate_sign": False},
        "classifier": {
            "type": "SGDClassifier",
            "loss": "log_loss",
            "penalty": "l2",
            "random_state": SEED,
        },
        "validation": result,
    }
    (RUN_DIR / "pretest_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
