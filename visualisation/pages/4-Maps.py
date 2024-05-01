import pandas as pd
import streamlit as st

import constants
from constants import (
    reversed_housing_types,
    get_min_max_year,
    get_postcodes,
)
import geopandas as gpd

from streamlit_folium import st_folium

from db import get_db

st.set_page_config(page_title="Rentals stats", layout="wide")

db = get_db()

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


@st.cache_data
def rental_per_bedroom(
    year_choice: list[int],
    selected_dwelling_types: list[str],
    selected_postcodes: list[str],
) -> pd.DataFrame:
    args = []
    if len(selected_dwelling_types) > 0:
        # prepare for SQL
        selected_dwellings = ",".join([f"'{x}'" for x in selected_dwelling_types])
        args.append('"type" IN ({})'.format(selected_dwellings))
    if len(selected_postcodes) > 0:
        args.append(f'rentals.postcode IN ({",".join(selected_postcodes)})')

    if len(args) > 0:
        args = f'AND {" AND ".join(args)}'
    else:
        args = ""
    # bar graph of number of rentals per number of bedrooms
    rentals_per_bedroom = db.sql(
        f"""
    SELECT
        rentals.postcode as postcode,
        round(AVG("weekly_rent"), 2) AS "Weekly rent"
    FROM rentals
    WHERE 
        datepart('year', \"lodgement_date\") >= {year_choice[0]}
        AND datepart('year',\"lodgement_date\") <= {year_choice[1]}
        {args}
    group by 1
    """
    )

    geo_data = db.sql("""
SELECT
            ST_AsWKB(geometry) as geometry,
            geo.postcode,
            "Weekly rent"
            from suburbs as geo
            inner join rentals_per_bedroom r on geo.postcode = r.postcode
            
    """)

    df = gpd.GeoDataFrame.from_records(
        geo_data.fetchall(),
        columns=["geometry", "postcode", "Weekly rent"],
    )
    # convert the geometry to a shapely object
    df["geometry"] = gpd.GeoSeries.from_wkb(df["geometry"], crs="4326")
    # Set the geometry column
    df.set_geometry("geometry", inplace=True)
    df = df.reset_index()
    # df = rentals_per_bedroom.df()
    print("rental_per_bedroom")
    print(df.info())
    # only keep lat, lon and weekly rent
    # df = df[['lat', 'lon', 'Weekly rent']]
    # rename Weekly rent to weekly_rent
    df.rename(columns={"Weekly rent": "weekly_rent"}, inplace=True)
    return df


print("Getting postcodes")

df = rental_per_bedroom(year_choice, selected_dwelling_types, selected_postcodes)

df["lat"] = df.geometry.centroid.x
df["lon"] = df.geometry.centroid.y

print(df.info())


map = df.explore(
    column="weekly_rent",
    # scheme="naturalbreaks",
    cmap="OrRd",
    k=10,
    legend=True,
)
print("callculated map")

make_map_responsive = """
     <style>
     [title~="st.iframe"] { width: 100%}
     </style>
    """
st.markdown(make_map_responsive, unsafe_allow_html=True)

st_date = st_folium(map, returned_objects=[], width=1000, height=500, use_container_width=True)
