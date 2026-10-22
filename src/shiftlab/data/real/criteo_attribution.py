"""Acquire Criteo's pinned display-attribution source with delayed outcomes."""

from __future__ import annotations

import json
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .common import save_source, structured_rows
from .download import download

REPOSITORY = "criteo/criteo-attribution-dataset"
REVISION = "904188a63cbad78bee43cd26ff5ee4ac77903986"
FILE = "criteo_attribution_dataset.tsv.gz"
FILE_SHA256 = "94ac7a465564349bc7ba008602211d5990a3c53cc133abc0aadef61ea2391a98"
FILE_BYTES = 653_015_824
URL = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/{FILE}?download=true"
README_URL = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/README.md"
LICENSE = "CC BY-NC-SA 4.0"
WINDOW_SECONDS = 30 * 86_400
FIELDS = [
    "timestamp",
    "uid",
    "campaign",
    "conversion",
    "conversion_timestamp",
    "conversion_id",
    "attribution",
    "click",
    "click_pos",
    "click_nb",
    "cost",
    "cpo",
    "time_since_last_click",
    *[f"cat{i}" for i in range(1, 10)],
]
INPUT_FIELDS = [
    "timestamp",
    "campaign",
    "time_since_last_click",
    *[f"cat{i}" for i in range(1, 10)],
]
ORACLE_FIELDS = ["conversion_id", "attribution", "click", "click_pos", "click_nb", "cost", "cpo"]


def _read_chunks(path: Path, chunk_size: int):
    return pd.read_csv(
        path,
        compression="gzip",
        sep="\t",
        header=0,
        names=FIELDS,
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
    )


def validate_config(config):
    config = dict(config)
    chunk_size = config.get("chunk_size", 50_000)
    max_bytes = config.get("max_download_bytes", 700_000_000)
    if type(chunk_size) is not int or not 1 <= chunk_size <= 200_000:
        raise ValueError("chunk_size must be an integer in [1, 200000]")
    if type(max_bytes) is not int or max_bytes < FILE_BYTES:
        raise ValueError(f"max_download_bytes must be at least {FILE_BYTES}")
    return config


