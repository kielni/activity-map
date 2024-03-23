import glob
import logging

import geopandas as gpd
import pandas as pd

log = logging.getLogger("main")


def prep_ridge_trail(input_path: str, output_fn: str):
    """Combine single-route Bay Area Ridge Trail files into one GeoJSON file.

    GeoJSON routes from https://www.alltrails.com/explore/list/bay-trail-62f91ce
    All south bay routes = 354k uncompressed / 72k compressed
    """
    filenames = glob.glob(f"{input_path}/*.js")
    routes = []
    for idx, filename in enumerate(filenames):
        log.info(f"loading {filename}")
        route = gpd.read_file(filename, engine="pyogrio")
        route["name"] = filename.replace(
            f"{input_path}/Bay Area Ridge Trail ", ""
        ).replace(".js", "")
        if len(route.index) > 1:
            log.info(f"\tmultiple features in {filename}")
            route = route[route["geometry"].geom_type == "MultiLineString"]
        route = route.to_crs("EPSG:4326")
        routes.append(route)
    gdf = gpd.GeoDataFrame(pd.concat(routes, ignore_index=True), crs="EPSG:4326")
    # keep only name and geometry columns
    gdf = gdf[["name", "geometry"]]
    gdf.to_file(output_fn, driver="GeoJSON")
    log.info(f"wrote {len(gdf)} routes to {output_fn}")


if __name__ == "__main__":
    # set logging handler to output date and message
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
    prep_ridge_trail("ridge_trail", "output/ridge_trail.geojson")
