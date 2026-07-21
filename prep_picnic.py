"""Extract picnic table features from Open Street Map to a static file.

[North America (US) taginfo](https://taginfo.geofabrik.de/north-america:us/) instance
shows a US & Canada extract has about 126k `leisure=picnic_table` nodes.
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


def parse_pbf(pbf: Path) -> str:
    """Filter one OSM extract to picnic table nodes.

    Writes a tag-filtered intermediate named by region (e.g. `us-latest`
    from `us-latest.osm.pbf`) so multiple regions can be processed
    without overwriting each other's output. Queries with
    `-sql "SELECT * FROM points WHERE ..."` so that GDAL's OSM driver will skip
    indexing node locations for way/relation geometry resolution.
    """
    region: str = pbf.name.split(".")[0]
    log.info(f"parsing {pbf}")
    output_dir: Path = Path("output")
    fgb: Path = output_dir / f"picnic_tags_{region}.fgb"
    log.info(f"filtering {pbf} to picnic table nodes as FlatGeobuf")
    # GDAL's default OSM driver config doesn't promote "leisure" to its own
    # column; it lives in the catch-all other_tags hstore string instead.
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "FlatGeobuf",
            str(fgb),
            str(pbf),
            "-sql",
            (
                "SELECT * FROM points "
                'WHERE other_tags LIKE \'%"leisure"=>"picnic_table"%\''
            ),
        ],
        check=True,
    )
    with fiona.open(str(fgb)) as source:
        count = len(source)
    log.info(f"{count} picnic table nodes")
    return region


def parse_osm() -> Path:
    """Filter every downloaded OSM extract to picnic table nodes.

    Extracts from every region in OSM_DATA_DIR (see parse_pbf) are
    combined into one output FlatGeobuf.
    """
    output_dir: Path = Path("output")
    pbf_paths: list[Path] = sorted(Path(os.environ["OSM_DATA_DIR"]).glob("*.osm.pbf"))
    regions: list[str] = [parse_pbf(p) for p in pbf_paths]

    log.info(f"loading {len(regions)} filtered extracts")
    tags: list[gpd.GeoDataFrame] = [
        gpd.read_file(output_dir / f"picnic_tags_{area}.fgb") for area in regions
    ]
    total = sum([len(gdf) for gdf in tags])
    log.info(f"loaded {total} features")
    gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        pd.concat(tags, ignore_index=True), crs="EPSG:4326"
    )

    log.info(f"stripping {len(gdf)} picnic tables to id and geometry")
    gdf = gdf[["osm_id", "geometry"]].rename(columns={"osm_id": "id"})
    # keep only unique rows by id
    # so that downloading overlapping areas will not create duplicates
    gdf = gdf.drop_duplicates(subset="id", ignore_index=True)
    log.info(f"{len(gdf)} after dropping duplicates")

    output_path = output_dir / "picnic.fgb"
    gdf.to_file(output_path, driver="FlatGeobuf")
    log.info(f"wrote {len(gdf)} picnic tables to {output_path}")
    return output_path


def main(ops: list[str], region: str = "north-america/us"):
    if "download" in ops:
        download_osm(region.split(","))
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
        default="north-america/us,north-america/canada",
        help="comma-delimited list of regions to download",
    )
    args = parser.parse_args()
    main(args.op, args.region)
