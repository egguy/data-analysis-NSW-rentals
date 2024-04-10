import streamlit as st

from db import get_db

housing_types = {
    "F": "Flat/unit",
    "H": "House",
    "T": "Terrace/townhouse/semi-detached",
    "O": "Other",
    "U": "Unknown",
}
reversed_housing_types = {v: k for k, v in housing_types.items()}

disclaimer = """Some Notes:
- The rentals with 5+ bedrooms are aggregated into the 5 category, This has a tendency to skew the data, so keep that in mind when looking at the data
- For the Bedrooms a 0 may indicate a bedsitter or studio apartment, or rented premises such as a garage or car space.
"""


@st.cache_data
def get_postcodes():
    db = get_db()
    postcodes = db.query('SELECT DISTINCT "postcode" FROM rentals')["postcode"].tolist()
    return postcodes


@st.cache_data
def get_dwelling_types():
    db = get_db()
    dwelling_types = db.query('SELECT DISTINCT "type" FROM rentals')["type"].tolist()
    return dwelling_types


@st.cache_data
def get_min_max_year():
    db = get_db()
    min_year, max_year = db.sql(
        'SELECT MIN("lodgement_date"), MAX("lodgement_date") FROM rentals'
    ).fetchone()
    return min_year.year, max_year.year


def header(title):
    st.set_page_config(page_title=title, layout="wide")
    st.markdown(disclaimer)
