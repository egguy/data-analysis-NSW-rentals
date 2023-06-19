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
            wkb_geometry,
            ST_GeomFromWKB(wkb_geometry) as geometry
        FROM
            st_read( 'data/shp/suburbs/Suburb.shp')
    UNION ALL
        -- Add the greater sydney region
        SELECT
            "GCC_NAME21" as name,
            '' as postcode,
            wkb_geometry,
            ST_GeomFromWKB(wkb_geometry) as geometry
        FROM
            st_read( 'data/shp/stats-boundaries/GCCSA_2021_AUST_WGS84.shp')
        WHERE
            "GCC_NAME21"  IN ('Greater Sydney', 'Rest of NSW')
    );