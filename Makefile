geojson:
	python gpx_to_geojson.py output/activities --bbox " $BOUNDING_BOX" --output output/routes.geojson
	ls -lh output/routes.geojson

tiles:
	tippecanoe -zg --force -o output/routes.mbtiles -l routes --drop-densest-as-needed output/routes.geojson
	ls -lh output/routes.mbtiles

sync:
	aws s3 cp index.html s3://$S3_BUCKET/index.html
	aws s3 cp config.js s3://$S3_BUCKET/config.js
	cp output/routes.geojson output/routes_gz.geojson
	gzip output/routes_gz.geojson
	mv output/routes_gz.geojson.gz output/routes_gz.geojson
	ls -lh output/routes*.geo*
	aws s3 cp output/routes_gz.geojson s3://$S3_BUCKET/routes.geojson --content-encoding gzip --content-type application/json
