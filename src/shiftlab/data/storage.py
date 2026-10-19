"""Immutable versioned Parquet datasets, separated evaluator files and checksummed manifests."""

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .provenance import commit, sha256, source_hash, utc_now, write_json
from .schemas import Manifest, validate_frame
from .tasks import dataset_task_specs


def _validate_written_observations(path: Path) -> None:
    """Validate invariants that must hold across Parquet row-group boundaries."""
    order = ["train", "validation", "calibration", "test"]
    bounds: dict[str, list[float]] = {split: [float("inf"), float("-inf")] for split in order}
    sample_ids: set[str] = set()
    parquet = pq.ParquetFile(path)
    for row_group in range(parquet.num_row_groups):
        for batch in parquet.iter_batches(batch_size=8192, row_groups=[row_group]):
            frame = batch.to_pandas()
            validate_frame(frame)
            ids = frame.sample_id.astype(str)
            if ids.duplicated().any() or sample_ids.intersection(ids):
                raise ValueError("sample_id must be unique across Parquet row groups")
            sample_ids.update(ids)
            for split in order:
                times = frame.loc[frame.split == split, "prediction_time"].dropna()
                if len(times):
                    bounds[split][0] = min(bounds[split][0], float(times.min()))
                    bounds[split][1] = max(bounds[split][1], float(times.max()))
    previous_end = None
    for split in order:
        start, end = bounds[split]
        if start == float("inf"):
            continue
        if previous_end is not None and start <= previous_end:
            raise ValueError("Chronological splits overlap or are reversed across row groups")
        previous_end = end


def save_dataset(
    chunks,
    name: str,
    root: str | Path,
    provenance: dict,
    config: dict,
    ground_truth="none",
    oracle_metadata=None,
    artifacts: dict[str, Path] | None = None,
) -> Path:
    root = Path(root)
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "config": config,
                "source": source_hash(),
                "commit": commit(),
                "raw": provenance.get("raw_checksums", {}),
                "artifacts": {name: sha256(path) for name, path in (artifacts or {}).items()},
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()[:20]
    destination = (
        root
        / ("synthetic" if ground_truth == "synthetic_known" else "processed")
        / name
        / fingerprint
    )
    if destination.exists():
        manifest = Manifest.model_validate_json((destination / "dataset_manifest.json").read_text())
        for relative, digest in manifest.files.items():
            if sha256(destination / relative) != digest:
                raise ValueError(f"Existing version corrupt: {destination / relative}")
        return destination
    temporary = destination.parent / f".building-{uuid.uuid4().hex}"
    temporary.mkdir(parents=True)
    total, missing_targets, feature_missing, feature_total = 0, 0, 0, 0
    domains: set[str] = set()
    first = last = None
    names = []
    files = {}
    writers = {}
    try:
        for relative, source in (artifacts or {}).items():
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError("Artifact paths must stay within the dataset version")
            target = temporary / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for frame, oracle in chunks:
            from .chronological_splits import purge_unavailable_labels

            frame = purge_unavailable_labels(frame)
            validate_frame(frame)
            total += len(frame)
            missing_targets += int(frame.target.isna().sum())
            domains.update(str(x) for x in frame.domain_id.dropna().unique())
            if len(frame):
                import numpy as np

                X = np.stack(frame.features.to_numpy())
                names = provenance.get("feature_names", [f"x{i}" for i in range(X.shape[1])])
                feature_missing += int(np.isnan(X).sum())
                feature_total += X.size
                times = frame.event_time.dropna()
                if len(times):
                    first = (
                        str(times.min())
                        if first is None
                        else str(min(float(first), float(times.min())))
                    )
                    last = (
                        str(times.max())
                        if last is None
                        else str(max(float(last), float(times.max())))
                    )
            for relative, data in [
                ("observations.parquet", frame),
                ("evaluator_only/oracle.parquet", oracle),
            ]:
                if data is None:
                    continue
                table = pa.Table.from_pandas(data, preserve_index=False)
                if relative not in writers:
                    path = temporary / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    writers[relative] = pq.ParquetWriter(path, table.schema, compression="zstd")
                writers[relative].write_table(table)
        for writer in writers.values():
            writer.close()
        writers.clear()
        if total == 0:
            raise ValueError("Cannot save empty dataset")
        _validate_written_observations(temporary / "observations.parquet")
        for path in temporary.rglob("*"):
            if path.is_file():
                files[path.relative_to(temporary).as_posix()] = sha256(path)
        if oracle_metadata is not None:
            write_json(temporary / "evaluator_only/dgp.json", oracle_metadata)
            files["evaluator_only/dgp.json"] = sha256(temporary / "evaluator_only/dgp.json")
        manifest = Manifest(
            dataset=name,
            version=fingerprint,
            publisher=provenance["publisher"],
            source_url=provenance["source_url"],
            citation=provenance["citation"],
            license=provenance["license"],
            permitted_use=provenance["permitted_use"],
            acquired_at=utc_now(),
            retrieval_parameters=provenance.get("retrieval_parameters", {}),
            raw_checksums=provenance.get("raw_checksums", {}),
            processing_config=config,
            task_specs=provenance.get(
                "task_specs",
                dataset_task_specs(
                    "synthetic" if ground_truth == "synthetic_known" else name, config
                ),
            ),
            code_commit=commit(),
            source_hash=source_hash(),
            n_observations=total,
            feature_names=names,
            feature_dtype=provenance.get("feature_dtype", config.get("dtype", "float64")),
            feature_kind=provenance.get("feature_kind", "numeric"),
            time_coverage=[first, last],
            domains=sorted(domains),
            missingness={
                "target": missing_targets / total,
                "features": feature_missing / max(1, feature_total),
            },
            limitations=provenance.get("limitations", []),
            ground_truth=ground_truth,
            files=files,
            oracle_file="evaluator_only/oracle.parquet" if oracle_metadata else None,
            environment=provenance.get("environment", {}),
        )
        write_json(temporary / "dataset_manifest.json", manifest.model_dump())
        os.replace(temporary, destination)
        write_json(
            root / "manifests" / f"{name}-{fingerprint}.json",
            {**manifest.model_dump(), "path": str(destination)},
        )
    except Exception:
        for writer in writers.values():
            writer.close()
        # Retain partial artifacts for diagnosis; never publish an incomplete version.
        raise
    return destination


def read_observations(path: Path) -> pd.DataFrame:
    """Read evaluator-owned rows. Use replay() to provide learner-visible messages."""
    return pd.read_parquet(path / "observations.parquet")
