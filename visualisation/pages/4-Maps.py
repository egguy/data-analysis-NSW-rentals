import json

import streamlit as st
import duckdb
from shapely import transform

import constants
from constants import (
    housing_types,
    reversed_housing_types,
    get_min_max_year,
    get_postcodes,
)
import shapely
import geopandas as gpd
import pydeck as pdk

import folium
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
    return postcodes


postcodes = get_postcode_boundaries(selected_postcodes)
postcodes["geometry"] = postcodes["geometry"].apply(
    lambda x: x.simplify(0.0002, preserve_topology=False)
)
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
# df['geometry'] = gpd.GeoSeries.from_wkb(df['geometry'], crs='4326')
# # Set the geometry column
# df.set_geometry('geometry', inplace=True, crs='4326')

# print(df['geometry'].iloc[0])
# df['geometry'].iloc[0].geom_type

# m = folium.Map(location=[-33.8688, 151.2093], zoom_start=10)
# maps = df.explore("Weekly rent", m=m)
# st_folium(m)
# df.set_index('postcode', inplace=True)
#
df["lat"] = df.geometry.centroid.x
df["lon"] = df.geometry.centroid.y

print(df.info())
# only keep lat, lon and weekly rent
# df = df[['lat', 'lon', 'Weekly rent']]
# rename Weekly rent to weekly_rent
df.rename(columns={"Weekly rent": "weekly_rent"}, inplace=True)


# center = db.sql("""select
#     ST_centroid(
#         ST_collect(
#             list(
#                 (select geometry from bounding)
#                 )
#             )
#         )""").fetchone()[0]

# center = df.dissolve().centroid
# m = folium.Map(location=[center.x, center.y], zoom_start=16)


# print(df.to_json())
def map(data, lat, lon, zoom):
    # get min and max weekly rent
    min_rent = data["weekly_rent"].min()
    max_rent = data["weekly_rent"].max()
    # calculate the ration to scale from 0 to 255
    ratio = 255 / (max_rent - min_rent)

    view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=50)
    price_columns = pdk.Layer(
        "ColumnLayer",
        data=data,
        # get_polygon="geometry",
        radius=100,
        get_position=["lat", "lon"],
        get_elevation="weekly_rent",
        elevation_scale=2,
        pickable=True,
        extruded=True,
        auto_highlight=True,
        get_fill_color=[f"weekly_rent*{ratio}", f"255-(weekly_rent*{ratio})", 0, 140],
    )
    tooltip = {
        "html": "<b>Mean weely rent: ${weekly_rent}</b><br/>Postcode: {postcode}",
        "style": {
            "background": "grey",
            "color": "white",
            "font-family": '"Helvetica Neue", Arial',
            "z-index": "10000",
        },
    }

    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[
                price_columns,
            ],
            tooltip=tooltip,
        )
    )


def map(data, lat, lon, zoom):
    # get min and max weekly rent
    min_rent = data["weekly_rent"].min()
    max_rent = data["weekly_rent"].max()
    # calculate the ration to scale from 0 to 255
    ratio = 255 / (max_rent - min_rent)

    # data['geometry'].map(lambda polygon: transform(lambda x, y: (y, x), polygon))

    view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=50)
    price_columns = pdk.Layer(
        "GeoJsonLayer",
        data=data,
        # get_polygon="geometry",
        # radius=100,
        get_polygon="geometry",
        # get_position=["lat", "lon"],
        # get_elevation='weekly_rent',
        # elevation_scale=2,
        # pickable=True,
        # extruded=True,
        # auto_highlight=True,
        get_fill_color=[f"weekly_rent*{ratio}", f"255-(weekly_rent*{ratio})", 0, 140],
    )
    tooltip = {
        "html": "<b>Mean weely rent: ${weekly_rent}</b><br/>Postcode: {postcode}",
        "style": {
            "background": "grey",
            "color": "white",
            "font-family": '"Helvetica Neue", Arial',
            "z-index": "10000",
        },
    }

    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[
                price_columns,
            ],
            tooltip=tooltip,
        )
    )


# map(df, -33.8688, 151.2093, 10)

# select the columns lat, lon and weekly rent
# df_rent = df[['geometry', 'Weekly rent']]
# rename Weekly rent to weekly_rent
# df_rent.rename(columns={'Weekly rent': 'weekly_rent'}, inplace=True)

# map(df_rent, center.x, center.y, 10)
# print(df_rent.iloc[0:1].to_json())
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

# print(df.head())
# print(df.info())

# df.plot(column='Weekly rent', legend=True)
# st.pyplot()
# Release the connection

