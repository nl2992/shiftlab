"""Acquisition helpers shared by actual source adapters."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..catalogue import SOURCES
from ..provenance import sha256
from ..storage import save_dataset


def utc_seconds(values):
    values = pd.Series(pd.to_datetime(values, utc=True))
    seconds = values.astype("datetime64[ns, UTC]").astype("int64").astype(float) / 1e9
    return seconds.mask(values.isna()).to_numpy()


def save_source(
    name: str,
    config: dict,
    root: Path,
    chunks,
    raw_paths,
    feature_names,
    limitations,
    *,
    ground_truth="none",
    artifacts=None,
    extra=None,
):
    source = SOURCES[name]
    provenance = {
        "publisher": source["publisher"],
        "source_url": source["url"],
        "citation": source["citation"],
        "license": source["license"],
        "permitted_use": "Respect original source and underlying-series terms; research use only where permitted",
        "retrieval_parameters": config,
        "raw_checksums": {str(p): sha256(p) for p in raw_paths},
        "feature_names": feature_names,
        "limitations": ["No verified real-world changepoints.", *limitations],
        **(extra or {}),
    }
    return save_dataset(chunks, name, root, provenance, config, ground_truth, artifacts=artifacts)


def numeric_rows(X, y, name, domain, metadata=None):
    # Import at invocation to avoid the adapter dispatcher cycle.
    from .adapters import standardize

    return standardize(X, y, domain, name, metadata=metadata)


def metadata_json(records):
    return [json.dumps(record, default=str, allow_nan=False) for record in records]


def structured_rows(labels, name, domain, references, metadata):
    frame = numeric_rows(np.empty((len(labels), 0)), labels, name, domain, metadata)
    frame["feature_reference"] = references
    return frame
