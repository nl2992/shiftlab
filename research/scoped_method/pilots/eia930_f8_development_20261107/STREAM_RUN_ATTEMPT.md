# Stream-construction attempt record

The first bulk-file run read the six registered EIA files and built the paired demand-classification
streams, but produced no 2,000-hour episodes and called no policies. The process stopped with a
`KeyError: 'ba'` when it tried to aggregate the empty episode table. The saved
`episode_results.jsonl` was zero bytes.

The cause was a time-unit mismatch in the adapter's continuity check: this pandas version stored
`DatetimeIndex.asi8` in microseconds while `Timedelta.value` is nanoseconds. The comparison marked
every adjacent hour as a gap. Independent read-only inspection of the same source files after
converting the timestamp index to nanoseconds found 6, 8, and 7 complete 2,000-hour windows for
PJM, ERCO, and CISO respectively. The runner now uses an explicit nanosecond conversion and has a
pre-policy gate that records the Failure Atlas target profile and stops before policy evaluation if
fewer than two registered BAs match F8.

This attempt generated no method outcomes and is not part of any performance comparison. The
subsequent run will use the corrected adapter at a new source revision and will not overwrite any
non-empty outcome file.
