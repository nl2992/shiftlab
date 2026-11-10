"""Capital Bikeshare (Washington DC area, Lyft) trips: member vs casual. See _bikeshare_common."""

from sources._bikeshare_common import make_module

globals().update(
    make_module(
        "capitalbikeshare_dc",
        "Capital Bikeshare / Lyft (DC Department of Transportation system data)",
        "https://s3.amazonaws.com/capitalbikeshare-data/{m}-capitalbikeshare-tripdata.zip",
        "Capital Bikeshare Data License Agreement (public trip data)",
        "https://capitalbikeshare.com/system-data",
    )
)
