BOUNDARIES_URL="https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/GCCSA_2021_AUST_SHP_GDA2020.zip"

default:
	@echo "Please specify a target"


init:
	@echo "Creating venv"
	python3 -m venv venv
	@echo "Installing requirements"
	venv/bin/pip install -r requirements.txt

data/rentals.csv data/rentals.parquet:
	@echo "Downloading rentals data"
	python scripts/download_rentals.py

data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.zip:
	curl -o $@ $(BOUNDARIES_URL)

data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.shp: data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.zip
	unzip $< -d data/shp/stats-boundaries/
	# touch to update timestamp
	touch data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.shp

data/shp/stats-boundaries/GCCSA_2021_AUST_WGS84.shp: data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.shp
	ogr2ogr -progress -f "ESRI Shapefile" -t_srs EPSG:4326 $@ $<


fill_database: data/rentals.csv data/shp/stats-boundaries/GCCSA_2021_AUST_WGS84.shp data/shp/suburbs/Suburb.shp
	@echo "Filling database with data"
	duckdb  rentals.duckdb < scripts/data_load.sql