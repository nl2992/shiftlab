"""Criteo delayed conversions. Source outcomes are excluded from feature construction."""

import json
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

from .common import numeric_rows, save_source
from .download import download

URL = "https://go.criteo.net/criteo-research-search-conversion.tar.gz"
COLUMNS = [
    "sale",
    "sales_amount_in_euro",
    "time_delay_for_conversion",
    "click_timestamp",
    "nb_clicks_1week",
    "product_price",
    "product_age_group",
    "device_type",
    "audience_id",
    "product_gender",
    "product_brand",
    *[f"product_category_{i}" for i in range(1, 8)],
    "product_country",
    "product_id",
    "product_title",
    "partner_id",
    "user_id",
]
OUTCOMES = {"sale", "sales_amount_in_euro", "time_delay_for_conversion"}


def conversion_rows(original: pd.DataFrame, config: dict):
    columns = config.get("feature_columns", ["nb_clicks_1week", "product_price"])
    if set(columns) & OUTCOMES:
        raise ValueError("Conversion outcomes/delays must never be predictive features")
    factors = {"seconds": 1.0, "minutes": 60.0, "hours": 3600.0, "days": 86400.0}
    if config.get("delay_unit") not in factors:
        raise ValueError(
            "Specify delay_unit only after verifying the source README or local export units"
        )
    click = (
        pd.to_numeric(original.click_timestamp, errors="raise").replace(0, np.nan).to_numpy(float)
    )
    sale = pd.to_numeric(original.sale, errors="raise").to_numpy()
    if not np.isin(sale, [0, 1]).all():
        raise ValueError("Criteo sale must be binary")
    delay = (
        pd.to_numeric(original.time_delay_for_conversion, errors="raise").to_numpy(float)
        * factors[config["delay_unit"]]
    )
    if np.any((sale == 1) & (delay < 0)):
        raise ValueError("Positive conversion has negative delay")
    window = float(config.get("outcome_window_days", 30)) * 86400
    if window <= 0:
        raise ValueError("Outcome window must be positive")
    target_event = np.where(sale == 1, click + delay, click + window)
    if np.any((sale == 1) & (target_event > click + window)):
        raise ValueError("Conversion exceeds documented outcome window")
    latency = float(config.get("feedback_latency_seconds", 0))
    if latency < 0:
        raise ValueError("feedback_latency_seconds must be nonnegative")
    available = target_event + latency
    observation_end = config.get("observation_end")
    if observation_end is None:
        # No observed positive at all can certify a later nonconversion's full 30-day followup.
        available = np.where(sale == 1, available, np.nan)
    else:
        available = np.where(available <= float(observation_end), available, np.nan)
    X = original[columns].apply(pd.to_numeric, errors="raise").replace(-1, np.nan).to_numpy(float)
    frame = numeric_rows(
        X,
        sale,
        "criteo",
        original.partner_id.astype(str).to_numpy(),
        [
            json.dumps(
                {
                    "source": row,
                    "clock": "publisher-shifted timestamp, not a verified calendar date",
                    "availability_assumption": "conversion event + configured feedback latency; negatives need full followup",
                    "delay_unit": config["delay_unit"],
                    "outcome_window_days": window / 86400,
                }
            )
            for row in json.loads(original.to_json(orient="records"))
        ],
    )
    frame["event_time"] = click
    frame["label_event_time"] = target_event
    frame["label_available_time"] = available
    if config.get("assume_instant_click_features", False):
        frame["prediction_time"] = click
        frame["feature_available_time"] = click
    return frame


def acquire(config, root: Path):
    path = (
        Path(config["path"])
        if "path" in config
        else download(
            URL,
            root / "raw/criteo/criteo-research-search-conversion.tar.gz",
            max_bytes=config.get("max_download_bytes", 400_000_000),
        )
    )
    maximum = int(config.get("max_records", 50000))
    if maximum < 1:
        raise ValueError("max_records must be positive")

    def read(handle):
        original = pd.read_csv(handle, sep="\t", header=None, names=COLUMNS, nrows=maximum)
        if len(original.columns) != len(COLUMNS):
            raise ValueError("Unexpected Criteo field count")
        return conversion_rows(original, config)

    if tarfile.is_tarfile(path):
        with tarfile.open(path, mode="r|gz") as archive:
            frame = None
            for member in archive:
                if member.isfile() and Path(member.name).name == "CriteoSearchData":
                    frame = read(archive.extractfile(member))
                    break
            if frame is None:
                raise ValueError("CriteoSearchData missing from source archive")
    else:
        with path.open("rb") as handle:
            frame = read(handle)
    return save_source(
        "criteo",
        config,
        root,
        [(frame, None)],
        [path],
        config.get("feature_columns", ["nb_clicks_1week", "product_price"]),
        [
            "Criteo source is CC BY-NC-SA 4.0; preserve attribution and share-alike/noncommercial conditions.",
            "Deterministic first-row subset; negatives without certified full followup retain unknown availability.",
            "Shifted click timestamps are not real calendar times. Feedback latency and instantaneous feature delivery, if used, are explicit assumptions.",
        ],
    )
