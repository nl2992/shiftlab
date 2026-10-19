"""Immutable versioned Parquet datasets, separated evaluator files and checksummed manifests."""

import hashlib
import json
import os
import uuid
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .provenance import commit, sha256, source_hash, utc_now, write_json
from .schemas import Manifest, validate_frame


def save_dataset(
    chunks,
    name: str,
    root: str | Path,
    provenance: dict,
    config: dict,
    ground_truth="none",
    oracle_metadata=None,
) -> Path:
    root = Path(root)
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "config": config,
                "source": source_hash(),
                "commit": commit(),
                "raw": provenance.get("raw_checksums", {}),
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
    domains, first, last, names = set(), None, None, []
    files = {}
    writers = {}
    try:
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
                    first = str(times.iloc[0]) if first is None else first
                    last = str(times.iloc[-1])
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
        for path in temporary.rglob("*.parquet"):
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
            code_commit=commit(),
            source_hash=source_hash(),
            n_observations=total,
            feature_names=names,
            feature_dtype=config.get("dtype", "float64"),
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
