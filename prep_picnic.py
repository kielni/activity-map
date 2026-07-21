"""Extract picnic table features from Open Street Map to a static file.

[North America (US) taginfo](https://taginfo.geofabrik.de/north-america:us/) instance
shows a US extract has about 102k `leisure=picnic_table` nodes.
"""

import argparse
import logging
import os
import subprocess
from pathlib import Path

import fiona
import geopandas as gpd
import pandas as pd
import requests
from tqdm import tqdm

log = logging.getLogger("main")

GEOFABRIK_BASE_URL = "https://download.geofabrik.de"


def download_osm(region: str = "north-america/us") -> Path:
    """Download a Geofabrik regional `.osm.pbf` extract to OSM_DATA_DIR.

    Output is named by region (e.g. `us-latest.osm.pbf`) so extracts for
    other regions can be added later without restructuring the pipeline.
    .pbf (Protocolbuffer Binary Format) is OSM's compact binary encoding.
    """
    region_slug: str = region.split("/")[-1]
    url: str = f"{GEOFABRIK_BASE_URL}/{region}-latest.osm.pbf"
    data_dir: Path = Path(os.environ["OSM_DATA_DIR"])
    data_dir.mkdir(parents=True, exist_ok=True)
    dest: Path = data_dir / f"{region_slug}-latest.osm.pbf"

    log.info(f"downloading {url} to {dest}")
    response: requests.Response = requests.get(url, stream=True)
    response.raise_for_status()
    total_bytes: int = int(response.headers.get("content-length", 0))

    chunk_size: int = 1024 * 1024
    with open(dest, "wb") as f, tqdm(
        total=total_bytes, unit="B", unit_scale=True, unit_divisor=1024, desc=str(dest)
    ) as progress:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            progress.update(len(chunk))

    log.info(f"downloaded {dest}")
    return dest


def _feature_count(geojson_path: Path) -> int:
    with fiona.open(str(geojson_path)) as source:
        return len(source)


def parse_pbf(pbf_path: Path) -> str:
    """Filter one OSM extract to picnic table nodes.

    Writes a tag-filtered intermediate named by area (e.g. `us-latest`
    from `us-latest.osm.pbf`) so multiple regions can be processed
    without overwriting each other's output. Queries with
    `-sql "SELECT * FROM points WHERE ..."` rather than naming `points`
    as the target layer plus `-where`: GDAL's OSM driver only skips
    indexing node locations for way/relation geometry resolution when it
    can tell, via that SQL, that no other layer is of interest.
    """
    area: str = pbf_path.name.split(".")[0]
    log.info(f"parsing {pbf_path}")
    output_dir: Path = Path("output")
    tags_geojson: Path = output_dir / f"picnic_tags_{area}.geojson"
    log.info(f"filtering {pbf_path} to picnic table nodes as GeoJSON")
    # GDAL's default OSM driver config doesn't promote "leisure" to its own
    # column; it lives in the catch-all other_tags hstore string instead.
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "GeoJSON",
            str(tags_geojson),
            str(pbf_path),
            "-sql",
            (
                "SELECT * FROM points "
                'WHERE other_tags LIKE \'%"leisure"=>"picnic_table"%\''
            ),
        ],
        check=True,
    )
    log.info(f"{_feature_count(tags_geojson)} picnic table nodes")
    return area


def parse_osm() -> Path:
    """Filter every downloaded OSM extract to picnic table nodes.

    Extracts from every region in OSM_DATA_DIR (see parse_pbf) are
    combined into one output FlatGeobuf.
    """
    output_dir: Path = Path("output")
    pbf_paths: list[Path] = sorted(Path(os.environ["OSM_DATA_DIR"]).glob("*.osm.pbf"))
    areas: list[str] = [parse_pbf(p) for p in pbf_paths]

    log.info(f"loading {len(areas)} filtered extracts")
    tags: list[gpd.GeoDataFrame] = [
        gpd.read_file(output_dir / f"picnic_tags_{area}.geojson") for area in areas
    ]
    total = sum([len(gdf) for gdf in tags])
    log.info(f"loaded {total} features")
    gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        pd.concat(tags, ignore_index=True), crs="EPSG:4326"
    )

    log.info(f"stripping {len(gdf)} picnic tables to minimal properties")
    gdf = gdf[["osm_id", "geometry"]].rename(columns={"osm_id": "id"})

    output_path = output_dir / "picnic.fgb"
    gdf.to_file(output_path, driver="FlatGeobuf")
    log.info(f"wrote {len(gdf)} picnic tables to {output_path}")
    return output_path


def main(ops: list[str], region: str = "north-america/us"):
    if "download" in ops:
        download_osm(region)
    if "parse" in ops:
        parse_osm()


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "op",
        type=str,
        nargs="+",
        choices=["download", "parse"],
        help="one or more of: download, parse",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="north-america/us",
        help="Geofabrik region path to download, e.g. north-america/us",
    )
    args = parser.parse_args()
    main(args.op, args.region)
