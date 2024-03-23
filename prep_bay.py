import logging

import geopandas as gpd

log = logging.getLogger("main")


def prep_bay_trail(input_fn: str, output_fn: str):
    """Prepare Bay Trail GeoJSON for matching with routes.

    From https://mtc.ca.gov/operations/regional-trails-parks/san-francisco-bay-trail/bay-trail-interactive-map  # noqa: E501
    GeoJSON: https://mtc.ca.gov/modules/custom/mtcca_baytrail_map/sf_baytrail.geojson
    Keep id, location, status, and legend fields.
    Keep only segments that are already exist or are in use but not officially part of the trail.
    """
    trail_df = gpd.read_file(input_fn)
    trail_df = trail_df[["FID", "Location", "STATUS", "IN_USE", "LEGEND", "geometry"]]
    rename = {
        "FID": "id",
        "Location": "name",
        "STATUS": "status",
        "IN_USE": "in_use",
        "LEGEND": "legend",
    }
    trail_df.rename(columns=rename, inplace=True)
    trail_df = trail_df[
        ((trail_df["status"] == "Existing") | (trail_df["in_use"] == "Yes"))
        & (trail_df["legend"] != "Other Trail")
    ]
    trail_df.to_file(output_fn, driver="GeoJSON")
    log.info(f"wrote {len(trail_df)} routes to {output_fn}")


if __name__ == "__main__":
    # set logging handler to output date and message
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
    prep_bay_trail("bay_trail/bay_trail.geojson", "output/bay_trail.geojson")
