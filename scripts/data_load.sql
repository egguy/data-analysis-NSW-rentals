-- install geospatial
INSTALL 'spatial';
-- Load geospatial
LOAD 'spatial';

-- Load rental data
CREATE OR REPLACE TABLE
rentals AS
SELECT
	"Lodgement Date" as lodgement_date,
	"Postcode"as postcode,
	"Dwelling Type" as "type",
	"Bedrooms" as bedrooms,
    "Weekly Rent" as weekly_rent
FROM
    read_csv('data/rentals.csv',
            dateformat='%Y-%m-%d',
            columns={
                'Lodgement Date': 'DATE',
                'Postcode': 'VARCHAR',
                'Dwelling Type': 'VARCHAR',
                'Bedrooms': 'INT',
                'Weekly Rent': 'INT'
        }, ignore_errors=True)
;

-- Load suburbs data
CREATE OR REPLACE TABLE suburbs AS
    (
        SELECT
            suburbname as name,
            postcode,
            geom as geometry
        FROM
            st_read( 'data/shp/suburbs/suburb.geojson')
    );

CREATE unique index geo_post on suburbs(postcode);
CREATE index rentals_post on rentals(postcode);