def _write_inputs(path: Path, destination: Path, chunk_size: int):
    writer = None
    total = 0
    last_timestamp = -np.inf
    try:
        for source in _read_chunks(path, chunk_size):
            timestamp = pd.to_numeric(source.timestamp, errors="raise").to_numpy(float)
            if not np.isfinite(timestamp).all() or (timestamp < 0).any():
                raise ValueError("Criteo impression timestamps must be finite and nonnegative")
            if timestamp[0] < last_timestamp or (np.diff(timestamp) < 0).any():
                raise ValueError("Criteo source is not ordered by impression timestamp")
            last_timestamp = timestamp[-1]
            features = source[INPUT_FIELDS].copy()
            features["timestamp"] = timestamp
            features["time_since_last_click"] = pd.to_numeric(
                features.time_since_last_click, errors="raise"
            ).to_numpy(float)
            table = pa.Table.from_pandas(features, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(destination, table.schema, compression="zstd")
            writer.write_table(table, row_group_size=chunk_size)
            total += len(source)
    finally:
        if writer is not None:
            writer.close()
    if total == 0:
        raise ValueError("Criteo source contains no observations")
    return total


def _make_frames(path: Path, chunk_size: int, input_count: int):
    offset = 0
    last_timestamp = -np.inf
    for source in _read_chunks(path, chunk_size):
        n = len(source)
        timestamp = pd.to_numeric(source.timestamp, errors="raise").to_numpy(float)
        conversion = pd.to_numeric(source.conversion, errors="raise").to_numpy(np.int8)
        conversion_timestamp = pd.to_numeric(source.conversion_timestamp, errors="raise").to_numpy(
            float
        )
        if len(source.columns) != len(FIELDS):
            raise ValueError("Unexpected Criteo attribution field count")
        if not np.isin(conversion, [0, 1]).all():
            raise ValueError("Criteo conversion must be binary")
        if timestamp[0] < last_timestamp or (np.diff(timestamp) < 0).any():
            raise ValueError("Criteo source is not ordered by impression timestamp")
        last_timestamp = timestamp[-1]
        positive = conversion == 1
        if np.any(
            positive & (~np.isfinite(conversion_timestamp) | (conversion_timestamp < timestamp))
        ):
            raise ValueError("Criteo conversion timestamp must follow its impression")
        if np.any(positive & (conversion_timestamp > timestamp + WINDOW_SECONDS)):
            raise ValueError("Criteo conversion exceeds the documented 30-day window")
        if np.any((~positive) & (conversion_timestamp != -1)):
            raise ValueError("Criteo nonconversion rows must use the documented -1 sentinel")

        refs = [
            json.dumps({"kind": "parquet_record", "path": "inputs.parquet", "row": i})
            for i in range(offset, offset + n)
        ]
        frame = structured_rows(
            conversion,
            "criteo-attribution",
            source.campaign.astype(str).to_numpy(),
            refs,
            json.dumps(
                {
                    "source_revision": REVISION,
                    "clock": "publisher-relative seconds from source start; not calendar time",
                    "label_maturation": "impression time + 30 days",
                    "feature_availability": "context is assumed known at impression time",
                }
            ),
        )
        frame["sample_id"] = [f"criteo-attribution:{i}" for i in range(offset, offset + n)]
        frame["entity_id"] = source.uid.astype(str).to_numpy()
        frame["event_time"] = timestamp
        frame["feature_available_time"] = timestamp
        frame["prediction_time"] = timestamp
        frame["label_event_time"] = np.where(
            positive, conversion_timestamp, timestamp + WINDOW_SECONDS
        )
        frame["label_available_time"] = timestamp + WINDOW_SECONDS

        oracle = source[ORACLE_FIELDS].copy()
        oracle.insert(0, "sample_id", frame.sample_id.to_numpy())
        oracle["source_conversion_timestamp"] = conversion_timestamp
        oracle["source_row_index"] = np.arange(offset, offset + n, dtype=np.int64)
        offset += n
        yield frame, oracle
    if offset != input_count:
        raise ValueError(f"Source changed between reads: inputs={input_count}, labels={offset}")


def acquire(config, root: Path):
    config = validate_config(config)
    root = Path(root)
    raw_dir = root / "raw/criteo_attribution"
    path = download(
        URL,
        raw_dir / FILE,
        expected_sha256=FILE_SHA256,
        max_bytes=config.get("max_download_bytes", 700_000_000),
    )
    if path.stat().st_size != FILE_BYTES:
        raise ValueError("Criteo attribution archive size does not match pinned Hub metadata")
    readme = download(
        README_URL,
        raw_dir / "README.md",
        max_bytes=100_000,
    )
    config.update(
        repository=REPOSITORY,
        revision=REVISION,
        source_file=FILE,
        source_sha256=FILE_SHA256,
        source_bytes=FILE_BYTES,
        source_license=LICENSE,
        chunk_size=config.get("chunk_size", 50_000),
    )

    with tempfile.TemporaryDirectory(prefix="shiftlab-criteo-attribution-") as temp:
        inputs = Path(temp) / "inputs.parquet"
        total = _write_inputs(path, inputs, config["chunk_size"])
        chunks = _make_frames(path, config["chunk_size"], total)
        return save_source(
            "criteo_attribution",
            config,
            root,
            chunks,
            [path, readme],
            INPUT_FIELDS,
            [
                "Display-attribution dataset, separate from the unavailable 90-day Sponsored Search conversion archive and from CriteoPrivateAds.",
                "Timestamp is a publisher-relative clock, not a calendar timestamp or verified publication time.",
                "Labels mature at impression time plus 30 days; this follows the publisher's stated conversion window and is conservative for earlier conversions.",
                "Context availability at impression time is an explicit assumption. Click outcomes, conversion fields, attribution, cost, and CPO are excluded from learner inputs; available to evaluators only where present.",
                "User ID is retained as entity_id for repeated-measures grouping, not included as an input feature.",
                "The source is a 30-day display-impression dataset, not sponsored search; no cross-source population equivalence is claimed.",
            ],
            artifacts={"inputs.parquet": inputs},
            extra={
                "feature_kind": "structured_reference",
                "feature_dtype": "categorical context and relative timestamp",
                "full_source_acquired": True,
                "n_source_rows": total,
                "source_revision": REVISION,
                "publisher_file_sha256": FILE_SHA256,
                "publisher_file_bytes": FILE_BYTES,
                "readme_sha256": __import__("hashlib").sha256(readme.read_bytes()).hexdigest(),
            },
        )


@lru_cache(maxsize=2)
def _parquet_file(path: str):
    return pq.ParquetFile(path)


@lru_cache(maxsize=4)
def _row_group(path: str, group: int):
    return _parquet_file(path).read_row_group(group)


def load_input(version_directory: Path, reference: str):
    """Load one structured learner input, excluding labels and evaluator-only fields."""
    spec = json.loads(reference)
    if spec.get("kind") != "parquet_record" or spec.get("path") != "inputs.parquet":
        raise ValueError("Unsupported Criteo attribution input reference")
    version_directory = Path(version_directory).resolve()
    path = (version_directory / spec["path"]).resolve()
    if not path.is_relative_to(version_directory):
        raise ValueError("Input reference escapes dataset version")
    parquet = _parquet_file(str(path))
    row = int(spec["row"])
    if row < 0 or row >= parquet.metadata.num_rows:
        raise IndexError("Criteo input reference outside feature table")
    offset = 0
    for group in range(parquet.num_row_groups):
        rows = parquet.metadata.row_group(group).num_rows
        if row < offset + rows:
            record = _row_group(str(path), group).slice(row - offset, 1).to_pylist()[0]
            return record
        offset += rows
    raise IndexError("Criteo input reference outside feature table")
