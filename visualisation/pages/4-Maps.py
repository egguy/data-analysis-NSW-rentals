import streamlit as st
import duckdb

import constants
from constants import (
    reversed_housing_types,
    get_min_max_year,
    get_postcodes,
)
import geopandas as gpd

from streamlit_folium import st_folium

st.set_page_config(page_title="Rentals stats", layout="wide")

db = duckdb.connect(database="rentals.duckdb", read_only=True)
db.execute("load 'spatial'")

st.markdown(constants.disclaimer)


header_col1, header_col2 = st.columns(2)

with header_col1:
    selected_postcodes = st.multiselect("Postcode", options=get_postcodes())

with header_col2:
    selected_dwelling_types = st.multiselect(
        "Dwelling type", options=reversed_housing_types.keys()
    )
selected_dwelling_types = [reversed_housing_types[x] for x in selected_dwelling_types]

# get min max year from rentals
min_year, max_year = get_min_max_year()
year_choice = st.slider(
    "Year", min_value=min_year, max_value=max_year, value=(min_year, max_year), step=1
)

# bar graph of number of rentals per number of bedrooms
rentals_per_bedroom = (
    db.sql(
        """
SELECT *, CASE WHEN bedrooms > 5 THEN 5 else bedrooms END AS "bedrooms_corrected"
FROM rentals
"""
    )
    .filter(f"datepart('year', \"lodgement_date\") >= {year_choice[0]}")
    .filter(f"datepart('year',\"lodgement_date\") <= {year_choice[1]}")
)

if len(selected_postcodes) > 0:
    rentals_per_bedroom = rentals_per_bedroom.filter(
        f'postcode IN ({",".join(selected_postcodes)})'
    )

if len(selected_dwelling_types) > 0:
    # prepare for SQL
    selected_dwelling_types = ",".join([f"'{x}'" for x in selected_dwelling_types])
    rentals_per_bedroom = rentals_per_bedroom.filter(
        '"type" IN ({})'.format(selected_dwelling_types)
    )

# mean_rentals_per_bedroom = db.sql("""
# SELECT
#     bedrooms_corrected as bedrooms,
#     round(AVG("weekly_rent"), 2) AS "Weekly rent"
#     from rentals_per_bedroom group by 1
# """).df()


@st.cache_data
def get_postcode_boundaries(selected_postcodes: list[str] = None):
    # get the bounds for the map
    geom_postcodes = db.sql(
        """
    SELECT
        -- ST_AsWKB(ST_FlipCoordinates(geometry)) as geometry,
        ST_AsWKB(geometry) as geometry,
        postcode
    FROM suburbs
    """
    )
    if selected_postcodes:
        geom_postcodes = geom_postcodes.filter(
            f'postcode IN ({",".join(selected_postcodes)})'
        )

    # load the postcode in a geopandas dataframe
    postcodes = gpd.GeoDataFrame.from_records(
        geom_postcodes.fetchall(), columns=["geometry", "postcode"]
    )
    # convert the geometry to a shapely object
    postcodes["geometry"] = gpd.GeoSeries.from_wkb(postcodes["geometry"], crs="4326")
    # Set the geometry column
    postcodes.set_geometry("geometry", inplace=True)
    print(postcodes.head(10))
    # postcodes.to_crs(epsg=4326, inplace=True)
    # group by postcode and union the geometry
    postcodes = postcodes.dissolve(by="postcode").reset_index()

    postcodes["geometry"] = postcodes["geometry"].apply(
        lambda x: x.simplify(0.0002, preserve_topology=False)
    )

    return postcodes


postcodes = get_postcode_boundaries(selected_postcodes)
print(postcodes.info())


# get average rent per postcode
rent_per_postcode = db.sql(
    """
SELECT
    postcode as postcode,
    -- bounding.centroid as centroid,
    round(AVG("weekly_rent"), 2) AS "Weekly rent"
FROM rentals_per_bedroom 
group by postcode
"""
).df()

# join the dataframes on postcode
df = postcodes.merge(rent_per_postcode, on="postcode", how="left")


#
df["lat"] = df.geometry.centroid.x
df["lon"] = df.geometry.centroid.y

print(df.info())
# only keep lat, lon and weekly rent
# df = df[['lat', 'lon', 'Weekly rent']]
# rename Weekly rent to weekly_rent
df.rename(columns={"Weekly rent": "weekly_rent"}, inplace=True)


map = df.explore(
    column="weekly_rent",
    # scheme="naturalbreaks",
    cmap="OrRd",
    k=10,
    legend=True,
)

make_map_responsive = """
     <style>
     [title~="st.iframe"] { width: 100%}
     </style>
    """
st.markdown(make_map_responsive, unsafe_allow_html=True)

st_date = st_folium(map, returned_objects=[], width=1000, height=500)
