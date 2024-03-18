geojson:
	python gpx_to_geojson.py output/activities --bbox " -122.732314,36.916954,-120.977248,37.699028" --output output/routes.geojson
	ls -lh output/routes.geojson

tiles:
	tippecanoe -zg --force -o output/routes.mbtiles -l routes --drop-densest-as-needed output/routes.geojson
	ls -lh output/routes.mbtiles
