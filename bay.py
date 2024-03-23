import logging
from typing import List

import geopandas as gpd
import pandas as pd

log = logging.getLogger("main")


def overlapping_routes(routes_fn: str, trail_fns: List[str], output_fn: str):
    """Load activity routes and output only routes that overlap Bay trails."""
    trails = []
    for filename in trail_fns:
        log.info(f"loading {filename}")
        trails.append(gpd.read_file(filename))

    trail_df = pd.concat(trails, ignore_index=True)
    route_df = gpd.read_file(routes_fn)
    log.info(f"loaded {len(trail_df)} trail segments, {len(route_df)} routes")
    # spatial join to find overlapping routes
    overlap_df = gpd.sjoin(route_df, trail_df, op="intersects")
    log.info(f"found {len(overlap_df.index)} intersecting routes")
    # use name_right (trail name) as name
    overlap_df["name"] = overlap_df["name_right"]
    overlap_df = overlap_df[["name", "id_right", "url", "start", "geometry", "legend"]]
    overlap_df.fillna("", inplace=True)
    overlap_df.to_file(output_fn, driver="GeoJSON")
    log.info(f"wrote {len(overlap_df)} routes to {output_fn}")


if __name__ == "__main__":
    # set logging handler to output date and message
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
    overlapping_routes(
        "output/routes.geojson",
        ["output/bay_trail.geojson", "output/ridge_trail.geojson"],
        "output/trail_routes.geojson",
    )
