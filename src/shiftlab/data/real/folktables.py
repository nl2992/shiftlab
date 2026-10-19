"""Bounded Census ZIP acquisition, streaming task conversion and coarse domain protocols."""

import inspect
import json
import tempfile
import zipfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from .common import save_source
from .download import download

TASKS = {"ACSIncome", "ACSEmployment", "ACSPublicCoverage", "ACSMobility", "ACSTravelTime"}


def comparison_plan(states, years):
    """Domain selectors for retrospective comparisons, never per-person chronology."""
    plans = []
    for state in states:
        for early, late in zip(sorted(years)[:-1], sorted(years)[1:]):
            plans.append(
                {
                    "kind": "within_state_cross_year",
                    "train_domains": [f"{state}-{early}"],
                    "test_domains": [f"{state}-{late}"],
                }
            )
    for year in years:
        for state in states[1:]:
            plans.append(
                {
                    "kind": "cross_state_same_year",
                    "train_domains": [f"{states[0]}-{year}"],
                    "test_domains": [f"{state}-{year}"],
                }
            )
    if len(years) > 1:
        early, late = min(years), max(years)
        plans.append(
            {
                "kind": "pooled_cross_year",
                "train_domains": [f"{s}-{early}" for s in states],
                "test_domains": [f"{s}-{late}" for s in states],
            }
        )
        if len(states) > 1:
            plans.append(
                {
                    "kind": "cross_state_cross_year",
                    "train_domains": [f"{states[0]}-{early}"],
                    "test_domains": [f"{s}-{late}" for s in states[1:]],
                }
            )
    return {
        "timing": "coarse annual domains; within-year observation order unknown",
        "comparisons": plans,
    }


def convert(records, task, task_name, state, year, density):
    from .adapters import standardize

    selected = task._preprocess(records)
    if not len(selected):
        return None
    X, y, groups = task.df_to_numpy(records)
    if len(X) != len(selected):
        raise ValueError("Folktables task preprocessing lost source-row alignment")
    weights = selected.PWGTP.to_numpy(float)
    if not np.isfinite(weights).all() or (weights < 0).any():
        raise ValueError("Invalid original ACS survey weights")
    meta = []
    missing = selected[task.features].isna()
    for row_index, group, (_, row) in zip(selected.index, groups.ravel(), selected.iterrows()):
        demographics = {
            key: (None if pd.isna(row[key]) else float(row[key]))
            for key in ["AGEP", "SEX", "RAC1P", "HISP"]
            if key in row
        }
        meta.append(
            json.dumps(
                {
                    "survey_year": year,
                    "state": state,
                    "task": task_name,
                    "source_row": int(row_index),
                    "demographic_group": int(group),
                    "demographics": demographics,
                    "within_year_order": "unknown",
                    "sampling_probability": density,
                    "sample_weight_origin": "original PWGTP; not divided by sampling probability",
                    "original_missing_feature_columns": missing.columns[
                        missing.loc[row_index]
                    ].tolist(),
                },
                allow_nan=False,
            )
        )
    frame = standardize(
        X,
        y.ravel(),
        f"{state}-{year}",
        f"acs-{task_name}-{state}-{year}",
        metadata=meta,
        weights=weights,
    )
    frame["sample_id"] = [f"acs-{task_name}-{state}-{year}:{i}" for i in selected.index]
    return frame


