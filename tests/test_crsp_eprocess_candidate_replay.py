import hashlib
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from scripts.replay_crsp_eprocess_candidates import replay


def test_replay_verifies_input_and_writes_all_matched_process_traces(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    trajectory = input_dir / "monitor_trajectory.parquet"
    n = 80
    costs = [0.002] * 40 + [0.008] * 40
    harms = [True] * 20 + [False] * 40 + [True] * 20
    pq.write_table(
        pa.Table.from_pandas(
            pd.DataFrame(
                {
                    "date": pd.date_range("2020-01-01", periods=n).strftime("%Y-%m-%d"),
                    "mean_paired_excess_cost_5bps": costs,
                    "next_20_date_harm_label": harms,
                }
            ),
            preserve_index=False,
        ),
        trajectory,
    )
    checksum = hashlib.sha256(trajectory.read_bytes()).hexdigest()
    (input_dir / "checksums.sha256").write_text(
        f"{checksum}  {trajectory.name}\n", encoding="utf-8"
    )

    output = replay(input_dir=input_dir, output_dir=tmp_path / "output")
    summary = pd.read_parquet(output / "monitor_comparison.parquet")
    trace = pd.read_parquet(output / "monitor_trajectory.parquet")
    assert len(summary) == 4
    assert set(summary.monitor) == {
        "fixed_stake_mixture",
        "predictable_kelly",
        "plug_in_empirical_bernstein",
        "uniform_eight_start_mixture",
    }
    assert len(trace) == n
    assert summary.updates.eq(n).all()
    assert (output / "checksums.sha256").is_file()
