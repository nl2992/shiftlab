"""Check archived hashes and export temperature and carbon-intensity tables."""

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def instant(value):
    result = datetime.fromisoformat(value)
    return result.replace(tzinfo=UTC) if result.tzinfo is None else result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.snapshot / "manifest.json").read_text())
    predictions, observations, carbon = [], [], {}
    checked, failed = 0, []
    for record in manifest["sources"]:
        if not record["ok"]:
            failed.append(record["name"])
            continue
        raw = (args.snapshot / record["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError(f"Checksum mismatch: {record['file']}")
        checked += 1
        payload = json.loads(raw)
        name, received = record["name"], record["retrieved_at_utc"]

        def prediction(site, model, valid, value, unit, received=received, record=record):
            if value is not None:
                predictions.append(
                    {
                        "site": site,
                        "model": model,
                        "valid_time_utc": instant(valid).isoformat(),
                        "captured_at_utc": received,
                        "temperature_c": value if unit == "C" else (value - 32) * 5 / 9,
                        "prospective": instant(valid) > instant(received),
                        "source_file": record["file"],
                    }
                )

        if name.startswith("open_meteo_"):
            site = name.removeprefix("open_meteo_")
            hourly = payload["hourly"]
            for model in ("gfs_seamless", "ecmwf_ifs025"):
                key = f"temperature_2m_{model}"
                if payload["hourly_units"][key] != "°C":
                    raise ValueError(f"Unexpected temperature unit: {key}")
                for valid, value in zip(hourly["time"], hourly[key], strict=True):
                    prediction(site, model, valid, value, "C")
        elif name.startswith("nws_forecast_"):
            for period in payload["properties"]["periods"]:
                prediction(
                    name.removeprefix("nws_forecast_"),
                    "nws",
                    period["startTime"],
                    period["temperature"],
                    period["temperatureUnit"],
                )
        elif name.startswith("nws_observations_"):
            for feature in payload["features"]:
                p = feature["properties"]
                temperature = p["temperature"]
                if temperature["unitCode"] != "wmoUnit:degC":
                    raise ValueError("Unexpected station temperature unit")
                observations.append(
                    {
                        "station": name.removeprefix("nws_observations_"),
                        "event_time_utc": p["timestamp"],
                        "captured_at_utc": received,
                        "temperature_c": temperature["value"],
                        "quality_control": temperature.get("qualityControl"),
                        "source_file": record["file"],
                    }
                )
        elif name.startswith("carbon_history_"):
            for row in payload["data"]:
                key = (row["from"], row["to"])
                item = {
                    "start_utc": key[0],
                    "end_utc": key[1],
                    "forecast_gco2_kwh": row["intensity"]["forecast"],
                    "actual_gco2_kwh": row["intensity"]["actual"],
                    "captured_at_utc": received,
                    "retrospective": True,
                }
                if key in carbon and (
                    carbon[key]["forecast_gco2_kwh"],
                    carbon[key]["actual_gco2_kwh"],
                ) != (item["forecast_gco2_kwh"], item["actual_gco2_kwh"]):
                    raise ValueError(f"Conflicting boundary records: {key}")
                carbon[key] = item

    def write(name, rows):
        if rows:
            with (args.snapshot / name).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

    write("temperature_predictions.csv", predictions)
    write("temperature_observations.csv", observations)
    write("carbon_retrospective.csv", [carbon[k] for k in sorted(carbon)])
    summary = {
        "verified_files": checked,
        "acquisition_failures": failed,
        "temperature_predictions": len(predictions),
        "prospective_temperature_predictions": sum(p["prospective"] for p in predictions),
        "station_observations": len(observations),
        "station_nonmissing_temperatures": sum(
            p["temperature_c"] is not None for p in observations
        ),
        "unique_carbon_intervals": len(carbon),
        "paired_carbon_intervals": sum(
            r["actual_gco2_kwh"] is not None and r["forecast_gco2_kwh"] is not None
            for r in carbon.values()
        ),
        "evaluation_performed": False,
    }
    (args.snapshot / "verification.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