def acquire(config, root):
    try:
        import folktables as package
        from folktables.load_acs import _STATE_CODES
    except ImportError as exc:
        raise RuntimeError("Install the data-sources optional dependency for Folktables") from exc
    states = config.get("states", ["NJ"])
    years = config.get("years", [2018])
    tasks = config.get("tasks", ["ACSIncome"])
    if not isinstance(tasks, list) or len(tasks) != 1 or tasks[0] not in TASKS:
        raise ValueError("Use one supported Folktables task per immutable version")
    if (
        not isinstance(states, list)
        or not states
        or any(s not in _STATE_CODES for s in states)
        or len(set(states)) != len(states)
    ):
        raise ValueError("Require unique supported ACS states")
    if (
        not isinstance(years, list)
        or not years
        or any(type(y) is not int or not 2014 <= y <= 2019 for y in years)
        or len(set(years)) != len(years)
    ):
        raise ValueError(
            "This validated Folktables adapter supports unique 1-Year survey years 2014–2019"
        )
    density = float(config.get("density", 1))
    seed, chunk_size = int(config.get("sampling_seed", 42)), int(config.get("chunk_size", 20000))
    if not 0 < density <= 1 or seed < 0 or not 1 <= chunk_size <= 100000:
        raise ValueError("Require density in (0,1], nonnegative seed, and chunk_size <= 100000")
    task_name, task = tasks[0], getattr(package, tasks[0])
    filter_fields = {
        "ACSIncome": {"AGEP", "PINCP", "WKHP", "PWGTP"},
        "ACSEmployment": set(),
        "ACSPublicCoverage": {"AGEP", "PINCP"},
        "ACSMobility": {"AGEP"},
        "ACSTravelTime": {"AGEP", "PWGTP", "ESR"},
    }
    required = (
        set(task.features) | {task.target, task.group, "ST", "PWGTP"} | filter_fields[task_name]
    )
    root, paths, members = Path(root), [], []
    for year in years:
        for state in states:
            path = download(
                f"https://www2.census.gov/programs-surveys/acs/data/pums/{year}/1-Year/csv_p{state.lower()}.zip",
                root / "raw/folktables" / str(year) / "1-Year" / f"csv_p{state.lower()}.zip",
                max_bytes=int(config.get("max_download_bytes", 80_000_000)),
            )
            member = (
                f"psam_p{_STATE_CODES[state]}.csv"
                if year >= 2017
                else f"ss{str(year)[-2:]}p{state.lower()}.csv"
            )
            with zipfile.ZipFile(path) as archive:
                info = archive.getinfo(member)
                if info.file_size > int(config.get("max_uncompressed_bytes", 600_000_000)):
                    raise ValueError("ACS uncompressed member exceeds explicit byte budget")
                with archive.open(member) as handle:
                    header = set(pd.read_csv(handle, nrows=0).columns)
                if missing := sorted(required - header):
                    raise ValueError(
                        f"{state} {year} source schema cannot support installed {task_name}: missing {missing}; no category harmonization inferred"
                    )
            paths.append(path)
            members.append((path, member, state, year))

    def chunks():
        for path, member, state, year in members:
            rng = np.random.default_rng(
                np.random.SeedSequence([seed, year, int(_STATE_CODES[state])])
            )
            with zipfile.ZipFile(path) as archive, archive.open(member) as handle:
                for records in pd.read_csv(
                    handle,
                    chunksize=chunk_size,
                    dtype={"SERIALNO": str, "SOCP": str, "NAICSP": str, "RT": str},
                    low_memory=False,
                ):
                    if "ST" not in records or not records.ST.eq(int(_STATE_CODES[state])).all():
                        raise ValueError("ACS records do not match requested state")
                    records = records.loc[rng.random(len(records)) < density]
                    frame = convert(records, task, task_name, state, year, density)
                    if frame is not None:
                        yield frame, None

    definitions = {
        "folktables_version": version("folktables"),
        "task": task_name,
        "features": task.features,
        "target": task.target,
        "group": task.group,
        "preprocess_source": inspect.getsource(task._preprocess),
        "target_transform_source": inspect.getsource(task.target_transform),
        "group_transform_source": inspect.getsource(task.group_transform),
        "postprocess_source": inspect.getsource(task._postprocess),
        "sampling": {
            "probability": density,
            "seed": seed,
            "rng": "NumPy PCG64, separate SeedSequence(seed,year,state-FIPS); Bernoulli before task filtering",
        },
        "comparisons": comparison_plan(states, years),
    }
    with tempfile.TemporaryDirectory(prefix="shiftlab-acs-") as temp:
        protocol = Path(temp) / "protocol.json"
        protocol.write_text(json.dumps(definitions, indent=2), encoding="utf-8")
        return save_source(
            "folktables",
            config,
            root,
            chunks(),
            paths,
            list(task.features),
            [
                "Annual records unordered; no individual observation, release or label-availability times invented.",
                "Official Folktables feature postprocessing uses its missing-value coding; original missing feature names preserved per row.",
                "Original survey weights and demographic values retained; Bernoulli inclusion probability separate from original PWGTP.",
                "Domain comparison plans are retrospective, not online chronological protocols or verified changepoints.",
            ],
            ground_truth="coarse_domains",
            artifacts={"acs_protocol.json": protocol},
            extra={"environment": {"folktables_version": version("folktables")}},
        )
