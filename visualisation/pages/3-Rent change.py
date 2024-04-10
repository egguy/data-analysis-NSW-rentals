import streamlit as st

import constants
from constants import (
    reversed_housing_types,
    get_postcodes,
    get_min_max_year,
)
import plotly.express as px

from db import get_db

st.set_page_config(page_title="Rentals stats", layout="wide")

db = get_db()

st.markdown(constants.disclaimer)


header_col1, header_col2 = st.columns(2)

with header_col1:
    selected_postcodes = st.multiselect(
        "Postcode", options=get_postcodes(), key="3-postcode"
    )

with header_col2:
    selected_dwelling_types = st.multiselect(
        "Dwelling type", options=reversed_housing_types.keys(), key="3-dwelling-type"
    )
selected_dwelling_types = [reversed_housing_types[x] for x in selected_dwelling_types]

# get min max year from rentals
min_year, max_year = get_min_max_year()
year_choice = st.slider(
    "Year",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
    key="3-year",
)

# Select 2 to 12 months for the trend
month_trend = st.slider("Select the number of months for the trend", 2, 12, 4)


# Get the base stats
rentals_per_bedroom = (
    db.sql(
        """
SELECT 
    *,
    datetrunc('month', "lodgement_date") AS "month",
FROM rentals where 
    "bedrooms" > 0 and "bedrooms" <= 5
    -- remove outliers
    AND "weekly_rent" > (SELECT QUANTILE_CONT(weekly_rent, 0.05) FROM rentals)
    AND "weekly_rent" < (SELECT QUANTILE_CONT(weekly_rent, 0.95)  FROM rentals) 
order by "lodgement_date", "bedrooms"
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

df_rentals = rentals_per_bedroom


# Calculate the mean weekly rent per bedroom
df_rentals = (
    rentals_per_bedroom.df()
    .groupby(["month", "bedrooms"])
    .agg({"weekly_rent": "mean"})
    .reset_index()
)

# do a rolling mean of the weekly rent
df_rentals["weekly_rent_trend"] = (
    df_rentals.groupby("bedrooms")["weekly_rent"]
    .rolling(month_trend)
    .mean()
    .reset_index(0, drop=True)
)
# # fill the NaN with 0
# df_rentals["weekly_rent_trend"] = df_rentals["weekly_rent_trend"].fillna(0)

# calculate the percentage change
df_rentals["weekly_rent_pct_change"] = (
    df_rentals.groupby("bedrooms")["weekly_rent"].pct_change()
) * 100

# do a cumsum of the pct change
df_rentals["weekly_rent_pct_change_cumsum"] = df_rentals.groupby("bedrooms")[
    "weekly_rent_pct_change"
].cumsum()

# do a percentage change of the rolling mean
df_rentals["weekly_rent_trend"] = (
    df_rentals.groupby("bedrooms")["weekly_rent_trend"].pct_change()
) * 100


# do a cumsum of the pct change
df_rentals["weekly_rent_trend_cumsum"] = df_rentals.groupby("bedrooms")[
    "weekly_rent_trend"
].cumsum()


def make_trend_graph(df, y, title):
    graph = px.line(
        df,
        x="month",
        y=y,
        color="bedrooms",
        title=title,
    )
    graph.add_shape(
        type="line",
        x0=df_rentals["month"].min(),
        y0=0,
        x1=df_rentals["month"].max(),
        y1=0,
        line=dict(
            color="black",
            width=0.5,
            dash="dashdot",
        ),
    )
    return graph


# create 2 columns
col1, col2 = st.columns(2)

# display on the col1 the percent change and the cumsum
with col1:
    st.write("Percentage change in weekly rent per bedroom per year")

    pct_change_trend = make_trend_graph(
        df_rentals,
        "weekly_rent_pct_change",
        "Percentage change in weekly rent per bedroom per year",
    )
    st.plotly_chart(pct_change_trend, use_container_width=True)

    # cumsum of the pct change
    cumsum_trend = make_trend_graph(
        df_rentals,
        "weekly_rent_pct_change_cumsum",
        "Cumulative percentage change in weekly rent per bedroom per year",
    )
    st.plotly_chart(cumsum_trend, use_container_width=True)

with col2:
    st.write(
        f"Smoothed percentage change in weekly rent per bedroom per year over {month_trend} months"
    )
    rolling_trend = make_trend_graph(
        df_rentals,
        "weekly_rent_trend",
        f"Smoothed percentage change in weekly rent per bedroom per year over {month_trend} months",
    )
    st.plotly_chart(rolling_trend, use_container_width=True)

    # cumsum of the pct change
    rolling_cumsum_trend = make_trend_graph(
        df_rentals,
        "weekly_rent_trend_cumsum",
        f"Cumulative smoothed percentage change in weekly rent per bedroom per year over {month_trend} months",
    )
    st.plotly_chart(rolling_cumsum_trend, use_container_width=True)

# display as a line chart
