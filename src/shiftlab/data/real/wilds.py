"""Official WILDS partitions and lazy inputs, without converting domain groups into time."""

import json
import tarfile
import uuid
from contextlib import nullcontext
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .common import save_source, structured_rows
from .download import download

SUPPORTED = {"civilcomments", "amazon", "fmow", "iwildcam", "camelyon17"}
CIVIL_URL = (
    "https://worksheets.codalab.org/rest/bundles/0x8cd3de0634154aeaad2ee6eb96723c6e/contents/blob/"
)
IDENTITIES = ["male", "female", "LGBTQ", "christian", "muslim", "other_religions", "black", "white"]


def civilcomments_export(original: pd.DataFrame, config: dict, root: Path, raw_paths):
    required = {"comment_text", "toxicity", "split", *IDENTITIES}
    if not required <= set(original):
        raise ValueError(f"CivilComments missing fields: {required - set(original)}")
    limit = int(config.get("max_per_split", 1000))
    if limit < 1:
        raise ValueError("max_per_split must be positive")
    selected = original.groupby("split", sort=False).head(limit).copy()
    if not selected.split.isin(["train", "val", "test"]).all():
        raise ValueError("Unexpected official CivilComments partition")
    interim = root / "interim/wilds" / uuid.uuid4().hex
    interim.mkdir(parents=True)
    inputs = interim / "inputs.parquet"
    pd.DataFrame({"text": selected.comment_text.fillna("").to_numpy()}).to_parquet(
        inputs, index=False, row_group_size=1000
    )
    labels = (selected.toxicity >= 0.5).astype(int).to_numpy()
    metadata = []
    for source_index, row in selected.iterrows():
        payload = json.loads(row.drop(labels=["comment_text"]).to_json())
        payload.update(
            official_row_index=str(source_index),
            official_split=row["split"],
            identity_threshold=0.5,
            official_metric="accuracy and worst identity-by-label group accuracy",
        )
        metadata.append(json.dumps(payload))
    references = [
        json.dumps({"kind": "parquet_text", "path": "inputs.parquet", "row": i, "column": "text"})
        for i in range(len(selected))
    ]
    frame = structured_rows(labels, "wilds-civilcomments", "civilcomments", references, metadata)
    frame["split"] = selected.split.map(
        {"train": "train", "val": "validation", "test": "test"}
    ).to_numpy()
    return save_source(
        "wilds",
        config,
        root,
        [(frame, None)],
        raw_paths,
        ["comment_text"],
        [
            "CivilComments-wilds v1.0; source CC0. Official train/val/test and identity annotations retained.",
            "Deterministic per-split subset: results on this subset are not full official benchmark scores.",
            "Text stored separately from targets. No individual event/feature/release times supplied by WILDS; online replay is unavailable.",
        ],
        ground_truth="coarse_domains",
        artifacts={"inputs.parquet": inputs},
        extra={
            "feature_kind": "structured_reference",
            "feature_dtype": "text reference",
            "license": "CC0 1.0 (CivilComments source as documented by WILDS)",
        },
    )


def from_official(dataset, config, root: Path):
    """Export metadata/references without calling get_input (image arrays remain lazy)."""
    name = config["dataset"]
    if name not in SUPPORTED:
        raise ValueError("Unsupported WILDS dataset")
    split_map = {int(v): k for k, v in dataset.split_dict.items()}
    labels = np.asarray(dataset.y_array).reshape(-1)
    splits = np.asarray(dataset.split_array)
    annotations = np.asarray(dataset.metadata_array)
    fields = list(dataset.metadata_fields)
    if len(labels) != len(splits) or len(annotations) != len(labels):
        raise ValueError("WILDS metadata lengths disagree")
    maximum = int(config.get("max_per_split", 1000))
    if maximum < 1:
        raise ValueError("max_per_split must be positive")
    selected = np.concatenate(
        [np.flatnonzero(splits == value)[:maximum] for value in sorted(split_map)]
    )
    selected = np.sort(selected)
    references = []
    metadata = []
    canonical = []
    for i in selected:
        official_split = split_map[int(splits[i])]
        canonical.append(
            "train"
            if official_split == "train"
            else "test"
            if "test" in official_split
            else "validation"
        )
        metadata.append(
            json.dumps(
                {
                    "official_index": int(i),
                    "official_split": official_split,
                    "official_metadata": dict(zip(fields, annotations[i].tolist())),
                }
            )
        )
        references.append(
            json.dumps(
                {
                    "kind": "wilds",
                    "dataset": name,
                    "version": str(dataset.version),
                    "index": int(i),
                    "root_dir": str(root / "raw/wilds"),
                }
            )
        )
    frame = structured_rows(labels[selected], f"wilds-{name}", name, references, metadata)
    frame["split"] = canonical
    # Snapshot every official metadata field; targets stay evaluator-owned, never encoded as features.
    interim = root / "interim/wilds" / uuid.uuid4().hex
    interim.mkdir(parents=True)
    snapshot = interim / "official_metadata.parquet"
    pd.DataFrame(
        {
            "official_index": selected,
            "official_split": [split_map[int(splits[i])] for i in selected],
            **{field: annotations[selected, j] for j, field in enumerate(fields)},
        }
    ).to_parquet(snapshot, index=False)
    source_metadata = [p for p in Path(dataset.data_dir).glob("*.csv")]
    return save_source(
        "wilds",
        config,
        root,
        [(frame, None)],
        source_metadata,
        ["structured input reference"],
        [
            f"Official WILDS {name} version {dataset.version}; original partitions and group fields preserved.",
            "Images/text loaded only by the official get_input accessor. Official dataset.eval remains the metric authority.",
            "Dataset-specific terms apply. Official source archives/metadata must remain available; individual images are not copied or eagerly decoded.",
            "No continuous changepoint or release availability inferred from grouped partitions.",
        ],
        ground_truth="coarse_domains",
        artifacts={"official_metadata.parquet": snapshot},
        extra={"feature_kind": "structured_reference", "feature_dtype": "official WILDS reference"},
    )


