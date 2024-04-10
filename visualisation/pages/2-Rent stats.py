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
        "Postcode", options=get_postcodes(), key="2-postcode"
    )

with header_col2:
    selected_dwelling_types = st.multiselect(
        "Dwelling type", options=reversed_housing_types.keys(), key="2-dwelling-type"
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
    key="2-year",
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

# Price per bedroom per year
df_rentals = rentals_per_bedroom.df()

# Cleanup the data, remove the outliers
lower_bound = df_rentals["weekly_rent"].quantile(0.05)
upper_bound = df_rentals["weekly_rent"].quantile(0.95)
df_rentals_filtered = df_rentals[df_rentals["weekly_rent"] >= lower_bound]
df_rentals_filtered = df_rentals_filtered[
    df_rentals_filtered["weekly_rent"] <= upper_bound
]

# stats on date, bedrooms, weekly rent, only select thoses columns
df_rentals_stats = db.query(
    """
SELECT date_trunc('month', lodgement_date) AS "month",
 bedrooms_corrected as "bedrooms",
  AVG("weekly_rent") as "weekly_rent",
  MIN("weekly_rent") as "min_weekly_rent",
    MAX("weekly_rent") as "max_weekly_rent",
    median("weekly_rent") as "median_weekly_rent"
FROM df_rentals_filtered
group by date_trunc('month', lodgement_date), bedrooms_corrected
order by date_trunc('month', lodgement_date), bedrooms_corrected
"""
)
# df_rentals_stats.set_index(['month', 'bedrooms'] , inplace=True)


c1, c2 = st.columns(2)
with c1:
    # display as a line chart
    figure = px.line(
        df_rentals_stats,
        x="month",
        y="weekly_rent",
        color="bedrooms",
        title="Average weekly rent per bedroom per year",
    )
    figure.update_layout(
        xaxis_title="Month",
        yaxis_title="Average weekly rent ($)",
        legend_title="Bedrooms",
    )
    st.plotly_chart(figure, use_container_width=True)

with c2:
    # create a histogram of the weekly rent per bedroom
    historgram = px.histogram(
        df_rentals_filtered,
        x="weekly_rent",
        color="bedrooms_corrected",
        title="Distribution weekly rent per bedroom",
        nbins=20,
    )
    historgram.update_layout(barmode="overlay")
    st.plotly_chart(historgram, use_container_width=True)

st.dataframe(df_rentals_stats)
