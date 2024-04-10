import plotly.express as px
import streamlit as st

import constants
from constants import (
    reversed_housing_types,
    get_postcodes,
    get_min_max_year,
)
from db import get_db

constants.header("Global stats")

db = get_db()


header_col1, header_col2 = st.columns(2)

with header_col1:
    selected_postcodes = st.multiselect("Postcode", options=get_postcodes(), key="1-ps")

with header_col2:
    selected_dwelling_types = st.multiselect(
        "Dwelling type", options=reversed_housing_types.keys(), key="1-dt"
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
    key="1-y",
)


# General filtering
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


# do a two column layout
col1, col2 = st.columns(2)

### Mean rent per bedroom
with col1:
    mean_rentals_per_bedroom = db.sql(
        """
    SELECT 
        bedrooms_corrected as bedrooms,
        round(AVG("weekly_rent"), 2) AS "Mean weekly rent",
        -- median
        round(median("weekly_rent"), 2) AS "Median weekly rent"
        from rentals_per_bedroom group by 1
    """
    ).df()

    # plot a barchart of the mean and median with ploty
    fig = px.bar(
        mean_rentals_per_bedroom,
        x="bedrooms",
        y=["Mean weekly rent", "Median weekly rent"],
        barmode="group",
        title="Mean and median weekly rent per bedroom",
    )
    fig.update_layout(
        xaxis_title="Bedrooms",
        yaxis_title="Weekly rent",
        legend_title="",
        font=dict(size=18),
    )
    st.plotly_chart(fig, use_container_width=True)


with col2:
    rentals_per_year = db.sql(
        """
    SELECT
        bedrooms_corrected as bedrooms,
        COUNT(*) AS "Bonds lodged"
    FROM rentals_per_bedroom
    GROUP BY 1
    """
    ).df()

    fig = px.bar(
        rentals_per_year,
        x="bedrooms",
        y="Bonds lodged",
        title="Number of rentals per bedroom",
    )
    fig.update_layout(
        xaxis_title="Bedrooms",
        yaxis_title="Number of rentals",
        legend_title="",
        font=dict(size=18),
    )
    st.plotly_chart(fig, use_container_width=True)

# Rentals per month
rentals_per_month = db.sql(
    """
SELECT
    datepart('month', "lodgement_date") AS "Month",
    COUNT(*) AS "Bonds lodged"
FROM rentals_per_bedroom
GROUP BY 1
"""
).df()

fig = px.bar(
    rentals_per_month,
    x="Month",
    y="Bonds lodged",
    title="Number of rentals per month",
)
fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Number of rentals",
    legend_title="",
    font=dict(size=18),
)
st.plotly_chart(fig, use_container_width=True)