def official_dataset(config, root, download_data=False):
    try:
        from wilds import get_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional wilds dependency with a torch/torchvision build compatible with your environment"
        ) from exc
    # WILDS 2.0 writes integer split codes into its initially textual pandas column.
    # Pandas 3 infers a strict string dtype; scope legacy inference to this constructor only.
    context = (
        pd.option_context("future.infer_string", False)
        if int(pd.__version__.split(".")[0]) >= 3
        else nullcontext()
    )
    with context:
        return get_dataset(
            dataset=config["dataset"],
            version=config.get("version"),
            root_dir=str(root / "raw/wilds"),
            download=download_data,
        )


def acquire(config, root: Path):
    config = {"dataset": "civilcomments", **config}
    if config["dataset"] not in SUPPORTED:
        raise ValueError(f"Supported WILDS sources: {sorted(SUPPORTED)}")
    if config["dataset"] != "civilcomments" or config.get("use_official_package", False):
        # Large sources must be provided locally or explicitly budgeted by their caller.
        if config.get("download", False) and not config.get("max_download_bytes"):
            raise ValueError(
                "Large WILDS downloads require max_download_bytes as a documented resource estimate; otherwise import an existing official installation"
            )
        return from_official(
            official_dataset(config, root, config.get("download", False)), config, root
        )
    if "path" in config:
        path = Path(config["path"])
        original = pd.read_csv(path, index_col=0)
        return civilcomments_export(original, config, root, [path])
    path = download(
        CIVIL_URL,
        root / "raw/wilds/civilcomments-v1.0.tar.gz",
        max_bytes=config.get("max_download_bytes", 130_000_000),
    )
    with tarfile.open(path, mode="r|gz") as archive:
        for member in archive:
            if member.isfile() and Path(member.name).name == "all_data_with_identities.csv":
                original = pd.read_csv(archive.extractfile(member), index_col=0)
                return civilcomments_export(original, config, root, [path])
    raise ValueError("Official CivilComments archive lacks all_data_with_identities.csv")


def load_input(version_directory: Path, reference: str):
    """Load one input, never its label or source row metadata."""
    spec = json.loads(reference)
    if spec["kind"] == "parquet_text":
        path = (version_directory / spec["path"]).resolve()
        if not path.is_relative_to(version_directory.resolve()):
            raise ValueError("Input reference escapes dataset directory")
        parquet = pq.ParquetFile(path)
        row = int(spec["row"])
        if row < 0 or row >= parquet.metadata.num_rows:
            raise IndexError("Text reference outside input table")
        offset = 0
        for group in range(parquet.num_row_groups):
            size = parquet.metadata.row_group(group).num_rows
            if row < offset + size:
                return (
                    parquet.read_row_group(group, columns=[spec["column"]])
                    .column(0)[row - offset]
                    .as_py()
                )
            offset += size
    if spec["kind"] == "wilds":
        if spec["dataset"] not in SUPPORTED:
            raise ValueError("Unrecognized WILDS reference")
        try:
            source = cached_official(spec["dataset"], spec["version"], spec["root_dir"])
        except ImportError as exc:
            raise RuntimeError(
                "Loading official WILDS references requires the optional wilds package"
            ) from exc
        return source.get_input(int(spec["index"]))
    raise ValueError("Unsupported structured input reference")


def evaluate_official(dataset, predictions, targets, metadata):
    """Use official metric definitions; transparently adapt only arithmetic group means when needed."""
    try:
        import torch_scatter  # noqa: F401
    except ImportError:
        from .wilds_metrics import evaluate_without_scatter

        return evaluate_without_scatter(dataset, predictions, targets, metadata)
    else:
        return dataset.eval(predictions, targets, metadata)


@lru_cache(maxsize=5)
def cached_official(name, version, root_dir):
    from wilds import get_dataset

    context = (
        pd.option_context("future.infer_string", False)
        if int(pd.__version__.split(".")[0]) >= 3
        else nullcontext()
    )
    with context:
        return get_dataset(dataset=name, version=version, root_dir=root_dir, download=False)
