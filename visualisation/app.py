import streamlit as st

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to NSW rentals stats! 👋")

st.sidebar.success("Select a stats above.")

st.markdown(
    """
    Streamlit is an open-source app framework built specifically for
    Machine Learning and Data Science projects.
    **👈 Select some stats from the sidebar** to see some examples
    ### Want to learn more?
    - Explore a [NSW rental dataset](https://github.com/egguy/data-analysis-NSW-rentals)
"""
)
