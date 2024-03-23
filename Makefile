lint:
	black *.py
	flake8 *.py

strava:
	python prep_strava.py output/activities --bbox " $BOUNDING_BOX" --output output/routes.geojson
	cp output/routes.geojson output/routes_gz.geojson
	gzip output/routes_gz.geojson
	mv output/routes_gz.geojson.gz output/routes_gz.geojson
	ls -lh output/routes*

ridge:
	python prep_ridge.py
	cp output/ridge_trail.geojson output/ridge_trail_gz.geojson
	gzip output/ridge_trail_gz.geojson
	mv output/ridge_trail_gz.geojson.gz output/ridge_trail_gz.geojson
	ls -lh output/ridge_trail*

shoreline:
	python prep_bay.py
	cp output/bay_trail.geojson output/bay_trail_gz.geojson
	gzip output/bay_trail_gz.geojson
	mv output/bay_trail_gz.geojson.gz output/bay_trail_gz.geojson
	ls -lh output/bay_trail*

overlap:
	python bay.py
	cp output/trail_routes.geojson output/trail_routes_gz.geojson
	gzip output/trail_routes_gz.geojson
	mv output/trail_routes_gz.geojson.gz output/trail_routes_gz.geojson
	ls -lh output/trail_routes*

sync:
	aws s3 cp index.html s3://$(S3_BUCKET)/index.html
	aws s3 cp bay.html s3://$(S3_BUCKET)/bay.html
	aws s3 cp config_aws.js s3://$(S3_BUCKET)/config.js
	aws s3 cp output/routes_gz.geojson s3://$(S3_BUCKET)/routes.geojson --content-encoding gzip --content-type application/json
	aws s3 cp output/ridge_trail_gz.geojson s3://$(S3_BUCKET)/ridge_trail.geojson --content-encoding gzip --content-type application/json
	aws s3 cp output/bay_trail_gz.geojson s3://$(S3_BUCKET)/bay_trail.geojson --content-encoding gzip --content-type application/json
	aws s3 cp output/trail_routes_gz.geojson s3://$(S3_BUCKET)/trail_routes.geojson --content-encoding gzip --content-type application/json
