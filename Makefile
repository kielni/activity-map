lint:
	black *.py
	flake8 *.py

download-strava:
	unzip -u strava.zip 'activities/*' -d strava
	gunzip strava/activities/*.gz

prep-strava:
	python -u prep_strava.py strava/activities --bbox " $(BOUNDING_BOX)" --output output/routes.geojson 2>&1 | tee prep-strava.log
	cp output/routes.geojson output/routes_gz.geojson
	gzip output/routes_gz.geojson
	mv output/routes_gz.geojson.gz output/routes_gz.geojson
	ls -lh output/routes*

prep-ridge:
	python -u prep_ridge.py 2>&1 | tee prep-rdige.log
	cp output/ridge_trail.geojson output/ridge_trail_gz.geojson
	gzip output/ridge_trail_gz.geojson
	mv output/ridge_trail_gz.geojson.gz output/ridge_trail_gz.geojson
	ls -lh output/ridge_trail*

prep-shoreline:
	python -u prep_bay.py 2>&1 | tee prep-shoreline.log
	cp output/bay_trail.geojson output/bay_trail_gz.geojson
	gzip output/bay_trail_gz.geojson
	mv output/bay_trail_gz.geojson.gz output/bay_trail_gz.geojson
	ls -lh output/bay_trail*

overlap:
	python -u bay.py 2>&1 | tee prep-bay.log
	cp output/trail_routes.geojson output/trail_routes_gz.geojson
	gzip output/trail_routes_gz.geojson
	mv output/trail_routes_gz.geojson.gz output/trail_routes_gz.geojson
	ls -lh output/trail_routes*

sync:
	# prereqs
	#   - set S3_BUCKET in environment
	#   - create config_aws.js with values for MAP_TILER_API_KEY and HOST on AWS
	echo "syncing to $(S3_BUCKET)"
	aws s3 cp index.html s3://$(S3_BUCKET)/index.html
	aws s3 cp bay.html s3://$(S3_BUCKET)/bay.html
	aws s3 cp config_aws.js s3://$(S3_BUCKET)/config.js
	aws s3 cp output/routes_gz.geojson s3://$(S3_BUCKET)/routes.geojson --content-encoding gzip --content-type application/json
	aws s3 cp output/ridge_trail_gz.geojson s3://$(S3_BUCKET)/ridge_trail.geojson --content-encoding gzip --content-type application/json
	aws s3 cp output/bay_trail_gz.geojson s3://$(S3_BUCKET)/bay_trail.geojson --content-encoding gzip --content-type application/json
	aws s3 cp output/trail_routes_gz.geojson s3://$(S3_BUCKET)/trail_routes.geojson --content-encoding gzip --content-type application/json
