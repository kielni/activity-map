import argparse
import glob
import logging
import re
from typing import Optional, Set, List

from dateutil import tz
import geopandas as gpd
import gpxpy
import pandas as pd
from shapely import Polygon

log = logging.getLogger("main")


def main(path: str, output_fn: str, bbox_str: Optional[str] = None):
    bbox_df: Optional[gpd.GeoDataFrame] = None
    # bounding box is a GeoDataFrame containing a Polygon
    if bbox_str:
        x1, y1, x2, y2 = [float(x) for x in bbox_str.split(",")]
        bbox_df = gpd.GeoDataFrame(
            geometry=[Polygon(((x1, y1), (x1, y2), (x2, y2), (x2, y1), (x1, y1)))],
            crs="EPSG:4326",
        )

    routes: List[gpd.GeoDataFrame] = []
    seen: Set[str] = set()
    log.info(f"loading {output_fn}")
    try:
        prev_df = gpd.read_file(output_fn)
        seen = set(prev_df["id"])
        log.info(f"loaded {len(prev_df)} routes from {output_fn}")
    except Exception:
        prev_df = gpd.GeoDataFrame(
            [], columns=["name", "geometry", "start", "id", "url"], crs="EPSG:4326"
        )

    local_tz = tz.gettz("America/Los_Angeles")
    filenames = glob.glob(f"{path}/*.gpx")
    log.info(f"loading {len(filenames)} gpx files from {path}")
    for idx, filename in enumerate(filenames):
        log.info(f"{idx+1}/{len(filenames)}\t{filename}")
        route_id = re.match(rf"{path}/(.+)?.gpx", filename).group(1)
        if route_id in seen:
            log.info("\tskipping: already in geojson")
            continue

        # read gpx to get start time
        with open(filename, "r") as f:
            gpx = gpxpy.parse(f)
        start = (
            gpx.tracks[0]
            .segments[0]
            .points[0]
            .time.astimezone(local_tz)
            .strftime("%b %-d, %Y %-I:%M%p")
        )

        # read gpx into geopandas GeoDataFrame
        route = gpd.read_file(filename, engine="pyogrio", layer="tracks")
        # geometry is a multilinestring
        route = route[["name", "geometry"]]
        route = route.to_crs("EPSG:4326")
        name = route["name"][0]
        # check if route is within bounding box
        if bbox_df is not None:
            if gpd.sjoin(route, bbox_df).empty:
                log.info(f"\tskipping: {name} not in bbox")
                continue
        # drop points outside of bounding box
        route = gpd.clip(route, bbox_df)
        route["start"] = start
        route["id"] = route_id
        route["url"] = f"https://www.strava.com/activities/{route_id}"
        log.info(f"\tadding {name}\t{start}")
        routes.append(route)

    gdf = gpd.GeoDataFrame(
        pd.concat([prev_df] + routes, ignore_index=True), crs="EPSG:4326"
    )
    gdf.to_file(output_fn, driver="GeoJSON")
    log.info(f"wrote {len(gdf)} routes to {output_fn}")


if __name__ == "__main__":
    # set logging handler to output date and message
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="path to gpx files")
    # need a leading space to prevent argparse from treating - as an argument
    # --bbox " -122.732314,36.916954,-120.977248,37.699028"
    parser.add_argument(
        "--bbox",
        type=str,
        help=(
            'bounding box: " lat,lng,lat,lng" include leading space before - so it '
            "won't be treated as an argument"
        ),
    )
    parser.add_argument(
        "--output", type=str, default="routes.geojson", help="output filename"
    )
    args = parser.parse_args()
    main(args.path, args.output, args.bbox.strip() if args.bbox else None)
