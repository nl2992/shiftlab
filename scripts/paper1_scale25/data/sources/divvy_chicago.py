"""Divvy (Chicago bikeshare, Lyft) trips: member vs casual. See _bikeshare_common for the window rule."""

from sources._bikeshare_common import make_module

globals().update(
    make_module(
        "divvy_chicago",
        "Divvy / Lyft (Chicago Department of Transportation system data)",
        "https://divvy-tripdata.s3.amazonaws.com/{m}-divvy-tripdata.zip",
        "Divvy Data License Agreement (public trip data; Lyft/CDOT)",
        "https://divvybikes.com/system-data",
    )
)
