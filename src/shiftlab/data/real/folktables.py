"""Bounded Census ZIP acquisition, streaming task conversion and coarse domain protocols."""

import inspect
import json
import tempfile
import zipfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from ..tasks import finite_real_parameter, integer_parameter
from .common import save_source
from .download import download

TASKS = {"ACSIncome", "ACSEmployment", "ACSPublicCoverage", "ACSMobility", "ACSTravelTime"}


def task_for_year(package, task_name, year):
    """Use the Census-published field names for the selected PUMS release."""
    task = getattr(package, task_name)
    aliases = {"RELP": "RELSHIPP", "JWTR": "JWTRNS"} if year >= 2019 else {}
    if not aliases or not any(name in aliases for name in task.features):
        return task, {}
    from folktables import BasicProblem

    adjusted = BasicProblem(
        features=[aliases.get(name, name) for name in task.features],
        target=task.target,
        target_transform=task.target_transform,
        group=task.group,
        group_transform=task.group_transform,
        preprocess=task._preprocess,
        postprocess=task._postprocess,
    )
    return adjusted, {name: aliases[name] for name in task.features if name in aliases}


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


def convert(records, task, task_name, state, year, density, source_aliases):
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
                    "source_field_aliases": source_aliases,
                    "source_feature_names": task.features,
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
    density = finite_real_parameter(config.get("density", 1), "density", positive=True)
    if density > 1:
        raise ValueError("density must lie in (0,1]")
    seed = integer_parameter(config.get("sampling_seed", 42), "sampling_seed", minimum=0)
    chunk_size = integer_parameter(
        config.get("chunk_size", 20000), "chunk_size", minimum=1, maximum=100000
    )
    task_name = tasks[0]
    base_task = getattr(package, task_name)
    filter_fields = {
        "ACSIncome": {"AGEP", "PINCP", "WKHP", "PWGTP"},
        "ACSEmployment": set(),
        "ACSPublicCoverage": {"AGEP", "PINCP"},
        "ACSMobility": {"AGEP"},
        "ACSTravelTime": {"AGEP", "PWGTP", "ESR"},
    }
    root, paths, members = Path(root), [], []
    for year in years:
        for state in states:
            task, aliases = task_for_year(package, task_name, year)
            required = (
                set(task.features)
                | {task.target, task.group, "ST", "PWGTP"}
                | filter_fields[task_name]
            )
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
            members.append((path, member, state, year, task, aliases))

    def chunks():
        for path, member, state, year, task, aliases in members:
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
                    frame = convert(records, task, task_name, state, year, density, aliases)
                    if frame is not None:
                        yield frame, None

    definitions = {
        "folktables_version": version("folktables"),
        "task": task_name,
        "features": base_task.features,
        "target": base_task.target,
        "group": base_task.group,
        "preprocess_source": inspect.getsource(base_task._preprocess),
        "target_transform_source": inspect.getsource(base_task.target_transform),
        "group_transform_source": inspect.getsource(base_task.group_transform),
        "postprocess_source": inspect.getsource(base_task._postprocess),
        "source_field_aliases_by_year": {
            str(year): task_for_year(package, task_name, year)[1] for year in years
        },
        "source_schema_note": (
            "Census changed RELP to RELSHIPP in 2019, with renamed/renumbered relationship "
            "categories, and JWTR to JWTRNS. Source fields are retained as named; numeric "
            "category codes are not harmonized across these annual releases."
        ),
        "source_schema_reference": "https://www2.census.gov/programs-surveys/acs/tech_docs/pums/ACS2019_PUMS_README.pdf",
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
            list(task_for_year(package, task_name, years[0])[0].features),
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
