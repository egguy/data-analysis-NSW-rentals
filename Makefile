BOUNDARIES_URL="https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/GCCSA_2021_AUST_SHP_GDA2020.zip"

default:
	@echo "Please specify a target"

convert_xlsx:
	@echo "Converting XLSX to CSV"
	python scripts/convert_xlsx_to_csv.py

clean_data: convert_xlsx
	@echo "Cleaning data"
	python scripts/cleanup_lodgements.py
	python scripts/cleanup_refunds.py

fill_datasette: clean_data
	@echo "Filling datasette"
	mkdir -p data/output/datasette/
	sqlite-utils enable-wal data/output/datasette/rentals.db
	sqlite-utils insert data/output/datasette/rentals.db rentals data/output/csv/lodgements_combined.csv --csv --truncate --convert '{"Bedrooms": int(row["Bedrooms"]),"Weekly Rent": int(row["Weekly Rent"])}'
	sqlite-utils transform data/output/datasette/rentals.db rentals --type "Bedrooms" INTEGER --type "Weekly Rent" INTEGER
	sqlite-utils insert data/output/datasette/rentals.db refunds data/output/csv/refunds_combined.csv --csv --truncate --convert '{"Payment To Tenant": int(row["Payment To Tenant"]),"Payment To Agent": int(row["Payment To Agent"]),"Bedrooms": int(row["Bedrooms"]),"Days Bond Held": int(row["Days Bond Held"])}'
	sqlite-utils transform data/output/datasette/rentals.db refunds --type "Payment To Tenant" INTEGER --type "Payment To Agent" INTEGER --type "Bedrooms" INTEGER --type "Days Bond Held" INTEGER
	sqlite-utils insert data/output/datasette/rentals.db postcodes data/input/postcodes/australian_postcodes.csv --csv --truncate
	sqlite-utils vacuum data/output/datasette/rentals.db

#
#fetch_data:
#	@echo "Downloading rentals data"
#	python scripts/download_rentals.py
#
#data/rentals.csv data/rentals.parquet:
#	@echo "Downloading rentals data"
#	python scripts/download_rentals.py
#
#data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.zip:
#	curl -o $@ $(BOUNDARIES_URL)
#
#data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.shp: data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.zip
#	unzip $< -d data/shp/stats-boundaries/
#	# touch to update timestamp
#	touch data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.shp
#
#data/shp/stats-boundaries/GCCSA_2021_AUST_WGS84.shp: data/shp/stats-boundaries/GCCSA_2021_AUST_GDA2020.shp
#	ogr2ogr -progress -f "ESRI Shapefile" -t_srs EPSG:4326 $@ $<
#
#
#fill_database: data/rentals.csv data/shp/stats-boundaries/GCCSA_2021_AUST_WGS84.shp data/shp/suburbs/Suburb.shp
#	@echo "Filling database with data"
#	duckdb  rentals.duckdb < scripts/data_load.sql
