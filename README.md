# setup

## prerequisites

- download [pmtiles](https://github.com/protomaps/go-pmtiles/releases)

## prepare

- get bounding box from bboxfinder: `-122.732314,36.916954,-120.977248,37.699028`
- download tiles: `pmtiles extract https://build.protomaps.com/20240316.pmtiles my_area.pmtiles --bbox=-122.732314,36.916954,-120.977248,37.699028`

- download activity data from Strava: [Download or Delete Your Account](https://www.strava.com/athlete/delete_your_account) Download Request / Request Your Archive.

  - download zip file from email
  - unzip and keep only `activities` directory (with .gpx files)
  - some but not all are .gz; `gunzip output/activities/*.gz`

# run

Create GeoJSON from gpx files, limited to bounding box:

    python gpx_to_geojson.py output/activities --bbox " -122.732314,36.916954,-120.977248,37.699028" --output output/routes.geojson

Start local server, then load http://localhost:8000/index.html

Use maptiler SDK to draw routes on the Outdoor basemap.

# resources

  - [Protomaps](https://protomaps.com/) is an open source map of the world, deployable as a single static file on cloud storage.
  - [tippecanoe](https://github.com/felt/tippecanoe) Builds vector tilesets from large (or small) collections of GeoJSON, FlatGeobuf, or CSV features
  - [bboxfinder](http://bboxfinder.com/#51.830755,4.742883,52.256198,5.552837) draw and get coordinates for a bounding box
  - [gpx_geojson_py](https://github.com/ivan4oto/gpx_geojson_py/tree/main)
  - [geopandas](https://geopandas.org/en/stable/getting_started/introduction.html)
  - [gpxpy](https://github.com/tkrajina/gpxpy)
  - [gpx to geopandas](https://www.riannek.de/2022/gpx-to-geopandas/)
  - [Felt](https://felt.com/)
  - [maptiler](https://docs.maptiler.com/sdk-js/examples/)
  - https://www.maptiler.com/news/2019/02/what-are-vector-tiles-and-why-you-should-care/
  - [GeoJSON line data](https://docs.maptiler.com/sdk-js/examples/geojson-line/)
