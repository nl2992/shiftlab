"""Build the EIA paired reserve decision streams into outputs/eia_paired_reserve/."""

from __future__ import annotations

import time
from pathlib import Path

import torch

from shiftlab.dive.eia_paired_reserve import (
    ARCHIVE,
    RESPONDENTS,
    build_respondent_streams,
    load_series,
    write_streams,
)

OUT = Path(__file__).resolve().parents[1] / "outputs/eia_paired_reserve"


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"{OUT} is not empty; refusing to overwrite")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    started = time.perf_counter()
    series = load_series(ARCHIVE)
    streams = []
    for respondent in RESPONDENTS:
        streams.extend(build_respondent_streams(series, respondent, device))
    write_streams(streams, OUT, device=device)
    print(f"device={device.type} runtime_s={time.perf_counter() - started:.1f}")


if __name__ == "__main__":
    main()
